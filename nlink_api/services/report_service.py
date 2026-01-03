"""Report generation service layer."""

from __future__ import annotations

import sys
import time
from pathlib import Path
from typing import Callable

from nlink_api.config import get_settings
from nlink_api.schemas.reports import (
    FigureInfoResponse,
    HumanReportResponse,
    RenderBasinImagesResponse,
    RenderHtmlResponse,
    ReportListItem,
    ReportListResponse,
    TrunkinessCycleStatsResponse,
    TrunkinessDashboardResponse,
)

# Ensure _core is importable
_scripts_dir = Path(__file__).resolve().parents[2] / "n-link-analysis" / "scripts"
if str(_scripts_dir) not in sys.path:
    sys.path.insert(0, str(_scripts_dir))


class ReportService:
    """Service for report generation operations."""

    def __init__(self) -> None:
        self._settings = get_settings()

    def compute_trunkiness_dashboard(
        self,
        *,
        n: int = 5,
        tag: str = "bootstrap_2025-12-30",
        progress_callback: Callable[[float, str], None] | None = None,
    ) -> TrunkinessDashboardResponse:
        """Compute trunkiness dashboard from branch analysis outputs.

        Args:
            n: N for the N-link rule.
            tag: Tag used in the output filename.
            progress_callback: Optional callback for progress updates.

        Returns:
            TrunkinessDashboardResponse with computed statistics.
        """
        from _core.dashboard_engine import compute_trunkiness_dashboard as do_compute

        result = do_compute(
            analysis_dir=self._settings.default_analysis_dir,
            n=n,
            tag=tag,
            write_output=True,
            progress_callback=progress_callback,
            verbose=False,  # Suppress prints in API mode
        )

        # Convert to response
        stats = [
            TrunkinessCycleStatsResponse(
                cycle_key=s.cycle_key,
                cycle_len=s.cycle_len,
                total_basin_nodes=s.total_basin_nodes,
                n_branches=s.n_branches,
                top1_branch_size=s.top1_branch_size,
                top1_share_total=s.top1_share_total,
                top5_share_total=s.top5_share_total,
                top10_share_total=s.top10_share_total,
                effective_branches=s.effective_branches,
                gini_branch_sizes=s.gini_branch_sizes,
                entropy_norm=s.entropy_norm,
                dominant_entry_title=s.dominant_entry_title,
                dominant_enters_cycle_title=s.dominant_enters_cycle_title,
                dominant_max_depth=s.dominant_max_depth,
                branches_all_path=s.branches_all_path,
            )
            for s in result.stats
        ]

        return TrunkinessDashboardResponse(
            n=result.n,
            tag=result.tag,
            stats=stats,
            output_tsv_path=result.output_tsv_path,
            elapsed_seconds=result.elapsed_seconds,
        )

    def generate_human_report(
        self,
        *,
        tag: str = "bootstrap_2025-12-30",
        progress_callback: Callable[[float, str], None] | None = None,
    ) -> HumanReportResponse:
        """Generate a human-facing report with charts.

        Args:
            tag: Tag to match for dashboard files.
            progress_callback: Optional callback for progress updates.

        Returns:
            HumanReportResponse with paths to generated files.
        """
        from _core.report_engine import generate_report as do_generate

        analysis_dir = self._settings.default_analysis_dir
        report_dir = self._settings.repo_root / "n-link-analysis" / "report"

        result = do_generate(
            analysis_dir=analysis_dir,
            report_dir=report_dir,
            tag=tag,
            repo_root=self._settings.repo_root,
            progress_callback=progress_callback,
            verbose=False,  # Suppress prints in API mode
        )

        # Convert to response
        figures = [
            FigureInfoResponse(
                name=f.name,
                path=f.path,
                description=f.description,
            )
            for f in result.figures
        ]

        return HumanReportResponse(
            tag=result.tag,
            report_path=result.report_path,
            assets_dir=result.assets_dir,
            figures=figures,
            trunk_data_path=result.trunk_data_path,
            collapse_data_path=result.collapse_data_path,
            chain_data_paths=result.chain_data_paths,
            elapsed_seconds=result.elapsed_seconds,
        )

    def list_reports(self) -> ReportListResponse:
        """List available reports.

        Returns:
            ReportListResponse with available reports.
        """
        report_dir = self._settings.repo_root / "n-link-analysis" / "report"
        reports: list[ReportListItem] = []

        # Find all report markdown files
        for md_path in sorted(report_dir.glob("*.md")):
            # Try to extract tag from filename
            name = md_path.stem
            if name == "overview":
                tag = "default"
            else:
                tag = name

            # Count figures in assets
            assets_dir = report_dir / "assets"
            figure_count = len(list(assets_dir.glob("*.png"))) if assets_dir.exists() else 0

            # Get modification time
            stat = md_path.stat()
            from datetime import datetime

            created_at = datetime.fromtimestamp(stat.st_mtime).isoformat()

            reports.append(
                ReportListItem(
                    tag=tag,
                    report_path=str(md_path),
                    created_at=created_at,
                    figure_count=figure_count,
                )
            )

        return ReportListResponse(reports=reports)

    def get_figure_path(self, filename: str) -> Path | None:
        """Get the path to a figure file.

        Args:
            filename: Name of the figure file.

        Returns:
            Path to the figure file, or None if not found.
        """
        assets_dir = self._settings.report_assets_dir
        path = assets_dir / filename

        if path.exists() and path.is_file():
            return path
        return None

    def render_reports_to_html(
        self,
        *,
        dry_run: bool = False,
        progress_callback: Callable[[float, str], None] | None = None,
    ) -> RenderHtmlResponse:
        """Convert markdown reports to styled HTML.

        Args:
            dry_run: If True, show what would be done without writing files.
            progress_callback: Optional callback for progress updates.

        Returns:
            RenderHtmlResponse with list of rendered files.
        """
        start_time = time.time()

        # Import the render script functions
        render_script = self._settings.repo_root / "n-link-analysis" / "scripts" / "render-reports-to-html.py"
        if str(render_script.parent) not in sys.path:
            sys.path.insert(0, str(render_script.parent))

        # Import the module components we need
        import importlib.util
        spec = importlib.util.spec_from_file_location("render_reports", render_script)
        render_module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(render_module)

        report_dir = self._settings.repo_root / "n-link-analysis" / "report"
        assets_dir = self._settings.report_assets_dir
        assets_dir.mkdir(parents=True, exist_ok=True)

        rendered = []
        total = len(render_module.REPORTS)

        for i, config in enumerate(render_module.REPORTS):
            if progress_callback:
                progress_callback(i / total, f"Converting {config.source}")

            if render_module.convert_report(config, report_dir, assets_dir, dry_run):
                rendered.append(config.output)

        if progress_callback:
            progress_callback(1.0, f"Completed {len(rendered)} reports")

        elapsed = time.time() - start_time

        return RenderHtmlResponse(
            rendered=rendered,
            output_dir=str(assets_dir),
            count=len(rendered),
            elapsed_seconds=elapsed,
        )

    def render_basin_images(
        self,
        *,
        n: int = 5,
        cycles: list[str] | None = None,
        comparison_grid: bool = False,
        width: int = 1200,
        height: int = 800,
        format: str = "png",
        max_plot_points: int = 120_000,
        progress_callback: Callable[[float, str], None] | None = None,
    ) -> RenderBasinImagesResponse:
        """Render basin geometry visualizations as static images.

        Args:
            n: N for the N-link rule.
            cycles: Specific cycle names to render. If None, renders all known cycles.
            comparison_grid: If True, create a comparison grid instead of individual images.
            width: Image width in pixels.
            height: Image height in pixels.
            format: Output format (png, svg, pdf).
            max_plot_points: Maximum points per plot.
            progress_callback: Optional callback for progress updates.

        Returns:
            RenderBasinImagesResponse with list of rendered files.
        """
        start_time = time.time()

        # Import the render script functions
        viz_dir = self._settings.repo_root / "n-link-analysis" / "viz"
        render_script = viz_dir / "batch-render-basin-images.py"
        if str(viz_dir) not in sys.path:
            sys.path.insert(0, str(viz_dir))

        import importlib.util
        spec = importlib.util.spec_from_file_location("batch_render", render_script)
        render_module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(render_module)

        output_dir = self._settings.report_assets_dir
        output_dir.mkdir(parents=True, exist_ok=True)

        rendered = []

        fig_kwargs = {
            "max_points": max_plot_points,
            "seed": 0,
            "colorscale": "Viridis",
            "opacity": 0.85,
            "show_axes": False,
        }

        if comparison_grid:
            if progress_callback:
                progress_callback(0.1, "Creating comparison grid")

            path = render_module.create_comparison_grid(
                n,
                render_module.N5_CYCLES,
                output_dir=output_dir,
                width=width,
                height=height,
                format=format,
            )
            if path:
                rendered.append(path.name)

            if progress_callback:
                progress_callback(1.0, "Comparison grid complete")

        else:
            # Determine which cycles to render
            if cycles:
                # Match user-specified cycle names
                cycles_to_render = []
                for name in cycles:
                    matched = False
                    for cycle_slug in render_module.N5_CYCLES:
                        if name.lower() in cycle_slug.lower():
                            cycles_to_render.append(cycle_slug)
                            matched = True
                            break
                    if not matched:
                        # Try exact match
                        cycles_to_render.append(name)
            else:
                cycles_to_render = render_module.N5_CYCLES

            total = len(cycles_to_render)
            for i, cycle_slug in enumerate(cycles_to_render):
                if progress_callback:
                    progress_callback(i / total, f"Rendering {cycle_slug}")

                cycle_name = cycle_slug.replace("_", " ")
                path = render_module.render_single_basin(
                    n,
                    cycle_slug,
                    cycle_name,
                    output_dir=output_dir,
                    width=width,
                    height=height,
                    format=format,
                    **fig_kwargs,
                )
                if path:
                    rendered.append(path.name)

            if progress_callback:
                progress_callback(1.0, f"Completed {len(rendered)} basins")

        elapsed = time.time() - start_time

        return RenderBasinImagesResponse(
            rendered=rendered,
            output_dir=str(output_dir),
            count=len(rendered),
            elapsed_seconds=elapsed,
        )
