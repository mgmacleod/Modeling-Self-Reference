#!/usr/bin/env python3
"""Dash app: interactive tributary-tree basin viewer (3D).

This avoids generating many standalone HTML plots while iterating.

Run (repo root):
  python n-link-analysis/scripts/dash-tributary-viewer.py

Then open the printed localhost URL.

The visualization is a *tributary skeleton*:
- For a terminal cycle (one or more titles), compute top-k depth-1 entry branches.
- Recurse for `max_levels` (tree depth / number of tiers).
- Use a reverse-expansion depth cap (`max_depth`) *inside each tier* when estimating
    branch sizes (0 = exhaustive, can be very expensive).

"""

from __future__ import annotations

import argparse
import math
import re
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, TypeAlias

import dash
from dash import Input, Output, State, dcc, html
import duckdb
import networkx as nx
import plotly.graph_objects as go
import pyarrow as pa


REPO_ROOT = Path(__file__).resolve().parents[2]
PROCESSED_DIR = REPO_ROOT / "data" / "wikipedia" / "processed"
NLINK_PATH = PROCESSED_DIR / "nlink_sequences.parquet"
PAGES_PATH = PROCESSED_DIR / "pages.parquet"
ANALYSIS_DIR = PROCESSED_DIR / "analysis"

NodeId: TypeAlias = int | str


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
    if not target_ids:
        return 0, []

    con.execute(
        "CREATE TEMP TABLE seen(page_id BIGINT PRIMARY KEY, entry_id BIGINT, depth INTEGER, enters_target_id BIGINT)"
    )
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

        new_row = con.execute("SELECT COUNT(*) FROM next_frontier").fetchone()
        new_nodes = int(new_row[0]) if new_row is not None and new_row[0] is not None else 0
        if new_nodes == 0:
            break

        con.execute("INSERT INTO seen SELECT page_id, entry_id, depth, enters_target_id FROM next_frontier")
        con.execute("DELETE FROM frontier")
        con.execute("INSERT INTO frontier SELECT page_id, entry_id, depth, enters_target_id FROM next_frontier")
        depth += 1

    total_row = con.execute("SELECT COUNT(*) FROM seen").fetchone()
    total_seen = int(total_row[0]) if total_row is not None and total_row[0] is not None else 0

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


