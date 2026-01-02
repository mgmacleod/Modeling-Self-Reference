#!/usr/bin/env python3
"""Dash app: interactive basin geometry viewer.

This is a human-facing visualization workbench. It intentionally avoids *live*
reverse-graph expansion. Instead, it renders precomputed basin artifacts
(Parquet) quickly and deterministically.

Views
-----
1) 3D point cloud ("violin")
   - Plots (x,y,z) from the Parquet directly.

2) 2D recursive-space layout (interval allocation)
   - Uses the parent pointer in the Parquet to build an in-tree rooted at the cycle.
   - Assigns each node an x-position via disjoint interval subdivision.

3) 2D fan (top-down) + edges
   - Converts the interval x-position into an angular coordinate.
   - Draws parent→child links (optionally bundled) for a tributary/radiating look.

4) 3D fan + edges
    - Same fan projection as (3), but rendered in 3D.
    - Uses depth as both fan radius and z-height (simple cone) for a rotatable view.

Run (repo root)
--------------
  python n-link-analysis/viz/dash-basin-geometry-viewer.py --host 127.0.0.1 --port 8054
"""

from __future__ import annotations

import argparse
import functools
import random
import re
import time
from pathlib import Path
from typing import TypeAlias

import dash
from dash import Input, Output, State, dcc, html
import numpy as np
import pandas as pd
import plotly.graph_objects as go
import pyarrow.parquet as pq

from shared import REPO_ROOT


PROCESSED_DIR = REPO_ROOT / "data" / "wikipedia" / "processed"
ANALYSIS_DIR = PROCESSED_DIR / "analysis"

NodeId: TypeAlias = int | str


def _slug(s: str) -> str:
    s = s.strip()
    s = re.sub(r"\s+", "_", s)
    s = re.sub(r"[^A-Za-z0-9_\-()]+", "", s)
    return s[:120] if len(s) > 120 else s


def _list_pointcloud_parquets() -> list[Path]:
    if not ANALYSIS_DIR.exists():
        return []
    files = sorted(ANALYSIS_DIR.glob("basin_pointcloud_n=*_cycle=*.parquet"))
    return files


@functools.lru_cache(maxsize=3)
def _load_pointcloud_df(parquet_path: str) -> pd.DataFrame:
    """Load a pointcloud parquet into memory with a tiny LRU cache."""

    path = Path(parquet_path)
    if not path.exists():
        raise FileNotFoundError(f"Missing: {path}")
    tbl = pq.read_table(path)
    df = tbl.to_pandas()

    df["page_id"] = df["page_id"].astype("int64")
    df["depth"] = df["depth"].astype("int32")
    if "parent_id" in df.columns:
        df["parent_id"] = df["parent_id"].astype("Int64")
    for col in ["x", "y", "z"]:
        df[col] = df[col].astype("float64")
    return df


@functools.lru_cache(maxsize=3)
def _compute_tree_layout_cached(parquet_path: str) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """Compute (x2, subtree_span, out_degree) aligned to the parquet's df order."""

    df = _load_pointcloud_df(parquet_path)
    if "parent_id" not in df.columns:
        raise ValueError("Pointcloud parquet is missing parent_id; regenerate with viz/render-full-basin-geometry.py")

    page_ids = df["page_id"].to_numpy(dtype=np.int64)
    parent_ids = df["parent_id"].to_numpy(dtype=object)

    root_id = -1
    children: dict[int, list[int]] = {}
    roots: list[int] = []

    for pid, par in zip(page_ids.tolist(), parent_ids.tolist(), strict=False):
        if par is None or str(par) == "<NA>":
            roots.append(int(pid))
            continue
        parent_int = int(par)
        children.setdefault(parent_int, []).append(int(pid))

    if not roots:
        raise ValueError("No roots found (parent_id all non-null). Expected cycle nodes with parent_id=NULL.")
    children[root_id] = sorted(roots)

    for k in list(children.keys()):
        children[k].sort()

    # Postorder subtree span (leaf-count with unit leaves).
    span: dict[int, int] = {}
    stack: list[tuple[int, int]] = [(root_id, 0)]
    while stack:
        node, state = stack.pop()
        if state == 0:
            stack.append((node, 1))
            for ch in children.get(node, []):
                stack.append((int(ch), 0))
        else:
            chs = children.get(node, [])
            if not chs:
                span[node] = 1
            else:
                span[node] = max(1, int(sum(span[int(c)] for c in chs)))

    # Sort children by descending span (tie-break id).
    for node, chs in list(children.items()):
        if len(chs) <= 1:
            continue
        chs.sort(key=lambda c: (-span[int(c)], int(c)))
        children[node] = chs

    # Top-down interval assignment.
    x_mid: dict[int, float] = {}
    total = float(span[root_id])
    stack2: list[tuple[int, float, float]] = [(root_id, 0.0, total)]
    while stack2:
        node, a, b = stack2.pop()
        x_mid[node] = (a + b) / 2.0
        cursor = a
        for ch in children.get(node, []):
            w = float(span[int(ch)])
            ca, cb = cursor, cursor + w
            cursor = cb
            stack2.append((int(ch), ca, cb))

    denom = max(1e-9, total / 2.0)
    x2 = np.array([(x_mid.get(int(pid), 0.0) - total / 2.0) / denom for pid in page_ids.tolist()], dtype=np.float64)
    span_arr = np.array([float(span.get(int(pid), 1)) for pid in page_ids.tolist()], dtype=np.float64)
    outdeg_arr = np.array([float(len(children.get(int(pid), []))) for pid in page_ids.tolist()], dtype=np.float64)
    return x2, span_arr, outdeg_arr


