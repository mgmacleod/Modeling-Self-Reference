#!/usr/bin/env python3
"""Interactive Dash dashboard for exploring tunneling analysis results.

A multi-tab dashboard providing comprehensive visualization of:
- Overview metrics and distributions
- Basin flow Sankey diagrams
- Tunnel node exploration
- Basin stability analysis
- Theory validation results

Usage:
    python tunneling-dashboard.py [--port PORT]

The dashboard will be available at http://localhost:PORT
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import pandas as pd
import numpy as np
import plotly.graph_objects as go
import plotly.express as px

try:
    import dash
    from dash import dcc, html, dash_table, callback, Input, Output, State
    import dash_bootstrap_components as dbc
except ImportError:
    print("Error: dash and dash-bootstrap-components required")
    print("Install with: pip install dash dash-bootstrap-components")
    exit(1)

REPO_ROOT = Path(__file__).resolve().parents[3]
MULTIPLEX_DIR = REPO_ROOT / "data" / "wikipedia" / "processed" / "multiplex"
REPORT_DIR = REPO_ROOT / "n-link-analysis" / "report" / "assets"

# Basin color scheme
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


def get_short_name(basin: str) -> str:
    """Get short display name for a basin."""
    for key, name in BASIN_SHORT_NAMES.items():
        if key in basin or basin in key:
            return name
    return basin.split("__")[0][:15]


def get_basin_color(basin: str) -> str:
    """Get color for a basin."""
    for key, color in BASIN_COLORS.items():
        if key in basin or basin in key:
            return color
    return "#7f7f7f"


# ============================================================================
# Data Loading
# ============================================================================

def load_semantic_model() -> dict:
    """Load semantic model JSON."""
    path = MULTIPLEX_DIR / "semantic_model_wikipedia.json"
    if not path.exists():
        return {}
    with open(path) as f:
        return json.load(f)


def load_basin_flows() -> pd.DataFrame:
    """Load basin flows data."""
    path = MULTIPLEX_DIR / "basin_flows.tsv"
    if not path.exists():
        return pd.DataFrame()
    return pd.read_csv(path, sep="\t")


def load_tunnel_ranking() -> pd.DataFrame:
    """Load tunnel frequency ranking."""
    path = MULTIPLEX_DIR / "tunnel_frequency_ranking.tsv"
    if not path.exists():
        return pd.DataFrame()
    return pd.read_csv(path, sep="\t")


def load_basin_stability() -> pd.DataFrame:
    """Load basin stability scores."""
    path = MULTIPLEX_DIR / "basin_stability_scores.tsv"
    if not path.exists():
        return pd.DataFrame()
    return pd.read_csv(path, sep="\t")


def load_mechanisms() -> pd.DataFrame:
    """Load tunnel mechanism summary."""
    path = MULTIPLEX_DIR / "tunnel_mechanism_summary.tsv"
    if not path.exists():
        return pd.DataFrame()
    return pd.read_csv(path, sep="\t")


def load_validation() -> pd.DataFrame:
    """Load validation metrics."""
    path = MULTIPLEX_DIR / "tunneling_validation_metrics.tsv"
    if not path.exists():
        return pd.DataFrame()
    return pd.read_csv(path, sep="\t")


# ============================================================================
# Visualization Components
# ============================================================================

def create_metric_card(value, label, color="#1f77b4"):
    """Create a metric card component."""
    return dbc.Card([
        dbc.CardBody([
            html.H2(value, className="card-title text-center", style={"color": color}),
            html.P(label, className="card-text text-center text-muted"),
        ])
    ], className="mb-3")


def create_overview_charts(semantic_model: dict, mechanisms_df: pd.DataFrame, tunnel_df: pd.DataFrame) -> tuple:
    """Create overview tab charts."""

    # Mechanism pie chart
    if not mechanisms_df.empty:
        mech_fig = px.pie(
            mechanisms_df,
            values="count",
            names="mechanism",
            title="Tunnel Mechanism Distribution",
            color_discrete_sequence=["#2ca02c", "#ff7f0e"],
            hole=0.4,
        )
        mech_fig.update_layout(margin=dict(t=50, b=20, l=20, r=20))
    else:
        mech_fig = go.Figure()
        mech_fig.add_annotation(text="No mechanism data", showarrow=False)

    # Tunnel score vs depth scatter
    if not tunnel_df.empty:
        scatter_fig = px.scatter(
            tunnel_df.head(500),  # Limit for performance
            x="mean_depth",
            y="tunnel_score",
            color="tunnel_type",
            hover_data=["page_title"],
            title="Tunnel Score vs Mean Depth",
            labels={"mean_depth": "Mean Depth", "tunnel_score": "Tunnel Score"},
            color_discrete_map={"progressive": "#2ca02c", "alternating": "#ff7f0e"},
        )
        scatter_fig.update_layout(margin=dict(t=50, b=50, l=50, r=20))
    else:
        scatter_fig = go.Figure()
        scatter_fig.add_annotation(text="No tunnel data", showarrow=False)

    # Type distribution bar
    if not tunnel_df.empty:
        type_counts = tunnel_df["tunnel_type"].value_counts()
        type_fig = go.Figure(data=[
            go.Bar(
                x=type_counts.index.tolist(),
                y=type_counts.values.tolist(),
                marker_color=["#2ca02c", "#ff7f0e"],
            )
        ])
        type_fig.update_layout(
            title="Tunnel Type Distribution",
            xaxis_title="Type",
            yaxis_title="Count",
            margin=dict(t=50, b=50, l=50, r=20),
        )
    else:
        type_fig = go.Figure()

    return mech_fig, scatter_fig, type_fig


def create_sankey_figure(flows_df: pd.DataFrame) -> go.Figure:
    """Create Sankey diagram from flows data."""
    if flows_df.empty:
        fig = go.Figure()
        fig.add_annotation(text="No flow data available", showarrow=False)
        return fig

    n_values = sorted(set(flows_df["from_n"].unique()) | set(flows_df["to_n"].unique()))
    all_basins = sorted(set(flows_df["from_basin"].unique()) | set(flows_df["to_basin"].unique()))

    nodes = []
    node_indices = {}

    for n in n_values:
        for basin in all_basins:
            node_key = f"{basin}@N{n}"
            node_indices[node_key] = len(nodes)
            nodes.append({
                "label": f"{get_short_name(basin)} (N={n})",
                "color": get_basin_color(basin),
            })

    sources, targets, values, colors = [], [], [], []

    for _, row in flows_df.iterrows():
        from_key = f"{row['from_basin']}@N{row['from_n']}"
        to_key = f"{row['to_basin']}@N{row['to_n']}"

        if from_key in node_indices and to_key in node_indices:
            sources.append(node_indices[from_key])
            targets.append(node_indices[to_key])
            values.append(row["count"])

            base_color = get_basin_color(row["from_basin"])
            hex_color = base_color.lstrip("#")
            r, g, b = tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))
            colors.append(f"rgba({r}, {g}, {b}, 0.5)")

    fig = go.Figure(data=[go.Sankey(
        arrangement="snap",
        node=dict(
            pad=20,
            thickness=25,
            line=dict(color="black", width=0.5),
            label=[n["label"] for n in nodes],
            color=[n["color"] for n in nodes],
        ),
        link=dict(
            source=sources,
            target=targets,
            value=values,
            color=colors,
        ),
    )])

    fig.update_layout(
        title="Cross-Basin Page Flows",
        height=500,
        margin=dict(t=50, b=20, l=20, r=20),
    )

    return fig


def create_stability_chart(stability_df: pd.DataFrame) -> go.Figure:
    """Create basin stability horizontal bar chart."""
    if stability_df.empty:
        fig = go.Figure()
        fig.add_annotation(text="No stability data", showarrow=False)
        return fig

    # Sort by stability
    df = stability_df.copy()
    df["short_name"] = df["canonical_cycle_id"].apply(get_short_name)

    # Color by stability class
    colors = []
    for _, row in df.iterrows():
        stability = row.get("stability_class", "unknown")
        if stability == "fragile":
            colors.append("#d62728")
        elif stability == "moderate":
            colors.append("#ff7f0e")
        elif stability == "stable":
            colors.append("#2ca02c")
        else:
            colors.append("#7f7f7f")

    fig = go.Figure(data=[
        go.Bar(
            y=df["short_name"],
            x=df["persistence_score"],
            orientation="h",
            marker_color=colors,
            text=[f"{row.get('total_pages', 0):,} pages" for _, row in df.iterrows()],
            textposition="outside",
        )
    ])

    fig.update_layout(
        title="Basin Stability Scores",
        xaxis_title="Persistence Score",
        yaxis_title="Basin",
        height=400,
        margin=dict(t=50, b=50, l=120, r=80),
    )

    return fig


def create_validation_table(validation_df: pd.DataFrame) -> dash_table.DataTable:
    """Create validation results table."""
    if validation_df.empty:
        return html.P("No validation data available")

    # Map result to status
    df = validation_df.copy()

    return dash_table.DataTable(
        id="validation-table",
        columns=[
            {"name": "Hypothesis", "id": "hypothesis"},
            {"name": "Expected", "id": "expected"},
            {"name": "Observed", "id": "observed"},
            {"name": "Statistic", "id": "statistic"},
            {"name": "P-Value", "id": "p_value"},
            {"name": "Result", "id": "result"},
        ],
        data=df.to_dict("records"),
        style_table={"overflowX": "auto"},
        style_cell={
            "textAlign": "left",
            "padding": "10px",
            "fontSize": "14px",
        },
        style_header={
            "backgroundColor": "#1a1a2e",
            "color": "white",
            "fontWeight": "bold",
        },
        style_data_conditional=[
            {
                "if": {"filter_query": '{result} = "validated"'},
                "backgroundColor": "#d4edda",
                "color": "#155724",
            },
            {
                "if": {"filter_query": '{result} = "refuted"'},
                "backgroundColor": "#f8d7da",
                "color": "#721c24",
            },
        ],
    )


# ============================================================================
# Dashboard Layout
# ============================================================================

def create_layout(semantic_model: dict) -> dbc.Container:
    """Create the main dashboard layout."""

    summary = semantic_model.get("summary", {})

    return dbc.Container([
        # Header
        dbc.Row([
            dbc.Col([
                html.H1("Tunneling Analysis Dashboard", className="mb-2"),
                html.P(
                    "Wikipedia N-Link Rule Analysis - Cross-Basin Tunneling Exploration",
                    className="text-muted"
                ),
            ])
        ], className="mb-4"),

        # Tabs
        dbc.Tabs([
            # Overview Tab
            dbc.Tab([
                dbc.Row([
                    dbc.Col(create_metric_card(
                        f"{summary.get('total_pages_in_hyperstructure', 0):,}",
                        "Total Pages",
                        "#1f77b4"
                    ), md=3),
                    dbc.Col(create_metric_card(
                        f"{summary.get('tunnel_nodes', 0):,}",
                        "Tunnel Nodes",
                        "#2ca02c"
                    ), md=3),
                    dbc.Col(create_metric_card(
                        f"{summary.get('tunnel_percentage', 0):.2f}%",
                        "Tunnel Rate",
                        "#ff7f0e"
                    ), md=3),
                    dbc.Col(create_metric_card(
                        f"{summary.get('n_basins', 0)}",
                        "Basins",
                        "#9467bd"
                    ), md=3),
                ], className="mb-4"),

                dbc.Row([
                    dbc.Col([
                        dcc.Graph(id="mechanism-pie")
                    ], md=4),
                    dbc.Col([
                        dcc.Graph(id="scatter-plot")
                    ], md=4),
                    dbc.Col([
                        dcc.Graph(id="type-bar")
                    ], md=4),
                ]),

                dbc.Row([
                    dbc.Col([
                        dbc.Card([
                            dbc.CardHeader("Key Insights"),
                            dbc.CardBody([
                                html.Ul([
                                    html.Li("99.3% of tunneling is caused by degree_shift (different Nth link)"),
                                    html.Li("N=5 is the critical phase transition point"),
                                    html.Li("Shallow nodes (low depth) tunnel more than deep nodes"),
                                    html.Li("Gulf of Maine acts as a 'sink' basin at higher N values"),
                                ])
                            ])
                        ])
                    ])
                ], className="mt-3"),
            ], label="Overview", tab_id="tab-overview"),

            # Basin Flows Tab
            dbc.Tab([
                dbc.Row([
                    dbc.Col([
                        dcc.Graph(id="sankey-diagram", style={"height": "600px"})
                    ])
                ]),
                dbc.Row([
                    dbc.Col([
                        dbc.Card([
                            dbc.CardHeader("Flow Pattern"),
                            dbc.CardBody([
                                html.P([
                                    "At the N=5→N=6 transition, pages flow ",
                                    html.Strong("into"),
                                    " Gulf of Maine from all other basins. This unidirectional flow ",
                                    "explains the phase transition behavior observed in the basin structure."
                                ])
                            ])
                        ])
                    ])
                ], className="mt-3"),
            ], label="Basin Flows", tab_id="tab-flows"),

            # Tunnel Nodes Tab
            dbc.Tab([
                dbc.Row([
                    dbc.Col([
                        html.H4("Filter Options", className="mb-3"),
                        dbc.Row([
                            dbc.Col([
                                dbc.Label("Tunnel Type"),
                                dcc.Dropdown(
                                    id="type-filter",
                                    options=[
                                        {"label": "All", "value": "all"},
                                        {"label": "Progressive", "value": "progressive"},
                                        {"label": "Alternating", "value": "alternating"},
                                    ],
                                    value="all",
                                    clearable=False,
                                ),
                            ], md=4),
                            dbc.Col([
                                dbc.Label("Minimum Score"),
                                dcc.Slider(
                                    id="score-slider",
                                    min=0,
                                    max=75,
                                    step=5,
                                    value=0,
                                    marks={i: str(i) for i in range(0, 80, 10)},
                                ),
                            ], md=6),
                        ]),
                    ])
                ], className="mb-4"),

                dbc.Row([
                    dbc.Col([
                        dash_table.DataTable(
                            id="tunnel-table",
                            columns=[
                                {"name": "Rank", "id": "rank"},
                                {"name": "Page Title", "id": "page_title"},
                                {"name": "Score", "id": "tunnel_score", "type": "numeric", "format": {"specifier": ".2f"}},
                                {"name": "Basins", "id": "n_basins_bridged"},
                                {"name": "Depth", "id": "mean_depth", "type": "numeric", "format": {"specifier": ".1f"}},
                                {"name": "Type", "id": "tunnel_type"},
                            ],
                            page_size=20,
                            sort_action="native",
                            filter_action="native",
                            style_table={"overflowX": "auto"},
                            style_cell={
                                "textAlign": "left",
                                "padding": "8px",
                                "fontSize": "13px",
                            },
                            style_header={
                                "backgroundColor": "#1a1a2e",
                                "color": "white",
                                "fontWeight": "bold",
                            },
                            style_data_conditional=[
                                {
                                    "if": {"filter_query": '{tunnel_type} = "progressive"'},
                                    "backgroundColor": "#d4edda",
                                },
                                {
                                    "if": {"filter_query": '{tunnel_type} = "alternating"'},
                                    "backgroundColor": "#fff3cd",
                                },
                            ],
                        )
                    ])
                ]),
            ], label="Tunnel Nodes", tab_id="tab-nodes"),

            # Stability Tab
            dbc.Tab([
                dbc.Row([
                    dbc.Col([
                        dcc.Graph(id="stability-chart")
                    ])
                ]),
                dbc.Row([
                    dbc.Col([
                        dbc.Card([
                            dbc.CardHeader("Stability Classes"),
                            dbc.CardBody([
                                dbc.Row([
                                    dbc.Col([
                                        html.Div([
                                            html.Span("■ ", style={"color": "#2ca02c", "fontSize": "20px"}),
                                            html.Strong("Stable"),
                                            html.P("Basin core persists across all N values", className="mb-0"),
                                        ])
                                    ], md=4),
                                    dbc.Col([
                                        html.Div([
                                            html.Span("■ ", style={"color": "#ff7f0e", "fontSize": "20px"}),
                                            html.Strong("Moderate"),
                                            html.P("Some fluctuation in membership", className="mb-0"),
                                        ])
                                    ], md=4),
                                    dbc.Col([
                                        html.Div([
                                            html.Span("■ ", style={"color": "#d62728", "fontSize": "20px"}),
                                            html.Strong("Fragile"),
                                            html.P("Major restructuring across N", className="mb-0"),
                                        ])
                                    ], md=4),
                                ])
                            ])
                        ])
                    ])
                ], className="mt-3"),
            ], label="Stability", tab_id="tab-stability"),

            # Validation Tab
            dbc.Tab([
                dbc.Row([
                    dbc.Col([
                        html.H4("Theory Validation Results", className="mb-3"),
                        html.Div(id="validation-container")
                    ])
                ]),
                dbc.Row([
                    dbc.Col([
                        dbc.Card([
                            dbc.CardHeader("Summary"),
                            dbc.CardBody([
                                html.P([
                                    "The tunneling analysis validated 3 of 4 theoretical predictions. ",
                                    "The ", html.Strong("hub hypothesis was refuted"), " - tunnel nodes ",
                                    "actually have slightly ", html.Em("lower"), " out-degree than average. ",
                                    "This suggests tunneling is about ", html.Strong("position (depth)"),
                                    " rather than ", html.Strong("connectivity (degree)"), "."
                                ])
                            ])
                        ])
                    ])
                ], className="mt-3"),
            ], label="Validation", tab_id="tab-validation"),
        ], id="tabs", active_tab="tab-overview"),

        # Footer
        html.Hr(),
        html.Footer([
            html.P([
                "Data: Wikipedia English (enwiki-20251220) | ",
                "Analysis: N-Link Rule Theory"
            ], className="text-muted text-center")
        ]),

    ], fluid=True, className="p-4")


# ============================================================================
# App Initialization
# ============================================================================

# Load data at startup
semantic_model = load_semantic_model()
flows_df = load_basin_flows()
tunnel_df = load_tunnel_ranking()
stability_df = load_basin_stability()
mechanisms_df = load_mechanisms()
validation_df = load_validation()

# Create Dash app
app = dash.Dash(
    __name__,
    external_stylesheets=[dbc.themes.BOOTSTRAP],
    title="Tunneling Dashboard"
)

app.layout = create_layout(semantic_model)


# ============================================================================
# Callbacks
# ============================================================================

@callback(
    Output("mechanism-pie", "figure"),
    Output("scatter-plot", "figure"),
    Output("type-bar", "figure"),
    Input("tabs", "active_tab"),
)
def update_overview_charts(active_tab):
    """Update overview charts."""
    return create_overview_charts(semantic_model, mechanisms_df, tunnel_df)


@callback(
    Output("sankey-diagram", "figure"),
    Input("tabs", "active_tab"),
)
def update_sankey(active_tab):
    """Update Sankey diagram."""
    return create_sankey_figure(flows_df)


@callback(
    Output("tunnel-table", "data"),
    Input("type-filter", "value"),
    Input("score-slider", "value"),
)
def update_tunnel_table(type_filter, min_score):
    """Filter tunnel nodes table."""
    df = tunnel_df.copy()

    if type_filter != "all":
        df = df[df["tunnel_type"] == type_filter]

    if min_score > 0:
        df = df[df["tunnel_score"] >= min_score]

    # Add rank
    df = df.reset_index(drop=True)
    df["rank"] = range(1, len(df) + 1)

    return df[["rank", "page_title", "tunnel_score", "n_basins_bridged", "mean_depth", "tunnel_type"]].to_dict("records")


@callback(
    Output("stability-chart", "figure"),
    Input("tabs", "active_tab"),
)
def update_stability(active_tab):
    """Update stability chart."""
    return create_stability_chart(stability_df)


@callback(
    Output("validation-container", "children"),
    Input("tabs", "active_tab"),
)
def update_validation(active_tab):
    """Update validation table."""
    return create_validation_table(validation_df)


# ============================================================================
# Main
# ============================================================================

def main():
    parser = argparse.ArgumentParser(description="Run tunneling dashboard")
    parser.add_argument("--port", type=int, default=8060, help="Port to run on")
    parser.add_argument("--debug", action="store_true", help="Run in debug mode")
    args = parser.parse_args()

    print("=" * 70)
    print("Tunneling Analysis Dashboard")
    print("=" * 70)
    print()
    print(f"Starting server on http://localhost:{args.port}")
    print("Press Ctrl+C to stop")
    print()

    app.run(debug=args.debug, port=args.port)


if __name__ == "__main__":
    main()
