"""Configuration for the N-Link API.

Supports configuration via environment variables and sensible defaults
for local development.
"""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Literal


@dataclass
class Settings:
    """Application settings."""

    # Data source configuration
    data_source: Literal["local", "huggingface"] = field(
        default_factory=lambda: os.environ.get("DATA_SOURCE", "local").lower()  # type: ignore[return-value]
    )
    local_data_dir: Path | None = field(
        default_factory=lambda: Path(os.environ["LOCAL_DATA_DIR"])
        if "LOCAL_DATA_DIR" in os.environ
        else None
    )
    hf_repo: str = field(
        default_factory=lambda: os.environ.get("HF_DATASET_REPO", "mgmacleod/wikidata1")
    )
    hf_cache_dir: Path | None = field(
        default_factory=lambda: Path(os.environ["HF_CACHE_DIR"])
        if "HF_CACHE_DIR" in os.environ
        else None
    )

    # API configuration
    api_prefix: str = "/api/v1"
    debug: bool = field(
        default_factory=lambda: os.environ.get("DEBUG", "false").lower() == "true"
    )

    # Task manager configuration
    max_workers: int = field(
        default_factory=lambda: int(os.environ.get("MAX_WORKERS", "2"))
    )
    max_task_history: int = field(
        default_factory=lambda: int(os.environ.get("MAX_TASK_HISTORY", "100"))
    )

    # Output configuration
    analysis_output_dir: Path | None = field(
        default_factory=lambda: Path(os.environ["ANALYSIS_OUTPUT_DIR"])
        if "ANALYSIS_OUTPUT_DIR" in os.environ
        else None
    )

    @property
    def repo_root(self) -> Path:
        """Get the repository root directory."""
        return Path(__file__).resolve().parents[1]

    @property
    def default_analysis_dir(self) -> Path:
        """Get the default analysis output directory."""
        if self.analysis_output_dir:
            return self.analysis_output_dir
        return self.repo_root / "data" / "wikipedia" / "processed" / "analysis"

    @property
    def report_assets_dir(self) -> Path:
        """Get the report assets directory."""
        return self.repo_root / "n-link-analysis" / "report" / "assets"


# Global settings instance (created on first access)
_settings: Settings | None = None


def get_settings() -> Settings:
    """Get the global settings instance."""
    global _settings
    if _settings is None:
        _settings = Settings()
    return _settings


def reset_settings() -> None:
    """Reset settings (useful for testing)."""
    global _settings
    _settings = None
