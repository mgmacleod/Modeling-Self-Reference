#!/usr/bin/env python3
"""Trace paths through specified N-sequences to demonstrate tunneling behavior.

This script traces N-link paths starting from specified pages, allowing
you to switch N values mid-trace to observe tunneling in action.

Use cases:
  - Demonstrate how paths diverge when N changes
  - Trace specific tunnel nodes through their transitions
  - Generate example paths for documentation and visualization

Output schema for tunneling_traces.tsv:
  trace_id: int              - Unique identifier for this trace
  step: int                  - Step number in the trace (0 = start)
  n_value: int               - N value used for this step
  page_id: int               - Current page
  page_title: string         - Title of current page
  next_link: string          - The Nth link followed (if any)
  basin: string              - Basin this page belongs to at current N
  event: string              - Special events (START, SWITCH_N, CYCLE, HALT)

Data dependencies:
  - data/wikipedia/processed/links_prose.parquet
  - data/wikipedia/processed/pages.parquet
  - data/wikipedia/processed/multiplex/tunnel_nodes.parquet
  - data/wikipedia/processed/multiplex/multiplex_basin_assignments.parquet
"""

from __future__ import annotations

import argparse
from pathlib import Path

import duckdb
import pandas as pd

REPO_ROOT = Path(__file__).resolve().parents[2]
PROCESSED_DIR = REPO_ROOT / "data" / "wikipedia" / "processed"
MULTIPLEX_DIR = PROCESSED_DIR / "multiplex"


