#!/usr/bin/env python3
"""Cross-N Basin Comparison Dashboard.

Interactive side-by-side comparison of basin properties across N values (N=3-10).
Designed for exploring how basins evolve with changing N, including size, depth,
and tunneling behavior.

Tabs
----
1) Basin Size Comparison
   - Interactive bar/line chart comparing basin sizes across N
   - Select specific cycles to compare
   - Log/linear scale toggle

2) Depth Analysis
   - Violin plots of depth distribution per N
   - Mean/median/max depth comparison
   - Per-cycle breakdown

3) Phase Transition Explorer
   - Animated or slider-based N transition
   - Shows how basins grow/collapse across N
   - Highlights N=5 peak

4) Tunneling Heatmap
   - Which pages change basins between adjacent N values
   - Transition matrix visualization
   - Drill-down to specific pages

Run (repo root)
---------------
  python n-link-analysis/viz/dash-cross-n-comparison.py --port 8062

Data Dependencies
-----------------
  - data/wikipedia/processed/multiplex/multiplex_basin_assignments.parquet
  - data/wikipedia/processed/multiplex/tunnel_classification.tsv
  - data/wikipedia/processed/multiplex/basin_flows.tsv
"""

from __future__ import annotations

import argparse
from pathlib import Path

import dash
from dash import dcc, html, Input, Output, callback
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

# Cache loaded data
_DATA_CACHE = {}


def load_basin_assignments() -> pd.DataFrame:
    """Load the unified basin assignments across all N values."""
    if "basin" in _DATA_CACHE:
        return _DATA_CACHE["basin"]

    path = MULTIPLEX_DIR / "multiplex_basin_assignments.parquet"
    if not path.exists():
        return pd.DataFrame()

    df = pd.read_parquet(path)
    _DATA_CACHE["basin"] = df
    return df


def load_basin_flows() -> pd.DataFrame:
    """Load cross-basin flow data."""
    if "flows" in _DATA_CACHE:
        return _DATA_CACHE["flows"]

    path = MULTIPLEX_DIR / "basin_flows.tsv"
    if not path.exists():
        return pd.DataFrame()

    df = pd.read_csv(path, sep="\t")
    _DATA_CACHE["flows"] = df
    return df


def load_tunnel_classification() -> pd.DataFrame:
    """Load tunnel node classification."""
    if "tunnel" in _DATA_CACHE:
        return _DATA_CACHE["tunnel"]

    path = MULTIPLEX_DIR / "tunnel_classification.tsv"
    if not path.exists():
        return pd.DataFrame()

    df = pd.read_csv(path, sep="\t")
    _DATA_CACHE["tunnel"] = df
    return df


def get_basin_stats() -> pd.DataFrame:
    """Compute basin statistics by N and cycle."""
    df = load_basin_assignments()
    if df.empty:
        return pd.DataFrame()

    # Filter out tunneling entries for main stats
    df_main = df[~df["cycle_key"].str.contains("_tunneling", na=False)]

    stats = df_main.groupby(["N", "cycle_key"]).agg(
        size=("page_id", "count"),
        mean_depth=("depth", "mean"),
        median_depth=("depth", "median"),
        max_depth=("depth", "max"),
    ).reset_index()

    # Extract base cycle name
    stats["cycle"] = stats["cycle_key"].str.split("__").str[0]

    return stats


def get_unique_cycles() -> list[str]:
    """Get list of unique cycle names."""
    stats = get_basin_stats()
    if stats.empty:
        return []
    return sorted(stats["cycle"].unique().tolist())


def get_n_values() -> list[int]:
    """Get list of available N values."""
    df = load_basin_assignments()
    if df.empty:
        return list(range(3, 11))
    return sorted(df["N"].unique().tolist())


# ============================================================================
# App Layout
# ============================================================================

app = dash.Dash(
    __name__,
    external_stylesheets=[dbc.themes.FLATLY],
    suppress_callback_exceptions=True,
)

app.title = "Cross-N Basin Comparison"


def create_layout():
    """Create the main app layout."""
    cycles = get_unique_cycles()
    n_values = get_n_values()

    return dbc.Container([
        # Header
        dbc.Row([
            dbc.Col([
                html.H1("Cross-N Basin Comparison", className="text-primary mb-2"),
                html.P(
                    "Compare basin properties across N values (N=3-10)",
                    className="text-muted"
                ),
            ])
        ], className="my-4"),

        # Main tabs
        dbc.Tabs([
            dbc.Tab(label="Basin Size", tab_id="tab-size"),
            dbc.Tab(label="Depth Analysis", tab_id="tab-depth"),
            dbc.Tab(label="Phase Transition", tab_id="tab-phase"),
            dbc.Tab(label="Tunneling Flows", tab_id="tab-flows"),
        ], id="tabs", active_tab="tab-size", className="mb-4"),

        # Tab content
        html.Div(id="tab-content"),

    ], fluid=True)


