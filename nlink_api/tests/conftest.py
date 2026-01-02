"""Pytest fixtures for N-Link API tests.

Provides:
- Mock data loader with synthetic data
- Test client fixture
- Task manager fixture
- Integration test markers
"""

from __future__ import annotations

import tempfile
from dataclasses import dataclass
from pathlib import Path
from typing import TYPE_CHECKING, Any
from unittest.mock import MagicMock, patch

import pandas as pd
import pytest
from fastapi.testclient import TestClient

if TYPE_CHECKING:
    from collections.abc import Generator


# =============================================================================
# Markers
# =============================================================================

def pytest_configure(config):
    """Configure custom markers."""
    config.addinivalue_line(
        "markers",
        "integration: marks tests as integration tests requiring data (deselect with '-m \"not integration\"')"
    )


# =============================================================================
# Synthetic Test Data
# =============================================================================

# Small set of pages for testing
TEST_PAGES = pd.DataFrame({
    "page_id": [1, 2, 3, 4, 5, 6, 7, 8, 9, 10],
    "title": [
        "Massachusetts",
        "Gulf_of_Maine",
        "United_States",
        "North_America",
        "Earth",
        "Solar_System",
        "Milky_Way",
        "Universe",
        "Physics",
        "Science",
    ],
    "namespace": [0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
    "is_redirect": [False, False, False, False, False, False, False, False, False, False],
})

# N-link sequences: for each page_id, the N-th link (link position)
# Format: page_id, link_n1, link_n2, link_n3, link_n4, link_n5...
# Each column represents the target page_id when following the N-th link
TEST_NLINK_SEQUENCES = pd.DataFrame({
    "page_id": [1, 2, 3, 4, 5, 6, 7, 8, 9, 10],
    "link_n1": [3, 1, 4, 5, 6, 7, 8, 9, 10, 3],
    "link_n2": [2, 3, 5, 6, 7, 8, 9, 10, 3, 4],
    "link_n3": [4, 4, 6, 7, 8, 9, 10, 3, 4, 5],
    "link_n4": [5, 5, 7, 8, 9, 10, 3, 4, 5, 6],
    "link_n5": [2, 1, 8, 9, 10, 3, 4, 5, 6, 7],  # Massachusetts(1)->Gulf(2)->Mass(1): cycle!
    "link_n6": [6, 6, 9, 10, 3, 4, 5, 6, 7, 8],
    "link_n7": [7, 7, 10, 3, 4, 5, 6, 7, 8, 9],
    "out_degree": [50, 50, 60, 70, 80, 90, 100, 110, 120, 130],
})


@dataclass
class MockDataPaths:
    """Mock data paths for testing."""
    nlink_sequences: Path
    pages: Path
    multiplex_basin_assignments: Path | None = None
    tunnel_nodes: Path | None = None
    multiplex_edges: Path | None = None
    links: Path | None = None
    links_prose: Path | None = None
    links_resolved: Path | None = None
    redirects: Path | None = None
    disambig_pages: Path | None = None


class MockDataLoader:
    """Mock data loader for testing.

    Provides synthetic data without requiring real data files.
    """

    def __init__(self, temp_dir: Path):
        self._temp_dir = temp_dir
        self._nlink_path = temp_dir / "nlink_sequences.parquet"
        self._pages_path = temp_dir / "pages.parquet"

        # Write test data to temp files
        TEST_NLINK_SEQUENCES.to_parquet(self._nlink_path)
        TEST_PAGES.to_parquet(self._pages_path)

        self._paths = MockDataPaths(
            nlink_sequences=self._nlink_path,
            pages=self._pages_path,
        )

    @property
    def source_name(self) -> str:
        return "mock"

    @property
    def paths(self) -> MockDataPaths:
        return self._paths

    @property
    def nlink_sequences_path(self) -> Path:
        return self._nlink_path

    @property
    def pages_path(self) -> Path:
        return self._pages_path

    def load_nlink_sequences(self) -> pd.DataFrame:
        return pd.read_parquet(self._nlink_path)

    def load_pages(self) -> pd.DataFrame:
        return pd.read_parquet(self._pages_path)

    def validate(self) -> tuple[bool, list[str], list[str]]:
        """Validate that test data files exist."""
        errors = []
        warnings = []

        if not self._nlink_path.exists():
            errors.append(f"Missing: {self._nlink_path}")
        if not self._pages_path.exists():
            errors.append(f"Missing: {self._pages_path}")

        return len(errors) == 0, errors, warnings


# =============================================================================
# Fixtures
# =============================================================================

@pytest.fixture(scope="session")
def temp_data_dir() -> Generator[Path, None, None]:
    """Create a temporary directory with test data files."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)


@pytest.fixture(scope="session")
def mock_data_loader(temp_data_dir: Path) -> MockDataLoader:
    """Create a mock data loader with test data."""
    return MockDataLoader(temp_data_dir)


@pytest.fixture(scope="session")
def mock_analysis_dir(temp_data_dir: Path) -> Path:
    """Create a temporary analysis output directory."""
    analysis_dir = temp_data_dir / "analysis"
    analysis_dir.mkdir(exist_ok=True)
    return analysis_dir


@pytest.fixture
def test_client(mock_data_loader: MockDataLoader, mock_analysis_dir: Path) -> Generator[TestClient, None, None]:
    """Create a test client with mocked dependencies.

    This fixture patches the dependency injection to use mock data.
    Note: Some endpoints may still fail if they use _core modules
    that require specific data formats not provided by the mock.
    """
    from nlink_api.config import Settings, reset_settings
    from nlink_api.dependencies import get_task_manager
    from nlink_api.main import create_app
    from nlink_api.tasks import TaskManager

    # Reset any cached settings
    reset_settings()

    # Create a fresh task manager for each test
    task_manager = TaskManager(max_workers=2, max_history=10)

    # Create mock settings
    mock_settings = MagicMock(spec=Settings)
    mock_settings.data_source = "mock"
    mock_settings.local_data_dir = None
    mock_settings.hf_repo = "test/repo"
    mock_settings.hf_cache_dir = None
    mock_settings.api_prefix = "/api/v1"
    mock_settings.debug = True
    mock_settings.max_workers = 2
    mock_settings.max_task_history = 10
    mock_settings.analysis_output_dir = mock_analysis_dir
    mock_settings.default_analysis_dir = mock_analysis_dir
    mock_settings.report_assets_dir = mock_analysis_dir / "assets"

    def get_mock_data_loader(*args: Any, **kwargs: Any) -> MockDataLoader:
        return mock_data_loader

    def get_mock_settings() -> Settings:
        return mock_settings

    def get_mock_task_manager() -> TaskManager:
        return task_manager

    with (
        patch("nlink_api.dependencies.get_data_loader", get_mock_data_loader),
        patch("nlink_api.config.get_settings", get_mock_settings),
        patch("nlink_api.dependencies.get_task_manager", get_mock_task_manager),
        patch("nlink_api.routers.health.get_data_loader", get_mock_data_loader),
        patch("nlink_api.routers.traces.get_data_loader", get_mock_data_loader),
        patch("nlink_api.routers.data.get_data_loader", get_mock_data_loader),
        patch("nlink_api.routers.basins.get_data_loader", get_mock_data_loader),
    ):
        app = create_app()

        # Override dependencies in the app
        app.dependency_overrides[get_task_manager] = get_mock_task_manager

        with TestClient(app) as client:
            yield client

        # Cleanup
        task_manager.shutdown(wait=False)

    reset_settings()


@pytest.fixture
def task_manager() -> Generator[Any, None, None]:
    """Create a standalone task manager for unit tests."""
    from nlink_api.tasks import TaskManager

    manager = TaskManager(max_workers=2, max_history=10)
    yield manager
    manager.shutdown(wait=False)
