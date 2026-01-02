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
