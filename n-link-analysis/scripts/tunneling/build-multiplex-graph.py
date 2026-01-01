#!/usr/bin/env python3
"""Build multiplex graph connecting (page_id, N) nodes.

This script constructs the multiplex graph structure where:
- Nodes are (page_id, N) tuples
- Within-N edges: f_N(page) → successor under N-link rule
- Tunneling edges: (page_id, N1) ↔ (page_id, N2) for same page across N

The multiplex graph enables cross-N reachability analysis and visualization
of how pages flow between different basins as N changes.

Output schema for multiplex_edges.parquet:
  src_page_id: int64
  src_N: int8
  dst_page_id: int64
  dst_N: int8
  edge_type: string  # "within_N" or "tunnel"

Data dependencies:
  - data/wikipedia/processed/nlink_sequences.parquet (for within-N edges)
  - data/wikipedia/processed/multiplex/tunnel_nodes.parquet (for tunnel edges)
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
NLINK_SEQ_PATH = PROCESSED_DIR / "nlink_sequences.parquet"


def build_within_n_edges(
    con: duckdb.DuckDBPyConnection,
    n_values: list[int],
    page_ids: set[int] | None = None,
    limit: int | None = None,
) -> pa.Table:
    """Build within-N edges from nlink_sequences.

    For each page with at least N links, creates edge:
    (page_id, N) → (link_sequence[N-1], N)
    """
    all_edges = []

    for n in n_values:
        print(f"  Building within-N edges for N={n}...", end=" ", flush=True)

        # Build query
        if page_ids is not None:
            page_filter = f"AND page_id IN ({','.join(str(p) for p in page_ids)})"
        else:
            page_filter = ""

        limit_clause = f"LIMIT {limit}" if limit else ""

        query = f"""
            SELECT
                page_id AS src_page_id,
                CAST({n} AS TINYINT) AS src_N,
                link_sequence[{n}] AS dst_page_id,
                CAST({n} AS TINYINT) AS dst_N,
                'within_N' AS edge_type
            FROM read_parquet('{NLINK_SEQ_PATH}')
            WHERE len(link_sequence) >= {n}
            {page_filter}
            {limit_clause}
        """

        result = con.execute(query).fetch_arrow_table()

        # Ensure consistent schema
        result = pa.table({
            "src_page_id": result.column("src_page_id").cast(pa.int64()),
            "src_N": result.column("src_N").cast(pa.int8()),
            "dst_page_id": result.column("dst_page_id").cast(pa.int64()),
            "dst_N": result.column("dst_N").cast(pa.int8()),
            "edge_type": result.column("edge_type"),
        })

        print(f"{len(result):,} edges")
        all_edges.append(result)

    if not all_edges:
        return pa.table({
            "src_page_id": pa.array([], type=pa.int64()),
            "src_N": pa.array([], type=pa.int8()),
            "dst_page_id": pa.array([], type=pa.int64()),
            "dst_N": pa.array([], type=pa.int8()),
            "edge_type": pa.array([], type=pa.string()),
        })

    return pa.concat_tables(all_edges)


def build_tunnel_edges(
    tunnel_nodes_path: Path,
    n_values: list[int],
) -> pa.Table:
    """Build tunnel edges connecting same page across different N values.

    For each tunnel node (page in multiple basins), creates bidirectional
    edges between all (page_id, N1) and (page_id, N2) pairs where the page
    has basin assignments.
    """
    print("  Building tunnel edges...", end=" ", flush=True)

    import pandas as pd

    # Load tunnel nodes
    tunnel_df = pd.read_parquet(tunnel_nodes_path)
    tunnel_df = tunnel_df[tunnel_df["is_tunnel_node"] == True]

    basin_cols = [f"basin_at_N{n}" for n in n_values]

    edges = []
    for _, row in tunnel_df.iterrows():
        page_id = row["page_id"]

        # Find which N values have basin assignments
        assigned_n = []
        for col in basin_cols:
            if col in row and pd.notna(row[col]):
                n = int(col.replace("basin_at_N", ""))
                assigned_n.append(n)

        # Create edges between all pairs of assigned N values
        for i, n1 in enumerate(assigned_n):
            for n2 in assigned_n[i + 1 :]:
                # Bidirectional tunnel edges
                edges.append({
                    "src_page_id": page_id,
                    "src_N": n1,
                    "dst_page_id": page_id,
                    "dst_N": n2,
                    "edge_type": "tunnel",
                })
                edges.append({
                    "src_page_id": page_id,
                    "src_N": n2,
                    "dst_page_id": page_id,
                    "dst_N": n1,
                    "edge_type": "tunnel",
                })

    print(f"{len(edges):,} edges")

    if not edges:
        return pa.table({
            "src_page_id": pa.array([], type=pa.int64()),
            "src_N": pa.array([], type=pa.int8()),
            "dst_page_id": pa.array([], type=pa.int64()),
            "dst_N": pa.array([], type=pa.int8()),
            "edge_type": pa.array([], type=pa.string()),
        })

    edge_df = pd.DataFrame(edges)

    # Ensure consistent types
    return pa.table({
        "src_page_id": pa.array(edge_df["src_page_id"].values, type=pa.int64()),
        "src_N": pa.array(edge_df["src_N"].values, type=pa.int8()),
        "dst_page_id": pa.array(edge_df["dst_page_id"].values, type=pa.int64()),
        "dst_N": pa.array(edge_df["dst_N"].values, type=pa.int8()),
        "edge_type": pa.array(edge_df["edge_type"].values, type=pa.string()),
    })


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Build multiplex graph connecting (page_id, N) nodes"
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=MULTIPLEX_DIR / "multiplex_edges.parquet",
        help="Output parquet path",
    )
    parser.add_argument(
        "--tunnel-nodes",
        type=Path,
        default=MULTIPLEX_DIR / "tunnel_nodes.parquet",
        help="Tunnel nodes parquet (for tunnel edges)",
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
        "--sample",
        type=int,
        default=None,
        help="Sample size per N (for testing, default: all)",
    )
    parser.add_argument(
        "--tunnel-nodes-only",
        action="store_true",
        help="Only build graph for pages that are tunnel nodes",
    )
    parser.add_argument(
        "--basin-pages-only",
        action="store_true",
        help="Only include pages that appear in basin assignments",
    )
    args = parser.parse_args()

    print("=" * 70)
    print("Building Multiplex Graph")
    print("=" * 70)
    print()

    n_values = list(range(args.n_min, args.n_max + 1))
    print(f"N values: {n_values}")
    print()

    # Connect to DuckDB
    con = duckdb.connect()

    # Determine which pages to include
    page_ids = None

    if args.tunnel_nodes_only:
        print("Mode: Tunnel nodes only")
        import pandas as pd
        tunnel_df = pd.read_parquet(args.tunnel_nodes)
        page_ids = set(tunnel_df[tunnel_df["is_tunnel_node"] == True]["page_id"])
        print(f"  {len(page_ids):,} tunnel node pages")
        print()

    elif args.basin_pages_only:
        print("Mode: Basin pages only")
        basin_path = MULTIPLEX_DIR / "multiplex_basin_assignments.parquet"
        import pandas as pd
        basin_df = pd.read_parquet(basin_path, columns=["page_id"])
        page_ids = set(basin_df["page_id"].unique())
        print(f"  {len(page_ids):,} pages in basins")
        print()

    # Build within-N edges
    print("Building within-N edges...")
    within_n_edges = build_within_n_edges(
        con, n_values, page_ids=page_ids, limit=args.sample
    )
    print(f"  Total within-N edges: {len(within_n_edges):,}")
    print()

    # Build tunnel edges
    print("Building tunnel edges...")
    if args.tunnel_nodes.exists():
        tunnel_edges = build_tunnel_edges(args.tunnel_nodes, n_values)
        print(f"  Total tunnel edges: {len(tunnel_edges):,}")
    else:
        print(f"  Warning: {args.tunnel_nodes} not found, skipping tunnel edges")
        tunnel_edges = pa.table({
            "src_page_id": pa.array([], type=pa.int64()),
            "src_N": pa.array([], type=pa.int8()),
            "dst_page_id": pa.array([], type=pa.int64()),
            "dst_N": pa.array([], type=pa.int8()),
            "edge_type": pa.array([], type=pa.string()),
        })
    print()

    # Combine edges
    print("Combining edges...")
    all_edges = pa.concat_tables([within_n_edges, tunnel_edges])
    print(f"  Total edges: {len(all_edges):,}")
    print()

    # Statistics
    print("=" * 70)
    print("MULTIPLEX GRAPH STATISTICS")
    print("=" * 70)
    print()

    # Count edges by type
    import pandas as pd
    edge_df = all_edges.to_pandas()

    print("Edge type distribution:")
    type_counts = edge_df["edge_type"].value_counts()
    for edge_type, count in type_counts.items():
        pct = 100 * count / len(edge_df)
        print(f"  {edge_type}: {count:,} ({pct:.1f}%)")
    print()

    # Count edges by N
    print("Within-N edges by source N:")
    within_n = edge_df[edge_df["edge_type"] == "within_N"]
    n_counts = within_n["src_N"].value_counts().sort_index()
    for n, count in n_counts.items():
        print(f"  N={n}: {count:,}")
    print()

    # Unique nodes
    src_nodes = set(zip(edge_df["src_page_id"], edge_df["src_N"]))
    dst_nodes = set(zip(edge_df["dst_page_id"], edge_df["dst_N"]))
    all_nodes = src_nodes | dst_nodes
    print(f"Unique (page_id, N) nodes: {len(all_nodes):,}")
    print(f"  Source nodes: {len(src_nodes):,}")
    print(f"  Destination nodes: {len(dst_nodes):,}")
    print()

    # Write output
    print(f"Writing to {args.output}...")
    args.output.parent.mkdir(parents=True, exist_ok=True)
    pq.write_table(all_edges, args.output, compression="snappy")
    print(f"  Size: {args.output.stat().st_size / 1024 / 1024:.2f} MB")
    print()

    print("=" * 70)
    print("DONE")
    print("=" * 70)


if __name__ == "__main__":
    main()
