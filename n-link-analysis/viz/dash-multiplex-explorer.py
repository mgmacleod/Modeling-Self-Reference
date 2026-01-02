#!/usr/bin/env python3
"""Interactive Multiplex Tunnel Explorer.

A human-facing visualization workbench for exploring cross-N basin connectivity,
tunnel nodes, and the multiplex graph structure from Phase 2-3 tunneling analysis.

Tabs
----
1) Layer Connectivity Matrix
   - Interactive heatmap of N×N edge counts
   - Click cells to see edge details
   - Toggle log/linear scale

2) Tunnel Node Explorer
   - Searchable/sortable table of tunnel nodes
   - Filter by tunnel type (progressive/alternating)
   - Filter by basin pair
   - Score-based ranking

3) Basin Pair Network
   - Network visualization of which basins connect via tunneling
   - Node size = basin mass, edge width = tunnel count
   - Hover for statistics

4) Cycle Reachability
   - Per-cycle BFS reachability across N layers
   - Stacked bar chart showing N-distribution of reachable nodes
   - Compare cycles side-by-side

Run (repo root)
---------------
  python n-link-analysis/viz/dash-multiplex-explorer.py --port 8056

Data Dependencies
-----------------
  - data/wikipedia/processed/multiplex/multiplex_layer_connectivity.tsv
  - data/wikipedia/processed/multiplex/tunnel_classification.tsv
  - data/wikipedia/processed/multiplex/tunnel_frequency_ranking.tsv
  - data/wikipedia/processed/multiplex/multiplex_reachability_summary.tsv
  - data/wikipedia/processed/multiplex/basin_intersection_by_cycle.tsv
"""

from __future__ import annotations

import argparse
from pathlib import Path

import dash
from dash import dcc, html, Input, Output, State, dash_table, callback
import dash_bootstrap_components as dbc
import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots


# ============================================================================
# Paths and Data Loading
# ============================================================================

REPO_ROOT = Path(__file__).resolve().parents[2]
MULTIPLEX_DIR = REPO_ROOT / "data" / "wikipedia" / "processed" / "multiplex"


def load_layer_connectivity() -> pd.DataFrame:
    """Load the N×N layer connectivity matrix."""
    path = MULTIPLEX_DIR / "multiplex_layer_connectivity.tsv"
    if not path.exists():
        return pd.DataFrame()
    return pd.read_csv(path, sep="\t")


def load_tunnel_classification() -> pd.DataFrame:
    """Load tunnel node classification data."""
    path = MULTIPLEX_DIR / "tunnel_classification.tsv"
    if not path.exists():
        return pd.DataFrame()
    df = pd.read_csv(path, sep="\t")
    return df


def load_tunnel_ranking() -> pd.DataFrame:
    """Load tunnel node frequency ranking with scores."""
    path = MULTIPLEX_DIR / "tunnel_frequency_ranking.tsv"
    if not path.exists():
        return pd.DataFrame()
    df = pd.read_csv(path, sep="\t")
    # Fill NaN page titles with page_id
    df["page_title"] = df["page_title"].fillna(df["page_id"].astype(str))
    return df


def load_reachability_summary() -> pd.DataFrame:
    """Load per-cycle reachability statistics."""
    path = MULTIPLEX_DIR / "multiplex_reachability_summary.tsv"
    if not path.exists():
        return pd.DataFrame()
    return pd.read_csv(path, sep="\t")


def load_basin_intersection() -> pd.DataFrame:
    """Load basin intersection data by cycle."""
    path = MULTIPLEX_DIR / "basin_intersection_by_cycle.tsv"
    if not path.exists():
        return pd.DataFrame()
    return pd.read_csv(path, sep="\t")


# Load all data at startup
print("Loading multiplex data...")
layer_conn_df = load_layer_connectivity()
tunnel_class_df = load_tunnel_classification()
tunnel_rank_df = load_tunnel_ranking()
reachability_df = load_reachability_summary()
intersection_df = load_basin_intersection()

