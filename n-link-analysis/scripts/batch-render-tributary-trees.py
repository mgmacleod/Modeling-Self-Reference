#!/usr/bin/env python3
"""Batch render tributary tree 3D visualizations for all N values and cycles.

This script discovers available cycles from the branch assignment parquet files
and generates tributary tree visualizations for each N × cycle combination.

Usage:
    # Generate all combinations with defaults
    python batch-render-tributary-trees.py

    # Generate only for specific N values
    python batch-render-tributary-trees.py --n 3 --n 5 --n 8

    # Generate only for specific cycles (partial match)
    python batch-render-tributary-trees.py --cycle Massachusetts --cycle Mountain

    # Custom visualization parameters
    python batch-render-tributary-trees.py --top-k 5 --max-levels 4 --max-depth 10

    # Dry run (show what would be generated)
    python batch-render-tributary-trees.py --dry-run

    # Skip existing files
    python batch-render-tributary-trees.py --skip-existing
"""

from __future__ import annotations

import argparse
import subprocess
import sys
from collections import defaultdict
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
ANALYSIS_DIR = Path.home() / ".cache/wikipedia-nlink-basins/mgmacleod_wikidata1/data/analysis"
REPORT_ASSETS_DIR = REPO_ROOT / "n-link-analysis" / "report" / "assets"
RENDER_SCRIPT = REPO_ROOT / "n-link-analysis" / "scripts" / "render-tributary-tree-3d.py"


def discover_cycles() -> dict[int, set[str]]:
    """Discover available cycles from branch assignment parquet files.

    Returns:
        Dictionary mapping N value to set of cycle keys (e.g., "Massachusetts__Gulf_of_Maine")
    """
    cycles_by_n: dict[int, set[str]] = defaultdict(set)

    if not ANALYSIS_DIR.exists():
        print(f"Warning: Analysis directory not found: {ANALYSIS_DIR}")
        return cycles_by_n

    for f in ANALYSIS_DIR.glob("branches_n=*.parquet"):
        name = f.stem

        # Parse n value
        if "_cycle=" not in name:
            continue
        n_part = name.split("_cycle=")[0]
        try:
            n = int(n_part.replace("branches_n=", ""))
        except ValueError:
            continue

        # Parse cycle key (two titles joined by __)
        cycle_part = name.split("_cycle=")[1]
        parts = cycle_part.split("__")
        if len(parts) < 2:
            continue

        title1 = parts[0]
        rest = "__".join(parts[1:])

        # Strip known suffixes to get title2
        for suffix in ["_reproduction", "_tunneling"]:
            if suffix in rest:
                title2 = rest.split(suffix)[0]
                break
        else:
            title2 = rest

        cycle = f"{title1}__{title2}"
        cycles_by_n[n].add(cycle)

    return cycles_by_n


def cycle_to_titles(cycle_key: str) -> list[str]:
    """Convert cycle key to list of titles.

    Example: "Massachusetts__Gulf_of_Maine" -> ["Massachusetts", "Gulf_of_Maine"]
    """
    return cycle_key.split("__")


