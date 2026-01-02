# Basin Geometry Visualization Tools

This directory contains tools for visualizing Wikipedia N-link basin structures.

## Dashboard Quick Start

| Dashboard | Port | Command |
|-----------|------|---------|
| Basin Geometry Viewer | 8055 | `python n-link-analysis/viz/dash-basin-geometry-viewer.py` |
| Multiplex Explorer | 8056 | `python n-link-analysis/viz/dash-multiplex-explorer.py` |
| Tunneling Dashboard | 8060 | `python n-link-analysis/viz/tunneling/tunneling-dashboard.py` |
| Path Tracer | 8061 | `python n-link-analysis/viz/tunneling/path-tracer-tool.py` |
| **Cross-N Comparison** | 8062 | `python n-link-analysis/viz/dash-cross-n-comparison.py` |

## Quick Start

### Generate Static Images (PNG)

```bash
# Render all N=5 basins as high-res PNGs
python n-link-analysis/viz/batch-render-basin-images.py --n 5 --all-cycles --width 1600 --height 1000

# Create comparison grid (3x3 layout)
python n-link-analysis/viz/batch-render-basin-images.py --n 5 --comparison-grid --width 3600 --height 2400

# Render specific basins
python n-link-analysis/viz/batch-render-basin-images.py --n 5 --cycles Massachusetts Kingdom --width 2400 --height 1600
```

### Generate Interactive HTML

```bash
# Create full basin point cloud with interactive 3D viewer
python n-link-analysis/viz/render-full-basin-geometry.py \
  --n 5 \
  --cycle-title "Massachusetts" \
  --cycle-title "Gulf_of_Maine" \
  --write-html \
  --max-plot-points 120000
```

### Launch Interactive Dashboards

```bash
# Basin geometry viewer (3D point clouds, interval layouts)
python n-link-analysis/viz/dash-basin-geometry-viewer.py --port 8055

# Multiplex tunnel explorer (cross-N connectivity, tunnel nodes)
python n-link-analysis/viz/dash-multiplex-explorer.py --port 8056
```

## Scripts

### `batch-render-basin-images.py`
**Purpose**: Automated batch rendering of basin visualizations as static images (PNG/SVG/PDF)

**Key Features**:
- Render all 9 N=5 basins with consistent styling
- Create comparison grids (3x3 layout)
- Customizable resolution, colorscales, opacity
- Requires: `kaleido` (`pip install kaleido`)

**Common Usage**:
```bash
# Publication-quality single basin (high-res)
python n-link-analysis/viz/batch-render-basin-images.py \
  --n 5 --cycles Massachusetts \
  --width 2400 --height 1600 \
  --colorscale Plasma --opacity 0.9

# All basins with custom styling
python n-link-analysis/viz/batch-render-basin-images.py \
  --n 5 --all-cycles \
  --width 1920 --height 1080 \
  --max-plot-points 150000 \
  --show-axes
```

### `render-full-basin-geometry.py`
**Purpose**: Generate basin point cloud data and optional HTML preview

**Key Features**:
- Reverse BFS from cycle members to map full basin
- Exports to Parquet (for Dash viewer) and HTML (standalone)
- Configurable depth limits, sampling, layout parameters

**Common Usage**:
```bash
# Generate basin with default settings (exhaustive)
python n-link-analysis/viz/render-full-basin-geometry.py \
  --n 5 \
  --cycle-title "American_Revolutionary_War" \
  --cycle-title "Eastern_United_States" \
  --write-html

# Limited depth/nodes (faster for testing)
python n-link-analysis/viz/render-full-basin-geometry.py \
  --n 5 \
  --cycle-title "Massachusetts" \
  --cycle-title "Gulf_of_Maine" \
  --max-depth 15 \
  --max-nodes 200000 \
  --write-html
```

### `dash-basin-geometry-viewer.py`
**Purpose**: Interactive web dashboard for exploring basin geometries

**Key Features**:
- 3D violin point cloud view
- 2D interval layout view
- 2D fan+edges graph view
- Real-time switching between cycles

