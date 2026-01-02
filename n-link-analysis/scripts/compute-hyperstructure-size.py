#!/usr/bin/env python3
"""Compute hyperstructure size: union of all basin members across N values.

A hyperstructure for a given cycle is the union of all pages that belong to
that cycle's basin at ANY N value. This answers WH's question:
"What % of Wikipedia is in the Massachusetts hyperstructure?"

The hyperstructure also includes pages that "tunnel" between basins, as these
represent semantic bridges in the multiplex graph.

Output:
  - Per-cycle hyperstructure sizes
  - Total hyperstructure coverage (union of all cycles)
  - Massachusetts-specific analysis
  - Comparison to individual N basin sizes
"""

from __future__ import annotations

import argparse
from pathlib import Path

import pandas as pd

REPO_ROOT = Path(__file__).resolve().parents[2]
PROCESSED_DIR = REPO_ROOT / "data" / "wikipedia" / "processed"
MULTIPLEX_DIR = PROCESSED_DIR / "multiplex"
ANALYSIS_DIR = PROCESSED_DIR / "analysis"

# Wikipedia total pages (from prior analysis)
WIKIPEDIA_TOTAL_PAGES = 17_970_000  # ~17.9M


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Compute hyperstructure sizes across all N values"
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
        default=ANALYSIS_DIR / "hyperstructure_analysis.tsv",
        help="Output analysis TSV",
    )
    parser.add_argument(
        "--cycle",
        type=str,
        default="Gulf_of_Maine__Massachusetts",
        help="Cycle to analyze in detail (default: Massachusetts)",
    )
    args = parser.parse_args()

    print("=" * 70)
    print("HYPERSTRUCTURE SIZE ANALYSIS")
    print("=" * 70)
    print()

    # Load multiplex assignments
    print(f"Loading {args.input}...")
    df = pd.read_parquet(args.input)
    print(f"  Total rows: {len(df):,}")
    print(f"  Unique pages: {df['page_id'].nunique():,}")
    print(f"  N values: {sorted(df['N'].unique())}")
    print()

    # Normalize cycle names - group tunneling variants with their base cycle
    # e.g., "Gulf_of_Maine_tunneling__Massachusetts" -> "Gulf_of_Maine__Massachusetts"
    def normalize_cycle(cycle_id: str) -> str:
        # Remove _tunneling suffix from cycle components
        if "_tunneling" in cycle_id:
            parts = cycle_id.split("__")
            normalized_parts = [p.replace("_tunneling", "") for p in parts]
            return "__".join(normalized_parts)
        return cycle_id

    df["base_cycle"] = df["canonical_cycle_id"].apply(normalize_cycle)

    # =====================================================================
    # 1. PER-CYCLE HYPERSTRUCTURE ANALYSIS
    # =====================================================================
    print("=" * 70)
    print("1. PER-CYCLE HYPERSTRUCTURE SIZES")
    print("=" * 70)
    print()

    # Get unique pages per base cycle (union across all N)
    cycle_hyperstructures = (
        df.groupby("base_cycle")["page_id"]
        .nunique()
        .sort_values(ascending=False)
        .reset_index()
    )
    cycle_hyperstructures.columns = ["cycle", "hyperstructure_size"]
    cycle_hyperstructures["pct_of_wikipedia"] = (
        cycle_hyperstructures["hyperstructure_size"] / WIKIPEDIA_TOTAL_PAGES * 100
    )

    print("Top 10 hyperstructures by size:")
    print("-" * 50)
    for _, row in cycle_hyperstructures.head(10).iterrows():
        print(
            f"  {row['cycle']}: {row['hyperstructure_size']:,} pages "
            f"({row['pct_of_wikipedia']:.2f}%)"
        )
    print()

    # =====================================================================
    # 2. MASSACHUSETTS DEEP DIVE
    # =====================================================================
    print("=" * 70)
    print(f"2. {args.cycle} HYPERSTRUCTURE ANALYSIS")
    print("=" * 70)
    print()

    # Filter to target cycle
    mass_df = df[df["base_cycle"] == args.cycle]

    if len(mass_df) == 0:
        print(f"WARNING: No data found for cycle '{args.cycle}'")
        print(f"Available cycles: {sorted(df['base_cycle'].unique())[:20]}")
        return

    # Unique pages in hyperstructure
    mass_pages = set(mass_df["page_id"].unique())
    mass_hyperstructure_size = len(mass_pages)
    mass_pct = mass_hyperstructure_size / WIKIPEDIA_TOTAL_PAGES * 100

    print(f"Hyperstructure size: {mass_hyperstructure_size:,} pages")
    print(f"Percentage of Wikipedia: {mass_pct:.2f}%")
    print()

    # Per-N breakdown
    print("Per-N breakdown:")
    print("-" * 50)
    mass_per_n = mass_df.groupby("N")["page_id"].nunique().sort_index()
    for n, count in mass_per_n.items():
        print(f"  N={n}: {count:,} pages")
    print()

    # How much overlap across N values?
    print("N-value overlap analysis:")
    print("-" * 50)

    # Compute pages that appear at multiple N values
    page_n_counts = mass_df.groupby("page_id")["N"].nunique()
    multi_n_pages = (page_n_counts > 1).sum()
    single_n_pages = (page_n_counts == 1).sum()

    print(f"  Pages in only 1 N-value basin: {single_n_pages:,}")
    print(f"  Pages in 2+ N-value basins: {multi_n_pages:,}")
    print()

    # Distribution of N-count
    n_count_dist = page_n_counts.value_counts().sort_index()
    print("  Distribution by # of N values:")
    for n_count, num_pages in n_count_dist.items():
        print(f"    {n_count} N-values: {num_pages:,} pages")
    print()

    # =====================================================================
    # 3. TOTAL HYPERSTRUCTURE (UNION OF ALL CYCLES)
    # =====================================================================
    print("=" * 70)
    print("3. TOTAL HYPERSTRUCTURE (ALL CYCLES)")
    print("=" * 70)
    print()

    total_pages = df["page_id"].nunique()
    total_pct = total_pages / WIKIPEDIA_TOTAL_PAGES * 100

    print(f"Total unique pages in ANY basin at ANY N: {total_pages:,}")
    print(f"Percentage of Wikipedia: {total_pct:.2f}%")
    print()

    # =====================================================================
    # 4. WH's HYPOTHESIS TEST
    # =====================================================================
    print("=" * 70)
    print("4. WH's HYPOTHESIS TEST")
    print("=" * 70)
    print()
    print("WH speculated: '2/3 of all (canonical 7.1 million) pages are in")
    print("                the Massachusetts hyper-structure'")
    print()

    # Note: WH said "canonical 7.1 million" which likely refers to article namespace
    # The full 17.9M includes other namespaces. Let's compute both ways.
    canonical_pages = 7_100_000  # WH's "canonical" count

    print(f"Against WH's canonical count ({canonical_pages/1e6:.1f}M pages):")
    print(
        f"  Massachusetts hyperstructure: {mass_hyperstructure_size:,} = "
        f"{mass_hyperstructure_size/canonical_pages*100:.1f}%"
    )
    print(f"  WH's guess (2/3): {canonical_pages*2//3:,} = 66.7%")
    print()

    print(f"Against our full count ({WIKIPEDIA_TOTAL_PAGES/1e6:.1f}M pages):")
    print(
        f"  Massachusetts hyperstructure: {mass_hyperstructure_size:,} = "
        f"{mass_pct:.1f}%"
    )
    print()

    # =====================================================================
    # 5. HYPERSTRUCTURE OVERLAP MATRIX
    # =====================================================================
    print("=" * 70)
    print("5. HYPERSTRUCTURE OVERLAP ANALYSIS")
    print("=" * 70)
    print()

    # For top 6 cycles, compute pairwise overlap
    top_cycles = cycle_hyperstructures["cycle"].head(6).tolist()

    print("Overlap between top hyperstructures:")
    print("-" * 50)

    # Get page sets for top cycles
    cycle_page_sets = {}
    for cycle in top_cycles:
        cycle_page_sets[cycle] = set(df[df["base_cycle"] == cycle]["page_id"])

    # Compute overlaps
    for i, c1 in enumerate(top_cycles):
        for c2 in top_cycles[i + 1 :]:
            overlap = len(cycle_page_sets[c1] & cycle_page_sets[c2])
            if overlap > 0:
                print(f"  {c1[:30]:30s} ∩ {c2[:30]:30s}: {overlap:,}")
    print()

    # =====================================================================
    # 6. SAVE RESULTS
    # =====================================================================
    print("=" * 70)
    print("6. SAVING RESULTS")
    print("=" * 70)
    print()

    # Save cycle hyperstructure sizes
    args.output.parent.mkdir(parents=True, exist_ok=True)
    cycle_hyperstructures.to_csv(args.output, sep="\t", index=False)
    print(f"Saved cycle hyperstructure sizes to: {args.output}")

    # Save Massachusetts analysis
    mass_output = args.output.parent / "massachusetts_hyperstructure_analysis.tsv"
    mass_analysis = pd.DataFrame(
        {
            "metric": [
                "hyperstructure_size",
                "pct_of_wikipedia",
                "pct_of_canonical_7m",
                "pages_in_single_n",
                "pages_in_multi_n",
                "n_values_covered",
            ],
            "value": [
                mass_hyperstructure_size,
                mass_pct,
                mass_hyperstructure_size / canonical_pages * 100,
                single_n_pages,
                multi_n_pages,
                len(mass_per_n),
            ],
        }
    )
    mass_analysis.to_csv(mass_output, sep="\t", index=False)
    print(f"Saved Massachusetts analysis to: {mass_output}")

    print()
    print("=" * 70)
    print("SUMMARY")
    print("=" * 70)
    print()
    print(f"Massachusetts hyperstructure: {mass_hyperstructure_size:,} pages")
    print(f"  = {mass_pct:.1f}% of Wikipedia ({WIKIPEDIA_TOTAL_PAGES/1e6:.1f}M)")
    print(
        f"  = {mass_hyperstructure_size/canonical_pages*100:.1f}% of 'canonical' 7.1M"
    )
    print()
    if mass_hyperstructure_size / canonical_pages > 0.5:
        print("  ✓ WH's guess is in the right ballpark!")
    else:
        print("  ✗ WH's guess (2/3) was optimistic")
    print()


if __name__ == "__main__":
    main()
