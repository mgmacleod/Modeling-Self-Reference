#!/usr/bin/env python3
"""Find tunnel nodes: pages that belong to different basins at different N values.

This script pivots the multiplex basin assignment table to identify pages
that switch between different terminal cycles as N changes. These are
"tunnel nodes" per Definition 4.1 from database-inference-graph-theory.md.

A tunnel node is a page that:
  - Belongs to basin A under rule N1
  - Belongs to basin B under rule N2 (where A != B)

Output schema for tunnel_nodes.parquet:
  page_id: int64
  basin_at_N3: string (nullable)  - Which cycle's basin at N=3
  basin_at_N4: string (nullable)  - Which cycle's basin at N=4
  basin_at_N5: string (nullable)  - Which cycle's basin at N=5
  basin_at_N6: string (nullable)  - Which cycle's basin at N=6
  basin_at_N7: string (nullable)  - Which cycle's basin at N=7
  n_distinct_basins: int8         - Count of unique basins across all N
  is_tunnel_node: bool            - True if n_distinct_basins > 1

Data dependencies:
  - data/wikipedia/processed/multiplex/multiplex_basin_assignments.parquet
"""

from __future__ import annotations

import argparse
from pathlib import Path

import pandas as pd
import pyarrow as pa
import pyarrow.parquet as pq

REPO_ROOT = Path(__file__).resolve().parents[3]
PROCESSED_DIR = REPO_ROOT / "data" / "wikipedia" / "processed"
MULTIPLEX_DIR = PROCESSED_DIR / "multiplex"


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Find tunnel nodes (pages in different basins at different N)"
    )
    parser.add_argument(
        "--input",
        type=Path,
        default=MULTIPLEX_DIR / "multiplex_basin_assignments.parquet",
        help="Input multiplex assignments parquet",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=MULTIPLEX_DIR / "tunnel_nodes.parquet",
        help="Output tunnel nodes parquet",
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
        default=7,
        help="Maximum N value to include (default: 7)",
    )
    args = parser.parse_args()

    print("=" * 70)
    print("Finding Tunnel Nodes")
    print("=" * 70)
    print()

    # Load multiplex assignments
    print(f"Loading {args.input}...")
    df = pd.read_parquet(args.input)
    print(f"  Loaded {len(df):,} rows")
    print(f"  Unique pages: {df['page_id'].nunique():,}")
    print(f"  N values: {sorted(df['N'].unique())}")
    print()

    # Filter to N range
    df = df[(df["N"] >= args.n_min) & (df["N"] <= args.n_max)]
    print(f"After filtering to N in [{args.n_min}, {args.n_max}]: {len(df):,} rows")
    print()

    # Use canonical_cycle_id for basin identity
    # This ensures consistent identity across different naming conventions
    if "canonical_cycle_id" in df.columns:
        basin_col = "canonical_cycle_id"
    else:
        basin_col = "cycle_key"
    print(f"Using '{basin_col}' for basin identity")
    print()

    # Pivot: rows = page_id, columns = N, values = basin
    print("Pivoting to page_id × N matrix...")

    # For pages with multiple entries at same N (shouldn't happen, but handle gracefully)
    # Take the first basin encountered
    pivot_df = df.pivot_table(
        index="page_id",
        columns="N",
        values=basin_col,
        aggfunc="first",
    )

    # Rename columns to basin_at_N{n}
    pivot_df.columns = [f"basin_at_N{n}" for n in pivot_df.columns]
    pivot_df = pivot_df.reset_index()

    print(f"  Pivot shape: {pivot_df.shape}")
    print()

    # Count distinct non-null basins per page
    print("Computing distinct basin counts...")
    basin_cols = [c for c in pivot_df.columns if c.startswith("basin_at_N")]

    def count_distinct_basins(row):
        """Count unique non-null basins for a row."""
        basins = set()
        for col in basin_cols:
            val = row[col]
            if pd.notna(val):
                basins.add(val)
        return len(basins)

    pivot_df["n_distinct_basins"] = pivot_df.apply(count_distinct_basins, axis=1).astype("int8")

    # A tunnel node has basins in multiple DIFFERENT cycles (not just multiple N values with same cycle)
    pivot_df["is_tunnel_node"] = pivot_df["n_distinct_basins"] > 1

    # Statistics
    n_total = len(pivot_df)
    n_tunnel = pivot_df["is_tunnel_node"].sum()
    n_single_basin = (pivot_df["n_distinct_basins"] == 1).sum()
    n_no_basin = (pivot_df["n_distinct_basins"] == 0).sum()  # Shouldn't happen given our data

    print()
    print("=" * 70)
    print("TUNNEL NODE STATISTICS")
    print("=" * 70)
    print()
    print(f"Total unique pages in multiplex: {n_total:,}")
    print(f"  Single-basin pages:            {n_single_basin:,} ({100*n_single_basin/n_total:.1f}%)")
    print(f"  Tunnel nodes (multi-basin):    {n_tunnel:,} ({100*n_tunnel/n_total:.1f}%)")
    if n_no_basin > 0:
        print(f"  No basin (unexpected):         {n_no_basin:,}")
    print()

    # Distribution of distinct basin counts
    print("Distribution of distinct basin counts:")
    dist = pivot_df["n_distinct_basins"].value_counts().sort_index()
    for count, freq in dist.items():
        print(f"  {count} basin(s): {freq:,} pages ({100*freq/n_total:.2f}%)")
    print()

    # Show some example tunnel nodes
    tunnel_examples = pivot_df[pivot_df["is_tunnel_node"]].head(10)
    if len(tunnel_examples) > 0:
        print("Example tunnel nodes (first 10):")
        print()
        for _, row in tunnel_examples.iterrows():
            page_id = row["page_id"]
            basins = []
            for col in basin_cols:
                if pd.notna(row[col]):
                    n = col.replace("basin_at_N", "")
                    basins.append(f"N{n}:{row[col][:30]}")
            print(f"  page_id={page_id}: {', '.join(basins)}")
        print()

    # Write output
    print(f"Writing to {args.output}...")

    # Convert to PyArrow table for efficient storage
    table = pa.Table.from_pandas(pivot_df, preserve_index=False)
    pq.write_table(table, args.output, compression="snappy")

    print(f"  Size: {args.output.stat().st_size / 1024 / 1024:.2f} MB")
    print()

    # Also write a summary TSV for quick reference
    summary_path = args.output.with_suffix(".tsv").with_name("tunnel_nodes_summary.tsv")
    summary_df = pivot_df[pivot_df["is_tunnel_node"]].copy()
    summary_df.to_csv(summary_path, sep="\t", index=False)
    print(f"Wrote tunnel node summary to {summary_path}")
    print(f"  {len(summary_df):,} tunnel nodes")
    print()

    print("=" * 70)
    print("DONE")
    print("=" * 70)


if __name__ == "__main__":
    main()