print(f"  Layer connectivity: {len(layer_conn_df)} rows")
print(f"  Tunnel classification: {len(tunnel_class_df)} rows")
print(f"  Tunnel ranking: {len(tunnel_rank_df)} rows")
print(f"  Reachability summary: {len(reachability_df)} rows")
print(f"  Basin intersection: {len(intersection_df)} rows")


# ============================================================================
# Helper Functions
# ============================================================================

def create_connectivity_matrix(df: pd.DataFrame, log_scale: bool = True) -> np.ndarray:
    """Convert layer connectivity dataframe to matrix form."""
    if df.empty:
        return np.zeros((5, 5))

    n_values = sorted(df["src_N"].unique())
    matrix = np.zeros((len(n_values), len(n_values)))

    for _, row in df.iterrows():
        i = n_values.index(row["src_N"])
        j = n_values.index(row["dst_N"])
        matrix[i, j] = row["edge_count"]

    if log_scale:
        matrix = np.log10(matrix + 1)

    return matrix


def get_basin_pairs_summary(df: pd.DataFrame) -> pd.DataFrame:
    """Aggregate tunnel nodes by basin pair."""
    if df.empty:
        return pd.DataFrame()

    # Count tunnels per basin pair
    pair_counts = df.groupby("basin_pair").agg({
        "page_id": "count",
        "tunnel_type": lambda x: (x == "progressive").sum(),
    }).reset_index()
    pair_counts.columns = ["basin_pair", "tunnel_count", "progressive_count"]
    pair_counts["alternating_count"] = pair_counts["tunnel_count"] - pair_counts["progressive_count"]
    pair_counts = pair_counts.sort_values("tunnel_count", ascending=False)

    return pair_counts


# ============================================================================
# Dash App
# ============================================================================

app = dash.Dash(
    __name__,
    external_stylesheets=[dbc.themes.BOOTSTRAP],
    suppress_callback_exceptions=True,
)

app.title = "Multiplex Tunnel Explorer"


# ============================================================================
# Layout Components
# ============================================================================

def create_header():
    """Create app header."""
    return dbc.Container([
        html.H1("Multiplex Tunnel Explorer", className="text-center my-4"),
        html.P(
            "Interactive exploration of cross-N basin connectivity and tunnel nodes",
            className="text-center text-muted mb-2"
        ),
        dbc.Row([
            dbc.Col([
                dbc.Badge(f"{len(tunnel_class_df):,} tunnel nodes", color="primary", className="me-2"),
                dbc.Badge(f"N=3-10 layers", color="secondary", className="me-2"),
                dbc.Badge("Phase 2-3 Analysis", color="success"),
            ], className="text-center mb-3")
        ]),
        html.Hr()
    ], fluid=True)


def create_tab_connectivity():
    """Tab 1: Layer Connectivity Matrix."""
    return dbc.Container([
        dbc.Row([
            dbc.Col([
                html.H4("Layer Connectivity Matrix"),
                html.P("Edge counts between N layers. Diagonal = within-N, off-diagonal = tunnel edges."),
            ], width=8),
            dbc.Col([
                dbc.Checklist(
                    id="connectivity-log-scale",
                    options=[{"label": "Log scale", "value": "log"}],
                    value=["log"],
                    switch=True,
                    className="mt-2"
                ),
            ], width=4, className="text-end"),
        ]),
        dbc.Row([
            dbc.Col([
                dcc.Graph(id="connectivity-heatmap", style={"height": "500px"}),
            ], width=8),
            dbc.Col([
                html.H5("Statistics"),
                html.Div(id="connectivity-stats", className="small"),
            ], width=4),
        ]),
        dbc.Row([
            dbc.Col([
                html.H5("Cross-Layer Edge Breakdown", className="mt-4"),
                dcc.Graph(id="cross-layer-bar", style={"height": "300px"}),
            ])
        ]),
    ], fluid=True)


