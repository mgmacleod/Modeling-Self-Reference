#!/usr/bin/env python3
"""Aggregate terminals across N to identify universal attractors.

A universal attractor is a cycle that appears across multiple N values.
This script:
- Reads multiplex basin assignments
- Identifies cycles that appear at multiple N values
- Ranks them by persistence and page count
- Outputs a TSV with universal attractor statistics

Run (repo root):
  python n-link-analysis/scripts/compute-universal-attractors.py
"""

from __future__ import annotations

import argparse
from pathlib import Path

import pandas as pd
import plotly.graph_objects as go


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


def compute_universal_attractors(df: pd.DataFrame) -> pd.DataFrame:
    """Compute universal attractor statistics from basin assignments."""
    # Normalize cycle keys (remove _tunneling suffix)
    df = df.copy()
    df['base_cycle'] = df['cycle_key'].str.replace('_tunneling', '')

    # For each base_cycle, compute:
    # - Number of N values it appears at
    # - Total pages across all N
    # - Pages at each N
    stats = []
    for cycle, group in df.groupby('base_cycle'):
        n_values = group['N'].unique()
        n_count = len(n_values)
        total_pages = len(group)

        # Pages at each N
        pages_by_n = group.groupby('N').size().to_dict()

        # Max and min sizes
        max_size = max(pages_by_n.values())
        min_size = min(pages_by_n.values())
        size_variation = max_size / max(min_size, 1)

        # N range
        n_min = min(n_values)
        n_max = max(n_values)

        stats.append({
            'cycle': cycle,
            'display_name': cycle.replace('__', ' ↔ ').replace('_', ' '),
            'n_values_count': n_count,
            'n_range': f"{n_min}-{n_max}",
            'total_pages': total_pages,
            'max_size': max_size,
            'min_size': min_size,
            'size_variation': size_variation,
            'is_universal': n_count >= 8,  # Appears at all N=3-10
            **{f'pages_n{n}': pages_by_n.get(n, 0) for n in range(3, 11)},
        })

    result = pd.DataFrame(stats)
    result = result.sort_values(['n_values_count', 'total_pages'], ascending=[False, False])
    return result


def create_universal_attractors_chart(df: pd.DataFrame, output_dir: Path) -> Path:
    """Create visualization of universal attractors."""
    # Filter to attractors present at 3+ N values
    df_filtered = df[df['n_values_count'] >= 3].head(15)

    if df_filtered.empty:
        print("⚠️  No attractors with 3+ N values found")
        return None

    fig = go.Figure()

    # Add bars colored by universality
    colors = ['#2ca02c' if u else '#ff7f0e' for u in df_filtered['is_universal']]

    fig.add_trace(go.Bar(
        x=df_filtered['display_name'],
        y=df_filtered['total_pages'],
        marker_color=colors,
        hovertemplate="<b>%{x}</b><br>Total Pages: %{y:,}<br>N Values: %{customdata[0]}<br>Range: %{customdata[1]}<extra></extra>",
        customdata=list(zip(df_filtered['n_values_count'], df_filtered['n_range'])),
    ))

    fig.update_layout(
        title=dict(
            text="Universal Attractors by Total Page Count<br><sub>Green = Universal (all N values), Orange = Partial</sub>",
            font=dict(size=18),
            x=0.5,
        ),
        xaxis=dict(
            title="",
            tickangle=45,
            tickfont=dict(size=9),
        ),
        yaxis=dict(
            title="Total Pages (all N combined)",
            type='log',
        ),
        template="plotly_white",
        width=1000,
        height=600,
        margin=dict(b=150),
    )

    return save_figure(fig, output_dir, "universal_attractors_chart")


def main() -> int:
    parser = argparse.ArgumentParser(description="Compute universal attractor statistics")
    parser.add_argument("--output-dir", type=Path, help="Output directory for TSV")
    parser.add_argument("--viz-dir", type=Path, help="Output directory for visualization")
    args = parser.parse_args()

    output_dir = args.output_dir or ANALYSIS_DIR
    viz_dir = args.viz_dir or REPORT_ASSETS_DIR

    output_dir.mkdir(parents=True, exist_ok=True)
    viz_dir.mkdir(parents=True, exist_ok=True)

    print("\nComputing universal attractors...")

    try:
        df = load_basin_assignments()
        print(f"Loaded {len(df):,} basin assignments")
    except FileNotFoundError as e:
        print(f"Error: {e}")
        return 1

    # Compute statistics
    attractors = compute_universal_attractors(df)
    print(f"Found {len(attractors)} distinct attractors")
    print(f"  - Universal (all N): {attractors['is_universal'].sum()}")
    print(f"  - Partial (some N): {(~attractors['is_universal']).sum()}")

    # Save TSV
    tsv_path = output_dir / "universal_attractors_n3_to_n10.tsv"
    attractors.to_csv(tsv_path, sep='\t', index=False)
    print(f"✓ Saved: {tsv_path.name}")

    # Create visualization
    create_universal_attractors_chart(attractors, viz_dir)

    # Print top attractors
    print("\nTop 10 Universal Attractors:")
    print("-" * 60)
    for _, row in attractors.head(10).iterrows():
        universal = "✓" if row['is_universal'] else " "
        print(f"[{universal}] {row['display_name']}")
        print(f"    N values: {row['n_values_count']} ({row['n_range']})")
        print(f"    Total pages: {row['total_pages']:,}")
        print(f"    Size variation: {row['size_variation']:.0f}×")

    print(f"\n✓ Universal attractor analysis complete")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
