#!/usr/bin/env python3
"""Analyze path characteristics to understand fragmentation vs concentration mechanisms.

Purpose
-------
Compute detailed path metrics to explain the N=4 minimum and N=5 peak:
- Path length distributions (fragmentation indicator)
- Convergence depth distributions (concentration indicator)
- HALT proximity (how close to HALT before reaching cycle)
- Branching statistics at each depth

This script extends sample-nlink-traces.py with additional analytics to test:
1. N=4 fragmentation hypothesis: Do paths HALT earlier at N=4?
2. N=5 concentration hypothesis: Do paths converge faster at N=5?
3. Coverage Paradox: Path existence vs path concentration trade-off

Outputs
-------
Writes multiple analysis files:
1. path_characteristics_n={N}.tsv - Per-sample detailed metrics
2. path_summary_n={N}.tsv - Aggregate statistics
3. depth_distribution_n={N}.tsv - Histogram of depths to cycle/HALT

Theory Connection
-----------------
Tests mechanisms from Coverage Paradox:
- Path Existence: Higher coverage → more paths can continue → longer paths
- Path Concentration: Lower coverage → fewer branches → faster convergence
- N=5 sweet spot: Both effects optimally balanced

References
----------
See llm-facing-documentation/contracts/contract-registry.md (NLR-C-0003)
See n-link-analysis/empirical-investigations/PHASE-TRANSITION-REFINED.md
"""

from __future__ import annotations

import argparse
import time
from collections import Counter, defaultdict
from dataclasses import dataclass
from pathlib import Path
from typing import Literal

import duckdb
import numpy as np


REPO_ROOT = Path(__file__).resolve().parents[2]
PROCESSED_DIR = REPO_ROOT / "data" / "wikipedia" / "processed"
NLINK_PATH = PROCESSED_DIR / "nlink_sequences.parquet"
ANALYSIS_DIR = PROCESSED_DIR / "analysis"

TerminalType = Literal["HALT", "CYCLE", "MAX_STEPS"]


@dataclass(frozen=True)
class PathCharacteristics:
    """Complete characterization of a single path trace."""

    seed: int
    start_page_id: int
    terminal_type: TerminalType

    # Basic metrics
    path_len: int
    steps: int

    # Cycle metrics (if terminal == CYCLE)
    transient_len: int | None
    cycle_len: int | None
    convergence_depth: int | None  # Same as transient_len, but clearer name

    # HALT metrics (if terminal == HALT)
    halt_depth: int | None  # Depth at which HALT occurred

    # Branching metrics (computed at each step)
    mean_outdegree: float  # Average outdegree along path
    min_outdegree: int  # Minimum outdegree encountered
    bottleneck_depth: int  # Depth of minimum outdegree (concentration point)

    # Fragmentation indicators
    early_halt: bool  # Did we HALT before depth 10?
    rapid_convergence: bool  # Did we reach cycle before depth 50?


def _load_successor_arrays(n: int) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """Load page_id → next_id mapping for fixed N."""
    if not NLINK_PATH.exists():
        raise FileNotFoundError(f"Missing: {NLINK_PATH}")

    query = f"""
        SELECT
            page_id::BIGINT AS page_id,
            list_extract(link_sequence, {n})::BIGINT AS next_id,
            list_count(link_sequence)::INTEGER AS out_degree
        FROM read_parquet('{NLINK_PATH.as_posix()}')
    """.strip()

    t0 = time.time()
    con = duckdb.connect()
    tbl = con.execute(query).fetch_arrow_table()
    con.close()

    page_ids = tbl["page_id"].combine_chunks().to_numpy(zero_copy_only=False).astype(np.int64)

    next_ids_raw = tbl["next_id"].combine_chunks().to_numpy(zero_copy_only=False)
    if isinstance(next_ids_raw, np.ma.MaskedArray):
        next_ids = next_ids_raw.filled(-1).astype(np.int64)
    else:
        if np.issubdtype(next_ids_raw.dtype, np.floating):
            next_ids = np.where(np.isnan(next_ids_raw), -1, next_ids_raw).astype(np.int64)
        else:
            next_ids = next_ids_raw.astype(np.int64)

    out_degree = tbl["out_degree"].combine_chunks().to_numpy(zero_copy_only=False).astype(np.int32)

    # Sort by page_id for binary search
    order = np.argsort(page_ids, kind="mergesort")
    page_ids = page_ids[order]
    next_ids = next_ids[order]
    out_degree = out_degree[order]

    dt = time.time() - t0
    print(f"Loaded successor arrays for N={n} in {dt:.1f}s ({len(page_ids):,} pages)")

    return page_ids, next_ids, out_degree


def _lookup_index(sorted_page_ids: np.ndarray, page_id: int) -> int | None:
    """Binary search for page_id index."""
    idx = int(np.searchsorted(sorted_page_ids, page_id))
    if idx >= len(sorted_page_ids) or int(sorted_page_ids[idx]) != page_id:
        return None
    return idx