**Common Usage**:
```bash
# Launch on default port
python n-link-analysis/viz/dash-basin-geometry-viewer.py

# Custom port
python n-link-analysis/viz/dash-basin-geometry-viewer.py --port 8060
```

### `dash-multiplex-explorer.py`
**Purpose**: Interactive exploration of cross-N basin connectivity and tunnel nodes

**Key Features**:
- Layer connectivity matrix (N×N heatmap)
- Tunnel node browser with filtering and scoring
- Basin pair network visualization
- Cycle reachability analysis

**Tabs**:
1. **Layer Connectivity**: Heatmap of within-N vs cross-N edges
2. **Tunnel Nodes**: Searchable table with 9,018 tunnel nodes
3. **Basin Pairs**: Network showing which basins connect via tunneling
4. **Reachability**: Per-cycle BFS reach across N layers

**Common Usage**:
```bash
# Launch on default port
python n-link-analysis/viz/dash-multiplex-explorer.py

# Custom port
python n-link-analysis/viz/dash-multiplex-explorer.py --port 8080
```

**See**: [MULTIPLEX-EXPLORER-GUIDE.md](MULTIPLEX-EXPLORER-GUIDE.md) for detailed usage

### `dash-cross-n-comparison.py`
**Purpose**: Side-by-side comparison of basin properties across N values (N=3-10)

**Key Features**:
- Basin size comparison with log/linear scale toggle
- Depth distribution analysis (violin plots, statistics)
- Phase transition explorer with N slider
- Tunneling flow Sankey diagram

**Tabs**:
1. **Basin Size**: Compare sizes across N for selected cycles
2. **Depth Analysis**: Violin plots and depth statistics per cycle
3. **Phase Transition**: Slider-based N selection with size charts
4. **Tunneling Flows**: Sankey diagram of cross-basin page movements

**Common Usage**:
```bash
# Launch on default port
python n-link-analysis/viz/dash-cross-n-comparison.py

# Custom port
python n-link-analysis/viz/dash-cross-n-comparison.py --port 8062
```

### `generate-multi-n-figures.py`
**Purpose**: Generate static multi-N analysis figures for reports

**Key Features**:
- Phase transition chart (basin size vs N)
- Basin collapse comparison (N=5 vs N=10)
- Tunnel node distribution chart
- Depth distribution by N
- Summary statistics HTML table

**Common Usage**:
```bash
# Generate all figures
python n-link-analysis/viz/generate-multi-n-figures.py --all

# Generate specific figures
python n-link-analysis/viz/generate-multi-n-figures.py --phase-transition --collapse-chart
```

## Output Locations

- **Static images (PNG/SVG/PDF)**: `n-link-analysis/report/assets/basin_3d_n={N}_cycle={CYCLE}.{format}`
- **Comparison grids**: `n-link-analysis/report/assets/basin_comparison_grid_n={N}.{format}`
- **Interactive HTML**: `n-link-analysis/report/assets/basin_pointcloud_3d_n={N}_cycle={CYCLE}.html`
- **Parquet data**: `data/wikipedia/processed/analysis/basin_pointcloud_n={N}_cycle={CYCLE}.parquet`
- **Edge databases**: `data/wikipedia/processed/analysis/edges_n={N}.duckdb`

## Shared API Client

The `api_client.py` module provides a reusable client for connecting visualization tools to the N-Link API server.

```python
from viz.api_client import NLinkAPIClient, check_api_available

# Quick availability check
if check_api_available("http://localhost:8000"):
    client = NLinkAPIClient("http://localhost:8000")

    # Search for pages
    results = client.search_pages("Massachusetts", limit=10)

    # Trace N-link path
    trace = client.trace_single(n=5, start_title="Massachusetts")

    # Get page info
    page = client.get_page(12345)
```

