#!/usr/bin/env python3
"""Classify tunnel nodes by their transition behavior.

This script categorizes tunnel nodes based on how their basin membership
changes across N values, enabling analysis of tunneling patterns.

Tunnel Types:
  - basin_switching: Different cycle basins under different N
  - partial_stable: Same basin for some consecutive N values, different for others
  - alternating: Basin switches back and forth between two basins
  - progressive: Basin changes monotonically with N (A at low N, B at high N)

Output schema for tunnel_classification.tsv:
  page_id: int64
  tunnel_type: string           - Classification category
  n_distinct_basins: int8       - Number of unique basins
  n_coverage: int8              - Number of N values with basin assignments
  stable_ranges: string         - N ranges where basin is stable (e.g., "3-5,7")
  switching_transitions: string - Transitions (e.g., "N4→N5: A→B")
  primary_basin: string         - Most frequent basin
  secondary_basin: string       - Second most frequent basin (if any)

Data dependencies:
  - data/wikipedia/processed/multiplex/tunnel_nodes.parquet
"""

from __future__ import annotations

import argparse
from collections import Counter
from pathlib import Path

import pandas as pd

REPO_ROOT = Path(__file__).resolve().parents[2]
PROCESSED_DIR = REPO_ROOT / "data" / "wikipedia" / "processed"
MULTIPLEX_DIR = PROCESSED_DIR / "multiplex"


