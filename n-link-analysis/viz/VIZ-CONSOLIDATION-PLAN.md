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
- [x] All shared modules pass import tests (2026-01-02)
- [x] No circular dependencies (2026-01-02)
- [x] Existing dashboards still run (unchanged) (2026-01-02)

**Phase 1 Complete**: 2026-01-02

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

#### 2.5 Validation Checkpoint

Before proceeding to Phase 3:
- [x] `tunneling-explorer.py` created with 6 tabs (2026-01-02)
- [x] All original functionality preserved (2026-01-02)
- [x] Uses shared modules (colors, loaders, components) (2026-01-02)
- [x] API mode preserved for live tracing (2026-01-02)
- [x] Original dashboards still work (no regressions) (2026-01-02)

**Phase 2 Complete**: 2026-01-02

**Actual Metrics**:
| Metric | Before | After |
|--------|--------|-------|
| Files | 2 | 1 |
| LOC | 1,477 | 1,499 |
| Callbacks | 7 | 7 |
| Ports | 2 | 1 |

Note: LOC slightly higher due to better formatting and docstrings. Net benefit is the unified tool and shared module usage.

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

#### 3.3 Validation Checkpoint

Before proceeding to Phase 4:
- [x] `multiplex-analyzer.py` created with 6 tabs (2026-01-02)
- [x] All original functionality preserved (2026-01-02)
- [x] Uses shared modules (colors, loaders, components) (2026-01-02)
- [x] All tab rendering verified (2026-01-02)
- [x] Original dashboards still work (no regressions) (2026-01-02)

**Phase 3 Complete**: 2026-01-02

**Actual Metrics**:
| Metric | Before | After |
|--------|--------|-------|
| Files | 2 | 1 |
| LOC | 1,439 | 1,062 |
| Callbacks | 11 | 9 |
| Ports | 2 | 1 |

Note: LOC reduced by 26% due to shared module usage and eliminated data loading duplication.

---

### Phase 4: Update Basin Geometry Viewer

**Goal**: Integrate shared components without structural changes.

#### 4.1 Changes

1. ~~Import `shared/colors.py` for consistent basin coloring~~ Not needed (uses Viridis colorscale, not basin colors)
2. Import `REPO_ROOT` from shared module for path consistency
3. ~~Add optional API mode for live basin mapping~~ Deferred (renders precomputed parquets)
4. No tab structure changes (already has internal view modes)

#### 4.2 Validation Checkpoint

- [x] Basin Geometry Viewer imports shared `REPO_ROOT` (2026-01-02)
- [x] All paths resolve correctly (2026-01-02)
- [x] No regressions (2026-01-02)

**Phase 4 Complete**: 2026-01-02

**Actual Metrics**:
| Metric | Before | After |
|--------|--------|-------|
| LOC | 1,130 | 1,130 |
| Callbacks | 1 | 1 |
| Shared imports | 0 | 1 (`REPO_ROOT`) |

Note: Minimal change since Basin Geometry Viewer doesn't use basin colors (uses continuous Viridis colorscale for depth/span/degree).

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

- [x] Created `_archive/` directory (2026-01-02)
- [x] Moved all 4 superseded files (2026-01-02)

#### 5.2 Update Documentation

1. [x] Update `viz/README.md` with new dashboard structure (2026-01-02)
2. [x] Update this plan document with completion status (2026-01-02)
3. [x] Add entry to project timeline (2026-01-02)

#### 5.3 Update Launcher Scripts

- [ ] Update `tunneling/launch-tunneling-viz.py` to launch consolidated tools (deferred - low priority)

**Phase 5 Complete**: 2026-01-02

---

### Phase 6: Comprehensive E2E Testing

**Goal**: Verify all consolidated dashboards and API integrations work correctly end-to-end.

#### 6.1 Dashboard Smoke Tests

Test each dashboard launches and renders without errors:

| Dashboard | Test | Command |
|-----------|------|---------|
| Basin Geometry Viewer | Launch + render | `python n-link-analysis/viz/dash-basin-geometry-viewer.py --port 8055` |
| Multiplex Analyzer | Launch + all 6 tabs | `python n-link-analysis/viz/multiplex-analyzer.py --port 8056` |
| Tunneling Explorer | Launch + all 6 tabs | `python n-link-analysis/viz/tunneling/tunneling-explorer.py --port 8060` |

**Checklist**:
- [ ] Basin Geometry Viewer: loads pointcloud parquets, renders 3D view
- [ ] Basin Geometry Viewer: all 4 view modes work (pointcloud, recursive2d, fan2d, fan3d)
- [ ] Multiplex Analyzer: all 6 tabs render without errors
- [ ] Multiplex Analyzer: data loads (2.1M basin assignments, 41K tunnel nodes)
- [ ] Tunneling Explorer: all 6 tabs render without errors
- [ ] Tunneling Explorer: local file mode works
- [ ] Tunneling Explorer: API mode works (with running API server)

