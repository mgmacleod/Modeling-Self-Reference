#!/usr/bin/env python3
"""Run complete analysis pipeline for a single cycle.

This is a focused harness for analyzing a specific cycle in detail.

Usage:
    # Using titles
    python run-single-cycle-analysis.py --n 5 --cycle-title Massachusetts --cycle-title "Gulf_of_Maine"

    # Using page IDs
    python run-single-cycle-analysis.py --n 5 --cycle-page-id 1645518 --cycle-page-id 714653
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
        description="Run complete analysis pipeline for a single cycle",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument("--n", type=int, default=5, help="N for N-link rule (default: 5)")
    parser.add_argument(
        "--cycle-title",
        type=str,
        action="append",
        default=[],
        help="Cycle node title (repeatable, must provide 2 for a 2-cycle)",
    )
    parser.add_argument(
        "--cycle-page-id",
        type=int,
        action="append",
        default=[],
        help="Cycle node page_id (repeatable, must provide 2 for a 2-cycle)",
    )
    parser.add_argument(
        "--tag",
        type=str,
        default=f"single_cycle_{date.today().isoformat()}",
        help="Tag for output files",
    )
    parser.add_argument(
        "--max-depth",
        type=int,
        default=0,
        help="Max basin depth (0 = unlimited)",
    )
    parser.add_argument(
        "--max-hops",
        type=int,
        default=25,
        help="Max dominant upstream chase hops",
    )
    parser.add_argument(
        "--top-k",
        type=int,
        default=50,
        help="Number of top branches to analyze",
    )
    parser.add_argument(
        "--render-3d",
        action="store_true",
        help="Generate 3D tributary tree visualization (slow)",
    )
    parser.add_argument(
        "--namespace",
        type=int,
        default=0,
        help="Namespace for title resolution (default: 0 = main articles)",
    )
    parser.add_argument(
        "--allow-redirects",
        action="store_true",
        help="Allow redirect pages when resolving titles",
    )
    parser.add_argument(
        "--write-membership",
        action="store_true",
        help="Write full basin membership to Parquet (large file)",
    )
    parser.add_argument(
        "--dominance-threshold",
        type=float,
        default=0.5,
        help="Stop dominant chase when share falls below this (default: 0.5)",
    )

    args = parser.parse_args()

    n = args.n
    tag = args.tag
    cycle_titles = args.cycle_title
    cycle_page_ids = args.cycle_page_id

    if not cycle_titles and not cycle_page_ids:
        print("ERROR: Must provide either --cycle-title or --cycle-page-id")
        sys.exit(1)

    ANALYSIS_DIR.mkdir(parents=True, exist_ok=True)

    # Build cycle key for filenames
    if cycle_titles:
        cycle_key = "__".join(cycle_titles)
        cycle_args = []
        for title in cycle_titles:
            cycle_args.extend(["--cycle-title", title])
        seed_title = cycle_titles[0]
    else:
        cycle_key = "__".join(str(pid) for pid in cycle_page_ids)
        cycle_args = []
        for pid in cycle_page_ids:
            cycle_args.extend(["--cycle-page-id", str(pid)])
        seed_title = None

    print(f"\n{'='*80}")
    print(f"SINGLE CYCLE ANALYSIS")
    print(f"{'='*80}")
    print(f"N: {n}")
    print(f"Cycle: {cycle_key}")
    print(f"Tag: {tag}")
    print(f"Max depth: {args.max_depth or 'unlimited'}")
    print(f"{'='*80}\n")

    results = {}

    # 1. Map basin from cycle
    print(f"\n{'#'*80}")
    print(f"# STEP 1: Map Basin")
    print(f"{'#'*80}\n")

    map_basin_args = [
        "--n", str(n),
        *cycle_args,
        "--max-depth", str(args.max_depth),
        "--log-every", "5",
        "--out-prefix", f"basin_n={n}_cycle={cycle_key}_{tag}",
        "--namespace", str(args.namespace),
    ]
    if args.allow_redirects:
        map_basin_args.append("--allow-redirects")
    if args.write_membership:
        map_basin_args.append("--write-membership")

    results["map-basin"] = run_script(
        "map-basin-from-cycle.py",
        map_basin_args,
        description=f"Map complete basin for {cycle_key}",
    )

    # 2. Branch analysis
    print(f"\n{'#'*80}")
    print(f"# STEP 2: Branch Analysis")
    print(f"{'#'*80}\n")

    branch_args = [
        "--n", str(n),
        *cycle_args,
        "--max-depth", "0",
        "--top-k", str(args.top_k),
        "--log-every", "10",
        "--out-prefix", f"branches_n={n}_cycle={cycle_key}_{tag}",
        "--namespace", str(args.namespace),
    ]
    if args.allow_redirects:
        branch_args.append("--allow-redirects")

    results["branch-analysis"] = run_script(
        "branch-basin-analysis.py",
        branch_args,
        description=f"Quantify branch structure for {cycle_key}",
    )

    # 3. Chase dominant upstream (if we have a title)
    if seed_title:
        print(f"\n{'#'*80}")
        print(f"# STEP 3: Chase Dominant Upstream")
        print(f"{'#'*80}\n")

        chase_args = [
            "--n", str(n),
            "--seed-title", seed_title,
            "--max-hops", str(args.max_hops),
            "--dominance-threshold", str(args.dominance_threshold),
            "--namespace", str(args.namespace),
        ]
        if args.allow_redirects:
            chase_args.append("--allow-redirects")

        results["chase-dominant"] = run_script(
            "chase-dominant-upstream.py",
            chase_args,
            description=f"Chase dominant upstream trunk from {seed_title}",
        )
    else:
        print("\n⚠ Skipping chase-dominant-upstream: no title provided (only page IDs)")
        results["chase-dominant"] = None

    # 4. Find preimages for first cycle node
    if cycle_titles:
        print(f"\n{'#'*80}")
        print(f"# STEP 4: Find Preimages")
        print(f"{'#'*80}\n")

        preimage_args = [
            "--n", str(n),
            "--target-title", cycle_titles[0],
            "--limit", "100",
            "--resolve-source-titles",
            "--namespace", str(args.namespace),
        ]
        if args.allow_redirects:
            preimage_args.append("--allow-redirects")

        results["find-preimages"] = run_script(
            "find-nlink-preimages.py",
            preimage_args,
            description=f"Find preimages for {cycle_titles[0]}",
        )
    else:
        print("\n⚠ Skipping find-preimages: no title provided (only page IDs)")
        results["find-preimages"] = None

    # 5. Render 3D tree (optional, slow)
    if args.render_3d and cycle_titles:
        print(f"\n{'#'*80}")
        print(f"# STEP 5: Render 3D Tributary Tree")
        print(f"{'#'*80}\n")

        render_args = [
            "--n", str(n),
            *cycle_args,
            "--top-k", "5",
            "--max-levels", "4",
            "--max-depth", "12",
            "--namespace", str(args.namespace),
        ]
        if args.allow_redirects:
            render_args.append("--allow-redirects")

        results["render-3d"] = run_script(
            "render-tributary-tree-3d.py",
            render_args,
            description=f"Render 3D tributary tree for {cycle_key}",
        )

    # Summary
    print(f"\n{'='*80}")
    print(f"SINGLE CYCLE ANALYSIS SUMMARY")
    print(f"{'='*80}\n")

    total = sum(1 for v in results.values() if v is not None)
    succeeded = sum(1 for v in results.values() if v is True)
    failed = total - succeeded

    print(f"Total steps run: {total}")
    print(f"Succeeded: {succeeded}")
    print(f"Failed: {failed}")
    print(f"\nSuccess rate: {100 * succeeded / total:.1f}%" if total > 0 else "No steps run")

    if failed > 0:
        print("\nFailed steps:")
        for name, success in results.items():
            if success is False:
                print(f"  ✗ {name}")

    print(f"\n{'='*80}")
    print(f"All outputs saved to: {ANALYSIS_DIR}")
    print(f"{'='*80}\n")

    sys.exit(0 if failed == 0 else 1)


if __name__ == "__main__":
    main()