def classify_tunnel_type(row: pd.Series, basin_cols: list[str]) -> dict:
    """Classify a tunnel node based on its basin transition pattern."""
    # Extract (N, basin) pairs where basin is non-null
    n_basin_pairs = []
    for col in basin_cols:
        basin = row[col]
        if pd.notna(basin):
            n = int(col.replace("basin_at_N", ""))
            n_basin_pairs.append((n, basin))

    n_basin_pairs.sort(key=lambda x: x[0])  # Sort by N

    if len(n_basin_pairs) == 0:
        return {
            "tunnel_type": "no_data",
            "n_coverage": 0,
            "stable_ranges": "",
            "switching_transitions": "",
            "primary_basin": "",
            "secondary_basin": "",
        }

    if len(n_basin_pairs) == 1:
        return {
            "tunnel_type": "single_n",
            "n_coverage": 1,
            "stable_ranges": str(n_basin_pairs[0][0]),
            "switching_transitions": "",
            "primary_basin": n_basin_pairs[0][1],
            "secondary_basin": "",
        }

    # Count basin frequencies
    basin_counts = Counter(basin for _, basin in n_basin_pairs)
    basins_by_freq = basin_counts.most_common()
    primary_basin = basins_by_freq[0][0]
    secondary_basin = basins_by_freq[1][0] if len(basins_by_freq) > 1 else ""

    # Find transitions (places where basin changes between consecutive N values)
    transitions = []
    stable_ranges = []
    current_range_start = n_basin_pairs[0][0]
    current_basin = n_basin_pairs[0][1]

    for i in range(1, len(n_basin_pairs)):
        prev_n, prev_basin = n_basin_pairs[i - 1]
        curr_n, curr_basin = n_basin_pairs[i]

        if curr_basin != prev_basin:
            # Record the stable range that just ended
            if current_range_start == prev_n:
                stable_ranges.append(str(current_range_start))
            else:
                stable_ranges.append(f"{current_range_start}-{prev_n}")

            # Record the transition
            transitions.append(f"N{prev_n}→N{curr_n}: {prev_basin[:20]}→{curr_basin[:20]}")

            # Start new range
            current_range_start = curr_n
            current_basin = curr_basin

    # Close the final range
    final_n = n_basin_pairs[-1][0]
    if current_range_start == final_n:
        stable_ranges.append(str(current_range_start))
    else:
        stable_ranges.append(f"{current_range_start}-{final_n}")

    # Classify tunnel type
    n_distinct = len(basin_counts)
    n_transitions = len(transitions)

    if n_distinct == 1:
        # Not actually a tunnel node (single basin across all N)
        tunnel_type = "stable"
    elif n_distinct == 2:
        # Check if it alternates or is progressive
        basin_sequence = [basin for _, basin in n_basin_pairs]

        # Count switches back to earlier basin
        switches_back = 0
        for i in range(2, len(basin_sequence)):
            if basin_sequence[i] == basin_sequence[i - 2] and basin_sequence[i] != basin_sequence[i - 1]:
                switches_back += 1

        if switches_back > 0:
            tunnel_type = "alternating"
        elif n_transitions == 1:
            tunnel_type = "progressive"
        else:
            tunnel_type = "partial_stable"
    else:
        # More than 2 distinct basins
        tunnel_type = "multi_basin"

    return {
        "tunnel_type": tunnel_type,
        "n_coverage": len(n_basin_pairs),
        "stable_ranges": ",".join(stable_ranges),
        "switching_transitions": "; ".join(transitions),
        "primary_basin": primary_basin,
        "secondary_basin": secondary_basin,
    }


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Classify tunnel nodes by transition behavior"
    )
    parser.add_argument(
        "--input",
        type=Path,
        default=MULTIPLEX_DIR / "tunnel_nodes.parquet",
        help="Input tunnel nodes parquet",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=MULTIPLEX_DIR / "tunnel_classification.tsv",
        help="Output classification TSV",
    )
    parser.add_argument(
        "--tunnel-only",
        action="store_true",
        default=True,
        help="Only classify actual tunnel nodes (n_distinct_basins > 1)",
    )
    args = parser.parse_args()

    print("=" * 70)
    print("Classifying Tunnel Nodes")
    print("=" * 70)
    print()

    # Load tunnel nodes
    print(f"Loading {args.input}...")
    df = pd.read_parquet(args.input)
    print(f"  Loaded {len(df):,} pages")
    print()

    # Filter to tunnel nodes only if requested
    if args.tunnel_only:
        df = df[df["is_tunnel_node"] == True].copy()
        print(f"Filtered to tunnel nodes only: {len(df):,} pages")
        print()

    # Identify basin columns
    basin_cols = [c for c in df.columns if c.startswith("basin_at_N")]
    print(f"Basin columns: {basin_cols}")
    print()

    # Classify each tunnel node
    print("Classifying tunnel nodes...")
    classifications = []

    for idx, row in df.iterrows():
        classification = classify_tunnel_type(row, basin_cols)
        classification["page_id"] = row["page_id"]
        classification["n_distinct_basins"] = row["n_distinct_basins"]
        classifications.append(classification)

        if len(classifications) % 1000 == 0:
            print(f"  Processed {len(classifications):,} / {len(df):,}...", end="\r")

    print(f"  Processed {len(classifications):,} / {len(df):,}")
    print()

    # Create output dataframe
    class_df = pd.DataFrame(classifications)

    # Reorder columns
    col_order = [
        "page_id",
        "tunnel_type",
        "n_distinct_basins",
        "n_coverage",
        "stable_ranges",
        "switching_transitions",
        "primary_basin",
        "secondary_basin",
    ]
    class_df = class_df[col_order]

    # Statistics
    print("=" * 70)
    print("CLASSIFICATION STATISTICS")
    print("=" * 70)
    print()

    type_counts = class_df["tunnel_type"].value_counts()
    print("Tunnel type distribution:")
    for tunnel_type, count in type_counts.items():
        pct = 100 * count / len(class_df)
        print(f"  {tunnel_type:20s}: {count:,} ({pct:.1f}%)")
    print()

    # Coverage distribution
    print("N-coverage distribution (how many N values have basin assignments):")
    coverage_counts = class_df["n_coverage"].value_counts().sort_index()
    for coverage, count in coverage_counts.items():
        pct = 100 * count / len(class_df)
        print(f"  {coverage} N values: {count:,} ({pct:.1f}%)")
    print()

    # Most common basin pairs
    print("Most common primary→secondary basin pairs:")
    class_df["basin_pair"] = class_df["primary_basin"].str[:25] + " / " + class_df["secondary_basin"].str[:25]
    pair_counts = class_df["basin_pair"].value_counts().head(10)
    for pair, count in pair_counts.items():
        print(f"  {count:5,}: {pair}")
    print()

    # Example of each type
    print("Examples of each tunnel type:")
    for tunnel_type in type_counts.index:
        examples = class_df[class_df["tunnel_type"] == tunnel_type].head(2)
        print(f"\n  {tunnel_type}:")
        for _, row in examples.iterrows():
            print(f"    page_id={row['page_id']}: {row['switching_transitions'][:60]}")

    print()

    # Write output
    print(f"Writing to {args.output}...")
    class_df.to_csv(args.output, sep="\t", index=False)
    print(f"  {len(class_df):,} rows written")
    print()

    print("=" * 70)
    print("DONE")
    print("=" * 70)


if __name__ == "__main__":
    main()
