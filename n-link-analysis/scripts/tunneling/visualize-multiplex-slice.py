#!/usr/bin/env python3
"""Visualize multiplex graph structure.

This script creates interactive 3D visualizations of the multiplex graph:
- Basins as horizontal layers (one per N)
- Within-N edges as layer-internal connections
- Tunneling edges as cross-layer vertical lines
- Color by cycle membership

Output:
- multiplex_visualization.html: Interactive 3D Plotly visualization
- multiplex_layer_summary.png: Static layer connectivity heatmap

Data dependencies:
  - data/wikipedia/processed/multiplex/multiplex_edges.parquet
  - data/wikipedia/processed/multiplex/tunnel_classification.tsv
  - data/wikipedia/processed/multiplex/multiplex_layer_connectivity.tsv
"""

from __future__ import annotations

import argparse
from pathlib import Path

import pandas as pd
import numpy as np

REPO_ROOT = Path(__file__).resolve().parents[3]
PROCESSED_DIR = REPO_ROOT / "data" / "wikipedia" / "processed"
MULTIPLEX_DIR = PROCESSED_DIR / "multiplex"
REPORT_DIR = REPO_ROOT / "n-link-analysis" / "report" / "assets"


def create_layer_heatmap(connectivity_path: Path, output_path: Path) -> None:
    """Create a heatmap of layer-to-layer connectivity."""
    import matplotlib.pyplot as plt

    print(f"Creating layer connectivity heatmap...")

    df = pd.read_csv(connectivity_path, sep="\t")

    # Pivot to matrix form
    n_values = sorted(df["src_N"].unique())
    matrix = np.zeros((len(n_values), len(n_values)))

    for _, row in df.iterrows():
        i = n_values.index(row["src_N"])
        j = n_values.index(row["dst_N"])
        matrix[i, j] = row["edge_count"]

    # Log scale for better visibility
    log_matrix = np.log10(matrix + 1)

    fig, ax = plt.subplots(figsize=(10, 8))

    im = ax.imshow(log_matrix, cmap="YlOrRd", aspect="equal")

    # Labels
    ax.set_xticks(range(len(n_values)))
    ax.set_yticks(range(len(n_values)))
    ax.set_xticklabels([f"N={n}" for n in n_values])
    ax.set_yticklabels([f"N={n}" for n in n_values])

    ax.set_xlabel("Destination N", fontsize=12)
    ax.set_ylabel("Source N", fontsize=12)
    ax.set_title("Multiplex Layer Connectivity\n(log10 edge count)", fontsize=14)

    # Add text annotations
    for i in range(len(n_values)):
        for j in range(len(n_values)):
            count = int(matrix[i, j])
            if count > 0:
                text_color = "white" if log_matrix[i, j] > log_matrix.max() * 0.6 else "black"
                ax.text(j, i, f"{count:,}", ha="center", va="center",
                        fontsize=8, color=text_color)

    # Colorbar
    cbar = plt.colorbar(im, ax=ax, shrink=0.8)
    cbar.set_label("log10(edge count + 1)", fontsize=10)

    plt.tight_layout()
    plt.savefig(output_path, dpi=150, bbox_inches="tight")
    plt.close()

    print(f"  Saved to {output_path}")


def create_3d_visualization(
    edges_path: Path,
    tunnel_class_path: Path,
    output_path: Path,
    sample_size: int = 5000,
) -> None:
    """Create interactive 3D Plotly visualization of multiplex structure."""
    try:
        import plotly.graph_objects as go
    except ImportError:
        print("  Plotly not installed, skipping 3D visualization")
        return

    print(f"Creating 3D multiplex visualization...")

    # Load edges
    edges_df = pd.read_parquet(edges_path)

    # Sample edges for visualization
    if len(edges_df) > sample_size:
        edges_df = edges_df.sample(n=sample_size, random_state=42)

    # Separate edge types
    within_n = edges_df[edges_df["edge_type"] == "within_N"]
    tunnel = edges_df[edges_df["edge_type"] == "tunnel"]

    # Create node positions
    # X, Y: random positions within layer
    # Z: N value (layer height)
    np.random.seed(42)

    node_positions = {}

    for _, row in edges_df.iterrows():
        for node in [(row["src_page_id"], row["src_N"]), (row["dst_page_id"], row["dst_N"])]:
            if node not in node_positions:
                node_positions[node] = (
                    np.random.uniform(-10, 10),
                    np.random.uniform(-10, 10),
                    node[1],  # Z = N value
                )

    # Create figure
    fig = go.Figure()

    # Add within-N edges (horizontal, within layers)
    for _, row in within_n.iterrows():
        src = (row["src_page_id"], row["src_N"])
        dst = (row["dst_page_id"], row["dst_N"])

        if src in node_positions and dst in node_positions:
            src_pos = node_positions[src]
            dst_pos = node_positions[dst]

            fig.add_trace(go.Scatter3d(
                x=[src_pos[0], dst_pos[0]],
                y=[src_pos[1], dst_pos[1]],
                z=[src_pos[2], dst_pos[2]],
                mode="lines",
                line=dict(color="lightblue", width=1),
                opacity=0.3,
                showlegend=False,
                hoverinfo="skip",
            ))

    # Add tunnel edges (vertical, between layers)
    for _, row in tunnel.iterrows():
        src = (row["src_page_id"], row["src_N"])
        dst = (row["dst_page_id"], row["dst_N"])

        if src in node_positions and dst in node_positions:
            src_pos = node_positions[src]
            dst_pos = node_positions[dst]

            fig.add_trace(go.Scatter3d(
                x=[src_pos[0], dst_pos[0]],
                y=[src_pos[1], dst_pos[1]],
                z=[src_pos[2], dst_pos[2]],
                mode="lines",
                line=dict(color="red", width=3),
                opacity=0.8,
                showlegend=False,
                hoverinfo="skip",
            ))

    # Add nodes by layer
    n_values = sorted(set(n for _, n in node_positions.keys()))
    colors = ["#1f77b4", "#ff7f0e", "#2ca02c", "#d62728", "#9467bd", "#8c564b", "#e377c2"]

    for i, n in enumerate(n_values):
        layer_nodes = [(page, pos) for (page, layer), pos in node_positions.items() if layer == n]
        if layer_nodes:
            x = [pos[0] for _, pos in layer_nodes]
            y = [pos[1] for _, pos in layer_nodes]
            z = [pos[2] for _, pos in layer_nodes]

            fig.add_trace(go.Scatter3d(
                x=x, y=y, z=z,
                mode="markers",
                marker=dict(
                    size=3,
                    color=colors[i % len(colors)],
                    opacity=0.6,
                ),
                name=f"N={n}",
                hovertemplate=f"N={n}<br>Page: %{{customdata}}<extra></extra>",
                customdata=[page for page, _ in layer_nodes],
            ))

    # Layout
    fig.update_layout(
        title="Multiplex Graph: Cross-N Basin Connectivity",
        scene=dict(
            xaxis_title="X (layout)",
            yaxis_title="Y (layout)",
            zaxis_title="N value (layer)",
            camera=dict(
                eye=dict(x=1.5, y=1.5, z=1.0),
            ),
        ),
        legend=dict(
            yanchor="top",
            y=0.99,
            xanchor="left",
            x=0.01,
        ),
        margin=dict(l=0, r=0, b=0, t=40),
    )

    # Save as HTML
    fig.write_html(output_path)
    print(f"  Saved to {output_path}")


