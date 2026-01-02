"""Basin mapping engine for N-Link path analysis.

This module provides the core logic for mapping basins (reverse-reachable sets)
from terminal cycles under the N-link rule. It uses reverse BFS with deduplication
to compute the set of pages that flow into a given cycle.

Extracted from map-basin-from-cycle.py for reuse in API layer.
"""

from __future__ import annotations

import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import TYPE_CHECKING, Callable

import duckdb
import pyarrow as pa

if TYPE_CHECKING:
    from data_loader import DataLoader


ProgressCallback = Callable[[float, str], None] | None


@dataclass
class LayerInfo:
    """Information about a single BFS layer."""

    depth: int
    new_nodes: int
    total_seen: int


@dataclass
class BasinMapResult:
    """Result of basin mapping operation."""

    n: int
    cycle_page_ids: list[int]
    total_nodes: int
    max_depth_reached: int
    layers: list[LayerInfo]
    stopped_reason: str  # "exhausted", "max_depth", "max_nodes"
    layers_tsv_path: str | None = None
    members_parquet_path: str | None = None
    elapsed_seconds: float = 0.0


def resolve_titles_to_ids(
    titles: list[str],
    loader: "DataLoader",
    *,
    namespace: int = 0,
    allow_redirects: bool = False,
) -> dict[str, int]:
    """Resolve page titles to page IDs.

    Args:
        titles: List of page titles to resolve.
        loader: DataLoader for accessing pages data.
        namespace: Wikipedia namespace (default: 0 = main namespace).
        allow_redirects: Whether to allow matching redirect pages.

    Returns:
        Dictionary mapping title -> page_id for found titles.
    """
    if not titles:
        return {}

    pages_path = loader.pages_path
    if not pages_path.exists():
        raise FileNotFoundError(f"Missing: {pages_path}")

    title_tbl = pa.table({"title": pa.array(titles, type=pa.string())})

    con = duckdb.connect()
    con.register("wanted_titles", title_tbl)

    redirect_clause = "" if allow_redirects else "AND p.is_redirect = FALSE"
    rows = con.execute(
        f"""
        SELECT w.title, min(p.page_id) AS page_id
        FROM wanted_titles w
        JOIN read_parquet('{pages_path.as_posix()}') p
          ON p.title = w.title
        WHERE p.namespace = {int(namespace)}
          {redirect_clause}
        GROUP BY w.title
        """.strip()
    ).fetchall()
    con.close()

    return {str(t): int(pid) for t, pid in rows}


def resolve_ids_to_titles(
    page_ids: list[int],
    loader: "DataLoader",
) -> dict[int, str]:
    """Resolve page IDs to titles.

    Args:
        page_ids: List of page IDs to resolve.
        loader: DataLoader for accessing pages data.

    Returns:
        Dictionary mapping page_id -> title for found IDs.
    """
    if not page_ids:
        return {}

    pages_path = loader.pages_path
    if not pages_path.exists():
        return {}

    unique_ids = sorted(set(int(x) for x in page_ids))
    id_tbl = pa.table({"page_id": pa.array(unique_ids, type=pa.int64())})

    con = duckdb.connect()
    con.register("wanted_ids", id_tbl)

    rows = con.execute(
        f"""
        SELECT p.page_id, p.title
        FROM read_parquet('{pages_path.as_posix()}') p
        JOIN wanted_ids w USING (page_id)
        """.strip()
    ).fetchall()
    con.close()

    return {int(pid): str(title) for pid, title in rows}