def build_tributary_tree_figure(
    con: duckdb.DuckDBPyConnection,
    *,
    cycle_titles: list[str],
    namespace: int,
    allow_redirects: bool,
    top_k: int,
    max_levels: int,
    max_depth: int,
) -> tuple[go.Figure, dict[str, object]]:
    title_to_id = _resolve_titles_to_ids(cycle_titles, namespace=namespace, allow_redirects=allow_redirects)
    missing = [t for t in cycle_titles if t not in title_to_id]
    if missing:
        raise ValueError(f"Could not resolve cycle titles (exact match failed): {missing}")

    root_ids = [int(title_to_id[t]) for t in cycle_titles]

    G = nx.DiGraph()
    title_cache: dict[int, str] = {}

    for tid in root_ids:
        G.add_node(tid, kind="cycle", level=0)

    frontier: list[tuple[list[int], int]] = [(root_ids, 0)]
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

            for tid in target_ids:
                if tid in G.nodes:
                    G.nodes[tid][f"basin_total_level{level}"] = int(total_seen)

            ids_to_resolve = [
                *target_ids,
                *[r.entry_id for r in top_entries],
                *[r.enters_target_id for r in top_entries],
            ]
            title_cache.update(_resolve_ids_to_titles([int(x) for x in ids_to_resolve]))

            denom = max(1, total_seen - len(target_ids))
            for r in top_entries:
                G.add_node(r.entry_id, kind="entry", level=level + 1)
                if r.enters_target_id in target_ids:
                    G.add_edge(
                        r.entry_id,
                        r.enters_target_id,
                        weight=int(r.entry_size),
                        share=float(r.entry_size / denom),
                    )

                key = (r.entry_id,)
                if key not in visited_targets:
                    visited_targets.add(key)
                    next_frontier.append(([r.entry_id], level + 1))

        frontier = next_frontier
        if not frontier:
            break

    title_cache.update(_resolve_ids_to_titles([int(nid) for nid in G.nodes]))

    pos = nx.spring_layout(G, dim=3, seed=0)

    edge_x: list[float | None] = []
    edge_y: list[float | None] = []
    edge_z: list[float | None] = []
    edge_width: list[float] = []

    weights = [float(d.get("weight", 1.0)) for _, _, d in G.edges(data=True)]
    w_max = max(weights) if weights else 1.0

    for u, v, data in G.edges(data=True):
        x0, y0, z0 = pos[u]
        x1, y1, z1 = pos[v]
        edge_x.extend([float(x0), float(x1), None])
        edge_y.extend([float(y0), float(y1), None])
        edge_z.extend([float(z0), float(z1), None])
        edge_width.append(float(data.get("weight", 1.0)))

    # Use a fixed width but encode weight in hover; true per-edge widths would require multiple traces.
    edge_trace = go.Scatter3d(
        x=edge_x,
        y=edge_y,
        z=edge_z,
        mode="lines",
        line=dict(color="rgba(120,120,120,0.55)", width=2),
        hoverinfo="none",
        name="edges",
    )

    node_x: list[float] = []
    node_y: list[float] = []
    node_z: list[float] = []
    node_text: list[str] = []
    node_size: list[float] = []
    node_color: list[float] = []

    for nid, data in G.nodes(data=True):
        x, y, z = pos[nid]
        node_x.append(x)
        node_y.append(y)
        node_z.append(z)

        title = title_cache.get(int(nid), str(nid))
        kind = data.get("kind", "node")
        level = int(data.get("level", 0))
        basin_keys = [k for k in data.keys() if str(k).startswith("basin_total_level")]
        basin_val = None
        if basin_keys:
            basin_val = data[sorted(basin_keys)[-1]]

        node_text.append(
            f"{title} ({nid})<br>kind={kind} level={level}" + (f"<br>basin≈{basin_val:,}" if basin_val else "")
        )

        if basin_val and isinstance(basin_val, int) and basin_val > 0:
            node_size.append(6.0 + 4.0 * math.log10(basin_val))
        else:
            node_size.append(6.0)

        node_color.append(float(level))

    node_trace = go.Scatter3d(
        x=node_x,
        y=node_y,
        z=node_z,
        mode="markers",
        marker=dict(size=node_size, color=node_color, colorscale="Viridis", opacity=0.9),
        text=node_text,
        hoverinfo="text",
        name="nodes",
    )

    fig = go.Figure(data=[edge_trace, node_trace])
    fig.update_layout(
        title="N=5 Tributary Tree (Top-k branches per level)",
        showlegend=False,
        margin=dict(l=0, r=0, t=40, b=0),
        scene=dict(xaxis=dict(visible=False), yaxis=dict(visible=False), zaxis=dict(visible=False)),
    )

    meta = {
        "nodes": int(G.number_of_nodes()),
        "edges": int(G.number_of_edges()),
        "max_edge_weight": float(w_max),
        "cycle_titles": cycle_titles,
    }

    return fig, meta


def _pick_directions_orthogonal(k: int) -> list[tuple[int, int, int]]:
    """Up to 4 orthogonal directions in the XY plane, then repeat."""
    base = [(1, 0, 0), (-1, 0, 0), (0, 1, 0), (0, -1, 0)]
    if k <= 0:
        return []
    out: list[tuple[int, int, int]] = []
    for i in range(k):
        out.append(base[i % len(base)])
    return out


def _orthogonal_children_dirs(parent_dir: tuple[int, int, int], k: int) -> list[tuple[int, int, int]]:
    """Choose child directions orthogonal to the parent (axis-aligned)."""
    candidates = [(1, 0, 0), (-1, 0, 0), (0, 1, 0), (0, -1, 0)]
    px, py, _ = parent_dir
    if abs(px) == 1:
        candidates = [(0, 1, 0), (0, -1, 0)]
    elif abs(py) == 1:
        candidates = [(1, 0, 0), (-1, 0, 0)]
    if k <= 0:
        return []
    out: list[tuple[int, int, int]] = []
    for i in range(k):
        out.append(candidates[i % len(candidates)])
    return out


