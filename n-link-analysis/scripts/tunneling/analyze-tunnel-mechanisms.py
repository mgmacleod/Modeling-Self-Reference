#!/usr/bin/env python3
"""Classify the mechanism causing each tunnel transition.

This script analyzes WHY pages switch between basins when N changes,
categorizing the root cause of each tunneling event.

Mechanisms:
  - degree_shift: The Nth link is simply different from the (N-1)th link
  - path_divergence: Same immediate successor at both N values, but paths diverge downstream
  - halt_creation: Page has <N links, so higher N causes HALT
  - link_not_found: The Nth link target doesn't exist or is a redirect loop

For each tunnel node, we examine each N transition where the basin changes
and determine which mechanism caused the change.

Output schema for tunnel_mechanisms.tsv:
  page_id: int64
  page_title: string
  transition: string           - e.g., "N5→N6"
  from_basin: string           - Basin at lower N
  to_basin: string             - Basin at higher N
  mechanism: string            - One of the mechanisms above
  nth_link_at_low_n: string    - What the Nth link was at lower N
  nth_link_at_high_n: string   - What the Nth link is at higher N (if exists)
  out_degree: int              - Number of outgoing links from this page
  explanation: string          - Human-readable explanation

Data dependencies:
  - data/wikipedia/processed/multiplex/tunnel_classification.tsv
  - data/wikipedia/processed/links_prose.parquet
  - data/wikipedia/processed/pages.parquet
"""

from __future__ import annotations

import argparse
from pathlib import Path

import duckdb
import pandas as pd

REPO_ROOT = Path(__file__).resolve().parents[3]
PROCESSED_DIR = REPO_ROOT / "data" / "wikipedia" / "processed"
MULTIPLEX_DIR = PROCESSED_DIR / "multiplex"


def get_nth_link(con: duckdb.DuckDBPyConnection, page_id: int, n: int) -> tuple[str | None, int]:
    """Get the Nth link from a page and its total out-degree.

    Returns:
        (nth_link_title, out_degree) or (None, out_degree) if n > out_degree
    """
    result = con.execute("""
        SELECT to_title, link_position
        FROM links_prose
        WHERE from_id = ?
        ORDER BY link_position
    """, [page_id]).fetchall()

    out_degree = len(result)

    if n <= out_degree:
        # Find the link at position n
        for title, pos in result:
            if pos == n:
                return title, out_degree
        # Fallback: use index if positions don't match exactly
        if n <= len(result):
            return result[n-1][0], out_degree

    return None, out_degree


def get_page_title(con: duckdb.DuckDBPyConnection, page_id: int) -> str:
    """Get the title for a page_id."""
    result = con.execute("""
        SELECT title FROM pages WHERE page_id = ?
    """, [page_id]).fetchone()
    return result[0] if result else f"[unknown:{page_id}]"


def classify_mechanism(
    con: duckdb.DuckDBPyConnection,
    page_id: int,
    low_n: int,
    high_n: int,
) -> dict:
    """Classify the mechanism causing a tunnel transition between two N values."""

    # Get the Nth links at both N values
    link_low, out_degree = get_nth_link(con, page_id, low_n)
    link_high, _ = get_nth_link(con, page_id, high_n)

    # Determine mechanism
    if out_degree < high_n:
        # Page doesn't have enough links for the higher N
        mechanism = "halt_creation"
        explanation = f"Page has only {out_degree} links, but N={high_n} requires at least {high_n}"
    elif link_high is None:
        # Shouldn't happen if out_degree >= high_n, but handle gracefully
        mechanism = "link_not_found"
        explanation = f"Link at position {high_n} not found despite out_degree={out_degree}"
    elif link_low != link_high:
        # The Nth link changed - this is the most common case
        mechanism = "degree_shift"
        explanation = f"Link #{low_n} is '{link_low}' but link #{high_n} is '{link_high}'"
    else:
        # Same immediate link but different basins - must diverge downstream
        mechanism = "path_divergence"
        explanation = f"Both N={low_n} and N={high_n} start at '{link_low}' but paths diverge downstream"

    return {
        "mechanism": mechanism,
        "nth_link_at_low_n": link_low,
        "nth_link_at_high_n": link_high,
        "out_degree": out_degree,
        "explanation": explanation,
    }


