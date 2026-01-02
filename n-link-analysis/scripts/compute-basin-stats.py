#!/usr/bin/env python3
"""Compute basin / terminal statistics for fixed N-link rules.

For each N value (3-10), computes:
- Number of basins (distinct cycles)
- Total pages in basins
- Largest basin size
- Basin size distribution statistics

Outputs TSV files with per-N statistics.

Run (repo root):
  python n-link-analysis/scripts/compute-basin-stats.py
"""

from __future__ import annotations

import argparse
from pathlib import Path

import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots


REPO_ROOT = Path(__file__).resolve().parents[2]
MULTIPLEX_DIR = REPO_ROOT / "data" / "wikipedia" / "processed" / "multiplex"
ANALYSIS_DIR = REPO_ROOT / "data" / "wikipedia" / "processed" / "analysis"
REPORT_ASSETS_DIR = REPO_ROOT / "n-link-analysis" / "report" / "assets"


def load_basin_assignments() -> pd.DataFrame:
    """Load multiplex basin assignments."""
    path = MULTIPLEX_DIR / "multiplex_basin_assignments.parquet"
    if not path.exists():
        raise FileNotFoundError(f"Missing: {path}")
    return pd.read_parquet(path)


def save_figure(fig, output_dir: Path, name: str, width: int = 1000, height: int = 600) -> Path:
    """Save figure as HTML (and PNG if Chrome available)."""
    html_path = output_dir / f"{name}.html"
    fig.write_html(str(html_path))
    print(f"✓ Saved: {html_path.name}")

    try:
        png_path = output_dir / f"{name}.png"
        fig.write_image(str(png_path), width=width, height=height, scale=2)
        print(f"✓ Saved: {png_path.name}")
    except Exception:
        print(f"⚠️  PNG export failed: {name}.png")

    return html_path


def compute_stats_by_n(df: pd.DataFrame) -> pd.DataFrame:
    """Compute basin statistics for each N value."""
    # Filter out tunneling entries for main stats
    df_main = df[~df['cycle_key'].str.contains('_tunneling', na=False)]

    stats = []
    for n, group in df_main.groupby('N'):
        basin_sizes = group.groupby('cycle_key').size()

        stats.append({
            'N': n,
            'n_basins': len(basin_sizes),
            'total_pages': len(group),
            'largest_basin': basin_sizes.max(),
            'smallest_basin': basin_sizes.min(),
            'mean_basin_size': basin_sizes.mean(),
            'median_basin_size': basin_sizes.median(),
            'basin_size_std': basin_sizes.std(),
            'largest_basin_cycle': basin_sizes.idxmax(),
            'top_3_basins': ', '.join(basin_sizes.nlargest(3).index.tolist()),
        })

    result = pd.DataFrame(stats).sort_values('N')
    return result


def compute_per_n_basin_details(df: pd.DataFrame, n: int) -> pd.DataFrame:
    """Compute detailed basin stats for a specific N value."""
    df_n = df[(df['N'] == n) & (~df['cycle_key'].str.contains('_tunneling', na=False))]

    if df_n.empty:
        return pd.DataFrame()

    basin_sizes = df_n.groupby('cycle_key').size().reset_index(name='size')
    basin_sizes = basin_sizes.sort_values('size', ascending=False)

    # Add display name
    basin_sizes['display_name'] = basin_sizes['cycle_key'].str.replace('__', ' ↔ ').str.replace('_', ' ')

    # Add rank
    basin_sizes['rank'] = range(1, len(basin_sizes) + 1)

    # Add percentage
    total = basin_sizes['size'].sum()
    basin_sizes['pct_of_total'] = (basin_sizes['size'] / total * 100).round(2)

    return basin_sizes


def create_summary_chart(stats_df: pd.DataFrame, output_dir: Path) -> Path:
    """Create summary chart of basin stats across N."""
    fig = make_subplots(
        rows=2, cols=2,
        subplot_titles=[
            "Total Pages by N",
            "Number of Basins by N",
            "Largest Basin Size by N",
            "Mean Basin Size by N"
        ],
    )

    # 1. Total pages
    fig.add_trace(go.Bar(
        x=stats_df['N'],
        y=stats_df['total_pages'],
        marker_color='#1f77b4',
    ), row=1, col=1)

    # 2. Number of basins
    fig.add_trace(go.Bar(
        x=stats_df['N'],
        y=stats_df['n_basins'],
        marker_color='#ff7f0e',
    ), row=1, col=2)

    # 3. Largest basin
    fig.add_trace(go.Bar(
        x=stats_df['N'],
        y=stats_df['largest_basin'],
        marker_color='#2ca02c',
    ), row=2, col=1)

    # 4. Mean basin size
    fig.add_trace(go.Bar(
        x=stats_df['N'],
        y=stats_df['mean_basin_size'],
        marker_color='#d62728',
    ), row=2, col=2)

    fig.update_layout(
        title=dict(
            text="Basin Statistics Summary (N=3-10)",
            font=dict(size=18),
            x=0.5,
        ),
        template="plotly_white",
        width=1000,
        height=700,
        showlegend=False,
    )

    fig.update_xaxes(title="N", tickmode='linear', tick0=3, dtick=1)
    fig.update_yaxes(title="Pages", type='log', row=1, col=1)
    fig.update_yaxes(title="Count", row=1, col=2)
    fig.update_yaxes(title="Pages", type='log', row=2, col=1)
    fig.update_yaxes(title="Pages", type='log', row=2, col=2)

    return save_figure(fig, output_dir, "basin_stats_summary", width=1000, height=700)


def main() -> int:
    parser = argparse.ArgumentParser(description="Compute basin statistics per N value")
    parser.add_argument("--output-dir", type=Path, help="Output directory for TSV files")
    parser.add_argument("--viz-dir", type=Path, help="Output directory for visualization")
    args = parser.parse_args()

    output_dir = args.output_dir or ANALYSIS_DIR
    viz_dir = args.viz_dir or REPORT_ASSETS_DIR

    output_dir.mkdir(parents=True, exist_ok=True)
    viz_dir.mkdir(parents=True, exist_ok=True)

    print("\nComputing basin statistics...")

    try:
        df = load_basin_assignments()
        print(f"Loaded {len(df):,} basin assignments")
    except FileNotFoundError as e:
        print(f"Error: {e}")
        return 1

    # Compute summary stats
    stats_df = compute_stats_by_n(df)
    print(f"\nBasin statistics for N=3-10:")
    print(stats_df[['N', 'n_basins', 'total_pages', 'largest_basin']].to_string(index=False))

    # Save summary TSV
    summary_path = output_dir / "basin_stats_summary_n3_to_n10.tsv"
    stats_df.to_csv(summary_path, sep='\t', index=False)
    print(f"\n✓ Saved: {summary_path.name}")

    # Compute per-N details
    for n in range(3, 11):
        details = compute_per_n_basin_details(df, n)
        if not details.empty:
            details_path = output_dir / f"basin_stats_n={n}.tsv"
            details.to_csv(details_path, sep='\t', index=False)
            print(f"✓ Saved: basin_stats_n={n}.tsv ({len(details)} basins)")

    # Create visualization
    create_summary_chart(stats_df, viz_dir)

    print(f"\n✓ Basin statistics computation complete")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
