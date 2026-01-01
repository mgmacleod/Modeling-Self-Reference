#!/usr/bin/env python3
"""Run the complete tunneling analysis pipeline.

This script orchestrates all 5 phases of the tunneling/multiplex analysis:

  Phase 1: Multiplex Data Layer
    - build-multiplex-table.py
    - normalize-cycle-identity.py
    - compute-intersection-matrix.py

  Phase 2: Tunnel Node Identification
    - find-tunnel-nodes.py
    - classify-tunnel-types.py
    - compute-tunnel-frequency.py

  Phase 3: Multiplex Connectivity
    - build-multiplex-graph.py
    - compute-multiplex-reachability.py
    - visualize-multiplex-slice.py

  Phase 4: Mechanism Classification
    - analyze-tunnel-mechanisms.py
    - trace-tunneling-paths.py
    - quantify-basin-stability.py

  Phase 5: Applications & Validation
    - compute-semantic-model.py
    - validate-tunneling-predictions.py
    - generate-tunneling-report.py

Usage:
    # Run all phases
    python run-tunneling-pipeline.py

    # Run specific phase(s)
    python run-tunneling-pipeline.py --phase 1
    python run-tunneling-pipeline.py --phase 1 2 3

    # Run from a specific phase onwards
    python run-tunneling-pipeline.py --from-phase 3

    # Dry run (show what would execute)
    python run-tunneling-pipeline.py --dry-run

    # Custom N range
    python run-tunneling-pipeline.py --n-min 3 --n-max 7
"""

from __future__ import annotations

import argparse
import subprocess
import sys
import time
from dataclasses import dataclass
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
REPO_ROOT = SCRIPT_DIR.parents[2]


@dataclass
class Script:
    """A script in the pipeline."""
    name: str
    description: str
    extra_args: list[str] | None = None


PHASES: dict[int, tuple[str, list[Script]]] = {
    1: ("Multiplex Data Layer", [
        Script("build-multiplex-table.py", "Build unified multiplex basin table"),
        Script("normalize-cycle-identity.py", "Canonicalize cycle identities"),
        Script("compute-intersection-matrix.py", "Compute basin overlap matrices"),
    ]),
    2: ("Tunnel Node Identification", [
        Script("find-tunnel-nodes.py", "Identify pages in multiple basins"),
        Script("classify-tunnel-types.py", "Categorize tunnel behavior"),
        Script("compute-tunnel-frequency.py", "Rank tunnels by importance"),
    ]),
    3: ("Multiplex Connectivity", [
        Script("build-multiplex-graph.py", "Construct multiplex edge graph"),
        Script("compute-multiplex-reachability.py", "Analyze cross-layer reachability"),
        Script("visualize-multiplex-slice.py", "Generate multiplex visualizations"),
    ]),
    4: ("Mechanism Classification", [
        Script("analyze-tunnel-mechanisms.py", "Classify tunnel transition causes"),
        Script("trace-tunneling-paths.py", "Trace example tunneling paths"),
        Script("quantify-basin-stability.py", "Measure basin stability scores"),
    ]),
    5: ("Applications & Validation", [
        Script("compute-semantic-model.py", "Extract semantic model (Algorithm 5.2)"),
        Script("validate-tunneling-predictions.py", "Test theory predictions"),
        Script("generate-tunneling-report.py", "Generate publication-ready report"),
    ]),
}


