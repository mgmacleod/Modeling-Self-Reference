"""Health and status endpoints."""

from __future__ import annotations

import platform
from datetime import datetime
from typing import Any

from fastapi import APIRouter, Depends

from nlink_api import __version__
from nlink_api.config import Settings, get_settings
from nlink_api.dependencies import get_data_loader, get_task_manager
from nlink_api.tasks import TaskManager, TaskStatus

router = APIRouter()


@router.get("/health")
async def health_check() -> dict[str, str]:
    """Basic liveness check.

    Returns a simple status indicator. Use /status for detailed information.
    """
    return {"status": "ok"}


@router.get("/status")
async def detailed_status(
    settings: Settings = Depends(get_settings),
    task_manager: TaskManager = Depends(get_task_manager),
) -> dict[str, Any]:
    """Detailed system status.

    Returns information about:
    - API version
    - Data source configuration
    - Active tasks
    - System information
    """
    # Get data source info
    try:
        loader = get_data_loader(settings)
        data_status = {
            "source": loader.source_name,
            "nlink_sequences_path": str(loader.nlink_sequences_path),
            "nlink_sequences_exists": loader.nlink_sequences_path.exists(),
            "pages_path": str(loader.pages_path),
            "pages_exists": loader.pages_path.exists(),
        }
    except Exception as e:
        data_status = {
            "source": settings.data_source,
            "error": str(e),
        }

    # Get task counts
    all_tasks = task_manager.list_tasks()
    task_counts = {
        "total": len(all_tasks),
        "running": len([t for t in all_tasks if t.status == TaskStatus.RUNNING]),
        "pending": len([t for t in all_tasks if t.status == TaskStatus.PENDING]),
        "completed": len([t for t in all_tasks if t.status == TaskStatus.COMPLETED]),
        "failed": len([t for t in all_tasks if t.status == TaskStatus.FAILED]),
    }

    return {
        "status": "ok",
        "version": __version__,
        "timestamp": datetime.now().isoformat(),
        "data": data_status,
        "tasks": task_counts,
        "system": {
            "python_version": platform.python_version(),
            "platform": platform.platform(),
        },
        "config": {
            "max_workers": settings.max_workers,
            "analysis_output_dir": str(settings.default_analysis_dir),
        },
    }
