#!/usr/bin/env python3
"""Interactive path tracer for exploring tunnel node behavior across N values.

A Dash application that allows users to:
1. Search for a Wikipedia page by title or ID
2. View its basin membership across all N values (3-10)
3. Visualize the tunneling timeline
4. See depth and entry point information

Usage:
    python path-tracer-tool.py [--port PORT]

The tracer will be available at http://localhost:PORT
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Optional

import pandas as pd
import numpy as np
import plotly.graph_objects as go

try:
    import dash
    from dash import dcc, html, callback, Input, Output, State
    import dash_bootstrap_components as dbc
except ImportError:
    print("Error: dash and dash-bootstrap-components required")
    print("Install with: pip install dash dash-bootstrap-components")
    exit(1)

REPO_ROOT = Path(__file__).resolve().parents[3]
MULTIPLEX_DIR = REPO_ROOT / "data" / "wikipedia" / "processed" / "multiplex"

# Basin colors
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
    if pd.isna(basin) or basin == "":
        return "N/A"
    for key, name in BASIN_SHORT_NAMES.items():
        if key in basin or basin in key:
            return name
    return basin.split("__")[0][:15] if "__" in basin else basin[:15]


def get_basin_color(basin: str) -> str:
    """Get color for a basin."""
    if pd.isna(basin) or basin == "":
        return "#cccccc"
    for key, color in BASIN_COLORS.items():
        if key in basin or basin in key:
            return color
    return "#7f7f7f"


# ============================================================================
# Data Loading
# ============================================================================

def load_tunnel_nodes() -> pd.DataFrame:
    """Load tunnel nodes with basin assignments."""
    path = MULTIPLEX_DIR / "tunnel_frequency_ranking.tsv"
    if not path.exists():
        return pd.DataFrame()
    return pd.read_csv(path, sep="\t")


def load_multiplex_assignments() -> pd.DataFrame:
    """Load full multiplex basin assignments."""
    path = MULTIPLEX_DIR / "multiplex_basin_assignments.parquet"
    if not path.exists():
        return pd.DataFrame()
    return pd.read_parquet(path)


# Load data at module level
print("Loading data...")
tunnel_df = load_tunnel_nodes()
multiplex_df = load_multiplex_assignments()

# Build lookup dictionaries
title_to_id = {}
id_to_title = {}
if not tunnel_df.empty:
    for _, row in tunnel_df.iterrows():
        page_id = row["page_id"]
        title = row.get("page_title", "")
        if pd.notna(title) and title != "":
            title_to_id[title.lower()] = page_id
            id_to_title[page_id] = title

print(f"  Loaded {len(tunnel_df):,} tunnel nodes")
print(f"  Loaded {len(multiplex_df):,} multiplex assignments")


def search_pages(query: str, limit: int = 20) -> list[dict]:
    """Search for pages by title or ID."""
    results = []
    query_lower = query.lower().strip()

    if not query_lower:
        return results

    # Try as page ID first
    try:
        page_id = int(query_lower)
        if page_id in id_to_title:
            results.append({
                "page_id": page_id,
                "title": id_to_title[page_id],
            })
    except ValueError:
        pass

    # Search by title prefix
    for title, page_id in title_to_id.items():
        if query_lower in title:
            results.append({
                "page_id": page_id,
                "title": id_to_title.get(page_id, f"page_{page_id}"),
            })
            if len(results) >= limit:
                break

    return results


def get_page_trace(page_id: int) -> Optional[dict]:
    """Get basin membership trace for a page across all N values."""
    # Get from tunnel_df first (has more info)
    tunnel_row = tunnel_df[tunnel_df["page_id"] == page_id]

    if tunnel_row.empty:
        return None

    row = tunnel_row.iloc[0]

    # Get per-N assignments from multiplex_df
    page_multiplex = multiplex_df[multiplex_df["page_id"] == page_id]

    n_basins = {}
    n_depths = {}

    if not page_multiplex.empty:
        for _, mrow in page_multiplex.iterrows():
            n = mrow["N"]
            n_basins[n] = mrow.get("cycle_key", "")
            n_depths[n] = mrow.get("depth", 0)

    # Build trace info
    trace = {
        "page_id": page_id,
        "title": row.get("page_title", f"page_{page_id}"),
        "tunnel_score": row.get("tunnel_score", 0),
        "tunnel_type": row.get("tunnel_type", ""),
        "n_basins_bridged": row.get("n_basins_bridged", 0),
        "n_transitions": row.get("n_transitions", 0),
        "mean_depth": row.get("mean_depth", 0),
        "basin_list": row.get("basin_list", ""),
        "stable_ranges": row.get("stable_ranges", ""),
        "n_values": {},
    }

    # Add per-N info
    for n in range(3, 11):
        basin = n_basins.get(n, "")
        depth = n_depths.get(n, None)
        trace["n_values"][n] = {
            "basin": basin,
            "basin_short": get_short_name(basin),
            "depth": depth,
            "color": get_basin_color(basin),
        }

    return trace


def create_timeline_figure(trace: dict) -> go.Figure:
    """Create timeline visualization of basin membership."""
    if not trace:
        fig = go.Figure()
        fig.add_annotation(text="No trace data", showarrow=False)
        return fig

    n_values = list(range(3, 11))
    basins = [trace["n_values"][n]["basin_short"] for n in n_values]
    colors = [trace["n_values"][n]["color"] for n in n_values]
    depths = [trace["n_values"][n]["depth"] for n in n_values]

    # Create horizontal bar chart showing basin membership at each N
    fig = go.Figure()

    for i, n in enumerate(n_values):
        fig.add_trace(go.Bar(
            y=[f"N={n}"],
            x=[1],
            orientation="h",
            marker_color=colors[i],
            text=[basins[i]],
            textposition="inside",
            textfont=dict(color="white", size=14),
            hovertemplate=(
                f"<b>N={n}</b><br>"
                f"Basin: {basins[i]}<br>"
                f"Depth: {depths[i]}<extra></extra>"
            ),
            showlegend=False,
        ))

    # Add transition markers
    for i in range(len(n_values) - 1):
        if basins[i] != basins[i + 1]:
            # Add transition indicator
            fig.add_annotation(
                x=1.05,
                y=i + 0.5,
                text="↓ TUNNEL",
                showarrow=False,
                font=dict(color="#d62728", size=12, weight="bold"),
                xanchor="left",
            )

    fig.update_layout(
        title=f"Basin Membership Timeline: {trace['title']}",
        xaxis=dict(visible=False, range=[0, 1.3]),
        yaxis=dict(autorange="reversed"),
        height=400,
        margin=dict(t=60, b=20, l=60, r=80),
        bargap=0.3,
    )

    return fig


def create_depth_figure(trace: dict) -> go.Figure:
    """Create depth visualization across N values."""
    if not trace:
        fig = go.Figure()
        fig.add_annotation(text="No trace data", showarrow=False)
        return fig

    n_values = list(range(3, 11))
    depths = [trace["n_values"][n]["depth"] for n in n_values]
    colors = [trace["n_values"][n]["color"] for n in n_values]

    # Filter out None depths
    valid_data = [(n, d, c) for n, d, c in zip(n_values, depths, colors) if d is not None]

    if not valid_data:
        fig = go.Figure()
        fig.add_annotation(text="No depth data available", showarrow=False)
        return fig

    ns, ds, cs = zip(*valid_data)

    fig = go.Figure(data=[
        go.Scatter(
            x=[f"N={n}" for n in ns],
            y=ds,
            mode="lines+markers",
            marker=dict(size=12, color=list(cs)),
            line=dict(color="#666", width=2),
            hovertemplate="N=%{x}<br>Depth: %{y}<extra></extra>",
        )
    ])

    fig.update_layout(
        title="Depth Across N Values",
        xaxis_title="N Value",
        yaxis_title="Depth from Cycle",
        height=250,
        margin=dict(t=60, b=50, l=60, r=20),
    )

    return fig


# ============================================================================
# App Layout
# ============================================================================

app = dash.Dash(
    __name__,
    external_stylesheets=[dbc.themes.BOOTSTRAP],
    title="Path Tracer"
)

app.layout = dbc.Container([
    # Header
    dbc.Row([
        dbc.Col([
            html.H1("Tunnel Path Tracer", className="mb-2"),
            html.P(
                "Explore how Wikipedia pages move between basins across N values",
                className="text-muted"
            ),
        ])
    ], className="mb-4"),

    # Search Row
    dbc.Row([
        dbc.Col([
            dbc.Card([
                dbc.CardBody([
                    dbc.Row([
                        dbc.Col([
                            dbc.Label("Search for a Wikipedia page:"),
                            dbc.InputGroup([
                                dbc.Input(
                                    id="search-input",
                                    type="text",
                                    placeholder="Enter page title or ID...",
                                    debounce=True,
                                ),
                                dbc.Button("Trace", id="trace-btn", color="primary"),
                            ]),
                        ], md=8),
                        dbc.Col([
                            dbc.Label("Quick examples:"),
                            dbc.ButtonGroup([
                                dbc.Button("Kidder_family", id="ex1-btn", color="secondary", size="sm", className="me-1"),
                                dbc.Button("Massachusetts", id="ex2-btn", color="secondary", size="sm"),
                            ]),
                        ], md=4),
                    ]),
                ])
            ])
        ])
    ], className="mb-4"),

    # Search Results
    dbc.Row([
        dbc.Col([
            html.Div(id="search-results")
        ])
    ], className="mb-4"),

    # Trace Display
    dbc.Row([
        dbc.Col([
            html.Div(id="trace-display")
        ])
    ]),

    # Footer
    html.Hr(),
    html.Footer([
        html.P("Wikipedia N-Link Rule Analysis | Path Tracer Tool", className="text-muted text-center")
    ]),

], fluid=True, className="p-4")


# ============================================================================
# Callbacks
# ============================================================================

@callback(
    Output("search-results", "children"),
    Input("search-input", "value"),
)
def update_search_results(query):
    """Show matching pages."""
    if not query or len(query) < 2:
        return ""

    results = search_pages(query)

    if not results:
        return dbc.Alert("No matching pages found", color="warning")

    buttons = []
    for r in results[:10]:
        buttons.append(
            dbc.Button(
                f"{r['title']} (ID: {r['page_id']})",
                id={"type": "result-btn", "page_id": r["page_id"]},
                color="light",
                className="me-2 mb-2",
                size="sm",
            )
        )

    return html.Div([
        html.P(f"Found {len(results)} matching pages:", className="mb-2"),
        html.Div(buttons),
    ])


@callback(
    Output("trace-display", "children"),
    Input("trace-btn", "n_clicks"),
    Input("ex1-btn", "n_clicks"),
    Input("ex2-btn", "n_clicks"),
    State("search-input", "value"),
    prevent_initial_call=True,
)
def show_trace(trace_clicks, ex1_clicks, ex2_clicks, search_value):
    """Display trace for selected page."""
    ctx = dash.callback_context
    if not ctx.triggered:
        return ""

    trigger_id = ctx.triggered[0]["prop_id"].split(".")[0]

    # Handle example buttons
    if trigger_id == "ex1-btn":
        page_id = 14758846  # Kidder_family
    elif trigger_id == "ex2-btn":
        # Search for Massachusetts
        results = search_pages("massachusetts")
        if results:
            page_id = results[0]["page_id"]
        else:
            return dbc.Alert("Massachusetts not found", color="warning")
    else:
        # Use search value
        if not search_value:
            return dbc.Alert("Please enter a search term", color="info")

        results = search_pages(search_value)
        if not results:
            return dbc.Alert("No matching page found", color="warning")
        page_id = results[0]["page_id"]

    # Get trace
    trace = get_page_trace(page_id)

    if not trace:
        return dbc.Alert(f"Page ID {page_id} not found in tunnel nodes", color="warning")

    # Build display
    return dbc.Card([
        dbc.CardHeader([
            html.H4([
                html.A(
                    trace["title"],
                    href=f"https://en.wikipedia.org/wiki/{trace['title'].replace(' ', '_')}",
                    target="_blank",
                ),
                html.Small(f" (ID: {trace['page_id']})", className="text-muted"),
            ]),
        ]),
        dbc.CardBody([
            # Stats row
            dbc.Row([
                dbc.Col([
                    html.Div([
                        html.Strong("Tunnel Score: "),
                        html.Span(f"{trace['tunnel_score']:.2f}"),
                    ])
                ], md=3),
                dbc.Col([
                    html.Div([
                        html.Strong("Type: "),
                        html.Span(
                            trace["tunnel_type"],
                            className=f"badge bg-{'success' if trace['tunnel_type'] == 'progressive' else 'warning'}"
                        ),
                    ])
                ], md=3),
                dbc.Col([
                    html.Div([
                        html.Strong("Basins Bridged: "),
                        html.Span(str(trace["n_basins_bridged"])),
                    ])
                ], md=3),
                dbc.Col([
                    html.Div([
                        html.Strong("Mean Depth: "),
                        html.Span(f"{trace['mean_depth']:.1f}"),
                    ])
                ], md=3),
            ], className="mb-4"),

            # Timeline chart
            dcc.Graph(figure=create_timeline_figure(trace)),

            # Depth chart
            dcc.Graph(figure=create_depth_figure(trace)),

            # Details table
            html.H5("Basin Details by N", className="mt-4 mb-3"),
            dbc.Table([
                html.Thead([
                    html.Tr([
                        html.Th("N Value"),
                        html.Th("Basin"),
                        html.Th("Depth"),
                    ])
                ]),
                html.Tbody([
                    html.Tr([
                        html.Td(f"N={n}"),
                        html.Td([
                            html.Span(
                                "■ ",
                                style={"color": trace["n_values"][n]["color"]}
                            ),
                            trace["n_values"][n]["basin_short"],
                        ]),
                        html.Td(str(trace["n_values"][n]["depth"]) if trace["n_values"][n]["depth"] else "N/A"),
                    ])
                    for n in range(3, 11)
                ]),
            ], bordered=True, hover=True),
        ])
    ])


# ============================================================================
# Main
# ============================================================================

def main():
    parser = argparse.ArgumentParser(description="Run path tracer tool")
    parser.add_argument("--port", type=int, default=8061, help="Port to run on")
    parser.add_argument("--debug", action="store_true", help="Run in debug mode")
    args = parser.parse_args()

    print("=" * 70)
    print("Tunnel Path Tracer Tool")
    print("=" * 70)
    print()
    print(f"Starting server on http://localhost:{args.port}")
    print("Press Ctrl+C to stop")
    print()

    app.run(debug=args.debug, port=args.port)


if __name__ == "__main__":
    main()
