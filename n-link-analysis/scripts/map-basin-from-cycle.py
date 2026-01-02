#!/usr/bin/env python3
"""Map the basin feeding a given cycle under the fixed N-link rule.

This computes reverse reachability (ancestor set) of a cycle under:
  f_N(page) = Nth outgoing link if it exists, else HALT.

Important: this does NOT enumerate all distinct paths (which can blow up).
Instead, it computes the *set* of pages that flow into the cycle using a
reverse BFS with deduplication (each node is added once).

Implementation strategy (parsimonious)
-------------------------------------
- Materialize an edge table once in a small DuckDB database:
    edges(src_page_id, dst_page_id)
  containing only pages with a defined Nth link.
- Iteratively expand:
    frontier_{t+1} = { src : (src -> dst) and dst in frontier_t and src not in seen }
    seen = seen ∪ frontier_{t+1}

Outputs
-------
- Prints layer-by-layer growth and totals.
- Writes a TSV with layer sizes.
- Optionally writes the full membership set (as Parquet) which may be large.

"""

from __future__ import annotations

import argparse
from pathlib import Path

from data_loader import get_data_loader

from _core.basin_engine import map_basin, resolve_titles_to_ids


REPO_ROOT = Path(__file__).resolve().parents[1]
PROCESSED_DIR = REPO_ROOT.parent / "data" / "wikipedia" / "processed"
ANALYSIS_DIR = PROCESSED_DIR / "analysis"


def main() -> None:
    parser = argparse.ArgumentParser(description="Map the reverse basin (ancestor set) feeding a given cycle under f_N.")
    parser.add_argument("--n", type=int, default=5, help="N for fixed N-link rule (default: 5)")
    parser.add_argument(
        "--cycle-page-id",
        type=int,
        action="append",
        default=[],
        help="Cycle node page_id (repeatable)",
    )
    parser.add_argument(
        "--cycle-title",
        type=str,
        action="append",
        default=[],
        help="Cycle node title (exact match; repeatable)",
    )
    parser.add_argument(
        "--namespace",
        type=int,
        default=0,
        help="Namespace for resolving --cycle-title (default: 0)",
    )
    parser.add_argument(
        "--allow-redirects",
        action="store_true",
        help="Allow resolving --cycle-title to redirects (default: false)",
    )
    parser.add_argument(
        "--max-depth",
        type=int,
        default=25,
        help="Stop after this many reverse layers (default: 25; 0 = no limit)",
    )
    parser.add_argument(
        "--log-every",
        type=int,
        default=1,
        help="Print progress every N layers (default: 1)",
    )
    parser.add_argument(
        "--max-nodes",
        type=int,
        default=0,
        help="Stop after discovering this many total nodes (default: 0 = no limit)",
    )
    parser.add_argument(
        "--write-membership",
        action="store_true",
        help="Write the discovered node set to Parquet (may be large)",
    )
    parser.add_argument(
        "--out-prefix",
        type=str,
        default=None,
        help="Output prefix under analysis/. Default: basin_from_cycle_n=...",
    )

    args = parser.parse_args()

    if args.n <= 0:
        raise SystemExit("--n must be >= 1")

    # Get loader
    loader = get_data_loader()

    # Resolve titles to IDs
    title_to_id = resolve_titles_to_ids(
        args.cycle_title,
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

    out_prefix = args.out_prefix or f"basin_from_cycle_n={int(args.n)}"
    out_layers = ANALYSIS_DIR / f"{out_prefix}_layers.tsv"
    out_members = ANALYSIS_DIR / f"{out_prefix}_members.parquet" if args.write_membership else None

    # Run basin mapping
    result = map_basin(
        loader,
        n=int(args.n),
        cycle_page_ids=cycle_ids,
        max_depth=int(args.max_depth),
        max_nodes=int(args.max_nodes),
        log_every=int(args.log_every),
        write_layers_tsv=out_layers,
        write_members_parquet=out_members,
        verbose=True,
    )

    print(f"\nBasin mapping complete:")
    print(f"  Total nodes: {result.total_nodes:,}")
    print(f"  Max depth: {result.max_depth_reached}")
    print(f"  Stopped: {result.stopped_reason}")
    print(f"  Elapsed: {result.elapsed_seconds:.1f}s")


if __name__ == "__main__":
    main()
