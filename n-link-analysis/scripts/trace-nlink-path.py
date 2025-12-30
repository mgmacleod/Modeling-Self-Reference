#!/usr/bin/env python3
"""Trace a single N-link path (sanity check).

Goal
----
Pick a starting Wikipedia page and follow the fixed N-link rule:
  f_N(page) = Nth outgoing link (ordered) if it exists, else HALT.

This script is intentionally *not* a full basin analysis. It is a minimal
"does the data produce long paths?" sanity check.

Data dependencies (produced by the pipeline)
-------------------------------------------
- data/wikipedia/processed/nlink_sequences.parquet
    schema: (page_id: int64, link_sequence: list<int64>)
- data/wikipedia/processed/pages.parquet
    schema: (page_id: int64, namespace: int32, title: string, is_redirect: bool)

Notes
-----
- For performance, we scan nlink_sequences.parquet once to build arrays:
    page_id -> next_id for the chosen N, plus out_degree.
  Then traversal uses binary search.
- Titles are resolved *after* traversal in one query.

"""

from __future__ import annotations

import argparse
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Literal

import duckdb
import numpy as np
import pyarrow as pa


REPO_ROOT = Path(__file__).resolve().parents[2]
PROCESSED_DIR = REPO_ROOT / "data" / "wikipedia" / "processed"
NLINK_PATH = PROCESSED_DIR / "nlink_sequences.parquet"
PAGES_PATH = PROCESSED_DIR / "pages.parquet"
ANALYSIS_DIR = PROCESSED_DIR / "analysis"


TerminalType = Literal["HALT", "CYCLE", "MAX_STEPS"]


@dataclass(frozen=True)
class TraceResult:
    n: int
    start_page_id: int
    path_page_ids: list[int]
    terminal_type: TerminalType
    cycle_start_index: int | None
    max_steps: int


def _load_successor_arrays(n: int) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """Load (page_id, next_id, out_degree) arrays for fixed N.

    next_id is -1 for HALT (out_degree < N).

    Returns:
        page_ids_sorted, next_ids_sorted, out_degree_sorted
    """

    if not NLINK_PATH.exists():
        raise FileNotFoundError(f"Missing: {NLINK_PATH}")

    query = f"""
        SELECT
            page_id::BIGINT AS page_id,
            list_extract(link_sequence, {n})::BIGINT AS next_id,
            list_count(link_sequence)::INTEGER AS out_degree
        FROM read_parquet('{NLINK_PATH.as_posix()}')
    """.strip()

    t0 = time.time()
    con = duckdb.connect()

    # Pull as Arrow to preserve NULLs cheaply.
    tbl = con.execute(query).fetch_arrow_table()
    con.close()

    page_ids = tbl["page_id"].combine_chunks().to_numpy(zero_copy_only=False).astype(np.int64)

    next_ids_raw = tbl["next_id"].combine_chunks().to_numpy(zero_copy_only=False)
    if isinstance(next_ids_raw, np.ma.MaskedArray):
        next_ids = next_ids_raw.filled(-1).astype(np.int64)
    else:
        # DuckDB may return floats with NaN for NULLs.
        if np.issubdtype(next_ids_raw.dtype, np.floating):
            next_ids = np.where(np.isnan(next_ids_raw), -1, next_ids_raw).astype(np.int64)
        else:
            next_ids = next_ids_raw.astype(np.int64)

    out_degree = tbl["out_degree"].combine_chunks().to_numpy(zero_copy_only=False).astype(np.int32)

    # Sort for binary-search lookup.
    order = np.argsort(page_ids, kind="mergesort")
    page_ids = page_ids[order]
    next_ids = next_ids[order]
    out_degree = out_degree[order]

    dt = time.time() - t0
    print(f"Loaded successor arrays for N={n} in {dt:.1f}s ({len(page_ids):,} pages)")

    return page_ids, next_ids, out_degree


def _lookup_index(sorted_page_ids: np.ndarray, page_id: int) -> int | None:
    idx = int(np.searchsorted(sorted_page_ids, page_id))
    if idx >= len(sorted_page_ids) or int(sorted_page_ids[idx]) != page_id:
        return None
    return idx