def build_trunk_and_branches_figure(
    con: duckdb.DuckDBPyConnection,
    *,
    cycle_titles: list[str],
    namespace: int,
    allow_redirects: bool,
    trunk_steps: int,
    trunk_reverse_depth: int,
    branch_k: int,
    branch_depth: int,
    branch_reverse_depth: int,
) -> tuple[go.Figure, dict[str, object]]:
    """Orthogonal view: dominant-upstream trunk + top-k side branches per trunk node.

    Notes on parameters
    -------------------
    - `trunk_steps`: how many dominant-upstream hops to take (tree scale axis).
    - `branch_k`: how many non-trunk branches to show per trunk node.
    - `branch_depth`: how many recursive tiers to show on each side branch.
    - `*_reverse_depth`: depth cap for reverse BFS when estimating branch sizes (0=exhaustive).
    """

    title_to_id = _resolve_titles_to_ids(cycle_titles, namespace=namespace, allow_redirects=allow_redirects)
    missing = [t for t in cycle_titles if t not in title_to_id]
    if missing:
        raise ValueError(f"Could not resolve cycle titles (exact match failed): {missing}")

    root_ids = [int(title_to_id[t]) for t in cycle_titles]
    root_key = "cycle:" + "__".join(cycle_titles)

    G = nx.DiGraph()
    G.add_node(root_key, kind="cycle", level=0)
    title_cache: dict[int, str] = {}

    def resolve_titles(ids: Iterable[int]) -> None:
        title_cache.update(_resolve_ids_to_titles([int(x) for x in ids]))

    # Build trunk
    trunk_nodes: list[NodeId] = [root_key]
    trunk_targets: list[list[int]] = [root_ids]
    trunk_stats: dict[NodeId, dict[str, float]] = {}

    for step in range(max(0, int(trunk_steps))):
        target_ids = trunk_targets[-1]
        total_seen, top_entries = _top_k_entries_for_targets(
            con,
            target_ids=target_ids,
            max_depth=int(trunk_reverse_depth),
            top_k=1,
        )

        trunk_stats[trunk_nodes[-1]] = {"basin_total": float(total_seen)}

        if not top_entries:
            break
        dominant = top_entries[0]
        resolve_titles([dominant.entry_id, *target_ids])
        G.add_node(dominant.entry_id, kind="trunk", level=step + 1, mass=float(dominant.entry_size))

        # Link trunk upstream -> downstream
        # If we are anchored on a multi-node cycle, connect to the synthetic root.
        downstream = trunk_nodes[-1]
        G.add_edge(dominant.entry_id, downstream, weight=float(dominant.entry_size), role="trunk")

        trunk_nodes.append(dominant.entry_id)
        trunk_targets.append([dominant.entry_id])

    # Side branches from each trunk node
    def expand_side_branch(
        *,
        parent: NodeId,
        target_ids: list[int],
        depth_remaining: int,
        parent_dir: tuple[int, int, int],
        exclude_entry_ids: set[int],
    ) -> None:
        if depth_remaining <= 0:
            return

        total_seen, top_entries = _top_k_entries_for_targets(
            con,
            target_ids=target_ids,
            max_depth=int(branch_reverse_depth),
            top_k=int(branch_k) + len(exclude_entry_ids) + 2,
        )
        denom = max(1, total_seen - len(target_ids))

        picked: list[BranchRow] = []
        for r in top_entries:
            if r.entry_id in exclude_entry_ids:
                continue
            picked.append(r)
            if len(picked) >= int(branch_k):
                break

        child_dirs = _orthogonal_children_dirs(parent_dir, len(picked))

        for r, cdir in zip(picked, child_dirs, strict=False):
            resolve_titles([r.entry_id, *target_ids])
            G.add_node(r.entry_id, kind="branch", mass=float(r.entry_size))
            G.add_edge(
                r.entry_id,
                parent,
                weight=float(r.entry_size),
                share=float(r.entry_size / denom),
                role="branch",
                dir=cdir,
            )

            expand_side_branch(
                parent=r.entry_id,
                target_ids=[r.entry_id],
                depth_remaining=depth_remaining - 1,
                parent_dir=cdir,
                exclude_entry_ids=set(),
            )

    # For each trunk node, show up to branch_k branches excluding the next trunk continuation.
    for idx, node in enumerate(trunk_nodes):
        if node == root_key:
            target_ids = root_ids
        else:
            if not isinstance(node, int):
                continue
            target_ids = [node]

        exclude: set[int] = set()
        if idx + 1 < len(trunk_nodes):
            next_node = trunk_nodes[idx + 1]
            if isinstance(next_node, int):
                exclude.add(next_node)

        dirs = _pick_directions_orthogonal(int(branch_k))

        total_seen, top_entries = _top_k_entries_for_targets(
            con,
            target_ids=target_ids,
            max_depth=int(branch_reverse_depth),
            top_k=int(branch_k) + len(exclude) + 2,
        )
        denom = max(1, total_seen - len(target_ids))

        picked: list[BranchRow] = []
        for r in top_entries:
            if r.entry_id in exclude:
                continue
            picked.append(r)
            if len(picked) >= int(branch_k):
                break

        for r, dvec in zip(picked, dirs, strict=False):
            resolve_titles([r.entry_id, *target_ids])
            G.add_node(r.entry_id, kind="branch", mass=float(r.entry_size))
            G.add_edge(
                r.entry_id,
                node,
                weight=float(r.entry_size),
                share=float(r.entry_size / denom),
                role="branch",
                dir=dvec,
            )
            expand_side_branch(
                parent=r.entry_id,
                target_ids=[r.entry_id],
                depth_remaining=int(branch_depth) - 1,
                parent_dir=dvec,
                exclude_entry_ids=set(),
            )

    # Orthogonal layout
    pos: dict[NodeId, tuple[float, float, float]] = {}

    # Trunk along Z
    z = 0.0
    z_step = 1.2
    for node in trunk_nodes:
        pos[node] = (0.0, 0.0, z)
        z += z_step

    # Side branches extend in XY, with lengths scaled by log(weight)
    def edge_len(w: float, *, base: float, shrink: float) -> float:
        return base * max(0.8, math.log10(max(10.0, w))) * shrink

    children: dict[NodeId, list[tuple[NodeId, dict[str, object]]]] = {n: [] for n in G.nodes}  # type: ignore[assignment]
    for u, v, data in G.edges(data=True):
        children.setdefault(v, []).append((u, data))

    def place_subtree(parent: NodeId, parent_dir: tuple[int, int, int], depth: int, shrink: float) -> None:
        if depth <= 0:
            return
        base_x, base_y, base_z = pos[parent]
        for child, data in children.get(parent, []):
            if data.get("role") == "trunk":
                continue
            if child in pos:
                continue
            raw_dir = data.get("dir", parent_dir)
            if isinstance(raw_dir, tuple) and len(raw_dir) == 3:
                dvec = (int(raw_dir[0]), int(raw_dir[1]), int(raw_dir[2]))
            else:
                dvec = parent_dir
            w_raw = data.get("weight", 1.0)
            w = float(w_raw) if isinstance(w_raw, (int, float)) else 1.0
            step = edge_len(w, base=0.9, shrink=shrink)
            cx = base_x + dvec[0] * step
            cy = base_y + dvec[1] * step
            cz = base_z + 0.15  # slight lift to reduce overlap
            pos[child] = (cx, cy, cz)
            place_subtree(child, dvec, depth - 1, shrink * 0.78)

    for node in trunk_nodes:
        place_subtree(node, (1, 0, 0), int(branch_depth), 1.0)

    # Plotly traces
    edge_x: list[float | None] = []
    edge_y: list[float | None] = []
    edge_z: list[float | None] = []
    for u, v, data in G.edges(data=True):
        if u not in pos or v not in pos:
            continue
        x0, y0, z0 = pos[u]
        x1, y1, z1 = pos[v]
        edge_x.extend([x0, x1, None])
        edge_y.extend([y0, y1, None])
        edge_z.extend([z0, z1, None])

    edge_trace = go.Scatter3d(
        x=edge_x,
        y=edge_y,
        z=edge_z,
        mode="lines",
        line=dict(color="rgba(80,80,80,0.55)", width=3),
        hoverinfo="none",
        name="edges",
    )

    node_x: list[float] = []
    node_y: list[float] = []
    node_z: list[float] = []
    node_text: list[str] = []
    node_size: list[float] = []
    node_color: list[float] = []

    # Resolve any remaining titles
    resolve_titles([nid for nid in G.nodes if isinstance(nid, int)])

    def node_mass(nid: NodeId) -> float:
        if nid in trunk_stats:
            return float(trunk_stats[nid].get("basin_total", 0.0))
        data = G.nodes[nid]
        return float(data.get("mass", 0.0))

    for nid, data in G.nodes(data=True):
        if nid not in pos:
            continue
        x, y, zc = pos[nid]
        node_x.append(float(x))
        node_y.append(float(y))
        node_z.append(float(zc))

        if isinstance(nid, int):
            title = title_cache.get(int(nid), str(nid))
        else:
            title = str(nid)
        kind = data.get("kind", "node")

        mass = node_mass(nid)
        node_text.append(f"{title}<br>kind={kind}<br>mass≈{int(mass):,}")
        node_size.append(6.0 + 3.2 * math.log10(max(10.0, mass)))

        # Color by trunk index if on trunk, else by share/mass-ish
        if nid in trunk_nodes:
            node_color.append(float(trunk_nodes.index(nid)))
        else:
            node_color.append(float(math.log10(max(10.0, mass))))

    node_trace = go.Scatter3d(
        x=node_x,
        y=node_y,
        z=node_z,
        mode="markers",
        marker=dict(size=node_size, color=node_color, colorscale="Viridis", opacity=0.95),
        text=node_text,
        hoverinfo="text",
        name="nodes",
    )

    fig = go.Figure(data=[edge_trace, node_trace])
    fig.update_layout(
        title="Orthogonal Trunk + Side Branches",
        showlegend=False,
        margin=dict(l=0, r=0, t=40, b=0),
        scene=dict(xaxis=dict(visible=False), yaxis=dict(visible=False), zaxis=dict(visible=False)),
    )

    meta = {
        "nodes": int(G.number_of_nodes()),
        "edges": int(G.number_of_edges()),
        "cycle_titles": cycle_titles,
        "trunk_len": int(len(trunk_nodes) - 1),
    }
    return fig, meta


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--host", type=str, default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8050)
    parser.add_argument("--n", type=int, default=5)
    parser.add_argument("--namespace", type=int, default=0)
    parser.add_argument("--allow-redirects", action="store_true")
    parser.add_argument("--cycle", action="append", default=["Massachusetts", "Gulf_of_Maine"], help="Repeatable")
    args = parser.parse_args()

    ANALYSIS_DIR.mkdir(parents=True, exist_ok=True)

    db_path = ANALYSIS_DIR / f"edges_n={int(args.n)}.duckdb"
    con = duckdb.connect(str(db_path))
    _ensure_edges_table(con, n=int(args.n))

    app = dash.Dash(__name__)

    app.layout = html.Div(
        [
            html.H2("N=5 Basin Tributary Viewer (3D)"),
            html.Div(
                [
                    html.Div(
                        [
                            html.Label("Cycle titles (one per line)"),
                            dcc.Textarea(
                                id="cycle-titles",
                                value="\n".join(args.cycle),
                                style={"width": "100%", "height": 90},
                            ),
                            html.Label("View"),
                            dcc.RadioItems(
                                id="view-mode",
                                options=[
                                    {"label": "Tributary skeleton (spring 3D)", "value": "tributary"},
                                    {"label": "Trunk + branches (orthogonal)", "value": "trunk"},
                                ],
                                value="trunk",
                            ),
                            html.Hr(),
                            html.Div(
                                [
                                    html.Label("Trunk steps (dominant-upstream)"),
                                    dcc.Input(id="trunk-steps", type="number", value=14, min=0, max=200, step=1),
                                    html.Br(),
                                    html.Label("Trunk reverse depth (0=exhaustive)"),
                                    dcc.Input(id="trunk-rdepth", type="number", value=0, min=0, max=500, step=1),
                                    html.Br(),
                                    html.Label("Branches per trunk node (K)"),
                                    dcc.Input(id="branch-k", type="number", value=4, min=0, max=50, step=1),
                                    html.Br(),
                                    html.Label("Branch depth (tiers from each trunk node)"),
                                    dcc.Input(id="branch-depth", type="number", value=1, min=0, max=10, step=1),
                                    html.Br(),
                                    html.Label(
                                        "Branch reverse depth (for sizing; 0=exhaustive)"
                                    ),
                                    dcc.Input(id="branch-rdepth", type="number", value=8, min=0, max=500, step=1),
                                ]
                            ),
                            html.Hr(),
                            html.Label("Top-k branches per node (breadth)"),
                            dcc.Input(id="top-k", type="number", value=5, min=1, max=50, step=1),
                            html.Br(),
                            html.Label("Max levels (tree depth / tiers)"),
                            dcc.Input(id="max-levels", type="number", value=5, min=1, max=20, step=1),
                            html.Br(),
                            html.Label("Reverse expansion depth cap (for branch sizing; 0=exhaustive)"),
                            dcc.Input(id="max-depth", type="number", value=8, min=0, max=200, step=1),
                            html.Br(),
                            html.Button("Render", id="render-btn", n_clicks=0),
                            html.Div(id="status", style={"marginTop": 10, "whiteSpace": "pre-wrap"}),
                        ],
                        style={"width": "320px", "paddingRight": 18},
                    ),
                    html.Div(
                        [
                            dcc.Loading(
                                dcc.Graph(id="graph", style={"height": "78vh"}),
                                type="default",
                            )
                        ],
                        style={"flex": "1"},
                    ),
                ],
                style={"display": "flex", "flexDirection": "row"},
            ),
            html.Div(id="hidden-meta", style={"display": "none"}),
        ],
        style={"padding": 12},
    )

    @app.callback(
        Output("graph", "figure"),
        Output("status", "children"),
        Input("render-btn", "n_clicks"),
        State("cycle-titles", "value"),
        State("view-mode", "value"),
        State("trunk-steps", "value"),
        State("trunk-rdepth", "value"),
        State("branch-k", "value"),
        State("branch-depth", "value"),
        State("branch-rdepth", "value"),
        State("top-k", "value"),
        State("max-levels", "value"),
        State("max-depth", "value"),
        prevent_initial_call=True,
    )
    def _render(
        _n_clicks,
        cycle_text,
        view_mode,
        trunk_steps,
        trunk_rdepth,
        branch_k,
        branch_depth,
        branch_rdepth,
        top_k,
        max_levels,
        max_depth,
    ):
        t0 = time.time()
        cycle_titles = [t.strip() for t in (cycle_text or "").splitlines() if t.strip()]
        if not cycle_titles:
            return go.Figure(), "Provide at least one cycle title."

        try:
            if (view_mode or "trunk") == "tributary":
                fig, meta = build_tributary_tree_figure(
                    con,
                    cycle_titles=cycle_titles,
                    namespace=int(args.namespace),
                    allow_redirects=bool(args.allow_redirects),
                    top_k=int(top_k or 5),
                    max_levels=int(max_levels or 5),
                    max_depth=int(max_depth or 8),
                )
            else:
                fig, meta = build_trunk_and_branches_figure(
                    con,
                    cycle_titles=cycle_titles,
                    namespace=int(args.namespace),
                    allow_redirects=bool(args.allow_redirects),
                    trunk_steps=int(trunk_steps or 0),
                    trunk_reverse_depth=int(trunk_rdepth or 0),
                    branch_k=int(branch_k or 0),
                    branch_depth=int(branch_depth or 0),
                    branch_reverse_depth=int(branch_rdepth or 0),
                )
        except Exception as e:
            return go.Figure(), f"Error: {e}"

        dt = time.time() - t0
        status = (
            f"cycle={cycle_titles}\n"
            f"nodes={meta['nodes']:,} edges={meta['edges']:,}\n"
            f"render_time={dt:.2f}s"
        )
        return fig, status

    print(f"Starting Dash on http://{args.host}:{args.port}  (Ctrl+C to stop)")
    app.run(host=args.host, port=args.port, debug=False)

    con.close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
