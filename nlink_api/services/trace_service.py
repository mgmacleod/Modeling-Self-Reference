"""Trace sampling service layer."""

from __future__ import annotations

import sys
from pathlib import Path
from typing import TYPE_CHECKING, Callable

from nlink_api.schemas.traces import (
    CycleInfo,
    TraceSampleResponse,
    TraceSingleResponse,
)

if TYPE_CHECKING:
    from n_link_analysis.scripts.data_loader import DataLoader

# Ensure _core is importable
_scripts_dir = Path(__file__).resolve().parents[2] / "n-link-analysis" / "scripts"
if str(_scripts_dir) not in sys.path:
    sys.path.insert(0, str(_scripts_dir))


class TraceService:
    """Service for trace sampling operations."""

    def __init__(self, loader: "DataLoader"):
        self._loader = loader

    def trace_single(
        self,
        *,
        n: int = 5,
        start_page_id: int | None = None,
        start_title: str | None = None,
        max_steps: int = 5000,
        resolve_titles: bool = True,
    ) -> TraceSingleResponse:
        """Trace a single N-link path.

        Either start_page_id or start_title must be provided.
        """
        from _core.trace_engine import (
            load_successor_arrays,
            resolve_titles as do_resolve_titles,
            trace_once,
        )

        # Resolve title to page_id if needed
        if start_page_id is None:
            if start_title is None:
                raise ValueError("Either start_page_id or start_title must be provided")
            from nlink_api.services.data_service import DataService

            data_service = DataService(self._loader)
            start_page_id = data_service.get_page_id_by_title(start_title)
            if start_page_id is None:
                raise ValueError(f"Page not found: {start_title}")

        # Load arrays and trace
        arrays = load_successor_arrays(n, self._loader)
        terminal_type, path, cycle_start = trace_once(
            start_page_id=start_page_id,
            arrays=arrays,
            max_steps=max_steps,
        )

        # Resolve titles if requested
        path_titles: list[str] | None = None
        resolved_start_title: str | None = start_title
        if resolve_titles:
            titles = do_resolve_titles(path, self._loader)
            path_titles = [titles.get(pid, str(pid)) for pid in path]
            if start_page_id in titles:
                resolved_start_title = titles[start_page_id]

        cycle_len = None
        if terminal_type == "CYCLE" and cycle_start is not None:
            cycle_len = len(path) - cycle_start

        return TraceSingleResponse(
            start_page_id=start_page_id,
            start_title=resolved_start_title,
            terminal_type=terminal_type,
            steps=max(0, len(path) - 1),
            path=path,
            path_titles=path_titles,
            cycle_start_index=cycle_start,
            cycle_len=cycle_len,
        )

    def sample_traces(
        self,
        *,
        n: int = 5,
        num_samples: int = 100,
        seed: int = 0,
        min_outdegree: int = 50,
        max_steps: int = 5000,
        top_cycles_k: int = 10,
        resolve_titles: bool = False,
        output_file: Path | None = None,
        progress_callback: Callable[[float, str], None] | None = None,
    ) -> TraceSampleResponse:
        """Sample multiple random traces.

        This is the core sampling operation, used both synchronously
        for small requests and as a background task for large requests.
        """
        from _core.trace_engine import sample_traces as do_sample_traces

        result = do_sample_traces(
            loader=self._loader,
            n=n,
            num_samples=num_samples,
            seed0=seed,
            min_outdegree=min_outdegree,
            max_steps=max_steps,
            resolve_titles_flag=resolve_titles,
            progress_callback=progress_callback,
        )

        # Write to file if requested
        output_path_str: str | None = None
        if output_file:
            self._write_tsv(result, output_file)
            output_path_str = str(output_file)

        # Compute summary statistics
        total_steps = sum(r.steps for r in result.rows)
        total_path_len = sum(r.path_len for r in result.rows)
        cycle_lens = [r.cycle_len for r in result.rows if r.cycle_len is not None]

        avg_steps = total_steps / num_samples if num_samples > 0 else 0.0
        avg_path_len = total_path_len / num_samples if num_samples > 0 else 0.0
        avg_cycle_len = (
            sum(cycle_lens) / len(cycle_lens) if cycle_lens else None
        )

        # Build top cycles response
        top_cycles: list[CycleInfo] = []
        for cyc, count in result.cycle_counter.most_common(top_cycles_k):
            cycle_titles = None
            if result.titles:
                cycle_titles = [result.titles.get(pid, str(pid)) for pid in cyc]
            top_cycles.append(
                CycleInfo(
                    cycle_ids=list(cyc),
                    cycle_titles=cycle_titles,
                    count=count,
                    length=len(cyc),
                )
            )

        return TraceSampleResponse(
            n=n,
            num_samples=num_samples,
            seed0=seed,
            min_outdegree=min_outdegree,
            max_steps=max_steps,
            terminal_counts=result.terminal_counts,
            avg_steps=avg_steps,
            avg_path_len=avg_path_len,
            avg_cycle_len=avg_cycle_len,
            top_cycles=top_cycles,
            output_file=output_path_str,
        )

    def _write_tsv(self, result, output_file: Path) -> None:
        """Write trace results to TSV file."""
        header = "seed\tstart_page_id\tterminal_type\tsteps\tpath_len\ttransient_len\tcycle_len"
        lines = [header]

        for r in result.rows:
            lines.append(
                "\t".join(
                    [
                        str(r.seed),
                        str(r.start_page_id),
                        r.terminal_type,
                        str(r.steps),
                        str(r.path_len),
                        "" if r.transient_len is None else str(r.transient_len),
                        "" if r.cycle_len is None else str(r.cycle_len),
                    ]
                )
            )

        output_file.parent.mkdir(parents=True, exist_ok=True)
        output_file.write_text("\n".join(lines), encoding="utf-8")
