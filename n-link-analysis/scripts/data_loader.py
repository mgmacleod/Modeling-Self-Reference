#!/usr/bin/env python3
"""Data loader abstraction for N-Link analysis.

Supports loading data from:
1. Local files (default): data/wikipedia/processed/
2. HuggingFace dataset: mgmacleod/wikidata1

Usage:
    # In scripts:
    from data_loader import get_data_loader

    loader = get_data_loader()  # Uses DATA_SOURCE env var or defaults to local
    loader = get_data_loader(source="huggingface")  # Explicit HF
    loader = get_data_loader(source="local")  # Explicit local

    # Access data paths
    nlink_path = loader.nlink_sequences_path
    pages_path = loader.pages_path

    # Or load DataFrames directly
    nlink_df = loader.load_nlink_sequences()
    pages_df = loader.load_pages()

Environment Variables:
    DATA_SOURCE: "local" or "huggingface" (default: "local")
    HF_DATASET_REPO: HuggingFace repo ID (default: "mgmacleod/wikidata1")
    HF_CACHE_DIR: Custom cache directory for HF downloads (optional)
"""

from __future__ import annotations

import os
from abc import ABC, abstractmethod
from dataclasses import dataclass
from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    import pandas as pd


# =============================================================================
# Constants
# =============================================================================

REPO_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_LOCAL_DIR = REPO_ROOT / "data" / "wikipedia" / "processed"
DEFAULT_HF_REPO = "mgmacleod/wikidata1"


# =============================================================================
# Data Loader Interface
# =============================================================================

@dataclass
class DataPaths:
    """Container for all data file paths."""

    # Source data (for computing analysis from scratch)
    nlink_sequences: Path
    pages: Path

    # Multiplex analysis results (pre-computed)
    multiplex_basin_assignments: Path | None = None
    tunnel_nodes: Path | None = None
    multiplex_edges: Path | None = None

    # Optional source files
    links: Path | None = None
    links_prose: Path | None = None
    links_resolved: Path | None = None
    redirects: Path | None = None
    disambig_pages: Path | None = None


class DataLoader(ABC):
    """Abstract base class for data loaders."""

    @property
    @abstractmethod
    def source_name(self) -> str:
        """Human-readable name of the data source."""
        ...

    @property
    @abstractmethod
    def paths(self) -> DataPaths:
        """Get all data file paths."""
        ...

    @property
    def nlink_sequences_path(self) -> Path:
        """Path to nlink_sequences.parquet."""
        return self.paths.nlink_sequences

    @property
    def pages_path(self) -> Path:
        """Path to pages.parquet."""
        return self.paths.pages

    @property
    def multiplex_basin_assignments_path(self) -> Path | None:
        """Path to multiplex_basin_assignments.parquet (may be None)."""
        return self.paths.multiplex_basin_assignments

    @property
    def tunnel_nodes_path(self) -> Path | None:
        """Path to tunnel_nodes.parquet (may be None)."""
        return self.paths.tunnel_nodes

    def load_nlink_sequences(self, columns: list[str] | None = None) -> "pd.DataFrame":
        """Load nlink_sequences as a pandas DataFrame."""
        import pandas as pd
        path = self.nlink_sequences_path
        if not path.exists():
            raise FileNotFoundError(f"nlink_sequences not found: {path}")
        return pd.read_parquet(path, columns=columns)

    def load_pages(self, columns: list[str] | None = None) -> "pd.DataFrame":
        """Load pages as a pandas DataFrame."""
        import pandas as pd
        path = self.pages_path
        if not path.exists():
            raise FileNotFoundError(f"pages not found: {path}")
        return pd.read_parquet(path, columns=columns)

    def load_multiplex_basin_assignments(self, columns: list[str] | None = None) -> "pd.DataFrame":
        """Load multiplex_basin_assignments as a pandas DataFrame."""
        import pandas as pd
        path = self.multiplex_basin_assignments_path
        if path is None or not path.exists():
            raise FileNotFoundError(f"multiplex_basin_assignments not found: {path}")
        return pd.read_parquet(path, columns=columns)

    def load_tunnel_nodes(self, columns: list[str] | None = None) -> "pd.DataFrame":
        """Load tunnel_nodes as a pandas DataFrame."""
        import pandas as pd
        path = self.tunnel_nodes_path
        if path is None or not path.exists():
            raise FileNotFoundError(f"tunnel_nodes not found: {path}")
        return pd.read_parquet(path, columns=columns)

    @abstractmethod
    def validate(self) -> tuple[bool, list[str]]:
        """Validate that required data files are accessible.

        Returns:
            (success, list of error messages)
        """
        ...

    def get_analysis_output_dir(self) -> Path:
        """Get the directory for analysis outputs.

        For local data, this is data/wikipedia/processed/analysis/
        For HF data, this is a local cache directory.
        """
        # Default to local analysis directory
        analysis_dir = DEFAULT_LOCAL_DIR / "analysis"
        analysis_dir.mkdir(parents=True, exist_ok=True)
        return analysis_dir


