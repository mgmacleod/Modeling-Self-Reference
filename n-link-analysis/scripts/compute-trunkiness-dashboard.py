#!/usr/bin/env python3
"""Compute summary "trunkiness" metrics from branch-basin-analysis outputs.

Reads files like:
  data/wikipedia/processed/analysis/branches_n=5_cycle=..._branches_all.tsv
  data/wikipedia/processed/analysis/branches_n=5_cycle=..._branches_topk.tsv

Writes:
  data/wikipedia/processed/analysis/branch_trunkiness_dashboard_n=5_<tag>.tsv

This script uses the _core.dashboard_engine module for the core logic.
"""

from __future__ import annotations

import argparse
from pathlib import Path

import pandas as pd

from _core.dashboard_engine import compute_trunkiness_dashboard


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

    result = compute_trunkiness_dashboard(
        analysis_dir=Path(args.analysis_dir),
        n=args.n,
        tag=args.tag,
        write_output=True,
        verbose=True,
    )

    # Print a small preview
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
    rows = [
        {
            "cycle_key": s.cycle_key,
            "total_basin_nodes": s.total_basin_nodes,
            "n_branches": s.n_branches,
            "top1_share_total": s.top1_share_total,
            "effective_branches": s.effective_branches,
            "gini_branch_sizes": s.gini_branch_sizes,
            "dominant_entry_title": s.dominant_entry_title,
            "dominant_enters_cycle_title": s.dominant_enters_cycle_title,
        }
        for s in result.stats[:25]
    ]
    out_df = pd.DataFrame(rows)
    print(out_df[preview_cols].to_string(index=False))

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
