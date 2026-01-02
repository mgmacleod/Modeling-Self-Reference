"""Trunkiness dashboard computation engine for N-Link analysis.

This module provides the core logic for computing "trunkiness" metrics from
branch-basin-analysis outputs. It aggregates branch sizes and computes
statistical measures of branch concentration.

Extracted from compute-trunkiness-dashboard.py for reuse in API layer.
"""

from __future__ import annotations

import math
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Callable

import pandas as pd


ProgressCallback = Callable[[float, str], None] | None


@dataclass
class TrunkinessCycleStats:
    """Trunkiness statistics for a single cycle/basin."""

    cycle_key: str
    cycle_len: int
    total_basin_nodes: int
    n_branches: int
    top1_branch_size: int
    top1_share_total: float
    top5_share_total: float
    top10_share_total: float
    effective_branches: float
    gini_branch_sizes: float
    entropy_norm: float
    dominant_entry_title: str | None
    dominant_enters_cycle_title: str | None
    dominant_max_depth: int | None
    branches_all_path: str


@dataclass
class TrunkinessDashboardResult:
    """Result of trunkiness dashboard computation."""

    n: int
    tag: str
    stats: list[TrunkinessCycleStats]
    output_tsv_path: str | None = None
    elapsed_seconds: float = 0.0


def gini_coefficient(values: list[int]) -> float:
    """Compute Gini coefficient for a list of values.

    Args:
        values: List of non-negative integers.

    Returns:
        Gini coefficient in [0, 1], or NaN if values is empty.
    """
    values = [v for v in values if v >= 0]
    n = len(values)
    if n == 0:
        return float("nan")
    total = sum(values)
    if total == 0:
        return 0.0

    values_sorted = sorted(values)
    cum = 0
    for i, x in enumerate(values_sorted, start=1):
        cum += i * x

    # G = (2 * sum(i * x_i)) / (n * sum x_i) - (n + 1) / n
    return (2 * cum) / (n * total) - (n + 1) / n