def _sample_pointcloud(df: pd.DataFrame, *, max_points: int, mode: str, seed: int) -> pd.DataFrame:
    if max_points <= 0 or len(df) <= max_points:
        return df

    rng = random.Random(int(seed))
    if mode == "by_depth":
        depths = df["depth"].to_numpy()
        unique, counts = np.unique(depths, return_counts=True)
        total = int(len(df))
        alloc = {int(d): max(5, int(round(max_points * (c / total)))) for d, c in zip(unique, counts, strict=False)}
        drift = sum(alloc.values()) - int(max_points)
        if drift != 0:
            order = sorted(unique.tolist(), key=lambda d: alloc[int(d)], reverse=True)
            i = 0
            while drift != 0 and i < len(order):
                dd = int(order[i])
                if drift > 0 and alloc[dd] > 5:
                    alloc[dd] -= 1
                    drift -= 1
                elif drift < 0:
                    alloc[dd] += 1
                    drift += 1
                else:
                    i += 1

        keep_idx: list[int] = []
        for d, k in alloc.items():
            layer = df.index[df["depth"] == d].to_list()
            if not layer:
                continue
            if len(layer) <= k:
                keep_idx.extend(layer)
            else:
                keep_idx.extend(rng.sample(layer, k=k))
        return df.loc[keep_idx]

    keep = rng.sample(range(len(df)), k=int(max_points))
    return df.iloc[keep]


def build_pointcloud_figure_from_df(
    df: pd.DataFrame,
    *,
    title: str,
    max_points: int,
    sampling_mode: str,
    depth_min: int,
    depth_max: int,
    point_size: float,
    opacity: float,
    seed: int,
    camera: dict | None,
) -> go.Figure:
    dmin = int(max(0, depth_min))
    dmax = int(depth_max)
    if dmax <= 0:
        dmax = int(df["depth"].max())

    df_f = df[(df["depth"] >= dmin) & (df["depth"] <= dmax)]
    if df_f.empty:
        fig = go.Figure()
        fig.update_layout(title=f"{title} (no points in depth range)")
        return fig

    df_plot = _sample_pointcloud(df_f, max_points=int(max_points), mode=str(sampling_mode), seed=int(seed)).copy()
    depth = df_plot["depth"].to_numpy(dtype=np.float32)

    fig = go.Figure(
        data=[
            go.Scatter3d(
                x=df_plot["x"],
                y=df_plot["y"],
                z=df_plot["z"],
                mode="markers",
                marker=dict(
                    size=float(point_size),
                    color=depth,
                    colorscale="Viridis",
                    opacity=float(opacity),
                ),
                hoverinfo="skip",
                name="points",
            )
        ]
    )

    scene = dict(xaxis=dict(visible=False), yaxis=dict(visible=False), zaxis=dict(visible=False))
    if camera:
        scene["camera"] = camera

    fig.update_layout(
        title=title,
        showlegend=False,
        margin=dict(l=0, r=0, t=40, b=0),
        scene=scene,
    )
    return fig


def _get_color_values(
    df: pd.DataFrame,
    *,
    color_mode: str,
    subtree_span: pd.Series,
    out_degree: pd.Series,
) -> np.ndarray:
    mode = (color_mode or "depth").strip().lower()
    if mode == "subtree_span":
        return np.log10(1.0 + subtree_span.to_numpy(dtype=np.float32))
    if mode == "out_degree":
        return np.log10(1.0 + out_degree.to_numpy(dtype=np.float32))
    return df["depth"].to_numpy(dtype=np.float32)


def _robust_unit_scale(values: np.ndarray) -> np.ndarray:
    """Robustly scale to approximately [-1, 1] using quantiles.

    Intended for visualization embeddings where raw magnitudes may vary widely.
    """

    v = np.asarray(values, dtype=np.float64)
    if v.size == 0:
        return v
    if np.all(~np.isfinite(v)):
        return np.zeros_like(v)

    finite = v[np.isfinite(v)]
    if finite.size == 0:
        return np.zeros_like(v)

    q05 = float(np.quantile(finite, 0.05))
    q50 = float(np.quantile(finite, 0.50))
    q95 = float(np.quantile(finite, 0.95))
    half = max(1e-9, (q95 - q05) / 2.0)
    out = (v - q50) / half
    out = np.clip(out, -1.0, 1.0)
    out[~np.isfinite(out)] = 0.0
    return out


