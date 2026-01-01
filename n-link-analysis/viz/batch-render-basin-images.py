#!/usr/bin/env python3
"""Batch render basin geometry visualizations as static images.

This script automates generating basin point cloud visualizations and exporting
them as static PNG images for publication, reports, and presentations.

Run (repo root)
--------------
  # Render all N=5 cycles with default settings
  python n-link-analysis/viz/batch-render-basin-images.py --n 5 --all-cycles

  # Render specific cycles with custom parameters
  python n-link-analysis/viz/batch-render-basin-images.py \
    --n 5 --cycles Massachusetts Kingdom --max-plot-points 150000 --width 1920 --height 1080

  # Generate comparison grid
  python n-link-analysis/viz/batch-render-basin-images.py --n 5 --comparison-grid
"""

from __future__ import annotations

import argparse
import sys
import time
from pathlib import Path
from typing import Any

import pandas as pd
import plotly.graph_objects as go


REPO_ROOT = Path(__file__).resolve().parents[2]
PROCESSED_DIR = REPO_ROOT / "data" / "wikipedia" / "processed"
ANALYSIS_DIR = PROCESSED_DIR / "analysis"
REPORT_ASSETS_DIR = REPO_ROOT / "n-link-analysis" / "report" / "assets"

# Known N=5 terminal cycles from previous analysis
# Note: Pointcloud files use single cycle member names, not full pairs
N5_CYCLES = [
    "Massachusetts",
    "Kingdom_(biology)",
    "Autumn",
    "Sea_salt",
    "Mountain",
    "Latvia",
    "Precedent",
    "American_Revolutionary_War",
    "Thermosetting_polymer",
]


def load_basin_pointcloud(n: int, cycle_slug: str) -> pd.DataFrame | None:
    """Load existing basin pointcloud from parquet."""
    parquet_path = ANALYSIS_DIR / f"basin_pointcloud_n={n}_cycle={cycle_slug}.parquet"
    if not parquet_path.exists():
        return None
    return pd.read_parquet(parquet_path)


def create_basin_figure(
    df: pd.DataFrame,
    *,
    title: str,
    max_points: int = 120_000,
    seed: int = 0,
    colorscale: str = "Viridis",
    opacity: float = 0.85,
    show_axes: bool = False,
) -> go.Figure:
    """Create Plotly 3D scatter figure from basin pointcloud."""
    import numpy as np
    import random

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
                    colorscale=colorscale,
                    opacity=opacity,
                ),
                hoverinfo="skip",
            )
        ]
    )

    axis_visible = dict(visible=show_axes)
    fig.update_layout(
        title=dict(text=title, font=dict(size=20)),
        showlegend=False,
        margin=dict(l=0, r=0, t=60, b=0),
        scene=dict(
            xaxis=axis_visible,
            yaxis=axis_visible,
            zaxis=axis_visible,
        ),
    )
    return fig


def render_single_basin(
    n: int,
    cycle_slug: str,
    cycle_name: str,
    *,
    output_dir: Path,
    width: int = 1200,
    height: int = 800,
    format: str = "png",
    **fig_kwargs: Any,
) -> Path | None:
    """Render a single basin as a static image."""
    df = load_basin_pointcloud(n, cycle_slug)
    if df is None:
        print(f"  ⚠️  No pointcloud found for {cycle_slug} (run render-full-basin-geometry.py first)")
        return None

    print(f"  Rendering {cycle_name} ({len(df):,} nodes)...")
    fig = create_basin_figure(
        df,
        title=f"{cycle_name} Basin (N={n}, {len(df):,} nodes)",
        **fig_kwargs,
    )

    output_path = output_dir / f"basin_3d_n={n}_cycle={cycle_slug}.{format}"

    # Use kaleido for static export
    try:
        fig.write_image(str(output_path), width=width, height=height, scale=2)
        print(f"  ✓ Saved: {output_path.name} ({width}x{height})")
        return output_path
    except Exception as e:
        print(f"  ✗ Failed to render {cycle_slug}: {e}")
        return None


