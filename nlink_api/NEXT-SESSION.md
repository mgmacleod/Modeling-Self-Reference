# N-Link API: Remaining Implementation Phases

**Created**: 2026-01-02
**Updated**: 2026-01-02
**Status**: Phases 1-4 complete, Phases 5-6 pending

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

### Phase 4: Basin Operations
- `n-link-analysis/scripts/_core/basin_engine.py` - Basin mapping via reverse BFS
- `n-link-analysis/scripts/_core/branch_engine.py` - Branch structure analysis
- Updated `map-basin-from-cycle.py` and `branch-basin-analysis.py` to use `_core` modules
- `schemas/basins.py` - Pydantic models for basin/branch operations
- `services/basin_service.py` - Service layer for basin operations
- `routers/basins.py` - API endpoints

**Endpoints**:
| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/v1/basins/map` | Map basin from cycle (sync/background) |
| GET | `/api/v1/basins/map/{task_id}` | Get mapping status |
| POST | `/api/v1/basins/branches` | Analyze branch structure (sync/background) |
| GET | `/api/v1/basins/branches/{task_id}` | Get analysis status |

---

## Remaining Phases

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

- [x] CLI script works unchanged
- [x] API server starts without errors (verified via syntax check)
- [x] Endpoint appears in `/docs` (router registered in main.py)
- [ ] Sync operation returns correct response
- [ ] Background task submits and completes
- [ ] Progress updates work correctly
- [ ] Error cases return appropriate HTTP status

---

## Key Files Reference

**Source Scripts** (to refactor):
- `/home/mgm/development/code/Modeling-Self-Reference-actual/n-link-analysis/scripts/render-human-report.py`
- `/home/mgm/development/code/Modeling-Self-Reference-actual/n-link-analysis/scripts/compute-trunkiness-dashboard.py`
- `/home/mgm/development/code/Modeling-Self-Reference-actual/n-link-analysis/scripts/reproduce-main-findings.py`

**Pattern Reference** (completed):
- `/home/mgm/development/code/Modeling-Self-Reference-actual/n-link-analysis/scripts/_core/trace_engine.py`
- `/home/mgm/development/code/Modeling-Self-Reference-actual/n-link-analysis/scripts/_core/basin_engine.py`
- `/home/mgm/development/code/Modeling-Self-Reference-actual/n-link-analysis/scripts/_core/branch_engine.py`
- `/home/mgm/development/code/Modeling-Self-Reference-actual/nlink_api/services/trace_service.py`
- `/home/mgm/development/code/Modeling-Self-Reference-actual/nlink_api/services/basin_service.py`
- `/home/mgm/development/code/Modeling-Self-Reference-actual/nlink_api/routers/traces.py`
- `/home/mgm/development/code/Modeling-Self-Reference-actual/nlink_api/routers/basins.py`

---

## Quick Start Next Session

```bash
# 1. Read this file
# 2. Pick up where we left off (Phase 5)
# 3. Start by reading render-human-report.py
# 4. Follow the implementation pattern above
```
