"""Basin mapping and branch analysis endpoints."""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends, HTTPException

from nlink_api.config import get_settings
from nlink_api.dependencies import get_data_loader, get_task_manager
from nlink_api.schemas.basins import (
    BasinMapRequest,
    BasinMapResponse,
    BranchAnalysisRequest,
    BranchAnalysisResponse,
)
from nlink_api.schemas.common import TaskSubmittedResponse
from nlink_api.services.basin_service import BasinService
from nlink_api.tasks import TaskManager

router = APIRouter()


def get_basin_service() -> BasinService:
    """Dependency to get BasinService instance."""
    loader = get_data_loader()
    return BasinService(loader)


@router.post("/map")
async def map_basin(
    request: BasinMapRequest,
    service: BasinService = Depends(get_basin_service),
    task_manager: TaskManager = Depends(get_task_manager),
) -> BasinMapResponse | TaskSubmittedResponse:
    """Map the basin (reverse-reachable set) from a cycle.

    Basin mapping computes all pages that flow into the given cycle
    under the N-link rule using reverse BFS.

    For small requests (limited depth/nodes), runs synchronously.
    For unlimited requests, runs as a background task.

    Returns either:
    - BasinMapResponse with results (if synchronous)
    - TaskSubmittedResponse with task_id to poll (if background)
    """
    # Validate input
    if not request.cycle_titles and not request.cycle_page_ids:
        raise HTTPException(
            status_code=400,
            detail="At least one cycle_title or cycle_page_id is required",
        )

    # Run synchronously for limited requests
    is_limited = (request.max_depth > 0 and request.max_depth <= 50) or (
        request.max_nodes > 0 and request.max_nodes <= 100000
    )

    if is_limited:
        try:
            return service.map_basin(
                n=request.n,
                cycle_titles=request.cycle_titles,
                cycle_page_ids=request.cycle_page_ids,
                max_depth=request.max_depth,
                max_nodes=request.max_nodes,
                write_membership=request.write_membership,
                tag=request.tag,
            )
        except ValueError as e:
            raise HTTPException(status_code=400, detail=str(e))
        except FileNotFoundError as e:
            raise HTTPException(status_code=500, detail=f"Data file not found: {e}")

    # Run as background task for unlimited requests
    def run_mapping(progress_callback=None):
        loader = get_data_loader()
        bg_service = BasinService(loader)
        return bg_service.map_basin(
            n=request.n,
            cycle_titles=request.cycle_titles,
            cycle_page_ids=request.cycle_page_ids,
            max_depth=request.max_depth,
            max_nodes=request.max_nodes,
            write_membership=request.write_membership,
            tag=request.tag,
            progress_callback=progress_callback,
        ).model_dump()

    task_id = task_manager.submit("basin_map", run_mapping)

    return TaskSubmittedResponse(
        task_id=task_id,
        task_type="basin_map",
        message=f"Basin mapping started for N={request.n}",
    )


@router.get("/map/{task_id}")
async def get_map_task(
    task_id: str,
    task_manager: TaskManager = Depends(get_task_manager),
) -> dict[str, Any]:
    """Get status of a basin mapping task.

    Returns task status and result (if completed).
    """
    task = task_manager.get_task(task_id)
    if task is None:
        raise HTTPException(status_code=404, detail=f"Task not found: {task_id}")
    return task.to_dict()


@router.post("/branches")
async def analyze_branches(
    request: BranchAnalysisRequest,
    service: BasinService = Depends(get_basin_service),
    task_manager: TaskManager = Depends(get_task_manager),
) -> BranchAnalysisResponse | TaskSubmittedResponse:
    """Analyze branch structure feeding a cycle.

    Branch analysis partitions the basin by depth-1 entry points and
    computes branch sizes (thickness). This reveals the "river/tributary"
    structure of the basin.

    For limited requests, runs synchronously.
    For unlimited requests, runs as a background task.

    Returns either:
    - BranchAnalysisResponse with results (if synchronous)
    - TaskSubmittedResponse with task_id to poll (if background)
    """
    # Validate input
    if not request.cycle_titles and not request.cycle_page_ids:
        raise HTTPException(
            status_code=400,
            detail="At least one cycle_title or cycle_page_id is required",
        )

    # Run synchronously for limited requests
    is_limited = request.max_depth > 0 and request.max_depth <= 50

    if is_limited:
        try:
            return service.analyze_branches(
                n=request.n,
                cycle_titles=request.cycle_titles,
                cycle_page_ids=request.cycle_page_ids,
                max_depth=request.max_depth,
                top_k=request.top_k,
                write_top_k_membership=request.write_top_k_membership,
                tag=request.tag,
            )
        except ValueError as e:
            raise HTTPException(status_code=400, detail=str(e))
        except FileNotFoundError as e:
            raise HTTPException(status_code=500, detail=f"Data file not found: {e}")

    # Run as background task for unlimited requests
    def run_analysis(progress_callback=None):
        loader = get_data_loader()
        bg_service = BasinService(loader)
        return bg_service.analyze_branches(
            n=request.n,
            cycle_titles=request.cycle_titles,
            cycle_page_ids=request.cycle_page_ids,
            max_depth=request.max_depth,
            top_k=request.top_k,
            write_top_k_membership=request.write_top_k_membership,
            tag=request.tag,
            progress_callback=progress_callback,
        ).model_dump()

    task_id = task_manager.submit("branch_analysis", run_analysis)

    return TaskSubmittedResponse(
        task_id=task_id,
        task_type="branch_analysis",
        message=f"Branch analysis started for N={request.n}",
    )


@router.get("/branches/{task_id}")
async def get_branches_task(
    task_id: str,
    task_manager: TaskManager = Depends(get_task_manager),
) -> dict[str, Any]:
    """Get status of a branch analysis task.

    Returns task status and result (if completed).
    """
    task = task_manager.get_task(task_id)
    if task is None:
        raise HTTPException(status_code=404, detail=f"Task not found: {task_id}")
    return task.to_dict()