def create_tab_tunnel_nodes():
    """Tab 2: Tunnel Node Explorer."""
    # Get unique values for filters
    tunnel_types = ["all"] + list(tunnel_class_df["tunnel_type"].unique()) if not tunnel_class_df.empty else ["all"]
    basin_pairs = ["all"] + list(tunnel_class_df["basin_pair"].unique()[:50]) if not tunnel_class_df.empty else ["all"]

    return dbc.Container([
        dbc.Row([
            dbc.Col([
                html.H4("Tunnel Node Explorer"),
                html.P("Browse and filter tunnel nodes by type, basin pair, and score."),
            ])
        ]),
        dbc.Row([
            dbc.Col([
                html.Label("Tunnel Type:", className="fw-bold"),
                dcc.Dropdown(
                    id="tunnel-type-filter",
                    options=[{"label": t.title() if t != "all" else "All Types", "value": t} for t in tunnel_types],
                    value="all",
                    clearable=False,
                ),
            ], width=3),
            dbc.Col([
                html.Label("Basin Pair:", className="fw-bold"),
                dcc.Dropdown(
                    id="basin-pair-filter",
                    options=[{"label": b if b != "all" else "All Pairs", "value": b} for b in basin_pairs],
                    value="all",
                    clearable=False,
                ),
            ], width=4),
            dbc.Col([
                html.Label("Min Score:", className="fw-bold"),
                dcc.Slider(
                    id="min-score-filter",
                    min=0,
                    max=80,
                    step=5,
                    value=0,
                    marks={i: str(i) for i in range(0, 81, 20)},
                ),
            ], width=4),
        ], className="mb-3"),
        dbc.Row([
            dbc.Col([
                html.Div(id="tunnel-table-summary", className="mb-2 text-muted"),
                dash_table.DataTable(
                    id="tunnel-table",
                    columns=[
                        {"name": "Page ID", "id": "page_id"},
                        {"name": "Title", "id": "page_title"},
                        {"name": "Type", "id": "tunnel_type"},
                        {"name": "Score", "id": "tunnel_score", "type": "numeric", "format": {"specifier": ".1f"}},
                        {"name": "Basins", "id": "n_basins_bridged"},
                        {"name": "Transitions", "id": "n_transitions"},
                        {"name": "Mean Depth", "id": "mean_depth", "type": "numeric", "format": {"specifier": ".1f"}},
                        {"name": "Basins", "id": "basin_list"},
                    ],
                    data=[],
                    page_size=15,
                    sort_action="native",
                    sort_mode="single",
                    sort_by=[{"column_id": "tunnel_score", "direction": "desc"}],
                    style_table={"overflowX": "auto"},
                    style_cell={"textAlign": "left", "padding": "8px", "fontSize": "12px"},
                    style_header={"fontWeight": "bold", "backgroundColor": "#f8f9fa"},
                    style_data_conditional=[
                        {"if": {"filter_query": "{tunnel_type} = 'progressive'"}, "backgroundColor": "#e8f5e9"},
                        {"if": {"filter_query": "{tunnel_type} = 'alternating'"}, "backgroundColor": "#fff3e0"},
                    ],
                ),
            ])
        ]),
        dbc.Row([
            dbc.Col([
                html.H5("Score Distribution", className="mt-4"),
                dcc.Graph(id="score-histogram", style={"height": "250px"}),
            ], width=6),
            dbc.Col([
                html.H5("Tunnel Type Breakdown", className="mt-4"),
                dcc.Graph(id="type-pie", style={"height": "250px"}),
            ], width=6),
        ]),
    ], fluid=True)


def create_tab_basin_pairs():
    """Tab 3: Basin Pair Network."""
    return dbc.Container([
        dbc.Row([
            dbc.Col([
                html.H4("Basin Pair Connectivity"),
                html.P("Network showing which basins connect via tunnel nodes."),
            ])
        ]),
        dbc.Row([
            dbc.Col([
                dcc.Graph(id="basin-pair-network", style={"height": "500px"}),
            ], width=8),
            dbc.Col([
                html.H5("Top Basin Pairs"),
                html.Div(id="top-basin-pairs"),
            ], width=4),
        ]),
        dbc.Row([
            dbc.Col([
                html.H5("Tunnel Count by Basin Pair", className="mt-4"),
                dcc.Graph(id="basin-pair-bar", style={"height": "300px"}),
            ])
        ]),
    ], fluid=True)