def output_filename(n: int, cycle_key: str, top_k: int, max_levels: int, max_depth: int) -> str:
    """Generate output filename matching render-tributary-tree-3d.py convention."""
    return f"tributary_tree_3d_n={n}_cycle={cycle_key}_k={top_k}_levels={max_levels}_depth={max_depth}.html"


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Batch render tributary tree visualizations for all N × cycle combinations.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )

    # Filtering options
    parser.add_argument(
        "--n",
        type=int,
        action="append",
        dest="n_values",
        help="Limit to specific N values (repeatable). Default: all discovered.",
    )
    parser.add_argument(
        "--cycle",
        action="append",
        dest="cycle_filters",
        help="Limit to cycles containing this substring (repeatable, case-insensitive). Default: all.",
    )

    # Visualization parameters (passed to render script)
    parser.add_argument("--top-k", type=int, default=4, help="Top-k branches per node (default: 4)")
    parser.add_argument("--max-levels", type=int, default=4, help="Tree depth levels (default: 4)")
    parser.add_argument("--max-depth", type=int, default=10, help="Reverse expansion depth cap (default: 10)")

    # Execution options
    parser.add_argument("--dry-run", action="store_true", help="Show what would be generated without running")
    parser.add_argument("--skip-existing", action="store_true", help="Skip if output file already exists")
    parser.add_argument("--parallel", type=int, default=1, help="Number of parallel jobs (default: 1)")

    args = parser.parse_args()

    # Discover available cycles
    print("Discovering available cycles...")
    cycles_by_n = discover_cycles()

    if not cycles_by_n:
        print("No cycles found. Check that analysis parquet files exist.")
        return 1

    # Filter by N values
    if args.n_values:
        n_filter = set(args.n_values)
        cycles_by_n = {n: cycles for n, cycles in cycles_by_n.items() if n in n_filter}

    # Filter by cycle name
    if args.cycle_filters:
        filters = [f.lower() for f in args.cycle_filters]
        cycles_by_n = {
            n: {c for c in cycles if any(f in c.lower() for f in filters)}
            for n, cycles in cycles_by_n.items()
        }
        cycles_by_n = {n: cycles for n, cycles in cycles_by_n.items() if cycles}

    # Build job list
    jobs: list[tuple[int, str]] = []
    for n in sorted(cycles_by_n.keys()):
        for cycle in sorted(cycles_by_n[n]):
            jobs.append((n, cycle))

    if not jobs:
        print("No matching N × cycle combinations found.")
        return 1

    # Report plan
    print(f"\nFound {len(jobs)} combinations to render:")
    for n in sorted(cycles_by_n.keys()):
        cycles = sorted(cycles_by_n[n])
        print(f"  N={n}: {len(cycles)} cycles")
        for c in cycles:
            print(f"    - {c}")

    print(f"\nParameters: top_k={args.top_k}, max_levels={args.max_levels}, max_depth={args.max_depth}")

    if args.dry_run:
        print("\n[DRY RUN] Would generate:")
        for n, cycle in jobs:
            out = output_filename(n, cycle, args.top_k, args.max_levels, args.max_depth)
            print(f"  {out}")
        return 0

    # Execute renders
    REPORT_ASSETS_DIR.mkdir(parents=True, exist_ok=True)

    success_count = 0
    skip_count = 0
    fail_count = 0

    for i, (n, cycle) in enumerate(jobs, 1):
        out_file = REPORT_ASSETS_DIR / output_filename(n, cycle, args.top_k, args.max_levels, args.max_depth)

        if args.skip_existing and out_file.exists():
            print(f"[{i}/{len(jobs)}] SKIP (exists): {out_file.name}")
            skip_count += 1
            continue

        titles = cycle_to_titles(cycle)
        cmd = [
            sys.executable,
            str(RENDER_SCRIPT),
            "--n", str(n),
            "--top-k", str(args.top_k),
            "--max-levels", str(args.max_levels),
            "--max-depth", str(args.max_depth),
        ]
        for t in titles:
            cmd.extend(["--cycle-title", t])

        print(f"\n[{i}/{len(jobs)}] Rendering N={n}, {cycle}...")
        try:
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=600)
            if result.returncode == 0:
                print(f"  OK: {out_file.name}")
                success_count += 1
            else:
                print(f"  FAILED (exit {result.returncode})")
                if result.stderr:
                    print(f"  stderr: {result.stderr[:500]}")
                fail_count += 1
        except subprocess.TimeoutExpired:
            print(f"  TIMEOUT after 600s")
            fail_count += 1
        except Exception as e:
            print(f"  ERROR: {e}")
            fail_count += 1

    # Summary
    print(f"\n{'='*60}")
    print(f"SUMMARY: {success_count} succeeded, {skip_count} skipped, {fail_count} failed")
    print(f"Output directory: {REPORT_ASSETS_DIR}")

    return 0 if fail_count == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
