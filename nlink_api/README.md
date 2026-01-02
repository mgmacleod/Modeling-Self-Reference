# N-Link Basin Analysis API

REST API for N-Link Basin Analysis — trace Wikipedia's link graph structure, map basins of attraction, and generate analysis reports.

**Version**: 0.1.0
**Status**: Production-ready with comprehensive test coverage

---

## Table of Contents

- [Quick Start](#quick-start)
- [Usage Guide](#usage-guide)
  - [Tracing N-Link Paths](#tracing-n-link-paths)
  - [Sampling Traces](#sampling-traces)
  - [Mapping Basins](#mapping-basins)
  - [Branch Analysis](#branch-analysis)
  - [Generating Reports](#generating-reports)
  - [Background Tasks](#background-tasks)
- [API Reference](#api-reference)
- [Configuration](#configuration)
- [Implementation Details](#implementation-details)
- [Testing](#testing)

---

## Quick Start

```bash
# Install dependencies
pip install -r requirements.txt

# Start the server
uvicorn nlink_api.main:app --reload --port 8000

# Access interactive API docs
open http://127.0.0.1:8000/docs
```

The API auto-generates interactive documentation:
- **Swagger UI**: http://127.0.0.1:8000/docs
- **ReDoc**: http://127.0.0.1:8000/redoc

---

## Usage Guide

### Tracing N-Link Paths

Trace a single page through the N-link rule (follow the N-th outgoing link repeatedly until reaching a cycle or dead end).

```bash
# Trace from a page title
curl "http://localhost:8000/api/v1/traces/single?n=5&start_title=Python_(programming_language)&max_steps=1000"

# Trace from a page ID
curl "http://localhost:8000/api/v1/traces/single?n=5&start_page_id=23862&max_steps=1000"
```

**Response**:
```json
{
  "start_page_id": 23862,
  "start_title": "Python_(programming_language)",
  "terminal_type": "CYCLE",
  "steps": 47,
  "path": [23862, 18942, ...],
  "cycle_start_index": 42,
  "cycle_len": 5
}
```

**Terminal types**:
- `CYCLE` — Path reached a repeating cycle
- `HALT` — Path hit a dead end (page with fewer than N links)
- `MAX_STEPS` — Exceeded step limit without terminating

---

### Sampling Traces

Sample multiple random traces to discover common cycles and gather statistics.

```bash
# Small sample (runs synchronously)
curl -X POST http://localhost:8000/api/v1/traces/sample \
  -H "Content-Type: application/json" \
  -d '{
    "n": 5,
    "num_samples": 50,
    "seed": 42,
    "min_outdegree": 50,
    "top_cycles_k": 10
  }'

# Large sample (runs as background task)
curl -X POST http://localhost:8000/api/v1/traces/sample \
  -H "Content-Type: application/json" \
  -d '{
    "n": 5,
    "num_samples": 1000,
    "seed": 0,
    "min_outdegree": 50
  }'
```

**Synchronous response** (≤100 samples):
```json
{
  "n": 5,
  "num_samples": 50,
  "terminal_counts": {"CYCLE": 48, "HALT": 2},
  "avg_steps": 127.4,
  "avg_cycle_len": 3.2,
  "top_cycles": [
    {"cycle_ids": [12345, 67890], "count": 15, "length": 2},
    ...
  ]
}
```

**Background task response** (>100 samples):
```json
{
  "task_id": "abc-123-def",
  "task_type": "trace_sample",
  "status": "pending",
  "message": "Sampling 1000 traces as background task"
}
```

---

### Mapping Basins

Map all pages that flow into a given cycle (the basin of attraction).

```bash
# Map basin from cycle titles
curl -X POST http://localhost:8000/api/v1/basins/map \
  -H "Content-Type: application/json" \
  -d '{
    "n": 5,
    "cycle_titles": ["Massachusetts", "Gulf_of_Maine"],
    "max_depth": 100,
    "write_membership": true,
    "tag": "massachusetts_n5"
  }'

# Map basin from cycle page IDs
curl -X POST http://localhost:8000/api/v1/basins/map \
  -H "Content-Type: application/json" \
  -d '{
    "n": 5,
    "cycle_page_ids": [18951, 157028],
    "max_depth": 0
  }'
```

**Parameters**:
- `max_depth`: Maximum BFS depth (0 = unlimited, triggers background task)
- `max_nodes`: Maximum nodes to discover (0 = unlimited)
- `write_membership`: Save full node list to Parquet file

**Response**:
```json
{
  "n": 5,
  "cycle_page_ids": [18951, 157028],
  "total_nodes": 1009471,
  "max_depth_reached": 87,
  "layers": [
    {"depth": 0, "new_nodes": 2, "total_seen": 2},
    {"depth": 1, "new_nodes": 156, "total_seen": 158},
    ...
  ],
  "stopped_reason": "exhausted",
  "members_parquet_path": "/path/to/massachusetts_n5_members.parquet",
  "elapsed_seconds": 45.2
}
```

---

### Branch Analysis

Analyze the tributary structure of a basin — how pages flow through entry points.

```bash
curl -X POST http://localhost:8000/api/v1/basins/branches \
  -H "Content-Type: application/json" \
  -d '{
    "n": 5,
    "cycle_titles": ["Massachusetts", "Gulf_of_Maine"],
    "top_k": 25,
    "write_top_k_membership": 10,
    "tag": "massachusetts_n5"
  }'
```

**Response**:
```json
{
  "n": 5,
  "total_basin_nodes": 1009471,
  "num_branches": 156,
  "branches": [
    {
      "rank": 1,
      "entry_id": 23456,
      "entry_title": "United_States",
      "basin_size": 523000,
      "max_depth": 45,
      "enters_cycle_page_id": 18951,
      "enters_cycle_title": "Massachusetts"
    },
    ...
  ],
  "branches_topk_tsv_path": "/path/to/branches_top25.tsv",
  "elapsed_seconds": 62.1
}
```

---

### Generating Reports

Generate analysis dashboards and human-readable reports.

**Trunkiness Dashboard** — Aggregates branch concentration metrics across basins:

```bash
# Synchronous
curl -X POST http://localhost:8000/api/v1/reports/trunkiness \
  -H "Content-Type: application/json" \
  -d '{"n": 5, "tag": "bootstrap_2025-12-30"}'

# Background task
curl -X POST http://localhost:8000/api/v1/reports/trunkiness/async \
  -H "Content-Type: application/json" \
  -d '{"n": 5, "tag": "bootstrap_2025-12-30"}'
```

**Human Report** — Generates Markdown report with PNG figures:

```bash
# Synchronous
curl -X POST http://localhost:8000/api/v1/reports/human \
  -H "Content-Type: application/json" \
  -d '{"tag": "bootstrap_2025-12-30"}'

# Background task
curl -X POST http://localhost:8000/api/v1/reports/human/async \
  -H "Content-Type: application/json" \
  -d '{"tag": "bootstrap_2025-12-30"}'
```

**List available reports**:
```bash
curl http://localhost:8000/api/v1/reports/list
```

**Serve generated figures**:
```bash
curl http://localhost:8000/api/v1/reports/figures/trunkiness_dashboard.png
```

---

### Background Tasks

Long-running operations execute as background tasks. The workflow:

1. **Submit request** → Receive `task_id`
2. **Poll for status** → Check progress
3. **Retrieve result** → Get final output when complete

```bash
# Check task status
curl http://localhost:8000/api/v1/tasks/{task_id}

# Response
{
  "task_id": "abc-123",
  "task_type": "trace_sample",
  "status": "running",
  "progress": 0.45,
  "progress_message": "Sampled 450/1000 traces",
  "created_at": "2026-01-02T10:30:00Z",
  "started_at": "2026-01-02T10:30:01Z"
}

# When complete
{
  "task_id": "abc-123",
  "status": "completed",
  "progress": 1.0,
  "result": { ... full response ... },
  "completed_at": "2026-01-02T10:32:15Z"
}
```

**Task management endpoints**:
```bash
# List all tasks (filter by status or type)
curl "http://localhost:8000/api/v1/tasks?status=running"
curl "http://localhost:8000/api/v1/tasks?task_type=basin_map"

# Cancel a pending task
curl -X DELETE http://localhost:8000/api/v1/tasks/{task_id}

# Clear completed tasks
curl -X DELETE http://localhost:8000/api/v1/tasks
```

**Task statuses**: `pending`, `running`, `completed`, `failed`, `cancelled`

---

## API Reference

### Health & Status

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/v1/health` | Liveness check — returns `{"status": "ok"}` |
| GET | `/api/v1/status` | Detailed status with version, data source, task counts |

### Data Operations

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/v1/data/source` | Data source configuration and file paths |
| POST | `/api/v1/data/validate` | Validate data file accessibility |
| GET | `/api/v1/data/pages/{page_id}` | Look up page by ID |
| GET | `/api/v1/data/pages/search?q=...` | Search pages by title (case-insensitive) |

### Trace Operations

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/v1/traces/single` | Trace single N-link path |
| POST | `/api/v1/traces/sample` | Sample multiple traces (sync ≤100, async >100) |
| GET | `/api/v1/traces/sample/{task_id}` | Get sampling task status |

### Basin Operations

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/v1/basins/map` | Map basin from cycle |
| GET | `/api/v1/basins/map/{task_id}` | Get mapping task status |
| POST | `/api/v1/basins/branches` | Analyze branch structure |
| GET | `/api/v1/basins/branches/{task_id}` | Get branch analysis status |

### Report Operations

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/v1/reports/trunkiness` | Generate trunkiness dashboard (sync) |
| POST | `/api/v1/reports/trunkiness/async` | Generate trunkiness dashboard (async) |
| POST | `/api/v1/reports/human` | Generate human report (sync) |
| POST | `/api/v1/reports/human/async` | Generate human report (async) |
| GET | `/api/v1/reports/{task_id}` | Get report generation status |
| GET | `/api/v1/reports/list` | List available reports |
| GET | `/api/v1/reports/figures/{filename}` | Serve figure file |

### Task Management

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/v1/tasks` | List all tasks (filter by `status`, `task_type`) |
| GET | `/api/v1/tasks/{task_id}` | Get task status and result |
| DELETE | `/api/v1/tasks/{task_id}` | Cancel pending task |
| DELETE | `/api/v1/tasks` | Clear completed/failed/cancelled tasks |

---

## Configuration

Configure via environment variables:

| Variable | Default | Description |
|----------|---------|-------------|
| `DATA_SOURCE` | `local` | Data source: `local` or `huggingface` |
| `LOCAL_DATA_DIR` | — | Path to local data directory |
| `HF_DATASET_REPO` | `mgmacleod/wikidata1` | HuggingFace dataset repository |
| `HF_CACHE_DIR` | — | HuggingFace cache directory |
| `ANALYSIS_OUTPUT_DIR` | `data/wikipedia/processed/analysis` | Output directory for analysis results |
| `MAX_WORKERS` | `2` | Background task thread pool size |
| `MAX_TASK_HISTORY` | `100` | Completed tasks to keep in history |
| `DEBUG` | `false` | Enable debug mode |

**Example**:
```bash
export DATA_SOURCE=local
export LOCAL_DATA_DIR=/path/to/wikipedia/data
export MAX_WORKERS=4
uvicorn nlink_api.main:app --port 8000
```

---

## Implementation Details

### Architecture

```
nlink_api/
├── main.py              # FastAPI app factory with lifespan management
├── config.py            # Settings from environment variables
├── dependencies.py      # Dependency injection (singletons, data loader)
│
├── routers/             # API endpoint definitions
│   ├── health.py        # Health & status
│   ├── tasks.py         # Task management
│   ├── data.py          # Data operations
│   ├── traces.py        # Trace sampling
│   ├── basins.py        # Basin mapping & branches
│   └── reports.py       # Report generation
│
├── schemas/             # Pydantic request/response models
│   ├── common.py        # TaskStatus, ErrorResponse, DataSourceInfo
│   ├── traces.py        # TraceSingleRequest/Response, TraceSampleRequest/Response
│   ├── basins.py        # BasinMapRequest/Response, BranchAnalysisRequest/Response
│   └── reports.py       # TrunkinessDashboard*, HumanReport*, ReportList*
│
├── services/            # Business logic layer
│   ├── data_service.py  # Data loading, validation, page lookup
│   ├── trace_service.py # Trace execution and sampling
│   ├── basin_service.py # Basin mapping and branch analysis
│   └── report_service.py# Report generation and file serving
│
├── tasks/               # Background task infrastructure
│   └── manager.py       # ThreadPoolExecutor-based task queue
│
└── tests/               # Test suite (90 tests)
    ├── conftest.py      # Fixtures and mock data
    └── test_*.py        # Endpoint and unit tests
```

### Layered Design

```
FastAPI Routers (HTTP layer)
    ↓ (Pydantic validation)
Service Classes (business logic)
    ↓ (imports)
Core Engines (n-link-analysis/scripts/_core/)
    ↓
Data Files (Parquet, NumPy arrays)
```

**Key principle**: Routers handle HTTP concerns, services orchestrate operations, core engines contain pure computation logic.

### Core Engines

The API reuses computation logic extracted from CLI scripts:

| Engine | Source Script | Purpose |
|--------|---------------|---------|
| `trace_engine.py` | `sample-nlink-traces.py` | N-link path tracing |
| `basin_engine.py` | `map-basin-from-cycle.py` | Reverse BFS basin mapping |
| `branch_engine.py` | `branch-basin-analysis.py` | Branch structure analysis |
| `dashboard_engine.py` | `compute-trunkiness-dashboard.py` | Trunkiness metrics |
| `report_engine.py` | `render-human-report.py` | Report & figure generation |

Engines are located in `n-link-analysis/scripts/_core/` and designed for reuse:
- Structured return types (dataclasses)
- Optional `progress_callback(float, str)` parameter
- No CLI/argparse dependencies

### Background Task System

`tasks/manager.py` provides a ThreadPoolExecutor-based task queue:

- **Thread pool**: Configurable worker count (`MAX_WORKERS`)
- **Progress tracking**: Tasks report 0.0–1.0 progress with messages
- **Lifecycle**: `PENDING` → `RUNNING` → `COMPLETED|FAILED|CANCELLED`
- **History**: Completed tasks retained up to `MAX_TASK_HISTORY`
- **Thread safety**: All operations protected by threading.Lock

**Sync/async thresholds**:
| Operation | Sync Condition | Async Condition |
|-----------|----------------|-----------------|
| Trace sampling | ≤100 samples | >100 samples |
| Basin mapping | depth ≤50 AND nodes ≤100k | depth >50 OR unlimited |
| Branch analysis | depth ≤50 | depth >50 OR unlimited |

### Static File Serving

Generated files are served via FastAPI's StaticFiles:
- `/static/analysis/` → Analysis output directory
- `/static/assets/` → Report figures and assets

### Data Flow Example

```
POST /api/v1/basins/map {n: 5, cycle_titles: ["A", "B"]}
    ↓
routers/basins.py: validate request, resolve titles to page IDs
    ↓
services/basin_service.py: determine sync/async, prepare parameters
    ↓
tasks/manager.py: submit to ThreadPoolExecutor (if async)
    ↓
_core/basin_engine.py: reverse BFS, track progress via callback
    ↓
services/basin_service.py: format response, write output files
    ↓
Return: BasinMapResponse with paths, layer info, timing
```

---

## Testing

The test suite includes 90 tests across 6 files:

| File | Tests | Coverage |
|------|-------|----------|
| `test_health.py` | 9 | Health & status endpoints |
| `test_data.py` | 11 | Data source, validation, page lookup |
| `test_traces.py` | 21 | Trace schemas, single/sample endpoints |
| `test_basins.py` | 18 | Basin mapping, branch analysis |
| `test_tasks.py` | 14 | Task manager lifecycle |
| `test_reports.py` | 17 | Report generation endpoints |

**Run tests**:
```bash
# Unit tests only (no data dependencies)
pytest nlink_api/tests/ -m "not integration"

# All tests (requires Wikipedia data)
pytest nlink_api/tests/

# With coverage report
pytest nlink_api/tests/ -m "not integration" --cov=nlink_api --cov-report=term-missing
```

**Test markers**:
- `@pytest.mark.integration` — Requires real Wikipedia data files

---

## Pipeline Integration

The API integrates with the main reproduction script:

```bash
# Traditional mode (subprocess calls)
python n-link-analysis/scripts/reproduce-main-findings.py --quick

# API mode (requires running server)
uvicorn nlink_api.main:app --port 8000 &
python n-link-analysis/scripts/reproduce-main-findings.py --quick --use-api
```

The `--use-api` flag routes all operations through the REST API, demonstrating full coverage of the analysis pipeline.

---

## Error Handling

All errors return structured responses:

```json
{
  "detail": "Page not found: 'Invalid_Page_Title'"
}
```

HTTP status codes:
- `200` — Success
- `400` — Bad request (invalid parameters)
- `404` — Not found (page, task, or resource)
- `422` — Validation error (Pydantic)
- `500` — Internal server error

---

## Related Documentation

- [NEXT-SESSION.md](NEXT-SESSION.md) — Implementation history and notes
- [Interactive Docs](http://127.0.0.1:8000/docs) — Swagger UI (when server running)
- [Project Timeline](../llm-facing-documentation/project-timeline.md) — Development history
