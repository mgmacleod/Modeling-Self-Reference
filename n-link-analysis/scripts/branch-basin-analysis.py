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
import time
from pathlib import Path

import duckdb
import pyarrow as pa


REPO_ROOT = Path(__file__).resolve().parents[2]
PROCESSED_DIR = REPO_ROOT / "data" / "wikipedia" / "processed"
NLINK_PATH = PROCESSED_DIR / "nlink_sequences.parquet"
PAGES_PATH = PROCESSED_DIR / "pages.parquet"
ANALYSIS_DIR = PROCESSED_DIR / "analysis"


def _resolve_titles_to_ids(
    titles: list[str],
    *,
    namespace: int,
    allow_redirects: bool,
) -> dict[str, int]:
    if not titles:
        return {}
    if not PAGES_PATH.exists():
        raise FileNotFoundError(f"Missing: {PAGES_PATH}")

    title_tbl = pa.table({"title": pa.array(titles, type=pa.string())})

    con = duckdb.connect()
    con.register("wanted_titles", title_tbl)

    redirect_clause = "" if allow_redirects else "AND p.is_redirect = FALSE"
    rows = con.execute(
        f"""
        SELECT w.title, min(p.page_id) AS page_id
        FROM wanted_titles w
        JOIN read_parquet('{PAGES_PATH.as_posix()}') p
          ON p.title = w.title
        WHERE p.namespace = {int(namespace)}
          {redirect_clause}
        GROUP BY w.title
        """.strip()
    ).fetchall()
    con.close()

    return {str(t): int(pid) for t, pid in rows}


def _resolve_ids_to_titles(page_ids: list[int]) -> dict[int, str]:
    if not page_ids:
        return {}
    if not PAGES_PATH.exists():
        return {}

    unique_ids = sorted(set(int(x) for x in page_ids))
    id_tbl = pa.table({"page_id": pa.array(unique_ids, type=pa.int64())})

    con = duckdb.connect()
    con.register("wanted_ids", id_tbl)

    rows = con.execute(
        f"""
        SELECT p.page_id, p.title
        FROM read_parquet('{PAGES_PATH.as_posix()}') p
        JOIN wanted_ids w USING (page_id)
        """.strip()
    ).fetchall()
    con.close()

    return {int(pid): str(title) for pid, title in rows}


