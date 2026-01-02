# Visualization Tool Consolidation Plan



**Document Type**: Implementation plan
**Target Audience**: LLMs
**Purpose**: Step-by-step plan for consolidating 5 visualization dashboards into 3
**Last Updated**: 2026-01-02
**Dependencies**: [NEXT-SESSION-VIZ-CONSOLIDATION.md](NEXT-SESSION-VIZ-CONSOLIDATION.md), [api_client.py](api_client.py)
**Status**: Active

---

## Executive Summary

This plan consolidates 5 separate Dash dashboards (ports 8055-8062) into 3 unified applications by merging related tools and extracting shared components. The approach balances maintainability gains against implementation effort.

**Current State**: 5 dashboards, 5 ports, 4,046 LOC, 19 callbacks, ~15 data files
**Target State**: 3 dashboards, 3 ports, ~3,500 LOC (estimated), shared component library

---

## Inventory Summary

### Current Dashboards

| Dashboard | Port | LOC | Callbacks | Primary Data |
|-----------|------|-----|-----------|--------------|
| Basin Geometry Viewer | 8055 | 1,130 | 1 | Pointcloud parquets |
| Multiplex Explorer | 8056 | 769 | 4 | Layer connectivity, tunnel classification |
| Tunneling Dashboard | 8060 | 726 | 5 | Basin flows, validation metrics |
| Path Tracer | 8061 | 751 | 2 | Tunnel ranking, basin assignments |
| Cross-N Comparison | 8062 | 670 | 7 | Basin assignments, flows |

### Identified Duplication

| Pattern | Occurrences | Files |
|---------|-------------|-------|
| `BASIN_COLORS` dict | 3 | tunneling-dashboard, path-tracer, cross-n-comparison |
| `get_short_name()` | 2 | tunneling-dashboard, path-tracer |
| TSV loading with error handling | 5 | All dashboards |
| Bootstrap tab layout | 4 | All except basin-geometry |
| Metric card creation | 3 | multiplex-explorer, tunneling-dashboard, cross-n-comparison |

---

## Architecture Decision

**Selected Option**: C - Selective Consolidation

**Rationale**:
1. Dashboards cluster naturally by purpose (tunneling analysis vs cross-N exploration)
2. Basin Geometry Viewer is fundamentally different (3D point clouds, specialized callbacks)
3. Merging related tools reduces port sprawl without creating a monolith
4. Shared components reduce duplication without over-abstracting

### Consolidation Map

| Current | Port | Merges Into | New Port |
|---------|------|-------------|----------|
| Basin Geometry Viewer | 8055 | (standalone) | 8055 |
| Multiplex Explorer | 8056 | Multiplex Analyzer | 8056 |
| Cross-N Comparison | 8062 | Multiplex Analyzer | 8056 |
| Tunneling Dashboard | 8060 | Tunneling Explorer | 8060 |
| Path Tracer | 8061 | Tunneling Explorer | 8060 |

---

## Implementation Phases

### Phase 1: Extract Shared Components

**Goal**: Create reusable module library without modifying existing dashboards.

#### 1.1 Create `viz/shared/` Directory Structure

```
n-link-analysis/viz/
├── shared/
│   ├── __init__.py
│   ├── colors.py      # Basin colors, short names
│   ├── loaders.py     # Data loading with caching
│   └── components.py  # UI component factories
├── api_client.py      # (existing)
└── ... (existing dashboards)
```

#### 1.2 Extract `colors.py`

**Source**: Extract from `tunneling-dashboard.py` lines 20-40

```python
# viz/shared/colors.py
"""Basin color schemes and display name mappings."""

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
    "Hill__Mountain": "Mountain",
    "Animal__Kingdom_(biology)": "Kingdom",
    "American_Revolutionary_War__Eastern_United_States": "Am. Rev. War",
    "Latvia__Lithuania": "Latvia",
    "Civil_law__Precedent": "Precedent",
    "Curing_(chemistry)__Thermosetting_polymer": "Thermosetting",
}

def get_basin_color(cycle_name: str) -> str:
    """Get color for basin, with fallback to gray."""
    return BASIN_COLORS.get(cycle_name, "#7f7f7f")

def get_short_name(cycle_name: str) -> str:
    """Get display-friendly short name for basin."""
    return BASIN_SHORT_NAMES.get(cycle_name, cycle_name.split("__")[0])
```

#### 1.3 Extract `loaders.py`

**Source**: Common patterns from all dashboards

