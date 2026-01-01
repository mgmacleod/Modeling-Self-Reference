#!/usr/bin/env python3
"""Quantify how stable basins are across N changes.

This script measures the stability of basins as N varies, computing metrics
that capture how much the basin structure persists or fragments.

Metrics:
  - Persistence score: Fraction of pages remaining in same basin across N
  - Fragmentation index: How many sub-basins a basin splits into at different N
  - Stability range: Contiguous N values where basin membership is stable
  - Jaccard stability: Pairwise Jaccard similarity of basin membership across N

Output schema for basin_stability_scores.tsv:
  canonical_cycle_id: string   - Basin identifier
  n_values_present: int        - Number of N values where basin exists
  total_pages: int             - Total unique pages ever in this basin
  persistence_score: float     - Fraction of pages stable across all N
  max_stable_range: int        - Longest contiguous N range with >80% overlap
  fragmentation_at_n{X}: int   - Number of distinct destinations at N=X
  mean_jaccard: float          - Mean Jaccard similarity between adjacent N
  stability_class: string      - Classification (stable, moderate, fragile)

Data dependencies:
  - data/wikipedia/processed/multiplex/multiplex_basin_assignments.parquet
  - data/wikipedia/processed/multiplex/tunnel_nodes.parquet
"""

from __future__ import annotations

import argparse
from collections import defaultdict
from pathlib import Path

import pandas as pd

REPO_ROOT = Path(__file__).resolve().parents[3]
PROCESSED_DIR = REPO_ROOT / "data" / "wikipedia" / "processed"
MULTIPLEX_DIR = PROCESSED_DIR / "multiplex"


def compute_jaccard(set1: set, set2: set) -> float:
    """Compute Jaccard similarity between two sets."""
    if not set1 and not set2:
        return 1.0
    intersection = len(set1 & set2)
    union = len(set1 | set2)
    return intersection / union if union > 0 else 0.0


def compute_basin_stability(
    assignments_df: pd.DataFrame,
    n_values: list[int],
) -> list[dict]:
    """Compute stability metrics for each basin."""

    # Group by canonical_cycle_id
    results = []

    # Get all unique basins
    all_basins = assignments_df["canonical_cycle_id"].unique()
    print(f"  Analyzing {len(all_basins)} unique basins...")

    for basin_id in all_basins:
        basin_df = assignments_df[assignments_df["canonical_cycle_id"] == basin_id]

        # Get pages per N value
        pages_by_n: dict[int, set] = {}
        for n in n_values:
            n_df = basin_df[basin_df["N"] == n]
            pages_by_n[n] = set(n_df["page_id"].tolist())

        # Skip basins that don't appear at any N
        n_values_present = [n for n in n_values if len(pages_by_n.get(n, set())) > 0]
        if not n_values_present:
            continue

        # Total unique pages across all N
        all_pages = set()
        for pages in pages_by_n.values():
            all_pages.update(pages)

        # Persistence: pages that appear at ALL N values where basin exists
        if len(n_values_present) > 1:
            persistent_pages = pages_by_n.get(n_values_present[0], set()).copy()
            for n in n_values_present[1:]:
                persistent_pages &= pages_by_n.get(n, set())
            persistence_score = len(persistent_pages) / len(all_pages) if all_pages else 0
        else:
            persistence_score = 1.0  # Single N = fully persistent

        # Jaccard similarities between adjacent N values
        jaccard_scores = []
        for i in range(len(n_values) - 1):
            n1, n2 = n_values[i], n_values[i + 1]
            if n1 in pages_by_n and n2 in pages_by_n:
                j = compute_jaccard(pages_by_n[n1], pages_by_n[n2])
                jaccard_scores.append(j)

        mean_jaccard = sum(jaccard_scores) / len(jaccard_scores) if jaccard_scores else 1.0

        # Stability range: longest contiguous run with Jaccard > 0.8
        max_stable_range = 1
        current_range = 1
        for j in jaccard_scores:
            if j >= 0.8:
                current_range += 1
                max_stable_range = max(max_stable_range, current_range)
            else:
                current_range = 1

        # Classify stability
        if persistence_score >= 0.8 and mean_jaccard >= 0.8:
            stability_class = "stable"
        elif persistence_score >= 0.5 or mean_jaccard >= 0.5:
            stability_class = "moderate"
        else:
            stability_class = "fragile"

        result = {
            "canonical_cycle_id": basin_id,
            "n_values_present": len(n_values_present),
            "total_pages": len(all_pages),
            "persistence_score": round(persistence_score, 4),
            "max_stable_range": max_stable_range,
            "mean_jaccard": round(mean_jaccard, 4),
            "stability_class": stability_class,
        }

        # Add per-N page counts
        for n in n_values:
            result[f"pages_at_n{n}"] = len(pages_by_n.get(n, set()))

        results.append(result)

    return results


