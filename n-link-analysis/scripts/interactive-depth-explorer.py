#!/usr/bin/env python3
"""Interactive depth structure explorer using Plotly Dash.

This creates a web-based UI for exploring basin mass vs depth relationships
with interactive zoom, filtering, and multi-scale visualization.

Features:
- Interactive log-log scatter plot with zoom/pan
- Cycle selection filters
- N value range sliders
- Linked overview + detail views
- Power-law fit overlay with adjustable α
- Data table with sorting
- Export views as PNG
"""

import pandas as pd
import numpy as np
from pathlib import Path
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
import dash
from dash import dcc, html, Input, Output, State
import dash_bootstrap_components as dbc

# ============================================================================
# Data Loading
# ============================================================================

ANALYSIS_DIR = Path("data/wikipedia/processed/analysis")

def load_all_data():
    """Load all entry breadth data files with max_depth."""
    all_data = []
    for n in [3, 4, 5, 6, 7]:
        file_path = ANALYSIS_DIR / f"entry_breadth_n={n}_full_analysis_2025_12_31.tsv"
        df = pd.read_csv(file_path, sep="\t")
        all_data.append(df)

    data = pd.concat(all_data, ignore_index=True)

    # Add computed columns
    data['log_depth'] = np.log10(data['max_depth'])
    data['log_mass'] = np.log10(data['basin_mass'])
    data['predicted_mass_2.0'] = data['entry_breadth'] * data['max_depth']**2.0
    data['predicted_mass_2.5'] = data['entry_breadth'] * data['max_depth']**2.5
    data['predicted_mass_3.0'] = data['entry_breadth'] * data['max_depth']**3.0

    return data

def load_fit_parameters():
    """Load power-law fit parameters."""
    return pd.read_csv(
        ANALYSIS_DIR / "depth_exploration/power_law_fit_parameters.tsv",
        sep="\t"
    )

# Load data
print("Loading data...")
data = load_all_data()
fit_params = load_fit_parameters()
print(f"Loaded {len(data)} data points from {data['cycle_label'].nunique()} cycles")

# ============================================================================
# Dash App Setup
# ============================================================================

app = dash.Dash(
    __name__,
    external_stylesheets=[dbc.themes.BOOTSTRAP],
    suppress_callback_exceptions=True
)

app.title = "Depth Structure Explorer"

# ============================================================================
# Layout Components
# ============================================================================

def create_header():
    """Create header with title and description."""
    return dbc.Container([
        html.H1("Depth Structure Explorer", className="text-center my-4"),
        html.P(
            "Interactive exploration of basin mass vs depth power-law relationships",
            className="text-center text-muted mb-4"
        ),
        html.Hr()
    ], fluid=True)

def create_controls():
    """Create control panel for filtering and adjusting views."""
    cycles = sorted(data['cycle_label'].unique())

    return dbc.Card([
        dbc.CardHeader(html.H5("Controls")),
        dbc.CardBody([
            # Cycle selection
            html.Label("Select Cycles:", className="fw-bold"),
            dcc.Dropdown(
                id='cycle-selector',
                options=[{'label': c, 'value': c} for c in cycles],
                value=cycles,  # All selected by default
                multi=True,
                className="mb-3"
            ),

            # N value range
            html.Label("N Value Range:", className="fw-bold"),
            dcc.RangeSlider(
                id='n-range-slider',
                min=3,
                max=7,
                step=1,
                value=[3, 7],
                marks={n: str(n) for n in [3, 4, 5, 6, 7]},
                className="mb-3"
            ),

            # Power-law exponent control
            html.Label("Reference Power-Law (α):", className="fw-bold"),
            dcc.Slider(
                id='alpha-slider',
                min=1.0,
                max=4.0,
                step=0.1,
                value=2.5,
                marks={a: f'{a}' for a in [1.0, 1.5, 2.0, 2.5, 3.0, 3.5, 4.0]},
                tooltip={"placement": "bottom", "always_visible": True},
                className="mb-3"
            ),

            # View options
            html.Label("Display Options:", className="fw-bold"),
            dbc.Checklist(
                id='display-options',
                options=[
                    {'label': ' Show reference power-law', 'value': 'show_powerlaw'},
                    {'label': ' Show fitted lines', 'value': 'show_fits'},
                    {'label': ' Show N labels', 'value': 'show_labels'},
                    {'label': ' Log-log scale', 'value': 'log_scale'},
                ],
                value=['show_powerlaw', 'show_fits', 'show_labels', 'log_scale'],
                className="mb-3"
            ),

            # Statistics display
            html.Hr(),
            html.Div(id='selection-stats', className="mt-3")
        ])
    ], className="mb-4")

def create_main_plot():
    """Create main interactive scatter plot."""
    return dbc.Card([
        dbc.CardHeader(html.H5("Basin Mass vs Max Depth")),
        dbc.CardBody([
            dcc.Graph(
                id='main-scatter',
                style={'height': '600px'},
                config={'displayModeBar': True, 'displaylogo': False}
            )
        ])
    ], className="mb-4")