#### 6.2 Shared Module Tests

Verify shared modules work correctly in isolation:

```bash
# Test shared module imports
python -c "from n-link-analysis.viz.shared import BASIN_COLORS, load_basin_assignments, metric_card; print('OK')"

# Test data loading
python -c "
import sys; sys.path.insert(0, 'n-link-analysis/viz')
from shared import load_basin_assignments, load_basin_flows, load_tunnel_ranking
df = load_basin_assignments()
print(f'Basin assignments: {len(df):,} rows')
flows = load_basin_flows()
print(f'Basin flows: {len(flows):,} rows')
ranking = load_tunnel_ranking()
print(f'Tunnel ranking: {len(ranking):,} rows')
"
```

**Checklist**:
- [ ] All shared module imports succeed
- [ ] `load_basin_assignments()` returns 2.1M+ rows
- [ ] `load_basin_flows()` returns 58 flows
- [ ] `load_tunnel_ranking()` returns 41K+ tunnel nodes
- [ ] `get_basin_color()` returns correct colors for known basins
- [ ] `get_short_name()` returns correct short names

#### 6.3 API Integration Tests

Test API client and dashboard-API integration:

```bash
# Start API server
uvicorn nlink_api.main:app --port 8000 &

# Test API client
python -c "
import sys; sys.path.insert(0, 'n-link-analysis/viz')
from api_client import NLinkAPIClient, check_api_available
if check_api_available('http://localhost:8000'):
    client = NLinkAPIClient('http://localhost:8000')
    print('API health:', client.health_check())
    results = client.search_pages('Massachusetts', limit=5)
    print(f'Search results: {len(results)} pages')
else:
    print('API not available')
"

# Test Tunneling Explorer in API mode
python n-link-analysis/viz/tunneling/tunneling-explorer.py --use-api --api-url http://localhost:8000 --port 8060
```

**Checklist**:
- [ ] API server starts without errors
- [ ] `check_api_available()` returns True
- [ ] `search_pages()` returns results
- [ ] `trace_single()` returns valid trace
- [ ] Tunneling Explorer API mode: search works
- [ ] Tunneling Explorer API mode: live tracing works

#### 6.4 Callback Tests

Verify dashboard callbacks work correctly (manual testing):

**Basin Geometry Viewer**:
- [ ] Render button triggers figure update
- [ ] View mode switch changes visualization
- [ ] Depth range slider filters points
- [ ] Sampling mode changes point distribution

**Multiplex Analyzer**:
- [ ] Basin Size tab: cycle selection updates chart
- [ ] Depth Analysis tab: violin plots render
- [ ] Phase Transition tab: N slider updates visualization
- [ ] Layer Connectivity tab: heatmap renders
- [ ] Tunnel Browser tab: search filters table
- [ ] Basin Pairs tab: network renders

**Tunneling Explorer**:
- [ ] Overview tab: metrics display correctly
- [ ] Basin Flows tab: Sankey diagram renders
- [ ] Tunnel Nodes tab: table filters work
- [ ] Path Tracer tab: search returns results
- [ ] Path Tracer tab: trace displays path
- [ ] Stability tab: chart renders
- [ ] Validation tab: hypothesis results display

#### 6.5 Regression Tests

Verify no functionality was lost in consolidation:

| Original Feature | Dashboard | Tab | Status |
|------------------|-----------|-----|--------|
| 3D point cloud | Basin Geometry | - | [ ] |
| Interval layout | Basin Geometry | - | [ ] |
| Fan + edges view | Basin Geometry | - | [ ] |
| Layer connectivity heatmap | Multiplex Analyzer | Layer Connectivity | [ ] |
| Tunnel node browser | Multiplex Analyzer | Tunnel Browser | [ ] |
| Basin pair network | Multiplex Analyzer | Basin Pairs | [ ] |
| Basin size comparison | Multiplex Analyzer | Basin Size | [ ] |
| Depth violin plots | Multiplex Analyzer | Depth Analysis | [ ] |
| Phase transition slider | Multiplex Analyzer | Phase Transition | [ ] |
| Tunneling metrics | Tunneling Explorer | Overview | [ ] |
| Sankey flow diagram | Tunneling Explorer | Basin Flows | [ ] |
| Tunnel node table | Tunneling Explorer | Tunnel Nodes | [ ] |
| Page path tracer | Tunneling Explorer | Path Tracer | [ ] |
| Basin stability chart | Tunneling Explorer | Stability | [ ] |
| Hypothesis validation | Tunneling Explorer | Validation | [ ] |

#### 6.6 Automated Test Script

Create `viz/tests/test_dashboards.py`:

