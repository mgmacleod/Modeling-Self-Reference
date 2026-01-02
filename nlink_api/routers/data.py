"""Data source endpoints."""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query

from nlink_api.dependencies import get_data_loader
from nlink_api.schemas.common import DataSourceInfo, ValidationResult
from nlink_api.services.data_service import DataService

router = APIRouter()


def get_data_service() -> DataService:
    """Dependency to get DataService instance."""
    loader = get_data_loader()
    return DataService(loader)


@router.get("/source", response_model=DataSourceInfo)
async def get_source_info(
    service: DataService = Depends(get_data_service),
) -> DataSourceInfo:
    """Get information about the current data source.

    Returns details about which data source is configured (local or HuggingFace)
    and the paths to key data files.
    """
    return service.get_source_info()


@router.post("/validate", response_model=ValidationResult)
async def validate_data(
    service: DataService = Depends(get_data_service),
) -> ValidationResult:
    """Validate that data files are accessible and well-formed.

    Returns validation status along with any errors or warnings.
    """
    return service.validate()


@router.get("/pages/{page_id}")
async def get_page_by_id(
    page_id: int,
    service: DataService = Depends(get_data_service),
) -> dict[str, Any]:
    """Look up a page by its ID.

    Returns page metadata including title, namespace, and redirect status.
    """
    page = service.lookup_page_by_id(page_id)
    if page is None:
        raise HTTPException(status_code=404, detail=f"Page not found: {page_id}")
    return page


@router.get("/pages/search")
async def search_pages(
    q: str = Query(..., min_length=1, description="Search query (case-insensitive contains)"),
    limit: int = Query(default=20, ge=1, le=100, description="Maximum results"),
    service: DataService = Depends(get_data_service),
) -> dict[str, Any]:
    """Search for pages by title.

    Performs a case-insensitive substring search on page titles.
    """
    results = service.search_pages_by_title(q, limit=limit)
    return {
        "query": q,
        "results": results,
        "count": len(results),
    }
