#!/usr/bin/env python3
"""Render a 3D interactive visualization of a basin *summary* as a tributary tree.

Motivation
----------
Fully mapping the Massachusetts↔Gulf_of_Maine basin (~1M nodes) into an interactive
3D graph is impractical. Instead, we build a "major tributaries" tree:

- Start from a terminal cycle (one or more titles).
- Compute the top-k depth-1 entry branches into that terminal (branch sizes).
- For each selected entry node, repeat: compute its top-k entry branches.
- Continue for `max_levels`.

This produces a visually rich, circulatory/river-network-like skeleton of how
mass aggregates, without attempting to draw all nodes.

Outputs
-------
- HTML: n-link-analysis/report/assets/tributary_tree_3d_*.html

Notes
-----
- `max_depth` caps the reverse expansion depth used to estimate branch sizes.
  Set to 0 for exhaustive (can be very expensive for large basins).
"""

from __future__ import annotations

import argparse
import json
import math
import re
import time
from dataclasses import dataclass
from pathlib import Path

import duckdb
import networkx as nx
import plotly.graph_objects as go
import pyarrow as pa


REPO_ROOT = Path(__file__).resolve().parents[2]
PROCESSED_DIR = REPO_ROOT / "data" / "wikipedia" / "processed"
NLINK_PATH = PROCESSED_DIR / "nlink_sequences.parquet"
PAGES_PATH = PROCESSED_DIR / "pages.parquet"
ANALYSIS_DIR = PROCESSED_DIR / "analysis"
REPORT_ASSETS_DIR = REPO_ROOT / "n-link-analysis" / "report" / "assets"


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
    row = con.execute(
        """
        SELECT COUNT(*)
        FROM information_schema.tables
        WHERE table_schema = 'main' AND table_name = 'edges'
        """.strip()
    ).fetchone()
    exists = int(row[0]) if row is not None and row[0] is not None else 0
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
    row = con.execute("SELECT COUNT(*) FROM edges").fetchone()
    n_edges = int(row[0]) if row is not None and row[0] is not None else 0
    print(f"Edges table ready: {n_edges:,} edges in {dt:.1f}s")


@dataclass(frozen=True)
class BranchRow:
    entry_id: int
    entry_size: int
    enters_target_id: int