app.layout = create_layout


# ============================================================================
# Tab: Basin Size Comparison
# ============================================================================

def create_size_tab():
    """Create basin size comparison tab."""
    cycles = get_unique_cycles()

    return dbc.Container([
        dbc.Row([
            dbc.Col([
                html.Label("Select Cycles to Compare:"),
                dcc.Dropdown(
                    id="size-cycle-select",
                    options=[{"label": c.replace("_", " "), "value": c} for c in cycles],
                    value=cycles[:6] if len(cycles) >= 6 else cycles,
                    multi=True,
                ),
            ], md=8),
            dbc.Col([
                html.Label("Scale:"),
                dbc.RadioItems(
                    id="size-scale",
                    options=[
                        {"label": "Log", "value": "log"},
                        {"label": "Linear", "value": "linear"},
                    ],
                    value="log",
                    inline=True,
                ),
            ], md=4),
        ], className="mb-4"),

        dbc.Row([
            dbc.Col([
                dcc.Graph(id="size-chart", style={"height": "500px"}),
            ]),
        ]),

        dbc.Row([
            dbc.Col([
                html.H5("Basin Size Table"),
                html.Div(id="size-table"),
            ]),
        ], className="mt-4"),
    ])


@callback(
    Output("size-chart", "figure"),
    Input("size-cycle-select", "value"),
    Input("size-scale", "value"),
)
def update_size_chart(selected_cycles, scale):
    """Update the basin size comparison chart."""
    stats = get_basin_stats()
    if stats.empty or not selected_cycles:
        return go.Figure()

    # Filter to selected cycles
    df = stats[stats["cycle"].isin(selected_cycles)]

    fig = px.line(
        df,
        x="N",
        y="size",
        color="cycle",
        markers=True,
        title="Basin Size by N Value",
        labels={"N": "N (link position)", "size": "Basin Size (pages)", "cycle": "Cycle"},
    )

    fig.update_layout(
        yaxis_type=scale,
        xaxis=dict(tickmode="linear", tick0=3, dtick=1),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="center", x=0.5),
        template="plotly_white",
    )

    # Add N=5 annotation
    fig.add_vline(x=5, line_dash="dash", line_color="gray", opacity=0.5)
    fig.add_annotation(x=5, y=1.05, yref="paper", text="N=5 Peak", showarrow=False)

    return fig


@callback(
    Output("size-table", "children"),
    Input("size-cycle-select", "value"),
)
def update_size_table(selected_cycles):
    """Update the basin size summary table."""
    stats = get_basin_stats()
    if stats.empty or not selected_cycles:
        return html.P("No data available")

    df = stats[stats["cycle"].isin(selected_cycles)]

    # Pivot to show N values as columns
    pivot = df.pivot_table(
        index="cycle",
        columns="N",
        values="size",
        aggfunc="sum",
    ).fillna(0).astype(int)

    # Add collapse factor (N=5 / N=10 if both exist)
    if 5 in pivot.columns and 10 in pivot.columns:
        pivot["Collapse (N5/N10)"] = (pivot[5] / pivot[10].replace(0, np.nan)).round(1)

    pivot = pivot.reset_index()

    return dbc.Table.from_dataframe(
        pivot,
        striped=True,
        bordered=True,
        hover=True,
        responsive=True,
        className="small",
    )


# ============================================================================
# Tab: Depth Analysis
# ============================================================================

def create_depth_tab():
    """Create depth analysis tab."""
    cycles = get_unique_cycles()

    return dbc.Container([
        dbc.Row([
            dbc.Col([
                html.Label("Select Cycle:"),
                dcc.Dropdown(
                    id="depth-cycle-select",
                    options=[{"label": c.replace("_", " "), "value": c} for c in cycles],
                    value=cycles[0] if cycles else None,
                ),
            ], md=6),
        ], className="mb-4"),

        dbc.Row([
            dbc.Col([
                dcc.Graph(id="depth-violin", style={"height": "400px"}),
            ], md=6),
            dbc.Col([
                dcc.Graph(id="depth-stats", style={"height": "400px"}),
            ], md=6),
        ]),

        dbc.Row([
            dbc.Col([
                dcc.Graph(id="depth-comparison", style={"height": "400px"}),
            ]),
        ], className="mt-4"),
    ])