def create_detail_panels():
    """Create detail view panels."""
    return dbc.Row([
        dbc.Col([
            dbc.Card([
                dbc.CardHeader(html.H6("Depth vs N")),
                dbc.CardBody([
                    dcc.Graph(id='depth-vs-n', style={'height': '300px'})
                ])
            ])
        ], md=6),
        dbc.Col([
            dbc.Card([
                dbc.CardHeader(html.H6("Basin Mass vs N")),
                dbc.CardBody([
                    dcc.Graph(id='mass-vs-n', style={'height': '300px'})
                ])
            ])
        ], md=6)
    ], className="mb-4")

def create_data_table():
    """Create data table with selected points."""
    return dbc.Card([
        dbc.CardHeader(html.H5("Selected Data Points")),
        dbc.CardBody([
            html.Div(id='data-table')
        ])
    ])

# ============================================================================
# Main Layout
# ============================================================================

app.layout = dbc.Container([
    create_header(),

    dbc.Row([
        # Left column: Controls
        dbc.Col([
            create_controls()
        ], md=3),

        # Right column: Main visualization
        dbc.Col([
            create_main_plot(),
            create_detail_panels(),
            create_data_table()
        ], md=9)
    ])
], fluid=True)

# ============================================================================
# Callbacks
# ============================================================================

