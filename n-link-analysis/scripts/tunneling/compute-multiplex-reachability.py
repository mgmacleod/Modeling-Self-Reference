#!/usr/bin/env python3
"""Compute reachability analysis in the multiplex graph.

This script analyzes how pages can reach each other across the multiplex,
enabling understanding of cross-N basin connectivity.

Analyses:
1. Reachability from cycle nodes: Which (page, N) pairs can reach each cycle?
2. Cross-N reachability: How do pages flow between N layers via tunneling?
3. Component analysis: Partition multiplex by connectivity patterns

Output:
- multiplex_reachability_summary.tsv: Statistics per cycle
- multiplex_cross_n_paths.tsv: Sample cross-N paths via tunneling

Data dependencies:
  - data/wikipedia/processed/multiplex/multiplex_edges.parquet
  - data/wikipedia/processed/multiplex/multiplex_basin_assignments.parquet
  - data/wikipedia/processed/multiplex/tunnel_nodes.parquet
"""

from __future__ import annotations

import argparse
from collections import defaultdict, deque
from pathlib import Path

import pandas as pd

REPO_ROOT = Path(__file__).resolve().parents[3]
PROCESSED_DIR = REPO_ROOT / "data" / "wikipedia" / "processed"
MULTIPLEX_DIR = PROCESSED_DIR / "multiplex"


def load_edges_as_graph(edges_path: Path) -> dict[tuple[int, int], list[tuple[int, int, str]]]:
    """Load multiplex edges as adjacency list.

    Returns: dict mapping (src_page, src_N) -> list of (dst_page, dst_N, edge_type)
    """
    print(f"Loading edges from {edges_path}...")
    df = pd.read_parquet(edges_path)
    print(f"  Loaded {len(df):,} edges")

    graph = defaultdict(list)
    for _, row in df.iterrows():
        src = (row["src_page_id"], row["src_N"])
        dst = (row["dst_page_id"], row["dst_N"])
        graph[src].append((dst[0], dst[1], row["edge_type"]))

    print(f"  Built graph with {len(graph):,} source nodes")
    return graph


def find_cycle_nodes(basin_path: Path) -> dict[str, list[int]]:
    """Extract cycle member page_ids from basin assignments.

    Returns: dict mapping cycle_key -> list of cycle member page_ids
    """
    print(f"Loading basin assignments from {basin_path}...")
    df = pd.read_parquet(basin_path)

    # Cycle members are pages at depth 0 (they are the cycle itself)
    # Actually, in our data, cycle members have entry_id == page_id for depth=1
    # Let's find pages that appear at depth=1 and are their own entry
    cycle_members = df[(df["depth"] == 1) & (df["page_id"] == df["entry_id"])]

    cycles = defaultdict(list)
    for _, row in cycle_members.iterrows():
        cycle_key = row.get("canonical_cycle_id", row.get("cycle_key", "unknown"))
        cycles[cycle_key].append(row["page_id"])

    print(f"  Found {len(cycles)} cycles with {sum(len(v) for v in cycles.values())} total members")
    return cycles


def bfs_reachability(
    graph: dict[tuple[int, int], list[tuple[int, int, str]]],
    start_nodes: list[tuple[int, int]],
    max_depth: int = 50,
) -> tuple[set[tuple[int, int]], dict[tuple[int, int], int]]:
    """BFS to find all nodes reachable from start_nodes.

    Returns: (reachable_nodes, depth_map)
    """
    visited = set()
    depth_map = {}
    queue = deque()

    for node in start_nodes:
        if node not in visited:
            visited.add(node)
            depth_map[node] = 0
            queue.append((node, 0))

    while queue:
        current, depth = queue.popleft()

        if depth >= max_depth:
            continue

        for dst_page, dst_n, edge_type in graph.get(current, []):
            neighbor = (dst_page, dst_n)
            if neighbor not in visited:
                visited.add(neighbor)
                depth_map[neighbor] = depth + 1
                queue.append((neighbor, depth + 1))

    return visited, depth_map


