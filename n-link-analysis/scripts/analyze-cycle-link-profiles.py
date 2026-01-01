#!/usr/bin/env python3
"""Analyze link profiles of cycle pages to understand why certain cycles dominate at specific N.

Purpose
-------
For each cycle (e.g., Massachusetts ↔ Gulf_of_Maine), examine:
1. How many outlinks does each page have?
2. What are the first 10 links (N=1 through N=10)?
3. Are there structural properties that favor specific N values?

This helps explain:
- Why Massachusetts dominates at N=5 (mean depth 51 steps!) but not N=4 (mean depth 3 steps)
- Whether cycle pages have "magic" link positions that create attractors

Outputs
-------
1. cycle_link_profiles.tsv - Complete link sequences for all cycle pages
2. cycle_link_analysis.tsv - Summary statistics per cycle
3. Visualization showing link degree distributions for dominant cycles

Theory Connection
-----------------
Tests whether:
- Cycle dominance correlates with specific link patterns
- N=5 dominance arises from link position 5 pointing to "hub" pages
"""

from __future__ import annotations

import argparse
from pathlib import Path

import duckdb


REPO_ROOT = Path(__file__).resolve().parents[2]
PROCESSED_DIR = REPO_ROOT / "data" / "wikipedia" / "processed"
NLINK_PATH = PROCESSED_DIR / "nlink_sequences.parquet"
PAGES_PATH = PROCESSED_DIR / "pages.parquet"
ANALYSIS_DIR = PROCESSED_DIR / "analysis"


def get_page_id(title: str) -> int | None:
    """Look up page_id for a given title."""
    if not PAGES_PATH.exists():
        return None

    con = duckdb.connect()
    result = con.execute(
        f"""
        SELECT page_id
        FROM read_parquet('{PAGES_PATH.as_posix()}')
        WHERE title = ?
        """,
        [title],
    ).fetchone()
    con.close()

    return int(result[0]) if result else None


def get_link_sequence(page_id: int, max_n: int = 10) -> tuple[list[int], list[str]]:
    """Get first max_n links for a page, with titles."""
    if not NLINK_PATH.exists():
        return [], []

    con = duckdb.connect()

    # Get link sequence (page IDs)
    link_seq_result = con.execute(
        f"""
        SELECT link_sequence
        FROM read_parquet('{NLINK_PATH.as_posix()}')
        WHERE page_id = ?
        """,
        [page_id],
    ).fetchone()

    if not link_seq_result or not link_seq_result[0]:
        con.close()
        return [], []

    link_ids = list(link_seq_result[0][:max_n])

    # Resolve titles
    if not PAGES_PATH.exists():
        con.close()
        return link_ids, [str(lid) for lid in link_ids]

    # Batch lookup
    placeholders = ",".join("?" * len(link_ids))
    title_results = con.execute(
        f"""
        SELECT page_id, title
        FROM read_parquet('{PAGES_PATH.as_posix()}')
        WHERE page_id IN ({placeholders})
        """,
        link_ids,
    ).fetchall()

    con.close()

    # Map page_id → title
    id_to_title = {int(pid): str(title) for pid, title in title_results}
    titles = [id_to_title.get(lid, f"[{lid}]") for lid in link_ids]

    return link_ids, titles


def parse_cycle_pages(cycle_name: str) -> list[str]:
    """Parse cycle name into constituent page titles.

    Example: 'Massachusetts__Gulf_of_Maine' → ['Massachusetts', 'Gulf_of_Maine']
    """
    return cycle_name.split("__")


