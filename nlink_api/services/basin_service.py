"""Basin mapping and branch analysis service layer."""

from __future__ import annotations

import sys
from pathlib import Path
from typing import TYPE_CHECKING, Callable

from nlink_api.schemas.basins import (
    BasinMapResponse,
    BranchAnalysisResponse,
    BranchInfoResponse,
    LayerInfoResponse,
)

if TYPE_CHECKING:
    from n_link_analysis.scripts.data_loader import DataLoader

# Ensure _core is importable
_scripts_dir = Path(__file__).resolve().parents[2] / "n-link-analysis" / "scripts"
if str(_scripts_dir) not in sys.path:
    sys.path.insert(0, str(_scripts_dir))


class BasinService:
    """Service for basin mapping and branch analysis operations."""

    def __init__(self, loader: "DataLoader"):
        self._loader = loader

    def resolve_cycle_ids(
        self,
        cycle_titles: list[str],
        cycle_page_ids: list[int],
    ) -> list[int]:
        """Resolve cycle specification to page IDs.

        Args:
            cycle_titles: List of page titles to resolve.
            cycle_page_ids: List of page IDs (used directly).

        Returns:
            Combined list of unique page IDs.

        Raises:
            ValueError: If titles cannot be resolved or no IDs provided.
        """
        from _core.basin_engine import resolve_titles_to_ids

        # Resolve titles if provided
        title_to_id: dict[str, int] = {}
        if cycle_titles:
            title_to_id = resolve_titles_to_ids(cycle_titles, self._loader)
            missing = [t for t in cycle_titles if t not in title_to_id]
            if missing:
                raise ValueError(f"Could not resolve titles: {missing}")

        # Combine and dedupe
        all_ids = list(dict.fromkeys([*cycle_page_ids, *title_to_id.values()]))
        if not all_ids:
            raise ValueError("At least one cycle_title or cycle_page_id is required")

        return all_ids

    def map_basin(
        self,
        *,
        n: int = 5,
        cycle_titles: list[str] | None = None,
        cycle_page_ids: list[int] | None = None,
        max_depth: int = 0,
        max_nodes: int = 0,
        write_membership: bool = False,
        tag: str | None = None,
        progress_callback: Callable[[float, str], None] | None = None,
    ) -> BasinMapResponse:
        """Map the basin (reverse-reachable set) from a cycle.

        Args:
            n: N for the N-link rule.
            cycle_titles: Cycle node titles to resolve.
            cycle_page_ids: Cycle node page IDs.
            max_depth: Maximum BFS depth (0 = unlimited).
            max_nodes: Maximum nodes to discover (0 = unlimited).
            write_membership: Whether to write membership Parquet.
            tag: Output file tag.
            progress_callback: Optional callback for progress updates.

        Returns:
            BasinMapResponse with mapping results.
        """
        from _core.basin_engine import map_basin as do_map_basin

        # Resolve cycle IDs
        cycle_ids = self.resolve_cycle_ids(
            cycle_titles or [],
            cycle_page_ids or [],
        )

        # Build output paths
        from nlink_api.config import get_settings

        settings = get_settings()
        analysis_dir = settings.default_analysis_dir
        prefix = tag or f"basin_from_cycle_n={n}"
        layers_path = analysis_dir / f"{prefix}_layers.tsv"
        members_path = (analysis_dir / f"{prefix}_members.parquet") if write_membership else None

        # Run basin mapping
        result = do_map_basin(
            self._loader,
            n=n,
            cycle_page_ids=cycle_ids,
            max_depth=max_depth,
            max_nodes=max_nodes,
            write_layers_tsv=layers_path,
            write_members_parquet=members_path,
            progress_callback=progress_callback,
            verbose=False,  # Suppress prints in API mode
        )

        # Convert to response
        layers = [
            LayerInfoResponse(
                depth=layer.depth,
                new_nodes=layer.new_nodes,
                total_seen=layer.total_seen,
            )
            for layer in result.layers
        ]

        return BasinMapResponse(
            n=result.n,
            cycle_page_ids=result.cycle_page_ids,
            total_nodes=result.total_nodes,
            max_depth_reached=result.max_depth_reached,
            layers=layers,
            stopped_reason=result.stopped_reason,
            layers_tsv_path=result.layers_tsv_path,
            members_parquet_path=result.members_parquet_path,
            elapsed_seconds=result.elapsed_seconds,
        )

    def analyze_branches(
        self,
        *,
        n: int = 5,
        cycle_titles: list[str] | None = None,
        cycle_page_ids: list[int] | None = None,
        max_depth: int = 0,
        top_k: int = 25,
        write_top_k_membership: int = 0,
        tag: str | None = None,
        progress_callback: Callable[[float, str], None] | None = None,
    ) -> BranchAnalysisResponse:
        """Analyze branch structure feeding a cycle.

        Args:
            n: N for the N-link rule.
            cycle_titles: Cycle node titles to resolve.
            cycle_page_ids: Cycle node page IDs.
            max_depth: Maximum BFS depth (0 = unlimited).
            top_k: Number of top branches to return.
            write_top_k_membership: Write membership for top-K branches (0 = none).
            tag: Output file tag.
            progress_callback: Optional callback for progress updates.

        Returns:
            BranchAnalysisResponse with analysis results.
        """
        from _core.branch_engine import analyze_branches as do_analyze_branches

        # Resolve cycle IDs
        cycle_ids = self.resolve_cycle_ids(
            cycle_titles or [],
            cycle_page_ids or [],
        )

        # Run branch analysis
        result = do_analyze_branches(
            self._loader,
            n=n,
            cycle_page_ids=cycle_ids,
            max_depth=max_depth,
            top_k=top_k,
            write_top_k_membership=write_top_k_membership,
            out_prefix=tag,
            progress_callback=progress_callback,
            verbose=False,  # Suppress prints in API mode
        )

        # Convert to response
        branches = [
            BranchInfoResponse(
                rank=b.rank,
                entry_id=b.entry_id,
                entry_title=b.entry_title,
                basin_size=b.basin_size,
                max_depth=b.max_depth,
                enters_cycle_page_id=b.enters_cycle_page_id,
                enters_cycle_title=b.enters_cycle_title,
            )
            for b in result.branches
        ]

        return BranchAnalysisResponse(
            n=result.n,
            cycle_page_ids=result.cycle_page_ids,
            total_basin_nodes=result.total_basin_nodes,
            num_branches=result.num_branches,
            max_depth_reached=result.max_depth_reached,
            branches=branches,
            branches_all_tsv_path=result.branches_all_tsv_path,
            branches_topk_tsv_path=result.branches_topk_tsv_path,
            assignments_parquet_path=result.assignments_parquet_path,
            elapsed_seconds=result.elapsed_seconds,
        )
