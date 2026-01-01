#!/usr/bin/env python3
"""Build unified multiplex basin assignment table.

This script creates a single table combining all per-N basin assignment files
into a unified multiplex structure suitable for tunneling analysis.

Output schema:
  page_id: int64       - Wikipedia page ID
  N: int8              - N-link rule value
  cycle_key: string    - Cycle identifier (e.g., "Massachusetts__Gulf_of_Maine")
  entry_id: int64      - Entry point page_id for this basin
  depth: int32         - Depth from cycle under this N

Data dependencies:
  - data/wikipedia/processed/analysis/branches_n=*_assignments.parquet
"""

from __future__ import annotations

import argparse
import re
from pathlib import Path

import pyarrow as pa
import pyarrow.parquet as pq

REPO_ROOT = Path(__file__).resolve().parents[3]
PROCESSED_DIR = REPO_ROOT / "data" / "wikipedia" / "processed"
ANALYSIS_DIR = PROCESSED_DIR / "analysis"
MULTIPLEX_DIR = PROCESSED_DIR / "multiplex"


def parse_filename(filename: str) -> tuple[int, str, str] | None:
    """Parse N, cycle_key, and tag from filename.

    Example: branches_n=5_cycle=Massachusetts__Gulf_of_Maine_reproduction_2025-12-31_assignments.parquet
    Returns: (5, "Massachusetts__Gulf_of_Maine", "reproduction_2025-12-31")
    """
    # Pattern: branches_n={N}_cycle={CYCLE}_{TAG}_assignments.parquet
    pattern = r"branches_n=(\d+)_cycle=(.+?)_([^_]+_\d{4}-\d{2}-\d{2})_assignments\.parquet"
    match = re.match(pattern, filename)
    if match:
        n = int(match.group(1))
        cycle_key = match.group(2)
        tag = match.group(3)
        return n, cycle_key, tag
    return None


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Build unified multiplex basin assignment table"
    )
    parser.add_argument(
        "--n-min",
        type=int,
        default=3,
        help="Minimum N value to include (default: 3)",
    )
    parser.add_argument(
        "--n-max",
        type=int,
        default=10,
        help="Maximum N value to include (default: 10)",
    )
    parser.add_argument(
        "--prefer-tag",
        type=str,
        default="2026-01-01",
        help="Prefer files with this tag date when duplicates exist (default: 2026-01-01)",
    )
    args = parser.parse_args()

    print("=" * 70)
    print("Building Multiplex Basin Assignment Table")
    print("=" * 70)
    print()

    # Find all assignment parquet files
    pattern = "branches_n=*_*_assignments.parquet"
    all_files = list(ANALYSIS_DIR.glob(pattern))

    if not all_files:
        print(f"ERROR: No files matching {pattern} found in {ANALYSIS_DIR}")
        return

    print(f"Found {len(all_files)} basin assignment files")
    print()

    # Group by (N, cycle_key) and select preferred file
    file_groups: dict[tuple[int, str], list[tuple[Path, str]]] = {}

    for filepath in all_files:
        parsed = parse_filename(filepath.name)
        if parsed is None:
            print(f"  Skipping (can't parse): {filepath.name}")
            continue

        n, cycle_key, tag = parsed

        if n < args.n_min or n > args.n_max:
            continue

        key = (n, cycle_key)
        if key not in file_groups:
            file_groups[key] = []
        file_groups[key].append((filepath, tag))

    # Select preferred file for each (N, cycle_key)
    selected_files: list[tuple[Path, int, str]] = []

    for (n, cycle_key), files in sorted(file_groups.items()):
        # Prefer file with preferred tag date
        preferred = None
        for filepath, tag in files:
            if args.prefer_tag in tag:
                preferred = filepath
                break
        if preferred is None:
            # Take the latest (last in sorted list)
            preferred = sorted(files, key=lambda x: x[1])[-1][0]

        selected_files.append((preferred, n, cycle_key))

    print(f"Selected {len(selected_files)} unique (N, cycle) combinations")
    print()

    # Build unified table
    all_tables = []
    total_rows = 0

    for filepath, n, cycle_key in sorted(selected_files):
        print(f"  Loading N={n}, {cycle_key}...", end=" ", flush=True)

        try:
            table = pq.read_table(filepath)
            num_rows = len(table)

            # Add N and cycle_key columns
            n_col = pa.array([n] * num_rows, type=pa.int8())
            cycle_col = pa.array([cycle_key] * num_rows, type=pa.string())

            # Rebuild table with new columns
            new_table = pa.table({
                "page_id": table["page_id"],
                "N": n_col,
                "cycle_key": cycle_col,
                "entry_id": table["entry_id"],
                "depth": table["depth"],
            })

            all_tables.append(new_table)
            total_rows += num_rows
            print(f"{num_rows:,} rows")

        except Exception as e:
            print(f"ERROR: {e}")
            continue

    if not all_tables:
        print("ERROR: No tables loaded successfully")
        return

    print()
    print(f"Concatenating {len(all_tables)} tables ({total_rows:,} total rows)...")

    # Concatenate all tables
    combined = pa.concat_tables(all_tables)

    # Write output
    MULTIPLEX_DIR.mkdir(parents=True, exist_ok=True)
    out_path = MULTIPLEX_DIR / "multiplex_basin_assignments.parquet"

    print(f"Writing to {out_path}...")
    pq.write_table(combined, out_path, compression="snappy")

    # Summary stats
    print()
    print("=" * 70)
    print("SUMMARY")
    print("=" * 70)
    print()
    print(f"Total rows: {len(combined):,}")
    print(f"Unique page_ids: {len(set(combined['page_id'].to_pylist())):,}")
    print(f"N values: {sorted(set(combined['N'].to_pylist()))}")
    print(f"Cycles: {len(set(combined['cycle_key'].to_pylist()))}")
    print()
    print(f"Output: {out_path}")
    print(f"Size: {out_path.stat().st_size / 1024 / 1024:.1f} MB")


if __name__ == "__main__":
    main()
