#!/usr/bin/env python3
"""Batch-run dominant-upstream chase and summarize "collapse" points.

For each seed title, run chase-dominant-upstream-style hops until:
- no predecessors, OR
- max_hops reached, OR
- dominance_share < threshold (if threshold>0).

Then record:
- first hop where share < threshold (if any)
- min share observed
- hops executed

This is intended for comparing many basins quickly (stop at collapse).
"""

from __future__ import annotations

import argparse
import math
import re
from pathlib import Path

import duckdb
import pandas as pd
import pyarrow as pa


REPO_ROOT = Path(__file__).resolve().parents[2]
PROCESSED_DIR = REPO_ROOT / "data" / "wikipedia" / "processed"
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


def _dominant_entry_for_seed(
    con: duckdb.DuckDBPyConnection,
    *,
    seed_id: int,
    max_depth: int,
) -> tuple[int | None, int, int, float]:
    """Return (dominant_entry_id, dominant_entry_size, total_seen, share)."""

    con.execute("CREATE TEMP TABLE seen(page_id BIGINT PRIMARY KEY, entry_id BIGINT, depth INTEGER)")
    con.execute("CREATE TEMP TABLE frontier(page_id BIGINT, entry_id BIGINT, depth INTEGER)")

    con.execute("INSERT INTO seen VALUES (?, NULL, 0)", [int(seed_id)])
    con.execute("INSERT INTO frontier VALUES (?, NULL, 0)", [int(seed_id)])

    depth = 0
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

        count_row = con.execute("SELECT COUNT(*) FROM next_frontier").fetchone()
        new_nodes = int(count_row[0]) if count_row is not None and count_row[0] is not None else 0
        if new_nodes == 0:
            break

        con.execute("INSERT INTO seen SELECT page_id, entry_id, depth FROM next_frontier")
        con.execute("DELETE FROM frontier")
        con.execute("INSERT INTO frontier SELECT page_id, entry_id, depth FROM next_frontier")
        depth += 1

    total_row = con.execute("SELECT COUNT(*) FROM seen").fetchone()
    total_seen = int(total_row[0]) if total_row is not None and total_row[0] is not None else 0

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

    if top is None or top[0] is None:
        dominant_entry_id = None
        dominant_size = 0
    else:
        dominant_entry_id = int(top[0])
        dominant_size = int(top[1])

    denom = max(0, total_seen - 1)
    share = (dominant_size / denom) if denom > 0 else 0.0

    con.execute("DROP TABLE IF EXISTS frontier")
    con.execute("DROP TABLE IF EXISTS seen")
    con.execute("DROP TABLE IF EXISTS next_frontier")

    return dominant_entry_id, dominant_size, total_seen, float(share)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--n", type=int, default=5)
    parser.add_argument("--dashboard", type=str, required=True, help="Input trunkiness dashboard TSV")
    parser.add_argument(
        "--seed-from",
        choices=["dominant_enters_cycle_title", "cycle_first", "cycle_second"],
        default="dominant_enters_cycle_title",
        help="Which title to use as the chase seed for each row.",
    )
    parser.add_argument("--namespace", type=int, default=0)
    parser.add_argument("--allow-redirects", action="store_true")
    parser.add_argument("--max-hops", type=int, default=40)
    parser.add_argument("--max-depth", type=int, default=0)
    parser.add_argument(
        "--dominance-threshold",
        type=float,
        default=0.5,
        help="Stop once share < threshold. Use 0 to disable.",
    )
    parser.add_argument("--tag", type=str, default="bootstrap_2025-12-30")
    args = parser.parse_args()

    if args.n <= 0:
        raise SystemExit("--n must be >= 1")
    if args.max_hops <= 0:
        raise SystemExit("--max-hops must be >= 1")

    dashboard = pd.read_csv(args.dashboard, sep="\t")

    seeds: list[str] = []
    for _, r in dashboard.iterrows():
        if args.seed_from == "dominant_enters_cycle_title":
            seeds.append(str(r["dominant_enters_cycle_title"]))
        else:
            parts = str(r["cycle_key"]).split("__")
            if args.seed_from == "cycle_first":
                seeds.append(parts[0])
            else:
                seeds.append(parts[1] if len(parts) > 1 else parts[0])

    # Resolve all seed titles first.
    seed_map = _resolve_titles_to_ids(
        seeds,
        namespace=int(args.namespace),
        allow_redirects=bool(args.allow_redirects),
    )

    db_path = ANALYSIS_DIR / f"edges_n={int(args.n)}.duckdb"
    con = duckdb.connect(str(db_path))

    rows: list[dict[str, object]] = []

    for seed_title in seeds:
        if seed_title not in seed_map:
            rows.append(
                {
                    "seed_title": seed_title,
                    "resolved": False,
                    "error": "resolve_failed",
                }
            )
            continue

        current_id = int(seed_map[seed_title])
        current_title = seed_title
        min_share = 1.0
        first_below_hop = None
        stop_reason = None
        hops_executed = 0

        for hop in range(int(args.max_hops)):
            dom_id, dom_size, total_seen, share = _dominant_entry_for_seed(
                con, seed_id=current_id, max_depth=int(args.max_depth)
            )
            hops_executed = hop + 1
            min_share = min(min_share, share)

            if args.dominance_threshold and share < float(args.dominance_threshold):
                first_below_hop = hop
                stop_reason = f"share_below_{args.dominance_threshold}"
                break

            if dom_id is None:
                stop_reason = "no_predecessors"
                break

            current_id = int(dom_id)
            titles = _resolve_ids_to_titles([current_id])
            current_title = titles.get(current_id, current_title)

        if stop_reason is None:
            stop_reason = "max_hops"

        rows.append(
            {
                "seed_title": seed_title,
                "resolved": True,
                "hops_executed": hops_executed,
                "min_share": float(min_share) if min_share == min_share else float("nan"),
                "first_below_threshold_hop": first_below_hop if first_below_hop is not None else "",
                "stop_reason": stop_reason,
                "stop_at_title": current_title,
            }
        )

    out_df = pd.DataFrame(rows)
    out_path = ANALYSIS_DIR / f"dominance_collapse_dashboard_n={int(args.n)}_{args.tag}.tsv"
    out_df.to_csv(out_path, sep="\t", index=False)

    print(f"Wrote: {out_path}")
    print(out_df.sort_values(["resolved", "min_share"], ascending=[False, True]).to_string(index=False))

    con.close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