def _choose_start_page(
    rng: np.random.Generator,
    sorted_page_ids: np.ndarray,
    next_ids: np.ndarray,
    out_degree: np.ndarray,
    *,
    min_outdegree: int,
) -> int:
    """Choose a random start page with sufficient outdegree."""
    candidates = np.where((next_ids != -1) & (out_degree >= min_outdegree))[0]
    if len(candidates) == 0:
        candidates = np.where(next_ids != -1)[0]

    if len(candidates) == 0:
        raise RuntimeError("No candidate pages found with a defined Nth link.")

    chosen_idx = int(rng.choice(candidates))
    return int(sorted_page_ids[chosen_idx])


def trace_with_characteristics(
    *,
    start_page_id: int,
    sorted_page_ids: np.ndarray,
    next_ids: np.ndarray,
    out_degree: np.ndarray,
    max_steps: int,
) -> PathCharacteristics:
    """Trace a single path and compute all characteristics."""

    visited_at: dict[int, int] = {}
    path: list[int] = []
    outdegrees: list[int] = []

    current = int(start_page_id)
    terminal: TerminalType = "MAX_STEPS"
    cycle_start: int | None = None

    for _ in range(max_steps + 1):
        if current in visited_at:
            terminal = "CYCLE"
            cycle_start = visited_at[current]
            break

        visited_at[current] = len(path)
        path.append(current)

        # Record outdegree at this node
        idx = _lookup_index(sorted_page_ids, current)
        if idx is None:
            terminal = "HALT"
            break

        current_outdegree = int(out_degree[idx])
        outdegrees.append(current_outdegree)

        nxt = int(next_ids[idx])
        if nxt == -1:
            terminal = "HALT"
            break

        current = nxt

    # Compute metrics
    path_len = len(path)
    steps = max(0, path_len - 1)

    transient_len: int | None = None
    cycle_len: int | None = None
    convergence_depth: int | None = None
    halt_depth: int | None = None

    if terminal == "CYCLE" and cycle_start is not None:
        transient_len = int(cycle_start)
        cycle_len = int(path_len - cycle_start)
        convergence_depth = int(cycle_start)

    if terminal == "HALT":
        halt_depth = int(path_len - 1)

    # Branching metrics
    if outdegrees:
        mean_outdegree = float(np.mean(outdegrees))
        min_outdegree = int(np.min(outdegrees))
        bottleneck_depth = int(np.argmin(outdegrees))
    else:
        mean_outdegree = 0.0
        min_outdegree = 0
        bottleneck_depth = 0

    # Fragmentation indicators
    early_halt = terminal == "HALT" and halt_depth is not None and halt_depth < 10
    rapid_convergence = terminal == "CYCLE" and convergence_depth is not None and convergence_depth < 50

    return PathCharacteristics(
        seed=0,  # Will be set by caller
        start_page_id=int(start_page_id),
        terminal_type=terminal,
        path_len=int(path_len),
        steps=int(steps),
        transient_len=transient_len,
        cycle_len=cycle_len,
        convergence_depth=convergence_depth,
        halt_depth=halt_depth,
        mean_outdegree=mean_outdegree,
        min_outdegree=min_outdegree,
        bottleneck_depth=bottleneck_depth,
        early_halt=early_halt,
        rapid_convergence=rapid_convergence,
    )


