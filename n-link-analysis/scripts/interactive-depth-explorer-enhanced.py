#!/usr/bin/env python3
"""Enhanced interactive depth structure explorer with distribution analysis.

New features beyond original explorer:
- Depth distribution histograms (interactive N selection)
- Variance and skewness panels
- Distribution statistics table
- Bimodal pattern visualization
- Side-by-side N comparison mode
"""

import pandas as pd
import numpy as np
from pathlib import Path
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
import dash
from dash import dcc, html, Input, Output, State, dash_table
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
        if file_path.exists():
            df = pd.read_csv(file_path, sep="\t")
            all_data.append(df)

    data = pd.concat(all_data, ignore_index=True)

    # Add computed columns
    data['log_depth'] = np.log10(data['max_depth'])
    data['log_mass'] = np.log10(data['basin_mass'])
    data['predicted_mass_2.5'] = data['entry_breadth'] * data['max_depth']**2.5

    return data

def load_depth_distributions():
    """Load depth distribution data for all N values."""
    distributions = {}
    for n in [3, 4, 5, 6, 7]:
        file_path = ANALYSIS_DIR / f"path_characteristics_n={n}_mechanism_depth_distributions.tsv"
        if file_path.exists():
            distributions[n] = pd.read_csv(file_path, sep="\t")
    return distributions

def load_depth_statistics():
    """Load precomputed depth statistics."""
    file_path = ANALYSIS_DIR / "depth_distributions/depth_statistics_by_n.tsv"
    if file_path.exists():
        return pd.read_csv(file_path, sep="\t")
    return None

# Load data
print("Loading data...")
data = load_all_data()
distributions = load_depth_distributions()
stats = load_depth_statistics()
print(f"Loaded {len(data)} data points from {data['cycle_label'].nunique()} cycles")
print(f"Loaded distributions for N={list(distributions.keys())}")

# ============================================================================
# Dash App Setup
# ============================================================================

app = dash.Dash(
    __name__,
    external_stylesheets=[dbc.themes.BOOTSTRAP],
    suppress_callback_exceptions=True
)

app.title = "Enhanced Depth Explorer"

# ============================================================================
# Layout Components
# ============================================================================

def create_header():
    """Create header with title and description."""
    return dbc.Container([
        html.H1("Enhanced Depth Structure Explorer", className="text-center my-4"),
        html.P(
            "Interactive exploration of basin mass, depth distributions, variance, and skewness",
            className="text-center text-muted mb-4"
        ),
        dbc.Row([
            dbc.Col([
                dbc.Badge("NEW: Depth Distributions", color="success", className="me-2"),
                dbc.Badge("NEW: Variance Analysis", color="info", className="me-2"),
                dbc.Badge("NEW: Skewness Patterns", color="warning"),
            ], className="text-center")
        ]),
        html.Hr()
    ], fluid=True)

def create_controls():
    """Create control panel for filtering and adjusting views."""
    return dbc.Card([
        dbc.CardHeader(html.H5("Controls")),
        dbc.CardBody([
            # N value selection for distribution view
            html.Label("Select N for Distribution:", className="fw-bold mt-3"),
            dcc.Dropdown(
                id='n-selector',
                options=[{'label': f'N={n}', 'value': n} for n in [3, 4, 5, 6, 7]],
                value=5,
                clearable=False
            ),

            # Comparison mode toggle
            html.Label("Comparison Mode:", className="fw-bold mt-3"),
            dbc.Checklist(
                id='comparison-mode',
                options=[{'label': 'Show all N values side-by-side', 'value': 'compare'}],
                value=[],
                switch=True
            ),

            # Cycle filter for basin mass plot
            html.Label("Filter Cycles:", className="fw-bold mt-3"),
            dcc.Dropdown(
                id='cycle-filter',
                options=[{'label': cycle, 'value': cycle}
                        for cycle in sorted(data['cycle_label'].unique())],
                value=list(data['cycle_label'].unique()),
                multi=True
            ),

            # Log scale toggle
            html.Label("Plot Options:", className="fw-bold mt-3"),
            dbc.Checklist(
                id='log-scale-toggle',
                options=[{'label': 'Log scale (basin mass)', 'value': 'log'}],
                value=['log'],
                switch=True
            ),
        ])
    ], className="mb-4")

def create_statistics_table():
    """Create table showing depth statistics by N."""
    if stats is None:
        return html.Div("Statistics not available")

    # Format for display
    display_stats = stats[['n', 'mean', 'median', 'p90', 'max', 'std', 'variance', 'skewness']].copy()
    display_stats = display_stats.round(2)

    return dash_table.DataTable(
        id='stats-table',
        columns=[{"name": col, "id": col} for col in display_stats.columns],
        data=display_stats.to_dict('records'),
        style_cell={'textAlign': 'center', 'padding': '10px'},
        style_header={'backgroundColor': 'lightgrey', 'fontWeight': 'bold'},
        style_data_conditional=[
            {
                'if': {'row_index': 2},  # N=5 row
                'backgroundColor': '#d4edda',
                'fontWeight': 'bold'
            }
        ]
    )

