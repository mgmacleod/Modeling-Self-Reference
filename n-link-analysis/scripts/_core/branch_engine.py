"""Branch structure analysis engine for N-Link path analysis.

This module provides the core logic for analyzing branch structure feeding
a terminal cycle under the N-link rule. It partitions the basin by depth-1
entry points and computes branch sizes (thickness).

Extracted from branch-basin-analysis.py for reuse in API layer.
"""

from __future__ import annotations

import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import TYPE_CHECKING, Callable

import duckdb
import pyarrow as pa

from _core.basin_engine import ensure_edges_table, get_edges_db_path, resolve_ids_to_titles

if TYPE_CHECKING:
    from data_loader import DataLoader


ProgressCallback = Callable[[float, str], None] | None


@dataclass
class BranchInfo:
    """Information about a single branch."""

    rank: int
    entry_id: int
    entry_title: str | None
    basin_size: int
    max_depth: int
    enters_cycle_page_id: int
    enters_cycle_title: str | None = None


@dataclass
class BranchAnalysisResult:
    """Result of branch structure analysis."""

    n: int
    cycle_page_ids: list[int]
    total_basin_nodes: int
    num_branches: int
    max_depth_reached: int
    branches: list[BranchInfo]
    branches_all_tsv_path: str | None = None
    branches_topk_tsv_path: str | None = None
    assignments_parquet_path: str | None = None
    elapsed_seconds: float = 0.0


