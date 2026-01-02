#!/usr/bin/env python3
"""Analyze "branch" structure feeding a terminal cycle under the fixed N-link rule.

Context
-------
For a fixed N, the map f_N induces a functional graph (each node has <=1 successor;
HALT nodes have no successor). For a chosen terminal cycle, the reverse-reachable
set (the basin) forms a forest of rooted trees attached to the cycle nodes.

This script makes the "river/tributary" intuition measurable by defining:

- entry node: a depth-1 predecessor of the cycle (one step upstream from cycle)
- branch: the subtree whose unique downstream path reaches the cycle via that
  entry node (i.e., the set of nodes whose last non-cycle node is that entry)
- thickness(branch): number of nodes in that subtree (including the entry node)

Outputs
-------
- Writes a TSV of branch sizes and metadata (titles, which cycle node it enters).
- Optionally writes membership for the top-K branches (as Parquet: page_id, entry_id, depth).

Notes
-----
- Uses the pre-materialized edges DB: data/wikipedia/processed/analysis/edges_n={N}.duckdb
  produced by map-basin-from-cycle.py (or materializes it if absent).
- Uses a reverse BFS with label propagation:
    depth 0: cycle nodes
    depth 1: entry_id := src_page_id
    depth >1: entry_id := parent's entry_id

"""

from __future__ import annotations

import argparse
from pathlib import Path

from data_loader import get_data_loader

from _core.basin_engine import resolve_titles_to_ids
from _core.branch_engine import analyze_branches


REPO_ROOT = Path(__file__).resolve().parents[1]
PROCESSED_DIR = REPO_ROOT.parent / "data" / "wikipedia" / "processed"
ANALYSIS_DIR = PROCESSED_DIR / "analysis"


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Quantify branch (entry-subtree) sizes feeding a given cycle under f_N.",
    )
    parser.add_argument("--n", type=int, default=5, help="N for fixed N-link rule (default: 5)")
    parser.add_argument("--cycle-page-id", type=int, action="append", default=[], help="Cycle node page_id (repeatable)")
    parser.add_argument("--cycle-title", type=str, action="append", default=[], help="Cycle node title (exact match; repeatable)")
    parser.add_argument("--namespace", type=int, default=0, help="Namespace for resolving --cycle-title (default: 0)")
    parser.add_argument(
        "--allow-redirects",
        action="store_true",
        help="Allow resolving --cycle-title to redirects (default: false)",
    )
    parser.add_argument(
        "--max-depth",
        type=int,
        default=0,
        help="Stop after this many reverse layers (default: 0 = no limit)",
    )
    parser.add_argument(
        "--log-every",
        type=int,
        default=10,
        help="Print progress every N layers (default: 10)",
    )
    parser.add_argument(
        "--top-k",
        type=int,
        default=25,
        help="Report the top-K branches by size (default: 25)",
    )
    parser.add_argument(
        "--write-membership-top-k",
        type=int,
        default=0,
        help="Write membership parquet for the top-K branches (default: 0 = none)",
    )
    parser.add_argument(
        "--out-prefix",
        type=str,
        default=None,
        help="Output prefix under analysis/. Default: branches_from_cycle_n=...",
    )

    args = parser.parse_args()

    if args.n <= 0:
        raise SystemExit("--n must be >= 1")

    # Get loader
    loader = get_data_loader()

    # Resolve titles to IDs
    title_to_id = resolve_titles_to_ids(
        list(args.cycle_title),
        loader,
        namespace=int(args.namespace),
        allow_redirects=bool(args.allow_redirects),
    )
    missing_titles = [t for t in args.cycle_title if t not in title_to_id]
    if missing_titles:
        raise SystemExit(f"Could not resolve titles to page_id (exact match failed): {missing_titles}")

    cycle_ids = list(dict.fromkeys([*map(int, args.cycle_page_id), *title_to_id.values()]))
    if not cycle_ids:
        raise SystemExit("Provide at least one --cycle-page-id or --cycle-title")

    ANALYSIS_DIR.mkdir(parents=True, exist_ok=True)

    # Run branch analysis
    result = analyze_branches(
        loader,
        n=int(args.n),
        cycle_page_ids=cycle_ids,
        max_depth=int(args.max_depth),
        log_every=int(args.log_every),
        top_k=int(args.top_k),
        write_top_k_membership=int(args.write_membership_top_k),
        out_prefix=args.out_prefix,
        verbose=True,
    )

    print(f"\nBranch analysis complete:")
    print(f"  Total basin nodes: {result.total_basin_nodes:,}")
    print(f"  Number of branches: {result.num_branches:,}")
    print(f"  Max depth: {result.max_depth_reached}")
    print(f"  Elapsed: {result.elapsed_seconds:.1f}s")

    if result.branches:
        print(f"\nTop {len(result.branches)} branches:")
        for b in result.branches[:10]:
            title = b.entry_title or f"<{b.entry_id}>"
            print(f"  {b.rank}. {title}: {b.basin_size:,} nodes (depth {b.max_depth})")


if __name__ == "__main__":
    main()
