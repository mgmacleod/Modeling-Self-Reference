#!/usr/bin/env python3
"""Chase the dominant upstream "trunk" under the fixed N-link rule.

Given a seed node X (title or page_id), consider its reverse basin under f_N:
  f_N(page) = Nth outgoing link if it exists, else HALT.

Define entry branches as in branch-basin-analysis.py:
- entry node e is a depth-1 predecessor of X (f_N(e) = X)
- branch(e) is the set of nodes whose last non-X node before reaching X is e
- thickness(e) = |branch(e)|

This script repeatedly:
1) computes entry-branch thicknesses for current seed
2) chooses the dominant entry (largest thickness)
3) steps seed := dominant_entry

Stop conditions:
- no predecessors (0 entry branches)
- repeat seed encountered (cycle in this chase)
- reached max_hops
- (optional) dominance_share < threshold (dominant branch not strong)

Outputs
-------
Writes a TSV report under data/wikipedia/processed/analysis/ with one row per hop.

Notes
-----
This is intentionally compute-heavy (it computes full branch sizes each hop), but
it is reproducible and directly matches the user's "find the trunk" intuition.

"""

from __future__ import annotations

import argparse
import re
import time
from pathlib import Path

import duckdb
import pyarrow as pa


REPO_ROOT = Path(__file__).resolve().parents[2]
PROCESSED_DIR = REPO_ROOT / "data" / "wikipedia" / "processed"
NLINK_PATH = PROCESSED_DIR / "nlink_sequences.parquet"
PAGES_PATH = PROCESSED_DIR / "pages.parquet"
ANALYSIS_DIR = PROCESSED_DIR / "analysis"


def _slug(s: str) -> str:
    s = s.strip()
    s = re.sub(r"\s+", "_", s)
    s = re.sub(r"[^A-Za-z0-9_\-()]+", "", s)
    return s[:120] if len(s) > 120 else s


def _resolve_titles_to_ids(titles: list[str], *, namespace: int, allow_redirects: bool) -> dict[str, int]:
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


def _dominant_entry_for_seed(
    con: duckdb.DuckDBPyConnection,
    *,
    seed_id: int,
    max_depth: int,
    log_every: int,
) -> tuple[int | None, int, int, float]:
    """Return (dominant_entry_id, dominant_entry_size, total_seen, share).

    total_seen includes the seed itself.
    share = dominant_entry_size / (total_seen - 1) when total_seen>1 else 0.
    """

    con.execute("CREATE TEMP TABLE seen(page_id BIGINT PRIMARY KEY, entry_id BIGINT, depth INTEGER)")
    con.execute("CREATE TEMP TABLE frontier(page_id BIGINT, entry_id BIGINT, depth INTEGER)")

    con.execute("INSERT INTO seen VALUES (?, NULL, 0)", [int(seed_id)])
    con.execute("INSERT INTO frontier VALUES (?, NULL, 0)", [int(seed_id)])

    depth = 0
    t0 = time.time()

    while True:
        if max_depth and depth >= max_depth:
            break

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
            break

        con.execute("INSERT INTO seen SELECT page_id, entry_id, depth FROM next_frontier")
        con.execute("DELETE FROM frontier")
        con.execute("INSERT INTO frontier SELECT page_id, entry_id, depth FROM next_frontier")
        depth += 1

        if log_every and depth % log_every == 0:
            total_row = con.execute("SELECT COUNT(*) FROM seen").fetchone()
            total_seen = int(total_row[0]) if total_row is not None else 0
            dt = time.time() - t0
            rate = total_seen / max(dt, 1e-9)
            print(f"  depth={depth}\tnew={new_nodes:,}\ttotal={total_seen:,}\t(rate={rate:,.1f} nodes/sec)")

    total_row = con.execute("SELECT COUNT(*) FROM seen").fetchone()
    total_seen = int(total_row[0]) if total_row is not None and total_row[0] is not None else 0

    # Entry branches: depth>=1 grouped by entry_id.
    top = con.execute(
        """
        SELECT entry_id, COUNT(*)::BIGINT AS basin_size
        FROM seen
        WHERE depth >= 1
        GROUP BY entry_id
        ORDER BY basin_size DESC
        LIMIT 1
        """.strip()
    ).fetchone()

    dominant_entry_id: int | None
    dominant_size: int

    if top is None or top[0] is None:
        dominant_entry_id = None
        dominant_size = 0
    else:
        dominant_entry_id = int(top[0])
        dominant_size = int(top[1])

    denom = max(0, total_seen - 1)
    share = (dominant_size / denom) if denom > 0 else 0.0

    # Clean up temp tables for next hop.
    con.execute("DROP TABLE IF EXISTS frontier")
    con.execute("DROP TABLE IF EXISTS seen")
    con.execute("DROP TABLE IF EXISTS next_frontier")

    return dominant_entry_id, dominant_size, total_seen, float(share)


