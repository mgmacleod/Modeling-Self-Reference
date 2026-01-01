#!/usr/bin/env python3
"""Compute summary "trunkiness" metrics from branch-basin-analysis outputs.

Reads files like:
  data/wikipedia/processed/analysis/branches_n=5_cycle=..._branches_all.tsv
  data/wikipedia/processed/analysis/branches_n=5_cycle=..._branches_topk.tsv

Writes:
  data/wikipedia/processed/analysis/branch_trunkiness_dashboard_n=5_<tag>.tsv
"""

from __future__ import annotations

import argparse
import math
import re
from pathlib import Path

import pandas as pd


def gini_coefficient(values: list[int]) -> float:
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


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--analysis-dir",
        default="data/wikipedia/processed/analysis",
        help="Directory containing branches_* outputs.",
    )
    parser.add_argument(
        "--tag",
        default="bootstrap_2025-12-30",
        help="Tag used in the output filename.",
    )
    parser.add_argument(
        "--n",
        type=int,
        default=5,
        help="N value for N-link rule (default: 5)",
    )
    args = parser.parse_args()

    analysis_dir = Path(args.analysis_dir)
    branch_all_paths = sorted(analysis_dir.glob(f"branches_n={args.n}_cycle=*branches_all.tsv"))

    if not branch_all_paths:
        raise SystemExit(f"No branches_all TSVs found in: {analysis_dir}")

    rows: list[dict[str, object]] = []

    for all_path in branch_all_paths:
        m = re.match(rf"^branches_n={args.n}_cycle=(.*)_branches_all\.tsv$", all_path.name)
        cycle_key = m.group(1) if m else all_path.stem
        cycle_len = len(cycle_key.split("__"))

        df = pd.read_csv(all_path, sep="\t")
        if "basin_size" not in df.columns:
            raise SystemExit(f"Unexpected columns in {all_path}: {list(df.columns)}")

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

        rows.append(
            {
                "cycle_key": cycle_key,
                "cycle_len": cycle_len,
                "total_basin_nodes": total_basin_nodes,
                "n_branches": n_branches,
                "top1_branch_size": top1,
                "top1_share_total": top1 / total_basin_nodes if total_basin_nodes else float("nan"),
                "top5_share_total": top5 / total_basin_nodes if total_basin_nodes else float("nan"),
                "top10_share_total": top10 / total_basin_nodes if total_basin_nodes else float("nan"),
                "effective_branches": effective_branches,
                "gini_branch_sizes": gini,
                "entropy_norm": entropy_norm,
                "dominant_entry_title": dominant_entry_title,
                "dominant_enters_cycle_title": dominant_enters_cycle_title,
                "dominant_max_depth": dominant_max_depth,
                "branches_all_path": all_path.as_posix(),
            }
        )

    out_df = pd.DataFrame(rows).sort_values(
        ["top1_share_total", "total_basin_nodes"], ascending=[False, False]
    )

    out_path = analysis_dir / f"branch_trunkiness_dashboard_n={args.n}_{args.tag}.tsv"
    out_df.to_csv(out_path, sep="\t", index=False)

    # Print a small preview.
    preview_cols = [
        "cycle_key",
        "total_basin_nodes",
        "n_branches",
        "top1_share_total",
        "effective_branches",
        "gini_branch_sizes",
        "dominant_entry_title",
        "dominant_enters_cycle_title",
    ]
    print(f"Wrote: {out_path}")
    print(out_df[preview_cols].head(25).to_string(index=False))

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