def compute_cross_basin_flows(
    tunnel_df: pd.DataFrame,
    n_values: list[int],
) -> pd.DataFrame:
    """Compute flow of pages between basins across N values."""

    # For each pair of adjacent N values, count pages that move between basins
    flows = []

    basin_cols = [f"basin_at_N{n}" for n in n_values]

    for i in range(len(n_values) - 1):
        n1, n2 = n_values[i], n_values[i + 1]
        col1, col2 = f"basin_at_N{n1}", f"basin_at_N{n2}"

        if col1 not in tunnel_df.columns or col2 not in tunnel_df.columns:
            continue

        # Get pages where basin changes
        changed = tunnel_df[
            (tunnel_df[col1].notna()) &
            (tunnel_df[col2].notna()) &
            (tunnel_df[col1] != tunnel_df[col2])
        ]

        # Count flows between basins
        flow_counts = changed.groupby([col1, col2]).size().reset_index(name="count")
        flow_counts["from_n"] = n1
        flow_counts["to_n"] = n2
        flow_counts = flow_counts.rename(columns={col1: "from_basin", col2: "to_basin"})

        flows.append(flow_counts)

    if flows:
        return pd.concat(flows, ignore_index=True)
    else:
        return pd.DataFrame(columns=["from_basin", "to_basin", "count", "from_n", "to_n"])


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Quantify basin stability across N values"
    )
    parser.add_argument(
        "--assignments",
        type=Path,
        default=MULTIPLEX_DIR / "multiplex_basin_assignments.parquet",
        help="Input multiplex assignments parquet",
    )
    parser.add_argument(
        "--tunnels",
        type=Path,
        default=MULTIPLEX_DIR / "tunnel_nodes.parquet",
        help="Input tunnel nodes parquet",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=MULTIPLEX_DIR / "basin_stability_scores.tsv",
        help="Output stability scores TSV",
    )
    parser.add_argument(
        "--n-min",
        type=int,
        default=3,
        help="Minimum N value",
    )
    parser.add_argument(
        "--n-max",
        type=int,
        default=7,
        help="Maximum N value",
    )
    args = parser.parse_args()

    print("=" * 70)
    print("Quantifying Basin Stability")
    print("=" * 70)
    print()

    n_values = list(range(args.n_min, args.n_max + 1))
    print(f"N values: {n_values}")
    print()

    # Load data
    print(f"Loading {args.assignments}...")
    assignments_df = pd.read_parquet(args.assignments)
    print(f"  Loaded {len(assignments_df):,} rows")
    print()

    print(f"Loading {args.tunnels}...")
    tunnel_df = pd.read_parquet(args.tunnels)
    print(f"  Loaded {len(tunnel_df):,} rows")
    print()

    # Compute basin stability
    print("Computing basin stability metrics...")
    stability_results = compute_basin_stability(assignments_df, n_values)
    stability_df = pd.DataFrame(stability_results)
    print(f"  Computed metrics for {len(stability_df)} basins")
    print()

    # Statistics
    print("=" * 70)
    print("STABILITY STATISTICS")
    print("=" * 70)
    print()

    if len(stability_df) > 0:
        # Class distribution
        class_counts = stability_df["stability_class"].value_counts()
        print("Stability class distribution:")
        for cls, count in class_counts.items():
            pct = 100 * count / len(stability_df)
            print(f"  {cls:12s}: {count:,} basins ({pct:.1f}%)")
        print()

        # Persistence score distribution
        print("Persistence score distribution:")
        print(f"  Mean:   {stability_df['persistence_score'].mean():.3f}")
        print(f"  Median: {stability_df['persistence_score'].median():.3f}")
        print(f"  Min:    {stability_df['persistence_score'].min():.3f}")
        print(f"  Max:    {stability_df['persistence_score'].max():.3f}")
        print()

        # Jaccard distribution
        print("Mean Jaccard similarity distribution:")
        print(f"  Mean:   {stability_df['mean_jaccard'].mean():.3f}")
        print(f"  Median: {stability_df['mean_jaccard'].median():.3f}")
        print()

        # Stable range distribution
        print("Max stable range distribution:")
        range_counts = stability_df["max_stable_range"].value_counts().sort_index()
        for rng, count in range_counts.items():
            pct = 100 * count / len(stability_df)
            print(f"  {rng} N values: {count:,} basins ({pct:.1f}%)")
        print()

        # Top stable basins
        print("Most stable basins (by persistence):")
        top_stable = stability_df.nlargest(5, "persistence_score")
        for _, row in top_stable.iterrows():
            print(f"  {row['canonical_cycle_id'][:40]:40s}: persistence={row['persistence_score']:.3f}, jaccard={row['mean_jaccard']:.3f}")
        print()

        # Most fragile basins
        print("Most fragile basins (by persistence):")
        fragile = stability_df.nsmallest(5, "persistence_score")
        for _, row in fragile.iterrows():
            print(f"  {row['canonical_cycle_id'][:40]:40s}: persistence={row['persistence_score']:.3f}, jaccard={row['mean_jaccard']:.3f}")
        print()

    # Compute cross-basin flows
    print("Computing cross-basin flows...")
    flows_df = compute_cross_basin_flows(tunnel_df, n_values)
    print(f"  Found {len(flows_df):,} basin-to-basin flows")
    print()

    if len(flows_df) > 0:
        print("Top flows between basins:")
        top_flows = flows_df.nlargest(10, "count")
        for _, row in top_flows.iterrows():
            print(f"  N{row['from_n']}→N{row['to_n']}: {row['from_basin'][:25]:25s} → {row['to_basin'][:25]:25s}: {row['count']:,} pages")
        print()

    # Write outputs
    print(f"Writing stability scores to {args.output}...")
    stability_df.to_csv(args.output, sep="\t", index=False)
    print(f"  {len(stability_df):,} rows written")

    flows_path = args.output.with_name("basin_flows.tsv")
    print(f"Writing basin flows to {flows_path}...")
    flows_df.to_csv(flows_path, sep="\t", index=False)
    print(f"  {len(flows_df):,} rows written")
    print()

    print("=" * 70)
    print("DONE")
    print("=" * 70)


if __name__ == "__main__":
    main()
