#!/usr/bin/env python3
"""Extract semantic model from tunneling analysis per Algorithm 5.2.

This script implements Phase 4 of Algorithm 5.2 from database-inference-graph-theory.md,
reconstructing a semantic model from the multiplex/tunneling analysis.

Semantic Model Components:
  1. Central entities: Pages with high tunnel frequency across N values
  2. Peripheral entities: Pages isolated in single basins across all N
  3. Subsystem boundaries: Basin partitions that persist across multiple N
  4. Hidden relationships: Tunnels revealing connections not visible at single N

Output: semantic_model_wikipedia.json with structured semantic information

Data dependencies:
  - data/wikipedia/processed/multiplex/tunnel_nodes.parquet
  - data/wikipedia/processed/multiplex/tunnel_frequency_ranking.tsv
  - data/wikipedia/processed/multiplex/basin_stability_scores.tsv
  - data/wikipedia/processed/multiplex/basin_flows.tsv
  - data/wikipedia/processed/pages.parquet
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from datetime import datetime

import duckdb
import pandas as pd

REPO_ROOT = Path(__file__).resolve().parents[2]
PROCESSED_DIR = REPO_ROOT / "data" / "wikipedia" / "processed"
MULTIPLEX_DIR = PROCESSED_DIR / "multiplex"


def extract_central_entities(
    tunnel_freq_df: pd.DataFrame,
    con: duckdb.DuckDBPyConnection,
    top_n: int = 100,
) -> list[dict]:
    """Extract central entities based on tunnel frequency.

    Central entities are pages that act as tunnels between many basins,
    indicating semantic importance in the knowledge graph.
    """
    # Get top tunnel nodes by score
    top_tunnels = tunnel_freq_df.nlargest(top_n, "tunnel_score")

    central_entities = []
    for _, row in top_tunnels.iterrows():
        page_id = row["page_id"]

        # Get page title
        result = con.execute(
            "SELECT title FROM pages WHERE page_id = ?", [int(page_id)]
        ).fetchone()
        title = result[0] if result else f"[page:{page_id}]"

        central_entities.append({
            "page_id": int(page_id),
            "title": title,
            "tunnel_score": float(row["tunnel_score"]),
            "basins_bridged": int(row["n_basins_bridged"]),
            "transitions": int(row["n_transitions"]),
            "mean_depth": float(row["mean_depth"]),
            "tunnel_type": row.get("tunnel_type", "unknown"),
            "basin_list": row.get("basin_list", ""),
        })

    return central_entities


def extract_subsystem_boundaries(
    stability_df: pd.DataFrame,
) -> list[dict]:
    """Extract subsystem boundaries from basin stability analysis.

    Stable basins (high persistence across N) represent coherent subsystems
    in the knowledge graph.
    """
    subsystems = []

    for _, row in stability_df.iterrows():
        subsystems.append({
            "basin_id": row["canonical_cycle_id"],
            "stability_class": row["stability_class"],
            "persistence_score": float(row["persistence_score"]),
            "mean_jaccard": float(row["mean_jaccard"]),
            "max_stable_range": int(row["max_stable_range"]),
            "n_values_present": int(row["n_values_present"]),
            "total_pages": int(row["total_pages"]),
        })

    # Sort by stability (most stable first)
    subsystems.sort(key=lambda x: -x["persistence_score"])

    return subsystems


def extract_hidden_relationships(
    flows_df: pd.DataFrame,
    tunnel_freq_df: pd.DataFrame,
) -> list[dict]:
    """Extract hidden relationships revealed by tunneling.

    Cross-basin flows at N transitions reveal relationships between
    knowledge domains that aren't visible when looking at any single N.
    """
    relationships = []

    # Major flows between basins
    for _, row in flows_df.iterrows():
        relationships.append({
            "type": "cross_n_flow",
            "from_basin": row["from_basin"],
            "to_basin": row["to_basin"],
            "from_n": int(row["from_n"]),
            "to_n": int(row["to_n"]),
            "page_count": int(row["count"]),
            "strength": "strong" if row["count"] > 500 else "moderate" if row["count"] > 100 else "weak",
        })

    # Tunnel bridges (pages connecting multiple basins)
    alternating_tunnels = tunnel_freq_df[tunnel_freq_df["tunnel_type"] == "alternating"]
    for _, row in alternating_tunnels.head(20).iterrows():
        relationships.append({
            "type": "alternating_tunnel",
            "page_id": int(row["page_id"]),
            "basins": row.get("basin_list", ""),
            "transitions": int(row["n_transitions"]),
            "description": "Page alternates between basins as N changes (non-monotonic)",
        })

    return relationships


def compute_summary_statistics(
    tunnel_nodes_df: pd.DataFrame,
    tunnel_freq_df: pd.DataFrame,
    stability_df: pd.DataFrame,
    flows_df: pd.DataFrame,
) -> dict:
    """Compute summary statistics for the semantic model."""

    n_tunnel_nodes = len(tunnel_nodes_df[tunnel_nodes_df["is_tunnel_node"] == True])
    n_total_pages = len(tunnel_nodes_df)

    return {
        "total_pages_in_hyperstructure": int(n_total_pages),
        "tunnel_nodes": int(n_tunnel_nodes),
        "tunnel_percentage": round(100 * n_tunnel_nodes / n_total_pages, 2) if n_total_pages > 0 else 0,
        "n_basins": len(stability_df),
        "stable_basins": len(stability_df[stability_df["stability_class"] == "stable"]),
        "moderate_basins": len(stability_df[stability_df["stability_class"] == "moderate"]),
        "fragile_basins": len(stability_df[stability_df["stability_class"] == "fragile"]),
        "cross_basin_flows": len(flows_df),
        "total_flow_volume": int(flows_df["count"].sum()) if len(flows_df) > 0 else 0,
        "mean_tunnel_score": float(tunnel_freq_df["tunnel_score"].mean()) if len(tunnel_freq_df) > 0 else 0,
        "max_tunnel_score": float(tunnel_freq_df["tunnel_score"].max()) if len(tunnel_freq_df) > 0 else 0,
    }


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Extract semantic model from tunneling analysis"
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=MULTIPLEX_DIR / "semantic_model_wikipedia.json",
        help="Output JSON file",
    )
    parser.add_argument(
        "--top-central",
        type=int,
        default=100,
        help="Number of top central entities to extract",
    )
    args = parser.parse_args()

    print("=" * 70)
    print("Computing Semantic Model (Algorithm 5.2 Phase 4)")
    print("=" * 70)
    print()

    # Connect to data
    print("Loading data sources...")
    con = duckdb.connect(":memory:")
    con.execute(f"""
        CREATE VIEW pages AS
        SELECT * FROM read_parquet('{PROCESSED_DIR / "pages.parquet"}')
    """)

    # Load tunnel data
    tunnel_nodes_df = pd.read_parquet(MULTIPLEX_DIR / "tunnel_nodes.parquet")
    print(f"  Tunnel nodes: {len(tunnel_nodes_df):,} pages")

    tunnel_freq_df = pd.read_csv(MULTIPLEX_DIR / "tunnel_frequency_ranking.tsv", sep="\t")
    print(f"  Tunnel frequency rankings: {len(tunnel_freq_df):,} entries")

    stability_df = pd.read_csv(MULTIPLEX_DIR / "basin_stability_scores.tsv", sep="\t")
    print(f"  Basin stability scores: {len(stability_df):,} basins")

    flows_df = pd.read_csv(MULTIPLEX_DIR / "basin_flows.tsv", sep="\t")
    print(f"  Cross-basin flows: {len(flows_df):,} flows")
    print()

    # Extract semantic model components
    print("Extracting semantic model components...")

    print("  1. Central entities (high tunnel frequency)...")
    central_entities = extract_central_entities(tunnel_freq_df, con, args.top_central)
    print(f"     Found {len(central_entities)} central entities")

    print("  2. Subsystem boundaries (stable basins)...")
    subsystem_boundaries = extract_subsystem_boundaries(stability_df)
    print(f"     Found {len(subsystem_boundaries)} subsystems")

    print("  3. Hidden relationships (cross-N flows)...")
    hidden_relationships = extract_hidden_relationships(flows_df, tunnel_freq_df)
    print(f"     Found {len(hidden_relationships)} relationships")

    print("  4. Summary statistics...")
    summary = compute_summary_statistics(
        tunnel_nodes_df, tunnel_freq_df, stability_df, flows_df
    )
    print()

    # Construct semantic model
    semantic_model = {
        "metadata": {
            "generated_at": datetime.now().isoformat(),
            "algorithm": "Algorithm 5.2 Phase 4 (Schema Discovery via Tunneling)",
            "source": "Wikipedia English (enwiki-20251220)",
            "n_range": [3, 7],
            "theory_document": "database-inference-graph-theory.md",
        },
        "summary": summary,
        "central_entities": central_entities,
        "subsystem_boundaries": subsystem_boundaries,
        "hidden_relationships": hidden_relationships,
    }

    # Print summary
    print("=" * 70)
    print("SEMANTIC MODEL SUMMARY")
    print("=" * 70)
    print()
    print(f"Total pages in hyperstructure: {summary['total_pages_in_hyperstructure']:,}")
    print(f"Tunnel nodes: {summary['tunnel_nodes']:,} ({summary['tunnel_percentage']:.2f}%)")
    print()
    print(f"Basins: {summary['n_basins']} total")
    print(f"  - Stable: {summary['stable_basins']}")
    print(f"  - Moderate: {summary['moderate_basins']}")
    print(f"  - Fragile: {summary['fragile_basins']}")
    print()
    print(f"Cross-basin flows: {summary['cross_basin_flows']}")
    print(f"Total flow volume: {summary['total_flow_volume']:,} pages")
    print()

    print("Top 10 Central Entities:")
    for i, entity in enumerate(central_entities[:10], 1):
        print(f"  {i:2d}. {entity['title'][:40]:40s} (score={entity['tunnel_score']:.1f}, bridges={entity['basins_bridged']})")
    print()

    print("Subsystem Stability:")
    for subsystem in subsystem_boundaries:
        print(f"  {subsystem['basin_id'][:40]:40s}: {subsystem['stability_class']} (p={subsystem['persistence_score']:.2f})")
    print()

    # Write output
    print(f"Writing to {args.output}...")
    with open(args.output, "w") as f:
        json.dump(semantic_model, f, indent=2)
    print(f"  {args.output.stat().st_size / 1024:.1f} KB written")
    print()

    con.close()

    print("=" * 70)
    print("DONE")
    print("=" * 70)


if __name__ == "__main__":
    main()
