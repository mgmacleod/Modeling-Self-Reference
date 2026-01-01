#!/usr/bin/env python3
"""Analyze entry breadth (number of depth=1 entry points) for basins across N values.

Context
-------
The "entry breadth" hypothesis states that basin mass depends critically on how many
unique entry points (depth=1 preimages) feed into the terminal cycle. This script:

1. For each basin at each N, counts unique depth=1 nodes (direct cycle predecessors)
2. Computes entry_breadth / basin_mass ratio
3. Tests correlation between entry breadth and basin size
4. Validates the prediction: B₀(N=5) / B₀(N=4) ≈ 8-10×

Theory Connection
-----------------
Statistical mechanics framework predicts:
    Basin_Mass = Entry_Breadth × Path_Survival × Convergence_Optimality

This script isolates and measures the Entry_Breadth component.

Outputs
-------
- entry_breadth_n={N}_{tag}.tsv: Per-basin entry breadth metrics
- entry_breadth_summary_{tag}.tsv: Cross-N comparison
- entry_breadth_correlation_{tag}.tsv: Correlation analysis

Usage
-----
    # Single N analysis
    python analyze-basin-entry-breadth.py --n 5 --cycles-file basin_cycles.tsv

    # Cross-N batch analysis
    python analyze-basin-entry-breadth.py --n-range 3 7 --cycles-file basin_cycles.tsv

"""

from __future__ import annotations

import argparse
import sys
import time
from pathlib import Path

import duckdb
import pyarrow as pa
import pyarrow.parquet as pq

REPO_ROOT = Path(__file__).resolve().parents[2]
PROCESSED_DIR = REPO_ROOT / "data" / "wikipedia" / "processed"
NLINK_PATH = PROCESSED_DIR / "nlink_sequences.parquet"
PAGES_PATH = PROCESSED_DIR / "pages.parquet"
ANALYSIS_DIR = PROCESSED_DIR / "analysis"


def _resolve_titles_to_ids(
    titles: list[str],
    *,
    namespace: int,
    allow_redirects: bool,
) -> dict[str, int]:
    """Resolve article titles to page_ids."""
    if not titles:
        return {}
    if not PAGES_PATH.exists():
        raise FileNotFoundError(f"Missing: {PAGES_PATH}")

    title_tbl = pa.table({"title": pa.array(titles, type=pa.string())})

    con = duckdb.connect()
    con.register("wanted_titles", title_tbl)

    redirect_clause = "" if allow_redirects else "AND p.is_redirect = FALSE"
    rows = con.execute(
        f"""
        SELECT w.title, min(p.page_id) AS page_id
        FROM wanted_titles w
        JOIN read_parquet('{PAGES_PATH.as_posix()}') p
          ON p.title = w.title
        WHERE p.namespace = {int(namespace)}
          {redirect_clause}
        GROUP BY w.title
        """.strip()
    ).fetchall()
    con.close()

    return {str(t): int(pid) for t, pid in rows}


def _resolve_ids_to_titles(page_ids: list[int]) -> dict[int, str]:
    """Resolve page_ids to titles."""
    if not page_ids:
        return {}
    if not PAGES_PATH.exists():
        return {}

    unique_ids = sorted(set(int(x) for x in page_ids))
    id_tbl = pa.table({"page_id": pa.array(unique_ids, type=pa.int64())})

    con = duckdb.connect()
    con.register("wanted_ids", id_tbl)

    rows = con.execute(
        f"""
        SELECT p.page_id, p.title
        FROM read_parquet('{PAGES_PATH.as_posix()}') p
        JOIN wanted_ids w USING (page_id)
        """.strip()
    ).fetchall()
    con.close()

    return {int(pid): str(title) for pid, title in rows}


