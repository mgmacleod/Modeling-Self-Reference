"""Trace sampling endpoints."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from fastapi import APIRouter, Depends, HTTPException

from nlink_api.config import get_settings
from nlink_api.dependencies import get_data_loader, get_task_manager
from nlink_api.schemas.common import TaskSubmittedResponse
from nlink_api.schemas.traces import (
    TraceSampleRequest,
    TraceSampleResponse,
    TraceSingleRequest,
    TraceSingleResponse,
)
from nlink_api.services.trace_service import TraceService
from nlink_api.tasks import TaskManager

router = APIRouter()

# Threshold for running sampling as background task
BACKGROUND_THRESHOLD = 100


def get_trace_service() -> TraceService:
    """Dependency to get TraceService instance."""
    loader = get_data_loader()
    return TraceService(loader)


@router.get("/single", response_model=TraceSingleResponse)
async def trace_single(
    n: int = 5,
    start_title: str | None = None,
    start_page_id: int | None = None,
    max_steps: int = 5000,
    resolve_titles: bool = True,
    service: TraceService = Depends(get_trace_service),
) -> TraceSingleResponse:
    """Trace a single N-link path from a starting page.

    Either start_title or start_page_id must be provided.

    Returns the complete path including terminal type (HALT, CYCLE, or MAX_STEPS)
    and cycle information if applicable.
    """
    if start_title is None and start_page_id is None:
        raise HTTPException(
            status_code=400,
            detail="Either start_title or start_page_id must be provided",
        )

    try:
        return service.trace_single(
            n=n,
            start_page_id=start_page_id,
            start_title=start_title,
            max_steps=max_steps,
            resolve_titles=resolve_titles,
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except FileNotFoundError as e:
        raise HTTPException(status_code=500, detail=f"Data file not found: {e}")


@router.post("/sample")
async def sample_traces(
    request: TraceSampleRequest,
    service: TraceService = Depends(get_trace_service),
    task_manager: TaskManager = Depends(get_task_manager),
) -> TraceSampleResponse | TaskSubmittedResponse:
    """Sample multiple random N-link traces.

    For small requests (num_samples <= 100), runs synchronously.
    For larger requests, submits as a background task.

    Returns either:
    - TraceSampleResponse with results (if synchronous)
    - TaskSubmittedResponse with task_id to poll (if background)
    """
    # Small requests run synchronously
    if request.num_samples <= BACKGROUND_THRESHOLD:
        try:
            return service.sample_traces(
                n=request.n,
                num_samples=request.num_samples,
                seed=request.seed,
                min_outdegree=request.min_outdegree,
                max_steps=request.max_steps,
                top_cycles_k=request.top_cycles_k,
                resolve_titles=request.resolve_titles,
            )
        except FileNotFoundError as e:
            raise HTTPException(status_code=500, detail=f"Data file not found: {e}")

    # Large requests run as background task
    settings = get_settings()
    output_dir = settings.default_analysis_dir
    output_file = output_dir / f"sample_traces_n={request.n}_num={request.num_samples}_seed0={request.seed}_api.tsv"

    def run_sampling(progress_callback=None):
        # Need to recreate service in background thread
        loader = get_data_loader()
        bg_service = TraceService(loader)
        return bg_service.sample_traces(
            n=request.n,
            num_samples=request.num_samples,
            seed=request.seed,
            min_outdegree=request.min_outdegree,
            max_steps=request.max_steps,
            top_cycles_k=request.top_cycles_k,
            resolve_titles=request.resolve_titles,
            output_file=output_file,
            progress_callback=progress_callback,
        ).model_dump()

    task_id = task_manager.submit("trace_sample", run_sampling)

    return TaskSubmittedResponse(
        task_id=task_id,
        task_type="trace_sample",
        message=f"Sampling {request.num_samples} traces as background task",
    )


@router.get("/sample/{task_id}")
async def get_sample_task(
    task_id: str,
    task_manager: TaskManager = Depends(get_task_manager),
) -> dict[str, Any]:
    """Get status of a trace sampling task.

    Returns task status and result (if completed).
    """
    task = task_manager.get_task(task_id)
    if task is None:
        raise HTTPException(status_code=404, detail=f"Task not found: {task_id}")
    return task.to_dict()