@app.callback(
    [Output('main-scatter', 'figure'),
     Output('depth-vs-n', 'figure'),
     Output('mass-vs-n', 'figure'),
     Output('selection-stats', 'children'),
     Output('data-table', 'children')],
    [Input('cycle-selector', 'value'),
     Input('n-range-slider', 'value'),
     Input('alpha-slider', 'value'),
     Input('display-options', 'value')]
)
def update_plots(selected_cycles, n_range, alpha_ref, display_options):
    """Update all plots based on filter selections."""

    # Filter data
    if not selected_cycles:
        selected_cycles = []

    filtered_data = data[
        (data['cycle_label'].isin(selected_cycles)) &
        (data['n'] >= n_range[0]) &
        (data['n'] <= n_range[1])
    ].copy()

    if len(filtered_data) == 0:
        # Return empty figures
        empty_fig = go.Figure()
        empty_fig.update_layout(title="No data selected")
        return empty_fig, empty_fig, empty_fig, "No data selected", ""

    # Determine scale type
    log_scale = 'log_scale' in display_options

    # ========================================================================
    # Main scatter plot
    # ========================================================================

    fig_main = go.Figure()

    # Plot data points by cycle
    for cycle in sorted(filtered_data['cycle_label'].unique()):
        cycle_data = filtered_data[filtered_data['cycle_label'] == cycle].sort_values('n')

        fig_main.add_trace(go.Scatter(
            x=cycle_data['max_depth'],
            y=cycle_data['basin_mass'],
            mode='markers+lines',
            name=cycle,
            marker=dict(size=12, line=dict(width=1, color='white')),
            line=dict(width=2),
            hovertemplate=(
                f'<b>{cycle}</b><br>' +
                'N=%{customdata[0]}<br>' +
                'Depth=%{x}<br>' +
                'Mass=%{y:,.0f}<br>' +
                'Entry Breadth=%{customdata[1]:,.0f}<br>' +
                '<extra></extra>'
            ),
            customdata=cycle_data[['n', 'entry_breadth']].values
        ))

        # Add N labels if requested
        if 'show_labels' in display_options:
            for _, row in cycle_data.iterrows():
                fig_main.add_annotation(
                    x=row['max_depth'],
                    y=row['basin_mass'],
                    text=f"N={row['n']}",
                    showarrow=False,
                    xshift=15,
                    yshift=10,
                    font=dict(size=9),
                    opacity=0.6
                )

    # Add reference power-law line
    if 'show_powerlaw' in display_options:
        depth_range = np.logspace(
            np.log10(filtered_data['max_depth'].min()),
            np.log10(filtered_data['max_depth'].max()),
            100
        )
        # Normalize to pass through median
        baseline = filtered_data['basin_mass'].median() / (filtered_data['max_depth'].median() ** alpha_ref)
        mass_ref = baseline * depth_range ** alpha_ref

        fig_main.add_trace(go.Scatter(
            x=depth_range,
            y=mass_ref,
            mode='lines',
            name=f'α={alpha_ref:.1f}',
            line=dict(dash='dash', color='gray', width=3),
            hoverinfo='skip'
        ))

    # Add fitted lines per cycle
    if 'show_fits' in display_options:
        for cycle in sorted(filtered_data['cycle_label'].unique()):
            fit_row = fit_params[fit_params['cycle'] == cycle]
            if len(fit_row) == 0:
                continue

            alpha_fit = fit_row['alpha'].values[0]
            B0 = fit_row['B0'].values[0]

            cycle_data = filtered_data[filtered_data['cycle_label'] == cycle]
            depth_fit = np.logspace(
                np.log10(cycle_data['max_depth'].min()),
                np.log10(cycle_data['max_depth'].max()),
                100
            )
            mass_fit = B0 * depth_fit ** alpha_fit

            fig_main.add_trace(go.Scatter(
                x=depth_fit,
                y=mass_fit,
                mode='lines',
                name=f'{cycle} fit (α={alpha_fit:.2f})',
                line=dict(dash='dot', width=2),
                hoverinfo='skip',
                showlegend=False,
                opacity=0.5
            ))

    # Update layout
    fig_main.update_layout(
        xaxis_title="Max Depth (steps)",
        yaxis_title="Basin Mass (nodes)",
        hovermode='closest',
        height=600,
        legend=dict(yanchor="top", y=0.99, xanchor="left", x=0.01),
        template='plotly_white'
    )

    if log_scale:
        fig_main.update_xaxes(type='log')
        fig_main.update_yaxes(type='log')

    # ========================================================================
    # Depth vs N plot
    # ========================================================================

    fig_depth = go.Figure()

    for cycle in sorted(filtered_data['cycle_label'].unique()):
        cycle_data = filtered_data[filtered_data['cycle_label'] == cycle].sort_values('n')

        fig_depth.add_trace(go.Scatter(
            x=cycle_data['n'],
            y=cycle_data['max_depth'],
            mode='markers+lines',
            name=cycle,
            marker=dict(size=10),
            line=dict(width=2),
            showlegend=False
        ))

    fig_depth.update_layout(
        xaxis_title="N",
        yaxis_title="Max Depth",
        height=300,
        template='plotly_white'
    )

    # ========================================================================
    # Mass vs N plot
    # ========================================================================

    fig_mass = go.Figure()

    for cycle in sorted(filtered_data['cycle_label'].unique()):
        cycle_data = filtered_data[filtered_data['cycle_label'] == cycle].sort_values('n')

        fig_mass.add_trace(go.Scatter(
            x=cycle_data['n'],
            y=cycle_data['basin_mass'],
            mode='markers+lines',
            name=cycle,
            marker=dict(size=10),
            line=dict(width=2),
            showlegend=False
        ))

    fig_mass.update_layout(
        xaxis_title="N",
        yaxis_title="Basin Mass",
        yaxis_type='log',
        height=300,
        template='plotly_white'
    )

    # ========================================================================
    # Statistics summary
    # ========================================================================

    stats_html = html.Div([
        html.H6("Selection Statistics", className="fw-bold"),
        html.P([
            html.Strong("Points: "), f"{len(filtered_data)}",
            html.Br(),
            html.Strong("Cycles: "), f"{filtered_data['cycle_label'].nunique()}",
            html.Br(),
            html.Strong("N range: "), f"{filtered_data['n'].min()}-{filtered_data['n'].max()}",
            html.Br(),
            html.Br(),
            html.Strong("Depth range: "), f"{filtered_data['max_depth'].min()}-{filtered_data['max_depth'].max()}",
            html.Br(),
            html.Strong("Mass range: "), f"{filtered_data['basin_mass'].min():,.0f}-{filtered_data['basin_mass'].max():,.0f}",
            html.Br(),
            html.Br(),
            html.Strong("Depth corr: "), f"r={filtered_data['basin_mass'].corr(filtered_data['max_depth']):.3f}",
        ], className="small")
    ])

    # ========================================================================
    # Data table
    # ========================================================================

    table_data = filtered_data.sort_values('basin_mass', ascending=False)[[
        'cycle_label', 'n', 'basin_mass', 'max_depth', 'entry_breadth', 'entry_ratio'
    ]].copy()

    table_data.columns = ['Cycle', 'N', 'Basin Mass', 'Max Depth', 'Entry Breadth', 'Entry Ratio']

    table_html = dbc.Table.from_dataframe(
        table_data,
        striped=True,
        bordered=True,
        hover=True,
        size='sm',
        style={'fontSize': '12px'}
    )

    return fig_main, fig_depth, fig_mass, stats_html, table_html

# ============================================================================
# Run App
# ============================================================================

if __name__ == '__main__':
    print()
    print("=" * 80)
    print("DEPTH STRUCTURE EXPLORER")
    print("=" * 80)
    print()
    print("Starting interactive web interface...")
    print("Open your browser to: http://127.0.0.1:8050")
    print()
    print("Controls:")
    print("  - Select cycles to compare")
    print("  - Adjust N value range")
    print("  - Change reference power-law exponent")
    print("  - Toggle display options")
    print("  - Zoom/pan on main plot")
    print()
    print("Press Ctrl+C to stop the server")
    print("=" * 80)
    print()

    app.run(debug=True, host='127.0.0.1', port=8050)