```python
# viz/shared/loaders.py
"""Cached data loading utilities for visualization tools."""

from pathlib import Path
from functools import lru_cache
from typing import Optional
import pandas as pd

# Default data directories
MULTIPLEX_DIR = Path("data/wikipedia/processed/multiplex")
ANALYSIS_DIR = Path("data/wikipedia/processed/analysis")

@lru_cache(maxsize=1)
def load_basin_assignments(data_dir: Optional[Path] = None) -> pd.DataFrame:
    """Load multiplex basin assignments parquet."""
    path = (data_dir or MULTIPLEX_DIR) / "multiplex_basin_assignments.parquet"
    if not path.exists():
        return pd.DataFrame()
    return pd.read_parquet(path)

@lru_cache(maxsize=1)
def load_tunnel_ranking(data_dir: Optional[Path] = None) -> pd.DataFrame:
    """Load tunnel frequency ranking TSV."""
    path = (data_dir or MULTIPLEX_DIR) / "tunnel_frequency_ranking.tsv"
    if not path.exists():
        return pd.DataFrame()
    return pd.read_csv(path, sep="\t")

@lru_cache(maxsize=1)
def load_basin_flows(data_dir: Optional[Path] = None) -> pd.DataFrame:
    """Load basin flows TSV."""
    path = (data_dir or MULTIPLEX_DIR) / "basin_flows.tsv"
    if not path.exists():
        return pd.DataFrame()
    return pd.read_csv(path, sep="\t")

def load_tsv_safe(path: Path) -> pd.DataFrame:
    """Load TSV with error handling, returns empty DataFrame if missing."""
    if not path.exists():
        return pd.DataFrame()
    try:
        return pd.read_csv(path, sep="\t")
    except Exception:
        return pd.DataFrame()
```

#### 1.4 Extract `components.py`

**Source**: Common UI patterns from multiplex-explorer, tunneling-dashboard

```python
# viz/shared/components.py
"""Reusable Dash UI components."""

import dash_bootstrap_components as dbc
from dash import html

def metric_card(title: str, value: str, color: str = "primary") -> dbc.Card:
    """Create a metric display card."""
    return dbc.Card([
        dbc.CardBody([
            html.H6(title, className="card-subtitle text-muted"),
            html.H3(value, className=f"card-title text-{color}"),
        ])
    ], className="mb-3")

def filter_row(*children) -> dbc.Row:
    """Create a row of filter controls with consistent spacing."""
    cols = [dbc.Col(child, width="auto") for child in children]
    return dbc.Row(cols, className="mb-3 align-items-end")

def badge(text: str, color: str = "primary") -> dbc.Badge:
    """Create a styled badge."""
    return dbc.Badge(text, color=color, className="me-1")
```

#### 1.5 Validation Checkpoint

Before proceeding to Phase 2:
- [ ] All shared modules pass import tests
- [ ] No circular dependencies
- [ ] Existing dashboards still run (unchanged)

---

### Phase 2: Merge Tunneling Tools (8060 + 8061)

**Goal**: Combine Tunneling Dashboard and Path Tracer into single 6-tab application.

#### 2.1 Create `tunneling-explorer.py`

**New file**: `viz/tunneling/tunneling-explorer.py`

**Tab Structure**:
| Tab | Source | Description |
|-----|--------|-------------|
| Overview | tunneling-dashboard | Metric cards, mechanism pie, scatter |
| Basin Flows | tunneling-dashboard | Sankey diagram |
| Tunnel Nodes | tunneling-dashboard | Filterable table |
| Path Tracer | path-tracer-tool | Search + trace display |
| Stability | tunneling-dashboard | Basin stability chart |
| Validation | tunneling-dashboard | Hypothesis results |

#### 2.2 Merge Strategy

1. Start with `tunneling-dashboard.py` as base (726 LOC)
2. Add Path Tracer tab content from `path-tracer-tool.py`:
   - Import API client integration
   - Add search input + trace display callbacks
   - Preserve dual-mode (local/API) functionality
3. Update imports to use `shared/` modules
4. Consolidate duplicate callbacks

#### 2.3 Key Code Changes

**Add to imports**:
```python
from shared.colors import BASIN_COLORS, get_short_name, get_basin_color
from shared.loaders import load_tunnel_ranking, load_basin_flows
from shared.components import metric_card, filter_row
from api_client import NLinkAPIClient, check_api_available
```

**New tab definition**:
```python
dbc.Tab(label="Path Tracer", tab_id="path-tracer", children=[
    dbc.Row([
        dbc.Col([
            dbc.Input(id="search-input", placeholder="Search page title...", debounce=True),
            html.Div(id="search-results"),
        ], width=4),
        dbc.Col([
            html.Div(id="trace-display"),
        ], width=8),
    ])
])
```

**New callbacks** (migrate from path-tracer-tool.py):
```python
@callback(Output("search-results", "children"), Input("search-input", "value"))
def update_search(query): ...

@callback(Output("trace-display", "children"), Input("trace-btn", "n_clicks"), ...)
def trace_page(n_clicks, ...): ...
```

#### 2.4 Estimated Changes

| Metric | Before | After |
|--------|--------|-------|
| Files | 2 | 1 |
| LOC | 1,477 | ~1,200 |
| Callbacks | 7 | 7 |
| Ports | 2 | 1 |

---

### Phase 3: Merge Cross-N Tools (8056 + 8062)

**Goal**: Combine Multiplex Explorer and Cross-N Comparison into single 6-tab application.

#### 3.1 Create `multiplex-analyzer.py`

**New file**: `viz/multiplex-analyzer.py`

