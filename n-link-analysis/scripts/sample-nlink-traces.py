#!/usr/bin/env python3
"""Sample many random N-link traces (sanity check).

This is a companion to trace-nlink-path.py.

Purpose
-------
Quantify how often traces end quickly in short cycles (especially 2-cycles),
without doing full basin decomposition.

Supports both local data and HuggingFace dataset sources via --data-source.

Outputs
-------
Writes a TSV with one row per sample:
  seed, start_page_id, terminal_type, steps, path_len, transient_len, cycle_len

Optionally prints the most frequent cycles (canonicalized) and resolves titles
for those cycle nodes.

Notes
-----
- Uses the _core.trace_engine module for reusable sampling logic.
- Start pages are chosen from pages with defined Nth link (next_id != -1),
  optionally filtered by min_outdegree.

"""

from __future__ import annotations

import argparse
from pathlib import Path

from _core.trace_engine import TraceSampleResult, sample_traces
from data_loader import add_data_source_args, get_data_loader_from_args


def write_tsv(result: TraceSampleResult, out_path: Path) -> None:
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

    out_path.write_text("\n".join(lines), encoding="utf-8")


def print_summary(result: TraceSampleResult, args: argparse.Namespace) -> None:
    """Print sampling summary to stdout."""
    print()
    print("=== Sampling Summary ===")
    print(f"N={result.n}")
    print(f"Samples: {result.num_samples}")
    print(f"min_outdegree: {result.min_outdegree}")
    print(f"max_steps: {result.max_steps}")
    print(f"Terminal counts: {result.terminal_counts}")


def print_top_cycles(result: TraceSampleResult, top_k: int) -> None:
    """Print the most frequent cycles."""
    if top_k <= 0 or not result.cycle_counter:
        return

    top = result.cycle_counter.most_common(top_k)
    print()
    print(f"=== Top {min(top_k, len(top))} Cycles (by frequency) ===")

    for cyc, cnt in top:
        if result.titles:
            label = " → ".join(result.titles.get(pid, str(pid)) for pid in cyc)
        else:
            label = " → ".join(str(pid) for pid in cyc)
        print(f"count={cnt}\tlen={len(cyc)}\t{label}")


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Sample many random N-link traces and summarize cycle statistics."
    )
    add_data_source_args(parser)
    parser.add_argument(
        "--n", type=int, default=5, help="N for fixed N-link rule (default: 5)"
    )
    parser.add_argument(
        "--num", type=int, default=100, help="Number of samples to draw (default: 100)"
    )
    parser.add_argument(
        "--seed0", type=int, default=0, help="First RNG seed (default: 0)"
    )
    parser.add_argument(
        "--min-outdegree",
        type=int,
        default=50,
        help="When choosing a start page, require out_degree >= this (default: 50)",
    )
    parser.add_argument(
        "--max-steps",
        type=int,
        default=5000,
        help="Stop after this many steps (default: 5000)",
    )
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
        help="Optional output TSV path. Default: <analysis_dir>/sample_traces_n=...tsv",
    )

    args = parser.parse_args()

    if args.n <= 0:
        raise SystemExit("--n must be >= 1")
    if args.num <= 0:
        raise SystemExit("--num must be >= 1")

    # Get the data loader
    loader = get_data_loader_from_args(args)
    print(f"Data source: {loader.source_name}")
    print(f"Using nlink data: {loader.nlink_sequences_path}")

    # Use the core sampling engine
    result = sample_traces(
        loader=loader,
        n=args.n,
        num_samples=args.num,
        seed0=args.seed0,
        min_outdegree=args.min_outdegree,
        max_steps=args.max_steps,
        resolve_titles_flag=args.resolve_titles,
        progress_callback=lambda p, m: print(m) if p < 1.0 else None,
    )

    # Write output
    analysis_dir = loader.get_analysis_output_dir()
    analysis_dir.mkdir(parents=True, exist_ok=True)
    out_path = (
        Path(args.out)
        if args.out
        else (analysis_dir / f"sample_traces_n={args.n}_num={args.num}_seed0={args.seed0}.tsv")
    )

    write_tsv(result, out_path)
    print(f"Saved per-trace TSV: {out_path}")

    # Print summary
    print_summary(result, args)
    print_top_cycles(result, args.top_cycles)


if __name__ == "__main__":
    main()
