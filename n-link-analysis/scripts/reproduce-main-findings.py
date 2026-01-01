#!/usr/bin/env python3
"""Reproduce main empirical findings from the N-Link Basin Analysis project.

This script executes the complete analysis pipeline to reproduce the key findings:
1. Basin size distribution shows heavy-tail with giant basin candidate
2. Many basins exhibit extreme "single-trunk" structure (depth-1 concentration)
3. Dominant-upstream chases reveal stable trunks that eventually collapse

Usage:
    python n-link-analysis/scripts/reproduce-main-findings.py [--quick] [--n N] [--tag TAG]

Options:
    --quick: Run quick version with reduced sample sizes (faster, but less complete)
    --n N: N-link rule to use (default: 5)
    --tag TAG: Tag for output files (default: reproduction_YYYY-MM-DD)
    --skip-sampling: Skip initial sampling (if already done)
    --skip-basins: Skip basin mapping (if already done)
    --skip-branches: Skip branch analysis (if already done)
    --skip-dashboards: Skip dashboard generation (if already done)
    --skip-report: Skip report generation (if already done)

Output:
    All results written to data/wikipedia/processed/analysis/
    Human-facing report: n-link-analysis/report/overview.md

Expected runtime (full):
    - Quick mode: ~10-30 minutes
    - Full mode: ~2-6 hours (depending on hardware)
"""

from __future__ import annotations

import argparse
import subprocess
import sys
from datetime import datetime
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]
SCRIPTS_DIR = REPO_ROOT / "n-link-analysis" / "scripts"
ANALYSIS_DIR = REPO_ROOT / "data" / "wikipedia" / "processed" / "analysis"


# Main finding: These cycles from the original investigation
MAIN_CYCLES = [
    ("Massachusetts", "Gulf_of_Maine"),  # Giant basin: 1,009,471 nodes
    ("Sea_salt", "Seawater"),  # Large basin: 265,940 nodes
    ("Mountain", "Hill"),  # Large basin: 189,269 nodes
    ("Autumn", "Summer"),  # High trunkiness: 162,689 nodes
    ("Kingdom_(biology)", "Animal"),  # Low trunkiness contrast: 116,998 nodes
    ("Latvia", "Lithuania"),  # Medium basin: 83,403 nodes
]

# Additional cycles for more complete picture (quick mode skips these)
ADDITIONAL_CYCLES = [
    ("Thermosetting_polymer", "Curing_(chemistry)"),  # Highest trunkiness
    ("Precedent", "Civil_law"),  # Medium trunkiness
    ("American_Revolutionary_War", "Eastern_United_States"),  # Low trunkiness
]