@callback(
    Output("depth-violin", "figure"),
    Output("depth-stats", "figure"),
    Input("depth-cycle-select", "value"),
)
def update_depth_charts(selected_cycle):
    """Update depth analysis charts."""
    df = load_basin_assignments()
    if df.empty or not selected_cycle:
        return go.Figure(), go.Figure()

    # Filter to selected cycle (match on base name)
    df_cycle = df[df["cycle_key"].str.startswith(selected_cycle)]

    if df_cycle.empty:
        return go.Figure(), go.Figure()

    # Violin plot of depth by N
    fig_violin = px.violin(
        df_cycle,
        x="N",
        y="depth",
        box=True,
        title=f"Depth Distribution: {selected_cycle.replace('_', ' ')}",
    )
    fig_violin.update_layout(template="plotly_white")

    # Stats chart (mean, median, max)
    stats = df_cycle.groupby("N").agg(
        mean_depth=("depth", "mean"),
        median_depth=("depth", "median"),
        max_depth=("depth", "max"),
    ).reset_index()

    fig_stats = go.Figure()
    fig_stats.add_trace(go.Bar(x=stats["N"], y=stats["max_depth"], name="Max", marker_color="#1f77b4"))
    fig_stats.add_trace(go.Scatter(x=stats["N"], y=stats["mean_depth"], mode="lines+markers", name="Mean", line=dict(color="#ff7f0e")))
    fig_stats.add_trace(go.Scatter(x=stats["N"], y=stats["median_depth"], mode="lines+markers", name="Median", line=dict(color="#2ca02c")))

    fig_stats.update_layout(
        title=f"Depth Statistics: {selected_cycle.replace('_', ' ')}",
        xaxis=dict(title="N", tickmode="linear"),
        yaxis=dict(title="Depth"),
        barmode="overlay",
        template="plotly_white",
    )

    return fig_violin, fig_stats


@callback(
    Output("depth-comparison", "figure"),
    Input("depth-cycle-select", "value"),
)
def update_depth_comparison(selected_cycle):
    """Update cross-cycle depth comparison."""
    stats = get_basin_stats()
    if stats.empty:
        return go.Figure()

    fig = px.scatter(
        stats,
        x="mean_depth",
        y="size",
        color="cycle",
        size="max_depth",
        hover_data=["N"],
        title="Basin Size vs Mean Depth (all cycles, all N)",
        labels={"mean_depth": "Mean Depth", "size": "Basin Size", "cycle": "Cycle"},
    )

    fig.update_layout(
        yaxis_type="log",
        template="plotly_white",
    )

    return fig


# ============================================================================
# Tab: Phase Transition
# ============================================================================

def create_phase_tab():
    """Create phase transition explorer tab."""
    n_values = get_n_values()

    return dbc.Container([
        dbc.Row([
            dbc.Col([
                html.Label("Select N Value:"),
                dcc.Slider(
                    id="phase-n-slider",
                    min=min(n_values) if n_values else 3,
                    max=max(n_values) if n_values else 10,
                    step=1,
                    value=5,
                    marks={n: str(n) for n in n_values},
                ),
            ], md=8),
            dbc.Col([
                html.Div(id="phase-n-info", className="text-center"),
            ], md=4),
        ], className="mb-4"),

        dbc.Row([
            dbc.Col([
                dcc.Graph(id="phase-chart", style={"height": "500px"}),
            ]),
        ]),

        dbc.Row([
            dbc.Col([
                html.H5("Cycle Statistics at Selected N"),
                html.Div(id="phase-table"),
            ]),
        ], className="mt-4"),
    ])


@callback(
    Output("phase-chart", "figure"),
    Output("phase-n-info", "children"),
    Output("phase-table", "children"),
    Input("phase-n-slider", "value"),
)
def update_phase_charts(selected_n):
    """Update phase transition charts."""
    stats = get_basin_stats()
    if stats.empty:
        return go.Figure(), "", html.P("No data")

    # Filter to selected N
    df_n = stats[stats["N"] == selected_n].sort_values("size", ascending=False)

    # Bar chart of basin sizes at this N
    fig = px.bar(
        df_n,
        x="cycle",
        y="size",
        color="cycle",
        title=f"Basin Sizes at N={selected_n}",
        labels={"cycle": "Cycle", "size": "Basin Size"},
    )

    fig.update_layout(
        yaxis_type="log",
        showlegend=False,
        xaxis_tickangle=45,
        template="plotly_white",
    )

    # Info box
    total_pages = df_n["size"].sum()
    n_cycles = len(df_n)
    info = dbc.Card([
        dbc.CardBody([
            html.H3(f"N = {selected_n}", className="text-primary"),
            html.P(f"Total: {total_pages:,} pages"),
            html.P(f"Cycles: {n_cycles}"),
        ])
    ])

    # Table
    table_df = df_n[["cycle", "size", "mean_depth", "max_depth"]].copy()
    table_df["mean_depth"] = table_df["mean_depth"].round(1)
    table_df.columns = ["Cycle", "Size", "Mean Depth", "Max Depth"]

    table = dbc.Table.from_dataframe(
        table_df,
        striped=True,
        bordered=True,
        hover=True,
        responsive=True,
    )

    return fig, info, table


