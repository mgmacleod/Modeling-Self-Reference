"""Trace sampling engine for N-Link path analysis.

This module provides the core logic for tracing N-link paths through
the Wikipedia graph. It supports both single traces and batch sampling.

Extracted from sample-nlink-traces.py for reuse in API layer.
"""

from __future__ import annotations

import time
from collections import Counter
from dataclasses import dataclass, field
from pathlib import Path
from typing import TYPE_CHECKING, Callable, Iterable, Literal

import duckdb
import numpy as np
import pyarrow as pa

if TYPE_CHECKING:
    from data_loader import DataLoader


TerminalType = Literal["HALT", "CYCLE", "MAX_STEPS"]
ProgressCallback = Callable[[float, str], None] | None


@dataclass(frozen=True)
class SampleRow:
    """Result of a single trace."""

    seed: int
    start_page_id: int
    terminal_type: TerminalType
    steps: int
    path_len: int
    transient_len: int | None
    cycle_len: int | None


@dataclass
class TraceSampleResult:
    """Result of batch trace sampling."""

    n: int
    num_samples: int
    seed0: int
    min_outdegree: int
    max_steps: int
    rows: list[SampleRow]
    terminal_counts: dict[str, int]
    cycle_counter: Counter[tuple[int, ...]]
    titles: dict[int, str] = field(default_factory=dict)


@dataclass
class SuccessorArrays:
    """Pre-loaded successor arrays for fast lookups."""

    page_ids: np.ndarray  # Sorted array of page IDs
    next_ids: np.ndarray  # Corresponding next page IDs (-1 for HALT)
    out_degree: np.ndarray  # Out-degree for each page
    n: int  # The N value these arrays are for


def load_successor_arrays(n: int, loader: "DataLoader") -> SuccessorArrays:
    """Load successor arrays for a given N-link rule.

    Args:
        n: The N for the N-link rule (1-indexed).
        loader: DataLoader instance for accessing data files.

    Returns:
        SuccessorArrays containing sorted page_ids, next_ids, and out_degrees.
    """
    nlink_path = loader.nlink_sequences_path
    if not nlink_path.exists():
        raise FileNotFoundError(f"Missing: {nlink_path}")

    query = f"""
        SELECT
            page_id::BIGINT AS page_id,
            list_extract(link_sequence, {n})::BIGINT AS next_id,
            list_count(link_sequence)::INTEGER AS out_degree
        FROM read_parquet('{nlink_path.as_posix()}')
    """.strip()

    t0 = time.time()
    con = duckdb.connect()
    tbl = con.execute(query).fetch_arrow_table()
    con.close()

    page_ids = tbl["page_id"].combine_chunks().to_numpy(zero_copy_only=False).astype(np.int64)

    next_ids_raw = tbl["next_id"].combine_chunks().to_numpy(zero_copy_only=False)
    if isinstance(next_ids_raw, np.ma.MaskedArray):
        next_ids = next_ids_raw.filled(-1).astype(np.int64)
    else:
        if np.issubdtype(next_ids_raw.dtype, np.floating):
            next_ids = np.where(np.isnan(next_ids_raw), -1, next_ids_raw).astype(np.int64)
        else:
            next_ids = next_ids_raw.astype(np.int64)

    out_degree = tbl["out_degree"].combine_chunks().to_numpy(zero_copy_only=False).astype(np.int32)

    # Sort by page_id for binary search
    order = np.argsort(page_ids, kind="mergesort")
    page_ids = page_ids[order]
    next_ids = next_ids[order]
    out_degree = out_degree[order]

    dt = time.time() - t0
    print(f"Loaded successor arrays for N={n} in {dt:.1f}s ({len(page_ids):,} pages)")

    return SuccessorArrays(
        page_ids=page_ids,
        next_ids=next_ids,
        out_degree=out_degree,
        n=n,
    )


def lookup_index(sorted_page_ids: np.ndarray, page_id: int) -> int | None:
    """Binary search for a page ID in sorted array.

    Returns the index if found, None otherwise.
    """
    idx = int(np.searchsorted(sorted_page_ids, page_id))
    if idx >= len(sorted_page_ids) or int(sorted_page_ids[idx]) != page_id:
        return None
    return idx


def choose_start_page(
    rng: np.random.Generator,
    arrays: SuccessorArrays,
    *,
    min_outdegree: int = 50,
) -> int:
    """Choose a random start page for tracing.

    Filters to pages that have a defined Nth link and meet minimum out-degree.
    """
    candidates = np.where(
        (arrays.next_ids != -1) & (arrays.out_degree >= min_outdegree)
    )[0]
    if len(candidates) == 0:
        # Fall back to any page with defined Nth link
        candidates = np.where(arrays.next_ids != -1)[0]

    if len(candidates) == 0:
        raise RuntimeError("No candidate pages found with a defined Nth link.")

    chosen_idx = int(rng.choice(candidates))
    return int(arrays.page_ids[chosen_idx])


def canonical_cycle(cycle_nodes: list[int]) -> tuple[int, ...]:
    """Canonicalize a directed cycle (rotation-invariant).

    We consider both rotations and reversal to get a stable signature
    for counting repeated cycles.
    """
    if not cycle_nodes:
        return tuple()

    nodes = list(cycle_nodes)
    k = len(nodes)

    # Find lexicographically smallest rotation
    best = None
    for shift in range(k):
        rot = tuple(nodes[shift:] + nodes[:shift])
        if best is None or rot < best:
            best = rot

    # Also consider reversed direction
    rev_nodes = list(reversed(nodes))
    best_rev = None
    for shift in range(k):
        rot = tuple(rev_nodes[shift:] + rev_nodes[:shift])
        if best_rev is None or rot < best_rev:
            best_rev = rot

    if best is not None and best_rev is not None:
        return min(best, best_rev)
    return best or best_rev or tuple()