def build_recursive_space_2d_figure_from_df(
    df: pd.DataFrame,
    *,
    title: str,
    max_points: int,
    sampling_mode: str,
    depth_min: int,
    depth_max: int,
    point_size: float,
    opacity: float,
    seed: int,
    x2: pd.Series,
    subtree_span: pd.Series,
    out_degree: pd.Series,
    color_mode: str,
) -> go.Figure:
    dmin = int(max(0, depth_min))
    dmax = int(depth_max)
    if dmax <= 0:
        dmax = int(df["depth"].max())

    df_f = df[(df["depth"] >= dmin) & (df["depth"] <= dmax)]
    if df_f.empty:
        fig = go.Figure()
        fig.update_layout(title=f"{title} (no points in depth range)")
        return fig

    df_plot_base = df_f.copy()
    df_plot_base["x2"] = x2.loc[df_plot_base.index]
    df_plot_base["_span"] = subtree_span.loc[df_plot_base.index]
    df_plot_base["_outdeg"] = out_degree.loc[df_plot_base.index]

    df_plot = _sample_pointcloud(df_plot_base, max_points=int(max_points), mode=str(sampling_mode), seed=int(seed)).copy()
    color = _get_color_values(
        df_plot,
        color_mode=str(color_mode or "depth"),
        subtree_span=df_plot["_span"],
        out_degree=df_plot["_outdeg"],
    )

    fig = go.Figure(
        data=[
            go.Scattergl(
                x=df_plot["x2"],
                y=df_plot["depth"],
                mode="markers",
                marker=dict(
                    size=float(point_size),
                    color=color,
                    colorscale="Viridis",
                    opacity=float(opacity),
                ),
                hoverinfo="skip",
                name="points",
            )
        ]
    )
    fig.update_layout(
        title=title,
        showlegend=False,
        margin=dict(l=0, r=0, t=40, b=0),
        xaxis=dict(visible=False),
        yaxis=dict(title="reverse depth", autorange="reversed"),
    )
    return fig


def build_fan_edges_2d_figure_from_df(
    df: pd.DataFrame,
    *,
    title: str,
    max_points: int,
    sampling_mode: str,
    depth_min: int,
    depth_max: int,
    point_size: float,
    point_opacity: float,
    seed: int,
    show_edges: bool,
    max_edges: int,
    edge_opacity: float,
    edge_width: float,
    angle_span_degrees: float,
    radius_step: float,
    edge_depth_max: int,
    bundle_edges: bool,
    bundle_pull: float,
    x2: pd.Series,
    subtree_span: pd.Series,
    out_degree: pd.Series,
    color_mode: str,
) -> go.Figure:
    dmin = int(max(0, depth_min))
    dmax = int(depth_max)
    if dmax <= 0:
        dmax = int(df["depth"].max())

    df_f = df[(df["depth"] >= dmin) & (df["depth"] <= dmax)]
    if df_f.empty:
        fig = go.Figure()
        fig.update_layout(title=f"{title} (no points in depth range)")
        return fig

    df_plot_base = df_f.copy()
    df_plot_base["x2"] = x2.loc[df_plot_base.index]
    df_plot_base["_span"] = subtree_span.loc[df_plot_base.index]
    df_plot_base["_outdeg"] = out_degree.loc[df_plot_base.index]

    df_points = _sample_pointcloud(df_plot_base, max_points=int(max_points), mode=str(sampling_mode), seed=int(seed)).copy()

    span_rad = float(angle_span_degrees) * (np.pi / 180.0)
    theta = df_points["x2"].to_numpy(dtype=np.float64) * (span_rad / 2.0)
    r = df_points["depth"].to_numpy(dtype=np.float64) * float(radius_step)
    px = r * np.cos(theta)
    py = r * np.sin(theta)

    fig = go.Figure()

    if show_edges:
        if "parent_id" not in df_plot_base.columns:
            raise ValueError("Pointcloud parquet is missing parent_id; regenerate with viz/render-full-basin-geometry.py")

        df_edges = df_plot_base
        edmax = int(edge_depth_max or 0)
        if edmax > 0:
            df_edges = df_edges[df_edges["depth"] <= edmax]

        if int(max_edges) > 0 and len(df_edges) > int(max_edges):
            df_edges = _sample_pointcloud(df_edges, max_points=int(max_edges), mode="random", seed=int(seed))

        x2_e = x2.loc[df_edges.index].to_numpy(dtype=np.float64)
        theta_e = x2_e * (span_rad / 2.0)
        r_e = df_edges["depth"].to_numpy(dtype=np.float64) * float(radius_step)
        ex = r_e * np.cos(theta_e)
        ey = r_e * np.sin(theta_e)

        ids_e = df_edges["page_id"].to_numpy(dtype=np.int64)
        parent_e = df_edges["parent_id"].to_numpy(dtype=object)
        span_e = df_edges["_span"].to_numpy(dtype=np.float64)

        coord: dict[int, tuple[float, float, float]] = {
            int(i): (float(x), float(y), float(s))
            for i, x, y, s in zip(ids_e.tolist(), ex.tolist(), ey.tolist(), span_e.tolist(), strict=False)
        }

        spans = np.array([s for _, (_, _, s) in coord.items()], dtype=np.float64)
        if spans.size:
            q1 = float(np.quantile(spans, 0.50))
            q2 = float(np.quantile(spans, 0.90))
        else:
            q1, q2 = 1.0, 10.0

        bins = [
            {"name": "edges_small", "xs": [], "ys": [], "w": 0.8},
            {"name": "edges_med", "xs": [], "ys": [], "w": 1.4},
            {"name": "edges_big", "xs": [], "ys": [], "w": 2.3},
        ]

        pull = float(bundle_pull)
        pull = 0.0 if pull < 0.0 else (1.0 if pull > 1.0 else pull)

        for cid, pid in zip(ids_e.tolist(), parent_e.tolist(), strict=False):
            if pid is None or str(pid) == "<NA>":
                continue
            parent_id = int(pid)
            a = coord.get(int(cid))
            b = coord.get(parent_id)
            if a is None or b is None:
                continue
            ax, ay, aspan = a
            bx, by, _ = b

            if aspan >= q2:
                bucket = bins[2]
            elif aspan >= q1:
                bucket = bins[1]
            else:
                bucket = bins[0]

            if bundle_edges and pull > 0.0:
                mx = ax * (1.0 - pull) + bx * pull
                my = ay * (1.0 - pull) + by * pull
                bucket["xs"].extend([ax, mx, bx, None])
                bucket["ys"].extend([ay, my, by, None])
            else:
                bucket["xs"].extend([ax, bx, None])
                bucket["ys"].extend([ay, by, None])

        for b in bins:
            if not b["xs"]:
                continue
            fig.add_trace(
                go.Scattergl(
                    x=b["xs"],
                    y=b["ys"],
                    mode="lines",
                    line=dict(
                        color=f"rgba(80,80,80,{float(edge_opacity):.3f})",
                        width=float(edge_width) * float(b["w"]),
                    ),
                    hoverinfo="skip",
                    name=b["name"],
                )
            )

    color = _get_color_values(
        df_points,
        color_mode=str(color_mode or "depth"),
        subtree_span=df_points["_span"],
        out_degree=df_points["_outdeg"],
    )

    fig.add_trace(
        go.Scattergl(
            x=px,
            y=py,
            mode="markers",
            marker=dict(
                size=float(point_size),
                color=color,
                colorscale="Viridis",
                opacity=float(point_opacity),
            ),
            hoverinfo="skip",
            name="points",
        )
    )

    fig.update_layout(
        title=title,
        showlegend=False,
        margin=dict(l=0, r=0, t=40, b=0),
        xaxis=dict(visible=False, scaleanchor="y", scaleratio=1),
        yaxis=dict(visible=False),
    )
    return fig