def _ensure_edges_table(con: duckdb.DuckDBPyConnection, *, n: int) -> None:
    """Ensure edges table exists in the DuckDB connection."""
    exists_row = con.execute(
        """
        SELECT COUNT(*)
        FROM information_schema.tables
        WHERE table_schema = 'main' AND table_name = 'edges'
        """.strip()
    ).fetchone()
    exists = int(exists_row[0]) if exists_row is not None else 0

    if exists:
        return

    if not NLINK_PATH.exists():
        raise FileNotFoundError(f"Missing: {NLINK_PATH}")

    print(f"Materializing edges table for N={n} (one-time cost)...")
    t0 = time.time()

    con.execute(
        f"""
        CREATE TABLE edges AS
        SELECT
            page_id::BIGINT AS src_page_id,
            list_extract(link_sequence, {int(n)})::BIGINT AS dst_page_id
        FROM read_parquet('{NLINK_PATH.as_posix()}')
        WHERE list_extract(link_sequence, {int(n)}) IS NOT NULL
        """.strip()
    )

    try:
        con.execute("CREATE INDEX edges_dst_idx ON edges(dst_page_id)")
    except Exception:
        pass

    dt = time.time() - t0
    n_edges_row = con.execute("SELECT COUNT(*) FROM edges").fetchone()
    n_edges = int(n_edges_row[0]) if n_edges_row is not None else 0
    print(f"Edges table ready: {n_edges:,} edges in {dt:.1f}s")