def create_tab_reachability():
    """Tab 4: Cycle Reachability."""
    return dbc.Container([
        dbc.Row([
            dbc.Col([
                html.H4("Cycle Reachability Analysis"),
                html.P("BFS reachability from each cycle across N layers."),
            ])
        ]),
        dbc.Row([
            dbc.Col([
                dcc.Graph(id="reachability-stacked", style={"height": "400px"}),
            ])
        ]),
        dbc.Row([
            dbc.Col([
                html.H5("Reachability Statistics", className="mt-4"),
                dash_table.DataTable(
                    id="reachability-table",
                    columns=[
                        {"name": "Cycle", "id": "cycle"},
                        {"name": "Members", "id": "cycle_members"},
                        {"name": "Total Reachable", "id": "total_reachable"},
                        {"name": "Tunnel Reachable", "id": "tunnel_reachable"},
                        {"name": "Max Depth", "id": "max_depth_reached"},
                    ],
                    data=reachability_df.to_dict("records") if not reachability_df.empty else [],
                    page_size=10,
                    sort_action="native",
                    style_cell={"textAlign": "left", "padding": "8px", "fontSize": "12px"},
                    style_header={"fontWeight": "bold", "backgroundColor": "#f8f9fa"},
                ),
            ])
        ]),
        dbc.Row([
            dbc.Col([
                html.H5("Basin Intersection (Jaccard)", className="mt-4"),
                dcc.Graph(id="intersection-heatmap", style={"height": "350px"}),
            ], width=6),
            dbc.Col([
                html.H5("Intersection by N Pair", className="mt-4"),
                dcc.Graph(id="intersection-bar", style={"height": "350px"}),
            ], width=6),
        ]),
    ], fluid=True)


# Main Layout
app.layout = html.Div([
    create_header(),
    dbc.Tabs([
        dbc.Tab(create_tab_connectivity(), label="Layer Connectivity", tab_id="tab-connectivity"),
        dbc.Tab(create_tab_tunnel_nodes(), label="Tunnel Nodes", tab_id="tab-tunnels"),
        dbc.Tab(create_tab_basin_pairs(), label="Basin Pairs", tab_id="tab-pairs"),
        dbc.Tab(create_tab_reachability(), label="Reachability", tab_id="tab-reach"),
    ], id="tabs", active_tab="tab-connectivity", className="mb-3"),
])


# ============================================================================
# Callbacks
# ============================================================================

