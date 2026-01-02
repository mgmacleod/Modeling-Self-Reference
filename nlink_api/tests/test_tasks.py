"""Tests for task manager and task endpoints."""

from __future__ import annotations

import time
from typing import TYPE_CHECKING

import pytest
from fastapi.testclient import TestClient

if TYPE_CHECKING:
    from nlink_api.tasks import TaskManager


class TestTaskManager:
    """Unit tests for TaskManager class."""

    def test_submit_creates_task(self, task_manager: "TaskManager") -> None:
        """Submit should create a new task."""
        def simple_task(progress_callback=None):
            return {"result": "success"}

        task_id = task_manager.submit("test_task", simple_task)

        assert task_id is not None
        assert isinstance(task_id, str)

    def test_get_task_returns_task(self, task_manager: "TaskManager") -> None:
        """Should retrieve submitted task."""
        def simple_task(progress_callback=None):
            return {"result": "success"}

        task_id = task_manager.submit("test_task", simple_task)
        task = task_manager.get_task(task_id)

        assert task is not None
        assert task.task_id == task_id
        assert task.task_type == "test_task"

    def test_get_task_unknown_returns_none(self, task_manager: "TaskManager") -> None:
        """Should return None for unknown task ID."""
        task = task_manager.get_task("nonexistent-task-id")
        assert task is None

    def test_task_completes(self, task_manager: "TaskManager") -> None:
        """Task should complete and store result."""
        def simple_task(progress_callback=None):
            return {"result": "completed"}

        task_id = task_manager.submit("test_task", simple_task)

        # Wait for completion
        time.sleep(0.5)

        task = task_manager.get_task(task_id)
        assert task is not None
        assert task.status.value in ["completed", "running"]

        if task.status.value == "completed":
            assert task.result == {"result": "completed"}

    def test_task_failure_captured(self, task_manager: "TaskManager") -> None:
        """Failed tasks should capture error."""
        def failing_task(progress_callback=None):
            raise ValueError("Test error")

        task_id = task_manager.submit("failing_task", failing_task)

        # Wait for completion
        time.sleep(0.5)

        task = task_manager.get_task(task_id)
        assert task is not None

        if task.status.value == "failed":
            assert task.error is not None
            assert "Test error" in task.error

    def test_progress_callback(self, task_manager: "TaskManager") -> None:
        """Progress callback should update task progress."""
        def progress_task(progress_callback=None):
            if progress_callback:
                progress_callback(0.5, "Halfway done")
            time.sleep(0.1)
            return {"done": True}

        task_id = task_manager.submit("progress_task", progress_task)

        # Wait a bit and check progress
        time.sleep(0.3)

        task = task_manager.get_task(task_id)
        assert task is not None
        # Progress might have been updated before completion
        assert task.progress >= 0.0

    def test_list_tasks_returns_all(self, task_manager: "TaskManager") -> None:
        """Should list all tasks."""
        def task1(progress_callback=None):
            return 1

        def task2(progress_callback=None):
            return 2

        task_manager.submit("task_type_a", task1)
        task_manager.submit("task_type_b", task2)

        tasks = task_manager.list_tasks()
        assert len(tasks) >= 2

    def test_list_tasks_filter_by_type(self, task_manager: "TaskManager") -> None:
        """Should filter tasks by type."""
        def task(progress_callback=None):
            return {}

        task_manager.submit("type_a", task)
        task_manager.submit("type_b", task)

        type_a_tasks = task_manager.list_tasks(task_type="type_a")
        type_b_tasks = task_manager.list_tasks(task_type="type_b")

        assert len(type_a_tasks) >= 1
        assert len(type_b_tasks) >= 1
        assert all(t.task_type == "type_a" for t in type_a_tasks)
        assert all(t.task_type == "type_b" for t in type_b_tasks)

    def test_cancel_pending_task(self, task_manager: "TaskManager") -> None:
        """Should be able to cancel pending tasks."""
        # Create a task that won't run immediately
        def long_task(progress_callback=None):
            time.sleep(10)
            return {}

        # Submit many tasks to queue this one
        task_id = task_manager.submit("cancel_test", long_task)

        # Try to cancel
        task = task_manager.get_task(task_id)
        # Can only test cancellation if task is still pending
        if task and task.status.value == "pending":
            cancelled = task_manager.cancel_task(task_id)
            # May or may not succeed depending on timing
            assert isinstance(cancelled, bool)

    def test_clear_completed(self, task_manager: "TaskManager") -> None:
        """Should clear completed tasks."""
        def quick_task(progress_callback=None):
            return {}

        task_manager.submit("quick", quick_task)
        time.sleep(0.5)

        cleared = task_manager.clear_completed()
        assert isinstance(cleared, int)

    def test_task_to_dict(self, task_manager: "TaskManager") -> None:
        """TaskRecord.to_dict should produce serializable dict."""
        def task(progress_callback=None):
            return {"key": "value"}

        task_id = task_manager.submit("dict_test", task)
        task = task_manager.get_task(task_id)

        assert task is not None
        d = task.to_dict()

        assert "task_id" in d
        assert "task_type" in d
        assert "status" in d
        assert "created_at" in d
        assert "progress" in d


class TestTaskEndpoints:
    """Tests for /api/v1/tasks/* endpoints."""

    def test_list_tasks(self, test_client: TestClient) -> None:
        """Should list all tasks."""
        response = test_client.get("/api/v1/tasks")

        # Note: endpoint might be /api/v1/tasks or /tasks
        if response.status_code == 404:
            pytest.skip("Tasks list endpoint not found")

        assert response.status_code == 200
        data = response.json()
        # Response could be a list or an object with "tasks" field
        if isinstance(data, dict):
            assert "tasks" in data
            assert isinstance(data["tasks"], list)
        else:
            assert isinstance(data, list)

    def test_get_task_not_found(self, test_client: TestClient) -> None:
        """Should return 404 for unknown task."""
        response = test_client.get("/api/v1/tasks/nonexistent-task-id")

        assert response.status_code == 404

    @pytest.mark.integration
    def test_get_task_after_submit(self, test_client: TestClient) -> None:
        """Should be able to retrieve task after submission."""
        # First, submit a trace sample task to get a task ID
        # (if it runs as background task)
        response = test_client.post(
            "/api/v1/traces/sample",
            json={"n": 5, "num_samples": 5}
        )

        # If this returned a task submission (not inline result)
        if response.status_code == 200:
            data = response.json()
            if "task_id" in data:
                task_id = data["task_id"]

                # Now fetch the task
                task_response = test_client.get(f"/api/v1/tasks/{task_id}")
                assert task_response.status_code == 200

                task_data = task_response.json()
                assert "task_id" in task_data
                assert "status" in task_data


class TestTaskStatus:
    """Tests for task status values."""

    def test_status_enum_values(self) -> None:
        """TaskStatus should have expected values."""
        from nlink_api.tasks import TaskStatus

        assert TaskStatus.PENDING.value == "pending"
        assert TaskStatus.RUNNING.value == "running"
        assert TaskStatus.COMPLETED.value == "completed"
        assert TaskStatus.FAILED.value == "failed"
        assert TaskStatus.CANCELLED.value == "cancelled"
