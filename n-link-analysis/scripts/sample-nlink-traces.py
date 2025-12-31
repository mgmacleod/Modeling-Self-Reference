#!/usr/bin/env python3
"""Sample many random N-link traces (sanity check).

This is a companion to trace-nlink-path.py.

Purpose
-------
Quantify how often traces end quickly in short cycles (especially 2-cycles),
without doing full basin decomposition.

Outputs
-------
Writes a TSV with one row per sample:
  seed, start_page_id, terminal_type, steps, path_len, transient_len, cycle_len

Optionally prints the most frequent cycles (canonicalized) and resolves titles
for those cycle nodes.

Notes
-----
- Loads successor arrays once (page_id -> next_id for fixed N).
- Start pages are chosen from pages with defined Nth link (next_id != -1),
  optionally filtered by min_outdegree.

"""

from __future__ import annotations

import argparse
import time
from collections import Counter
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, Literal

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
class SampleRow:
    seed: int
    start_page_id: int
    terminal_type: TerminalType
    steps: int
    path_len: int
    transient_len: int | None
    cycle_len: int | None


def _load_successor_arrays(n: int) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
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
    rng: np.random.Generator,
    sorted_page_ids: np.ndarray,
    next_ids: np.ndarray,
    out_degree: np.ndarray,
    *,
    min_outdegree: int,
) -> int:
    candidates = np.where((next_ids != -1) & (out_degree >= min_outdegree))[0]
    if len(candidates) == 0:
        candidates = np.where(next_ids != -1)[0]

    if len(candidates) == 0:
        raise RuntimeError("No candidate pages found with a defined Nth link.")

    chosen_idx = int(rng.choice(candidates))
    return int(sorted_page_ids[chosen_idx])


def _canonical_cycle(cycle_nodes: list[int]) -> tuple[int, ...]:
    """Canonicalize a directed cycle (rotation-invariant).

    We ignore direction reversal; for this use-case we want a stable signature
    for counting repeated cycles.
    """

    if not cycle_nodes:
        return tuple()

    # Ensure it's a simple list (may contain repeats if caller is wrong).
    nodes = list(cycle_nodes)

    # Rotation: choose lexicographically smallest rotation.
    k = len(nodes)
    best = None
    for shift in range(k):
        rot = tuple(nodes[shift:] + nodes[:shift])
        if best is None or rot < best:
            best = rot

    # Also consider reversed direction (still a cycle in undirected sense).
    rev_nodes = list(reversed(nodes))
    best_rev = None
    for shift in range(k):
        rot = tuple(rev_nodes[shift:] + rev_nodes[:shift])
        if best_rev is None or rot < best_rev:
            best_rev = rot

    return min(best, best_rev) if best is not None and best_rev is not None else (best or best_rev)  # type: ignore[return-value]


def trace_once(
    *,
    start_page_id: int,
    sorted_page_ids: np.ndarray,
    next_ids: np.ndarray,
    max_steps: int,
) -> tuple[TerminalType, list[int], int | None]:
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

        idx = _lookup_index(sorted_page_ids, current)
        if idx is None:
            terminal = "HALT"
            break

        nxt = int(next_ids[idx])
        if nxt == -1:
            terminal = "HALT"
            break

        current = nxt

    return terminal, path, cycle_start


