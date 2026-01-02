# N-Link Basin Analysis API

FastAPI-based service layer for the N-Link Basin Analysis project.

## Quick Start

```bash
# Install dependencies
pip install -r requirements.txt

# Start the server
uvicorn nlink_api.main:app --reload --port 8000

# Visit API docs
open http://127.0.0.1:8000/docs
```

## Available Endpoints

### Health & Status

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/v1/health` | GET | Basic liveness check |
| `/api/v1/status` | GET | Detailed status (data source, tasks) |

### Data Operations

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/v1/data/source` | GET | Current data source info |
| `/api/v1/data/validate` | POST | Validate data files |
| `/api/v1/data/pages/{page_id}` | GET | Look up page by ID |
| `/api/v1/data/pages/search?q=...` | GET | Search pages by title |

### Trace Operations

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/v1/traces/single` | GET | Trace single N-link path |
| `/api/v1/traces/sample` | POST | Sample multiple traces (sync or background) |
| `/api/v1/traces/sample/{task_id}` | GET | Get sampling task status |

### Task Management

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/v1/tasks` | GET | List all tasks |
| `/api/v1/tasks/{task_id}` | GET | Get task status |
| `/api/v1/tasks/{task_id}` | DELETE | Cancel pending task |
| `/api/v1/tasks` | DELETE | Clear completed tasks |

## Configuration

Environment variables:

| Variable | Default | Description |
|----------|---------|-------------|
| `DATA_SOURCE` | `local` | Data source: `local` or `huggingface` |
| `HF_DATASET_REPO` | `mgmacleod/wikidata1` | HuggingFace repository |
| `HF_CACHE_DIR` | `~/.cache/...` | HuggingFace cache directory |
| `MAX_WORKERS` | `2` | Background task workers |
| `DEBUG` | `false` | Enable debug mode |

## Architecture

```
nlink_api/
├── main.py              # FastAPI app factory
├── config.py            # Configuration settings
├── dependencies.py      # Dependency injection
├── routers/             # API endpoints
│   ├── health.py
│   ├── tasks.py
│   ├── data.py
│   └── traces.py
├── schemas/             # Pydantic models
│   ├── common.py
│   └── traces.py
├── services/            # Business logic
│   ├── data_service.py
│   └── trace_service.py
└── tasks/               # Background tasks
    └── manager.py
```

## Background Tasks

Large operations (e.g., sampling >100 traces) run as background tasks:

1. POST request returns `task_id`
2. Poll `/api/v1/tasks/{task_id}` for status
3. Status includes `progress` (0-1) and `progress_message`
4. When `status: completed`, result is in `result` field

Example:
```bash
# Submit large sampling request
curl -X POST http://localhost:8000/api/v1/traces/sample \
  -H "Content-Type: application/json" \
  -d '{"n": 5, "num_samples": 500}'

# Response: {"task_id": "abc-123", "status": "pending", ...}

# Poll for status
curl http://localhost:8000/api/v1/tasks/abc-123
```

## Integration with Scripts

The API uses the same core logic as CLI scripts via the `_core/` package:

```
n-link-analysis/scripts/
├── _core/
│   └── trace_engine.py    # Reusable sampling logic
├── sample-nlink-traces.py # CLI wrapper (uses _core)
└── ...
```

## Remaining Work

- [ ] Basin operations (`/api/v1/basins/*`)
- [ ] Report generation (`/api/v1/reports/*`)
- [ ] `reproduce-main-findings.py --use-api` integration