def build_fan_edges_3d_figure_from_df(
    df: pd.DataFrame,
    *,
    title: str,
    max_points: int,
    sampling_mode: str,
    depth_min: int,
    depth_max: int,
    point_size: float,
    point_opacity: float,
    seed: int,
    show_edges: bool,
    max_edges: int,
    edge_opacity: float,
    edge_width: float,
    angle_span_degrees: float,
    radius_step: float,
    edge_depth_max: int,
    bundle_edges: bool,
    bundle_pull: float,
    x2: pd.Series,
    subtree_span: pd.Series,
    out_degree: pd.Series,
    color_mode: str,
    z_mode: str,
    z_scale: float,
    camera: dict | None,
) -> go.Figure:
    dmin = int(max(0, depth_min))
    dmax = int(depth_max)
    if dmax <= 0:
        dmax = int(df["depth"].max())

    df_f = df[(df["depth"] >= dmin) & (df["depth"] <= dmax)]
    if df_f.empty:
        fig = go.Figure()
        fig.update_layout(title=f"{title} (no points in depth range)")
        return fig

    df_plot_base = df_f.copy()
    df_plot_base["x2"] = x2.loc[df_plot_base.index]
    df_plot_base["_span"] = subtree_span.loc[df_plot_base.index]
    df_plot_base["_outdeg"] = out_degree.loc[df_plot_base.index]

    df_points = _sample_pointcloud(df_plot_base, max_points=int(max_points), mode=str(sampling_mode), seed=int(seed)).copy()

    span_rad = float(angle_span_degrees) * (np.pi / 180.0)
    theta = df_points["x2"].to_numpy(dtype=np.float64) * (span_rad / 2.0)
    depth = df_points["depth"].to_numpy(dtype=np.float64)
    r = depth * float(radius_step)
    px = r * np.cos(theta)
    py = r * np.sin(theta)

    z_mode_n = (z_mode or "depth_cone").strip().lower()
    z_scale_f = float(z_scale)
    if z_scale_f <= 0:
        z_scale_f = 1.0

    if z_mode_n == "flat":
        pz = np.zeros_like(depth)
    elif z_mode_n == "parquet_z":
        zraw = df_points["z"].to_numpy(dtype=np.float64)
        pz = _robust_unit_scale(zraw) * z_scale_f * float(radius_step) * np.maximum(1.0, depth)
    elif z_mode_n == "crystal_span":
        span_log = np.log10(1.0 + df_points["_span"].to_numpy(dtype=np.float64))
        pz = _robust_unit_scale(span_log) * z_scale_f * float(radius_step) * np.maximum(1.0, depth)
    elif z_mode_n == "twist":
        # Helical twist: depth cone with an angular-dependent lift.
        pz = depth * float(radius_step) + (theta / max(1e-9, (span_rad / 2.0))) * z_scale_f * float(radius_step) * 5.0
    elif z_mode_n == "watershed_bowl":
        # Bowl: higher depth drops "down" into a basin.
        max_r = max(1e-9, float(dmax) * float(radius_step))
        pz = -((r / max_r) ** 2) * z_scale_f * max_r
    else:
        # Default: simple cone.
        pz = depth * float(radius_step)

    fig = go.Figure()

    if show_edges:
        if "parent_id" not in df_plot_base.columns:
            raise ValueError("Pointcloud parquet is missing parent_id; regenerate with viz/render-full-basin-geometry.py")

        df_edges = df_plot_base
        edmax = int(edge_depth_max or 0)
        if edmax > 0:
            df_edges = df_edges[df_edges["depth"] <= edmax]

        if int(max_edges) > 0 and len(df_edges) > int(max_edges):
            df_edges = _sample_pointcloud(df_edges, max_points=int(max_edges), mode="random", seed=int(seed))

        x2_e = x2.loc[df_edges.index].to_numpy(dtype=np.float64)
        theta_e = x2_e * (span_rad / 2.0)
        depth_e = df_edges["depth"].to_numpy(dtype=np.float64)
        r_e = depth_e * float(radius_step)
        ex = r_e * np.cos(theta_e)
        ey = r_e * np.sin(theta_e)

        if z_mode_n == "flat":
            ez = np.zeros_like(depth_e)
        elif z_mode_n == "parquet_z":
            zraw_e = df_edges["z"].to_numpy(dtype=np.float64)
            ez = _robust_unit_scale(zraw_e) * z_scale_f * float(radius_step) * np.maximum(1.0, depth_e)
        elif z_mode_n == "crystal_span":
            span_log_e = np.log10(1.0 + df_edges["_span"].to_numpy(dtype=np.float64))
            ez = _robust_unit_scale(span_log_e) * z_scale_f * float(radius_step) * np.maximum(1.0, depth_e)
        elif z_mode_n == "twist":
            ez = depth_e * float(radius_step) + (theta_e / max(1e-9, (span_rad / 2.0))) * z_scale_f * float(radius_step) * 5.0
        elif z_mode_n == "watershed_bowl":
            max_r = max(1e-9, float(dmax) * float(radius_step))
            ez = -((r_e / max_r) ** 2) * z_scale_f * max_r
        else:
            ez = depth_e * float(radius_step)

        ids_e = df_edges["page_id"].to_numpy(dtype=np.int64)
        parent_e = df_edges["parent_id"].to_numpy(dtype=object)
        span_e = df_edges["_span"].to_numpy(dtype=np.float64)

        coord: dict[int, tuple[float, float, float, float]] = {
            int(i): (float(x), float(y), float(z), float(s))
            for i, x, y, z, s in zip(ids_e.tolist(), ex.tolist(), ey.tolist(), ez.tolist(), span_e.tolist(), strict=False)
        }

        spans = np.array([s for _, (_, _, _, s) in coord.items()], dtype=np.float64)
        if spans.size:
            q1 = float(np.quantile(spans, 0.50))
            q2 = float(np.quantile(spans, 0.90))
        else:
            q1, q2 = 1.0, 10.0

        bins = [
            {"name": "edges_small", "xs": [], "ys": [], "zs": [], "w": 0.8},
            {"name": "edges_med", "xs": [], "ys": [], "zs": [], "w": 1.4},
            {"name": "edges_big", "xs": [], "ys": [], "zs": [], "w": 2.3},
        ]

        pull = float(bundle_pull)
        pull = 0.0 if pull < 0.0 else (1.0 if pull > 1.0 else pull)

        for cid, pid in zip(ids_e.tolist(), parent_e.tolist(), strict=False):
            if pid is None or str(pid) == "<NA>":
                continue
            parent_id = int(pid)
            a = coord.get(int(cid))
            b = coord.get(parent_id)
            if a is None or b is None:
                continue
            ax, ay, az, aspan = a
            bx, by, bz, _ = b

            if aspan >= q2:
                bucket = bins[2]
            elif aspan >= q1:
                bucket = bins[1]
            else:
                bucket = bins[0]

            if bundle_edges and pull > 0.0:
                mx = ax * (1.0 - pull) + bx * pull
                my = ay * (1.0 - pull) + by * pull
                mz = az * (1.0 - pull) + bz * pull
                bucket["xs"].extend([ax, mx, bx, None])
                bucket["ys"].extend([ay, my, by, None])
                bucket["zs"].extend([az, mz, bz, None])
            else:
                bucket["xs"].extend([ax, bx, None])
                bucket["ys"].extend([ay, by, None])
                bucket["zs"].extend([az, bz, None])

        for b in bins:
            if not b["xs"]:
                continue
            fig.add_trace(
                go.Scatter3d(
                    x=b["xs"],
                    y=b["ys"],
                    z=b["zs"],
                    mode="lines",
                    line=dict(
                        color=f"rgba(80,80,80,{float(edge_opacity):.3f})",
                        width=float(edge_width) * float(b["w"]),
                    ),
                    hoverinfo="skip",
                    name=b["name"],
                )
            )

    color = _get_color_values(
        df_points,
        color_mode=str(color_mode or "depth"),
        subtree_span=df_points["_span"],
        out_degree=df_points["_outdeg"],
    )

    fig.add_trace(
        go.Scatter3d(
            x=px,
            y=py,
            z=pz,
            mode="markers",
            marker=dict(
                size=float(point_size),
                color=color,
                colorscale="Viridis",
                opacity=float(point_opacity),
            ),
            hoverinfo="skip",
            name="points",
        )
    )

    scene = dict(xaxis=dict(visible=False), yaxis=dict(visible=False), zaxis=dict(visible=False))
    if camera:
        scene["camera"] = camera

    fig.update_layout(
        title=title,
        showlegend=False,
        margin=dict(l=0, r=0, t=40, b=0),
        scene=scene,
    )
    return fig


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--host", type=str, default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8050)
    args = parser.parse_args()

    ANALYSIS_DIR.mkdir(parents=True, exist_ok=True)

    app = dash.Dash(__name__)

    pointcloud_files = _list_pointcloud_parquets()
    pc_options = [{"label": p.name, "value": str(p)} for p in pointcloud_files]
    default_pc = pc_options[0]["value"] if pc_options else None

    app.layout = html.Div(
        [
            html.H2("Basin Geometry Viewer"),
            html.Div(
                [
                    html.Div(
                        [
                            html.Label("View"),
                            dcc.RadioItems(
                                id="view-mode",
                                options=[
                                    {"label": "3D point cloud (violin)", "value": "pointcloud"},
                                    {"label": "2D recursive space (interval)", "value": "recursive2d"},
                                    {"label": "2D fan (top-down) + edges", "value": "fan2d"},
                                    {"label": "3D fan + edges", "value": "fan3d"},
                                ],
                                value="pointcloud",
                            ),
                            html.Hr(),
                            html.Div(
                                [
                                    html.H4("Dataset", style={"margin": "6px 0"}),
                                    html.Label("Pointcloud dataset (Parquet)"),
                                    dcc.Dropdown(
                                        id="pc-path",
                                        options=pc_options,  # type: ignore[arg-type]
                                        value=default_pc,
                                        placeholder="No pointcloud parquet found under analysis/",
                                    ),
                                    html.Label("Sampling"),
                                    dcc.Dropdown(
                                        id="pc-sampling",
                                        options=[
                                            {"label": "Stratified by depth (preserve violin)", "value": "by_depth"},
                                            {"label": "Random", "value": "random"},
                                        ],
                                        value="by_depth",
                                        clearable=False,
                                    ),
                                    html.Label("Max points to render (0 = all)"),
                                    dcc.Input(
                                        id="pc-max-points",
                                        type="number",
                                        value=120000,
                                        min=0,
                                        max=2_000_000,
                                        step=1000,
                                    ),
                                    html.Br(),
                                    html.Label("Depth min"),
                                    dcc.Input(id="pc-depth-min", type="number", value=0, min=0, max=100000, step=1),
                                    html.Br(),
                                    html.Label("Depth max (0 = auto)"),
                                    dcc.Input(id="pc-depth-max", type="number", value=0, min=0, max=100000, step=1),
                                    html.Br(),
                                    html.Label("Point size"),
                                    dcc.Input(id="pc-point-size", type="number", value=2.0, min=0.1, max=20.0, step=0.1),
                                    html.Br(),
                                    html.Label("Opacity"),
                                    dcc.Slider(
                                        id="pc-opacity",
                                        min=0.05,
                                        max=1.0,
                                        step=0.05,
                                        value=0.85,
                                        marks=None,
                                        tooltip={"placement": "bottom", "always_visible": False},
                                    ),
                                    html.Label("Color points by"),
                                    dcc.Dropdown(
                                        id="pc-color-mode",
                                        options=[
                                            {"label": "Depth", "value": "depth"},
                                            {"label": "Subtree span (log10)", "value": "subtree_span"},
                                            {"label": "Local fanout / out-degree (log10)", "value": "out_degree"},
                                        ],
                                        value="depth",
                                        clearable=False,
                                    ),
                                    html.Hr(),
                                    html.H4("Edges (fan view)", style={"margin": "6px 0"}),
                                    dcc.Checklist(
                                        id="fan-show-edges",
                                        options=[{"label": "Show parent→child edges", "value": "on"}],
                                        value=["on"],
                                    ),
                                    html.Label("Max edges to draw (0 = all in depth range)"),
                                    dcc.Input(
                                        id="fan-max-edges",
                                        type="number",
                                        value=120000,
                                        min=0,
                                        max=2_000_000,
                                        step=1000,
                                    ),
                                    html.Br(),
                                    html.Label("Edge max depth (0 = follow point depth max)"),
                                    dcc.Input(
                                        id="fan-edge-depth-max",
                                        type="number",
                                        value=0,
                                        min=0,
                                        max=100000,
                                        step=1,
                                    ),
                                    html.Br(),
                                    dcc.Checklist(
                                        id="fan-bundle-edges",
                                        options=[{"label": "Bundle edges (river-like)", "value": "on"}],
                                        value=["on"],
                                    ),
                                    html.Label("Bundle pull (0-1)"),
                                    dcc.Slider(
                                        id="fan-bundle-pull",
                                        min=0.0,
                                        max=1.0,
                                        step=0.05,
                                        value=0.35,
                                        marks=None,
                                        tooltip={"placement": "bottom", "always_visible": False},
                                    ),
                                    html.Label("Edge opacity"),
                                    dcc.Slider(
                                        id="fan-edge-opacity",
                                        min=0.02,
                                        max=0.8,
                                        step=0.02,
                                        value=0.14,
                                        marks=None,
                                        tooltip={"placement": "bottom", "always_visible": False},
                                    ),
                                    html.Label("Edge width"),
                                    dcc.Input(id="fan-edge-width", type="number", value=1.0, min=0.1, max=5.0, step=0.1),
                                    html.Br(),
                                    html.Label("Fan angle span (degrees)"),
                                    dcc.Input(id="fan-angle-span", type="number", value=150, min=20, max=360, step=5),
                                    html.Br(),
                                    html.Label("Radius step (per depth)"),
                                    dcc.Input(id="fan-radius-step", type="number", value=1.0, min=0.05, max=10.0, step=0.05),
                                    html.Br(),
                                    html.Label("3D fan z-mode"),
                                    dcc.Dropdown(
                                        id="fan3d-z-mode",
                                        options=[
                                            {"label": "Depth cone (default)", "value": "depth_cone"},
                                            {"label": "Flat disc", "value": "flat"},
                                            {"label": "Parquet z (robust scaled)", "value": "parquet_z"},
                                            {"label": "Crystal (span lift)", "value": "crystal_span"},
                                            {"label": "Twist (helical)", "value": "twist"},
                                            {"label": "Watershed (bowl)", "value": "watershed_bowl"},
                                        ],
                                        value="depth_cone",
                                        clearable=False,
                                    ),
                                    html.Label("3D z-scale"),
                                    dcc.Slider(
                                        id="fan3d-z-scale",
                                        min=0.1,
                                        max=4.0,
                                        step=0.1,
                                        value=1.0,
                                        marks=None,
                                        tooltip={"placement": "bottom", "always_visible": False},
                                    ),
                                ],
                                id="dataset-controls",
                            ),
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
        ],
        style={"padding": 12},
    )

    @app.callback(
        Output("graph", "figure"),
        Output("status", "children"),
        Input("render-btn", "n_clicks"),
        State("view-mode", "value"),
        State("pc-path", "value"),
        State("pc-sampling", "value"),
        State("pc-max-points", "value"),
        State("pc-depth-min", "value"),
        State("pc-depth-max", "value"),
        State("pc-point-size", "value"),
        State("pc-opacity", "value"),
        State("pc-color-mode", "value"),
        State("fan-show-edges", "value"),
        State("fan-max-edges", "value"),
        State("fan-edge-depth-max", "value"),
        State("fan-bundle-edges", "value"),
        State("fan-bundle-pull", "value"),
        State("fan-edge-opacity", "value"),
        State("fan-edge-width", "value"),
        State("fan-angle-span", "value"),
        State("fan-radius-step", "value"),
        State("fan3d-z-mode", "value"),
        State("fan3d-z-scale", "value"),
        State("graph", "relayoutData"),
        prevent_initial_call=True,
    )
    def _render(
        _n_clicks,
        view_mode,
        pc_path,
        pc_sampling,
        pc_max_points,
        pc_depth_min,
        pc_depth_max,
        pc_point_size,
        pc_opacity,
        pc_color_mode,
        fan_show_edges,
        fan_max_edges,
        fan_edge_depth_max,
        fan_bundle_edges,
        fan_bundle_pull,
        fan_edge_opacity,
        fan_edge_width,
        fan_angle_span,
        fan_radius_step,
        fan3d_z_mode,
        fan3d_z_scale,
        relayout_data,
    ):
        t0 = time.time()

        camera = None
        if isinstance(relayout_data, dict) and "scene.camera" in relayout_data:
            camera = relayout_data.get("scene.camera")

        try:
            if not pc_path:
                return go.Figure(), "No pointcloud dataset selected (and none found under analysis/)."

            df = _load_pointcloud_df(str(pc_path))
            x2_arr, span_arr, outdeg_arr = _compute_tree_layout_cached(str(pc_path))
            x2 = pd.Series(x2_arr, index=df.index, name="x2")
            subtree_span = pd.Series(span_arr, index=df.index, name="span")
            out_degree = pd.Series(outdeg_arr, index=df.index, name="outdeg")

            mode = (view_mode or "pointcloud").strip()
            if mode == "recursive2d":
                fig = build_recursive_space_2d_figure_from_df(
                    df,
                    title=f"2D recursive space ({Path(str(pc_path)).name})",
                    max_points=int(pc_max_points or 0),
                    sampling_mode=str(pc_sampling or "by_depth"),
                    depth_min=int(pc_depth_min or 0),
                    depth_max=int(pc_depth_max or 0),
                    point_size=float(pc_point_size or 2.0),
                    opacity=float(pc_opacity or 0.85),
                    seed=0,
                    x2=x2,
                    subtree_span=subtree_span,
                    out_degree=out_degree,
                    color_mode=str(pc_color_mode or "depth"),
                )
            elif mode == "fan2d":
                fig = build_fan_edges_2d_figure_from_df(
                    df,
                    title=f"2D fan + edges ({Path(str(pc_path)).name})",
                    max_points=int(pc_max_points or 0),
                    sampling_mode=str(pc_sampling or "by_depth"),
                    depth_min=int(pc_depth_min or 0),
                    depth_max=int(pc_depth_max or 0),
                    point_size=float(pc_point_size or 2.0),
                    point_opacity=float(pc_opacity or 0.85),
                    seed=0,
                    show_edges=bool(fan_show_edges) and ("on" in (fan_show_edges or [])),
                    max_edges=int(fan_max_edges or 0),
                    edge_opacity=float(fan_edge_opacity or 0.14),
                    edge_width=float(fan_edge_width or 1.0),
                    angle_span_degrees=float(fan_angle_span or 150.0),
                    radius_step=float(fan_radius_step or 1.0),
                    edge_depth_max=int(fan_edge_depth_max or 0) or int(pc_depth_max or 0),
                    bundle_edges=bool(fan_bundle_edges) and ("on" in (fan_bundle_edges or [])),
                    bundle_pull=float(fan_bundle_pull or 0.35),
                    x2=x2,
                    subtree_span=subtree_span,
                    out_degree=out_degree,
                    color_mode=str(pc_color_mode or "depth"),
                )
            elif mode == "fan3d":
                fig = build_fan_edges_3d_figure_from_df(
                    df,
                    title=f"3D fan + edges ({Path(str(pc_path)).name})",
                    max_points=int(pc_max_points or 0),
                    sampling_mode=str(pc_sampling or "by_depth"),
                    depth_min=int(pc_depth_min or 0),
                    depth_max=int(pc_depth_max or 0),
                    point_size=float(pc_point_size or 2.0),
                    point_opacity=float(pc_opacity or 0.85),
                    seed=0,
                    show_edges=bool(fan_show_edges) and ("on" in (fan_show_edges or [])),
                    max_edges=int(fan_max_edges or 0),
                    edge_opacity=float(fan_edge_opacity or 0.14),
                    edge_width=float(fan_edge_width or 1.0),
                    angle_span_degrees=float(fan_angle_span or 150.0),
                    radius_step=float(fan_radius_step or 1.0),
                    edge_depth_max=int(fan_edge_depth_max or 0) or int(pc_depth_max or 0),
                    bundle_edges=bool(fan_bundle_edges) and ("on" in (fan_bundle_edges or [])),
                    bundle_pull=float(fan_bundle_pull or 0.35),
                    x2=x2,
                    subtree_span=subtree_span,
                    out_degree=out_degree,
                    color_mode=str(pc_color_mode or "depth"),
                    z_mode=str(fan3d_z_mode or "depth_cone"),
                    z_scale=float(fan3d_z_scale or 1.0),
                    camera=camera,
                )
            else:
                fig = build_pointcloud_figure_from_df(
                    df,
                    title=f"3D point cloud ({Path(str(pc_path)).name})",
                    max_points=int(pc_max_points or 0),
                    sampling_mode=str(pc_sampling or "by_depth"),
                    depth_min=int(pc_depth_min or 0),
                    depth_max=int(pc_depth_max or 0),
                    point_size=float(pc_point_size or 2.0),
                    opacity=float(pc_opacity or 0.85),
                    seed=0,
                    camera=camera,
                )

            meta = {"nodes": int(len(df)), "edges": 0}
        except Exception as e:
            return go.Figure(), f"Error: {e}"

        dt = time.time() - t0
        status = f"nodes={meta['nodes']:,} edges={meta['edges']:,}\nrender_time={dt:.2f}s"
        return fig, status

    print(f"Starting Dash on http://{args.host}:{args.port}  (Ctrl+C to stop)")
    app.run(host=args.host, port=args.port, debug=False)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