def _resolve_titles(page_ids: Iterable[int]) -> dict[int, str]:
    if not PAGES_PATH.exists():
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
        FROM read_parquet('{PAGES_PATH.as_posix()}') p
        JOIN trace_ids t USING (page_id)
        """.strip()
    ).fetchall()
    con.close()

    return {int(pid): str(title) for pid, title in rows}


def main() -> None:
    parser = argparse.ArgumentParser(description="Sample many random N-link traces and summarize cycle statistics.")
    parser.add_argument("--n", type=int, default=5, help="N for fixed N-link rule (default: 5)")
    parser.add_argument("--num", type=int, default=100, help="Number of samples to draw (default: 100)")
    parser.add_argument("--seed0", type=int, default=0, help="First RNG seed (default: 0)")
    parser.add_argument(
        "--min-outdegree",
        type=int,
        default=50,
        help="When choosing a start page, require out_degree >= this (default: 50)",
    )
    parser.add_argument("--max-steps", type=int, default=5000, help="Stop after this many steps (default: 5000)")
    parser.add_argument(
        "--top-cycles",
        type=int,
        default=10,
        help="Print the top-K most frequent cycles (default: 10)",
    )
    parser.add_argument(
        "--resolve-titles",
        action="store_true",
        help="Resolve titles for nodes in the printed top cycles (slower)",
    )
    parser.add_argument(
        "--out",
        type=str,
        default=None,
        help="Optional output TSV path. Default: data/wikipedia/processed/analysis/sample_traces_n=...tsv",
    )

    args = parser.parse_args()

    if args.n <= 0:
        raise SystemExit("--n must be >= 1")
    if args.num <= 0:
        raise SystemExit("--num must be >= 1")

    print(f"Using nlink data: {NLINK_PATH}")
    page_ids, next_ids, out_degree = _load_successor_arrays(args.n)

    rows: list[SampleRow] = []
    term_counts: Counter[str] = Counter()
    cycle_counter: Counter[tuple[int, ...]] = Counter()

    t0 = time.time()
    for i in range(args.num):
        seed = int(args.seed0 + i)
        rng = np.random.default_rng(seed)
        start = _choose_start_page(
            rng,
            page_ids,
            next_ids,
            out_degree,
            min_outdegree=int(args.min_outdegree),
        )

        terminal, path, cycle_start = trace_once(
            start_page_id=start,
            sorted_page_ids=page_ids,
            next_ids=next_ids,
            max_steps=int(args.max_steps),
        )

        path_len = len(path)
        steps = max(0, path_len - 1)

        transient_len: int | None = None
        cycle_len: int | None = None
        if terminal == "CYCLE" and cycle_start is not None:
            transient_len = int(cycle_start)
            cycle_len = int(path_len - cycle_start)
            cyc = _canonical_cycle(path[cycle_start:])
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

        if (i + 1) % 25 == 0 or (i + 1) == args.num:
            dt = time.time() - t0
            rate = (i + 1) / max(dt, 1e-9)
            print(f"Sampled {i+1}/{args.num} traces ({rate:.1f} traces/sec)")

    ANALYSIS_DIR.mkdir(parents=True, exist_ok=True)
    out_path = Path(args.out) if args.out else (ANALYSIS_DIR / f"sample_traces_n={args.n}_num={args.num}_seed0={args.seed0}.tsv")

    header = "seed\tstart_page_id\tterminal_type\tsteps\tpath_len\ttransient_len\tcycle_len"
    lines = [header]
    for r in rows:
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

    out_path.write_text("\n".join(lines), encoding="utf-8")

    print()
    print("=== Sampling Summary ===")
    print(f"N={args.n}")
    print(f"Samples: {args.num}")
    print(f"min_outdegree: {args.min_outdegree}")
    print(f"max_steps: {args.max_steps}")
    print(f"Terminal counts: {dict(term_counts)}")
    print(f"Saved per-trace TSV: {out_path}")

    if args.top_cycles > 0 and len(cycle_counter) > 0:
        top = cycle_counter.most_common(int(args.top_cycles))
        print()
        print(f"=== Top {min(args.top_cycles, len(top))} Cycles (by frequency) ===")

        titles: dict[int, str] = {}
        if args.resolve_titles:
            ids_to_resolve: set[int] = set()
            for cyc, _cnt in top:
                ids_to_resolve.update(cyc)
            titles = _resolve_titles(ids_to_resolve)

        for cyc, cnt in top:
            if args.resolve_titles and titles:
                label = " → ".join(titles.get(pid, str(pid)) for pid in cyc)
            else:
                label = " → ".join(str(pid) for pid in cyc)
            print(f"count={cnt}\tlen={len(cyc)}\t{label}")


if __name__ == "__main__":
    main()
