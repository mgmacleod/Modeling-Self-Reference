# N-Link API: Remaining Implementation Phases

**Created**: 2026-01-02
**Status**: Phases 1-3 complete, Phases 4-6 pending

---

## Completed Work

### Phase 1: Foundation
- `nlink_api/` package structure
- `main.py` FastAPI app factory
- `config.py` configuration
- `tasks/manager.py` ThreadPoolExecutor-based background tasks
- `routers/health.py` and `routers/tasks.py`

### Phase 2: Core Engine Extraction
- Created `n-link-analysis/scripts/_core/` package
- Extracted `trace_engine.py` from `sample-nlink-traces.py`
- Verified CLI script still works with refactored code

### Phase 3: Data & Traces API
- `schemas/common.py`, `schemas/traces.py` - Pydantic models
- `services/data_service.py`, `services/trace_service.py`
- `routers/data.py`, `routers/traces.py`
- Endpoints: `/data/source`, `/data/validate`, `/data/pages/*`, `/traces/single`, `/traces/sample`

---

## Remaining Phases

### Phase 4: Basin Operations

**Goal**: Expose basin mapping and branch analysis via API

**Scripts to Refactor**:
1. `map-basin-from-cycle.py` → `_core/basin_engine.py`
2. `branch-basin-analysis.py` → `_core/branch_engine.py`

**Key Functions to Extract**:
```python
# From map-basin-from-cycle.py
def map_basin(
    loader: DataLoader,
    n: int,
    cycle_page_ids: list[int],
    max_depth: int = 0,
    progress_callback: ProgressCallback = None,
) -> BasinMapResult:
    """Reverse BFS to map all nodes flowing into a cycle."""

# From branch-basin-analysis.py
def analyze_branches(
    loader: DataLoader,
    n: int,
    cycle_page_ids: list[int],
    top_k: int = 25,
    progress_callback: ProgressCallback = None,
) -> BranchAnalysisResult:
    """Partition basin by depth-1 entry points, compute trunkiness."""
```

**Files to Create**:
- `n-link-analysis/scripts/_core/basin_engine.py`
- `n-link-analysis/scripts/_core/branch_engine.py`
- `nlink_api/schemas/basins.py`
- `nlink_api/services/basin_service.py`
- `nlink_api/routers/basins.py`

**Endpoints**:
| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/v1/basins/map` | Map basin from cycle (background) |
| GET | `/api/v1/basins/map/{task_id}` | Get mapping status |
| POST | `/api/v1/basins/branches` | Analyze branch structure (background) |
| GET | `/api/v1/basins/branches/{task_id}` | Get analysis status |
| GET | `/api/v1/basins/list` | List available basin artifacts |

**Request Schema Example**:
```python
class BasinMapRequest(BaseModel):
    n: int = 5
    cycle_titles: list[str] = []      # e.g., ["Massachusetts", "Gulf_of_Maine"]
    cycle_page_ids: list[int] = []    # Alternative to titles
    max_depth: int = 0                # 0 = unlimited
    tag: str | None = None            # Output file tag
```

---

### Phase 5: Reports & Figures

**Goal**: Generate reports and figures via API

**Scripts to Refactor**:
1. `render-human-report.py` → `_core/report_engine.py`
2. `compute-trunkiness-dashboard.py` → `_core/dashboard_engine.py`

**Key Functions to Extract**:
```python
# From render-human-report.py
def generate_report(
    analysis_dir: Path,
    output_dir: Path,
    tag: str,
    progress_callback: ProgressCallback = None,
) -> ReportResult:
    """Generate Markdown report + PNG figures."""

# From compute-trunkiness-dashboard.py
def compute_trunkiness_dashboard(
    analysis_dir: Path,
    tag: str,
    n: int = 5,
) -> TrunkinessDashboardResult:
    """Aggregate branch metrics into dashboard TSV."""
