#!/usr/bin/env python3
"""Analysis harness to run all N-link analysis scripts with sensible defaults.

This script orchestrates the complete analysis pipeline for a given N-link rule,
running all scripts that require specific inputs with reasonable defaults.

Usage:
    python run-analysis-harness.py --n 5 [--tag harness_2026-01-01] [--skip-existing]
"""

from __future__ import annotations

import argparse
import subprocess
import sys
import time
from pathlib import Path
from datetime import date

REPO_ROOT = Path(__file__).resolve().parents[2]
SCRIPTS_DIR = REPO_ROOT / "n-link-analysis" / "scripts"
ANALYSIS_DIR = REPO_ROOT / "data" / "wikipedia" / "processed" / "analysis"

# Known cycles from reproduce-main-findings.py
KNOWN_CYCLES = [
    ("Massachusetts", "Gulf_of_Maine"),
    ("Sea_salt", "Seawater"),
    ("Mountain", "Hill"),
    ("Autumn", "Summer"),
    ("Kingdom_(biology)", "Animal"),
    ("Latvia", "Lithuania"),
    ("Thermosetting_polymer", "Curing_(chemistry)"),
    ("Precedent", "Civil_law"),
    ("American_Revolutionary_War", "Eastern_United_States"),
]

def run_script(script_name: str, args: list[str], *, description: str) -> bool:
    """Run a script and return True if successful."""
    print(f"\n{'='*80}")
    print(f"Running: {script_name}")
    print(f"Description: {description}")
    print(f"Args: {' '.join(args)}")
    print(f"{'='*80}")

    script_path = SCRIPTS_DIR / script_name
    cmd = [sys.executable, str(script_path)] + args

    t0 = time.time()
    try:
        result = subprocess.run(cmd, check=True, capture_output=False)
        dt = time.time() - t0
        print(f"\n✓ SUCCESS ({dt:.1f}s)")
        return True
    except subprocess.CalledProcessError as e:
        dt = time.time() - t0
        print(f"\n✗ FAILED ({dt:.1f}s): {e}")
        return False
    except Exception as e:
        dt = time.time() - t0
        print(f"\n✗ ERROR ({dt:.1f}s): {e}")
        return False


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Run complete N-link analysis pipeline with sensible defaults",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument("--n", type=int, default=5, help="N for N-link rule (default: 5)")
    parser.add_argument(
        "--tag",
        type=str,
        default=f"harness_{date.today().isoformat()}",
        help="Tag for output files",
    )
    parser.add_argument(
        "--skip-existing",
        action="store_true",
        help="Skip scripts if output files already exist",
    )
    parser.add_argument(
        "--quick",
        action="store_true",
        help="Quick mode with reduced samples (fewer cycles, smaller samples)",
    )
    parser.add_argument(
        "--max-cycles",
        type=int,
        default=None,
        help="Maximum number of cycles to analyze (default: all 9, or 6 in quick mode)",
    )

    args = parser.parse_args()

    n = args.n
    tag = args.tag
    skip_existing = args.skip_existing
    quick = args.quick

    # Select cycles
    if quick:
        cycles = KNOWN_CYCLES[:6]  # Quick mode: first 6 cycles
    else:
        cycles = KNOWN_CYCLES  # Full mode: all 9 cycles

    if args.max_cycles:
        cycles = cycles[:args.max_cycles]

    ANALYSIS_DIR.mkdir(parents=True, exist_ok=True)

    print(f"\n{'='*80}")
    print(f"N-LINK ANALYSIS HARNESS")
    print(f"{'='*80}")
    print(f"N: {n}")
    print(f"Tag: {tag}")
    print(f"Cycles: {len(cycles)}")
    print(f"Quick mode: {quick}")
    print(f"Skip existing: {skip_existing}")
    print(f"{'='*80}\n")

    results = {}

    # ========================================================================
    # TIER 0: Validation & Sampling
    # ========================================================================

    # 1. Validate data dependencies
    results["validate-data-dependencies"] = run_script(
        "validate-data-dependencies.py",
        [],
        description="Validate all required data files exist",
    )

    # 2. Sample traces to identify frequent cycles
    sample_size = 100 if quick else 500
    results["sample-nlink-traces"] = run_script(
        "sample-nlink-traces.py",
        ["--n", str(n), "--num", str(sample_size), "--seed0", "0", "--resolve-titles"],
        description=f"Sample {sample_size} random traces to identify frequent cycles",
    )

    # 3. Trace a single path as sanity check
    results["trace-nlink-path"] = run_script(
        "trace-nlink-path.py",
        ["--n", str(n), "--seed", "42"],
        description="Trace single random path as sanity check",
    )

    # 4. Path characteristics analysis
    path_sample_size = 50 if quick else 200
    results["analyze-path-characteristics"] = run_script(
        "analyze-path-characteristics.py",
        ["--n", str(n), "--num", str(path_sample_size), "--tag", tag],
        description=f"Analyze {path_sample_size} path characteristics (convergence, bottlenecks)",
    )

    # ========================================================================
    # TIER 1: Basin Construction & Branch Analysis (per cycle)
    # ========================================================================

    for i, (title1, title2) in enumerate(cycles, 1):
        cycle_key = f"{title1}__{title2}"
        print(f"\n{'#'*80}")
        print(f"# CYCLE {i}/{len(cycles)}: {cycle_key}")
        print(f"{'#'*80}\n")

        # 5. Map basin from cycle
        map_basin_key = f"map-basin-{cycle_key}"
        results[map_basin_key] = run_script(
            "map-basin-from-cycle.py",
            [
                "--n", str(n),
                "--cycle-title", title1,
                "--cycle-title", title2,
                "--max-depth", "30" if quick else "0",
                "--log-every", "5",
                "--out-prefix", f"basin_n={n}_cycle={cycle_key}_{tag}",
            ],
            description=f"Map complete basin for {cycle_key}",
        )

        # 6. Branch analysis
        branch_key = f"branch-analysis-{cycle_key}"
        results[branch_key] = run_script(
            "branch-basin-analysis.py",
            [
                "--n", str(n),
                "--cycle-title", title1,
                "--cycle-title", title2,
                "--max-depth", "0",
                "--top-k", "50",
                "--log-every", "10",
                "--out-prefix", f"branches_n={n}_cycle={cycle_key}_{tag}",
            ],
            description=f"Quantify branch structure for {cycle_key}",
        )

        # 7. Chase dominant upstream
        chase_key = f"chase-dominant-{cycle_key}"
        results[chase_key] = run_script(
            "chase-dominant-upstream.py",
            [
                "--n", str(n),
                "--seed-title", title1,
                "--max-hops", "20" if quick else "40",
                "--dominance-threshold", "0.5",
            ],
            description=f"Chase dominant upstream trunk from {title1}",
        )

        # 8. Find preimages for cycle nodes
        preimages_key = f"find-preimages-{title1}"
        results[preimages_key] = run_script(
            "find-nlink-preimages.py",
            [
                "--n", str(n),
                "--target-title", title1,
                "--limit", "100",
            ],
            description=f"Find preimages for {title1}",
        )

    # ========================================================================
    # TIER 2: Aggregation & Dashboards
    # ========================================================================

    # 9. Compute trunkiness dashboard
    results["compute-trunkiness-dashboard"] = run_script(
        "compute-trunkiness-dashboard.py",
        ["--tag", tag, "--n", str(n), "--analysis-dir", str(ANALYSIS_DIR)],
        description="Aggregate concentration metrics across all cycles",
    )

    # 10. Batch chase collapse metrics
    dashboard_file = ANALYSIS_DIR / f"branch_trunkiness_dashboard_n={n}_{tag}.tsv"
    if dashboard_file.exists():
        results["batch-chase-collapse-metrics"] = run_script(
            "batch-chase-collapse-metrics.py",
            [
                "--n", str(n),
                "--dashboard", str(dashboard_file),
                "--seed-from", "dominant_enters_cycle_title",
                "--max-hops", "20" if quick else "40",
                "--dominance-threshold", "0.5",
                "--tag", tag,
            ],
            description="Measure dominance collapse patterns across cycles",
        )
    else:
        print(f"\n⚠ Skipping batch-chase-collapse-metrics: dashboard file not found")
        results["batch-chase-collapse-metrics"] = False

    # ========================================================================
    # TIER 3: Cross-N Comparisons (if multiple N values)
    # ========================================================================

    # 11. Compare across N (if we have data for multiple N values)
    # For now, skip unless user specifies

    # 12. Compare cycle evolution
    results["compare-cycle-evolution"] = run_script(
        "compare-cycle-evolution.py",
        ["--n-values", str(n)],
        description="Analyze cycle evolution and stability",
    )

    # 13. Analyze cycle link profiles
    results["analyze-cycle-link-profiles"] = run_script(
        "analyze-cycle-link-profiles.py",
        ["--max-n", str(n + 2)],
        description="Analyze link sequences of cycle pages",
    )

    # ========================================================================
    # TIER 4: Visualization & Reporting
    # ========================================================================

    # 14. Visualize mechanism comparison
    results["visualize-mechanism-comparison"] = run_script(
        "visualize-mechanism-comparison.py",
        [],
        description="Generate mechanism comparison charts",
    )

    # 15. Render human report
    results["render-human-report"] = run_script(
        "render-human-report.py",
        ["--tag", tag],
        description="Generate human-facing summary report with charts",
    )

    # 16. Render 3D tributary tree for top cycle (if not quick mode)
    if not quick and cycles:
        title1, title2 = cycles[0]  # Massachusetts ↔ Gulf_of_Maine
        results["render-tributary-tree-3d"] = run_script(
            "render-tributary-tree-3d.py",
            [
                "--n", str(n),
                "--cycle-title", title1,
                "--cycle-title", title2,
                "--top-k", "3",
                "--max-levels", "4",
                "--max-depth", "12",
            ],
            description=f"Render 3D tributary tree for {title1} ↔ {title2}",
        )

    # ========================================================================
    # SUMMARY
    # ========================================================================

    print(f"\n{'='*80}")
    print(f"ANALYSIS HARNESS SUMMARY")
    print(f"{'='*80}\n")

    total = len(results)
    succeeded = sum(1 for v in results.values() if v)
    failed = total - succeeded

    print(f"Total scripts run: {total}")
    print(f"Succeeded: {succeeded}")
    print(f"Failed: {failed}")
    print(f"\nSuccess rate: {100 * succeeded / total:.1f}%\n")

    if failed > 0:
        print("Failed scripts:")
        for name, success in results.items():
            if not success:
                print(f"  ✗ {name}")

    print(f"\n{'='*80}")
    print(f"All outputs saved to: {ANALYSIS_DIR}")
    print(f"Human report: n-link-analysis/report/overview.md")
    print(f"{'='*80}\n")

    sys.exit(0 if failed == 0 else 1)


if __name__ == "__main__":
    main()