def create_tunnel_summary_chart(
    tunnel_class_path: Path,
    output_path: Path,
) -> None:
    """Create summary chart of tunnel node types."""
    import matplotlib.pyplot as plt

    print(f"Creating tunnel summary chart...")

    df = pd.read_csv(tunnel_class_path, sep="\t")

    fig, axes = plt.subplots(1, 3, figsize=(15, 5))

    # 1. Tunnel type distribution
    ax = axes[0]
    type_counts = df["tunnel_type"].value_counts()
    ax.bar(type_counts.index, type_counts.values, color=["steelblue", "coral"])
    ax.set_xlabel("Tunnel Type")
    ax.set_ylabel("Count")
    ax.set_title("Tunnel Node Types")
    for i, (type_name, count) in enumerate(type_counts.items()):
        ax.text(i, count + 50, f"{count:,}", ha="center", fontsize=10)

    # 2. N-coverage distribution
    ax = axes[1]
    coverage_counts = df["n_coverage"].value_counts().sort_index()
    ax.bar(coverage_counts.index, coverage_counts.values, color="steelblue")
    ax.set_xlabel("Number of N Values")
    ax.set_ylabel("Count")
    ax.set_title("N-Value Coverage per Tunnel Node")
    for i, (n_cov, count) in enumerate(coverage_counts.items()):
        ax.text(n_cov, count + 50, f"{count:,}", ha="center", fontsize=10)

    # 3. Basin pair distribution (top 10)
    ax = axes[2]
    df["basin_pair"] = df["primary_basin"].str[:15] + " / " + df["secondary_basin"].str[:15]
    pair_counts = df["basin_pair"].value_counts().head(10)
    ax.barh(range(len(pair_counts)), pair_counts.values, color="steelblue")
    ax.set_yticks(range(len(pair_counts)))
    ax.set_yticklabels(pair_counts.index, fontsize=8)
    ax.set_xlabel("Count")
    ax.set_title("Top 10 Basin Pairs")
    ax.invert_yaxis()

    plt.tight_layout()
    plt.savefig(output_path, dpi=150, bbox_inches="tight")
    plt.close()

    print(f"  Saved to {output_path}")


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Visualize multiplex graph structure"
    )
    parser.add_argument(
        "--edges",
        type=Path,
        default=MULTIPLEX_DIR / "multiplex_edges.parquet",
        help="Multiplex edges parquet",
    )
    parser.add_argument(
        "--tunnel-class",
        type=Path,
        default=MULTIPLEX_DIR / "tunnel_classification.tsv",
        help="Tunnel classification TSV",
    )
    parser.add_argument(
        "--layer-connectivity",
        type=Path,
        default=MULTIPLEX_DIR / "multiplex_layer_connectivity.tsv",
        help="Layer connectivity TSV",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=REPORT_DIR,
        help="Output directory for visualizations",
    )
    parser.add_argument(
        "--sample-size",
        type=int,
        default=5000,
        help="Sample size for 3D visualization (default: 5000)",
    )
    args = parser.parse_args()

    print("=" * 70)
    print("Visualizing Multiplex Structure")
    print("=" * 70)
    print()

    args.output_dir.mkdir(parents=True, exist_ok=True)

    # 1. Layer connectivity heatmap
    if args.layer_connectivity.exists():
        heatmap_path = args.output_dir / "multiplex_layer_connectivity.png"
        create_layer_heatmap(args.layer_connectivity, heatmap_path)
        print()

    # 2. 3D visualization
    if args.edges.exists():
        viz_path = args.output_dir / "multiplex_visualization.html"
        create_3d_visualization(
            args.edges, args.tunnel_class, viz_path, sample_size=args.sample_size
        )
        print()

    # 3. Tunnel summary chart
    if args.tunnel_class.exists():
        tunnel_chart_path = args.output_dir / "tunnel_summary_chart.png"
        create_tunnel_summary_chart(args.tunnel_class, tunnel_chart_path)
        print()

    print("=" * 70)
    print("DONE")
    print("=" * 70)


if __name__ == "__main__":
    main()
