#!/usr/bin/env python3
"""Generate interactive Sankey diagram of cross-basin tunneling flows.

This script creates a standalone HTML visualization showing how pages
flow between basins as N changes (N=4 -> N=5 -> N=6 transitions).

Output:
  - report/assets/tunneling_sankey.html

Data dependencies:
  - data/wikipedia/processed/multiplex/basin_flows.tsv
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import pandas as pd
import plotly.graph_objects as go

REPO_ROOT = Path(__file__).resolve().parents[3]
MULTIPLEX_DIR = REPO_ROOT / "data" / "wikipedia" / "processed" / "multiplex"
REPORT_DIR = REPO_ROOT / "n-link-analysis" / "report" / "assets"

# Basin color scheme (consistent across all visualizations)
BASIN_COLORS = {
    "Gulf_of_Maine__Massachusetts": "#1f77b4",
    "Sea_salt__Seawater": "#2ca02c",
    "Autumn__Summer": "#ff7f0e",
    "Hill__Mountain": "#8c564b",
    "Animal__Kingdom_(biology)": "#9467bd",
    "American_Revolutionary_War__Eastern_United_States": "#d62728",
    "Latvia__Lithuania": "#17becf",
    "Civil_law__Precedent": "#bcbd22",
    "Curing_(chemistry)__Thermosetting_polymer": "#e377c2",
}

# Short display names for basins
BASIN_SHORT_NAMES = {
    "Gulf_of_Maine__Massachusetts": "Gulf of Maine",
    "Sea_salt__Seawater": "Sea Salt",
    "Autumn__Summer": "Autumn",
    "Hill__Mountain": "Hill/Mountain",
    "Animal__Kingdom_(biology)": "Animal Kingdom",
    "American_Revolutionary_War__Eastern_United_States": "Am. Revolution",
    "Latvia__Lithuania": "Latvia/Lithuania",
    "Civil_law__Precedent": "Civil Law",
    "Curing_(chemistry)__Thermosetting_polymer": "Curing/Polymer",
}


def get_basin_color(basin: str) -> str:
    """Get color for a basin, with fallback."""
    for key, color in BASIN_COLORS.items():
        if key in basin or basin in key:
            return color
    return "#7f7f7f"  # gray fallback


def get_short_name(basin: str) -> str:
    """Get short display name for a basin."""
    for key, name in BASIN_SHORT_NAMES.items():
        if key in basin or basin in key:
            return name
    # Fallback: first part before __
    return basin.split("__")[0][:15]


def load_basin_flows(path: Path) -> pd.DataFrame:
    """Load basin flows data."""
    if not path.exists():
        raise FileNotFoundError(f"Basin flows file not found: {path}")
    return pd.read_csv(path, sep="\t")


def create_sankey_diagram(flows_df: pd.DataFrame) -> go.Figure:
    """Create Sankey diagram from basin flows data."""

    # Get unique N values and basins
    n_values = sorted(set(flows_df["from_n"].unique()) | set(flows_df["to_n"].unique()))
    all_basins = sorted(set(flows_df["from_basin"].unique()) | set(flows_df["to_basin"].unique()))

    # Create node list: each basin at each N value
    nodes = []
    node_indices = {}

    for n in n_values:
        for basin in all_basins:
            node_key = f"{basin}@N{n}"
            node_indices[node_key] = len(nodes)
            nodes.append({
                "label": f"{get_short_name(basin)} (N={n})",
                "color": get_basin_color(basin),
                "basin": basin,
                "n": n,
            })

    # Create links from flows
    sources = []
    targets = []
    values = []
    link_colors = []
    customdata = []

    for _, row in flows_df.iterrows():
        from_key = f"{row['from_basin']}@N{row['from_n']}"
        to_key = f"{row['to_basin']}@N{row['to_n']}"

        if from_key in node_indices and to_key in node_indices:
            sources.append(node_indices[from_key])
            targets.append(node_indices[to_key])
            values.append(row["count"])

            # Link color: slightly transparent version of source basin color
            base_color = get_basin_color(row["from_basin"])
            link_colors.append(base_color.replace("#", "rgba(") + ", 0.4)" if "#" in base_color else base_color)

            customdata.append({
                "from_basin": get_short_name(row["from_basin"]),
                "to_basin": get_short_name(row["to_basin"]),
                "from_n": row["from_n"],
                "to_n": row["to_n"],
                "count": row["count"],
            })

    # Convert link colors to proper RGBA format
    rgba_colors = []
    for color in link_colors:
        if color.startswith("rgba"):
            rgba_colors.append(color)
        else:
            # Convert hex to rgba
            hex_color = color.lstrip("#")
            r, g, b = tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))
            rgba_colors.append(f"rgba({r}, {g}, {b}, 0.5)")

    # Build figure
    fig = go.Figure(data=[go.Sankey(
        arrangement="snap",
        node=dict(
            pad=20,
            thickness=25,
            line=dict(color="black", width=0.5),
            label=[n["label"] for n in nodes],
            color=[n["color"] for n in nodes],
            hovertemplate="%{label}<extra></extra>",
        ),
        link=dict(
            source=sources,
            target=targets,
            value=values,
            color=rgba_colors,
            hovertemplate=(
                "<b>%{source.label}</b> → <b>%{target.label}</b><br>"
                "Pages: %{value:,}<extra></extra>"
            ),
        ),
    )])

    # Calculate total flow volume
    total_flow = sum(values)

    fig.update_layout(
        title=dict(
            text=(
                f"<b>Cross-Basin Tunneling Flows</b><br>"
                f"<span style='font-size:14px'>Total: {total_flow:,} page transitions across N values</span>"
            ),
            x=0.5,
            xanchor="center",
        ),
        font=dict(size=12, family="Arial"),
        height=700,
        margin=dict(l=20, r=20, t=80, b=20),
        paper_bgcolor="white",
    )

    return fig


def create_transition_summary(flows_df: pd.DataFrame) -> str:
    """Create HTML summary of transitions."""
    # Group by transition type
    by_transition = flows_df.groupby(["from_n", "to_n"])["count"].sum().reset_index()
    by_transition = by_transition.sort_values("count", ascending=False)

    rows = []
    for _, row in by_transition.iterrows():
        rows.append(f"<tr><td>N={row['from_n']} → N={row['to_n']}</td><td>{row['count']:,}</td></tr>")

    return f"""
    <div style="margin-top: 20px; padding: 15px; background: #f8f9fa; border-radius: 8px;">
        <h3 style="margin-top: 0;">Transition Summary</h3>
        <table style="border-collapse: collapse; width: auto;">
            <tr style="background: #e9ecef;"><th style="padding: 8px; text-align: left;">Transition</th><th style="padding: 8px; text-align: right;">Pages</th></tr>
            {''.join(rows)}
        </table>
    </div>
    """


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Generate Sankey diagram of cross-basin tunneling flows"
    )
    parser.add_argument(
        "--input",
        type=Path,
        default=MULTIPLEX_DIR / "basin_flows.tsv",
        help="Basin flows TSV file",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=REPORT_DIR / "tunneling_sankey.html",
        help="Output HTML file",
    )
    args = parser.parse_args()

    print("=" * 70)
    print("Generating Tunneling Sankey Diagram")
    print("=" * 70)
    print()

    # Load data
    print(f"Loading basin flows from {args.input}...")
    flows_df = load_basin_flows(args.input)
    print(f"  Found {len(flows_df)} cross-basin flows")
    print(f"  Total pages in flows: {flows_df['count'].sum():,}")
    print()

    # Create visualization
    print("Creating Sankey diagram...")
    fig = create_sankey_diagram(flows_df)

    # Create summary HTML
    summary_html = create_transition_summary(flows_df)

    # Write output
    args.output.parent.mkdir(parents=True, exist_ok=True)

    # Get plotly HTML
    plotly_html = fig.to_html(full_html=False, include_plotlyjs="cdn")

    # Wrap in full HTML with summary
    full_html = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <title>Tunneling Basin Flows - Sankey Diagram</title>
    <style>
        body {{
            font-family: Arial, sans-serif;
            margin: 20px;
            background: #ffffff;
        }}
        .container {{
            max-width: 1200px;
            margin: 0 auto;
        }}
        .header {{
            text-align: center;
            margin-bottom: 20px;
        }}
        .description {{
            background: #e7f3ff;
            padding: 15px;
            border-radius: 8px;
            margin-bottom: 20px;
        }}
        .legend {{
            display: flex;
            flex-wrap: wrap;
            gap: 10px;
            justify-content: center;
            margin: 20px 0;
        }}
        .legend-item {{
            display: flex;
            align-items: center;
            gap: 5px;
            font-size: 12px;
        }}
        .legend-color {{
            width: 16px;
            height: 16px;
            border-radius: 3px;
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>Cross-Basin Tunneling Flows</h1>
            <p>Wikipedia N-Link Rule Analysis</p>
        </div>

        <div class="description">
            <p><strong>What this shows:</strong> When the N-link rule changes (e.g., from N=5 to N=6),
            some Wikipedia pages switch from one basin to another. This Sankey diagram shows the
            volume of these transitions.</p>
            <p><strong>Key insight:</strong> At N=5→N=6, pages flow <em>into</em> Gulf of Maine from
            all other basins, making it a "sink" basin at higher N values.</p>
        </div>

        <div class="legend">
            {''.join(f'<div class="legend-item"><div class="legend-color" style="background: {color};"></div>{get_short_name(basin)}</div>' for basin, color in BASIN_COLORS.items())}
        </div>

        {plotly_html}

        {summary_html}
    </div>
</body>
</html>
"""

    with open(args.output, "w") as f:
        f.write(full_html)

    print(f"  Saved to {args.output}")
    print()
    print("=" * 70)
    print("DONE")
    print("=" * 70)


if __name__ == "__main__":
    main()
