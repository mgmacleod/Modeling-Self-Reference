"""Data source service layer."""

from __future__ import annotations

from typing import TYPE_CHECKING

from nlink_api.schemas.common import DataSourceInfo, ValidationResult

if TYPE_CHECKING:
    from n_link_analysis.scripts.data_loader import DataLoader


class DataService:
    """Service for data source operations."""

    def __init__(self, loader: "DataLoader"):
        self._loader = loader

    def get_source_info(self) -> DataSourceInfo:
        """Get information about the current data source."""
        paths = self._loader.paths
        return DataSourceInfo(
            source=self._loader.source_name,
            nlink_sequences_path=str(paths.nlink_sequences),
            nlink_sequences_exists=paths.nlink_sequences.exists(),
            pages_path=str(paths.pages),
            pages_exists=paths.pages.exists(),
            multiplex_available=(
                paths.multiplex_basin_assignments is not None
                and paths.multiplex_basin_assignments.exists()
            ),
        )

    def validate(self) -> ValidationResult:
        """Validate data files are accessible and well-formed."""
        success, errors = self._loader.validate()
        warnings: list[str] = []

        # Additional checks
        paths = self._loader.paths
        if paths.multiplex_basin_assignments and not paths.multiplex_basin_assignments.exists():
            warnings.append(
                f"Multiplex data not found: {paths.multiplex_basin_assignments}"
            )
        if paths.tunnel_nodes and not paths.tunnel_nodes.exists():
            warnings.append(f"Tunnel nodes not found: {paths.tunnel_nodes}")

        return ValidationResult(
            valid=success,
            errors=errors,
            warnings=warnings,
        )

    def lookup_page_by_id(self, page_id: int) -> dict | None:
        """Look up a page by ID."""
        import duckdb

        pages_path = self._loader.pages_path
        if not pages_path.exists():
            return None

        con = duckdb.connect()
        result = con.execute(
            f"""
            SELECT page_id, title, namespace, is_redirect
            FROM read_parquet('{pages_path.as_posix()}')
            WHERE page_id = {page_id}
            """
        ).fetchone()
        con.close()

        if result is None:
            return None

        return {
            "page_id": result[0],
            "title": result[1],
            "namespace": result[2],
            "is_redirect": result[3],
        }

    def search_pages_by_title(
        self, pattern: str, limit: int = 20
    ) -> list[dict]:
        """Search for pages by title pattern (case-insensitive contains)."""
        import duckdb

        pages_path = self._loader.pages_path
        if not pages_path.exists():
            return []

        # Escape single quotes in pattern
        safe_pattern = pattern.replace("'", "''")

        con = duckdb.connect()
        results = con.execute(
            f"""
            SELECT page_id, title, namespace, is_redirect
            FROM read_parquet('{pages_path.as_posix()}')
            WHERE lower(title) LIKE '%{safe_pattern.lower()}%'
            LIMIT {limit}
            """
        ).fetchall()
        con.close()

        return [
            {
                "page_id": row[0],
                "title": row[1],
                "namespace": row[2],
                "is_redirect": row[3],
            }
            for row in results
        ]

    def get_page_id_by_title(self, title: str) -> int | None:
        """Get page ID from exact title match."""
        import duckdb

        pages_path = self._loader.pages_path
        if not pages_path.exists():
            return None

        # Escape single quotes
        safe_title = title.replace("'", "''")

        con = duckdb.connect()
        result = con.execute(
            f"""
            SELECT page_id
            FROM read_parquet('{pages_path.as_posix()}')
            WHERE title = '{safe_title}'
            """
        ).fetchone()
        con.close()

        return result[0] if result else None