def compute_entry_breadth(
    con: duckdb.DuckDBPyConnection,
    cycle_ids: list[int],
    *,
    max_depth: int = 0,
) -> dict:
    """
    Compute entry breadth for a given cycle.

    Returns dict with:
        - basin_mass: Total nodes in basin
        - entry_breadth: Count of unique depth=1 entry nodes
        - entry_ratio: entry_breadth / basin_mass
        - max_depth: Maximum depth reached
        - depth_distribution: List of (depth, count) tuples
    """
    # Create temporary tables for BFS
    con.execute("DROP TABLE IF EXISTS seen")
    con.execute("DROP TABLE IF EXISTS frontier")
    con.execute("CREATE TEMP TABLE seen(page_id BIGINT PRIMARY KEY, depth INTEGER)")
    con.execute("CREATE TEMP TABLE frontier(page_id BIGINT, depth INTEGER)")

    # Seed with cycle nodes (depth 0)
    cycle_tbl = pa.table({"page_id": pa.array(cycle_ids, type=pa.int64())})
    con.register("cycle_tbl", cycle_tbl)
    con.execute("INSERT INTO seen SELECT page_id, 0 AS depth FROM cycle_tbl")
    con.execute("INSERT INTO frontier SELECT page_id, 0 AS depth FROM cycle_tbl")

    depth = 0
    depth_distribution = [(0, len(cycle_ids))]

    while True:
        if max_depth and depth >= max_depth:
            break

        # Expand one reverse layer
        con.execute("DROP TABLE IF EXISTS next_frontier")
        con.execute(
            """
            CREATE TEMP TABLE next_frontier AS
            SELECT
                e.src_page_id AS page_id,
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
            break

        con.execute("INSERT INTO seen SELECT page_id, depth FROM next_frontier")
        con.execute("DELETE FROM frontier")
        con.execute("INSERT INTO frontier SELECT page_id, depth FROM next_frontier")

        depth += 1
        depth_distribution.append((depth, new_nodes))

    # Total basin mass
    total_row = con.execute("SELECT COUNT(*) FROM seen").fetchone()
    basin_mass = int(total_row[0]) if total_row is not None else 0

    # Entry breadth (count of depth=1 nodes)
    entry_row = con.execute("SELECT COUNT(*) FROM seen WHERE depth = 1").fetchone()
    entry_breadth = int(entry_row[0]) if entry_row is not None else 0

    # Maximum depth
    max_depth_row = con.execute("SELECT MAX(depth) FROM seen").fetchone()
    actual_max_depth = int(max_depth_row[0]) if max_depth_row is not None else 0

    # Entry ratio
    entry_ratio = entry_breadth / basin_mass if basin_mass > 0 else 0.0

    return {
        "basin_mass": basin_mass,
        "entry_breadth": entry_breadth,
        "entry_ratio": entry_ratio,
        "max_depth": actual_max_depth,
        "depth_distribution": depth_distribution,
    }


def analyze_single_n(
    n: int,
    cycles: list[dict],
    *,
    tag: str,
    max_depth: int = 0,
) -> list[dict]:
    """
    Analyze entry breadth for all cycles at a given N.

    Args:
        n: N-link rule index
        cycles: List of cycle dicts with 'titles' or 'page_ids' keys
        tag: Output file tag
        max_depth: Maximum BFS depth (0 = unlimited)

    Returns:
        List of result dicts with entry breadth metrics
    """
    db_path = ANALYSIS_DIR / f"edges_n={n}.duckdb"
    print(f"\n{'='*60}")
    print(f"Analyzing N={n}")
    print(f"Database: {db_path}")
    print(f"{'='*60}")

    con = duckdb.connect(str(db_path))
    _ensure_edges_table(con, n=n)

    results = []

    for i, cycle_spec in enumerate(cycles, 1):
        # Resolve cycle node IDs
        if "page_ids" in cycle_spec:
            cycle_ids = cycle_spec["page_ids"]
            cycle_label = f"Cycle_{i}"
        elif "titles" in cycle_spec:
            titles = cycle_spec["titles"]
            title_to_id = _resolve_titles_to_ids(
                titles,
                namespace=cycle_spec.get("namespace", 0),
                allow_redirects=cycle_spec.get("allow_redirects", False),
            )
            missing = [t for t in titles if t not in title_to_id]
            if missing:
                print(f"WARNING: Could not resolve titles: {missing}")
                continue
            cycle_ids = list(title_to_id.values())
            cycle_label = " ↔ ".join(titles)
        else:
            print(f"WARNING: Cycle {i} has no 'page_ids' or 'titles'")
            continue

        print(f"\n[{i}/{len(cycles)}] {cycle_label}")
        print(f"  Cycle nodes: {len(cycle_ids)}")

        t0 = time.time()
        metrics = compute_entry_breadth(con, cycle_ids, max_depth=max_depth)
        dt = time.time() - t0

        print(f"  Basin mass: {metrics['basin_mass']:,}")
        print(f"  Entry breadth: {metrics['entry_breadth']:,}")
        print(f"  Entry ratio: {metrics['entry_ratio']:.6f}")
        print(f"  Max depth: {metrics['max_depth']}")
        print(f"  Time: {dt:.1f}s")

        results.append({
            "n": n,
            "cycle_label": cycle_label,
            "cycle_size": len(cycle_ids),
            **metrics,
        })

    con.close()

    # Write results
    out_path = ANALYSIS_DIR / f"entry_breadth_n={n}_{tag}.tsv"
    with open(out_path, "w") as f:
        f.write("n\tcycle_label\tcycle_size\tbasin_mass\tentry_breadth\tentry_ratio\tmax_depth\n")
        for r in results:
            f.write(
                f"{r['n']}\t{r['cycle_label']}\t{r['cycle_size']}\t"
                f"{r['basin_mass']}\t{r['entry_breadth']}\t{r['entry_ratio']:.6f}\t"
                f"{r['max_depth']}\n"
            )
    print(f"\nWrote: {out_path}")

    return results


def cross_n_summary(all_results: list[dict], *, tag: str) -> None:
    """Generate cross-N summary and correlation analysis."""

    # Group by cycle_label
    by_cycle = {}
    for r in all_results:
        label = r["cycle_label"]
        if label not in by_cycle:
            by_cycle[label] = []
        by_cycle[label].append(r)

    # Summary table
    out_summary = ANALYSIS_DIR / f"entry_breadth_summary_{tag}.tsv"
    with open(out_summary, "w") as f:
        f.write("cycle_label\tn\tbasin_mass\tentry_breadth\tentry_ratio\n")
        for label in sorted(by_cycle.keys()):
            for r in sorted(by_cycle[label], key=lambda x: x["n"]):
                f.write(
                    f"{label}\t{r['n']}\t{r['basin_mass']}\t"
                    f"{r['entry_breadth']}\t{r['entry_ratio']:.6f}\n"
                )
    print(f"\nWrote summary: {out_summary}")

    # Correlation analysis
    out_corr = ANALYSIS_DIR / f"entry_breadth_correlation_{tag}.tsv"
    with open(out_corr, "w") as f:
        f.write("n\ttotal_basins\tmean_entry_breadth\tmean_basin_mass\tmean_entry_ratio\n")

        by_n = {}
        for r in all_results:
            n = r["n"]
            if n not in by_n:
                by_n[n] = []
            by_n[n].append(r)

        for n in sorted(by_n.keys()):
            results = by_n[n]
            mean_breadth = sum(r["entry_breadth"] for r in results) / len(results)
            mean_mass = sum(r["basin_mass"] for r in results) / len(results)
            mean_ratio = sum(r["entry_ratio"] for r in results) / len(results)

            f.write(f"{n}\t{len(results)}\t{mean_breadth:.1f}\t{mean_mass:.1f}\t{mean_ratio:.6f}\n")

    print(f"Wrote correlation: {out_corr}")

    # Print key comparisons
    print("\n" + "="*60)
    print("KEY COMPARISONS")
    print("="*60)

    if 4 in by_n and 5 in by_n:
        n4_breadth = sum(r["entry_breadth"] for r in by_n[4]) / len(by_n[4])
        n5_breadth = sum(r["entry_breadth"] for r in by_n[5]) / len(by_n[5])
        ratio = n5_breadth / n4_breadth if n4_breadth > 0 else 0

        print(f"\nEntry Breadth Amplification (N=4 → N=5):")
        print(f"  N=4 mean entry breadth: {n4_breadth:,.1f}")
        print(f"  N=5 mean entry breadth: {n5_breadth:,.1f}")
        print(f"  Ratio (N=5 / N=4): {ratio:.2f}×")
        print(f"  Prediction: 8-10×")
        print(f"  Status: {'✓ VALIDATED' if 8 <= ratio <= 10 else '✗ NEEDS INVESTIGATION'}")


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Analyze entry breadth (depth=1 entry points) for basins across N values.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    parser.add_argument("--n", type=int, help="Single N value to analyze")
    parser.add_argument(
        "--n-range",
        type=int,
        nargs=2,
        metavar=("START", "END"),
        help="Analyze N from START to END (inclusive)",
    )
    parser.add_argument(
        "--cycles-file",
        type=str,
        help="TSV file with cycle specifications (columns: title1, title2, ...)",
    )
    parser.add_argument(
        "--cycle-title",
        type=str,
        action="append",
        default=[],
        help="Individual cycle title (repeatable, forms one cycle)",
    )
    parser.add_argument(
        "--max-depth",
        type=int,
        default=0,
        help="Maximum BFS depth (0 = unlimited, default: 0)",
    )
    parser.add_argument(
        "--tag",
        type=str,
        default="analysis",
        help="Output file tag (default: analysis)",
    )
    parser.add_argument(
        "--namespace",
        type=int,
        default=0,
        help="Namespace for title resolution (default: 0)",
    )
    parser.add_argument(
        "--allow-redirects",
        action="store_true",
        help="Allow redirect pages when resolving titles",
    )

    args = parser.parse_args()

    # Determine N values to analyze
    if args.n is not None:
        n_values = [args.n]
    elif args.n_range is not None:
        n_values = list(range(args.n_range[0], args.n_range[1] + 1))
    else:
        print("ERROR: Must specify either --n or --n-range")
        sys.exit(1)

    # Load cycle specifications
    cycles = []

    if args.cycles_file:
        # Read from TSV file
        cycles_path = Path(args.cycles_file)
        if not cycles_path.exists():
            # Try relative to ANALYSIS_DIR
            cycles_path = ANALYSIS_DIR / args.cycles_file

        if not cycles_path.exists():
            print(f"ERROR: Cycles file not found: {args.cycles_file}")
            sys.exit(1)

        with open(cycles_path) as f:
            lines = [line.strip() for line in f if line.strip() and not line.startswith("#")]

        for line in lines[1:]:  # Skip header
            parts = line.split("\t")
            titles = [p.strip() for p in parts if p.strip()]
            if titles:
                cycles.append({"titles": titles, "namespace": args.namespace, "allow_redirects": args.allow_redirects})

    if args.cycle_title:
        cycles.append({
            "titles": args.cycle_title,
            "namespace": args.namespace,
            "allow_redirects": args.allow_redirects,
        })

    if not cycles:
        print("ERROR: No cycles specified. Use --cycles-file or --cycle-title")
        sys.exit(1)

    ANALYSIS_DIR.mkdir(parents=True, exist_ok=True)

    print(f"Entry Breadth Analysis")
    print(f"N values: {n_values}")
    print(f"Cycles: {len(cycles)}")
    print(f"Tag: {args.tag}")

    # Analyze each N
    all_results = []
    for n in n_values:
        results = analyze_single_n(
            n,
            cycles,
            tag=args.tag,
            max_depth=args.max_depth,
        )
        all_results.extend(results)

    # Cross-N summary
    if len(n_values) > 1:
        cross_n_summary(all_results, tag=args.tag)

    print("\n" + "="*60)
    print("ANALYSIS COMPLETE")
    print("="*60)


if __name__ == "__main__":
    main()