# =============================================================================
# Local File Loader
# =============================================================================

class LocalDataLoader(DataLoader):
    """Loads data from local filesystem."""

    def __init__(self, base_dir: Path | None = None):
        self._base_dir = base_dir or DEFAULT_LOCAL_DIR
        self._paths: DataPaths | None = None

    @property
    def source_name(self) -> str:
        return f"local:{self._base_dir}"

    @property
    def paths(self) -> DataPaths:
        if self._paths is None:
            base = self._base_dir
            multiplex = base / "multiplex"

            self._paths = DataPaths(
                nlink_sequences=base / "nlink_sequences.parquet",
                pages=base / "pages.parquet",
                multiplex_basin_assignments=multiplex / "multiplex_basin_assignments.parquet" if multiplex.exists() else None,
                tunnel_nodes=multiplex / "tunnel_nodes.parquet" if multiplex.exists() else None,
                multiplex_edges=multiplex / "multiplex_edges.parquet" if multiplex.exists() else None,
                links=base / "links.parquet",
                links_prose=base / "links_prose.parquet",
                links_resolved=base / "links_resolved.parquet",
                redirects=base / "redirects.parquet",
                disambig_pages=base / "disambig_pages.parquet",
            )
        return self._paths

    def validate(self) -> tuple[bool, list[str]]:
        errors = []

        # Check required files
        if not self.paths.nlink_sequences.exists():
            errors.append(f"Missing required file: {self.paths.nlink_sequences}")
        if not self.paths.pages.exists():
            errors.append(f"Missing required file: {self.paths.pages}")

        return len(errors) == 0, errors

    def get_analysis_output_dir(self) -> Path:
        analysis_dir = self._base_dir / "analysis"
        analysis_dir.mkdir(parents=True, exist_ok=True)
        return analysis_dir


# =============================================================================
# HuggingFace Dataset Loader
# =============================================================================

class HuggingFaceDataLoader(DataLoader):
    """Loads data from HuggingFace dataset repository.

    Downloads the dataset on first access and caches it locally.
    """

    def __init__(
        self,
        repo_id: str | None = None,
        cache_dir: Path | None = None,
        config: str = "default",
    ):
        self._repo_id = repo_id or os.environ.get("HF_DATASET_REPO", DEFAULT_HF_REPO)
        self._cache_dir = cache_dir or self._get_default_cache_dir()
        self._config = config
        self._paths: DataPaths | None = None
        self._downloaded = False

    def _get_default_cache_dir(self) -> Path:
        """Get default cache directory for HF downloads."""
        # Check environment variable first
        env_cache = os.environ.get("HF_CACHE_DIR")
        if env_cache:
            return Path(env_cache)

        # Default to ~/.cache/wikipedia-nlink-basins
        return Path.home() / ".cache" / "wikipedia-nlink-basins"

    @property
    def source_name(self) -> str:
        return f"huggingface:{self._repo_id}"

    @property
    def local_dir(self) -> Path:
        """Directory where HF data is cached locally."""
        return self._cache_dir / self._repo_id.replace("/", "_")

    def _ensure_downloaded(self) -> None:
        """Download dataset if not already cached."""
        if self._downloaded:
            return

        # Check if already downloaded (quick check for key file)
        source_dir = self.local_dir / "data" / "source"
        if (source_dir / "nlink_sequences.parquet").exists():
            self._downloaded = True
            return

        print(f"Downloading dataset from HuggingFace: {self._repo_id}")
        print(f"Cache directory: {self.local_dir}")

        try:
            from huggingface_hub import snapshot_download
        except ImportError:
            raise ImportError(
                "huggingface_hub not installed. "
                "Run: pip install huggingface_hub"
            )

        self.local_dir.mkdir(parents=True, exist_ok=True)

        snapshot_download(
            repo_id=self._repo_id,
            repo_type="dataset",
            local_dir=str(self.local_dir),
            local_dir_use_symlinks=False,
        )

        print(f"Download complete: {self.local_dir}")
        self._downloaded = True

    @property
    def paths(self) -> DataPaths:
        if self._paths is None:
            self._ensure_downloaded()

            base = self.local_dir / "data"
            source = base / "source"
            multiplex = base / "multiplex"

            self._paths = DataPaths(
                nlink_sequences=source / "nlink_sequences.parquet",
                pages=source / "pages.parquet",
                multiplex_basin_assignments=multiplex / "multiplex_basin_assignments.parquet" if multiplex.exists() else None,
                tunnel_nodes=multiplex / "tunnel_nodes.parquet" if multiplex.exists() else None,
                multiplex_edges=multiplex / "multiplex_edges.parquet" if multiplex.exists() else None,
            )
        return self._paths

    def validate(self) -> tuple[bool, list[str]]:
        errors = []

        try:
            self._ensure_downloaded()
        except Exception as e:
            errors.append(f"Failed to download dataset: {e}")
            return False, errors

        # Check required files
        if not self.paths.nlink_sequences.exists():
            errors.append(f"Missing required file: {self.paths.nlink_sequences}")
        if not self.paths.pages.exists():
            errors.append(f"Missing required file: {self.paths.pages}")

        return len(errors) == 0, errors

    def get_analysis_output_dir(self) -> Path:
        """Get analysis output directory.

        For HF data, we create an analysis dir alongside the cached data.
        """
        analysis_dir = self.local_dir / "data" / "analysis"
        analysis_dir.mkdir(parents=True, exist_ok=True)
        return analysis_dir


