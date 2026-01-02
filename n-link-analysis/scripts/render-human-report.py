#!/usr/bin/env python3
"""Render a human-facing Markdown report + charts from analysis TSV artifacts.

Inputs (expected in data/wikipedia/processed/analysis/):
- branch_trunkiness_dashboard_n=5_*.tsv
- dominance_collapse_dashboard_n=5_*.tsv
- dominant_upstream_chain_n=5_from=*.tsv (optional; a few will be plotted if present)

Outputs (committed to repo):
- n-link-analysis/report/overview.md
- n-link-analysis/report/assets/*.png

Rationale: keep `data/**/analysis/**` gitignored, but publish lightweight, human-facing
summaries inside the repo.

This script uses the _core.report_engine module for the core logic.
"""

from __future__ import annotations

import argparse
from pathlib import Path

from _core.report_engine import generate_report


REPO_ROOT = Path(__file__).resolve().parents[2]
ANALYSIS_DIR = REPO_ROOT / "data" / "wikipedia" / "processed" / "analysis"
REPORT_DIR = REPO_ROOT / "n-link-analysis" / "report"


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--tag",
        default="bootstrap_2025-12-30",
        help="Which dashboard tag to prefer when multiple exist.",
    )
    args = parser.parse_args()

    result = generate_report(
        analysis_dir=ANALYSIS_DIR,
        report_dir=REPORT_DIR,
        tag=args.tag,
        repo_root=REPO_ROOT,
        verbose=True,
    )

    print(f"Generated {len(result.figures)} figures")
    print(f"Elapsed: {result.elapsed_seconds:.1f}s")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