@callback(
    [Output("connectivity-heatmap", "figure"),
     Output("connectivity-stats", "children"),
     Output("cross-layer-bar", "figure")],
    [Input("connectivity-log-scale", "value")]
)
def update_connectivity_tab(log_scale):
    """Update layer connectivity visualizations."""
    use_log = "log" in log_scale if log_scale else False

    if layer_conn_df.empty:
        empty_fig = go.Figure()
        empty_fig.add_annotation(text="No data available", showarrow=False)
        return empty_fig, "No data", empty_fig

    # Create heatmap
    n_values = sorted(layer_conn_df["src_N"].unique())
    matrix = create_connectivity_matrix(layer_conn_df, log_scale=use_log)

    # Raw matrix for annotations
    raw_matrix = create_connectivity_matrix(layer_conn_df, log_scale=False)

    # Format annotations
    annotations = []
    for i, src_n in enumerate(n_values):
        for j, dst_n in enumerate(n_values):
            count = int(raw_matrix[i, j])
            annotations.append(
                dict(
                    x=j, y=i,
                    text=f"{count:,}",
                    showarrow=False,
                    font=dict(color="white" if matrix[i, j] > matrix.max() * 0.5 else "black", size=10),
                )
            )

    heatmap = go.Figure(data=go.Heatmap(
        z=matrix,
        x=[f"N={n}" for n in n_values],
        y=[f"N={n}" for n in n_values],
        colorscale="YlOrRd",
        colorbar=dict(title="log10(count)" if use_log else "count"),
    ))
    heatmap.update_layout(
        title="Layer-to-Layer Edge Counts",
        xaxis_title="Destination N",
        yaxis_title="Source N",
        annotations=annotations,
        yaxis=dict(autorange="reversed"),
        margin=dict(l=60, r=20, t=50, b=60),
    )

    # Statistics
    total_edges = int(raw_matrix.sum())
    diagonal_edges = int(np.trace(raw_matrix))
    cross_layer_edges = total_edges - diagonal_edges

    stats = [
        html.P([html.Strong("Total edges: "), f"{total_edges:,}"]),
        html.P([html.Strong("Within-N: "), f"{diagonal_edges:,} ({100*diagonal_edges/total_edges:.1f}%)"]),
        html.P([html.Strong("Cross-N: "), f"{cross_layer_edges:,} ({100*cross_layer_edges/total_edges:.1f}%)"]),
        html.Hr(),
        html.P([html.Strong("Strongest cross-layer:")]),
    ]

    # Find strongest cross-layer connections
    cross_layer = layer_conn_df[layer_conn_df["src_N"] != layer_conn_df["dst_N"]].copy()
    cross_layer = cross_layer.sort_values("edge_count", ascending=False).head(5)
    for _, row in cross_layer.iterrows():
        stats.append(html.P(f"N={row['src_N']}→N={row['dst_N']}: {row['edge_count']:,}", className="small"))

    # Cross-layer bar chart
    cross_layer_all = layer_conn_df[layer_conn_df["src_N"] != layer_conn_df["dst_N"]].copy()
    cross_layer_all["pair"] = cross_layer_all.apply(
        lambda r: f"N={r['src_N']}→N={r['dst_N']}", axis=1
    )

    bar_fig = px.bar(
        cross_layer_all.sort_values("edge_count", ascending=True),
        x="edge_count",
        y="pair",
        orientation="h",
        title="Cross-Layer Edge Counts",
        labels={"edge_count": "Edge Count", "pair": "Layer Pair"},
    )
    bar_fig.update_layout(margin=dict(l=100, r=20, t=50, b=40))

    return heatmap, stats, bar_fig


@callback(
    [Output("tunnel-table", "data"),
     Output("tunnel-table-summary", "children"),
     Output("score-histogram", "figure"),
     Output("type-pie", "figure")],
    [Input("tunnel-type-filter", "value"),
     Input("basin-pair-filter", "value"),
     Input("min-score-filter", "value")]
)
def update_tunnel_table(tunnel_type, basin_pair, min_score):
    """Update tunnel node table and visualizations."""
    if tunnel_rank_df.empty:
        empty_fig = go.Figure()
        return [], "No data", empty_fig, empty_fig

    # Filter data
    filtered = tunnel_rank_df.copy()

    if tunnel_type != "all":
        filtered = filtered[filtered["tunnel_type"] == tunnel_type]

    if basin_pair != "all":
        # Need to join with classification to filter by basin pair
        class_subset = tunnel_class_df[tunnel_class_df["basin_pair"] == basin_pair]["page_id"]
        filtered = filtered[filtered["page_id"].isin(class_subset)]

    if min_score > 0:
        filtered = filtered[filtered["tunnel_score"] >= min_score]

    # Summary
    summary = f"Showing {len(filtered):,} of {len(tunnel_rank_df):,} tunnel nodes"

    # Table data
    table_data = filtered.head(500).to_dict("records")

    # Score histogram
    hist_fig = px.histogram(
        filtered,
        x="tunnel_score",
        nbins=30,
        title="Score Distribution",
        labels={"tunnel_score": "Tunnel Score"},
    )
    hist_fig.update_layout(margin=dict(l=40, r=20, t=50, b=40), showlegend=False)

    # Type pie chart
    type_counts = filtered["tunnel_type"].value_counts()
    pie_fig = px.pie(
        values=type_counts.values,
        names=type_counts.index,
        title="Tunnel Types",
        color_discrete_map={"progressive": "#4CAF50", "alternating": "#FF9800"},
    )
    pie_fig.update_layout(margin=dict(l=20, r=20, t=50, b=20))

    return table_data, summary, hist_fig, pie_fig


