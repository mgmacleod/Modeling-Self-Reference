"""FastAPI application factory and configuration.

Usage:
    # Development
    uvicorn nlink_api.main:app --reload --port 8000

    # Production-like
    uvicorn nlink_api.main:app --host 0.0.0.0 --port 8000
"""

from __future__ import annotations

from contextlib import asynccontextmanager
from pathlib import Path
from typing import AsyncGenerator

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from nlink_api import __version__
from nlink_api.config import get_settings
from nlink_api.dependencies import get_task_manager


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Application lifespan context manager.

    Handles startup and shutdown events.
    """
    # Startup
    settings = get_settings()
    print(f"Starting N-Link API v{__version__}")
    print(f"  Data source: {settings.data_source}")
    print(f"  Analysis output: {settings.default_analysis_dir}")
    print(f"  Max workers: {settings.max_workers}")

    yield

    # Shutdown
    print("Shutting down N-Link API...")
    task_manager = get_task_manager()
    task_manager.shutdown(wait=True)
    print("Shutdown complete.")


def create_app() -> FastAPI:
    """Create and configure the FastAPI application."""
    settings = get_settings()

    app = FastAPI(
        title="N-Link Basin Analysis API",
        description=(
            "REST API for N-Link Basin Analysis. "
            "Provides endpoints for trace sampling, basin mapping, and report generation."
        ),
        version=__version__,
        lifespan=lifespan,
        docs_url="/docs",
        redoc_url="/redoc",
    )

    # Mount static files for generated assets
    analysis_dir = settings.default_analysis_dir
    if analysis_dir.exists():
        app.mount(
            "/static/analysis",
            StaticFiles(directory=str(analysis_dir)),
            name="analysis",
        )

    report_assets = settings.report_assets_dir
    if report_assets.exists():
        app.mount(
            "/static/assets",
            StaticFiles(directory=str(report_assets)),
            name="assets",
        )

    # Include routers
    from nlink_api.routers import basins, data, health, reports, tasks, traces

    app.include_router(health.router, prefix=settings.api_prefix, tags=["health"])
    app.include_router(
        tasks.router, prefix=f"{settings.api_prefix}/tasks", tags=["tasks"]
    )
    app.include_router(
        data.router, prefix=f"{settings.api_prefix}/data", tags=["data"]
    )
    app.include_router(
        traces.router, prefix=f"{settings.api_prefix}/traces", tags=["traces"]
    )
    app.include_router(
        basins.router, prefix=f"{settings.api_prefix}/basins", tags=["basins"]
    )
    app.include_router(
        reports.router, prefix=f"{settings.api_prefix}/reports", tags=["reports"]
    )

    return app


# Create the app instance
app = create_app()