def _choose_start_page(
    sorted_page_ids: np.ndarray,
    next_ids: np.ndarray,
    out_degree: np.ndarray,
    *,
    min_outdegree: int,
    seed: int,
) -> int:
    rng = np.random.default_rng(seed)

    # Candidate = has at least N links (next_id != -1), and out_degree >= min_outdegree.
    candidates = np.where((next_ids != -1) & (out_degree >= min_outdegree))[0]
    if len(candidates) == 0:
        # Fall back: any page with at least N links.
        candidates = np.where(next_ids != -1)[0]

    if len(candidates) == 0:
        raise RuntimeError("No candidate pages found with a defined Nth link.")

    chosen_idx = int(rng.choice(candidates))
    return int(sorted_page_ids[chosen_idx])


def trace_path(
    *,
    n: int,
    start_page_id: int,
    sorted_page_ids: np.ndarray,
    next_ids: np.ndarray,
    max_steps: int,
) -> TraceResult:
    visited_at: dict[int, int] = {}
    path: list[int] = []

    current = start_page_id
    terminal_type: TerminalType = "MAX_STEPS"
    cycle_start: int | None = None

    for step in range(max_steps + 1):
        if current in visited_at:
            terminal_type = "CYCLE"
            cycle_start = visited_at[current]
            break

        visited_at[current] = len(path)
        path.append(current)

        idx = _lookup_index(sorted_page_ids, current)
        if idx is None:
            terminal_type = "HALT"
            break

        nxt = int(next_ids[idx])
        if nxt == -1:
            terminal_type = "HALT"
            break

        current = nxt

    return TraceResult(
        n=n,
        start_page_id=start_page_id,
        path_page_ids=path,
        terminal_type=terminal_type,
        cycle_start_index=cycle_start,
        max_steps=max_steps,
    )


def _resolve_titles(page_ids: list[int]) -> dict[int, str]:
    if not PAGES_PATH.exists():
        return {}

    unique_ids = sorted(set(page_ids))
    id_tbl = pa.table({"page_id": pa.array(unique_ids, type=pa.int64())})

    con = duckdb.connect()
    con.register("trace_ids", id_tbl)

    # No namespace filtering here: the goal is just to label IDs.
    rows = con.execute(
        f"""
        SELECT p.page_id, p.title
        FROM read_parquet('{PAGES_PATH.as_posix()}') p
        JOIN trace_ids t USING (page_id)
        """.strip()
    ).fetchall()
    con.close()

    return {int(pid): str(title) for pid, title in rows}


def _write_trace_file(
    *,
    out_path: Path,
    trace: TraceResult,
    titles: dict[int, str],
) -> None:
    out_path.parent.mkdir(parents=True, exist_ok=True)

    lines: list[str] = []
    lines.append(f"N={trace.n}")
    lines.append(f"start_page_id={trace.start_page_id}")
    lines.append(f"terminal_type={trace.terminal_type}")
    if trace.terminal_type == "CYCLE" and trace.cycle_start_index is not None:
        lines.append(f"cycle_start_index={trace.cycle_start_index}")
        lines.append(f"cycle_length={len(trace.path_page_ids) - trace.cycle_start_index}")
    lines.append("")

    for i, pid in enumerate(trace.path_page_ids):
        title = titles.get(pid, "<unknown>")
        lines.append(f"{i}\t{pid}\t{title}")

    out_path.write_text("\n".join(lines), encoding="utf-8")