@callback(
    [Output("basin-pair-network", "figure"),
     Output("top-basin-pairs", "children"),
     Output("basin-pair-bar", "figure")],
    [Input("tabs", "active_tab")]
)
def update_basin_pairs(active_tab):
    """Update basin pair visualizations."""
    if tunnel_class_df.empty:
        empty_fig = go.Figure()
        return empty_fig, "No data", empty_fig

    # Get basin pair summary
    pair_summary = get_basin_pairs_summary(tunnel_class_df)

    if pair_summary.empty:
        empty_fig = go.Figure()
        return empty_fig, "No data", empty_fig

    # Top pairs list
    top_pairs = []
    for _, row in pair_summary.head(10).iterrows():
        top_pairs.append(
            html.Div([
                html.Strong(f"{row['tunnel_count']:,}"),
                html.Span(f" tunnels: {row['basin_pair'][:40]}...", className="small"),
            ], className="mb-2")
        )

    # Bar chart of top pairs
    top_20 = pair_summary.head(20)
    bar_fig = px.bar(
        top_20,
        x="tunnel_count",
        y="basin_pair",
        orientation="h",
        color="progressive_count",
        color_continuous_scale="Greens",
        title="Top 20 Basin Pairs by Tunnel Count",
        labels={"tunnel_count": "Tunnel Count", "basin_pair": "Basin Pair", "progressive_count": "Progressive"},
    )
    bar_fig.update_layout(
        margin=dict(l=200, r=20, t=50, b=40),
        yaxis=dict(autorange="reversed"),
        height=400,
    )

    # Network visualization (simplified - show top pairs as nodes and edges)
    # Extract unique basins
    basins = set()
    edges = []
    for _, row in pair_summary.head(30).iterrows():
        pair = row["basin_pair"]
        if " / " in pair:
            b1, b2 = pair.split(" / ")[:2]
            b1, b2 = b1.strip()[:20], b2.strip()[:20]
            basins.add(b1)
            basins.add(b2)
            edges.append((b1, b2, row["tunnel_count"]))

    # Create network positions (simple circular layout)
    basin_list = list(basins)
    n_basins = len(basin_list)
    angles = np.linspace(0, 2 * np.pi, n_basins, endpoint=False)
    positions = {b: (np.cos(a), np.sin(a)) for b, a in zip(basin_list, angles)}

    # Create edge traces
    edge_traces = []
    for b1, b2, count in edges:
        x0, y0 = positions.get(b1, (0, 0))
        x1, y1 = positions.get(b2, (0, 0))
        edge_traces.append(go.Scatter(
            x=[x0, x1, None],
            y=[y0, y1, None],
            mode="lines",
            line=dict(width=max(1, np.log10(count + 1) * 2), color="rgba(100, 100, 100, 0.5)"),
            hoverinfo="skip",
            showlegend=False,
        ))

    # Create node trace
    node_trace = go.Scatter(
        x=[positions[b][0] for b in basin_list],
        y=[positions[b][1] for b in basin_list],
        mode="markers+text",
        marker=dict(size=15, color="#1f77b4"),
        text=basin_list,
        textposition="top center",
        hovertemplate="%{text}<extra></extra>",
        showlegend=False,
    )

    network_fig = go.Figure(data=edge_traces + [node_trace])
    network_fig.update_layout(
        title="Basin Pair Network (Top 30)",
        showlegend=False,
        xaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
        yaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
        margin=dict(l=20, r=20, t=50, b=20),
    )

    return network_fig, top_pairs, bar_fig


