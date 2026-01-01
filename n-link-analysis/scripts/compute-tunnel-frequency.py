#!/usr/bin/env python3
"""Compute tunnel frequency rankings and importance metrics.

This script ranks tunnel nodes by how many basins they bridge and computes
importance metrics for identifying semantically central entities.

Metrics computed:
  - n_basins_bridged: Number of distinct basins the page belongs to across N
  - n_transitions: Number of N→N+1 basin changes
  - total_depth: Sum of depths across all basin memberships
  - mean_depth: Average depth across basin memberships
  - tunnel_score: Weighted importance metric combining factors

Output schema for tunnel_frequency_ranking.tsv:
  page_id: int64
  page_title: string (if available)
  n_basins_bridged: int8
  n_transitions: int8
  n_coverage: int8           - How many N values have assignments
  total_depth: int32
  mean_depth: float32
  tunnel_score: float64      - Importance score
  basin_list: string         - Comma-separated list of basins

Data dependencies:
  - data/wikipedia/processed/multiplex/tunnel_nodes.parquet
  - data/wikipedia/processed/multiplex/tunnel_classification.tsv
  - data/wikipedia/processed/multiplex/multiplex_basin_assignments.parquet
  - data/wikipedia/extracted/page.parquet (for titles, optional)
"""

from __future__ import annotations

import argparse
from pathlib import Path

import pandas as pd

REPO_ROOT = Path(__file__).resolve().parents[2]
PROCESSED_DIR = REPO_ROOT / "data" / "wikipedia" / "processed"
MULTIPLEX_DIR = PROCESSED_DIR / "multiplex"
EXTRACTED_DIR = PROCESSED_DIR.parent / "extracted"