def _top_k_entries_for_targets(
    con: duckdb.DuckDBPyConnection,
    *,
    target_ids: list[int],
    max_depth: int,
    top_k: int,
) -> tuple[int, list[BranchRow]]:
    """Compute top-k entry branches into a *set* of target nodes.

    We treat the provided target set as the terminal; depth-1 predecessors are
    entries, and we propagate `entry_id` from those depth-1 nodes.

    Returns:
      (total_seen_including_targets, top_k_rows)
    """

    if not target_ids:
        return 0, []

    con.execute("CREATE TEMP TABLE seen(page_id BIGINT PRIMARY KEY, entry_id BIGINT, depth INTEGER, enters_target_id BIGINT)")
    con.execute("CREATE TEMP TABLE frontier(page_id BIGINT, entry_id BIGINT, depth INTEGER, enters_target_id BIGINT)")

    for tid in target_ids:
        con.execute("INSERT INTO seen VALUES (?, NULL, 0, ?)", [int(tid), int(tid)])
        con.execute("INSERT INTO frontier VALUES (?, NULL, 0, ?)", [int(tid), int(tid)])

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
                f.depth + 1 AS depth,
                f.enters_target_id AS enters_target_id
            FROM edges e
            JOIN frontier f
              ON e.dst_page_id = f.page_id
            LEFT JOIN seen s
              ON s.page_id = e.src_page_id
            WHERE s.page_id IS NULL
            """.strip()
        )

        row = con.execute("SELECT COUNT(*) FROM next_frontier").fetchone()
        new_nodes = int(row[0]) if row is not None and row[0] is not None else 0
        if new_nodes == 0:
            break

        con.execute("INSERT INTO seen SELECT page_id, entry_id, depth, enters_target_id FROM next_frontier")
        con.execute("DELETE FROM frontier")
        con.execute("INSERT INTO frontier SELECT page_id, entry_id, depth, enters_target_id FROM next_frontier")
        depth += 1

    row = con.execute("SELECT COUNT(*) FROM seen").fetchone()
    total_seen = int(row[0]) if row is not None and row[0] is not None else 0

    rows = con.execute(
        f"""
        SELECT entry_id, COUNT(*)::BIGINT AS entry_size, min(enters_target_id) AS enters_target_id
        FROM seen
        WHERE depth >= 1
        GROUP BY entry_id
        ORDER BY entry_size DESC
        LIMIT {int(top_k)}
        """.strip()
    ).fetchall()

    out: list[BranchRow] = []
    for entry_id, entry_size, enters_target_id in rows:
        if entry_id is None:
            continue
        out.append(BranchRow(entry_id=int(entry_id), entry_size=int(entry_size), enters_target_id=int(enters_target_id)))

    con.execute("DROP TABLE IF EXISTS frontier")
    con.execute("DROP TABLE IF EXISTS seen")
    con.execute("DROP TABLE IF EXISTS next_frontier")

    return total_seen, out


def _build_tributary_tree(
    con: duckdb.DuckDBPyConnection,
    *,
    root_cycle_titles: list[str],
    n: int,
    namespace: int,
    allow_redirects: bool,
    max_levels: int,
    top_k: int,
    max_depth: int,
) -> tuple[nx.DiGraph, dict[int, str]]:
    """Build a directed tributary tree graph (entry -> target)."""

    title_to_id = _resolve_titles_to_ids(root_cycle_titles, namespace=namespace, allow_redirects=allow_redirects)
    missing = [t for t in root_cycle_titles if t not in title_to_id]
    if missing:
        raise SystemExit(f"Could not resolve cycle titles (exact match failed): {missing}")

    root_ids = [int(title_to_id[t]) for t in root_cycle_titles]

    # BFS by levels over selected entries.
    G = nx.DiGraph()

    # Keep a title cache for nodes we touch.
    title_cache: dict[int, str] = {}

    # Add cycle nodes.
    for tid in root_ids:
        G.add_node(tid, kind="cycle", level=0)

    frontier: list[tuple[list[int], int]] = [(root_ids, 0)]  # (target_ids, level)
    visited_targets: set[tuple[int, ...]] = {tuple(sorted(root_ids))}

    for level in range(max_levels):
        next_frontier: list[tuple[list[int], int]] = []

        for target_ids, target_level in frontier:
            if target_level != level:
                continue

            total_seen, top_entries = _top_k_entries_for_targets(
                con,
                target_ids=target_ids,
                max_depth=max_depth,
                top_k=top_k,
            )

            # Annotate target nodes with basin size (within cap).
            for tid in target_ids:
                if tid in G.nodes:
                    G.nodes[tid][f"basin_total_level{level}"] = int(total_seen)

            # Resolve titles for entries + targets for hover.
            ids_to_resolve = [*target_ids, *[r.entry_id for r in top_entries], *[r.enters_target_id for r in top_entries]]
            title_cache.update(_resolve_ids_to_titles([int(x) for x in ids_to_resolve]))

            denom = max(1, total_seen - len(target_ids))
            for r in top_entries:
                G.add_node(r.entry_id, kind="entry", level=level + 1)

                for tid in target_ids:
                    # Only connect to the specific target this entry routes into.
                    if tid == r.enters_target_id:
                        G.add_edge(
                            r.entry_id,
                            tid,
                            weight=int(r.entry_size),
                            share=float(r.entry_size / denom),
                        )

                # Next step: treat this entry as the new single target.
                key = (r.entry_id,)
                if key not in visited_targets:
                    visited_targets.add(key)
                    next_frontier.append(([r.entry_id], level + 1))

        frontier = next_frontier
        if not frontier:
            break

    # Ensure titles exist for all nodes.
    title_cache.update(_resolve_ids_to_titles([int(nid) for nid in G.nodes]))
    return G, title_cache


def _graph_to_plotly_3d(G: nx.DiGraph, titles: dict[int, str]) -> go.Figure:
    # 3D force layout (deterministic).
    pos = nx.spring_layout(G, dim=3, seed=0)

    # Edge traces as a single set of segments.
    # Plotly uses `None` separators between segments, so these lists must allow None.
    edge_x: list[float | None] = []
    edge_y: list[float | None] = []
    edge_z: list[float | None] = []
    edge_w: list[float] = []

    for u, v, data in G.edges(data=True):
        x0, y0, z0 = pos[u]
        x1, y1, z1 = pos[v]
        edge_x.extend([x0, x1, None])
        edge_y.extend([y0, y1, None])
        edge_z.extend([z0, z1, None])
        edge_w.append(float(data.get("weight", 1.0)))

    # Node trace.
    node_x: list[float] = []
    node_y: list[float] = []
    node_z: list[float] = []
    node_text: list[str] = []
    node_size: list[float] = []

    for nid, data in G.nodes(data=True):
        x, y, z = pos[nid]
        node_x.append(x)
        node_y.append(y)
        node_z.append(z)

        title = titles.get(int(nid), str(nid))
        kind = data.get("kind", "node")
        level = data.get("level", "")
        # Prefer the deepest recorded basin_total_* metric.
        basin_keys = [k for k in data.keys() if str(k).startswith("basin_total_level")]
        basin_val = None
        if basin_keys:
            basin_val = data[sorted(basin_keys)[-1]]

        node_text.append(
            f"{title} ({nid})<br>kind={kind} level={level}" + (f"<br>basin≈{basin_val:,}" if basin_val else "")
        )

        # Size by (log) basin estimate when present; else small.
        if basin_val and isinstance(basin_val, int) and basin_val > 0:
            node_size.append(6.0 + 4.0 * math.log10(basin_val))
        else:
            node_size.append(6.0)

    edge_trace = go.Scatter3d(
        x=edge_x,
        y=edge_y,
        z=edge_z,
        mode="lines",
        line=dict(color="rgba(120,120,120,0.55)", width=2),
        hoverinfo="none",
        name="edges",
    )

    node_trace = go.Scatter3d(
        x=node_x,
        y=node_y,
        z=node_z,
        mode="markers",
        marker=dict(size=node_size, color="rgba(0,90,160,0.85)"),
        text=node_text,
        hoverinfo="text",
        name="nodes",
    )

    fig = go.Figure(data=[edge_trace, node_trace])
    fig.update_layout(
        title="N=5 Tributary Tree (Top-k branches per level)",
        showlegend=False,
        margin=dict(l=0, r=0, t=40, b=0),
        scene=dict(
            xaxis=dict(visible=False),
            yaxis=dict(visible=False),
            zaxis=dict(visible=False),
        ),
    )
    return fig


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--n", type=int, default=5)
    parser.add_argument(
        "--cycle-title",
        action="append",
        required=True,
        help="Terminal cycle title (repeatable for 2-cycles).",
    )
    parser.add_argument("--namespace", type=int, default=0)
    parser.add_argument("--allow-redirects", action="store_true")
    parser.add_argument("--top-k", type=int, default=5)
    parser.add_argument("--max-levels", type=int, default=5)
    parser.add_argument(
        "--max-depth",
        type=int,
        default=12,
        help="Reverse expansion depth cap per level (0 = exhaustive; expensive).",
    )
    parser.add_argument(
        "--out",
        type=str,
        default=None,
        help="Optional output HTML path (default: n-link-analysis/report/assets/...).",
    )
    args = parser.parse_args()

    if args.n <= 0:
        raise SystemExit("--n must be >= 1")

    REPORT_ASSETS_DIR.mkdir(parents=True, exist_ok=True)

    out_path = Path(args.out) if args.out else (
        REPORT_ASSETS_DIR
        / (
            f"tributary_tree_3d_n={int(args.n)}_cycle={'__'.join(_slug(t) for t in args.cycle_title)}"
            f"_k={int(args.top_k)}_levels={int(args.max_levels)}_depth={int(args.max_depth)}.html"
        )
    )

    db_path = ANALYSIS_DIR / f"edges_n={int(args.n)}.duckdb"
    print(f"Using edges DB: {db_path}")
    con = duckdb.connect(str(db_path))
    _ensure_edges_table(con, n=int(args.n))

    print("Building tributary tree...")
    G, titles = _build_tributary_tree(
        con,
        root_cycle_titles=[str(t) for t in args.cycle_title],
        n=int(args.n),
        namespace=int(args.namespace),
        allow_redirects=bool(args.allow_redirects),
        max_levels=int(args.max_levels),
        top_k=int(args.top_k),
        max_depth=int(args.max_depth),
    )

    print(f"Graph: {G.number_of_nodes():,} nodes, {G.number_of_edges():,} edges")

    fig = _graph_to_plotly_3d(G, titles)
    fig.write_html(str(out_path), include_plotlyjs=True)
    print(f"Wrote HTML: {out_path}")

    # Also write a small JSON sidecar for debugging / reuse.
    sidecar = out_path.with_suffix(".json")
    data = {
        "nodes": [
            {
                "page_id": int(nid),
                "title": titles.get(int(nid), ""),
                **{k: (int(v) if isinstance(v, (int,)) else v) for k, v in G.nodes[nid].items()},
            }
            for nid in G.nodes
        ],
        "edges": [
            {
                "src": int(u),
                "dst": int(v),
                "weight": int(d.get("weight", 0)),
                "share": float(d.get("share", 0.0)),
            }
            for u, v, d in G.edges(data=True)
        ],
    }
    sidecar.write_text(json.dumps(data, indent=2), encoding="utf-8")
    print(f"Wrote JSON: {sidecar}")

    con.close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