def compute_summary_statistics(characteristics: list[PathCharacteristics]) -> dict[str, float | int]:
    """Compute aggregate statistics from path characteristics."""

    if not characteristics:
        return {}

    # Terminal type counts
    terminal_counts = Counter(c.terminal_type for c in characteristics)
    total = len(characteristics)

    # Path length statistics
    path_lens = [c.path_len for c in characteristics]

    # Convergence depth statistics (cycles only)
    convergence_depths = [c.convergence_depth for c in characteristics if c.convergence_depth is not None]

    # HALT depth statistics (halts only)
    halt_depths = [c.halt_depth for c in characteristics if c.halt_depth is not None]

    # Branching statistics
    mean_outdegrees = [c.mean_outdegree for c in characteristics]
    min_outdegrees = [c.min_outdegree for c in characteristics]
    bottleneck_depths = [c.bottleneck_depth for c in characteristics]

    # Fragmentation indicators
    early_halt_count = sum(1 for c in characteristics if c.early_halt)
    rapid_convergence_count = sum(1 for c in characteristics if c.rapid_convergence)

    return {
        # Sample size
        "total_samples": total,

        # Terminal type distribution
        "halt_count": terminal_counts.get("HALT", 0),
        "cycle_count": terminal_counts.get("CYCLE", 0),
        "max_steps_count": terminal_counts.get("MAX_STEPS", 0),
        "halt_pct": 100.0 * terminal_counts.get("HALT", 0) / total,
        "cycle_pct": 100.0 * terminal_counts.get("CYCLE", 0) / total,

        # Path length statistics
        "mean_path_len": float(np.mean(path_lens)),
        "median_path_len": float(np.median(path_lens)),
        "p25_path_len": float(np.percentile(path_lens, 25)),
        "p75_path_len": float(np.percentile(path_lens, 75)),
        "max_path_len": int(np.max(path_lens)),

        # Convergence depth (cycles only)
        "mean_convergence_depth": float(np.mean(convergence_depths)) if convergence_depths else 0.0,
        "median_convergence_depth": float(np.median(convergence_depths)) if convergence_depths else 0.0,
        "p25_convergence_depth": float(np.percentile(convergence_depths, 25)) if convergence_depths else 0.0,
        "p75_convergence_depth": float(np.percentile(convergence_depths, 75)) if convergence_depths else 0.0,

        # HALT depth (halts only)
        "mean_halt_depth": float(np.mean(halt_depths)) if halt_depths else 0.0,
        "median_halt_depth": float(np.median(halt_depths)) if halt_depths else 0.0,
        "p25_halt_depth": float(np.percentile(halt_depths, 25)) if halt_depths else 0.0,
        "p75_halt_depth": float(np.percentile(halt_depths, 75)) if halt_depths else 0.0,

        # Branching statistics
        "mean_mean_outdegree": float(np.mean(mean_outdegrees)),
        "mean_min_outdegree": float(np.mean(min_outdegrees)),
        "mean_bottleneck_depth": float(np.mean(bottleneck_depths)),

        # Fragmentation indicators
        "early_halt_count": early_halt_count,
        "early_halt_pct": 100.0 * early_halt_count / total,
        "rapid_convergence_count": rapid_convergence_count,
        "rapid_convergence_pct": 100.0 * rapid_convergence_count / total,
    }