```

**Files to Create**:
- `n-link-analysis/scripts/_core/report_engine.py`
- `n-link-analysis/scripts/_core/dashboard_engine.py`
- `nlink_api/schemas/reports.py`
- `nlink_api/services/report_service.py`
- `nlink_api/routers/reports.py`

**Endpoints**:
| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/v1/reports/trunkiness` | Generate trunkiness dashboard |
| POST | `/api/v1/reports/human` | Generate human-facing report |
| GET | `/api/v1/reports/{task_id}` | Get generation status |
| GET | `/api/v1/reports/list` | List available reports |
| GET | `/api/v1/reports/figures/{filename}` | Serve figure file |

---

### Phase 6: Pipeline Integration

**Goal**: Update `reproduce-main-findings.py` to optionally use API

**Changes to `reproduce-main-findings.py`**:
```python
parser.add_argument("--use-api", action="store_true",
                    help="Execute via API server instead of subprocess")
parser.add_argument("--api-base", default="http://127.0.0.1:8000",
                    help="API base URL")

def run_via_api(api_base: str, endpoint: str, payload: dict) -> dict:
    """Submit task and poll until completion."""
    resp = requests.post(f"{api_base}{endpoint}", json=payload)
    task_id = resp.json()["task_id"]

    while True:
        status = requests.get(f"{api_base}/api/v1/tasks/{task_id}").json()
        if status["status"] in ("completed", "failed"):
            break
        print(f"Progress: {status['progress']:.0%} - {status['progress_message']}")
        time.sleep(2)

    return status["result"]
```

**Usage**:
```bash
# Traditional mode (subprocess calls)
python reproduce-main-findings.py --quick

# API mode (requires running server)
uvicorn nlink_api.main:app --port 8000 &
python reproduce-main-findings.py --quick --use-api
```

---

## Implementation Pattern

Each phase follows the same pattern:

1. **Read the source script** to understand the logic
2. **Extract core functions** to `_core/` module with:
   - Structured return types (dataclasses)
   - Optional `progress_callback` parameter
   - No CLI/argparse dependencies
3. **Update original script** to import from `_core`
4. **Verify CLI still works**
5. **Create Pydantic schemas** for request/response
6. **Create service class** that wraps the engine
7. **Create router** with endpoints
8. **Update `main.py`** to include new router
9. **Test endpoints** via `/docs`

---

## Testing Checklist

Before marking a phase complete:

- [ ] CLI script works unchanged
- [ ] API server starts without errors
- [ ] Endpoint appears in `/docs`
- [ ] Sync operation returns correct response
- [ ] Background task submits and completes
- [ ] Progress updates work correctly
- [ ] Error cases return appropriate HTTP status

---

## Key Files Reference

**Source Scripts** (to refactor):
- `/home/mgm/development/code/Modeling-Self-Reference-actual/n-link-analysis/scripts/map-basin-from-cycle.py`
- `/home/mgm/development/code/Modeling-Self-Reference-actual/n-link-analysis/scripts/branch-basin-analysis.py`
- `/home/mgm/development/code/Modeling-Self-Reference-actual/n-link-analysis/scripts/render-human-report.py`
- `/home/mgm/development/code/Modeling-Self-Reference-actual/n-link-analysis/scripts/compute-trunkiness-dashboard.py`
- `/home/mgm/development/code/Modeling-Self-Reference-actual/n-link-analysis/scripts/reproduce-main-findings.py`

**Pattern Reference** (completed):
- `/home/mgm/development/code/Modeling-Self-Reference-actual/n-link-analysis/scripts/_core/trace_engine.py`
- `/home/mgm/development/code/Modeling-Self-Reference-actual/nlink_api/services/trace_service.py`
- `/home/mgm/development/code/Modeling-Self-Reference-actual/nlink_api/routers/traces.py`

---

## Quick Start Next Session

```bash
# 1. Read this file
# 2. Pick up where we left off (Phase 4)
# 3. Start by reading map-basin-from-cycle.py
# 4. Follow the implementation pattern above
```
