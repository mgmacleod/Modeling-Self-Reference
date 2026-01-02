"""FastAPI dependency injection for shared resources.

Provides dependency functions for:
- Data loader (local or HuggingFace)
- Task manager
- Settings
"""

from __future__ import annotations

import sys
from functools import lru_cache
from pathlib import Path
from typing import TYPE_CHECKING

from nlink_api.config import Settings, get_settings
from nlink_api.tasks import TaskManager

if TYPE_CHECKING:
    from n_link_analysis.scripts.data_loader import DataLoader


# Add scripts directory to path for imports
_scripts_dir = Path(__file__).resolve().parents[1] / "n-link-analysis" / "scripts"
if str(_scripts_dir) not in sys.path:
    sys.path.insert(0, str(_scripts_dir))


@lru_cache
def get_task_manager() -> TaskManager:
    """Get the global task manager instance."""
    settings = get_settings()
    return TaskManager(
        max_workers=settings.max_workers,
        max_history=settings.max_task_history,
    )


def get_data_loader(settings: Settings | None = None) -> "DataLoader":
    """Get a data loader instance based on settings.

    Creates a new loader each time to support runtime configuration changes.
    """
    if settings is None:
        settings = get_settings()

    # Import here to avoid circular dependencies
    from data_loader import get_data_loader as _get_data_loader

    return _get_data_loader(
        source=settings.data_source,
        local_dir=settings.local_data_dir,
        hf_repo=settings.hf_repo,
        hf_cache_dir=settings.hf_cache_dir,
    )


def get_analysis_output_dir(settings: Settings | None = None) -> Path:
    """Get the analysis output directory."""
    if settings is None:
        settings = get_settings()
    output_dir = settings.default_analysis_dir
    output_dir.mkdir(parents=True, exist_ok=True)
    return output_dir