def run_script(script: Script, n_min: int, n_max: int, dry_run: bool) -> bool:
    """Run a single script. Returns True on success."""
    script_path = SCRIPT_DIR / script.name

    if not script_path.exists():
        print(f"  ERROR: Script not found: {script_path}")
        return False

    cmd = [sys.executable, str(script_path)]

    # Add N range if script accepts it
    if script.name in [
        "build-multiplex-table.py",
        "find-tunnel-nodes.py",
        "compute-intersection-matrix.py",
    ]:
        cmd.extend(["--n-min", str(n_min), "--n-max", str(n_max)])

    # Add any extra args
    if script.extra_args:
        cmd.extend(script.extra_args)

    print(f"  Running: {script.name}")
    print(f"    {script.description}")

    if dry_run:
        print(f"    [DRY RUN] Would execute: {' '.join(cmd)}")
        return True

    start = time.time()
    try:
        result = subprocess.run(
            cmd,
            cwd=REPO_ROOT,
            capture_output=False,
            text=True,
        )
        elapsed = time.time() - start

        if result.returncode != 0:
            print(f"    FAILED (exit code {result.returncode}) after {elapsed:.1f}s")
            return False

        print(f"    Completed in {elapsed:.1f}s")
        return True

    except Exception as e:
        print(f"    ERROR: {e}")
        return False


def run_phase(phase_num: int, n_min: int, n_max: int, dry_run: bool) -> bool:
    """Run all scripts in a phase. Returns True if all succeed."""
    if phase_num not in PHASES:
        print(f"ERROR: Unknown phase {phase_num}")
        return False

    phase_name, scripts = PHASES[phase_num]

    print()
    print("=" * 70)
    print(f"Phase {phase_num}: {phase_name}")
    print("=" * 70)

    all_success = True
    for script in scripts:
        success = run_script(script, n_min, n_max, dry_run)
        if not success:
            all_success = False
            print(f"  Stopping phase {phase_num} due to failure")
            break
        print()

    return all_success


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Run the complete tunneling analysis pipeline",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python run-tunneling-pipeline.py                  # Run all 5 phases
  python run-tunneling-pipeline.py --phase 1 2     # Run phases 1 and 2 only
  python run-tunneling-pipeline.py --from-phase 3  # Run phases 3, 4, 5
  python run-tunneling-pipeline.py --dry-run       # Show what would run
        """,
    )
    parser.add_argument(
        "--phase",
        type=int,
        nargs="+",
        choices=[1, 2, 3, 4, 5],
        help="Run specific phase(s) only",
    )
    parser.add_argument(
        "--from-phase",
        type=int,
        choices=[1, 2, 3, 4, 5],
        help="Run from this phase onwards",
    )
    parser.add_argument(
        "--n-min",
        type=int,
        default=3,
        help="Minimum N value (default: 3)",
    )
    parser.add_argument(
        "--n-max",
        type=int,
        default=7,
        help="Maximum N value (default: 7)",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show what would be executed without running",
    )
    args = parser.parse_args()

    # Determine which phases to run
    if args.phase:
        phases_to_run = sorted(args.phase)
    elif args.from_phase:
        phases_to_run = list(range(args.from_phase, 6))
    else:
        phases_to_run = [1, 2, 3, 4, 5]

    print("=" * 70)
    print("TUNNELING ANALYSIS PIPELINE")
    print("=" * 70)
    print()
    print(f"Phases to run: {phases_to_run}")
    print(f"N range: {args.n_min} to {args.n_max}")
    if args.dry_run:
        print("Mode: DRY RUN (no scripts will execute)")
    print()

    total_start = time.time()
    failed_phases = []

    for phase_num in phases_to_run:
        success = run_phase(phase_num, args.n_min, args.n_max, args.dry_run)
        if not success:
            failed_phases.append(phase_num)
            print(f"\nPhase {phase_num} failed. Stopping pipeline.")
            break

    total_elapsed = time.time() - total_start

    print()
    print("=" * 70)
    print("PIPELINE SUMMARY")
    print("=" * 70)
    print(f"Total time: {total_elapsed:.1f}s ({total_elapsed/60:.1f} minutes)")

    if failed_phases:
        print(f"Status: FAILED at phase(s) {failed_phases}")
        sys.exit(1)
    else:
        print(f"Status: SUCCESS - {len(phases_to_run)} phase(s) completed")
        sys.exit(0)


if __name__ == "__main__":
    main()