def ensure_edges_table(
    con: duckdb.DuckDBPyConnection,
    *,
    n: int,
    nlink_path: Path,
    verbose: bool = True,
) -> int:
    """Ensure edges table exists in the connection.

    Creates the edges table if it doesn't exist.

    Args:
        con: DuckDB connection.
        n: N for the N-link rule.
        nlink_path: Path to nlink_sequences.parquet.
        verbose: Whether to print progress.

    Returns:
        Number of edges in the table.
    """
    exists_row = con.execute(
        """
        SELECT COUNT(*)
        FROM information_schema.tables
        WHERE table_schema = 'main' AND table_name = 'edges'
        """.strip()
    ).fetchone()
    exists = int(exists_row[0]) if exists_row is not None else 0

    if exists:
        n_edges_row = con.execute("SELECT COUNT(*) FROM edges").fetchone()
        return int(n_edges_row[0]) if n_edges_row is not None else 0

    if not nlink_path.exists():
        raise FileNotFoundError(f"Missing: {nlink_path}")

    if verbose:
        print(f"Materializing edges table for N={n} (one-time cost)...")

    t0 = time.time()

    # Keep only defined Nth links (dst_page_id IS NOT NULL).
    con.execute(
        f"""
        CREATE TABLE edges AS
        SELECT
            page_id::BIGINT AS src_page_id,
            list_extract(link_sequence, {int(n)})::BIGINT AS dst_page_id
        FROM read_parquet('{nlink_path.as_posix()}')
        WHERE list_extract(link_sequence, {int(n)}) IS NOT NULL
        """.strip()
    )

    # An index on dst accelerates reverse expansions.
    try:
        con.execute("CREATE INDEX edges_dst_idx ON edges(dst_page_id)")
    except Exception:
        # Index creation can fail on older DuckDB builds; it will still work without it.
        pass

    dt = time.time() - t0
    n_edges_row = con.execute("SELECT COUNT(*) FROM edges").fetchone()
    n_edges = int(n_edges_row[0]) if n_edges_row is not None else 0

    if verbose:
        print(f"Edges table ready: {n_edges:,} edges in {dt:.1f}s")

    return n_edges


def get_edges_db_path(analysis_dir: Path, n: int) -> Path:
    """Get the path to the edges database for a given N."""
    return analysis_dir / f"edges_n={int(n)}.duckdb"