def main() -> None:
    parser = argparse.ArgumentParser(description="Chase the dominant upstream entry branch repeatedly under f_N.")
    parser.add_argument("--n", type=int, default=5, help="N for fixed N-link rule (default: 5)")
    parser.add_argument("--seed-title", type=str, required=True, help="Start title (exact match)")
    parser.add_argument("--namespace", type=int, default=0, help="Namespace for resolving titles (default: 0)")
    parser.add_argument("--allow-redirects", action="store_true", help="Allow resolving seed title to redirects")
    parser.add_argument("--max-hops", type=int, default=25, help="Maximum hops upstream (default: 25)")
    parser.add_argument("--max-depth", type=int, default=0, help="Max reverse depth per hop (default: 0 = no limit)")
    parser.add_argument("--log-every", type=int, default=0, help="Log every N depths within each hop (default: 0 = quiet)")
    parser.add_argument(
        "--dominance-threshold",
        type=float,
        default=0.0,
        help="Stop if dominant share falls below this (default: 0 = disabled)",
    )
    parser.add_argument("--out", type=str, default=None, help="Optional output TSV path")

    args = parser.parse_args()
    if args.n <= 0:
        raise SystemExit("--n must be >= 1")
    if args.max_hops <= 0:
        raise SystemExit("--max-hops must be >= 1")

    seed_map = _resolve_titles_to_ids(
        [str(args.seed_title)],
        namespace=int(args.namespace),
        allow_redirects=bool(args.allow_redirects),
    )
    if args.seed_title not in seed_map:
        raise SystemExit(f"Could not resolve seed title to page_id (exact match failed): {args.seed_title}")

    seed_id = int(seed_map[args.seed_title])

    ANALYSIS_DIR.mkdir(parents=True, exist_ok=True)
    out_path = Path(args.out) if args.out else (
        ANALYSIS_DIR / f"dominant_upstream_chain_n={int(args.n)}_from={_slug(args.seed_title)}.tsv"
    )

    db_path = ANALYSIS_DIR / f"edges_n={int(args.n)}.duckdb"
    print(f"Using edges DB: {db_path}")
    con = duckdb.connect(str(db_path))
    _ensure_edges_table(con, n=int(args.n))

    visited: dict[int, int] = {}
    rows: list[dict[str, object]] = []

    current_id = seed_id
    current_title = str(args.seed_title)

    for hop in range(int(args.max_hops)):
        if current_id in visited:
            first = visited[current_id]
            print(f"Stop: repeated seed encountered at hop={hop} (previous hop={first})")
            break
        visited[current_id] = hop

        print(f"\n=== Hop {hop} seed={current_title} ({current_id}) ===")
        dom_id, dom_size, total_seen, share = _dominant_entry_for_seed(
            con,
            seed_id=current_id,
            max_depth=int(args.max_depth),
            log_every=int(args.log_every),
        )

        # Resolve titles for the dominant entry, if any.
        titles = _resolve_ids_to_titles([current_id, dom_id] if dom_id is not None else [current_id])
        dom_title = titles.get(dom_id, "<unknown>") if dom_id is not None else "<none>"

        print(f"Total basin nodes (including seed): {total_seen:,}")
        print(f"Dominant entry: {dom_title} ({dom_id}) size={dom_size:,} share={share:.2%}")

        rows.append(
            {
                "hop": hop,
                "seed_page_id": int(current_id),
                "seed_title": titles.get(current_id, current_title),
                "basin_total_including_seed": int(total_seen),
                "dominant_entry_page_id": int(dom_id) if dom_id is not None else "",
                "dominant_entry_title": dom_title if dom_id is not None else "",
                "dominant_entry_size": int(dom_size),
                "dominant_share_of_upstream": float(share),
            }
        )

        if dom_id is None:
            print("Stop: no predecessors (no entry branches).")
            break

        if args.dominance_threshold and share < float(args.dominance_threshold):
            print(f"Stop: dominance_share {share:.2%} < threshold {args.dominance_threshold:.2%}")
            break

        current_id = int(dom_id)
        current_title = dom_title

    # Write TSV.
    header = [
        "hop",
        "seed_page_id",
        "seed_title",
        "basin_total_including_seed",
        "dominant_entry_page_id",
        "dominant_entry_title",
        "dominant_entry_size",
        "dominant_share_of_upstream",
    ]
    lines = ["\t".join(header)]
    for r in rows:
        lines.append("\t".join(str(r[h]) for h in header))
    out_path.write_text("\n".join(lines), encoding="utf-8")
    print(f"\nWrote chain TSV: {out_path}")

    con.close()


if __name__ == "__main__":
    main()