# ============================================================================
# Tab: Tunneling Flows
# ============================================================================

def create_flows_tab():
    """Create tunneling flows tab."""
    return dbc.Container([
        dbc.Row([
            dbc.Col([
                dcc.Graph(id="flows-sankey", style={"height": "600px"}),
            ]),
        ]),

        dbc.Row([
            dbc.Col([
                html.H5("Flow Details"),
                html.Div(id="flows-table"),
            ]),
        ], className="mt-4"),
    ])


@callback(
    Output("flows-sankey", "figure"),
    Output("flows-table", "children"),
    Input("tabs", "active_tab"),
)
def update_flows_charts(active_tab):
    """Update tunneling flows visualization."""
    if active_tab != "tab-flows":
        return go.Figure(), html.P("")

    flows = load_basin_flows()
    if flows.empty:
        return go.Figure(), html.P("No flow data available")

    # Build Sankey diagram
    # Create unique list of all basins
    all_basins = list(set(flows["from_basin"].tolist() + flows["to_basin"].tolist()))
    basin_idx = {b: i for i, b in enumerate(all_basins)}

    # Shorten basin names for display
    labels = [b.split("__")[0][:20] for b in all_basins]

    fig = go.Figure(go.Sankey(
        node=dict(
            pad=15,
            thickness=20,
            line=dict(color="black", width=0.5),
            label=labels,
            color="rgba(31, 119, 180, 0.8)",
        ),
        link=dict(
            source=[basin_idx[b] for b in flows["from_basin"]],
            target=[basin_idx[b] for b in flows["to_basin"]],
            value=flows["count"],
            color="rgba(31, 119, 180, 0.3)",
        ),
    ))

    fig.update_layout(
        title="Cross-Basin Tunneling Flows",
        template="plotly_white",
    )

    # Table
    table_df = flows[["from_basin", "to_basin", "count", "from_n", "to_n"]].copy()
    table_df["from_basin"] = table_df["from_basin"].str.split("__").str[0]
    table_df["to_basin"] = table_df["to_basin"].str.split("__").str[0]
    table_df = table_df.sort_values("count", ascending=False).head(20)
    table_df.columns = ["From", "To", "Pages", "From N", "To N"]

    table = dbc.Table.from_dataframe(
        table_df,
        striped=True,
        bordered=True,
        hover=True,
        responsive=True,
    )

    return fig, table


# ============================================================================
# Tab Router
# ============================================================================

@callback(
    Output("tab-content", "children"),
    Input("tabs", "active_tab"),
)
def render_tab(active_tab):
    """Render the active tab content."""
    if active_tab == "tab-size":
        return create_size_tab()
    elif active_tab == "tab-depth":
        return create_depth_tab()
    elif active_tab == "tab-phase":
        return create_phase_tab()
    elif active_tab == "tab-flows":
        return create_flows_tab()
    return html.P("Select a tab")


# ============================================================================
# Main
# ============================================================================

def main() -> int:
    parser = argparse.ArgumentParser(description="Cross-N Basin Comparison Dashboard")
    parser.add_argument("--port", type=int, default=8062, help="Port to run on")
    parser.add_argument("--debug", action="store_true", help="Enable debug mode")
    args = parser.parse_args()

    print(f"\n{'='*60}")
    print("Cross-N Basin Comparison Dashboard")
    print(f"{'='*60}")
    print(f"URL: http://127.0.0.1:{args.port}")
    print(f"{'='*60}\n")

    # Pre-load data
    print("Loading data...")
    df = load_basin_assignments()
    if df.empty:
        print("WARNING: No basin assignment data found!")
    else:
        print(f"  Loaded {len(df):,} basin assignments")

    flows = load_basin_flows()
    print(f"  Loaded {len(flows)} cross-basin flows")

    print("\nStarting server...")
    app.run(debug=args.debug, port=args.port)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