def map_basin(
    loader: "DataLoader",
    n: int,
    cycle_page_ids: list[int],
    *,
    max_depth: int = 0,
    max_nodes: int = 0,
    log_every: int = 1,
    write_layers_tsv: Path | None = None,
    write_members_parquet: Path | None = None,
    progress_callback: ProgressCallback = None,
    verbose: bool = True,
) -> BasinMapResult:
    """Map the basin (reverse-reachable set) feeding a given cycle.

    Uses reverse BFS to find all nodes that flow into the cycle under
    the N-link rule.

    Args:
        loader: DataLoader for accessing data files.
        n: N for the N-link rule (1-indexed).
        cycle_page_ids: List of page IDs forming the cycle.
        max_depth: Stop after this many reverse layers (0 = no limit).
        max_nodes: Stop after discovering this many nodes (0 = no limit).
        log_every: Print progress every N layers.
        write_layers_tsv: Path to write layer sizes TSV.
        write_members_parquet: Path to write membership Parquet.
        progress_callback: Optional callback for progress updates.
        verbose: Whether to print progress.

    Returns:
        BasinMapResult with mapping statistics.
    """
    if not cycle_page_ids:
        raise ValueError("At least one cycle page ID is required")

    cycle_ids = list(dict.fromkeys(int(x) for x in cycle_page_ids))  # Dedupe, preserve order

    # Get paths from loader
    nlink_path = loader.nlink_sequences_path
    analysis_dir = nlink_path.parent / "analysis"
    analysis_dir.mkdir(parents=True, exist_ok=True)

    db_path = get_edges_db_path(analysis_dir, n)
    if verbose:
        print(f"Using edges DB: {db_path}")

    con = duckdb.connect(str(db_path))
    ensure_edges_table(con, n=n, nlink_path=nlink_path, verbose=verbose)

    # Temp tables for BFS
    con.execute("CREATE TEMP TABLE seen(page_id BIGINT)")
    con.execute("CREATE TEMP TABLE frontier(page_id BIGINT)")

    cycle_tbl = pa.table({"page_id": pa.array(cycle_ids, type=pa.int64())})
    con.register("cycle_tbl", cycle_tbl)
    con.execute("INSERT INTO seen SELECT page_id FROM cycle_tbl")
    con.execute("INSERT INTO frontier SELECT page_id FROM cycle_tbl")

    # Track layer sizes
    layers: list[LayerInfo] = []
    total_seen_row = con.execute("SELECT COUNT(*) FROM seen").fetchone()
    total_seen = int(total_seen_row[0]) if total_seen_row is not None else 0
    layers.append(LayerInfo(depth=0, new_nodes=len(cycle_ids), total_seen=total_seen))

    depth = 0
    t0 = time.time()
    stopped_reason = "exhausted"

    while True:
        if max_depth and depth >= max_depth:
            stopped_reason = "max_depth"
            if verbose:
                print(f"Reached max_depth={max_depth}")
            break

        if max_nodes and total_seen >= max_nodes:
            stopped_reason = "max_nodes"
            if verbose:
                print(f"Reached max_nodes={max_nodes}")
            break

        depth += 1

        remaining_clause = ""
        if max_nodes:
            remaining = max(0, max_nodes - total_seen)
            if remaining > 0:
                remaining_clause = f"QUALIFY row_number() OVER (ORDER BY page_id) <= {remaining}"
            else:
                remaining_clause = "QUALIFY 1=0"

        con.execute("DROP TABLE IF EXISTS new_frontier")
        con.execute(
            f"""
            CREATE TEMP TABLE new_frontier AS
            SELECT DISTINCT e.src_page_id AS page_id
            FROM edges e
            JOIN frontier f
              ON e.dst_page_id = f.page_id
            LEFT JOIN seen s
              ON e.src_page_id = s.page_id
            WHERE s.page_id IS NULL
            {remaining_clause}
            """.strip()
        )

        new_count_row = con.execute("SELECT COUNT(*) FROM new_frontier").fetchone()
        new_count = int(new_count_row[0]) if new_count_row is not None else 0
        if new_count == 0:
            if verbose:
                print("Frontier exhausted (no new nodes).")
            break

        con.execute("INSERT INTO seen SELECT page_id FROM new_frontier")
        total_seen_row = con.execute("SELECT COUNT(*) FROM seen").fetchone()
        total_seen = int(total_seen_row[0]) if total_seen_row is not None else 0

        con.execute("DELETE FROM frontier")
        con.execute("INSERT INTO frontier SELECT page_id FROM new_frontier")

        layers.append(LayerInfo(depth=depth, new_nodes=new_count, total_seen=total_seen))

        dt = time.time() - t0
        rate = total_seen / max(dt, 1e-9)

        if verbose and depth % log_every == 0:
            print(f"depth={depth}\tnew={new_count:,}\ttotal={total_seen:,}\t(rate={rate:,.1f} nodes/sec)")

        if progress_callback:
            # Estimate progress based on growth rate slowing
            msg = f"Depth {depth}: {total_seen:,} nodes ({rate:,.0f}/sec)"
            # Can't know total in advance, so report depth-based progress
            progress_callback(0.0, msg)

    elapsed = time.time() - t0

    # Cleanup frontier tables
    con.execute("DROP TABLE IF EXISTS frontier")
    con.execute("DROP TABLE IF EXISTS new_frontier")

    # Write outputs if requested
    layers_path_str: str | None = None
    if write_layers_tsv:
        layer_lines = ["depth\tnew_nodes\ttotal_seen"]
        for layer in layers:
            layer_lines.append(f"{layer.depth}\t{layer.new_nodes}\t{layer.total_seen}")
        write_layers_tsv.parent.mkdir(parents=True, exist_ok=True)
        write_layers_tsv.write_text("\n".join(layer_lines), encoding="utf-8")
        layers_path_str = str(write_layers_tsv)
        if verbose:
            print(f"Saved layer sizes: {write_layers_tsv}")

    members_path_str: str | None = None
    if write_members_parquet:
        write_members_parquet.parent.mkdir(parents=True, exist_ok=True)
        con.execute(
            f"""
            COPY (SELECT page_id FROM seen) TO '{write_members_parquet.as_posix()}' (FORMAT PARQUET)
            """.strip()
        )
        members_path_str = str(write_members_parquet)
        if verbose:
            print(f"Wrote membership set: {write_members_parquet}")

    con.close()

    return BasinMapResult(
        n=n,
        cycle_page_ids=cycle_ids,
        total_nodes=total_seen,
        max_depth_reached=depth,
        layers=layers,
        stopped_reason=stopped_reason,
        layers_tsv_path=layers_path_str,
        members_parquet_path=members_path_str,
        elapsed_seconds=elapsed,
    )