def _ensure_edges_table(con: duckdb.DuckDBPyConnection, *, n: int) -> None:
    exists_row = con.execute(
        """
        SELECT COUNT(*)
        FROM information_schema.tables
        WHERE table_schema = 'main' AND table_name = 'edges'
        """.strip()
    ).fetchone()
    exists = int(exists_row[0]) if exists_row is not None else 0

    if exists:
        return

    if not NLINK_PATH.exists():
        raise FileNotFoundError(f"Missing: {NLINK_PATH}")

    print(f"Materializing edges table for N={n} (one-time cost)...")
    t0 = time.time()

    con.execute(
        f"""
        CREATE TABLE edges AS
        SELECT
            page_id::BIGINT AS src_page_id,
            list_extract(link_sequence, {int(n)})::BIGINT AS dst_page_id
        FROM read_parquet('{NLINK_PATH.as_posix()}')
        WHERE list_extract(link_sequence, {int(n)}) IS NOT NULL
        """.strip()
    )

    try:
        con.execute("CREATE INDEX edges_dst_idx ON edges(dst_page_id)")
    except Exception:
        pass

    dt = time.time() - t0
    n_edges_row = con.execute("SELECT COUNT(*) FROM edges").fetchone()
    n_edges = int(n_edges_row[0]) if n_edges_row is not None else 0
    print(f"Edges table ready: {n_edges:,} edges in {dt:.1f}s")


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

    title_to_id = _resolve_titles_to_ids(
        list(args.cycle_title),
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

    out_prefix = args.out_prefix or f"branches_from_cycle_n={int(args.n)}"
    out_branches_all = ANALYSIS_DIR / f"{out_prefix}_branches_all.tsv"
    out_branches_topk = ANALYSIS_DIR / f"{out_prefix}_branches_topk.tsv"
    out_assignments = ANALYSIS_DIR / f"{out_prefix}_assignments.parquet"

    db_path = ANALYSIS_DIR / f"edges_n={int(args.n)}.duckdb"
    print(f"Using edges DB: {db_path}")

    con = duckdb.connect(str(db_path))
    _ensure_edges_table(con, n=int(args.n))

    # Seed tables.
    con.execute("CREATE TEMP TABLE seen(page_id BIGINT PRIMARY KEY, entry_id BIGINT, depth INTEGER)")
    con.execute("CREATE TEMP TABLE frontier(page_id BIGINT, entry_id BIGINT, depth INTEGER)")

    cycle_tbl = pa.table({"page_id": pa.array(cycle_ids, type=pa.int64())})
    con.register("cycle_tbl", cycle_tbl)

    # depth 0 cycle nodes: entry_id = NULL
    con.execute("INSERT INTO seen SELECT page_id, NULL::BIGINT AS entry_id, 0 AS depth FROM cycle_tbl")
    con.execute("INSERT INTO frontier SELECT page_id, NULL::BIGINT AS entry_id, 0 AS depth FROM cycle_tbl")

    max_depth = int(args.max_depth)
    log_every = max(1, int(args.log_every))

    depth = 0
    t0 = time.time()

    while True:
        if max_depth and depth >= max_depth:
            print(f"Reached max_depth={max_depth}")
            break

        # Expand one reverse layer.
        con.execute("DROP TABLE IF EXISTS next_frontier")
        con.execute(
            """
            CREATE TEMP TABLE next_frontier AS
            SELECT
                e.src_page_id AS page_id,
                CASE
                    WHEN f.depth = 0 THEN e.src_page_id
                    ELSE f.entry_id
                END AS entry_id,
                f.depth + 1 AS depth
            FROM edges e
            JOIN frontier f
              ON e.dst_page_id = f.page_id
            LEFT JOIN seen s
              ON s.page_id = e.src_page_id
            WHERE s.page_id IS NULL
            """.strip()
        )

        new_row = con.execute("SELECT COUNT(*) FROM next_frontier").fetchone()
        new_nodes = int(new_row[0]) if new_row is not None else 0

        if new_nodes == 0:
            print("Frontier exhausted (no new nodes).")
            break

        con.execute("INSERT INTO seen SELECT page_id, entry_id, depth FROM next_frontier")
        con.execute("DELETE FROM frontier")
        con.execute("INSERT INTO frontier SELECT page_id, entry_id, depth FROM next_frontier")

        depth += 1

        if depth % log_every == 0:
            total_row = con.execute("SELECT COUNT(*) FROM seen").fetchone()
            total_seen = int(total_row[0]) if total_row is not None else 0
            dt = time.time() - t0
            rate = total_seen / max(dt, 1e-9)
            print(f"depth={depth}\tnew={new_nodes:,}\ttotal={total_seen:,}\t(rate={rate:,.1f} nodes/sec)")

    total_row = con.execute("SELECT COUNT(*) FROM seen").fetchone()
    total_seen = int(total_row[0]) if total_row is not None else 0
    print(f"Total basin nodes (including cycle): {total_seen:,}")

    # Branch sizes (exclude cycle nodes: depth>=1, entry_id not null)
    con.execute("DROP TABLE IF EXISTS branch_sizes")
    con.execute(
        """
        CREATE TEMP TABLE branch_sizes AS
        SELECT
            entry_id,
            COUNT(*)::BIGINT AS basin_size,
            MAX(depth)::INTEGER AS max_depth
        FROM seen
        WHERE depth >= 1
        GROUP BY entry_id
        """.strip()
    )

    n_branches_row = con.execute("SELECT COUNT(*) FROM branch_sizes").fetchone()
    n_branches = int(n_branches_row[0]) if n_branches_row is not None else 0
    print(f"Entry branches (depth-1 predecessors): {n_branches:,}")

    # Identify which cycle node each entry flows into (successor of the entry).
    con.execute("DROP TABLE IF EXISTS branch_meta")
    con.execute(
        """
        CREATE TEMP TABLE branch_meta AS
        SELECT
            b.entry_id,
            b.basin_size,
            b.max_depth,
            e.dst_page_id AS enters_cycle_page_id
        FROM branch_sizes b
        JOIN edges e
          ON e.src_page_id = b.entry_id
        """.strip()
    )

    # Write full (all branches) TSV for downstream analysis.
    all_rows = con.execute(
        """
        SELECT entry_id, basin_size, max_depth, enters_cycle_page_id
        FROM branch_meta
        ORDER BY basin_size DESC
        """.strip()
    ).fetchall()

    out_lines_all = ["rank\tentry_id\tbasin_size\tmax_depth\tenters_cycle_page_id"]
    for i, (entry_id, basin_size, max_d, enters_cycle) in enumerate(all_rows, start=1):
        enters_i = int(enters_cycle) if enters_cycle is not None else -1
        out_lines_all.append(
            "\t".join(
                [
                    str(i),
                    str(int(entry_id)),
                    str(int(basin_size)),
                    str(int(max_d)),
                    str(enters_i),
                ]
            )
        )
    out_branches_all.write_text("\n".join(out_lines_all), encoding="utf-8")
    print(f"Wrote all-branches table: {out_branches_all}")

    # Also write a human-friendly titled top-K table.
    top_k = max(1, int(args.top_k))
    top_rows = all_rows[:top_k]

    ids_to_resolve: list[int] = []
    ids_to_resolve.extend(int(x) for x in cycle_ids)
    ids_to_resolve.extend(int(r[0]) for r in top_rows)
    ids_to_resolve.extend(int(r[3]) for r in top_rows if r[3] is not None)
    titles = _resolve_ids_to_titles(ids_to_resolve)

    out_lines_topk = [
        "rank\tentry_id\tentry_title\tbasin_size\tmax_depth\tenters_cycle_page_id\tenters_cycle_title",
    ]
    for i, (entry_id, basin_size, max_d, enters_cycle) in enumerate(top_rows, start=1):
        entry_id_i = int(entry_id)
        enters_i = int(enters_cycle) if enters_cycle is not None else -1
        out_lines_topk.append(
            "\t".join(
                [
                    str(i),
                    str(entry_id_i),
                    titles.get(entry_id_i, "<unknown>"),
                    str(int(basin_size)),
                    str(int(max_d)),
                    str(enters_i),
                    titles.get(enters_i, "<unknown>") if enters_i != -1 else "<unknown>",
                ]
            )
        )

    out_branches_topk.write_text("\n".join(out_lines_topk), encoding="utf-8")
    print(f"Wrote top-{top_k} titled branch table: {out_branches_topk}")

    # Optionally write membership for top-K branches.
    write_k = int(args.write_membership_top_k)
    if write_k > 0:
        k = min(write_k, len(top_rows))
        top_entry_ids = [int(r[0]) for r in top_rows[:k]]
        con.register(
            "top_entries",
            pa.table({"entry_id": pa.array(top_entry_ids, type=pa.int64())}),
        )

        # Write (page_id, entry_id, depth) for nodes assigned to top entries.
        con.execute(
            f"""
            COPY (
                SELECT page_id, entry_id, depth
                FROM seen
                WHERE entry_id IN (SELECT entry_id FROM top_entries)
            ) TO '{out_assignments.as_posix()}' (FORMAT PARQUET)
            """.strip()
        )
        print(f"Wrote membership assignments for top-{k} branches: {out_assignments}")

    con.close()


if __name__ == "__main__":
    main()