def _print_summary(
    *,
    trace: TraceResult,
    titles: dict[int, str],
    sorted_page_ids: np.ndarray,
    out_degree: np.ndarray,
    print_max: int,
    trace_file: Path | None,
) -> None:
    path = trace.path_page_ids
    unique_nodes = len(path)
    hops = max(0, len(path) - 1)

    start_title = titles.get(trace.start_page_id, "<unknown>")

    print()
    print("=== N-Link Trace (Sanity Check) ===")
    print(f"N: {trace.n}")
    print(f"Start: {trace.start_page_id}  {start_title}")
    print(f"Terminal: {trace.terminal_type}")

    if trace.terminal_type == "HALT":
        last = path[-1]
        idx = _lookup_index(sorted_page_ids, last)
        last_k = int(out_degree[idx]) if idx is not None else 0
        print(f"HALT at step {hops} (last out_degree={last_k})")

    if trace.terminal_type == "CYCLE" and trace.cycle_start_index is not None:
        cs = trace.cycle_start_index
        cycle_len = len(path) - cs
        cycle_preview = " → ".join(titles.get(pid, str(pid)) for pid in path[cs : min(cs + 5, len(path))])
        print(f"Cycle detected: start_index={cs}, cycle_length={cycle_len}")
        print(f"Cycle preview: {cycle_preview}{' → ...' if cycle_len > 5 else ''}")

    if trace.terminal_type == "MAX_STEPS":
        print(f"Stopped at max_steps={trace.max_steps} (no HALT/CYCLE yet)")

    print(f"Unique nodes visited: {unique_nodes}")

    if trace_file is not None:
        print(f"Full trace saved to: {trace_file}")

    print()
    print("--- Path (titles) ---")

    def fmt(i: int, pid: int) -> str:
        return f"{i:>5}  {titles.get(pid, '<unknown>')} ({pid})"

    if len(path) <= print_max:
        for i, pid in enumerate(path):
            print(fmt(i, pid))
        return

    head_n = max(10, print_max // 2)
    tail_n = max(10, print_max - head_n)

    for i, pid in enumerate(path[:head_n]):
        print(fmt(i, pid))

    print(f"... ({len(path) - head_n - tail_n} omitted; see saved trace file) ...")

    offset = len(path) - tail_n
    for i, pid in enumerate(path[offset:], start=offset):
        print(fmt(i, pid))


def main() -> None:
    parser = argparse.ArgumentParser(description="Trace a single fixed-N link path and report basic stats.")
    parser.add_argument("--n", type=int, default=5, help="N for the fixed N-link rule (default: 5)")
    parser.add_argument("--start-page-id", type=int, default=None, help="Optional explicit starting page_id")
    parser.add_argument(
        "--min-outdegree",
        type=int,
        default=50,
        help="When auto-choosing a start page, require out_degree >= this (default: 50)",
    )
    parser.add_argument("--seed", type=int, default=0, help="RNG seed for choosing a start page")
    parser.add_argument("--max-steps", type=int, default=5000, help="Stop after this many steps if no HALT/CYCLE")
    parser.add_argument(
        "--print-max",
        type=int,
        default=200,
        help="Max number of path rows to print to console (default: 200)",
    )
    parser.add_argument(
        "--no-save",
        action="store_true",
        help="Do not write the full trace to a file under data/wikipedia/processed/analysis/",
    )
    args = parser.parse_args()

    if args.n <= 0:
        raise SystemExit("--n must be >= 1")

    print(f"Using nlink data: {NLINK_PATH}")
    page_ids, next_ids, out_degree = _load_successor_arrays(args.n)

    if args.start_page_id is None:
        start_page_id = _choose_start_page(
            page_ids,
            next_ids,
            out_degree,
            min_outdegree=args.min_outdegree,
            seed=args.seed,
        )
    else:
        start_page_id = int(args.start_page_id)

    trace = trace_path(
        n=args.n,
        start_page_id=start_page_id,
        sorted_page_ids=page_ids,
        next_ids=next_ids,
        max_steps=args.max_steps,
    )

    titles = _resolve_titles(trace.path_page_ids)

    trace_file: Path | None = None
    if not args.no_save:
        ANALYSIS_DIR.mkdir(parents=True, exist_ok=True)
        trace_file = ANALYSIS_DIR / f"trace_n={trace.n}_start={trace.start_page_id}.tsv"
        _write_trace_file(out_path=trace_file, trace=trace, titles=titles)

    _print_summary(
        trace=trace,
        titles=titles,
        sorted_page_ids=page_ids,
        out_degree=out_degree,
        print_max=args.print_max,
        trace_file=trace_file,
    )


if __name__ == "__main__":
    main()