**Key Methods**:
| Method | Description |
|--------|-------------|
| `health_check()` | Check if API is available |
| `search_pages(query, limit)` | Search pages by title |
| `get_page(page_id)` | Get page by ID |
| `get_page_by_title(title)` | Get page by title |
| `trace_single(n, start_title=, start_page_id=)` | Trace N-link path |
| `map_basin(n, cycle_titles, background=)` | Map basin from cycle |
| `get_task_status(task_id)` | Get background task status |
| `wait_for_task(task_id)` | Wait for task completion |

## Dependencies

Core visualization:
```bash
pip install plotly pandas pyarrow duckdb
```

Static image export (PNG/SVG/PDF):
```bash
pip install kaleido
```

Interactive dashboard:
```bash
pip install dash dash-bootstrap-components
```

## N=5 Basins Available

1. **Massachusetts** (121k nodes) - Explosive wide, depth 8
2. **Kingdom (biology)** (55k nodes) - Hub-driven, depth 9
3. **Autumn** (55k nodes) - Balanced, depth 7
4. **Sea salt** (105k nodes) - Tall trunk, late peak at depth 14
5. **Mountain** (74k nodes) - Tall trunk, depth 20
6. **Latvia** (52k nodes) - Balanced, depth 12
7. **Precedent** (56k nodes) - Hub-driven, depth 23
8. **American Revolutionary War** (46k nodes) - Balanced, depth 10
9. **Thermosetting polymer** (61k nodes) - Skyscraper trunk, depth 48 (!!)

## Visualization Parameters

### Layout Parameters (render-full-basin-geometry.py)
- `--z-step` (default: 0.35) - Vertical spacing between depth layers
- `--radius-scale` (default: 0.015) - Horizontal spread of each layer
- `--twist-per-layer` (default: 0.15) - Rotation per depth layer (radians)

### Rendering Parameters (batch-render-basin-images.py)
- `--width` / `--height` - Output resolution (pixels)
- `--max-plot-points` - Subsample large basins (default: 120k)
- `--colorscale` - Plotly colorscale (Viridis, Plasma, Inferno, etc.)
- `--opacity` - Point transparency (0.0-1.0)
- `--show-axes` - Display 3D coordinate axes

## Examples

### Publication Figure Pipeline
```bash
# 1. Generate full basin data (if not already done)
python n-link-analysis/viz/render-full-basin-geometry.py \
  --n 5 --cycle-title Massachusetts --cycle-title Gulf_of_Maine

# 2. Render high-res static image
python n-link-analysis/viz/batch-render-basin-images.py \
  --n 5 --cycles Massachusetts \
  --width 3200 --height 2400 \
  --colorscale Plasma --format png

# 3. Generate comparison grid for paper
python n-link-analysis/viz/batch-render-basin-images.py \
  --n 5 --comparison-grid \
  --width 4800 --height 3200 \
  --format pdf
```

### Interactive Exploration
```bash
# 1. Ensure all basins have point clouds
for cycle in Massachusetts Kingdom Autumn Sea_salt Mountain Latvia Precedent American_Revolutionary_War Thermosetting_polymer; do
  echo "Processing $cycle..."
  # (Use appropriate cycle pairs from your data)
done

# 2. Launch Dash viewer
python n-link-analysis/viz/dash-basin-geometry-viewer.py --port 8055

# 3. Open browser to http://localhost:8055
```

## Tips

1. **Performance**: Large basins (>100k nodes) benefit from `--max-plot-points` sampling
2. **Memory**: Use `--max-depth` and `--max-nodes` for testing before full basin runs
3. **Quality**: Higher `--width`/`--height` with `scale=2` (hardcoded) gives 2× resolution
4. **Formats**: PNG for web/reports, SVG for editing, PDF for publications
5. **Colorscales**: `Viridis` (default, colorblind-safe), `Plasma` (vibrant), `Inferno` (warm)

## Troubleshooting

**"No pointcloud found"**: Run `render-full-basin-geometry.py` first to generate basin data

**"kaleido required"**: Install with `pip install kaleido`

**Out of memory**: Reduce `--max-plot-points` or use `--max-nodes` to limit basin size

**Slow rendering**: Use `--max-depth 10` for quick previews, full depth for final renders

---

**Last Updated**: 2026-01-01
