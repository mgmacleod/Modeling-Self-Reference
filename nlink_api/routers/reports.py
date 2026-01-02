"""Report generation endpoints."""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import FileResponse

from nlink_api.dependencies import get_task_manager
from nlink_api.schemas.common import TaskSubmittedResponse
from nlink_api.schemas.reports import (
    HumanReportRequest,
    HumanReportResponse,
    ReportListResponse,
    TrunkinessDashboardRequest,
    TrunkinessDashboardResponse,
)
from nlink_api.services.report_service import ReportService
from nlink_api.tasks import TaskManager

router = APIRouter()


def get_report_service() -> ReportService:
    """Dependency to get ReportService instance."""
    return ReportService()


@router.post("/trunkiness")
async def compute_trunkiness_dashboard(
    request: TrunkinessDashboardRequest,
    service: ReportService = Depends(get_report_service),
    task_manager: TaskManager = Depends(get_task_manager),
) -> TrunkinessDashboardResponse | TaskSubmittedResponse:
    """Compute trunkiness dashboard from branch analysis outputs.

    This aggregates branch sizes across basins and computes statistical
    measures of branch concentration (Gini, effective branches, etc.).

    For typical datasets, runs synchronously. For very large datasets,
    can be submitted as a background task.
    """
    # Try synchronous execution first
    try:
        return service.compute_trunkiness_dashboard(
            n=request.n,
            tag=request.tag,
        )
    except FileNotFoundError as e:
        # If no data files found, suggest running branch analysis first
        raise HTTPException(
            status_code=404,
            detail=f"No branch analysis outputs found. Run branch analysis first. {e}",
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/trunkiness/async")
async def compute_trunkiness_dashboard_async(
    request: TrunkinessDashboardRequest,
    task_manager: TaskManager = Depends(get_task_manager),
) -> TaskSubmittedResponse:
    """Compute trunkiness dashboard as a background task.

    Use this endpoint for very large datasets where synchronous
    computation may timeout.
    """

    def run_computation(progress_callback=None):
        svc = ReportService()
        return svc.compute_trunkiness_dashboard(
            n=request.n,
            tag=request.tag,
            progress_callback=progress_callback,
        ).model_dump()

    task_id = task_manager.submit("trunkiness_dashboard", run_computation)

    return TaskSubmittedResponse(
        task_id=task_id,
        task_type="trunkiness_dashboard",
        message=f"Trunkiness dashboard computation started for N={request.n}",
    )


@router.post("/human")
async def generate_human_report(
    request: HumanReportRequest,
    service: ReportService = Depends(get_report_service),
    task_manager: TaskManager = Depends(get_task_manager),
) -> HumanReportResponse | TaskSubmittedResponse:
    """Generate a human-facing Markdown report with charts.

    This generates a comprehensive report with:
    - Trunkiness bar chart and scatter plot
    - Dominance collapse charts
    - Chase series charts (if data available)
    - Overlay comparison charts

    Output is written to n-link-analysis/report/.
    """
    # Try synchronous execution first
    try:
        return service.generate_human_report(
            tag=request.tag,
        )
    except FileNotFoundError as e:
        raise HTTPException(
            status_code=404,
            detail=f"Required data files not found. {e}",
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/human/async")
async def generate_human_report_async(
    request: HumanReportRequest,
    task_manager: TaskManager = Depends(get_task_manager),
) -> TaskSubmittedResponse:
    """Generate human report as a background task.

    Use this endpoint if chart generation takes too long.
    """

    def run_generation(progress_callback=None):
        svc = ReportService()
        return svc.generate_human_report(
            tag=request.tag,
            progress_callback=progress_callback,
        ).model_dump()

    task_id = task_manager.submit("human_report", run_generation)

    return TaskSubmittedResponse(
        task_id=task_id,
        task_type="human_report",
        message=f"Human report generation started for tag={request.tag}",
    )


@router.get("/{task_id}")
async def get_report_task(
    task_id: str,
    task_manager: TaskManager = Depends(get_task_manager),
) -> dict[str, Any]:
    """Get status of a report generation task.

    Returns task status and result (if completed).
    """
    task = task_manager.get_task(task_id)
    if task is None:
        raise HTTPException(status_code=404, detail=f"Task not found: {task_id}")
    return task.to_dict()


@router.get("/list")
async def list_reports(
    service: ReportService = Depends(get_report_service),
) -> ReportListResponse:
    """List available reports.

    Returns a list of generated report files with metadata.
    """
    return service.list_reports()


@router.get("/figures/{filename}")
async def get_figure(
    filename: str,
    service: ReportService = Depends(get_report_service),
) -> FileResponse:
    """Serve a generated figure file.

    Args:
        filename: Name of the figure file (e.g., "trunkiness_top1_share.png")

    Returns:
        The figure file as a PNG image.
    """
    path = service.get_figure_path(filename)
    if path is None:
        raise HTTPException(status_code=404, detail=f"Figure not found: {filename}")

    return FileResponse(
        path=path,
        media_type="image/png",
        filename=filename,
    )
