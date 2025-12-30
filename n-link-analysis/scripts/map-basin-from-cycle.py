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

    # Keep only defined Nth links (dst_page_id IS NOT NULL).
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

    # An index on dst accelerates reverse expansions.
    try:
        con.execute("CREATE INDEX edges_dst_idx ON edges(dst_page_id)")
    except Exception:
        # Index creation can fail on older DuckDB builds; it will still work without it.
        pass

    dt = time.time() - t0
    n_edges_row = con.execute("SELECT COUNT(*) FROM edges").fetchone()
    n_edges = int(n_edges_row[0]) if n_edges_row is not None else 0
    print(f"Edges table ready: {n_edges:,} edges in {dt:.1f}s")


def _get_successor(con: duckdb.DuckDBPyConnection, page_id: int) -> int | None:
    row = con.execute(
        """
        SELECT dst_page_id
        FROM edges
        WHERE src_page_id = ?
        LIMIT 1
        """.strip(),
        [int(page_id)],
    ).fetchone()
    if row is None:
        return None
    return int(row[0]) if row[0] is not None else None


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

    title_to_id = _resolve_titles_to_ids(
        args.cycle_title,
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
    out_members = ANALYSIS_DIR / f"{out_prefix}_members.parquet"

    db_path = ANALYSIS_DIR / f"edges_n={int(args.n)}.duckdb"
    print(f"Using edges DB: {db_path}")

    con = duckdb.connect(str(db_path))
    _ensure_edges_table(con, n=int(args.n))

    # Quick sanity check: print successors of cycle nodes.
    print("Cycle nodes:")
    for pid in cycle_ids:
        succ = _get_successor(con, pid)
        print(f"  {pid} -> {succ}")

    # Temp tables.
    con.execute("CREATE TEMP TABLE seen(page_id BIGINT)")
    con.execute("CREATE TEMP TABLE frontier(page_id BIGINT)")

    cycle_tbl = pa.table({"page_id": pa.array(cycle_ids, type=pa.int64())})
    con.register("cycle_tbl", cycle_tbl)
    con.execute("INSERT INTO seen SELECT page_id FROM cycle_tbl")
    con.execute("INSERT INTO frontier SELECT page_id FROM cycle_tbl")

    # Track layer sizes.
    layer_lines: list[str] = ["depth\tnew_nodes\ttotal_seen"]
    total_seen_row = con.execute("SELECT COUNT(*) FROM seen").fetchone()
    total_seen = int(total_seen_row[0]) if total_seen_row is not None else 0
    layer_lines.append(f"0\t{len(cycle_ids)}\t{total_seen}")

    max_depth = int(args.max_depth)
    max_nodes = int(args.max_nodes)
    log_every = max(1, int(args.log_every))

    depth = 0
    t0 = time.time()

    while True:
        if max_depth and depth >= max_depth:
            print(f"Reached max_depth={max_depth}")
            break

        if max_nodes and total_seen >= max_nodes:
            print(f"Reached max_nodes={max_nodes}")
            break

        depth += 1

        remaining_clause = ""
        if max_nodes:
            remaining = max(0, max_nodes - total_seen)
            remaining_clause = f"QUALIFY row_number() OVER (ORDER BY page_id) <= {remaining}" if remaining > 0 else "QUALIFY 1=0"

        con.execute("DROP TABLE IF EXISTS new_frontier")
        con.execute(
            f"""
            CREATE TEMP TABLE new_frontier AS
            SELECT DISTINCT e.src_page_id AS page_id
            FROM edges e
            JOIN frontier f
              ON e.dst_page_id = f.page_id
            LEFT JOIN seen s
              ON e.src_page_id = s.page_id
            WHERE s.page_id IS NULL
            {remaining_clause}
            """.strip()
        )

        new_count_row = con.execute("SELECT COUNT(*) FROM new_frontier").fetchone()
        new_count = int(new_count_row[0]) if new_count_row is not None else 0
        if new_count == 0:
            print("Frontier exhausted (no new nodes).")
            break

        con.execute("INSERT INTO seen SELECT page_id FROM new_frontier")
        total_seen_row = con.execute("SELECT COUNT(*) FROM seen").fetchone()
        total_seen = int(total_seen_row[0]) if total_seen_row is not None else 0

        con.execute("DELETE FROM frontier")
        con.execute("INSERT INTO frontier SELECT page_id FROM new_frontier")

        layer_lines.append(f"{depth}\t{new_count}\t{total_seen}")
        dt = time.time() - t0
        rate = total_seen / max(dt, 1e-9)
        if depth % log_every == 0:
            print(f"depth={depth}\tnew={new_count:,}\ttotal={total_seen:,}\t(rate={rate:,.1f} nodes/sec)")

    con.execute("DROP TABLE IF EXISTS frontier")
    con.execute("DROP TABLE IF EXISTS new_frontier")

    out_layers.write_text("\n".join(layer_lines), encoding="utf-8")
    print(f"Saved layer sizes: {out_layers}")

    if args.write_membership:
        print(f"Writing membership set to: {out_members}")
        con.execute(
            f"""
            COPY (SELECT page_id FROM seen) TO '{out_members.as_posix()}' (FORMAT PARQUET)
            """.strip()
        )

    con.close()


if __name__ == "__main__":
    main()
