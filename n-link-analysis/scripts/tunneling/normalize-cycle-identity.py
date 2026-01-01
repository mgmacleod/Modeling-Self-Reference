#!/usr/bin/env python3
"""Normalize cycle identities across N values.

Cycles are currently named by their member pages (e.g., "Massachusetts__Gulf_of_Maine").
The order can vary between runs. This script creates a canonical mapping.

Canonicalization rule: Alphabetically sort cycle members.
  - "Massachusetts__Gulf_of_Maine" → "Gulf_of_Maine__Massachusetts"
  - "Gulf_of_Maine__Massachusetts" → "Gulf_of_Maine__Massachusetts"

Output:
  - cycle_identity_map.tsv: Maps raw cycle keys to canonical IDs
  - Updates multiplex_basin_assignments.parquet with canonical_cycle_id column

Data dependencies:
  - data/wikipedia/processed/multiplex/multiplex_basin_assignments.parquet
"""

from __future__ import annotations

import argparse
from pathlib import Path

import duckdb
import pyarrow as pa
import pyarrow.parquet as pq

REPO_ROOT = Path(__file__).resolve().parents[3]
PROCESSED_DIR = REPO_ROOT / "data" / "wikipedia" / "processed"
MULTIPLEX_DIR = PROCESSED_DIR / "multiplex"


def canonicalize_cycle_key(cycle_key: str) -> str:
    """Convert cycle_key to canonical form (alphabetically sorted members)."""
    # Split on "__" to get member names
    members = cycle_key.split("__")
    # Sort alphabetically
    members.sort()
    # Rejoin
    return "__".join(members)


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Normalize cycle identities to canonical form"
    )
    parser.add_argument(
        "--input",
        type=Path,
        default=MULTIPLEX_DIR / "multiplex_basin_assignments.parquet",
        help="Input multiplex parquet file",
    )
    args = parser.parse_args()

    print("=" * 70)
    print("Normalizing Cycle Identities")
    print("=" * 70)
    print()

    if not args.input.exists():
        print(f"ERROR: Input file not found: {args.input}")
        print("Run build-multiplex-table.py first.")
        return

    # Load multiplex table
    print(f"Loading {args.input}...")
    table = pq.read_table(args.input)
    print(f"  {len(table):,} rows")
    print()

    # Get unique cycle keys
    cycle_keys = set(table["cycle_key"].to_pylist())
    print(f"Found {len(cycle_keys)} unique cycle keys")
    print()

    # Build canonical mapping
    canonical_map: dict[str, str] = {}
    for key in cycle_keys:
        canonical = canonicalize_cycle_key(key)
        canonical_map[key] = canonical

    # Display mapping
    print("Cycle Identity Mapping:")
    print("-" * 70)
    for raw, canonical in sorted(canonical_map.items()):
        if raw != canonical:
            print(f"  {raw}")
            print(f"    → {canonical}")
        else:
            print(f"  {raw} (already canonical)")
    print()

    # Check for collisions (multiple raw keys → same canonical)
    canonical_to_raw: dict[str, list[str]] = {}
    for raw, canonical in canonical_map.items():
        if canonical not in canonical_to_raw:
            canonical_to_raw[canonical] = []
        canonical_to_raw[canonical].append(raw)

    collisions = {k: v for k, v in canonical_to_raw.items() if len(v) > 1}
    if collisions:
        print("Collisions detected (multiple raw keys → same canonical):")
        for canonical, raws in collisions.items():
            print(f"  {canonical}: {raws}")
        print()

    # Write mapping file
    map_path = MULTIPLEX_DIR / "cycle_identity_map.tsv"
    with open(map_path, "w") as f:
        f.write("raw_cycle_key\tcanonical_cycle_id\n")
        for raw, canonical in sorted(canonical_map.items()):
            f.write(f"{raw}\t{canonical}\n")

    print(f"Mapping saved to: {map_path}")
    print()

    # Add canonical_cycle_id column to table
    print("Adding canonical_cycle_id column to multiplex table...")

    # Map each row's cycle_key to canonical
    cycle_keys_list = table["cycle_key"].to_pylist()
    canonical_ids = [canonical_map[k] for k in cycle_keys_list]

    # Create new table with canonical column
    new_table = pa.table({
        "page_id": table["page_id"],
        "N": table["N"],
        "cycle_key": table["cycle_key"],
        "canonical_cycle_id": pa.array(canonical_ids, type=pa.string()),
        "entry_id": table["entry_id"],
        "depth": table["depth"],
    })

    # Overwrite input file
    pq.write_table(new_table, args.input, compression="snappy")
    print(f"Updated: {args.input}")

    # Summary stats
    print()
    print("=" * 70)
    print("SUMMARY")
    print("=" * 70)
    print()

    unique_canonical = len(set(canonical_ids))
    print(f"Raw cycle keys: {len(cycle_keys)}")
    print(f"Canonical cycle IDs: {unique_canonical}")

    # Show which cycles appear at which N values
    print()
    print("Cycles by N value:")
    print("-" * 50)

    con = duckdb.connect()
    con.register("multiplex", new_table)
    result = con.execute("""
        SELECT canonical_cycle_id, list(DISTINCT N ORDER BY N) as n_values, COUNT(*) as rows
        FROM multiplex
        GROUP BY canonical_cycle_id
        ORDER BY canonical_cycle_id
    """).fetchall()
    con.close()

    for cycle_id, n_values, rows in result:
        n_str = ",".join(str(n) for n in n_values)
        print(f"  {cycle_id}: N∈{{{n_str}}} ({rows:,} rows)")


if __name__ == "__main__":
    main()