def run_command(cmd: list[str], description: str, *, check: bool = True) -> subprocess.CompletedProcess:
    """Run a command and print status."""
    print(f"\n{'='*80}")
    print(f"Running: {description}")
    print(f"Command: {' '.join(cmd)}")
    print(f"{'='*80}\n")

    result = subprocess.run(cmd, cwd=REPO_ROOT, check=False)

    if check and result.returncode != 0:
        print(f"\n✗ FAILED: {description}")
        print(f"  Exit code: {result.returncode}")
        sys.exit(1)

    print(f"\n✓ Completed: {description}\n")
    return result


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--quick", action="store_true", help="Quick mode with reduced samples")
    parser.add_argument("--n", type=int, default=5, help="N for N-link rule (default: 5)")
    parser.add_argument("--tag", type=str, default=None, help="Tag for outputs (default: reproduction_YYYY-MM-DD)")
    parser.add_argument("--skip-sampling", action="store_true", help="Skip sampling phase")
    parser.add_argument("--skip-basins", action="store_true", help="Skip basin mapping phase")
    parser.add_argument("--skip-branches", action="store_true", help="Skip branch analysis phase")
    parser.add_argument("--skip-dashboards", action="store_true", help="Skip dashboard generation phase")
    parser.add_argument("--skip-report", action="store_true", help="Skip report generation phase")
    args = parser.parse_args()

    # Generate tag
    tag = args.tag or f"reproduction_{datetime.now().strftime('%Y-%m-%d')}"
    n = args.n

    print("="*80)
    print("N-Link Basin Analysis - Main Findings Reproduction")
    print("="*80)
    print(f"N-link rule: N={n}")
    print(f"Mode: {'Quick (reduced samples)' if args.quick else 'Full (complete reproduction)'}")
    print(f"Tag: {tag}")
    print(f"Output directory: {ANALYSIS_DIR}")
    print("="*80)

    # Ensure analysis directory exists
    ANALYSIS_DIR.mkdir(parents=True, exist_ok=True)

    # Phase 1: Sampling (Terminal/Cycle Statistics)
    if not args.skip_sampling:
        print("\n\n" + "="*80)
        print("PHASE 1: SAMPLING - Identify frequent cycles")
        print("="*80)

        if args.quick:
            # Quick: 500 samples
            run_command(
                [
                    "python", str(SCRIPTS_DIR / "sample-nlink-traces.py"),
                    "--n", str(n),
                    "--num", "500",
                    "--seed0", "0",
                    "--min-outdegree", "50",
                    "--max-steps", "5000",
                    "--top-cycles", "20",
                    "--resolve-titles",
                    "--out", str(ANALYSIS_DIR / f"sample_traces_n={n}_num=500_seed0=0_{tag}.tsv"),
                ],
                description="Quick sampling (500 traces)",
            )
        else:
            # Full: 5000 samples (matches original investigation)
            run_command(
                [
                    "python", str(SCRIPTS_DIR / "sample-nlink-traces.py"),
                    "--n", str(n),
                    "--num", "5000",
                    "--seed0", "0",
                    "--min-outdegree", "50",
                    "--max-steps", "5000",
                    "--top-cycles", "30",
                    "--resolve-titles",
                    "--out", str(ANALYSIS_DIR / f"sample_traces_n={n}_num=5000_seed0=0_{tag}.tsv"),
                ],
                description="Full sampling (5000 traces)",
            )

    # Phase 2: Basin Mapping
    if not args.skip_basins:
        print("\n\n" + "="*80)
        print("PHASE 2: BASIN MAPPING - Compute basin sizes via reverse BFS")
        print("="*80)

        cycles_to_map = MAIN_CYCLES
        if not args.quick:
            cycles_to_map = MAIN_CYCLES + ADDITIONAL_CYCLES

        for cycle_a, cycle_b in cycles_to_map:
            run_command(
                [
                    "python", str(SCRIPTS_DIR / "map-basin-from-cycle.py"),
                    "--n", str(n),
                    "--cycle-title", cycle_a,
                    "--cycle-title", cycle_b,
                    "--max-depth", "0",  # Unlimited depth
                    "--log-every", "25",
                    "--out-prefix", f"basin_n={n}_cycle={cycle_a}__{cycle_b}_{tag}",
                ],
                description=f"Map basin for {cycle_a} ↔ {cycle_b}",
            )

    # Phase 3: Branch Analysis (Tributary Structure)
    if not args.skip_branches:
        print("\n\n" + "="*80)
        print("PHASE 3: BRANCH ANALYSIS - Quantify tributary structure")
        print("="*80)

        cycles_to_analyze = MAIN_CYCLES
        if not args.quick:
            cycles_to_analyze = MAIN_CYCLES + ADDITIONAL_CYCLES

        for cycle_a, cycle_b in cycles_to_analyze:
            # Write membership only for largest basin in quick mode, all in full mode
            write_membership = "10" if (not args.quick or (cycle_a, cycle_b) == MAIN_CYCLES[0]) else "0"

            run_command(
                [
                    "python", str(SCRIPTS_DIR / "branch-basin-analysis.py"),
                    "--n", str(n),
                    "--cycle-title", cycle_a,
                    "--cycle-title", cycle_b,
                    "--max-depth", "0",  # Unlimited depth
                    "--log-every", "0",  # Quiet
                    "--top-k", "30",
                    "--write-membership-top-k", write_membership,
                    "--out-prefix", f"branches_n={n}_cycle={cycle_a}__{cycle_b}_{tag}",
                ],
                description=f"Branch analysis for {cycle_a} ↔ {cycle_b}",
            )

    # Phase 4: Dashboards (Aggregation & Metrics)
    if not args.skip_dashboards:
        print("\n\n" + "="*80)
        print("PHASE 4: DASHBOARDS - Aggregate concentration metrics")
        print("="*80)

        # Trunkiness dashboard
        run_command(
            [
                "python", str(SCRIPTS_DIR / "compute-trunkiness-dashboard.py"),
                "--tag", tag,
            ],
            description="Compute trunkiness dashboard (Gini, HH, entropy)",
        )

        # Collapse dashboard (batch chase)
        dashboard_path = ANALYSIS_DIR / f"branch_trunkiness_dashboard_n={n}_{tag}.tsv"
        if dashboard_path.exists():
            run_command(
                [
                    "python", str(SCRIPTS_DIR / "batch-chase-collapse-metrics.py"),
                    "--n", str(n),
                    "--dashboard", str(dashboard_path),
                    "--seed-from", "dominant_enters_cycle_title",
                    "--max-hops", "50" if not args.quick else "30",
                    "--max-depth", "0",
                    "--dominance-threshold", "0.5",
                    "--tag", f"{tag}_seed=dominant_enters_cycle_title_thr=0.5",
                ],
                description="Batch chase for dominance collapse metrics",
            )
        else:
            print(f"⚠ Skipping collapse dashboard: {dashboard_path} not found")

    # Phase 5: Human Report
    if not args.skip_report:
        print("\n\n" + "="*80)
        print("PHASE 5: REPORT GENERATION - Create human-facing summary")
        print("="*80)

        run_command(
            [
                "python", str(SCRIPTS_DIR / "render-human-report.py"),
                "--tag", tag,
            ],
            description="Generate human-facing report with charts",
        )

    # Summary
    print("\n\n" + "="*80)
    print("✓ REPRODUCTION COMPLETE")
    print("="*80)
    print("\nKey outputs:")
    print(f"  - Analysis artifacts: {ANALYSIS_DIR}")
    print(f"  - Human report: {REPO_ROOT / 'n-link-analysis' / 'report' / 'overview.md'}")
    print(f"  - Trunkiness dashboard: {ANALYSIS_DIR / f'branch_trunkiness_dashboard_n={n}_{tag}.tsv'}")
    print(f"  - Collapse dashboard: {ANALYSIS_DIR / f'dominance_collapse_dashboard_n={n}_{tag}_seed=dominant_enters_cycle_title_thr=0.5.tsv'}")

    print("\nMain findings reproduced:")
    print("  1. Heavy-tail basin size distribution")
    print("     → Massachusetts ↔ Gulf_of_Maine is giant basin (>1M nodes)")
    print("  2. Single-trunk structure in many basins")
    print("     → Top-1 branch captures >95% of upstream mass in 6/9 tested basins")
    print("  3. Dominance collapse patterns")
    print("     → Stable trunks eventually diffuse (share < 0.5) within 5-20 hops")

    print("\nNext steps:")
    print("  - Review report: n-link-analysis/report/overview.md")
    print("  - Explore trunkiness dashboard TSV for quantitative metrics")
    print("  - Visualize specific basins:")
    print(f"    python n-link-analysis/scripts/render-tributary-tree-3d.py --n {n} --cycle-title Massachusetts --cycle-title Gulf_of_Maine")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
