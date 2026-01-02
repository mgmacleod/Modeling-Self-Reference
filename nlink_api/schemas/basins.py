"""Schemas for basin mapping and branch analysis endpoints."""

from __future__ import annotations

from pydantic import BaseModel, Field


class BasinMapRequest(BaseModel):
    """Request for mapping a basin from a cycle."""

    n: int = Field(default=5, ge=1, le=100, description="N for N-link rule")
    cycle_titles: list[str] = Field(
        default_factory=list,
        description="Cycle node titles (resolved to page IDs)",
    )
    cycle_page_ids: list[int] = Field(
        default_factory=list,
        description="Cycle node page IDs (alternative to titles)",
    )
    max_depth: int = Field(
        default=0,
        ge=0,
        description="Maximum BFS depth (0 = unlimited)",
    )
    max_nodes: int = Field(
        default=0,
        ge=0,
        description="Maximum nodes to discover (0 = unlimited)",
    )
    write_membership: bool = Field(
        default=False,
        description="Write full membership set to Parquet",
    )
    tag: str | None = Field(
        default=None,
        description="Output file tag (prefix for filenames)",
    )


class LayerInfoResponse(BaseModel):
    """Information about a single BFS layer."""

    depth: int
    new_nodes: int
    total_seen: int


class BasinMapResponse(BaseModel):
    """Response for basin mapping operation."""

    n: int
    cycle_page_ids: list[int]
    total_nodes: int
    max_depth_reached: int
    layers: list[LayerInfoResponse]
    stopped_reason: str
    layers_tsv_path: str | None = None
    members_parquet_path: str | None = None
    elapsed_seconds: float


class BranchAnalysisRequest(BaseModel):
    """Request for branch structure analysis."""

    n: int = Field(default=5, ge=1, le=100, description="N for N-link rule")
    cycle_titles: list[str] = Field(
        default_factory=list,
        description="Cycle node titles (resolved to page IDs)",
    )
    cycle_page_ids: list[int] = Field(
        default_factory=list,
        description="Cycle node page IDs (alternative to titles)",
    )
    max_depth: int = Field(
        default=0,
        ge=0,
        description="Maximum BFS depth (0 = unlimited)",
    )
    top_k: int = Field(
        default=25,
        ge=1,
        le=1000,
        description="Number of top branches to return",
    )
    write_top_k_membership: int = Field(
        default=0,
        ge=0,
        le=1000,
        description="Write membership for top-K branches (0 = none)",
    )
    tag: str | None = Field(
        default=None,
        description="Output file tag (prefix for filenames)",
    )


class BranchInfoResponse(BaseModel):
    """Information about a single branch."""

    rank: int
    entry_id: int
    entry_title: str | None = None
    basin_size: int
    max_depth: int
    enters_cycle_page_id: int
    enters_cycle_title: str | None = None


class BranchAnalysisResponse(BaseModel):
    """Response for branch structure analysis."""

    n: int
    cycle_page_ids: list[int]
    total_basin_nodes: int
    num_branches: int
    max_depth_reached: int
    branches: list[BranchInfoResponse]
    branches_all_tsv_path: str | None = None
    branches_topk_tsv_path: str | None = None
    assignments_parquet_path: str | None = None
    elapsed_seconds: float