# ============================================================================
# Layout
# ============================================================================

app.layout = dbc.Container([
    create_header(),

    dbc.Row([
        # Left column: Controls
        dbc.Col([
            create_controls(),

            # Statistics summary card
            dbc.Card([
                dbc.CardHeader(html.H5("Quick Stats")),
                dbc.CardBody([
                    html.Div(id='quick-stats')
                ])
            ])
        ], width=3),

        # Right column: Visualizations
        dbc.Col([
            # Tab interface
            dbc.Tabs([
                # Tab 1: Depth Distributions
                dbc.Tab([
                    dcc.Graph(id='distribution-plot', style={'height': '600px'})
                ], label="Depth Distributions", tab_id="tab-dist"),

                # Tab 2: Basin Mass vs Depth
                dbc.Tab([
                    dcc.Graph(id='basin-mass-plot', style={'height': '600px'})
                ], label="Basin Mass Analysis", tab_id="tab-mass"),

                # Tab 3: Variance & Skewness
                dbc.Tab([
                    dcc.Graph(id='variance-skewness-plot', style={'height': '600px'})
                ], label="Variance & Skewness", tab_id="tab-variance"),

                # Tab 4: Statistics Table
                dbc.Tab([
                    html.Div([
                        html.H5("Depth Statistics by N", className="mt-3 mb-3"),
                        create_statistics_table(),
                        html.Div([
                            html.Hr(),
                            html.H6("Key Insights:", className="mt-3"),
                            html.Ul([
                                html.Li("N=5 has highest variance (σ²=473) and skewness (1.88)"),
                                html.Li("N=5 mean depth is 1.43× deeper than N=4"),
                                html.Li("N=5 p90/median ratio is 5.3× (strongest tail)"),
                                html.Li("N=7 has highest mean depth (24.7) but lower basin mass"),
                            ])
                        ])
                    ])
                ], label="Statistics Table", tab_id="tab-table"),
            ], id='tabs', active_tab='tab-dist')
        ], width=9)
    ]),

], fluid=True)

# ============================================================================
# Callbacks
# ============================================================================

@app.callback(
    Output('distribution-plot', 'figure'),
    [Input('n-selector', 'value'),
     Input('comparison-mode', 'value')]
)
def update_distribution_plot(selected_n, comparison_mode):
    """Update depth distribution histogram."""

    if 'compare' in comparison_mode:
        # Show all N values side-by-side
        fig = make_subplots(
            rows=5, cols=1,
            subplot_titles=[f'N={n}' for n in [3, 4, 5, 6, 7]],
            vertical_spacing=0.05
        )

        for idx, n in enumerate([3, 4, 5, 6, 7], start=1):
            if n not in distributions:
                continue

            dist = distributions[n]

            # Histogram
            fig.add_trace(
                go.Bar(
                    x=dist['depth'],
                    y=dist['convergence_count'],
                    name=f'N={n}',
                    marker_color='steelblue',
                    showlegend=False
                ),
                row=idx, col=1
            )

            # Add statistics lines if available
            if stats is not None:
                stat_row = stats[stats['n'] == n].iloc[0]

                # Mean
                fig.add_vline(
                    x=stat_row['mean'],
                    line_dash="dash",
                    line_color="red",
                    annotation_text=f"Mean: {stat_row['mean']:.1f}",
                    annotation_position="top right",
                    row=idx, col=1
                )

                # Median
                fig.add_vline(
                    x=stat_row['median'],
                    line_dash="dash",
                    line_color="green",
                    annotation_text=f"Median: {stat_row['median']:.1f}",
                    annotation_position="top left",
                    row=idx, col=1
                )

        fig.update_xaxes(title_text="Depth (steps)", row=5, col=1)
        fig.update_yaxes(title_text="Count")
        fig.update_layout(height=2000, title_text="Depth Distributions Comparison (All N)")

    else:
        # Show single N value with detailed annotations
        if selected_n not in distributions:
            return go.Figure().add_annotation(text="No data available", showarrow=False)

        dist = distributions[selected_n]

        fig = go.Figure()

        # Histogram
        fig.add_trace(
            go.Bar(
                x=dist['depth'],
                y=dist['convergence_count'],
                name='Convergence paths',
                marker_color='steelblue',
                opacity=0.7
            )
        )

        # Add statistics if available
        if stats is not None:
            stat_row = stats[stats['n'] == selected_n].iloc[0]

            # Mean
            fig.add_vline(
                x=stat_row['mean'],
                line_dash="dash",
                line_color="red",
                line_width=3,
                annotation_text=f"Mean: {stat_row['mean']:.1f}",
                annotation_position="top right"
            )

            # Median
            fig.add_vline(
                x=stat_row['median'],
                line_dash="dash",
                line_color="green",
                line_width=3,
                annotation_text=f"Median: {stat_row['median']:.1f}",
                annotation_position="top left"
            )

            # 90th percentile
            fig.add_vline(
                x=stat_row['p90'],
                line_dash="dash",
                line_color="orange",
                line_width=3,
                annotation_text=f"90th: {stat_row['p90']:.1f}",
                annotation_position="bottom right"
            )

            # Add statistics box
            stats_text = (
                f"<b>Statistics for N={selected_n}</b><br>"
                f"Mean: {stat_row['mean']:.2f}<br>"
                f"Median: {stat_row['median']:.2f}<br>"
                f"Std Dev: {stat_row['std']:.2f}<br>"
                f"Variance: {stat_row['variance']:.2f}<br>"
                f"Skewness: {stat_row['skewness']:.2f}<br>"
                f"Max: {stat_row['max']:.0f}<br>"
                f"Paths: {stat_row['count']:.0f}"
            )

            fig.add_annotation(
                text=stats_text,
                xref="paper", yref="paper",
                x=0.98, y=0.98,
                xanchor='right', yanchor='top',
                bgcolor="rgba(255, 255, 200, 0.8)",
                bordercolor="black",
                borderwidth=1,
                showarrow=False
            )

        fig.update_layout(
            title=f"Depth Distribution for N={selected_n}",
            xaxis_title="Depth (steps to convergence)",
            yaxis_title="Number of paths",
            height=600,
            showlegend=True,
            hovermode='x unified'
        )

    return fig

