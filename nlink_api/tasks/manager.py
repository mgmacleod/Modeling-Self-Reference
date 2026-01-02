"""Thread-based background task manager.

Provides a lightweight task queue using ThreadPoolExecutor for local development.
Supports progress tracking and task lifecycle management.
"""

from __future__ import annotations

import threading
import uuid
from concurrent.futures import Future, ThreadPoolExecutor
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Callable


class TaskStatus(str, Enum):
    """Task execution status."""

    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


@dataclass
class TaskRecord:
    """Record of a background task."""

    task_id: str
    task_type: str
    status: TaskStatus
    created_at: datetime
    started_at: datetime | None = None
    completed_at: datetime | None = None
    progress: float = 0.0  # 0.0 to 1.0
    progress_message: str = ""
    result: Any = None
    error: str | None = None
    _future: Future | None = field(default=None, repr=False)

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "task_id": self.task_id,
            "task_type": self.task_type,
            "status": self.status.value,
            "created_at": self.created_at.isoformat(),
            "started_at": self.started_at.isoformat() if self.started_at else None,
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
            "progress": self.progress,
            "progress_message": self.progress_message,
            "result": self.result,
            "error": self.error,
        }


class TaskManager:
    """Manages background task execution using ThreadPoolExecutor.

    Thread-safe implementation for concurrent task submission and status queries.

    Example:
        manager = TaskManager(max_workers=2)

        def long_running_task(x: int, progress_callback=None):
            for i in range(x):
                if progress_callback:
                    progress_callback(i / x, f"Step {i+1}/{x}")
                time.sleep(1)
            return {"result": x * 2}

        task_id = manager.submit("my_task", long_running_task, 10)
        status = manager.get_task(task_id)
    """

    def __init__(self, max_workers: int = 2, max_history: int = 100):
        """Initialize the task manager.

        Args:
            max_workers: Maximum concurrent background tasks.
            max_history: Maximum completed tasks to keep in history.
        """
        self._executor = ThreadPoolExecutor(max_workers=max_workers)
        self._tasks: dict[str, TaskRecord] = {}
        self._lock = threading.Lock()
        self._max_history = max_history

    def submit(
        self,
        task_type: str,
        fn: Callable[..., Any],
        *args: Any,
        **kwargs: Any,
    ) -> str:
        """Submit a task for background execution.

        The function should accept an optional `progress_callback` keyword argument
        with signature `(progress: float, message: str) -> None`.

        Args:
            task_type: Type identifier for the task (e.g., "trace_sample").
            fn: Function to execute in background.
            *args: Positional arguments for fn.
            **kwargs: Keyword arguments for fn.

        Returns:
            Task ID for tracking.
        """
        task_id = str(uuid.uuid4())
        record = TaskRecord(
            task_id=task_id,
            task_type=task_type,
            status=TaskStatus.PENDING,
            created_at=datetime.now(),
        )

        def wrapped() -> None:
            with self._lock:
                record.status = TaskStatus.RUNNING
                record.started_at = datetime.now()

            try:
                # Inject progress callback
                result = fn(
                    *args,
                    **kwargs,
                    progress_callback=self._make_progress_callback(task_id),
                )
                with self._lock:
                    record.result = result
                    record.status = TaskStatus.COMPLETED
                    record.progress = 1.0
                    record.completed_at = datetime.now()
            except Exception as e:
                with self._lock:
                    record.error = str(e)
                    record.status = TaskStatus.FAILED
                    record.completed_at = datetime.now()

        future = self._executor.submit(wrapped)
        record._future = future

        with self._lock:
            self._tasks[task_id] = record
            self._cleanup_old_tasks()

        return task_id

    def _make_progress_callback(
        self, task_id: str
    ) -> Callable[[float, str], None]:
        """Create a progress callback for a specific task."""

        def callback(progress: float, message: str = "") -> None:
            with self._lock:
                if task_id in self._tasks:
                    self._tasks[task_id].progress = min(1.0, max(0.0, progress))
                    self._tasks[task_id].progress_message = message

        return callback

    def get_task(self, task_id: str) -> TaskRecord | None:
        """Get a task record by ID."""
        with self._lock:
            return self._tasks.get(task_id)

    def list_tasks(
        self,
        status: TaskStatus | None = None,
        task_type: str | None = None,
    ) -> list[TaskRecord]:
        """List tasks, optionally filtered by status or type."""
        with self._lock:
            tasks = list(self._tasks.values())

        if status is not None:
            tasks = [t for t in tasks if t.status == status]
        if task_type is not None:
            tasks = [t for t in tasks if t.task_type == task_type]

        # Sort by creation time (newest first)
        tasks.sort(key=lambda t: t.created_at, reverse=True)
        return tasks

    def cancel_task(self, task_id: str) -> bool:
        """Attempt to cancel a task.

        Returns True if the task was successfully cancelled.
        Note: Only pending tasks can be cancelled; running tasks will complete.
        """
        with self._lock:
            record = self._tasks.get(task_id)
            if record is None:
                return False

            if record.status == TaskStatus.PENDING and record._future:
                cancelled = record._future.cancel()
                if cancelled:
                    record.status = TaskStatus.CANCELLED
                    record.completed_at = datetime.now()
                return cancelled

            return False

    def clear_completed(self) -> int:
        """Clear all completed, failed, and cancelled tasks from history.

        Returns the number of tasks cleared.
        """
        with self._lock:
            terminal_statuses = {
                TaskStatus.COMPLETED,
                TaskStatus.FAILED,
                TaskStatus.CANCELLED,
            }
            to_remove = [
                tid for tid, t in self._tasks.items()
                if t.status in terminal_statuses
            ]
            for tid in to_remove:
                del self._tasks[tid]
            return len(to_remove)

    def _cleanup_old_tasks(self) -> None:
        """Remove old completed tasks to stay within history limit."""
        terminal_statuses = {
            TaskStatus.COMPLETED,
            TaskStatus.FAILED,
            TaskStatus.CANCELLED,
        }
        completed = [
            t for t in self._tasks.values()
            if t.status in terminal_statuses
        ]

        if len(completed) > self._max_history:
            # Sort by completion time and remove oldest
            completed.sort(
                key=lambda t: t.completed_at or t.created_at,
                reverse=False,
            )
            to_remove = completed[: len(completed) - self._max_history]
            for task in to_remove:
                del self._tasks[task.task_id]

    def shutdown(self, wait: bool = True) -> None:
        """Shutdown the executor.

        Args:
            wait: If True, wait for pending tasks to complete.
        """
        self._executor.shutdown(wait=wait)