def trace_once(
    *,
    start_page_id: int,
    arrays: SuccessorArrays,
    max_steps: int = 5000,
) -> tuple[TerminalType, list[int], int | None]:
    """Trace a single N-link path from a start page.

    Args:
        start_page_id: Page ID to start tracing from.
        arrays: Pre-loaded successor arrays.
        max_steps: Maximum steps before giving up.

    Returns:
        Tuple of (terminal_type, path, cycle_start_index).
        cycle_start_index is None unless terminal_type is CYCLE.
    """
    visited_at: dict[int, int] = {}
    path: list[int] = []

    current = int(start_page_id)
    terminal: TerminalType = "MAX_STEPS"
    cycle_start: int | None = None

    for _ in range(max_steps + 1):
        if current in visited_at:
            terminal = "CYCLE"
            cycle_start = visited_at[current]
            break

        visited_at[current] = len(path)
        path.append(current)

        idx = lookup_index(arrays.page_ids, current)
        if idx is None:
            terminal = "HALT"
            break

        nxt = int(arrays.next_ids[idx])
        if nxt == -1:
            terminal = "HALT"
            break

        current = nxt

    return terminal, path, cycle_start


def resolve_titles(page_ids: Iterable[int], loader: "DataLoader") -> dict[int, str]:
    """Resolve page IDs to titles.

    Args:
        page_ids: Collection of page IDs to resolve.
        loader: DataLoader for accessing pages data.

    Returns:
        Dictionary mapping page_id -> title.
    """
    pages_path = loader.pages_path
    if not pages_path.exists():
        return {}

    unique_ids = sorted(set(int(x) for x in page_ids))
    if not unique_ids:
        return {}

    id_tbl = pa.table({"page_id": pa.array(unique_ids, type=pa.int64())})

    con = duckdb.connect()
    con.register("trace_ids", id_tbl)

    rows = con.execute(
        f"""
        SELECT p.page_id, p.title
        FROM read_parquet('{pages_path.as_posix()}') p
        JOIN trace_ids t USING (page_id)
        """.strip()
    ).fetchall()
    con.close()

    return {int(pid): str(title) for pid, title in rows}


def sample_traces(
    *,
    loader: "DataLoader",
    n: int = 5,
    num_samples: int = 100,
    seed0: int = 0,
    min_outdegree: int = 50,
    max_steps: int = 5000,
    resolve_titles_flag: bool = False,
    progress_callback: ProgressCallback = None,
) -> TraceSampleResult:
    """Sample multiple random N-link traces.

    Args:
        loader: DataLoader for accessing data files.
        n: N for the N-link rule (1-indexed).
        num_samples: Number of traces to sample.
        seed0: Starting seed for RNG (each sample uses seed0 + i).
        min_outdegree: Minimum out-degree for start page selection.
        max_steps: Maximum steps per trace.
        resolve_titles_flag: If True, resolve titles for cycle nodes.
        progress_callback: Optional callback for progress updates.

    Returns:
        TraceSampleResult with all trace data.
    """
    arrays = load_successor_arrays(n, loader)

    rows: list[SampleRow] = []
    term_counts: Counter[str] = Counter()
    cycle_counter: Counter[tuple[int, ...]] = Counter()

    t0 = time.time()
    for i in range(num_samples):
        seed = int(seed0 + i)
        rng = np.random.default_rng(seed)
        start = choose_start_page(rng, arrays, min_outdegree=min_outdegree)

        terminal, path, cycle_start = trace_once(
            start_page_id=start,
            arrays=arrays,
            max_steps=max_steps,
        )

        path_len = len(path)
        steps = max(0, path_len - 1)

        transient_len: int | None = None
        cycle_len: int | None = None
        if terminal == "CYCLE" and cycle_start is not None:
            transient_len = int(cycle_start)
            cycle_len = int(path_len - cycle_start)
            cyc = canonical_cycle(path[cycle_start:])
            cycle_counter[cyc] += 1

        rows.append(
            SampleRow(
                seed=seed,
                start_page_id=int(start),
                terminal_type=terminal,
                steps=int(steps),
                path_len=int(path_len),
                transient_len=transient_len,
                cycle_len=cycle_len,
            )
        )
        term_counts[terminal] += 1

        # Progress reporting
        if progress_callback and ((i + 1) % 25 == 0 or (i + 1) == num_samples):
            progress = (i + 1) / num_samples
            dt = time.time() - t0
            rate = (i + 1) / max(dt, 1e-9)
            progress_callback(progress, f"Sampled {i+1}/{num_samples} ({rate:.1f}/sec)")

    # Resolve titles if requested
    titles: dict[int, str] = {}
    if resolve_titles_flag and cycle_counter:
        ids_to_resolve: set[int] = set()
        for cyc in cycle_counter:
            ids_to_resolve.update(cyc)
        titles = resolve_titles(ids_to_resolve, loader)

    return TraceSampleResult(
        n=n,
        num_samples=num_samples,
        seed0=seed0,
        min_outdegree=min_outdegree,
        max_steps=max_steps,
        rows=rows,
        terminal_counts=dict(term_counts),
        cycle_counter=cycle_counter,
        titles=titles,
    )
