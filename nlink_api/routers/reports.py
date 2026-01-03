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
    RenderBasinImagesRequest,
    RenderBasinImagesResponse,
    RenderHtmlRequest,
    RenderHtmlResponse,
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


# --- Render HTML Endpoints ---


@router.post("/render/html")
async def render_html(
    request: RenderHtmlRequest,
    service: ReportService = Depends(get_report_service),
) -> RenderHtmlResponse:
    """Convert markdown reports to styled HTML.

    Converts core research reports from Markdown to self-contained HTML files
    with styling that matches the gallery aesthetic.

    Output files are written to n-link-analysis/report/assets/.
    """
    try:
        return service.render_reports_to_html(dry_run=request.dry_run)
    except FileNotFoundError as e:
        raise HTTPException(status_code=404, detail=f"Source file not found: {e}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Render failed: {e}")


@router.post("/render/html/async")
async def render_html_async(
    request: RenderHtmlRequest,
    task_manager: TaskManager = Depends(get_task_manager),
) -> TaskSubmittedResponse:
    """Convert markdown reports to HTML as a background task.

    Use this endpoint for non-blocking execution.
    """

    def run_render(progress_callback=None):
        svc = ReportService()
        return svc.render_reports_to_html(
            dry_run=request.dry_run,
            progress_callback=progress_callback,
        ).model_dump()

    task_id = task_manager.submit("render_html", run_render)

    return TaskSubmittedResponse(
        task_id=task_id,
        task_type="render_html",
        message="HTML rendering started",
    )


# --- Render Basin Images Endpoints ---


@router.post("/render/basins")
async def render_basin_images(
    request: RenderBasinImagesRequest,
    service: ReportService = Depends(get_report_service),
) -> RenderBasinImagesResponse:
    """Render basin geometry visualizations as static images.

    Generates 3D point cloud visualizations of basin geometry and exports
    them as PNG images for publication, reports, and presentations.

    Output files are written to n-link-analysis/report/assets/.

    Note: This can take several minutes for all basins. Consider using
    the async endpoint for large renders.
    """
    try:
        return service.render_basin_images(
            n=request.n,
            cycles=request.cycles,
            comparison_grid=request.comparison_grid,
            width=request.width,
            height=request.height,
            format=request.format,
            max_plot_points=request.max_plot_points,
        )
    except FileNotFoundError as e:
        raise HTTPException(
            status_code=404,
            detail=f"Basin pointcloud data not found. Run render-full-basin-geometry.py first. {e}",
        )
    except ImportError as e:
        raise HTTPException(
            status_code=500,
            detail=f"Missing dependency (kaleido required): {e}",
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Render failed: {e}")


@router.post("/render/basins/async")
async def render_basin_images_async(
    request: RenderBasinImagesRequest,
    task_manager: TaskManager = Depends(get_task_manager),
) -> TaskSubmittedResponse:
    """Render basin images as a background task.

    Recommended for rendering multiple basins, as this can take several minutes.
    Poll GET /api/v1/tasks/{task_id} to check progress.
    """

    def run_render(progress_callback=None):
        svc = ReportService()
        return svc.render_basin_images(
            n=request.n,
            cycles=request.cycles,
            comparison_grid=request.comparison_grid,
            width=request.width,
            height=request.height,
            format=request.format,
            max_plot_points=request.max_plot_points,
            progress_callback=progress_callback,
        ).model_dump()

    task_id = task_manager.submit("render_basin_images", run_render)

    cycles_desc = request.cycles if request.cycles else "all"
    mode = "comparison grid" if request.comparison_grid else f"cycles={cycles_desc}"

    return TaskSubmittedResponse(
        task_id=task_id,
        task_type="render_basin_images",
        message=f"Basin image rendering started (N={request.n}, {mode})",
    )