def create_comparison_grid(
    n: int,
    cycles: list[str],
    *,
    output_dir: Path,
    grid_cols: int = 3,
    width: int = 3600,
    height: int = 2400,
    format: str = "png",
) -> Path | None:
    """Create a grid comparison of multiple basins."""
    from plotly.subplots import make_subplots

    print(f"\nCreating comparison grid ({len(cycles)} basins)...")

    # Load all pointclouds
    data = []
    for cycle_slug in cycles:
        df = load_basin_pointcloud(n, cycle_slug)
        cycle_name = cycle_slug.replace("_", " ")
        if df is not None:
            data.append((cycle_name, df))
        else:
            print(f"  ⚠️  Skipping {cycle_name} (no data)")

    if not data:
        print("  ✗ No data to render")
        return None

    # Calculate grid dimensions
    n_plots = len(data)
    n_rows = (n_plots + grid_cols - 1) // grid_cols

    # Create subplots
    fig = make_subplots(
        rows=n_rows,
        cols=grid_cols,
        subplot_titles=[name for name, _ in data],
        specs=[[{"type": "scatter3d"}] * grid_cols for _ in range(n_rows)],
        horizontal_spacing=0.02,
        vertical_spacing=0.05,
    )

    import numpy as np
    import random

    max_points_per_plot = 40_000
    rng = random.Random(0)

    # Add each basin as a subplot
    for idx, (name, df) in enumerate(data):
        row = (idx // grid_cols) + 1
        col = (idx % grid_cols) + 1

        # Sample if too large
        if len(df) > max_points_per_plot:
            keep = rng.sample(range(len(df)), k=max_points_per_plot)
            df_plot = df.iloc[keep].copy()
        else:
            df_plot = df

        depth = df_plot["depth"].to_numpy(dtype=np.float32)
        size = 1.5 + 0.3 * np.log10(1.0 + depth)

        fig.add_trace(
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
                    showscale=(col == grid_cols),  # Only show scale on rightmost
                ),
                hoverinfo="skip",
                showlegend=False,
            ),
            row=row,
            col=col,
        )

        # Hide axes for cleaner look
        scene_name = "scene" if row == 1 and col == 1 else f"scene{idx + 1}"
        fig.update_layout({
            scene_name: dict(
                xaxis=dict(visible=False),
                yaxis=dict(visible=False),
                zaxis=dict(visible=False),
            )
        })

    fig.update_layout(
        title=dict(
            text=f"N={n} Basin Geometry Comparison ({len(data)} cycles)",
            font=dict(size=24),
            x=0.5,
            xanchor="center",
        ),
        showlegend=False,
        margin=dict(l=10, r=10, t=80, b=10),
    )

    output_path = output_dir / f"basin_comparison_grid_n={n}.{format}"

    try:
        fig.write_image(str(output_path), width=width, height=height, scale=2)
        print(f"  ✓ Saved: {output_path.name} ({width}x{height})")
        return output_path
    except Exception as e:
        print(f"  ✗ Failed to render grid: {e}")
        return None


def main() -> int:
    parser = argparse.ArgumentParser(description="Batch render basin geometry visualizations")
    parser.add_argument("--n", type=int, default=5, help="N-link rule value")
    parser.add_argument("--cycles", nargs="+", help="Specific cycle names to render")
    parser.add_argument("--all-cycles", action="store_true", help="Render all known N=5 cycles")
    parser.add_argument("--comparison-grid", action="store_true", help="Create comparison grid")

    parser.add_argument("--output-dir", type=Path, help="Output directory (default: report/assets)")
    parser.add_argument("--width", type=int, default=1200, help="Image width in pixels")
    parser.add_argument("--height", type=int, default=800, help="Image height in pixels")
    parser.add_argument("--format", default="png", choices=["png", "svg", "pdf"], help="Output format")

    parser.add_argument("--max-plot-points", type=int, default=120_000, help="Max points per plot")
    parser.add_argument("--colorscale", default="Viridis", help="Plotly colorscale")
    parser.add_argument("--opacity", type=float, default=0.85, help="Point opacity")
    parser.add_argument("--show-axes", action="store_true", help="Show 3D axes")
    parser.add_argument("--seed", type=int, default=0, help="Random seed for sampling")

    args = parser.parse_args()

    # Check for kaleido
    try:
        import kaleido  # noqa: F401
    except ImportError:
        print("Error: kaleido is required for static image export")
        print("Install with: pip install kaleido")
        return 1

    output_dir = args.output_dir or REPORT_ASSETS_DIR
    output_dir.mkdir(parents=True, exist_ok=True)

    fig_kwargs = {
        "max_points": args.max_plot_points,
        "seed": args.seed,
        "colorscale": args.colorscale,
        "opacity": args.opacity,
        "show_axes": args.show_axes,
    }

    # Determine which cycles to render
    if args.comparison_grid:
        # Create comparison grid
        create_comparison_grid(
            args.n,
            N5_CYCLES,
            output_dir=output_dir,
            width=args.width,
            height=args.height,
            format=args.format,
        )

    elif args.all_cycles or args.cycles:
        # Render individual basins
        if args.all_cycles:
            cycles_to_render = N5_CYCLES
        else:
            # Match user-specified cycle names
            cycles_to_render = []
            for name in args.cycles:
                matched = False
                for cycle_slug in N5_CYCLES:
                    if name.lower() in cycle_slug.lower():
                        cycles_to_render.append(cycle_slug)
                        matched = True
                        break
                if not matched:
                    print(f"Warning: No match found for '{name}'")

        print(f"\nRendering {len(cycles_to_render)} basin(s)...\n")

        rendered = []
        for cycle_slug in cycles_to_render:
            cycle_name = cycle_slug.replace("_", " ")

            path = render_single_basin(
                args.n,
                cycle_slug,
                cycle_name,
                output_dir=output_dir,
                width=args.width,
                height=args.height,
                format=args.format,
                **fig_kwargs,
            )
            if path:
                rendered.append(path)

        print(f"\n✓ Successfully rendered {len(rendered)}/{len(cycles_to_render)} basins")
        if rendered:
            print(f"  Output directory: {output_dir}")

    else:
        print("Error: Specify --all-cycles, --cycles <names>, or --comparison-grid")
        parser.print_help()
        return 1

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
