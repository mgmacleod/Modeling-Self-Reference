#!/usr/bin/env python3
"""Render a *fully mapped* basin as a 3D geometric object (point cloud).

This is a human-facing geometry/export pipeline. It creates shareable artifacts
(Parquet + optional HTML preview) that the Dash viewer can render cheaply.

Run (repo root)
--------------
  python n-link-analysis/viz/render-full-basin-geometry.py \
    --n 5 --cycle-title "American_Revolutionary_War" --cycle-title "Eastern_United_States" \
    --max-depth 0 --max-nodes 0 --write-html --max-plot-points 120000
"""

from __future__ import annotations

import argparse
import math
import random
import re
import time
from pathlib import Path

import duckdb
import numpy as np
import pandas as pd
import plotly.graph_objects as go
import pyarrow as pa
import pyarrow.parquet as pq


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
    n_edges_row = con.execute("SELECT COUNT(*) FROM edges").fetchone()
    n_edges = int(n_edges_row[0]) if n_edges_row is not None and n_edges_row[0] is not None else 0
    print(f"Edges table ready: {n_edges:,} edges in {dt:.1f}s")


def map_basin_with_parent(
    con: duckdb.DuckDBPyConnection,
    *,
    cycle_ids: list[int],
    max_depth: int,
    max_nodes: int,
    log_every: int,
) -> pa.Table:
    """Reverse BFS with a single chosen parent per node (a BFS spanning forest)."""

    con.execute("DROP TABLE IF EXISTS seen")
    con.execute("DROP TABLE IF EXISTS frontier")
    con.execute("DROP TABLE IF EXISTS next_frontier")

    con.execute("CREATE TEMP TABLE seen(page_id BIGINT PRIMARY KEY, parent_id BIGINT, depth INTEGER)")
    con.execute("CREATE TEMP TABLE frontier(page_id BIGINT PRIMARY KEY, depth INTEGER)")

    for cid in cycle_ids:
        con.execute("INSERT INTO seen VALUES (?, NULL, 0)", [int(cid)])
        con.execute("INSERT INTO frontier VALUES (?, 0)", [int(cid)])

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
                min(f.page_id) AS parent_id,
                min(f.depth + 1) AS depth
            FROM edges e
            JOIN frontier f
              ON e.dst_page_id = f.page_id
            LEFT JOIN seen s
              ON s.page_id = e.src_page_id
            WHERE s.page_id IS NULL
            GROUP BY e.src_page_id
            """.strip()
        )

        row = con.execute("SELECT COUNT(*) FROM next_frontier").fetchone()
        new_nodes = int(row[0]) if row is not None and row[0] is not None else 0
        if new_nodes == 0:
            break

        con.execute("INSERT INTO seen SELECT page_id, parent_id, depth FROM next_frontier")

        total_row = con.execute("SELECT COUNT(*) FROM seen").fetchone()
        total = int(total_row[0]) if total_row is not None and total_row[0] is not None else 0

        if log_every and (depth % log_every == 0):
            print(f"depth={depth + 1:>4}  new={new_nodes:>8,}  total={total:>10,}")

        if max_nodes and total >= max_nodes:
            print(f"Stopping at max_nodes={max_nodes:,}")
            break

        con.execute("DELETE FROM frontier")
        con.execute("INSERT INTO frontier SELECT page_id, depth FROM next_frontier")
        depth += 1

    tbl = con.execute("SELECT page_id, parent_id, depth FROM seen").fetch_arrow_table()

    con.execute("DROP TABLE IF EXISTS seen")
    con.execute("DROP TABLE IF EXISTS frontier")
    con.execute("DROP TABLE IF EXISTS next_frontier")

    return tbl


def assign_layered_radial_coords(
    df: pd.DataFrame,
    *,
    z_step: float,
    radius_scale: float,
    twist_per_layer: float,
) -> pd.DataFrame:
    """Add x,y,z columns to df using deterministic golden-angle packing per depth layer."""

    golden_angle = math.pi * (3 - math.sqrt(5))

    df = df.copy()
    df["x"] = 0.0
    df["y"] = 0.0
    df["z"] = df["depth"].astype(float) * float(z_step)

    depths = df["depth"].to_numpy(dtype=np.int32)
    order = np.lexsort((df["page_id"].to_numpy(dtype=np.int64), depths))
    df = df.iloc[order].reset_index(drop=True)
    depths = df["depth"].to_numpy(dtype=np.int32)

    unique_depths, starts = np.unique(depths, return_index=True)
    ends = np.append(starts[1:], len(df))

    for d, s, e in zip(unique_depths.tolist(), starts.tolist(), ends.tolist(), strict=False):
        n = e - s
        if n <= 0:
            continue

        layer_radius = float(radius_scale) * math.sqrt(float(n))
        twist = float(twist_per_layer) * float(d)

        idx = np.arange(n, dtype=np.float32)
        r = np.sqrt((idx + 0.5) / float(n)) * layer_radius
        theta = idx * golden_angle + twist
        x = r * np.cos(theta)
        y = r * np.sin(theta)

        df.loc[s : e - 1, "x"] = x
        df.loc[s : e - 1, "y"] = y

    return df


def build_pointcloud_figure(
    df: pd.DataFrame,
    *,
    title: str,
    max_points: int,
    seed: int,
) -> go.Figure:
    if max_points and len(df) > max_points:
        rng = random.Random(int(seed))
        keep = rng.sample(range(len(df)), k=int(max_points))
        df_plot = df.iloc[keep].copy()
    else:
        df_plot = df

    depth = df_plot["depth"].to_numpy(dtype=np.float32)
    size = 2.0 + 0.5 * np.log10(1.0 + depth)

    fig = go.Figure(
        data=[
            go.Scatter3d(
                x=df_plot["x"],
                y=df_plot["y"],
                z=df_plot["z"],
                mode="markers",
                marker=dict(
                    size=size,
                    color=depth,
                    colorscale="Viridis",
                    opacity=0.85,
                ),
                hoverinfo="skip",
            )
        ]
    )

    fig.update_layout(
        title=title,
        showlegend=False,
        margin=dict(l=0, r=0, t=40, b=0),
        scene=dict(xaxis=dict(visible=False), yaxis=dict(visible=False), zaxis=dict(visible=False)),
    )
    return fig


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--n", type=int, default=5)
    parser.add_argument("--cycle-page-id", type=int, action="append", default=[])
    parser.add_argument("--cycle-title", type=str, action="append", default=[])
    parser.add_argument("--namespace", type=int, default=0)
    parser.add_argument("--allow-redirects", action="store_true")

    parser.add_argument("--max-depth", type=int, default=0, help="Reverse BFS depth cap (0=exhaustive)")
    parser.add_argument("--max-nodes", type=int, default=0, help="Stop after discovering this many nodes (0=exhaustive)")
    parser.add_argument("--log-every", type=int, default=1)

    parser.add_argument("--z-step", type=float, default=0.35)
    parser.add_argument("--radius-scale", type=float, default=0.015)
    parser.add_argument("--twist-per-layer", type=float, default=0.15)

    parser.add_argument("--write-html", action="store_true")
    parser.add_argument("--max-plot-points", type=int, default=120_000)
    parser.add_argument("--seed", type=int, default=0)

    args = parser.parse_args()

    title_to_id = _resolve_titles_to_ids(
        args.cycle_title,
        namespace=int(args.namespace),
        allow_redirects=bool(args.allow_redirects),
    )
    missing = [t for t in args.cycle_title if t not in title_to_id]
    if missing:
        raise SystemExit(f"Could not resolve cycle titles (exact match failed): {missing}")

    cycle_ids = list(dict.fromkeys([*map(int, args.cycle_page_id), *title_to_id.values()]))
    if not cycle_ids:
        raise SystemExit("Provide at least one --cycle-page-id or --cycle-title")

    ANALYSIS_DIR.mkdir(parents=True, exist_ok=True)
    REPORT_ASSETS_DIR.mkdir(parents=True, exist_ok=True)

    cycle_slug = "__".join([_slug(t) for t in (args.cycle_title or [str(i) for i in cycle_ids])])
    out_parquet = ANALYSIS_DIR / f"basin_pointcloud_n={int(args.n)}_cycle={cycle_slug}.parquet"
    out_html = REPORT_ASSETS_DIR / f"basin_pointcloud_3d_n={int(args.n)}_cycle={cycle_slug}.html"

    db_path = ANALYSIS_DIR / f"edges_n={int(args.n)}.duckdb"
    con = duckdb.connect(str(db_path))
    _ensure_edges_table(con, n=int(args.n))

    print(f"Mapping basin for cycle_ids={cycle_ids} (N={int(args.n)})")
    t0 = time.time()
    tbl = map_basin_with_parent(
        con,
        cycle_ids=cycle_ids,
        max_depth=int(args.max_depth),
        max_nodes=int(args.max_nodes),
        log_every=int(args.log_every),
    )
    con.close()
    dt = time.time() - t0

    df = tbl.to_pandas()
    df["page_id"] = df["page_id"].astype("int64")
    df["depth"] = df["depth"].astype("int32")
    if "parent_id" in df.columns:
        df["parent_id"] = df["parent_id"].astype("Int64")

    print(f"Mapped nodes: {len(df):,} in {dt:.1f}s")

    df = assign_layered_radial_coords(
        df,
        z_step=float(args.z_step),
        radius_scale=float(args.radius_scale),
        twist_per_layer=float(args.twist_per_layer),
    )

    pq.write_table(pa.Table.from_pandas(df, preserve_index=False), out_parquet)
    print(f"Wrote: {out_parquet}")

    if args.write_html:
        fig = build_pointcloud_figure(
            df,
            title=f"Full basin point cloud (N={int(args.n)})",
            max_points=int(args.max_plot_points),
            seed=int(args.seed),
        )
        fig.write_html(str(out_html), include_plotlyjs="cdn")
        print(f"Wrote: {out_html}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