def analyze_branches(
    loader: "DataLoader",
    n: int,
    cycle_page_ids: list[int],
    *,
    max_depth: int = 0,
    log_every: int = 10,
    top_k: int = 25,
    write_top_k_membership: int = 0,
    out_prefix: str | None = None,
    progress_callback: ProgressCallback = None,
    verbose: bool = True,
) -> BranchAnalysisResult:
    """Analyze branch structure feeding a given cycle.

    Uses reverse BFS with label propagation to partition the basin by
    entry points (depth-1 predecessors of the cycle).

    Args:
        loader: DataLoader for accessing data files.
        n: N for the N-link rule (1-indexed).
        cycle_page_ids: List of page IDs forming the cycle.
        max_depth: Stop after this many reverse layers (0 = no limit).
        log_every: Print progress every N layers.
        top_k: Number of top branches to include in result.
        write_top_k_membership: Write membership for top-K branches (0 = none).
        out_prefix: Output prefix for files under analysis/.
        progress_callback: Optional callback for progress updates.
        verbose: Whether to print progress.

    Returns:
        BranchAnalysisResult with branch statistics and file paths.
    """
    if not cycle_page_ids:
        raise ValueError("At least one cycle page ID is required")

    cycle_ids = list(dict.fromkeys(int(x) for x in cycle_page_ids))  # Dedupe, preserve order

    # Get paths from loader
    nlink_path = loader.nlink_sequences_path
    analysis_dir = nlink_path.parent / "analysis"
    analysis_dir.mkdir(parents=True, exist_ok=True)

    # Set up output paths
    prefix = out_prefix or f"branches_from_cycle_n={int(n)}"
    out_branches_all = analysis_dir / f"{prefix}_branches_all.tsv"
    out_branches_topk = analysis_dir / f"{prefix}_branches_topk.tsv"
    out_assignments = analysis_dir / f"{prefix}_assignments.parquet"

    db_path = get_edges_db_path(analysis_dir, n)
    if verbose:
        print(f"Using edges DB: {db_path}")

    con = duckdb.connect(str(db_path))
    ensure_edges_table(con, n=n, nlink_path=nlink_path, verbose=verbose)

    # Seed tables with entry_id tracking
    con.execute("CREATE TEMP TABLE seen(page_id BIGINT PRIMARY KEY, entry_id BIGINT, depth INTEGER)")
    con.execute("CREATE TEMP TABLE frontier(page_id BIGINT, entry_id BIGINT, depth INTEGER)")

    cycle_tbl = pa.table({"page_id": pa.array(cycle_ids, type=pa.int64())})
    con.register("cycle_tbl", cycle_tbl)

    # Depth 0: cycle nodes have entry_id = NULL
    con.execute("INSERT INTO seen SELECT page_id, NULL::BIGINT AS entry_id, 0 AS depth FROM cycle_tbl")
    con.execute("INSERT INTO frontier SELECT page_id, NULL::BIGINT AS entry_id, 0 AS depth FROM cycle_tbl")

    depth = 0
    t0 = time.time()

    while True:
        if max_depth and depth >= max_depth:
            if verbose:
                print(f"Reached max_depth={max_depth}")
            break

        # Expand one reverse layer
        con.execute("DROP TABLE IF EXISTS next_frontier")
        con.execute(
            """
            CREATE TEMP TABLE next_frontier AS
            SELECT
                e.src_page_id AS page_id,
                CASE
                    WHEN f.depth = 0 THEN e.src_page_id
                    ELSE f.entry_id
                END AS entry_id,
                f.depth + 1 AS depth
            FROM edges e
            JOIN frontier f
              ON e.dst_page_id = f.page_id
            LEFT JOIN seen s
              ON s.page_id = e.src_page_id
            WHERE s.page_id IS NULL
            """.strip()
        )

        new_row = con.execute("SELECT COUNT(*) FROM next_frontier").fetchone()
        new_nodes = int(new_row[0]) if new_row is not None else 0

        if new_nodes == 0:
            if verbose:
                print("Frontier exhausted (no new nodes).")
            break

        con.execute("INSERT INTO seen SELECT page_id, entry_id, depth FROM next_frontier")
        con.execute("DELETE FROM frontier")
        con.execute("INSERT INTO frontier SELECT page_id, entry_id, depth FROM next_frontier")

        depth += 1

        if verbose and depth % log_every == 0:
            total_row = con.execute("SELECT COUNT(*) FROM seen").fetchone()
            total_seen = int(total_row[0]) if total_row is not None else 0
            dt = time.time() - t0
            rate = total_seen / max(dt, 1e-9)
            print(f"depth={depth}\tnew={new_nodes:,}\ttotal={total_seen:,}\t(rate={rate:,.1f} nodes/sec)")

        if progress_callback:
            total_row = con.execute("SELECT COUNT(*) FROM seen").fetchone()
            total_seen = int(total_row[0]) if total_row is not None else 0
            msg = f"Depth {depth}: {total_seen:,} nodes"
            progress_callback(0.0, msg)

    total_row = con.execute("SELECT COUNT(*) FROM seen").fetchone()
    total_seen = int(total_row[0]) if total_row is not None else 0
    if verbose:
        print(f"Total basin nodes (including cycle): {total_seen:,}")

    # Branch sizes (exclude cycle nodes: depth>=1, entry_id not null)
    con.execute("DROP TABLE IF EXISTS branch_sizes")
    con.execute(
        """
        CREATE TEMP TABLE branch_sizes AS
        SELECT
            entry_id,
            COUNT(*)::BIGINT AS basin_size,
            MAX(depth)::INTEGER AS max_depth
        FROM seen
        WHERE depth >= 1
        GROUP BY entry_id
        """.strip()
    )

    n_branches_row = con.execute("SELECT COUNT(*) FROM branch_sizes").fetchone()
    n_branches = int(n_branches_row[0]) if n_branches_row is not None else 0
    if verbose:
        print(f"Entry branches (depth-1 predecessors): {n_branches:,}")

    # Identify which cycle node each entry flows into
    con.execute("DROP TABLE IF EXISTS branch_meta")
    con.execute(
        """
        CREATE TEMP TABLE branch_meta AS
        SELECT
            b.entry_id,
            b.basin_size,
            b.max_depth,
            e.dst_page_id AS enters_cycle_page_id
        FROM branch_sizes b
        JOIN edges e
          ON e.src_page_id = b.entry_id
        """.strip()
    )

    # Get all branch data
    all_rows = con.execute(
        """
        SELECT entry_id, basin_size, max_depth, enters_cycle_page_id
        FROM branch_meta
        ORDER BY basin_size DESC
        """.strip()
    ).fetchall()

    # Write all-branches TSV
    out_lines_all = ["rank\tentry_id\tbasin_size\tmax_depth\tenters_cycle_page_id"]
    for i, (entry_id, basin_size, max_d, enters_cycle) in enumerate(all_rows, start=1):
        enters_i = int(enters_cycle) if enters_cycle is not None else -1
        out_lines_all.append(
            "\t".join([
                str(i),
                str(int(entry_id)),
                str(int(basin_size)),
                str(int(max_d)),
                str(enters_i),
            ])
        )
    out_branches_all.write_text("\n".join(out_lines_all), encoding="utf-8")
    if verbose:
        print(f"Wrote all-branches table: {out_branches_all}")

    # Build result with top-K branches
    top_rows = all_rows[:top_k]

    # Resolve titles for top-K branches
    ids_to_resolve: list[int] = list(cycle_ids)
    ids_to_resolve.extend(int(r[0]) for r in top_rows)
    ids_to_resolve.extend(int(r[3]) for r in top_rows if r[3] is not None)
    titles = resolve_ids_to_titles(ids_to_resolve, loader)

    # Write titled top-K TSV
    out_lines_topk = [
        "rank\tentry_id\tentry_title\tbasin_size\tmax_depth\tenters_cycle_page_id\tenters_cycle_title",
    ]
    branches: list[BranchInfo] = []
    for i, (entry_id, basin_size, max_d, enters_cycle) in enumerate(top_rows, start=1):
        entry_id_i = int(entry_id)
        enters_i = int(enters_cycle) if enters_cycle is not None else -1
        entry_title = titles.get(entry_id_i)
        enters_title = titles.get(enters_i) if enters_i != -1 else None

        out_lines_topk.append(
            "\t".join([
                str(i),
                str(entry_id_i),
                entry_title or "<unknown>",
                str(int(basin_size)),
                str(int(max_d)),
                str(enters_i),
                enters_title or "<unknown>",
            ])
        )

        branches.append(BranchInfo(
            rank=i,
            entry_id=entry_id_i,
            entry_title=entry_title,
            basin_size=int(basin_size),
            max_depth=int(max_d),
            enters_cycle_page_id=enters_i,
            enters_cycle_title=enters_title,
        ))

    out_branches_topk.write_text("\n".join(out_lines_topk), encoding="utf-8")
    if verbose:
        print(f"Wrote top-{top_k} titled branch table: {out_branches_topk}")

    # Optionally write membership for top-K branches
    assignments_path_str: str | None = None
    if write_top_k_membership > 0 and top_rows:
        k = min(write_top_k_membership, len(top_rows))
        top_entry_ids = [int(r[0]) for r in top_rows[:k]]
        con.register(
            "top_entries",
            pa.table({"entry_id": pa.array(top_entry_ids, type=pa.int64())}),
        )

        con.execute(
            f"""
            COPY (
                SELECT page_id, entry_id, depth
                FROM seen
                WHERE entry_id IN (SELECT entry_id FROM top_entries)
            ) TO '{out_assignments.as_posix()}' (FORMAT PARQUET)
            """.strip()
        )
        assignments_path_str = str(out_assignments)
        if verbose:
            print(f"Wrote membership assignments for top-{k} branches: {out_assignments}")

    elapsed = time.time() - t0
    con.close()

    return BranchAnalysisResult(
        n=n,
        cycle_page_ids=cycle_ids,
        total_basin_nodes=total_seen,
        num_branches=n_branches,
        max_depth_reached=depth,
        branches=branches,
        branches_all_tsv_path=str(out_branches_all),
        branches_topk_tsv_path=str(out_branches_topk),
        assignments_parquet_path=assignments_path_str,
        elapsed_seconds=elapsed,
    )