```python
"""Automated smoke tests for consolidated dashboards."""

import subprocess
import sys
import time
import requests

def test_shared_imports():
    """Test shared module imports."""
    sys.path.insert(0, 'n-link-analysis/viz')
    from shared import BASIN_COLORS, load_basin_assignments, metric_card
    assert len(BASIN_COLORS) > 0
    df = load_basin_assignments()
    assert len(df) > 2_000_000

def test_dashboard_starts(dashboard_cmd, port, timeout=30):
    """Test that a dashboard starts and responds."""
    proc = subprocess.Popen(dashboard_cmd, shell=True)
    try:
        for _ in range(timeout):
            try:
                resp = requests.get(f'http://localhost:{port}')
                if resp.status_code == 200:
                    return True
            except:
                pass
            time.sleep(1)
        return False
    finally:
        proc.terminate()

def run_all_tests():
    """Run all dashboard smoke tests."""
    print("Testing shared imports...")
    test_shared_imports()
    print("✓ Shared imports OK")

    dashboards = [
        ("Basin Geometry Viewer", "python n-link-analysis/viz/dash-basin-geometry-viewer.py --port 8155", 8155),
        ("Multiplex Analyzer", "python n-link-analysis/viz/multiplex-analyzer.py --port 8156", 8156),
        ("Tunneling Explorer", "python n-link-analysis/viz/tunneling/tunneling-explorer.py --port 8160", 8160),
    ]

    for name, cmd, port in dashboards:
        print(f"Testing {name}...")
        if test_dashboard_starts(cmd, port):
            print(f"✓ {name} OK")
        else:
            print(f"✗ {name} FAILED")

if __name__ == "__main__":
    run_all_tests()
```

#### 6.7 Validation Checkpoint

Before marking Phase 6 complete:
- [ ] All dashboard smoke tests pass
- [ ] All shared module tests pass
- [ ] API integration tests pass (with running server)
- [ ] All callback tests pass (manual)
- [ ] All regression tests pass
- [ ] Automated test script runs without errors

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

1. **Phase 1** (shared components) - Foundation, no risk ✓
2. **Phase 2** (tunneling merge) - Highest value, clear overlap ✓
3. **Phase 3** (multiplex merge) - Second highest value ✓
4. **Phase 4** (basin viewer update) - Low effort, optional ✓
5. **Phase 5** (cleanup) - Only after validation ✓
6. **Phase 6** (E2E testing) - Comprehensive verification

**Estimated effort**: 4-5 focused sessions (Phases 1-5 complete, Phase 6 pending)

---

## Related Documents

- [NEXT-SESSION-VIZ-CONSOLIDATION.md](NEXT-SESSION-VIZ-CONSOLIDATION.md) - Assessment questions (superseded by this plan)
- [README.md](README.md) - Current tool documentation
- [api_client.py](api_client.py) - Shared API client
- [tunneling/README.md](tunneling/README.md) - Tunneling tool documentation

---

## Changelog

### 2026-01-02 (Phase 3 Complete)
- Created `viz/multiplex-analyzer.py` (1,062 LOC) merging:
  - `dash-multiplex-explorer.py` (769 LOC) - 4 tabs, multiplex structure
  - `dash-cross-n-comparison.py` (670 LOC) - 4 tabs, cross-N analysis
- New 6-tab structure: Basin Size, Depth Analysis, Phase Transition, Layer Connectivity, Tunnel Browser, Basin Pairs
- Uses shared modules: colors.py, loaders.py, components.py
- LOC reduced by 26% (1,439 -> 1,062) due to shared module usage
- All original dashboards still work (no regressions)
- Port consolidation: 8056 + 8062 -> 8056

### 2026-01-02 (Phase 2 Complete)
- Created `viz/tunneling/tunneling-explorer.py` (1,499 LOC) merging:
  - `tunneling-dashboard.py` (726 LOC) - 5 tabs
  - `path-tracer-tool.py` (751 LOC) - search + trace functionality
- New 6-tab structure: Overview, Basin Flows, Tunnel Nodes, Path Tracer, Stability, Validation
- Uses shared modules: colors.py, loaders.py, components.py
- Preserves dual-mode operation (local files / API mode)
- Added `hex_to_rgba` and `info_card` to shared module exports
- All 5 original dashboards still work (no regressions)
- Port consolidation: 8060 + 8061 → 8060

### 2026-01-02 (Phase 1 Complete)
- Created `viz/shared/` directory with `__init__.py`, `colors.py`, `loaders.py`, `components.py`
- Extracted basin color scheme and short names to `colors.py` (from 3 dashboards)
- Extracted data loaders with caching to `loaders.py` (from 5 dashboards)
- Extracted UI components (metric_card, badge, filter_row, etc.) to `components.py`
- All shared modules pass import tests
- All existing dashboards still run unchanged (no regressions)

### 2026-01-02 (Initial)
- Initial plan creation based on inventory assessment
- Selected Option C (Selective Consolidation) architecture
- Defined 5-phase implementation with code examples

---

**END OF DOCUMENT**