def compute_tunnel_score(row: pd.Series) -> float:
    """Compute tunnel importance score.

    Score formula:
      tunnel_score = n_basins_bridged * log(1 + n_transitions) * (1 / mean_depth)

    Intuition:
      - More basins bridged = more central
      - More transitions = more dynamic behavior
      - Shallower depth = closer to cycle cores (more central)
    """
    import math

    n_basins = row["n_basins_bridged"]
    n_trans = row["n_transitions"]
    mean_depth = row["mean_depth"]

    # Avoid division by zero
    depth_factor = 1.0 / max(mean_depth, 1.0)

    # Log-transform transitions to reduce impact of outliers
    trans_factor = math.log(1 + n_trans)

    return n_basins * trans_factor * depth_factor * 100  # Scale for readability


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Compute tunnel frequency rankings and importance metrics"
    )
    parser.add_argument(
        "--tunnel-nodes",
        type=Path,
        default=MULTIPLEX_DIR / "tunnel_nodes.parquet",
        help="Input tunnel nodes parquet",
    )
    parser.add_argument(
        "--classification",
        type=Path,
        default=MULTIPLEX_DIR / "tunnel_classification.tsv",
        help="Input tunnel classification TSV",
    )
    parser.add_argument(
        "--assignments",
        type=Path,
        default=MULTIPLEX_DIR / "multiplex_basin_assignments.parquet",
        help="Input multiplex assignments parquet (for depth data)",
    )
    parser.add_argument(
        "--page-table",
        type=Path,
        default=EXTRACTED_DIR / "page.parquet",
        help="Page table for title lookup (optional)",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=MULTIPLEX_DIR / "tunnel_frequency_ranking.tsv",
        help="Output ranking TSV",
    )
    parser.add_argument(
        "--top-k",
        type=int,
        default=100,
        help="Show top K tunnel nodes in summary (default: 100)",
    )
    args = parser.parse_args()

    print("=" * 70)
    print("Computing Tunnel Frequency Rankings")
    print("=" * 70)
    print()

    # Load tunnel classification
    print(f"Loading {args.classification}...")
    class_df = pd.read_csv(args.classification, sep="\t")
    print(f"  Loaded {len(class_df):,} classified tunnel nodes")
    print()

    # Load multiplex assignments for depth data
    print(f"Loading {args.assignments}...")
    assign_df = pd.read_parquet(args.assignments)
    print(f"  Loaded {len(assign_df):,} assignments")
    print()

    # Compute depth statistics per tunnel node
    print("Computing depth statistics for tunnel nodes...")
    tunnel_page_ids = set(class_df["page_id"])
    tunnel_assign = assign_df[assign_df["page_id"].isin(tunnel_page_ids)]

    depth_stats = tunnel_assign.groupby("page_id").agg(
        total_depth=("depth", "sum"),
        mean_depth=("depth", "mean"),
        min_depth=("depth", "min"),
        max_depth=("depth", "max"),
    ).reset_index()

    print(f"  Computed depth stats for {len(depth_stats):,} tunnel nodes")
    print()

    # Count transitions from classification (parse switching_transitions)
    def count_transitions(trans_str):
        if pd.isna(trans_str) or trans_str == "":
            return 0
        return len(trans_str.split("; "))

    class_df["n_transitions"] = class_df["switching_transitions"].apply(count_transitions)

    # Merge with depth stats
    result_df = class_df.merge(depth_stats, on="page_id", how="left")

    # Rename for clarity
    result_df = result_df.rename(columns={"n_distinct_basins": "n_basins_bridged"})

    # Compute tunnel score
    print("Computing tunnel scores...")
    result_df["tunnel_score"] = result_df.apply(compute_tunnel_score, axis=1)

    # Create basin list (combine primary and secondary)
    result_df["basin_list"] = result_df.apply(
        lambda r: ", ".join(filter(None, [r["primary_basin"], r["secondary_basin"]])),
        axis=1
    )

    # Try to load page titles
    if args.page_table.exists():
        print(f"Loading page titles from {args.page_table}...")
        try:
            page_df = pd.read_parquet(args.page_table, columns=["page_id", "page_title"])
            result_df = result_df.merge(page_df, on="page_id", how="left")
            print(f"  Matched {result_df['page_title'].notna().sum():,} titles")
        except Exception as e:
            print(f"  Warning: Could not load page titles: {e}")
            result_df["page_title"] = None
    else:
        print(f"Page table not found at {args.page_table}, skipping title lookup")
        result_df["page_title"] = None

    print()

    # Sort by tunnel score (descending)
    result_df = result_df.sort_values("tunnel_score", ascending=False)

    # Select output columns
    output_cols = [
        "page_id",
        "page_title",
        "n_basins_bridged",
        "n_transitions",
        "n_coverage",
        "total_depth",
        "mean_depth",
        "tunnel_score",
        "basin_list",
        "tunnel_type",
        "stable_ranges",
    ]

    # Only include columns that exist
    output_cols = [c for c in output_cols if c in result_df.columns]
    output_df = result_df[output_cols]

    # Statistics
    print("=" * 70)
    print("TUNNEL FREQUENCY STATISTICS")
    print("=" * 70)
    print()

    print(f"Total tunnel nodes: {len(output_df):,}")
    print()

    print("Basins bridged distribution:")
    bridge_counts = output_df["n_basins_bridged"].value_counts().sort_index()
    for n_basins, count in bridge_counts.items():
        pct = 100 * count / len(output_df)
        print(f"  {n_basins} basins: {count:,} ({pct:.1f}%)")
    print()

    print("Transitions distribution:")
    trans_counts = output_df["n_transitions"].value_counts().sort_index()
    for n_trans, count in trans_counts.items():
        pct = 100 * count / len(output_df)
        print(f"  {n_trans} transitions: {count:,} ({pct:.1f}%)")
    print()

    print(f"Top {args.top_k} tunnel nodes by score:")
    print()
    print(f"{'Rank':>5} {'Score':>8} {'Page ID':>12} {'Basins':>7} {'Trans':>6} {'Mean Depth':>10}  Title/Basins")
    print("-" * 90)

    for idx, row in output_df.head(args.top_k).iterrows():
        rank = output_df.index.get_loc(idx) + 1
        title = row.get("page_title", "") or ""
        if pd.isna(title):
            title = ""
        title_display = title[:30] if title else row["basin_list"][:40]
        print(
            f"{rank:5d} {row['tunnel_score']:8.2f} {row['page_id']:12d} "
            f"{row['n_basins_bridged']:7d} {row['n_transitions']:6d} "
            f"{row['mean_depth']:10.1f}  {title_display}"
        )

    print()

    # Depth analysis for tunnel nodes
    print("Depth statistics for tunnel nodes:")
    print(f"  Mean depth: {output_df['mean_depth'].mean():.1f}")
    print(f"  Median depth: {output_df['mean_depth'].median():.1f}")
    print(f"  Min depth: {output_df['mean_depth'].min():.1f}")
    print(f"  Max depth: {output_df['mean_depth'].max():.1f}")
    print()

    # Write output
    print(f"Writing to {args.output}...")
    output_df.to_csv(args.output, sep="\t", index=False)
    print(f"  {len(output_df):,} rows written")
    print()

    # Also write top tunnel nodes to a separate file for easy reference
    top_path = args.output.with_name("tunnel_top_100.tsv")
    output_df.head(100).to_csv(top_path, sep="\t", index=False)
    print(f"Wrote top 100 tunnel nodes to {top_path}")
    print()

    print("=" * 70)
    print("DONE")
    print("=" * 70)


if __name__ == "__main__":
    main()