**Tab Structure**:
| Tab | Source | Description |
|-----|--------|-------------|
| Basin Size | cross-n-comparison | Size comparison across N |
| Depth Analysis | cross-n-comparison | Violin plots, statistics |
| Phase Transition | cross-n-comparison | N slider with size charts |
| Layer Connectivity | multiplex-explorer | Heatmap of N×N edges |
| Tunnel Browser | multiplex-explorer | Searchable tunnel table |
| Basin Pairs | multiplex-explorer | Network of connected basins |

#### 3.2 Merge Strategy

1. Start with `dash-multiplex-explorer.py` as base (769 LOC)
2. Add Cross-N tabs from `dash-cross-n-comparison.py`:
   - Basin Size tab with log/linear toggle
   - Depth Analysis with violin plots
   - Phase Transition with N slider
3. Update imports to use `shared/` modules
4. Consolidate data loading (both use `multiplex_basin_assignments.parquet`)

#### 3.3 Estimated Changes

| Metric | Before | After |
|--------|--------|-------|
| Files | 2 | 1 |
| LOC | 1,439 | ~1,100 |
| Callbacks | 11 | 9 |
| Ports | 2 | 1 |

---

### Phase 4: Update Basin Geometry Viewer

**Goal**: Integrate shared components without structural changes.

#### 4.1 Changes

1. Import `shared/colors.py` for consistent basin coloring
2. Add optional API mode for live basin mapping
3. No tab structure changes (already has internal view modes)

#### 4.2 Estimated Changes

| Metric | Before | After |
|--------|--------|-------|
| LOC | 1,130 | ~1,100 |
| Callbacks | 1 | 1 |

---

### Phase 5: Cleanup and Documentation

#### 5.1 Archive Old Files

Move replaced files to `viz/_archive/`:
```
viz/_archive/
├── tunneling-dashboard.py.bak
├── path-tracer-tool.py.bak
├── dash-multiplex-explorer.py.bak
└── dash-cross-n-comparison.py.bak
```

#### 5.2 Update Documentation

1. Update `viz/README.md` with new dashboard structure
2. Update `NEXT-SESSION-VIZ-CONSOLIDATION.md` → mark complete
3. Add entry to project timeline

#### 5.3 Update Launcher Scripts

Update `tunneling/launch-tunneling-viz.py` to launch consolidated tools.

---

## Final Architecture

### Dashboard Structure

```
n-link-analysis/viz/
├── shared/
│   ├── __init__.py
│   ├── colors.py
│   ├── loaders.py
│   └── components.py
├── api_client.py
├── dash-basin-geometry-viewer.py    # Port 8055 (unchanged)
├── multiplex-analyzer.py            # Port 8056 (merged)
├── tunneling/
│   └── tunneling-explorer.py        # Port 8060 (merged)
└── _archive/                        # Old files
```

### Port Mapping

| Dashboard | Port | Description |
|-----------|------|-------------|
| Basin Geometry Viewer | 8055 | 3D point clouds, interval layouts |
| Multiplex Analyzer | 8056 | Cross-N analysis, tunnel browser |
| Tunneling Explorer | 8060 | Flows, tracing, validation |

### Quick Start Commands

```bash
# Launch all dashboards
python n-link-analysis/viz/dash-basin-geometry-viewer.py --port 8055 &
python n-link-analysis/viz/multiplex-analyzer.py --port 8056 &
python n-link-analysis/viz/tunneling/tunneling-explorer.py --port 8060 &

# Or use unified launcher (future)
python n-link-analysis/viz/launch-all.py
```

---

## Success Metrics

| Metric | Before | After | Target Met? |
|--------|--------|-------|-------------|
| Ports | 5 | 3 | Yes (< 3) |
| Total LOC | 4,046 | ~3,400 | Yes (reduced) |
| Duplicate color dicts | 3 | 1 | Yes |
| Shared component usage | 0 | 3 dashboards | Yes |
| Single entry point | No | Partial | Future work |

---

## Risk Mitigation

| Risk | Mitigation |
|------|------------|
| Breaking existing workflows | Archive old files, preserve port numbers |
| Callback conflicts in merged apps | Use unique callback IDs, test thoroughly |
| Memory increase from larger apps | Lazy-load tab content on activation |
| Lost functionality | Comprehensive tab mapping, manual testing |

---

## Implementation Order

**Recommended sequence** (each phase is independently valuable):

1. **Phase 1** (shared components) - Foundation, no risk
2. **Phase 2** (tunneling merge) - Highest value, clear overlap
3. **Phase 3** (multiplex merge) - Second highest value
4. **Phase 4** (basin viewer update) - Low effort, optional
5. **Phase 5** (cleanup) - Only after validation

**Estimated effort**: 3-4 focused sessions

---

## Related Documents

- [NEXT-SESSION-VIZ-CONSOLIDATION.md](NEXT-SESSION-VIZ-CONSOLIDATION.md) - Assessment questions (superseded by this plan)
- [README.md](README.md) - Current tool documentation
- [api_client.py](api_client.py) - Shared API client
- [tunneling/README.md](tunneling/README.md) - Tunneling tool documentation

---

## Changelog

### 2026-01-02
- Initial plan creation based on inventory assessment
- Selected Option C (Selective Consolidation) architecture
- Defined 5-phase implementation with code examples

---

**END OF DOCUMENT**
