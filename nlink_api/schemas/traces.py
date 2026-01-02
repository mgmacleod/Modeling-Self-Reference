"""Schemas for trace sampling endpoints."""

from __future__ import annotations

from pydantic import BaseModel, Field


class TraceSingleRequest(BaseModel):
    """Request for tracing a single N-link path."""

    start_title: str | None = Field(
        default=None, description="Page title to start from (alternative to page_id)"
    )
    start_page_id: int | None = Field(
        default=None, description="Page ID to start from (alternative to title)"
    )
    n: int = Field(default=5, ge=1, le=100, description="N for N-link rule")
    max_steps: int = Field(default=5000, ge=1, le=100000, description="Maximum trace steps")


class TraceSingleResponse(BaseModel):
    """Response for a single trace."""

    start_page_id: int
    start_title: str | None = None
    terminal_type: str  # HALT, CYCLE, MAX_STEPS
    steps: int
    path: list[int]  # page_ids in order
    path_titles: list[str] | None = None
    cycle_start_index: int | None = None
    cycle_len: int | None = None


class TraceSampleRequest(BaseModel):
    """Request for batch trace sampling."""

    n: int = Field(default=5, ge=1, le=100, description="N for N-link rule")
    num_samples: int = Field(default=100, ge=1, le=10000, description="Number of traces")
    seed: int = Field(default=0, ge=0, description="Starting RNG seed")
    min_outdegree: int = Field(default=50, ge=0, description="Minimum out-degree for start pages")
    max_steps: int = Field(default=5000, ge=1, le=100000, description="Max steps per trace")
    top_cycles_k: int = Field(default=10, ge=0, le=100, description="Top K cycles to return")
    resolve_titles: bool = Field(default=False, description="Resolve titles for cycle nodes")


class CycleInfo(BaseModel):
    """Information about a discovered cycle."""

    cycle_ids: list[int]
    cycle_titles: list[str] | None = None
    count: int
    length: int


class TraceSampleResponse(BaseModel):
    """Response for batch trace sampling.

    For background tasks, this is the result payload.
    """

    n: int
    num_samples: int
    seed0: int
    min_outdegree: int
    max_steps: int
    terminal_counts: dict[str, int]
    avg_steps: float
    avg_path_len: float
    avg_cycle_len: float | None = None
    top_cycles: list[CycleInfo]
    output_file: str | None = None  # Path to TSV if written