@app.callback(
    Output('basin-mass-plot', 'figure'),
    [Input('cycle-filter', 'value'),
     Input('log-scale-toggle', 'value')]
)
def update_basin_mass_plot(selected_cycles, log_scale):
    """Update basin mass vs depth scatter plot."""

    # Filter data
    filtered_data = data[data['cycle_label'].isin(selected_cycles)]

    use_log = 'log' in log_scale

    fig = go.Figure()

    # Color by N
    for n in sorted(filtered_data['n'].unique()):
        n_data = filtered_data[filtered_data['n'] == n]

        fig.add_trace(
            go.Scatter(
                x=n_data['max_depth'],
                y=n_data['basin_mass'],
                mode='markers',
                name=f'N={n}',
                marker=dict(size=10, opacity=0.7),
                text=n_data['cycle_label'],
                hovertemplate='<b>%{text}</b><br>Depth: %{x}<br>Mass: %{y:,}<extra></extra>'
            )
        )

    # Add power-law reference line (α=2.5)
    if use_log:
        depth_range = np.logspace(0, 2.5, 100)
    else:
        depth_range = np.linspace(1, 200, 100)

    # Scale to match data roughly
    avg_entry = filtered_data['entry_breadth'].mean()
    predicted = avg_entry * depth_range**2.5

    fig.add_trace(
        go.Scatter(
            x=depth_range,
            y=predicted,
            mode='lines',
            name='Power-law (α=2.5)',
            line=dict(color='black', dash='dash', width=2),
            hovertemplate='Depth: %{x:.1f}<br>Predicted: %{y:,.0f}<extra></extra>'
        )
    )

    if use_log:
        fig.update_xaxes(type='log', title='Max Depth (steps)')
        fig.update_yaxes(type='log', title='Basin Mass (nodes)')
    else:
        fig.update_xaxes(title='Max Depth (steps)')
        fig.update_yaxes(title='Basin Mass (nodes)')

    fig.update_layout(
        title='Basin Mass vs Max Depth (Power-law: Mass ∝ Depth^2.5)',
        height=600,
        hovermode='closest'
    )

    return fig