def compute_depth_distributions(
    characteristics: list[PathCharacteristics],
) -> tuple[dict[int, int], dict[int, int]]:
    """Compute histograms of convergence depths and halt depths."""

    convergence_hist: dict[int, int] = defaultdict(int)
    halt_hist: dict[int, int] = defaultdict(int)

    for c in characteristics:
        if c.convergence_depth is not None:
            convergence_hist[c.convergence_depth] += 1
        if c.halt_depth is not None:
            halt_hist[c.halt_depth] += 1

    return dict(convergence_hist), dict(halt_hist)


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Analyze path characteristics to understand fragmentation vs concentration mechanisms."
    )
    parser.add_argument("--n", type=int, required=True, help="N for fixed N-link rule")
    parser.add_argument("--num", type=int, default=1000, help="Number of samples to draw (default: 1000)")
    parser.add_argument("--seed0", type=int, default=0, help="First RNG seed (default: 0)")
    parser.add_argument(
        "--min-outdegree",
        type=int,
        default=50,
        help="When choosing start page, require out_degree >= this (default: 50)",
    )
    parser.add_argument("--max-steps", type=int, default=5000, help="Stop after this many steps (default: 5000)")
    parser.add_argument(
        "--tag",
        type=str,
        default="",
        help="Optional tag for output filename (e.g., 'mechanism_test')",
    )

    args = parser.parse_args()

    if args.n <= 0:
        raise SystemExit("--n must be >= 1")
    if args.num <= 0:
        raise SystemExit("--num must be >= 1")

    print(f"=== Path Characteristics Analysis for N={args.n} ===")
    print(f"Samples: {args.num}")
    print(f"Min outdegree: {args.min_outdegree}")
    print(f"Max steps: {args.max_steps}")
    print()

    # Load data
    print(f"Using nlink data: {NLINK_PATH}")
    page_ids, next_ids, out_degree = _load_successor_arrays(args.n)

    # Sample traces
    characteristics: list[PathCharacteristics] = []

    t0 = time.time()
    for i in range(args.num):
        seed = int(args.seed0 + i)
        rng = np.random.default_rng(seed)
        start = _choose_start_page(
            rng,
            page_ids,
            next_ids,
            out_degree,
            min_outdegree=int(args.min_outdegree),
        )

        char = trace_with_characteristics(
            start_page_id=start,
            sorted_page_ids=page_ids,
            next_ids=next_ids,
            out_degree=out_degree,
            max_steps=int(args.max_steps),
        )

        # Set seed
        char = PathCharacteristics(
            seed=seed,
            start_page_id=char.start_page_id,
            terminal_type=char.terminal_type,
            path_len=char.path_len,
            steps=char.steps,
            transient_len=char.transient_len,
            cycle_len=char.cycle_len,
            convergence_depth=char.convergence_depth,
            halt_depth=char.halt_depth,
            mean_outdegree=char.mean_outdegree,
            min_outdegree=char.min_outdegree,
            bottleneck_depth=char.bottleneck_depth,
            early_halt=char.early_halt,
            rapid_convergence=char.rapid_convergence,
        )

        characteristics.append(char)

        if (i + 1) % 100 == 0 or (i + 1) == args.num:
            dt = time.time() - t0
            rate = (i + 1) / max(dt, 1e-9)
            print(f"Sampled {i+1}/{args.num} traces ({rate:.1f} traces/sec)")

    # Compute summary statistics
    print()
    print("Computing summary statistics...")
    summary = compute_summary_statistics(characteristics)

    # Compute depth distributions
    convergence_hist, halt_hist = compute_depth_distributions(characteristics)

    # Save outputs
    ANALYSIS_DIR.mkdir(parents=True, exist_ok=True)

    tag_suffix = f"_{args.tag}" if args.tag else ""
    base_name = f"path_characteristics_n={args.n}{tag_suffix}"

    # 1. Per-sample detailed metrics
    details_path = ANALYSIS_DIR / f"{base_name}_details.tsv"
    header = "\t".join([
        "seed", "start_page_id", "terminal_type", "path_len", "steps",
        "transient_len", "cycle_len", "convergence_depth", "halt_depth",
        "mean_outdegree", "min_outdegree", "bottleneck_depth",
        "early_halt", "rapid_convergence"
    ])
    lines = [header]
    for c in characteristics:
        lines.append("\t".join([
            str(c.seed),
            str(c.start_page_id),
            c.terminal_type,
            str(c.path_len),
            str(c.steps),
            "" if c.transient_len is None else str(c.transient_len),
            "" if c.cycle_len is None else str(c.cycle_len),
            "" if c.convergence_depth is None else str(c.convergence_depth),
            "" if c.halt_depth is None else str(c.halt_depth),
            f"{c.mean_outdegree:.2f}",
            str(c.min_outdegree),
            str(c.bottleneck_depth),
            "1" if c.early_halt else "0",
            "1" if c.rapid_convergence else "0",
        ]))
    details_path.write_text("\n".join(lines), encoding="utf-8")
    print(f"Saved detailed metrics: {details_path}")

    # 2. Summary statistics
    summary_path = ANALYSIS_DIR / f"{base_name}_summary.tsv"
    summary_lines = ["metric\tvalue"]
    for key, value in sorted(summary.items()):
        if isinstance(value, float):
            summary_lines.append(f"{key}\t{value:.3f}")
        else:
            summary_lines.append(f"{key}\t{value}")
    summary_path.write_text("\n".join(summary_lines), encoding="utf-8")
    print(f"Saved summary statistics: {summary_path}")

    # 3. Depth distributions
    depth_dist_path = ANALYSIS_DIR / f"{base_name}_depth_distributions.tsv"
    depth_lines = ["depth\tconvergence_count\thalt_count"]
    all_depths = sorted(set(convergence_hist.keys()) | set(halt_hist.keys()))
    for depth in all_depths:
        depth_lines.append(f"{depth}\t{convergence_hist.get(depth, 0)}\t{halt_hist.get(depth, 0)}")
    depth_dist_path.write_text("\n".join(depth_lines), encoding="utf-8")
    print(f"Saved depth distributions: {depth_dist_path}")

    # Print summary
    print()
    print("=== Summary Statistics ===")
    print(f"Total samples: {summary['total_samples']}")
    print(f"HALT rate: {summary['halt_pct']:.1f}% ({summary['halt_count']} samples)")
    print(f"CYCLE rate: {summary['cycle_pct']:.1f}% ({summary['cycle_count']} samples)")
    print()
    print(f"Mean path length: {summary['mean_path_len']:.1f}")
    print(f"Median path length: {summary['median_path_len']:.1f}")
    print()
    print(f"Mean convergence depth (cycles): {summary['mean_convergence_depth']:.1f}")
    print(f"Median convergence depth (cycles): {summary['median_convergence_depth']:.1f}")
    print()
    print(f"Mean HALT depth (halts): {summary['mean_halt_depth']:.1f}")
    print(f"Median HALT depth (halts): {summary['median_halt_depth']:.1f}")
    print()
    print(f"Early HALT rate (<10 steps): {summary['early_halt_pct']:.1f}% ({summary['early_halt_count']} samples)")
    print(f"Rapid convergence rate (<50 steps): {summary['rapid_convergence_pct']:.1f}% ({summary['rapid_convergence_count']} samples)")
    print()
    print(f"Mean avg outdegree along path: {summary['mean_mean_outdegree']:.1f}")
    print(f"Mean min outdegree (bottleneck): {summary['mean_min_outdegree']:.1f}")
    print(f"Mean bottleneck depth: {summary['mean_bottleneck_depth']:.1f}")


if __name__ == "__main__":
    main()