def main() -> None:
    parser = argparse.ArgumentParser(description="Analyze link profiles of cycle pages")
    parser.add_argument(
        "--cycles",
        type=str,
        default=None,
        help="Comma-separated cycle names (default: load from universal_cycles.tsv)",
    )
    parser.add_argument(
        "--max-n",
        type=int,
        default=10,
        help="Maximum N to analyze (default: 10)",
    )

    args = parser.parse_args()

    # Load cycles
    if args.cycles:
        cycle_names = [c.strip() for c in args.cycles.split(",")]
    else:
        universal_path = ANALYSIS_DIR / "universal_cycles.tsv"
        if not universal_path.exists():
            raise FileNotFoundError(
                f"No universal_cycles.tsv found. Run compare-cycle-evolution.py first, or use --cycles"
            )

        lines = universal_path.read_text(encoding="utf-8").strip().split("\n")
        cycle_names = [line.split("\t")[0] for line in lines[1:]]  # Skip header

    print(f"=== Cycle Link Profile Analysis ===")
    print(f"Analyzing {len(cycle_names)} cycles")
    print(f"Max N: {args.max_n}")
    print()

    # Analyze each cycle
    results = []

    for cycle_name in cycle_names:
        print(f"Analyzing: {cycle_name}")
        page_titles = parse_cycle_pages(cycle_name)

        for page_title in page_titles:
            page_id = get_page_id(page_title)
            if page_id is None:
                print(f"  WARNING: Could not find page_id for '{page_title}'")
                continue

            link_ids, link_titles = get_link_sequence(page_id, max_n=args.max_n)

            print(f"  {page_title} (page_id={page_id})")
            print(f"    Total outlinks: {len(link_ids)}")
            if len(link_ids) >= args.max_n:
                print(f"    First {args.max_n} links:")
                for i, (lid, ltitle) in enumerate(zip(link_ids, link_titles), start=1):
                    print(f"      N={i}: {ltitle} (id={lid})")
            else:
                print(f"    All {len(link_ids)} links:")
                for i, (lid, ltitle) in enumerate(zip(link_ids, link_titles), start=1):
                    print(f"      N={i}: {ltitle} (id={lid})")

            results.append({
                "cycle_name": cycle_name,
                "page_title": page_title,
                "page_id": page_id,
                "total_outlinks": len(link_ids),
                "link_ids": link_ids,
                "link_titles": link_titles,
            })

        print()

    # Save link profiles
    ANALYSIS_DIR.mkdir(parents=True, exist_ok=True)

    profiles_path = ANALYSIS_DIR / "cycle_link_profiles.tsv"
    header = ["cycle_name", "page_title", "page_id", "total_outlinks"] + [f"link_N={i}" for i in range(1, args.max_n + 1)]
    lines = ["\t".join(header)]

    for r in results:
        row = [
            r["cycle_name"],
            r["page_title"],
            str(r["page_id"]),
            str(r["total_outlinks"]),
        ]
        # Pad link titles to max_n
        link_titles_padded = r["link_titles"] + [""] * (args.max_n - len(r["link_titles"]))
        row.extend(link_titles_padded[:args.max_n])
        lines.append("\t".join(row))

    profiles_path.write_text("\n".join(lines), encoding="utf-8")
    print(f"Saved link profiles: {profiles_path}")

    # Save summary analysis
    summary_path = ANALYSIS_DIR / "cycle_link_analysis_summary.tsv"
    summary_lines = ["cycle_name\tpage_title\tpage_id\ttotal_outlinks\thas_5_links\thas_10_links"]

    for r in results:
        has_5 = "Yes" if r["total_outlinks"] >= 5 else "No"
        has_10 = "Yes" if r["total_outlinks"] >= 10 else "No"
        summary_lines.append(f"{r['cycle_name']}\t{r['page_title']}\t{r['page_id']}\t{r['total_outlinks']}\t{has_5}\t{has_10}")

    summary_path.write_text("\n".join(summary_lines), encoding="utf-8")
    print(f"Saved link analysis summary: {summary_path}")

    # Print summary statistics
    print()
    print("=== Summary Statistics ===")
    print(f"Total pages analyzed: {len(results)}")

    outlink_counts = [r["total_outlinks"] for r in results]
    print(f"Outlink count range: {min(outlink_counts)} to {max(outlink_counts)}")
    print(f"Mean outlinks: {sum(outlink_counts) / len(outlink_counts):.1f}")

    pages_with_5_plus = sum(1 for r in results if r["total_outlinks"] >= 5)
    pages_with_10_plus = sum(1 for r in results if r["total_outlinks"] >= 10)
    print(f"Pages with ≥5 links: {pages_with_5_plus}/{len(results)} ({100*pages_with_5_plus/len(results):.1f}%)")
    print(f"Pages with ≥10 links: {pages_with_10_plus}/{len(results)} ({100*pages_with_10_plus/len(results):.1f}%)")


if __name__ == "__main__":
    main()