def parse_transition(transition_str: str) -> tuple[int, int]:
    """Parse a transition string like 'N5→N6' into (5, 6)."""
    # Handle format: "N5→N6: basin1→basin2"
    if ":" in transition_str:
        transition_str = transition_str.split(":")[0].strip()

    parts = transition_str.replace("N", "").split("→")
    return int(parts[0]), int(parts[1])


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Classify mechanisms causing tunnel transitions"
    )
    parser.add_argument(
        "--input",
        type=Path,
        default=MULTIPLEX_DIR / "tunnel_classification.tsv",
        help="Input tunnel classification TSV",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=MULTIPLEX_DIR / "tunnel_mechanisms.tsv",
        help="Output mechanisms TSV",
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=0,
        help="Limit number of tunnel nodes to analyze (0 = all)",
    )
    parser.add_argument(
        "--sample",
        type=int,
        default=0,
        help="Random sample of tunnel nodes to analyze (0 = no sampling)",
    )
    args = parser.parse_args()

    print("=" * 70)
    print("Analyzing Tunnel Mechanisms")
    print("=" * 70)
    print()

    # Load tunnel classifications
    print(f"Loading {args.input}...")
    tunnels_df = pd.read_csv(args.input, sep="\t")
    print(f"  Loaded {len(tunnels_df):,} tunnel nodes")
    print()

    # Apply limit/sample
    if args.sample > 0:
        tunnels_df = tunnels_df.sample(n=min(args.sample, len(tunnels_df)), random_state=42)
        print(f"Sampled {len(tunnels_df):,} tunnel nodes")
    elif args.limit > 0:
        tunnels_df = tunnels_df.head(args.limit)
        print(f"Limited to {len(tunnels_df):,} tunnel nodes")
    print()

    # Connect to DuckDB for efficient queries
    print("Connecting to data sources...")
    con = duckdb.connect(":memory:")

    # Register parquet files as views
    con.execute(f"""
        CREATE VIEW links_prose AS
        SELECT * FROM read_parquet('{PROCESSED_DIR / "links_prose.parquet"}')
    """)
    con.execute(f"""
        CREATE VIEW pages AS
        SELECT * FROM read_parquet('{PROCESSED_DIR / "pages.parquet"}')
    """)
    print("  Registered links_prose and pages views")
    print()

    # Analyze each tunnel node
    print("Analyzing mechanisms...")
    results = []

    for idx, row in tunnels_df.iterrows():
        page_id = row["page_id"]
        transitions_str = row.get("switching_transitions", "")

        if pd.isna(transitions_str) or not transitions_str:
            continue

        # Get page title
        page_title = get_page_title(con, page_id)

        # Parse and analyze each transition
        for transition in transitions_str.split("; "):
            if "→" not in transition:
                continue

            try:
                low_n, high_n = parse_transition(transition)
            except (ValueError, IndexError):
                continue

            # Extract basin info from transition string
            if ":" in transition:
                basin_part = transition.split(": ", 1)[1]
                if "→" in basin_part:
                    from_basin, to_basin = basin_part.split("→", 1)
                else:
                    from_basin, to_basin = basin_part, ""
            else:
                from_basin = row.get("primary_basin", "")
                to_basin = row.get("secondary_basin", "")

            # Classify mechanism
            mechanism_info = classify_mechanism(con, page_id, low_n, high_n)

            results.append({
                "page_id": page_id,
                "page_title": page_title,
                "transition": f"N{low_n}→N{high_n}",
                "from_basin": from_basin[:50] if from_basin else "",
                "to_basin": to_basin[:50] if to_basin else "",
                **mechanism_info,
            })

        if len(results) % 500 == 0:
            print(f"  Processed {idx + 1:,} / {len(tunnels_df):,} tunnel nodes ({len(results):,} transitions)...", end="\r")

    print(f"  Processed {len(tunnels_df):,} tunnel nodes, {len(results):,} transitions")
    print()

    # Create output dataframe
    results_df = pd.DataFrame(results)

    # Statistics
    print("=" * 70)
    print("MECHANISM STATISTICS")
    print("=" * 70)
    print()

    if len(results_df) > 0:
        mech_counts = results_df["mechanism"].value_counts()
        print("Mechanism distribution:")
        for mech, count in mech_counts.items():
            pct = 100 * count / len(results_df)
            print(f"  {mech:20s}: {count:,} ({pct:.1f}%)")
        print()

        # Transition distribution
        print("Transition distribution:")
        trans_counts = results_df["transition"].value_counts().head(10)
        for trans, count in trans_counts.items():
            pct = 100 * count / len(results_df)
            print(f"  {trans:10s}: {count:,} ({pct:.1f}%)")
        print()

        # Out-degree statistics for each mechanism
        print("Out-degree by mechanism:")
        for mech in mech_counts.index:
            mech_df = results_df[results_df["mechanism"] == mech]
            mean_deg = mech_df["out_degree"].mean()
            median_deg = mech_df["out_degree"].median()
            print(f"  {mech:20s}: mean={mean_deg:.1f}, median={median_deg:.0f}")
        print()

        # Examples of each mechanism
        print("Examples of each mechanism:")
        for mech in mech_counts.index:
            examples = results_df[results_df["mechanism"] == mech].head(3)
            print(f"\n  {mech}:")
            for _, ex in examples.iterrows():
                print(f"    {ex['page_title'][:30]:30s} {ex['transition']}: {ex['explanation'][:50]}")
        print()
    else:
        print("No transitions found to analyze.")
        print()

    # Write output
    print(f"Writing to {args.output}...")
    results_df.to_csv(args.output, sep="\t", index=False)
    print(f"  {len(results_df):,} rows written")
    print()

    # Summary statistics file
    if len(results_df) > 0:
        summary_path = args.output.with_name("tunnel_mechanism_summary.tsv")
        summary_data = []
        for mech in results_df["mechanism"].unique():
            mech_df = results_df[results_df["mechanism"] == mech]
            summary_data.append({
                "mechanism": mech,
                "count": len(mech_df),
                "pct": 100 * len(mech_df) / len(results_df),
                "mean_out_degree": mech_df["out_degree"].mean(),
                "median_out_degree": mech_df["out_degree"].median(),
            })
        summary_df = pd.DataFrame(summary_data)
        summary_df.to_csv(summary_path, sep="\t", index=False)
        print(f"Wrote summary to {summary_path}")
        print()

    con.close()

    print("=" * 70)
    print("DONE")
    print("=" * 70)


if __name__ == "__main__":
    main()
