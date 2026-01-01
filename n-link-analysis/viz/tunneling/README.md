# Tunneling Visualization Tools

Interactive visualization and exploration tools for tunneling analysis results.

## Quick Start

```bash
# Generate all static HTML files
python launch-tunneling-viz.py --static

# Start the main dashboard
python launch-tunneling-viz.py --dashboard

# Start all servers (dashboard + path tracer)
python launch-tunneling-viz.py --all

# Generate static files and start all servers
python launch-tunneling-viz.py --static --all --open-browser
```

## Available Tools

### Static HTML (No Server Required)

| Tool | Output | Description |
|------|--------|-------------|
| **Sankey Diagram** | `report/assets/tunneling_sankey.html` | Interactive flow diagram showing cross-basin page transitions |
| **Node Explorer** | `report/assets/tunnel_node_explorer.html` | Searchable table of all 9,018 tunnel nodes |

Generate with:
```bash
python sankey-basin-flows.py
python tunnel-node-explorer.py
```

### Interactive Servers

| Tool | Default Port | Description |
|------|--------------|-------------|
| **Dashboard** | 8060 | 5-tab Dash app: Overview, Basin Flows, Tunnel Nodes, Stability, Validation |
| **Path Tracer** | 8061 | Search and trace individual page paths across N values |

Start individually:
```bash
python tunneling-dashboard.py --port 8060
python path-tracer-tool.py --port 8061
```

## Dashboard Tabs

1. **Overview**: Summary metrics, mechanism pie chart, tunnel score distribution
2. **Basin Flows**: Sankey diagram of cross-basin transitions
3. **Tunnel Nodes**: Filterable DataTable of all tunnel nodes
4. **Stability**: Per-basin stability comparison chart
5. **Validation**: Theory validation test results

## Data Sources

All visualizations read from `data/wikipedia/processed/multiplex/`:

| File | Used By |
|------|---------|
| `semantic_model_wikipedia.json` | Dashboard |
| `basin_flows.tsv` | Sankey, Dashboard |
| `tunnel_frequency_ranking.tsv` | Explorer, Dashboard, Tracer |
| `basin_stability_scores.tsv` | Dashboard |
| `tunnel_mechanism_summary.tsv` | Dashboard |
| `tunneling_validation_metrics.tsv` | Dashboard |
| `multiplex_basin_assignments.parquet` | Tracer |

## Requirements

```bash
pip install dash dash-bootstrap-components plotly pandas
```

## File Structure

```
viz/tunneling/
├── launch-tunneling-viz.py      # Unified launcher
├── tunneling-dashboard.py       # Main 5-tab dashboard
├── sankey-basin-flows.py        # Sankey HTML generator
├── tunnel-node-explorer.py      # Searchable table generator
├── path-tracer-tool.py          # Per-page path tracer
└── README.md                    # This file
```

## Examples

### View all tunnel nodes sorted by score
Open `tunnel_node_explorer.html` in a browser, then click the "Score" column header.

### Find tunneling patterns for a specific page
1. Start the path tracer: `python path-tracer-tool.py`
2. Go to http://localhost:8061
3. Search for a page title (e.g., "Massachusetts")
4. View the basin membership timeline across N=3-7

### Explore basin transition flows
1. Generate the Sankey: `python sankey-basin-flows.py`
2. Open `tunneling_sankey.html`
3. Hover over flows to see page counts

## Key Insights

- **99.3%** of tunneling is caused by `degree_shift` (different Nth link)
- **N=5→N=6** transition accounts for 53% of all tunneling
- **Gulf of Maine** acts as a sink basin at higher N values
- Shallow nodes (low depth) tunnel more than deep nodes