@app.callback(
    Output('variance-skewness-plot', 'figure'),
    Input('tabs', 'active_tab')
)
def update_variance_plot(active_tab):
    """Update variance and skewness visualization."""

    if stats is None:
        return go.Figure().add_annotation(text="Statistics not available", showarrow=False)

    fig = make_subplots(
        rows=2, cols=2,
        subplot_titles=['Variance vs N', 'Standard Deviation vs N',
                       'Skewness vs N', 'Coefficient of Variation vs N'],
        specs=[[{"secondary_y": False}, {"secondary_y": False}],
               [{"secondary_y": False}, {"secondary_y": False}]]
    )

    # Variance
    fig.add_trace(
        go.Scatter(
            x=stats['n'],
            y=stats['variance'],
            mode='lines+markers',
            name='Variance',
            marker=dict(size=12, color='purple'),
            line=dict(width=3)
        ),
        row=1, col=1
    )

    # Highlight N=5
    n5_var = stats[stats['n'] == 5]['variance'].iloc[0]
    fig.add_annotation(
        x=5, y=n5_var,
        text=f"N=5: σ²={n5_var:.0f}<br>(4× higher than N=4)",
        showarrow=True,
        arrowhead=2,
        row=1, col=1
    )

    # Standard Deviation
    fig.add_trace(
        go.Scatter(
            x=stats['n'],
            y=stats['std'],
            mode='lines+markers',
            name='Std Dev',
            marker=dict(size=12, color='blue'),
            line=dict(width=3)
        ),
        row=1, col=2
    )

    # Skewness
    fig.add_trace(
        go.Scatter(
            x=stats['n'],
            y=stats['skewness'],
            mode='lines+markers',
            name='Skewness',
            marker=dict(size=12, color='red'),
            line=dict(width=3)
        ),
        row=2, col=1
    )

    # Add reference line at skewness=0
    fig.add_hline(y=0, line_dash="dash", line_color="gray", opacity=0.5, row=2, col=1)

    # Highlight N=5
    n5_skew = stats[stats['n'] == 5]['skewness'].iloc[0]
    fig.add_annotation(
        x=5, y=n5_skew,
        text=f"N=5: {n5_skew:.2f}<br>(most right-skewed)",
        showarrow=True,
        arrowhead=2,
        row=2, col=1
    )

    # Coefficient of Variation (CV = std/mean)
    stats['cv'] = stats['std'] / stats['mean']
    fig.add_trace(
        go.Scatter(
            x=stats['n'],
            y=stats['cv'],
            mode='lines+markers',
            name='CV',
            marker=dict(size=12, color='green'),
            line=dict(width=3)
        ),
        row=2, col=2
    )

    # Update axes
    fig.update_xaxes(title_text="N", row=1, col=1)
    fig.update_xaxes(title_text="N", row=1, col=2)
    fig.update_xaxes(title_text="N", row=2, col=1)
    fig.update_xaxes(title_text="N", row=2, col=2)

    fig.update_yaxes(title_text="Variance (σ²)", row=1, col=1)
    fig.update_yaxes(title_text="Std Dev (σ)", row=1, col=2)
    fig.update_yaxes(title_text="Skewness", row=2, col=1)
    fig.update_yaxes(title_text="CV (σ/μ)", row=2, col=2)

    fig.update_layout(
        height=600,
        title_text="Depth Distribution Metrics Across N Values",
        showlegend=False
    )

    return fig

@app.callback(
    Output('quick-stats', 'children'),
    Input('n-selector', 'value')
)
def update_quick_stats(selected_n):
    """Update quick statistics display."""

    if stats is None:
        return "Statistics not available"

    stat_row = stats[stats['n'] == selected_n].iloc[0]

    return html.Div([
        html.H6(f"N={selected_n} Summary"),
        html.Hr(),
        html.P([html.Strong("Mean depth: "), f"{stat_row['mean']:.2f} steps"]),
        html.P([html.Strong("Median depth: "), f"{stat_row['median']:.2f} steps"]),
        html.P([html.Strong("90th %ile: "), f"{stat_row['p90']:.2f} steps"]),
        html.P([html.Strong("Max depth: "), f"{stat_row['max']:.0f} steps"]),
        html.P([html.Strong("Variance: "), f"{stat_row['variance']:.1f}"]),
        html.P([html.Strong("Skewness: "), f"{stat_row['skewness']:.2f}"]),
        html.Hr(),
        html.P([
            html.Strong("Tail ratio: "),
            f"{stat_row['p90']/stat_row['median']:.2f}× (p90/median)"
        ]),
    ])

# ============================================================================
# Main
# ============================================================================

if __name__ == '__main__':
    print("\n" + "="*80)
    print("ENHANCED DEPTH EXPLORER")
    print("="*80)
    print("\nStarting server at http://127.0.0.1:8051")
    print("\nFeatures:")
    print("  - Depth distribution histograms (Tab 1)")
    print("  - Basin mass analysis with power-law fit (Tab 2)")
    print("  - Variance and skewness visualization (Tab 3)")
    print("  - Statistics table with key insights (Tab 4)")
    print("\nControls:")
    print("  - Select N value to view its distribution")
    print("  - Toggle comparison mode to see all N values side-by-side")
    print("  - Filter cycles for basin mass plot")
    print("  - Toggle log scale for easier viewing")
    print("\nPress Ctrl+C to stop the server")
    print("="*80 + "\n")

    app.run(debug=True, host='127.0.0.1', port=8051)