@callback(
    [Output("reachability-stacked", "figure"),
     Output("intersection-heatmap", "figure"),
     Output("intersection-bar", "figure")],
    [Input("tabs", "active_tab")]
)
def update_reachability(active_tab):
    """Update reachability visualizations."""
    # Stacked bar for reachability by N
    if reachability_df.empty:
        empty_fig = go.Figure()
        return empty_fig, empty_fig, empty_fig

    # Prepare data for stacked bar
    reach_cols = [c for c in reachability_df.columns if c.startswith("reachable_N")]

    stacked_fig = go.Figure()
    colors = px.colors.qualitative.Set2

    for i, col in enumerate(reach_cols):
        n_val = col.replace("reachable_N", "")
        stacked_fig.add_trace(go.Bar(
            name=f"N={n_val}",
            x=reachability_df["cycle"].str[:25],
            y=reachability_df[col],
            marker_color=colors[i % len(colors)],
        ))

    stacked_fig.update_layout(
        title="Reachable Nodes by N Layer (per cycle)",
        barmode="stack",
        xaxis_title="Cycle",
        yaxis_title="Reachable Nodes",
        legend_title="N Layer",
        margin=dict(l=60, r=20, t=50, b=100),
        xaxis_tickangle=-45,
    )

    # Intersection heatmap (for Gulf_of_Maine)
    if intersection_df.empty:
        empty_fig = go.Figure()
        empty_fig.add_annotation(text="No intersection data", showarrow=False)
        return stacked_fig, empty_fig, empty_fig

    # Create N×N Jaccard matrix for first cycle
    cycle_data = intersection_df[intersection_df["cycle_id"] == intersection_df["cycle_id"].iloc[0]]
    n_vals = sorted(set(cycle_data["N1"].tolist() + cycle_data["N2"].tolist()))

    jaccard_matrix = np.zeros((len(n_vals), len(n_vals)))
    for _, row in cycle_data.iterrows():
        i = n_vals.index(row["N1"])
        j = n_vals.index(row["N2"])
        jaccard_matrix[i, j] = row["jaccard"]
        jaccard_matrix[j, i] = row["jaccard"]

    # Diagonal = 1.0 (self-intersection)
    np.fill_diagonal(jaccard_matrix, 1.0)

    intersection_heatmap = go.Figure(data=go.Heatmap(
        z=jaccard_matrix,
        x=[f"N={n}" for n in n_vals],
        y=[f"N={n}" for n in n_vals],
        colorscale="Blues",
        colorbar=dict(title="Jaccard"),
    ))
    intersection_heatmap.update_layout(
        title=f"Basin Intersection (Jaccard) - {cycle_data['cycle_id'].iloc[0][:30]}",
        yaxis=dict(autorange="reversed"),
        margin=dict(l=60, r=20, t=50, b=60),
    )

    # Intersection bar by N pair
    intersection_bar = px.bar(
        cycle_data,
        x="jaccard",
        y=cycle_data.apply(lambda r: f"N={r['N1']}-N={r['N2']}", axis=1),
        orientation="h",
        title="Jaccard Similarity by N Pair",
        labels={"jaccard": "Jaccard Index", "y": "N Pair"},
    )
    intersection_bar.update_layout(margin=dict(l=80, r=20, t=50, b=40))

    return stacked_fig, intersection_heatmap, intersection_bar


# ============================================================================
# Main
# ============================================================================

def main():
    parser = argparse.ArgumentParser(description="Multiplex Tunnel Explorer")
    parser.add_argument("--host", default="127.0.0.1", help="Host to bind to")
    parser.add_argument("--port", type=int, default=8056, help="Port to bind to")
    parser.add_argument("--debug", action="store_true", help="Enable debug mode")
    args = parser.parse_args()

    print(f"\nStarting Multiplex Tunnel Explorer at http://{args.host}:{args.port}")
    print("Press Ctrl+C to stop\n")

    app.run(host=args.host, port=args.port, debug=args.debug)


if __name__ == "__main__":
    main()
