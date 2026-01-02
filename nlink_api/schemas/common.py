"""Common schema definitions shared across endpoints."""

from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import BaseModel


class ErrorResponse(BaseModel):
    """Standard error response."""

    error: str
    detail: str | None = None


class TaskStatusResponse(BaseModel):
    """Background task status response."""

    task_id: str
    task_type: str
    status: str  # pending, running, completed, failed, cancelled
    progress: float
    progress_message: str
    created_at: datetime
    started_at: datetime | None = None
    completed_at: datetime | None = None
    result: Any = None
    error: str | None = None

    model_config = {"from_attributes": True}


class TaskSubmittedResponse(BaseModel):
    """Response when a background task is submitted."""

    task_id: str
    task_type: str
    status: str = "pending"
    message: str = "Task submitted"


class DataSourceInfo(BaseModel):
    """Information about the current data source."""

    source: str
    nlink_sequences_path: str
    nlink_sequences_exists: bool
    pages_path: str
    pages_exists: bool
    multiplex_available: bool = False


class ValidationResult(BaseModel):
    """Result of data validation."""

    valid: bool
    errors: list[str] = []
    warnings: list[str] = []
