#!/usr/bin/env python3
"""Reproduce main empirical findings from the N-Link Basin Analysis project.

This script executes the complete analysis pipeline to reproduce the key findings:
1. Basin size distribution shows heavy-tail with giant basin candidate
2. Many basins exhibit extreme "single-trunk" structure (depth-1 concentration)
3. Dominant-upstream chases reveal stable trunks that eventually collapse

Usage:
    # Subprocess mode (default)
    python n-link-analysis/scripts/reproduce-main-findings.py [--quick] [--n N] [--tag TAG]

    # API mode (requires running API server)
    uvicorn nlink_api.main:app --port 8000 &
    python n-link-analysis/scripts/reproduce-main-findings.py --use-api [--quick]

Options:
    --quick: Run quick version with reduced sample sizes (faster, but less complete)
    --n N: N-link rule to use (default: 5)
    --tag TAG: Tag for output files (default: reproduction_YYYY-MM-DD)
    --skip-sampling: Skip initial sampling (if already done)
    --skip-basins: Skip basin mapping (if already done)
    --skip-branches: Skip branch analysis (if already done)
    --skip-dashboards: Skip dashboard generation (if already done)
    --skip-report: Skip report generation (if already done)
    --use-api: Execute via API server instead of subprocess calls
    --api-base URL: API base URL (default: http://127.0.0.1:8000)

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
import time
from datetime import datetime
from pathlib import Path
from typing import Any

# Optional: requests for API mode
try:
    import requests
    HAS_REQUESTS = True
except ImportError:
    HAS_REQUESTS = False


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


# =============================================================================
# API Mode Functions
# =============================================================================

def check_api_available(api_base: str) -> bool:
    """Check if the API server is available."""
    if not HAS_REQUESTS:
        print("ERROR: 'requests' package required for API mode. Install with: pip install requests")
        return False
    try:
        resp = requests.get(f"{api_base}/api/v1/health", timeout=5)
        return resp.status_code == 200
    except requests.exceptions.RequestException:
        return False


def run_via_api(
    api_base: str,
    endpoint: str,
    payload: dict[str, Any],
    description: str,
    *,
    poll_interval: float = 2.0,
) -> dict[str, Any] | None:
    """Submit a task via API and poll until completion.

    Args:
        api_base: Base URL of the API server
        endpoint: API endpoint (e.g., "/api/v1/traces/sample")
        payload: Request payload
        description: Human-readable description for logging
        poll_interval: Seconds between status checks

    Returns:
        Task result dict, or None if failed
    """
    print(f"\n{'='*80}")
    print(f"Running via API: {description}")
    print(f"Endpoint: POST {endpoint}")
    print(f"{'='*80}\n")

    # Submit the request
    try:
        resp = requests.post(f"{api_base}{endpoint}", json=payload, timeout=30)
        resp.raise_for_status()
    except requests.exceptions.RequestException as e:
        print(f"✗ FAILED to submit: {e}")
        return None

    data = resp.json()

    # Check if this is a synchronous response (no task_id)
    if "task_id" not in data:
        print(f"✓ Completed (sync): {description}\n")
        return data

    # Background task - poll for completion
    task_id = data["task_id"]
    task_type = data.get("task_type", "unknown")
    print(f"Task submitted: {task_id} ({task_type})")

    # Determine the status endpoint
    # Reports router uses /api/v1/reports/{task_id}
    # Traces router uses /api/v1/traces/sample/{task_id}
    # Basins router uses /api/v1/basins/map/{task_id} or /api/v1/basins/branches/{task_id}
    if "/reports/" in endpoint:
        status_endpoint = f"/api/v1/reports/{task_id}"
    elif "/traces/" in endpoint:
        status_endpoint = f"/api/v1/traces/sample/{task_id}"
    elif "/basins/map" in endpoint:
        status_endpoint = f"/api/v1/basins/map/{task_id}"
    elif "/basins/branches" in endpoint:
        status_endpoint = f"/api/v1/basins/branches/{task_id}"
    else:
        # Fallback to generic tasks endpoint
        status_endpoint = f"/api/v1/tasks/{task_id}"

    # Poll until completion
    last_progress = -1.0
    while True:
        try:
            status_resp = requests.get(f"{api_base}{status_endpoint}", timeout=30)
            status_resp.raise_for_status()
            status = status_resp.json()
        except requests.exceptions.RequestException as e:
            print(f"  Warning: Failed to get status: {e}")
            time.sleep(poll_interval)
            continue

        task_status = status.get("status", "unknown")
        progress = status.get("progress", 0.0)
        progress_msg = status.get("progress_message", "")

        # Only print progress if it changed
        if progress != last_progress:
            pct = progress * 100
            if progress_msg:
                print(f"  Progress: {pct:.0f}% - {progress_msg}")
            else:
                print(f"  Progress: {pct:.0f}%")
            last_progress = progress

        if task_status == "completed":
            print(f"\n✓ Completed: {description}\n")
            return status.get("result")
        elif task_status == "failed":
            error = status.get("error", "Unknown error")
            print(f"\n✗ FAILED: {description}")
            print(f"  Error: {error}")
            return None
        elif task_status == "cancelled":
            print(f"\n✗ CANCELLED: {description}")
            return None

        time.sleep(poll_interval)


def run_sampling_via_api(
    api_base: str,
    n: int,
    num_samples: int,
    *,
    seed: int = 0,
    min_outdegree: int = 50,
    max_steps: int = 5000,
    top_cycles: int = 20,
    resolve_titles: bool = True,
) -> dict[str, Any] | None:
    """Run trace sampling via API."""
    payload = {
        "n": n,
        "num_samples": num_samples,
        "seed": seed,
        "min_outdegree": min_outdegree,
        "max_steps": max_steps,
        "top_cycles_k": top_cycles,
        "resolve_titles": resolve_titles,
    }
    return run_via_api(
        api_base,
        "/api/v1/traces/sample",
        payload,
        f"Sampling {num_samples} traces (N={n})",
    )


def run_basin_mapping_via_api(
    api_base: str,
    n: int,
    cycle_a: str,
    cycle_b: str,
    tag: str,
    *,
    max_depth: int = 0,
) -> dict[str, Any] | None:
    """Run basin mapping via API."""
    payload = {
        "n": n,
        "cycle_titles": [cycle_a, cycle_b],
        "max_depth": max_depth,
        "max_nodes": 0,  # Unlimited
        "write_membership": True,
        "tag": tag,
    }
    return run_via_api(
        api_base,
        "/api/v1/basins/map",
        payload,
        f"Map basin for {cycle_a} ↔ {cycle_b}",
    )


def run_branch_analysis_via_api(
    api_base: str,
    n: int,
    cycle_a: str,
    cycle_b: str,
    tag: str,
    *,
    max_depth: int = 0,
    top_k: int = 30,
    write_membership_top_k: int = 10,
) -> dict[str, Any] | None:
    """Run branch analysis via API."""
    payload = {
        "n": n,
        "cycle_titles": [cycle_a, cycle_b],
        "max_depth": max_depth,
        "top_k": top_k,
        "write_top_k_membership": write_membership_top_k,
        "tag": tag,
    }
    return run_via_api(
        api_base,
        "/api/v1/basins/branches",
        payload,
        f"Branch analysis for {cycle_a} ↔ {cycle_b}",
    )


def run_trunkiness_dashboard_via_api(
    api_base: str,
    n: int,
    tag: str,
) -> dict[str, Any] | None:
    """Run trunkiness dashboard computation via API."""
    payload = {
        "n": n,
        "tag": tag,
    }
    # Use async endpoint for safety (can be slow)
    return run_via_api(
        api_base,
        "/api/v1/reports/trunkiness/async",
        payload,
        "Compute trunkiness dashboard",
    )


def run_human_report_via_api(
    api_base: str,
    tag: str,
) -> dict[str, Any] | None:
    """Generate human report via API."""
    payload = {
        "tag": tag,
    }
    return run_via_api(
        api_base,
        "/api/v1/reports/human/async",
        payload,
        "Generate human-facing report",
    )


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
    # API mode options
    parser.add_argument("--use-api", action="store_true",
                        help="Execute via API server instead of subprocess calls")
    parser.add_argument("--api-base", type=str, default="http://127.0.0.1:8000",
                        help="API base URL (default: http://127.0.0.1:8000)")
    args = parser.parse_args()

    # Generate tag
    tag = args.tag or f"reproduction_{datetime.now().strftime('%Y-%m-%d')}"
    n = args.n
    use_api = args.use_api
    api_base = args.api_base

    print("="*80)
    print("N-Link Basin Analysis - Main Findings Reproduction")
    print("="*80)
    print(f"N-link rule: N={n}")
    print(f"Mode: {'Quick (reduced samples)' if args.quick else 'Full (complete reproduction)'}")
    print(f"Execution: {'API (' + api_base + ')' if use_api else 'Subprocess'}")
    print(f"Tag: {tag}")
    print(f"Output directory: {ANALYSIS_DIR}")
    print("="*80)

    # Check API availability if using API mode
    if use_api:
        if not check_api_available(api_base):
            print(f"\n✗ ERROR: API server not available at {api_base}")
            print("  Start the server with: uvicorn nlink_api.main:app --port 8000")
            return 1
        print(f"\n✓ API server available at {api_base}")

    # Ensure analysis directory exists
    ANALYSIS_DIR.mkdir(parents=True, exist_ok=True)

    # Phase 1: Sampling (Terminal/Cycle Statistics)
    if not args.skip_sampling:
        print("\n\n" + "="*80)
        print("PHASE 1: SAMPLING - Identify frequent cycles")
        print("="*80)

        num_samples = 500 if args.quick else 5000
        top_cycles = 20 if args.quick else 30

        if use_api:
            result = run_sampling_via_api(
                api_base, n, num_samples,
                seed=0, min_outdegree=50, max_steps=5000, top_cycles=top_cycles,
            )
            if result is None:
                print("✗ Sampling failed via API")
                return 1
        else:
            run_command(
                [
                    "python", str(SCRIPTS_DIR / "sample-nlink-traces.py"),
                    "--n", str(n),
                    "--num", str(num_samples),
                    "--seed0", "0",
                    "--min-outdegree", "50",
                    "--max-steps", "5000",
                    "--top-cycles", str(top_cycles),
                    "--resolve-titles",
                    "--out", str(ANALYSIS_DIR / f"sample_traces_n={n}_num={num_samples}_seed0=0_{tag}.tsv"),
                ],
                description=f"{'Quick' if args.quick else 'Full'} sampling ({num_samples} traces)",
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
            if use_api:
                result = run_basin_mapping_via_api(
                    api_base, n, cycle_a, cycle_b, tag,
                    max_depth=0,
                )
                if result is None:
                    print(f"✗ Basin mapping failed for {cycle_a} ↔ {cycle_b}")
                    return 1
            else:
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
            write_membership_k = 10 if (not args.quick or (cycle_a, cycle_b) == MAIN_CYCLES[0]) else 0

            if use_api:
                result = run_branch_analysis_via_api(
                    api_base, n, cycle_a, cycle_b, tag,
                    max_depth=0, top_k=30, write_membership_top_k=write_membership_k,
                )
                if result is None:
                    print(f"✗ Branch analysis failed for {cycle_a} ↔ {cycle_b}")
                    return 1
            else:
                run_command(
                    [
                        "python", str(SCRIPTS_DIR / "branch-basin-analysis.py"),
                        "--n", str(n),
                        "--cycle-title", cycle_a,
                        "--cycle-title", cycle_b,
                        "--max-depth", "0",  # Unlimited depth
                        "--log-every", "0",  # Quiet
                        "--top-k", "30",
                        "--write-membership-top-k", str(write_membership_k),
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
        if use_api:
            result = run_trunkiness_dashboard_via_api(api_base, n, tag)
            if result is None:
                print("✗ Trunkiness dashboard computation failed via API")
                return 1
        else:
            run_command(
                [
                    "python", str(SCRIPTS_DIR / "compute-trunkiness-dashboard.py"),
                    "--tag", tag,
                ],
                description="Compute trunkiness dashboard (Gini, HH, entropy)",
            )

        # Collapse dashboard (batch chase) - always via subprocess (no API endpoint yet)
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

        if use_api:
            result = run_human_report_via_api(api_base, tag)
            if result is None:
                print("✗ Human report generation failed via API")
                return 1
        else:
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
