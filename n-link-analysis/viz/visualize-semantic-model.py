#!/usr/bin/env python3
"""Visualize the semantic model from tunneling analysis.

Creates visualizations of the semantic_model_wikipedia.json data:
1. Central entities bar chart - top tunnel nodes by tunnel_score
2. Subsystem stability comparison - basin stability classes
3. Hidden relationships flow diagram - cross-basin flows

Run (repo root):
  python n-link-analysis/viz/visualize-semantic-model.py --all
  python n-link-analysis/viz/visualize-semantic-model.py --central-entities
  python n-link-analysis/viz/visualize-semantic-model.py --stability
  python n-link-analysis/viz/visualize-semantic-model.py --flows
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import pandas as pd


REPO_ROOT = Path(__file__).resolve().parents[2]
MULTIPLEX_DIR = REPO_ROOT / "data" / "wikipedia" / "processed" / "multiplex"
REPORT_ASSETS_DIR = REPO_ROOT / "n-link-analysis" / "report" / "assets"

# Color palette for basins
BASIN_COLORS = {
    "Gulf_of_Maine__Massachusetts": "#1f77b4",
    "Sea_salt__Seawater": "#ff7f0e",
    "Hill__Mountain": "#2ca02c",
    "Autumn__Summer": "#d62728",
    "Animal__Kingdom_(biology)": "#9467bd",
    "Latvia__Lithuania": "#8c564b",
    "Civil_law__Precedent": "#e377c2",
    "American_Revolutionary_War__Eastern_United_States": "#7f7f7f",
    "Curing_(chemistry)__Thermosetting_polymer": "#bcbd22",
}

STABILITY_COLORS = {
    "stable": "#2ca02c",
    "moderate": "#ff7f0e",
    "fragile": "#d62728",
}


def load_semantic_model() -> dict:
    """Load the semantic model JSON."""
    path = MULTIPLEX_DIR / "semantic_model_wikipedia.json"
    if not path.exists():
        raise FileNotFoundError(f"Missing: {path}")
    with open(path) as f:
        return json.load(f)


def save_figure(fig, output_dir: Path, name: str, width: int = 1200, height: int = 600) -> Path:
    """Save figure as PNG (if possible) and HTML. Returns path to HTML."""
    html_path = output_dir / f"{name}.html"
    fig.write_html(str(html_path))
    print(f"✓ Saved: {html_path.name}")

    # Try PNG export (may fail if Chrome not installed)
    png_path = output_dir / f"{name}.png"
    try:
        fig.write_image(str(png_path), width=width, height=height, scale=2)
        print(f"✓ Saved: {png_path.name}")
    except Exception as e:
        print(f"⚠️  PNG export failed (Chrome not available): {png_path.name}")

    return html_path


def create_central_entities_chart(model: dict, output_dir: Path, top_n: int = 30) -> Path:
    """Create bar chart of top central entities by tunnel score."""
    entities = model.get("central_entities", [])[:top_n]

    if not entities:
        print("⚠️  No central entities in model")
        return None

    df = pd.DataFrame(entities)

    # Create color mapping based on primary basin
    df["primary_basin"] = df["basin_list"].str.split(", ").str[0]
    df["color"] = df["primary_basin"].map(BASIN_COLORS).fillna("#666666")

    # Create hover text
    df["hover"] = df.apply(
        lambda r: f"<b>{r['title'].replace('_', ' ')}</b><br>"
                  f"Tunnel Score: {r['tunnel_score']:.1f}<br>"
                  f"Basins Bridged: {r['basins_bridged']}<br>"
                  f"Type: {r['tunnel_type']}<br>"
                  f"Mean Depth: {r['mean_depth']:.1f}",
        axis=1
    )

    fig = go.Figure()

    # Add bars
    fig.add_trace(go.Bar(
        x=df["title"].str.replace("_", " "),
        y=df["tunnel_score"],
        marker_color=df["color"],
        hovertext=df["hover"],
        hoverinfo="text",
    ))

    fig.update_layout(
        title=dict(
            text=f"Top {top_n} Central Tunnel Entities by Tunnel Score",
            font=dict(size=18),
            x=0.5,
        ),
        xaxis=dict(
            title="",
            tickangle=45,
            tickfont=dict(size=9),
        ),
        yaxis=dict(
            title="Tunnel Score",
        ),
        template="plotly_white",
        width=1200,
        height=600,
        showlegend=False,
        margin=dict(b=150),
    )

    # Add annotation for top entity
    if len(df) > 0:
        top = df.iloc[0]
        fig.add_annotation(
            x=0, y=top["tunnel_score"] + 2,
            text=f"Top: {top['title'].replace('_', ' ')}<br>Score: {top['tunnel_score']:.1f}",
            showarrow=True,
            arrowhead=2,
            font=dict(size=10),
        )

    return save_figure(fig, output_dir, "semantic_model_central_entities")


def create_stability_comparison_chart(model: dict, output_dir: Path) -> Path:
    """Create subsystem stability comparison chart."""
    boundaries = model.get("subsystem_boundaries", [])

    if not boundaries:
        print("⚠️  No subsystem boundaries in model")
        return None

    df = pd.DataFrame(boundaries)

    # Sort by persistence score
    df = df.sort_values("persistence_score", ascending=False)

    # Create color based on stability class
    df["color"] = df["stability_class"].map(STABILITY_COLORS).fillna("#666666")

    fig = make_subplots(
        rows=1, cols=2,
        subplot_titles=["Basin Stability by Persistence Score", "Total Pages"],
        column_widths=[0.6, 0.4],
    )

    # Clean up basin names for display
    df["display_name"] = df["basin_id"].str.replace("__", " ↔ ").str.replace("_", " ")

    # Left: Persistence score with stability coloring
    fig.add_trace(go.Bar(
        x=df["display_name"],
        y=df["persistence_score"],
        marker_color=df["color"],
        name="Persistence Score",
        hovertemplate="<b>%{x}</b><br>Persistence: %{y:.2f}<br>Jaccard: %{customdata:.3f}<extra></extra>",
        customdata=df["mean_jaccard"],
    ), row=1, col=1)

    # Right: Total pages in basin
    fig.add_trace(go.Bar(
        x=df["display_name"],
        y=df["total_pages"],
        marker_color="#1f77b4",
        name="Total Pages",
        showlegend=False,
    ), row=1, col=2)

    fig.update_layout(
        title=dict(
            text="Basin Stability Analysis<br><sub>Green=Stable, Orange=Moderate, Red=Fragile</sub>",
            font=dict(size=18),
            x=0.5,
        ),
        template="plotly_white",
        width=1200,
        height=500,
        showlegend=False,
    )

    fig.update_xaxes(tickangle=45, tickfont=dict(size=9))
    fig.update_yaxes(title="Persistence Score", row=1, col=1)
    fig.update_yaxes(title="Pages", type="log", row=1, col=2)

    return save_figure(fig, output_dir, "subsystem_stability_comparison", width=1200, height=500)


def create_hidden_relationships_flow(model: dict, output_dir: Path) -> Path:
    """Create Sankey diagram of hidden relationships (cross-basin flows)."""
    relationships = model.get("hidden_relationships", [])

    if not relationships:
        print("⚠️  No hidden relationships in model")
        return None

    # Extract flows from relationships
    flows = [r for r in relationships if r.get("type") == "cross_basin_flow"]

    if not flows:
        # Try to extract from alternating_tunnel entries
        alt_tunnels = [r for r in relationships if r.get("type") == "alternating_tunnel"]
        if alt_tunnels:
            # Create flow summary from alternating tunnels
            flow_counts = {}
            for tunnel in alt_tunnels:
                basins = tunnel.get("basins", [])
                if len(basins) >= 2:
                    key = tuple(sorted([basins[0], basins[1]]))
                    flow_counts[key] = flow_counts.get(key, 0) + 1

            # Convert to flow format
            flows = [
                {"from_basin": k[0], "to_basin": k[1], "volume": v}
                for k, v in flow_counts.items()
            ]

    if not flows:
        print("⚠️  No flow data found in relationships")
        return None

    # Build Sankey data
    basins = set()
    for flow in flows:
        basins.add(flow.get("from_basin", flow.get("basins", [""])[0]))
        basins.add(flow.get("to_basin", flow.get("basins", [""])[-1] if len(flow.get("basins", [])) > 1 else ""))
    basins = sorted([b for b in basins if b])

    basin_to_idx = {b: i for i, b in enumerate(basins)}

    sources = []
    targets = []
    values = []

    for flow in flows:
        from_b = flow.get("from_basin", flow.get("basins", [""])[0])
        to_b = flow.get("to_basin", flow.get("basins", [""])[-1] if len(flow.get("basins", [])) > 1 else "")
        vol = flow.get("volume", flow.get("count", 1))

        if from_b in basin_to_idx and to_b in basin_to_idx:
            sources.append(basin_to_idx[from_b])
            targets.append(basin_to_idx[to_b])
            values.append(vol)

    # Clean basin names for display
    labels = [b.replace("__", " ↔ ").replace("_", " ") for b in basins]
    colors = [BASIN_COLORS.get(b, "#666666") for b in basins]

    fig = go.Figure(go.Sankey(
        node=dict(
            pad=15,
            thickness=20,
            line=dict(color="black", width=0.5),
            label=labels,
            color=colors,
        ),
        link=dict(
            source=sources,
            target=targets,
            value=values,
            color="rgba(128, 128, 128, 0.3)",
        ),
    ))

    fig.update_layout(
        title=dict(
            text="Cross-Basin Flow Relationships<br><sub>Hidden semantic connections revealed by tunneling</sub>",
            font=dict(size=18),
            x=0.5,
        ),
        width=1000,
        height=600,
    )

    return save_figure(fig, output_dir, "hidden_relationships_flow", width=1000, height=600)


def create_tunnel_type_breakdown(model: dict, output_dir: Path) -> Path:
    """Create pie chart of tunnel types (alternating vs progressive)."""
    entities = model.get("central_entities", [])

    if not entities:
        print("⚠️  No central entities in model")
        return None

    df = pd.DataFrame(entities)
    type_counts = df["tunnel_type"].value_counts()

    fig = go.Figure(go.Pie(
        labels=type_counts.index,
        values=type_counts.values,
        hole=0.4,
        marker=dict(colors=["#1f77b4", "#ff7f0e"]),
        textinfo="label+percent",
        textposition="outside",
    ))

    fig.update_layout(
        title=dict(
            text="Tunnel Type Distribution<br><sub>Alternating: switches back and forth | Progressive: one-way transition</sub>",
            font=dict(size=16),
            x=0.5,
        ),
        width=600,
        height=500,
        showlegend=False,
    )

    # Add center annotation with total
    fig.add_annotation(
        text=f"<b>{len(entities)}</b><br>entities",
        x=0.5, y=0.5,
        font=dict(size=16),
        showarrow=False,
    )

    return save_figure(fig, output_dir, "tunnel_type_breakdown", width=600, height=500)


def create_depth_vs_score_scatter(model: dict, output_dir: Path) -> Path:
    """Create scatter plot of mean depth vs tunnel score."""
    entities = model.get("central_entities", [])

    if not entities:
        print("⚠️  No central entities in model")
        return None

    df = pd.DataFrame(entities)

    fig = px.scatter(
        df,
        x="mean_depth",
        y="tunnel_score",
        color="tunnel_type",
        size="basins_bridged",
        hover_name="title",
        hover_data=["basins_bridged", "transitions"],
        color_discrete_map={"alternating": "#1f77b4", "progressive": "#ff7f0e"},
    )

    fig.update_layout(
        title=dict(
            text="Tunnel Score vs Mean Depth<br><sub>Size = number of basins bridged</sub>",
            font=dict(size=16),
            x=0.5,
        ),
        xaxis=dict(title="Mean Depth"),
        yaxis=dict(title="Tunnel Score"),
        template="plotly_white",
        width=800,
        height=600,
    )

    return save_figure(fig, output_dir, "depth_vs_tunnel_score", width=800, height=600)


def print_summary(model: dict) -> None:
    """Print summary of semantic model."""
    summary = model.get("summary", {})
    metadata = model.get("metadata", {})

    print("\n" + "="*60)
    print("SEMANTIC MODEL SUMMARY")
    print("="*60)
    print(f"Source: {metadata.get('source', 'Unknown')}")
    print(f"N Range: {metadata.get('n_range', 'Unknown')}")
    print(f"Generated: {metadata.get('generated_at', 'Unknown')}")
    print()
    print(f"Total pages in hyperstructure: {summary.get('total_pages_in_hyperstructure', 0):,}")
    print(f"Tunnel nodes: {summary.get('tunnel_nodes', 0):,} ({summary.get('tunnel_percentage', 0):.2f}%)")
    print(f"Basins: {summary.get('n_basins', 0)} (stable: {summary.get('stable_basins', 0)}, "
          f"moderate: {summary.get('moderate_basins', 0)}, fragile: {summary.get('fragile_basins', 0)})")
    print(f"Cross-basin flows: {summary.get('cross_basin_flows', 0)}")
    print(f"Mean tunnel score: {summary.get('mean_tunnel_score', 0):.2f}")
    print(f"Max tunnel score: {summary.get('max_tunnel_score', 0):.2f}")
    print("="*60 + "\n")


def main() -> int:
    parser = argparse.ArgumentParser(description="Visualize semantic model from tunneling analysis")
    parser.add_argument("--all", action="store_true", help="Generate all visualizations")
    parser.add_argument("--central-entities", action="store_true", help="Central entities bar chart")
    parser.add_argument("--stability", action="store_true", help="Stability comparison chart")
    parser.add_argument("--flows", action="store_true", help="Hidden relationships flow diagram")
    parser.add_argument("--types", action="store_true", help="Tunnel type breakdown")
    parser.add_argument("--scatter", action="store_true", help="Depth vs score scatter")
    parser.add_argument("--output-dir", type=Path, help="Output directory")
    parser.add_argument("--top-n", type=int, default=30, help="Number of top entities to show")

    args = parser.parse_args()

    output_dir = args.output_dir or REPORT_ASSETS_DIR
    output_dir.mkdir(parents=True, exist_ok=True)

    # If no specific flags, default to --all
    if not any([args.central_entities, args.stability, args.flows, args.types, args.scatter]):
        args.all = True

    print(f"\nVisualizing semantic model...")
    print(f"Output: {output_dir}\n")

    # Load model
    model = load_semantic_model()
    print_summary(model)

    generated = []

    if args.all or args.central_entities:
        path = create_central_entities_chart(model, output_dir, top_n=args.top_n)
        if path:
            generated.append(path)

    if args.all or args.stability:
        path = create_stability_comparison_chart(model, output_dir)
        if path:
            generated.append(path)

    if args.all or args.flows:
        path = create_hidden_relationships_flow(model, output_dir)
        if path:
            generated.append(path)

    if args.all or args.types:
        path = create_tunnel_type_breakdown(model, output_dir)
        if path:
            generated.append(path)

    if args.all or args.scatter:
        path = create_depth_vs_score_scatter(model, output_dir)
        if path:
            generated.append(path)

    print(f"\n✓ Generated {len(generated)} visualizations")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