# =============================================================================
# Factory Function
# =============================================================================

def get_data_loader(
    source: str | None = None,
    local_dir: Path | None = None,
    hf_repo: str | None = None,
    hf_cache_dir: Path | None = None,
) -> DataLoader:
    """Get a data loader for the specified source.

    Args:
        source: "local" or "huggingface". If None, uses DATA_SOURCE env var
                or defaults to "local".
        local_dir: Override local data directory (for local source).
        hf_repo: Override HuggingFace repo ID (for huggingface source).
        hf_cache_dir: Override HF cache directory (for huggingface source).

    Returns:
        Configured DataLoader instance.

    Examples:
        # Use environment variable or default
        loader = get_data_loader()

        # Explicit local
        loader = get_data_loader(source="local")

        # Explicit HuggingFace
        loader = get_data_loader(source="huggingface")

        # Custom local directory
        loader = get_data_loader(source="local", local_dir=Path("/data/wiki"))
    """
    if source is None:
        source = os.environ.get("DATA_SOURCE", "local").lower()

    source = source.lower().strip()

    if source in ("local", "file", "filesystem"):
        return LocalDataLoader(base_dir=local_dir)

    elif source in ("huggingface", "hf", "hub"):
        return HuggingFaceDataLoader(
            repo_id=hf_repo,
            cache_dir=hf_cache_dir,
        )

    else:
        raise ValueError(
            f"Unknown data source: {source!r}. "
            f"Expected 'local' or 'huggingface'."
        )


def add_data_source_args(parser) -> None:
    """Add standard data source arguments to an argparse parser.

    Adds:
        --data-source: "local" or "huggingface"
        --local-dir: Override local data directory
        --hf-repo: Override HuggingFace repo ID
        --hf-cache-dir: Override HF cache directory

    Usage:
        parser = argparse.ArgumentParser()
        add_data_source_args(parser)
        args = parser.parse_args()
        loader = get_data_loader_from_args(args)
    """
    group = parser.add_argument_group("Data Source")
    group.add_argument(
        "--data-source",
        choices=["local", "huggingface"],
        default=None,
        help="Data source: 'local' (default) or 'huggingface'. "
             "Can also be set via DATA_SOURCE env var.",
    )
    group.add_argument(
        "--local-dir",
        type=Path,
        default=None,
        help="Override local data directory (for --data-source=local)",
    )
    group.add_argument(
        "--hf-repo",
        type=str,
        default=None,
        help=f"Override HuggingFace repo ID (default: {DEFAULT_HF_REPO})",
    )
    group.add_argument(
        "--hf-cache-dir",
        type=Path,
        default=None,
        help="Override HuggingFace cache directory",
    )


def get_data_loader_from_args(args) -> DataLoader:
    """Create a DataLoader from parsed command-line arguments.

    Args:
        args: Namespace from argparse with data source arguments
              (added by add_data_source_args).

    Returns:
        Configured DataLoader instance.
    """
    return get_data_loader(
        source=getattr(args, "data_source", None),
        local_dir=getattr(args, "local_dir", None),
        hf_repo=getattr(args, "hf_repo", None),
        hf_cache_dir=getattr(args, "hf_cache_dir", None),
    )


# =============================================================================
# CLI for Testing
# =============================================================================

def main():
    """Test the data loader."""
    import argparse

    parser = argparse.ArgumentParser(
        description="Test data loader",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    add_data_source_args(parser)
    parser.add_argument(
        "--validate",
        action="store_true",
        help="Run validation checks",
    )

    args = parser.parse_args()
    loader = get_data_loader_from_args(args)

    print(f"Data source: {loader.source_name}")
    print()

    print("Paths:")
    paths = loader.paths
    print(f"  nlink_sequences: {paths.nlink_sequences}")
    print(f"    exists: {paths.nlink_sequences.exists()}")
    print(f"  pages: {paths.pages}")
    print(f"    exists: {paths.pages.exists()}")

    if paths.multiplex_basin_assignments:
        print(f"  multiplex_basin_assignments: {paths.multiplex_basin_assignments}")
        print(f"    exists: {paths.multiplex_basin_assignments.exists()}")

    if paths.tunnel_nodes:
        print(f"  tunnel_nodes: {paths.tunnel_nodes}")
        print(f"    exists: {paths.tunnel_nodes.exists()}")

    print()
    print(f"Analysis output dir: {loader.get_analysis_output_dir()}")

    if args.validate:
        print()
        print("Validation:")
        success, errors = loader.validate()
        if success:
            print("  All checks passed!")
        else:
            print("  Errors:")
            for err in errors:
                print(f"    - {err}")
        return 0 if success else 1

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