class NLinkTracer:
    """Traces N-link paths with support for N-switching."""

    def __init__(self, con: duckdb.DuckDBPyConnection):
        self.con = con
        self._title_cache: dict[int, str] = {}
        self._id_cache: dict[str, int] = {}
        self._links_cache: dict[int, list[tuple[int, str, int | None]]] = {}

    def get_title(self, page_id: int) -> str:
        """Get title for a page_id."""
        if page_id not in self._title_cache:
            result = self.con.execute(
                "SELECT title FROM pages WHERE page_id = ?", [page_id]
            ).fetchone()
            self._title_cache[page_id] = result[0] if result else f"[page:{page_id}]"
        return self._title_cache[page_id]

    def get_page_id(self, title: str) -> int | None:
        """Get page_id for a title (non-redirect pages preferred)."""
        if title not in self._id_cache:
            # Prefer non-redirect pages
            result = self.con.execute("""
                SELECT page_id FROM pages
                WHERE title = ? AND is_redirect = false
                LIMIT 1
            """, [title]).fetchone()
            if result is None:
                # Fall back to any page with this title
                result = self.con.execute(
                    "SELECT page_id FROM pages WHERE title = ? LIMIT 1", [title]
                ).fetchone()
            self._id_cache[title] = result[0] if result else None
        return self._id_cache[title]

    def get_links(self, page_id: int) -> list[tuple[int, str, int | None]]:
        """Get ordered list of (position, target_title, target_id) for a page."""
        if page_id not in self._links_cache:
            # Join with pages to get target page_id, prefer non-redirects
            result = self.con.execute("""
                SELECT l.link_position, l.to_title, p.page_id as target_id
                FROM links_prose l
                LEFT JOIN pages p ON l.to_title = p.title AND p.is_redirect = false
                WHERE l.from_id = ?
                ORDER BY l.link_position, p.page_id
            """, [page_id]).fetchall()

            # Deduplicate by position (keep first match per position)
            seen_positions = set()
            deduped = []
            for pos, title, target_id in result:
                if pos not in seen_positions:
                    seen_positions.add(pos)
                    deduped.append((pos, title, target_id))

            self._links_cache[page_id] = deduped
        return self._links_cache[page_id]

    def get_nth_link_target(self, page_id: int, n: int) -> tuple[str | None, int | None]:
        """Get the Nth link target and its page_id.

        Returns:
            (target_title, target_page_id) or (None, None) if not enough links
        """
        links = self.get_links(page_id)
        if n > len(links):
            return None, None

        # Find link at position n
        for pos, title, target_id in links:
            if pos == n:
                return title, target_id

        # Fallback: use index
        if n <= len(links):
            _, title, target_id = links[n-1]
            return title, target_id

        return None, None

    def get_basin(self, page_id: int, n: int) -> str:
        """Get the basin for a page at a given N value."""
        result = self.con.execute("""
            SELECT canonical_cycle_id
            FROM multiplex_assignments
            WHERE page_id = ? AND N = ?
        """, [page_id, n]).fetchone()
        return result[0] if result else "[not_in_basin]"

    def trace(
        self,
        start_page_id: int,
        n_sequence: list[tuple[int, int]],  # List of (n_value, num_steps)
        max_total_steps: int = 100,
    ) -> list[dict]:
        """Trace a path following the given N-sequence.

        Args:
            start_page_id: Starting page
            n_sequence: List of (n_value, steps_to_take) tuples
            max_total_steps: Safety limit on total steps

        Returns:
            List of trace step dictionaries
        """
        trace = []
        current_id = start_page_id
        total_steps = 0
        visited = set()

        for n_value, num_steps in n_sequence:
            # Record N switch if not first segment
            if trace:
                prev_n = trace[-1]["n_value"]
                if prev_n != n_value:
                    trace.append({
                        "step": total_steps,
                        "n_value": n_value,
                        "page_id": current_id,
                        "page_title": self.get_title(current_id),
                        "next_link": "",
                        "basin": self.get_basin(current_id, n_value),
                        "event": f"SWITCH_N:{prev_n}→{n_value}",
                    })

            for step_in_segment in range(num_steps):
                if total_steps >= max_total_steps:
                    break

                page_title = self.get_title(current_id)
                basin = self.get_basin(current_id, n_value)

                # Check for cycle
                state = (current_id, n_value)
                if state in visited:
                    trace.append({
                        "step": total_steps,
                        "n_value": n_value,
                        "page_id": current_id,
                        "page_title": page_title,
                        "next_link": "",
                        "basin": basin,
                        "event": "CYCLE_DETECTED",
                    })
                    break

                visited.add(state)

                # Get next link
                next_title, next_id = self.get_nth_link_target(current_id, n_value)

                if next_id is None:
                    # HALT - not enough links
                    trace.append({
                        "step": total_steps,
                        "n_value": n_value,
                        "page_id": current_id,
                        "page_title": page_title,
                        "next_link": next_title or "[HALT]",
                        "basin": basin,
                        "event": "HALT",
                    })
                    break

                # Record step
                event = "START" if total_steps == 0 else ""
                trace.append({
                    "step": total_steps,
                    "n_value": n_value,
                    "page_id": current_id,
                    "page_title": page_title,
                    "next_link": next_title,
                    "basin": basin,
                    "event": event,
                })

                current_id = next_id
                total_steps += 1

            else:
                # Completed all steps in this segment
                continue
            break  # Broke out of inner loop (HALT or CYCLE)

        return trace


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Trace paths through N-sequences to demonstrate tunneling"
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=MULTIPLEX_DIR / "tunneling_traces.tsv",
        help="Output traces TSV",
    )
    parser.add_argument(
        "--start-titles",
        type=str,
        nargs="+",
        default=["Massachusetts", "Boston", "United_States"],
        help="Starting page titles",
    )
    parser.add_argument(
        "--tunnel-sample",
        type=int,
        default=20,
        help="Number of tunnel nodes to sample for automatic tracing",
    )
    parser.add_argument(
        "--steps-per-n",
        type=int,
        default=15,
        help="Steps to trace at each N value",
    )
    parser.add_argument(
        "--n-sequence",
        type=str,
        default="5:15,3:15",
        help="N-sequence as 'n:steps,n:steps,...' (default: 5:15,3:15)",
    )
    args = parser.parse_args()

    print("=" * 70)
    print("Tracing Tunneling Paths")
    print("=" * 70)
    print()

    # Parse N-sequence
    n_sequence = []
    for part in args.n_sequence.split(","):
        n, steps = part.split(":")
        n_sequence.append((int(n), int(steps)))
    print(f"N-sequence: {n_sequence}")
    print()

    # Connect to data
    print("Connecting to data sources...")
    con = duckdb.connect(":memory:")

    con.execute(f"""
        CREATE VIEW links_prose AS
        SELECT * FROM read_parquet('{PROCESSED_DIR / "links_prose.parquet"}')
    """)
    con.execute(f"""
        CREATE VIEW pages AS
        SELECT * FROM read_parquet('{PROCESSED_DIR / "pages.parquet"}')
    """)
    con.execute(f"""
        CREATE VIEW multiplex_assignments AS
        SELECT * FROM read_parquet('{MULTIPLEX_DIR / "multiplex_basin_assignments.parquet"}')
    """)
    con.execute(f"""
        CREATE VIEW tunnel_nodes AS
        SELECT * FROM read_parquet('{MULTIPLEX_DIR / "tunnel_nodes.parquet"}')
    """)
    print("  Registered all views")
    print()

    tracer = NLinkTracer(con)
    all_traces = []
    trace_id = 0

    # Trace from specified starting titles (look them up)
    print(f"Looking up specified titles: {args.start_titles}")
    for title in args.start_titles:
        page_id = tracer.get_page_id(title)
        if page_id is None:
            # Try to find in tunnel nodes by title pattern
            result = con.execute(f"""
                SELECT t.page_id, p.title
                FROM tunnel_nodes t
                JOIN pages p ON t.page_id = p.page_id
                WHERE p.title ILIKE '%{title}%' AND t.is_tunnel_node = true
                LIMIT 1
            """).fetchone()
            if result:
                page_id = result[0]
                title = result[1]
                print(f"  Found '{title}' (page_id={page_id})")
            else:
                print(f"  Warning: '{title}' not found, skipping")
                continue
        else:
            print(f"  Found '{title}' (page_id={page_id})")

        trace = tracer.trace(page_id, n_sequence)
        for step in trace:
            step["trace_id"] = trace_id
            step["start_title"] = title
        all_traces.extend(trace)
        print(f"    Traced {len(trace)} steps")
        trace_id += 1
    print()

    # Sample tunnel nodes and trace them
    if args.tunnel_sample > 0:
        print(f"Sampling {args.tunnel_sample} tunnel nodes...")

        # Get high-scoring tunnel nodes
        tunnel_sample = con.execute(f"""
            SELECT page_id
            FROM tunnel_nodes
            WHERE is_tunnel_node = true
            ORDER BY n_distinct_basins DESC, page_id
            LIMIT {args.tunnel_sample}
        """).fetchall()

        print(f"  Found {len(tunnel_sample)} tunnel nodes")

        for (page_id,) in tunnel_sample:
            title = tracer.get_title(page_id)
            trace = tracer.trace(page_id, n_sequence)
            for step in trace:
                step["trace_id"] = trace_id
                step["start_title"] = title
            all_traces.extend(trace)
            trace_id += 1

        print(f"  Traced {len(tunnel_sample)} tunnel nodes")
        print()

    # Create output dataframe
    results_df = pd.DataFrame(all_traces)

    # Reorder columns
    col_order = [
        "trace_id", "start_title", "step", "n_value", "page_id",
        "page_title", "next_link", "basin", "event"
    ]
    results_df = results_df[[c for c in col_order if c in results_df.columns]]

    # Statistics
    print("=" * 70)
    print("TRACE STATISTICS")
    print("=" * 70)
    print()

    n_traces = results_df["trace_id"].nunique()
    n_steps = len(results_df)
    print(f"Total traces: {n_traces}")
    print(f"Total steps: {n_steps}")
    print()

    # Event distribution
    if "event" in results_df.columns:
        event_counts = results_df[results_df["event"] != ""]["event"].value_counts()
        if len(event_counts) > 0:
            print("Event distribution:")
            for event, count in event_counts.items():
                print(f"  {event:20s}: {count}")
            print()

    # Basin transitions
    print("Example trace (first 20 steps):")
    first_trace = results_df[results_df["trace_id"] == 0].head(20)
    for _, row in first_trace.iterrows():
        event_str = f" [{row['event']}]" if row.get("event") else ""
        print(f"  {row['step']:3d} N={row['n_value']}: {row['page_title'][:35]:35s} → {row['next_link'][:25] if row['next_link'] else '':25s} ({row['basin'][:20]}){event_str}")
    print()

    # Write output
    print(f"Writing to {args.output}...")
    results_df.to_csv(args.output, sep="\t", index=False)
    print(f"  {len(results_df):,} rows written")
    print()

    con.close()

    print("=" * 70)
    print("DONE")
    print("=" * 70)


if __name__ == "__main__":
    main()
