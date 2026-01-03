"""Schemas for report generation endpoints."""

from __future__ import annotations

from pydantic import BaseModel, Field


class TrunkinessDashboardRequest(BaseModel):
    """Request for computing trunkiness dashboard."""

    n: int = Field(default=5, ge=1, le=100, description="N for N-link rule")
    tag: str = Field(
        default="bootstrap_2025-12-30",
        description="Tag used in the output filename",
    )


class TrunkinessCycleStatsResponse(BaseModel):
    """Trunkiness statistics for a single cycle/basin."""

    cycle_key: str
    cycle_len: int
    total_basin_nodes: int
    n_branches: int
    top1_branch_size: int
    top1_share_total: float
    top5_share_total: float
    top10_share_total: float
    effective_branches: float
    gini_branch_sizes: float
    entropy_norm: float
    dominant_entry_title: str | None = None
    dominant_enters_cycle_title: str | None = None
    dominant_max_depth: int | None = None
    branches_all_path: str


class TrunkinessDashboardResponse(BaseModel):
    """Response for trunkiness dashboard computation."""

    n: int
    tag: str
    stats: list[TrunkinessCycleStatsResponse]
    output_tsv_path: str | None = None
    elapsed_seconds: float


class HumanReportRequest(BaseModel):
    """Request for generating a human-facing report."""

    tag: str = Field(
        default="bootstrap_2025-12-30",
        description="Tag to match for dashboard files",
    )


class FigureInfoResponse(BaseModel):
    """Information about a generated figure."""

    name: str
    path: str
    description: str


class HumanReportResponse(BaseModel):
    """Response for human report generation."""

    tag: str
    report_path: str
    assets_dir: str
    figures: list[FigureInfoResponse]
    trunk_data_path: str | None = None
    collapse_data_path: str | None = None
    chain_data_paths: list[str] = Field(default_factory=list)
    elapsed_seconds: float


class ReportListItem(BaseModel):
    """Summary of an available report."""

    tag: str
    report_path: str
    created_at: str | None = None
    figure_count: int = 0


class ReportListResponse(BaseModel):
    """List of available reports."""

    reports: list[ReportListItem]


# --- Render HTML Endpoints ---


class RenderHtmlRequest(BaseModel):
    """Request for rendering markdown reports to HTML."""

    dry_run: bool = Field(
        default=False,
        description="If true, show what would be done without writing files",
    )


class RenderHtmlResponse(BaseModel):
    """Response for HTML rendering."""

    rendered: list[str] = Field(description="List of generated HTML filenames")
    output_dir: str = Field(description="Directory where files were written")
    count: int = Field(description="Number of files rendered")
    elapsed_seconds: float


# --- Render Basin Images Endpoints ---


class RenderBasinImagesRequest(BaseModel):
    """Request for rendering basin geometry images."""

    n: int = Field(default=5, ge=1, le=100, description="N for N-link rule")
    cycles: list[str] | None = Field(
        default=None,
        description="Specific cycle names to render. If None, renders all known cycles.",
    )
    comparison_grid: bool = Field(
        default=False,
        description="Create a comparison grid of all basins instead of individual images",
    )
    width: int = Field(default=1200, ge=100, le=4000, description="Image width in pixels")
    height: int = Field(default=800, ge=100, le=4000, description="Image height in pixels")
    format: str = Field(default="png", description="Output format: png, svg, or pdf")
    max_plot_points: int = Field(
        default=120_000,
        ge=1000,
        description="Maximum points per plot (samples if exceeded)",
    )


class RenderBasinImagesResponse(BaseModel):
    """Response for basin image rendering."""

    rendered: list[str] = Field(description="List of generated image filenames")
    output_dir: str = Field(description="Directory where files were written")
    count: int = Field(description="Number of images rendered")
    elapsed_seconds: float
