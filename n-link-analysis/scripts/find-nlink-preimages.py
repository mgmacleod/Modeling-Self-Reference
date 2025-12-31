#!/usr/bin/env python3
"""Find preimages under the fixed N-link rule.

For a fixed N, each page has at most one successor:
  f_N(page) = Nth outgoing link if it exists, else HALT.

This script answers:
  "Which pages map to a given target under f_N?"

I.e. it returns the preimage set:
  f_N^{-1}(target) = { p : f_N(p) = target }

This is the computationally parsimonious way to work *from a cycle*:
- Counting / listing inbound edges is a single scan.
- Building the full basin that feeds a cycle can be done by reverse BFS over
  preimages without enumerating paths.

"""

from __future__ import annotations

import argparse
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


def main() -> None:
    parser = argparse.ArgumentParser(description="Find pages whose Nth link points to a target page (preimages under f_N).")
    parser.add_argument("--n", type=int, default=5, help="N for the fixed N-link rule (default: 5)")
    parser.add_argument(
        "--target-page-id",
        type=int,
        action="append",
        default=[],
        help="Target page_id to find preimages for (repeatable)",
    )
    parser.add_argument(
        "--target-title",
        type=str,
        action="append",
        default=[],
        help="Target title (exact match to pages.parquet title; repeatable)",
    )
    parser.add_argument(
        "--namespace",
        type=int,
        default=0,
        help="Namespace to use when resolving --target-title (default: 0)",
    )
    parser.add_argument(
        "--allow-redirects",
        action="store_true",
        help="Allow resolving --target-title to redirect pages (default: false)",
    )
    parser.add_argument(
        "--resolve-source-titles",
        action="store_true",
        help="Also resolve titles for source pages in the output (slower)",
    )
    parser.add_argument(
        "--out",
        type=str,
        default=None,
        help="Optional output TSV. Default: data/wikipedia/processed/analysis/preimages_n=...tsv",
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=0,
        help="Optional limit on number of source rows returned per target (0 = no limit)",
    )

    args = parser.parse_args()

    if args.n <= 0:
        raise SystemExit("--n must be >= 1")
    if not NLINK_PATH.exists():
        raise FileNotFoundError(f"Missing: {NLINK_PATH}")

    title_to_id = _resolve_titles_to_ids(
        args.target_title,
        namespace=int(args.namespace),
        allow_redirects=bool(args.allow_redirects),
    )
    missing_titles = [t for t in args.target_title if t not in title_to_id]
    if missing_titles:
        raise SystemExit(f"Could not resolve titles to page_id (exact match failed): {missing_titles}")

    target_ids = list(dict.fromkeys([*map(int, args.target_page_id), *title_to_id.values()]))
    if not target_ids:
        raise SystemExit("Provide at least one --target-page-id or --target-title")

    targets_tbl = pa.table({"target_id": pa.array(target_ids, type=pa.int64())})

    con = duckdb.connect()
    con.register("targets", targets_tbl)

    # Compute true preimage counts (no LIMIT).
    counts_rows = con.execute(
        f"""
        WITH edges AS (
            SELECT
                page_id::BIGINT AS src_page_id,
                list_extract(link_sequence, {int(args.n)})::BIGINT AS dst_page_id
            FROM read_parquet('{NLINK_PATH.as_posix()}')
        )
        SELECT
            t.target_id AS target_page_id,
            COUNT(*)::BIGINT AS preimage_count
        FROM edges e
        JOIN targets t
          ON e.dst_page_id = t.target_id
        GROUP BY t.target_id
        """.strip()
    ).fetchall()
    counts: dict[int, int] = {tid: 0 for tid in target_ids}
    for tid, cnt in counts_rows:
        counts[int(tid)] = int(cnt)

    # Fetch (optionally limited) source rows for output.
    limit_n = int(args.limit) if args.limit and int(args.limit) > 0 else 0
    rows = con.execute(
        f"""
        WITH edges AS (
            SELECT
                page_id::BIGINT AS src_page_id,
                list_extract(link_sequence, {int(args.n)})::BIGINT AS dst_page_id
            FROM read_parquet('{NLINK_PATH.as_posix()}')
        ), matched AS (
            SELECT
                t.target_id AS target_page_id,
                e.src_page_id AS src_page_id,
                row_number() OVER (PARTITION BY t.target_id ORDER BY e.src_page_id) AS rn
            FROM edges e
            JOIN targets t
              ON e.dst_page_id = t.target_id
        )
        SELECT target_page_id, src_page_id
        FROM matched
        {f"WHERE rn <= {limit_n}" if limit_n else ""}
        ORDER BY target_page_id, src_page_id
        """.strip()
    ).fetchall()

    src_ids = [int(src) for _t, src in rows]

    src_titles: dict[int, str] = {}
    if args.resolve_source_titles and src_ids and PAGES_PATH.exists():
        src_tbl = pa.table({"page_id": pa.array(sorted(set(src_ids)), type=pa.int64())})
        con.register("src_ids", src_tbl)
        title_rows = con.execute(
            f"""
            SELECT p.page_id, p.title
            FROM read_parquet('{PAGES_PATH.as_posix()}') p
            JOIN src_ids s USING (page_id)
            """.strip()
        ).fetchall()
        src_titles = {int(pid): str(title) for pid, title in title_rows}

    con.close()

    # Write output.
    ANALYSIS_DIR.mkdir(parents=True, exist_ok=True)
    out_path = Path(args.out) if args.out else (ANALYSIS_DIR / f"preimages_n={int(args.n)}.tsv")

    header_cols = ["target_page_id", "src_page_id"]
    if args.resolve_source_titles:
        header_cols.append("src_title")

    lines = ["\t".join(header_cols)]
    for t, src in rows:
        if args.resolve_source_titles:
            lines.append(f"{int(t)}\t{int(src)}\t{src_titles.get(int(src), '<unknown>')}")
        else:
            lines.append(f"{int(t)}\t{int(src)}")

    out_path.write_text("\n".join(lines), encoding="utf-8")

    print("=== Preimages under f_N ===")
    print(f"N={int(args.n)}")
    print(f"Targets: {target_ids}")
    if title_to_id:
        print(f"Resolved titles: {title_to_id}")
    print("Counts (in-degree under f_N):")
    for tid in target_ids:
        print(f"  {tid}: {counts.get(tid, 0)}")
    if limit_n:
        print(f"Returned rows per target were limited to {limit_n} (counts above are still full counts).")
    print(f"Saved TSV: {out_path}")


if __name__ == "__main__":
    main()