def compute_trunkiness_dashboard(
    analysis_dir: Path,
    n: int,
    tag: str,
    *,
    write_output: bool = True,
    progress_callback: ProgressCallback = None,
    verbose: bool = True,
) -> TrunkinessDashboardResult:
    """Compute trunkiness dashboard from branch analysis outputs.

    Reads branches_all.tsv files and computes aggregate statistics
    measuring branch size concentration.

    Args:
        analysis_dir: Directory containing branches_* outputs.
        n: N value for N-link rule.
        tag: Tag used in the output filename.
        write_output: Whether to write the output TSV.
        progress_callback: Optional callback for progress updates.
        verbose: Whether to print progress.

    Returns:
        TrunkinessDashboardResult with computed statistics.
    """
    import time

    t0 = time.time()
    analysis_dir = Path(analysis_dir)
    branch_all_paths = sorted(analysis_dir.glob(f"branches_n={n}_cycle=*branches_all.tsv"))

    if not branch_all_paths:
        raise FileNotFoundError(f"No branches_all TSVs found in: {analysis_dir}")

    stats: list[TrunkinessCycleStats] = []
    total_files = len(branch_all_paths)

    for i, all_path in enumerate(branch_all_paths):
        if progress_callback:
            progress = (i / total_files) if total_files > 0 else 0.0
            progress_callback(progress, f"Processing {all_path.name}")

        m = re.match(rf"^branches_n={n}_cycle=(.*)_branches_all\.tsv$", all_path.name)
        cycle_key = m.group(1) if m else all_path.stem
        cycle_len = len(cycle_key.split("__"))

        df = pd.read_csv(all_path, sep="\t")
        if "basin_size" not in df.columns:
            raise ValueError(f"Unexpected columns in {all_path}: {list(df.columns)}")

        branch_sizes = df["basin_size"].astype("int64").tolist()
        sum_branches = int(sum(branch_sizes))
        total_basin_nodes = sum_branches + cycle_len

        top_sorted = sorted(branch_sizes, reverse=True)
        top1 = int(top_sorted[0]) if top_sorted else 0
        top5 = int(sum(top_sorted[:5]))
        top10 = int(sum(top_sorted[:10]))

        p = [s / sum_branches for s in branch_sizes] if sum_branches else []
        hh = sum(pi * pi for pi in p) if p else 0.0
        effective_branches = (1.0 / hh) if hh > 0 else float("inf")

        entropy_nats = -sum(pi * math.log(pi) for pi in p if pi > 0)
        n_branches = len(branch_sizes)
        entropy_norm = entropy_nats / math.log(n_branches) if n_branches > 1 else 0.0

        gini = gini_coefficient(branch_sizes)

        topk_path = all_path.with_name(all_path.name.replace("_branches_all.tsv", "_branches_topk.tsv"))
        dominant_entry_title = None
        dominant_enters_cycle_title = None
        dominant_max_depth = None
        if topk_path.exists():
            topk_df = pd.read_csv(topk_path, sep="\t")
            if not topk_df.empty:
                dominant_entry_title = str(topk_df.loc[0].get("entry_title", "")) or None
                dominant_enters_cycle_title = str(topk_df.loc[0].get("enters_cycle_title", "")) or None
                if "max_depth" in topk_df.columns:
                    md = topk_df.iloc[0]["max_depth"]
                    if md == md:  # NaN check
                        dominant_max_depth = int(md)

        stats.append(
            TrunkinessCycleStats(
                cycle_key=cycle_key,
                cycle_len=cycle_len,
                total_basin_nodes=total_basin_nodes,
                n_branches=n_branches,
                top1_branch_size=top1,
                top1_share_total=top1 / total_basin_nodes if total_basin_nodes else float("nan"),
                top5_share_total=top5 / total_basin_nodes if total_basin_nodes else float("nan"),
                top10_share_total=top10 / total_basin_nodes if total_basin_nodes else float("nan"),
                effective_branches=effective_branches,
                gini_branch_sizes=gini,
                entropy_norm=entropy_norm,
                dominant_entry_title=dominant_entry_title,
                dominant_enters_cycle_title=dominant_enters_cycle_title,
                dominant_max_depth=dominant_max_depth,
                branches_all_path=all_path.as_posix(),
            )
        )

    # Sort by top1_share_total descending, then total_basin_nodes descending
    stats.sort(key=lambda s: (-s.top1_share_total, -s.total_basin_nodes))

    output_path_str: str | None = None
    if write_output:
        out_path = analysis_dir / f"branch_trunkiness_dashboard_n={n}_{tag}.tsv"
        rows = [
            {
                "cycle_key": s.cycle_key,
                "cycle_len": s.cycle_len,
                "total_basin_nodes": s.total_basin_nodes,
                "n_branches": s.n_branches,
                "top1_branch_size": s.top1_branch_size,
                "top1_share_total": s.top1_share_total,
                "top5_share_total": s.top5_share_total,
                "top10_share_total": s.top10_share_total,
                "effective_branches": s.effective_branches,
                "gini_branch_sizes": s.gini_branch_sizes,
                "entropy_norm": s.entropy_norm,
                "dominant_entry_title": s.dominant_entry_title,
                "dominant_enters_cycle_title": s.dominant_enters_cycle_title,
                "dominant_max_depth": s.dominant_max_depth,
                "branches_all_path": s.branches_all_path,
            }
            for s in stats
        ]
        out_df = pd.DataFrame(rows)
        out_df.to_csv(out_path, sep="\t", index=False)
        output_path_str = str(out_path)
        if verbose:
            print(f"Wrote: {out_path}")

    elapsed = time.time() - t0

    if progress_callback:
        progress_callback(1.0, "Complete")

    return TrunkinessDashboardResult(
        n=n,
        tag=tag,
        stats=stats,
        output_tsv_path=output_path_str,
        elapsed_seconds=elapsed,
    )
