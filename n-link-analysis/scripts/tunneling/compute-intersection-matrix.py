#!/usr/bin/env python3
"""Compute basin intersection matrix across N values.

For each pair of N values (N1, N2), computes the overlap between basins:
- How many pages appear in both?
- What's the Jaccard similarity?
- What fraction of N1's basin is in N2?

This directly answers questions about basin stability across N transitions
and identifies potential tunnel nodes (pages that switch basins).

Output:
  - basin_intersection_summary.tsv: Pairwise N overlap statistics
  - basin_intersection_by_cycle.tsv: Per-cycle overlap details

Data dependencies:
  - data/wikipedia/processed/multiplex/multiplex_basin_assignments.parquet
"""

from __future__ import annotations

import argparse
from collections import defaultdict
from pathlib import Path

import duckdb
import pyarrow.parquet as pq

REPO_ROOT = Path(__file__).resolve().parents[3]
PROCESSED_DIR = REPO_ROOT / "data" / "wikipedia" / "processed"
MULTIPLEX_DIR = PROCESSED_DIR / "multiplex"


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Compute basin intersection matrix across N values"
    )
    parser.add_argument(
        "--input",
        type=Path,
        default=MULTIPLEX_DIR / "multiplex_basin_assignments.parquet",
        help="Input multiplex parquet file",
    )
    args = parser.parse_args()

    print("=" * 70)
    print("Computing Basin Intersection Matrix")
    print("=" * 70)
    print()

    if not args.input.exists():
        print(f"ERROR: Input file not found: {args.input}")
        print("Run build-multiplex-table.py first.")
        return

    # Load multiplex table
    print(f"Loading {args.input}...")
    table = pq.read_table(args.input)
    print(f"  {len(table):,} rows")
    print()

    # Get unique N values
    n_values = sorted(set(table["N"].to_pylist()))
    print(f"N values present: {n_values}")
    print()

    # Build page sets by N
    print("Building page sets by N value...")
    pages_by_n: dict[int, set[int]] = defaultdict(set)

    for row in range(len(table)):
        n = table["N"][row].as_py()
        page_id = table["page_id"][row].as_py()
        pages_by_n[n].add(page_id)

    for n in n_values:
        print(f"  N={n}: {len(pages_by_n[n]):,} unique pages")
    print()

    # Compute pairwise intersections
    print("Computing pairwise intersections...")
    print()

    results = []

    for i, n1 in enumerate(n_values):
        for n2 in n_values[i:]:
            set1 = pages_by_n[n1]
            set2 = pages_by_n[n2]

            intersection = set1 & set2
            union = set1 | set2

            intersection_size = len(intersection)
            union_size = len(union)
            jaccard = intersection_size / union_size if union_size > 0 else 0

            # Fraction of N1 in N2 and vice versa
            frac_n1_in_n2 = intersection_size / len(set1) if len(set1) > 0 else 0
            frac_n2_in_n1 = intersection_size / len(set2) if len(set2) > 0 else 0

            # Pages unique to each
            only_n1 = len(set1 - set2)
            only_n2 = len(set2 - set1)

            results.append({
                "N1": n1,
                "N2": n2,
                "size_N1": len(set1),
                "size_N2": len(set2),
                "intersection": intersection_size,
                "union": union_size,
                "jaccard": jaccard,
                "frac_N1_in_N2": frac_n1_in_n2,
                "frac_N2_in_N1": frac_n2_in_n1,
                "only_N1": only_n1,
                "only_N2": only_n2,
            })

    # Print results
    print("=" * 70)
    print("INTERSECTION MATRIX")
    print("=" * 70)
    print()

    print(f"{'N1':>3} {'N2':>3} | {'|N1|':>10} {'|N2|':>10} | {'∩':>10} {'∪':>10} | {'Jaccard':>8} | {'N1∩N2/N1':>10} {'N1∩N2/N2':>10}")
    print("-" * 100)

    for r in results:
        print(
            f"{r['N1']:>3} {r['N2']:>3} | "
            f"{r['size_N1']:>10,} {r['size_N2']:>10,} | "
            f"{r['intersection']:>10,} {r['union']:>10,} | "
            f"{r['jaccard']:>8.4f} | "
            f"{r['frac_N1_in_N2']:>10.4f} {r['frac_N2_in_N1']:>10.4f}"
        )

    # Save results
    out_path = MULTIPLEX_DIR / "basin_intersection_summary.tsv"
    with open(out_path, "w") as f:
        headers = ["N1", "N2", "size_N1", "size_N2", "intersection", "union",
                   "jaccard", "frac_N1_in_N2", "frac_N2_in_N1", "only_N1", "only_N2"]
        f.write("\t".join(headers) + "\n")
        for r in results:
            f.write("\t".join(str(r[h]) for h in headers) + "\n")

    print()
    print(f"Results saved to: {out_path}")

    # Per-cycle analysis for cycles that appear at multiple N values
    print()
    print("=" * 70)
    print("PER-CYCLE INTERSECTION (cycles appearing at multiple N values)")
    print("=" * 70)
    print()

    # Find cycles that appear at multiple N values
    con = duckdb.connect()
    con.register("multiplex", table)

    cycles_multi_n = con.execute("""
        SELECT canonical_cycle_id, list(DISTINCT N ORDER BY N) as n_values
        FROM multiplex
        GROUP BY canonical_cycle_id
        HAVING COUNT(DISTINCT N) > 1
    """).fetchall()
    con.close()

    if not cycles_multi_n:
        print("No cycles appear at multiple N values in current data.")
    else:
        cycle_results = []

        for cycle_id, cycle_n_values in cycles_multi_n:
            print(f"Cycle: {cycle_id}")
            print(f"  N values: {cycle_n_values}")

            # Build page sets for this cycle at each N
            cycle_pages_by_n: dict[int, set[int]] = defaultdict(set)

            for row in range(len(table)):
                if table["canonical_cycle_id"][row].as_py() == cycle_id:
                    n = table["N"][row].as_py()
                    page_id = table["page_id"][row].as_py()
                    cycle_pages_by_n[n].add(page_id)

            # Compute intersections
            for i, n1 in enumerate(cycle_n_values):
                for n2 in cycle_n_values[i+1:]:
                    set1 = cycle_pages_by_n[n1]
                    set2 = cycle_pages_by_n[n2]

                    intersection = set1 & set2
                    jaccard = len(intersection) / len(set1 | set2) if (set1 | set2) else 0

                    print(f"  N={n1} ({len(set1):,}) ∩ N={n2} ({len(set2):,}): "
                          f"{len(intersection):,} pages, Jaccard={jaccard:.4f}")

                    cycle_results.append({
                        "cycle_id": cycle_id,
                        "N1": n1,
                        "N2": n2,
                        "size_N1": len(set1),
                        "size_N2": len(set2),
                        "intersection": len(intersection),
                        "jaccard": jaccard,
                    })

            print()

        # Save per-cycle results
        cycle_out_path = MULTIPLEX_DIR / "basin_intersection_by_cycle.tsv"
        with open(cycle_out_path, "w") as f:
            headers = ["cycle_id", "N1", "N2", "size_N1", "size_N2", "intersection", "jaccard"]
            f.write("\t".join(headers) + "\n")
            for r in cycle_results:
                f.write("\t".join(str(r[h]) for h in headers) + "\n")

        print(f"Per-cycle results saved to: {cycle_out_path}")

    # Identify potential tunnel nodes
    print()
    print("=" * 70)
    print("TUNNEL NODE PREVIEW")
    print("=" * 70)
    print()

    # Pages that appear at multiple N values
    page_n_counts: dict[int, set[int]] = defaultdict(set)
    for row in range(len(table)):
        page_id = table["page_id"][row].as_py()
        n = table["N"][row].as_py()
        page_n_counts[page_id].add(n)

    multi_n_pages = {pid: ns for pid, ns in page_n_counts.items() if len(ns) > 1}
    print(f"Pages appearing at multiple N values: {len(multi_n_pages):,}")

    # Pages that appear in different cycles at different N values (true tunnels)
    page_cycles: dict[int, dict[int, str]] = defaultdict(dict)
    for row in range(len(table)):
        page_id = table["page_id"][row].as_py()
        n = table["N"][row].as_py()
        cycle = table["canonical_cycle_id"][row].as_py()
        page_cycles[page_id][n] = cycle

    tunnel_candidates = {
        pid: cycles for pid, cycles in page_cycles.items()
        if len(set(cycles.values())) > 1
    }
    print(f"True tunnel nodes (different cycles at different N): {len(tunnel_candidates):,}")

    # Show a few examples
    if tunnel_candidates:
        print()
        print("Example tunnel nodes:")
        for i, (pid, cycles) in enumerate(list(tunnel_candidates.items())[:5]):
            print(f"  page_id={pid}:")
            for n, cycle in sorted(cycles.items()):
                print(f"    N={n}: {cycle}")


if __name__ == "__main__":
    main()
