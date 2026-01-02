"""Task management endpoints."""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends, HTTPException

from nlink_api.dependencies import get_task_manager
from nlink_api.tasks import TaskManager, TaskStatus

router = APIRouter()


@router.get("")
async def list_tasks(
    status: str | None = None,
    task_type: str | None = None,
    task_manager: TaskManager = Depends(get_task_manager),
) -> dict[str, Any]:
    """List all tasks.

    Args:
        status: Filter by status (pending, running, completed, failed, cancelled).
        task_type: Filter by task type.

    Returns:
        List of task records.
    """
    # Parse status filter
    status_filter: TaskStatus | None = None
    if status:
        try:
            status_filter = TaskStatus(status.lower())
        except ValueError:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid status: {status}. "
                f"Valid values: {[s.value for s in TaskStatus]}",
            )

    tasks = task_manager.list_tasks(status=status_filter, task_type=task_type)
    return {
        "tasks": [t.to_dict() for t in tasks],
        "count": len(tasks),
    }


@router.get("/{task_id}")
async def get_task(
    task_id: str,
    task_manager: TaskManager = Depends(get_task_manager),
) -> dict[str, Any]:
    """Get task status and result.

    Args:
        task_id: The task ID to look up.

    Returns:
        Task record including status, progress, and result (if completed).
    """
    task = task_manager.get_task(task_id)
    if task is None:
        raise HTTPException(status_code=404, detail=f"Task not found: {task_id}")
    return task.to_dict()


@router.delete("/{task_id}")
async def cancel_task(
    task_id: str,
    task_manager: TaskManager = Depends(get_task_manager),
) -> dict[str, Any]:
    """Cancel a pending task.

    Only pending tasks can be cancelled. Running tasks will complete.

    Args:
        task_id: The task ID to cancel.

    Returns:
        Cancellation status.
    """
    task = task_manager.get_task(task_id)
    if task is None:
        raise HTTPException(status_code=404, detail=f"Task not found: {task_id}")

    if task.status != TaskStatus.PENDING:
        return {
            "cancelled": False,
            "message": f"Cannot cancel task with status: {task.status.value}",
        }

    cancelled = task_manager.cancel_task(task_id)
    return {
        "cancelled": cancelled,
        "message": "Task cancelled" if cancelled else "Failed to cancel task",
    }


@router.delete("")
async def clear_completed_tasks(
    task_manager: TaskManager = Depends(get_task_manager),
) -> dict[str, Any]:
    """Clear all completed, failed, and cancelled tasks from history.

    Returns:
        Number of tasks cleared.
    """
    count = task_manager.clear_completed()
    return {
        "cleared": count,
        "message": f"Cleared {count} completed tasks",
    }