def analyze_cross_n_paths(
    graph: dict[tuple[int, int], list[tuple[int, int, str]]],
    tunnel_nodes: set[int],
    n_values: list[int],
    sample_size: int = 100,
) -> list[dict]:
    """Find example paths that cross N layers via tunneling."""
    cross_n_paths = []

    # Sample tunnel nodes
    tunnel_list = list(tunnel_nodes)[:sample_size]

    for page_id in tunnel_list:
        # Check which N values this page appears at
        present_at = []
        for n in n_values:
            if (page_id, n) in graph:
                present_at.append(n)

        if len(present_at) >= 2:
            # This page can tunnel between N values
            path_info = {
                "page_id": page_id,
                "n_values": ",".join(str(n) for n in present_at),
                "n_count": len(present_at),
            }

            # Check if there are tunnel edges
            for n in present_at:
                for dst_page, dst_n, edge_type in graph.get((page_id, n), []):
                    if edge_type == "tunnel":
                        path_info["has_tunnel_edge"] = True
                        break

            cross_n_paths.append(path_info)

    return cross_n_paths


def compute_layer_connectivity(
    graph: dict[tuple[int, int], list[tuple[int, int, str]]],
    n_values: list[int],
) -> dict[tuple[int, int], int]:
    """Compute connectivity between N layers.

    Returns: dict mapping (N1, N2) -> count of edges from N1 to N2
    """
    connectivity = defaultdict(int)

    for (src_page, src_n), neighbors in graph.items():
        for dst_page, dst_n, edge_type in neighbors:
            connectivity[(src_n, dst_n)] += 1

    return connectivity


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Compute multiplex reachability analysis"
    )
    parser.add_argument(
        "--edges",
        type=Path,
        default=MULTIPLEX_DIR / "multiplex_edges.parquet",
        help="Multiplex edges parquet",
    )
    parser.add_argument(
        "--basins",
        type=Path,
        default=MULTIPLEX_DIR / "multiplex_basin_assignments.parquet",
        help="Basin assignments parquet",
    )
    parser.add_argument(
        "--tunnel-nodes",
        type=Path,
        default=MULTIPLEX_DIR / "tunnel_nodes.parquet",
        help="Tunnel nodes parquet",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=MULTIPLEX_DIR,
        help="Output directory",
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
    parser.add_argument(
        "--max-reachability-depth",
        type=int,
        default=20,
        help="Maximum BFS depth for reachability analysis",
    )
    args = parser.parse_args()

    print("=" * 70)
    print("Computing Multiplex Reachability")
    print("=" * 70)
    print()

    n_values = list(range(args.n_min, args.n_max + 1))

    # Load graph
    graph = load_edges_as_graph(args.edges)
    print()

    # Find cycle nodes
    cycles = find_cycle_nodes(args.basins)
    print()

    # Load tunnel nodes
    print(f"Loading tunnel nodes from {args.tunnel_nodes}...")
    tunnel_df = pd.read_parquet(args.tunnel_nodes)
    tunnel_node_ids = set(tunnel_df[tunnel_df["is_tunnel_node"] == True]["page_id"])
    print(f"  {len(tunnel_node_ids):,} tunnel nodes")
    print()

    # Analysis 1: Layer connectivity matrix
    print("Computing layer connectivity...")
    connectivity = compute_layer_connectivity(graph, n_values)

    print()
    print("=" * 70)
    print("LAYER CONNECTIVITY MATRIX")
    print("=" * 70)
    print()
    print("Edge counts from source N (row) to destination N (column):")
    print()

    # Build matrix
    print(f"{'Src\\Dst':>8}", end="")
    for n in n_values:
        print(f"{n:>12}", end="")
    print()
    print("-" * (8 + 12 * len(n_values)))

    for src_n in n_values:
        print(f"{src_n:>8}", end="")
        for dst_n in n_values:
            count = connectivity.get((src_n, dst_n), 0)
            if count > 0:
                print(f"{count:>12,}", end="")
            else:
                print(f"{'---':>12}", end="")
        print()
    print()

    # Analysis 2: Reachability from each cycle
    print("=" * 70)
    print("CYCLE REACHABILITY ANALYSIS")
    print("=" * 70)
    print()

    reachability_stats = []

    for cycle_key, members in list(cycles.items())[:10]:  # Top 10 cycles
        print(f"Analyzing cycle: {cycle_key[:40]}...")

        # Create start nodes at each N value
        start_nodes = []
        for page_id in members:
            for n in n_values:
                if (page_id, n) in graph or any(
                    (page_id, n) in [tuple(x[:2]) for x in neighbors]
                    for neighbors in graph.values()
                ):
                    start_nodes.append((page_id, n))

        if not start_nodes:
            print(f"  No nodes in graph, skipping")
            continue

        # BFS from cycle nodes
        reachable, depth_map = bfs_reachability(
            graph, start_nodes, max_depth=args.max_reachability_depth
        )

        # Analyze reachable nodes by N layer
        nodes_by_n = defaultdict(int)
        for page_id, n in reachable:
            nodes_by_n[n] += 1

        # Count tunnel nodes in reachable set
        tunnel_reachable = sum(1 for page_id, n in reachable if page_id in tunnel_node_ids)

        stats = {
            "cycle": cycle_key,
            "cycle_members": len(members),
            "start_nodes": len(start_nodes),
            "total_reachable": len(reachable),
            "tunnel_reachable": tunnel_reachable,
            "max_depth_reached": max(depth_map.values()) if depth_map else 0,
        }

        for n in n_values:
            stats[f"reachable_N{n}"] = nodes_by_n.get(n, 0)

        reachability_stats.append(stats)

        print(f"  Start nodes: {len(start_nodes):,}")
        print(f"  Reachable: {len(reachable):,} (max depth: {stats['max_depth_reached']})")
        print(f"  By N: {dict(nodes_by_n)}")
        print()

    # Analysis 3: Cross-N path examples
    print("=" * 70)
    print("CROSS-N PATH ANALYSIS")
    print("=" * 70)
    print()

    cross_n_paths = analyze_cross_n_paths(graph, tunnel_node_ids, n_values, sample_size=50)

    print(f"Analyzed {len(cross_n_paths)} tunnel nodes for cross-N connectivity")
    if cross_n_paths:
        n_count_dist = defaultdict(int)
        for path in cross_n_paths:
            n_count_dist[path["n_count"]] += 1

        print("\nN-layer coverage distribution:")
        for n_count, count in sorted(n_count_dist.items()):
            print(f"  {n_count} N layers: {count} tunnel nodes")

    print()

    # Write outputs
    print("=" * 70)
    print("WRITING OUTPUTS")
    print("=" * 70)
    print()

    # Reachability summary
    if reachability_stats:
        reach_df = pd.DataFrame(reachability_stats)
        reach_path = args.output_dir / "multiplex_reachability_summary.tsv"
        reach_df.to_csv(reach_path, sep="\t", index=False)
        print(f"Wrote reachability summary to {reach_path}")

    # Cross-N paths
    if cross_n_paths:
        paths_df = pd.DataFrame(cross_n_paths)
        paths_path = args.output_dir / "multiplex_cross_n_paths.tsv"
        paths_df.to_csv(paths_path, sep="\t", index=False)
        print(f"Wrote cross-N paths to {paths_path}")

    # Layer connectivity
    conn_data = [
        {"src_N": src_n, "dst_N": dst_n, "edge_count": count}
        for (src_n, dst_n), count in sorted(connectivity.items())
    ]
    conn_df = pd.DataFrame(conn_data)
    conn_path = args.output_dir / "multiplex_layer_connectivity.tsv"
    conn_df.to_csv(conn_path, sep="\t", index=False)
    print(f"Wrote layer connectivity to {conn_path}")

    print()
    print("=" * 70)
    print("DONE")
    print("=" * 70)


if __name__ == "__main__":
    main()
