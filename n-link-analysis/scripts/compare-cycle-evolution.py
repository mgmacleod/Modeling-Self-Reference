#!/usr/bin/env python3
"""Compare how individual cycles evolve across N values.

Purpose
-------
Analyze why certain cycles (like Massachusetts ↔ Gulf_of_Maine) dominate at specific N values.
Tracks basin size, depth distribution, and dominance percentage across N.

This script answers:
1. Why does Massachusetts have 1M nodes at N=5 but only 11k at N=4?
2. What structural properties change across N?
3. Which cycles are "universal" (appear at all N)?

Outputs
-------
1. cycle_evolution_summary.tsv - Basin metrics for each cycle × N combination
2. cycle_dominance_matrix.tsv - Dominance percentage for each cycle across N
3. universal_cycles.tsv - Cycles that appear at all N values
4. Visualizations showing basin size evolution

Theory Connection
-----------------
Tests whether cycle dominance is:
- Graph-intrinsic (same cycles dominate at all N)
- Rule-dependent (different cycles dominate at different N)

References
----------
See MECHANISM-ANALYSIS.md for context on premature convergence
See PHASE-TRANSITION-REFINED.md for N=5 peak phenomenon
"""

from __future__ import annotations

import argparse
from collections import defaultdict
from pathlib import Path
from typing import Optional

import matplotlib.pyplot as plt
import matplotlib.gridspec as gridspec
import numpy as np


REPO_ROOT = Path(__file__).resolve().parents[2]
ANALYSIS_DIR = REPO_ROOT / "data" / "wikipedia" / "processed" / "analysis"
REPORT_DIR = REPO_ROOT / "n-link-analysis" / "report" / "assets"


def parse_cycle_name(filename: str) -> Optional[str]:
    """Extract canonical cycle name from basin filename.

    Example: 'basin_n=5_cycle=Massachusetts__Gulf_of_Maine_reproduction_2025-12-31_layers.tsv'
    Returns: 'Massachusetts__Gulf_of_Maine'
    """
    if not filename.startswith("basin_n="):
        return None

    parts = filename.split("_cycle=")
    if len(parts) < 2:
        return None

    cycle_part = parts[1].split("_reproduction_")[0]
    return cycle_part


def load_basin_size(filepath: Path) -> int:
    """Load total basin size from layers TSV."""
    if not filepath.exists():
        return 0

    lines = filepath.read_text(encoding="utf-8").strip().split("\n")
    if len(lines) < 2:
        return 0

    # Last line has total_seen
    last_line = lines[-1]
    parts = last_line.split("\t")
    if len(parts) < 3:
        return 0

    try:
        return int(parts[2])
    except ValueError:
        return 0


def load_depth_stats(filepath: Path) -> dict[str, float]:
    """Load depth distribution statistics from layers TSV."""
    if not filepath.exists():
        return {}

    lines = filepath.read_text(encoding="utf-8").strip().split("\n")
    if len(lines) < 2:
        return {}

    depths = []
    new_nodes = []

    for line in lines[1:]:  # Skip header
        parts = line.split("\t")
        if len(parts) < 2:
            continue
        try:
            depth = int(parts[0])
            nodes = int(parts[1])
            depths.append(depth)
            new_nodes.append(nodes)
        except ValueError:
            continue

    if not new_nodes:
        return {}

    # Compute weighted statistics
    total_nodes = sum(new_nodes)
    mean_depth = sum(d * n for d, n in zip(depths, new_nodes)) / total_nodes if total_nodes > 0 else 0

    # Median depth (approximate)
    cumsum = 0
    median_depth = 0
    for d, n in zip(depths, new_nodes):
        cumsum += n
        if cumsum >= total_nodes / 2:
            median_depth = d
            break

    # Max depth
    max_depth = max(depths) if depths else 0

    # Depth at which 90% of basin is captured
    cumsum = 0
    depth_90 = 0
    for d, n in zip(depths, new_nodes):
        cumsum += n
        if cumsum >= 0.9 * total_nodes:
            depth_90 = d
            break

    return {
        "mean_depth": mean_depth,
        "median_depth": median_depth,
        "max_depth": max_depth,
        "depth_90": depth_90,
        "total_nodes": total_nodes,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Compare cycle evolution across N values")
    parser.add_argument(
        "--n-values",
        type=str,
        default="3,4,5,6,7",
        help="Comma-separated N values to analyze (default: 3,4,5,6,7)",
    )

    args = parser.parse_args()
    n_values = [int(n.strip()) for n in args.n_values.split(",")]

    print(f"=== Cycle Evolution Analysis ===")
    print(f"Analyzing N values: {n_values}")
    print()

    # Discover all cycles
    cycle_data: dict[str, dict[int, dict]] = defaultdict(lambda: defaultdict(dict))

    for n in n_values:
        pattern = f"basin_n={n}_cycle=*_layers.tsv"
        basin_files = list(ANALYSIS_DIR.glob(pattern))

        print(f"N={n}: Found {len(basin_files)} basin files")

        for filepath in basin_files:
            cycle_name = parse_cycle_name(filepath.name)
            if not cycle_name:
                continue

            size = load_basin_size(filepath)
            depth_stats = load_depth_stats(filepath)

            cycle_data[cycle_name][n] = {
                "size": size,
                **depth_stats,
            }

    print()
    print(f"Total unique cycles found: {len(cycle_data)}")
    print()

    # Identify universal cycles (appear at all N)
    universal_cycles = []
    for cycle_name, n_data in cycle_data.items():
        if all(n in n_data for n in n_values):
            universal_cycles.append(cycle_name)

    print(f"Universal cycles (appear at all N={n_values}): {len(universal_cycles)}")
    for cycle_name in sorted(universal_cycles):
        sizes = [cycle_data[cycle_name][n]["size"] for n in n_values]
        print(f"  {cycle_name}: {sizes}")
    print()

    # Compute total basin mass per N
    total_mass: dict[int, int] = {}
    for n in n_values:
        total = sum(
            data[n].get("size", 0)
            for data in cycle_data.values()
            if n in data
        )
        total_mass[n] = total

    print("Total basin mass per N:")
    for n in n_values:
        print(f"  N={n}: {total_mass[n]:,} nodes")
    print()

    # Compute dominance percentages
    dominance: dict[str, dict[int, float]] = {}
    for cycle_name, n_data in cycle_data.items():
        dominance[cycle_name] = {}
        for n in n_values:
            if n in n_data and total_mass[n] > 0:
                dominance[cycle_name][n] = 100.0 * n_data[n]["size"] / total_mass[n]
            else:
                dominance[cycle_name][n] = 0.0

    # Save cycle evolution summary
    summary_path = ANALYSIS_DIR / "cycle_evolution_summary.tsv"
    header = ["cycle_name", "N", "basin_size", "dominance_pct", "mean_depth", "median_depth", "max_depth", "depth_90"]
    lines = ["\t".join(header)]

    for cycle_name in sorted(cycle_data.keys()):
        for n in n_values:
            if n in cycle_data[cycle_name]:
                data = cycle_data[cycle_name][n]
                dom = dominance[cycle_name][n]
                lines.append("\t".join([
                    cycle_name,
                    str(n),
                    str(data.get("size", 0)),
                    f"{dom:.2f}",
                    f"{data.get('mean_depth', 0):.1f}",
                    str(int(data.get("median_depth", 0))),
                    str(int(data.get("max_depth", 0))),
                    str(int(data.get("depth_90", 0))),
                ]))

    summary_path.write_text("\n".join(lines), encoding="utf-8")
    print(f"Saved cycle evolution summary: {summary_path}")

    # Save dominance matrix
    matrix_path = ANALYSIS_DIR / "cycle_dominance_matrix.tsv"
    matrix_lines = ["cycle_name\t" + "\t".join(f"N={n}" for n in n_values)]

    for cycle_name in sorted(dominance.keys(), key=lambda c: -max(dominance[c].values())):
        row = [cycle_name] + [f"{dominance[cycle_name][n]:.1f}%" for n in n_values]
        matrix_lines.append("\t".join(row))

    matrix_path.write_text("\n".join(matrix_lines), encoding="utf-8")
    print(f"Saved dominance matrix: {matrix_path}")

    # Save universal cycles
    if universal_cycles:
        universal_path = ANALYSIS_DIR / "universal_cycles.tsv"
        universal_lines = ["cycle_name\t" + "\t".join(f"size_N={n}" for n in n_values)]

        for cycle_name in sorted(universal_cycles):
            row = [cycle_name] + [str(cycle_data[cycle_name][n]["size"]) for n in n_values]
            universal_lines.append("\t".join(row))

        universal_path.write_text("\n".join(universal_lines), encoding="utf-8")
        print(f"Saved universal cycles: {universal_path}")

    # Generate visualizations
    REPORT_DIR.mkdir(parents=True, exist_ok=True)

    # Figure 1: Universal cycle size evolution
    if universal_cycles:
        fig, ax = plt.subplots(figsize=(12, 7))

        colors = plt.cm.tab10(np.linspace(0, 1, len(universal_cycles)))

        for i, cycle_name in enumerate(sorted(universal_cycles)):
            sizes = [cycle_data[cycle_name][n]["size"] for n in n_values]
            ax.plot(n_values, sizes, "o-", linewidth=2, markersize=8,
                   label=cycle_name.replace("__", " ↔ "), color=colors[i])

        ax.set_xlabel("N (Link Index)", fontsize=13)
        ax.set_ylabel("Basin Size (nodes)", fontsize=13)
        ax.set_title("Universal Cycle Evolution: Basin Size Across N", fontsize=14, fontweight="bold")
        ax.set_yscale("log")
        ax.legend(fontsize=10, loc="best")
        ax.grid(True, alpha=0.3)
        ax.set_xticks(n_values)

        out_path = REPORT_DIR / "cycle_evolution_basin_sizes.png"
        fig.savefig(out_path, dpi=300, bbox_inches="tight")
        print(f"Saved basin size evolution: {out_path}")
        plt.close(fig)

    # Figure 2: Dominance percentage evolution
    if universal_cycles:
        fig, ax = plt.subplots(figsize=(12, 7))

        for i, cycle_name in enumerate(sorted(universal_cycles)):
            doms = [dominance[cycle_name][n] for n in n_values]
            ax.plot(n_values, doms, "o-", linewidth=2, markersize=8,
                   label=cycle_name.replace("__", " ↔ "), color=colors[i])

        ax.set_xlabel("N (Link Index)", fontsize=13)
        ax.set_ylabel("Dominance (%)", fontsize=13)
        ax.set_title("Universal Cycle Dominance: Share of Total Basin Mass", fontsize=14, fontweight="bold")
        ax.legend(fontsize=10, loc="best")
        ax.grid(True, alpha=0.3)
        ax.set_xticks(n_values)
        ax.axhline(50, color="red", linestyle=":", alpha=0.3, label="50% dominance")

        out_path = REPORT_DIR / "cycle_dominance_evolution.png"
        fig.savefig(out_path, dpi=300, bbox_inches="tight")
        print(f"Saved dominance evolution: {out_path}")
        plt.close(fig)

    # Figure 3: Massachusetts deep-dive (if present)
    massachusetts_cycle = None
    for cycle_name in cycle_data.keys():
        if "Massachusetts" in cycle_name:
            massachusetts_cycle = cycle_name
            break

    if massachusetts_cycle:
        print()
        print(f"=== Massachusetts Deep-Dive ===")
        print(f"Cycle: {massachusetts_cycle}")
        print()

        # Filter to only N values where Massachusetts has data
        mass_n_values = [n for n in n_values if n in cycle_data[massachusetts_cycle] and "size" in cycle_data[massachusetts_cycle][n]]

        if not mass_n_values:
            print("No Massachusetts data found for any N values")
        else:
            fig = plt.figure(figsize=(14, 10))
            gs = gridspec.GridSpec(2, 2, hspace=0.3, wspace=0.3)

            # Panel 1: Basin size across N
            ax1 = fig.add_subplot(gs[0, 0])
            sizes = [cycle_data[massachusetts_cycle][n]["size"] for n in mass_n_values]
        ax1.plot(n_values, sizes, "o-", linewidth=3, markersize=10, color="#E63946")
        ax1.axvline(5, color="red", linestyle=":", alpha=0.3, label="N=5 peak")
        ax1.set_xlabel("N (Link Index)", fontsize=12)
        ax1.set_ylabel("Basin Size (nodes)", fontsize=12)
        ax1.set_title("(A) Massachusetts Basin Size Evolution", fontsize=13, fontweight="bold")
        ax1.set_yscale("log")
        ax1.legend(fontsize=10)
        ax1.grid(True, alpha=0.3)
        ax1.set_xticks(n_values)

        # Panel 2: Dominance percentage
        ax2 = fig.add_subplot(gs[0, 1])
        doms = [dominance[massachusetts_cycle][n] for n in n_values]
        ax2.plot(n_values, doms, "o-", linewidth=3, markersize=10, color="#457B9D")
        ax2.axvline(5, color="red", linestyle=":", alpha=0.3, label="N=5 peak")
        ax2.axhline(50, color="gray", linestyle="--", alpha=0.3, label="50% majority")
        ax2.set_xlabel("N (Link Index)", fontsize=12)
        ax2.set_ylabel("Dominance (%)", fontsize=12)
        ax2.set_title("(B) Massachusetts Dominance Percentage", fontsize=13, fontweight="bold")
        ax2.legend(fontsize=10)
        ax2.grid(True, alpha=0.3)
        ax2.set_xticks(n_values)

        # Panel 3: Mean depth evolution
        ax3 = fig.add_subplot(gs[1, 0])
        mean_depths = [cycle_data[massachusetts_cycle][n].get("mean_depth", 0) for n in n_values]
        ax3.plot(n_values, mean_depths, "o-", linewidth=3, markersize=10, color="#06A77D")
        ax3.axvline(5, color="red", linestyle=":", alpha=0.3, label="N=5 peak")
        ax3.set_xlabel("N (Link Index)", fontsize=12)
        ax3.set_ylabel("Mean Depth (steps)", fontsize=12)
        ax3.set_title("(C) Massachusetts Mean Basin Depth", fontsize=13, fontweight="bold")
        ax3.legend(fontsize=10)
        ax3.grid(True, alpha=0.3)
        ax3.set_xticks(n_values)

        # Panel 4: Amplification factors (only if N=5 exists in data)
        ax4 = fig.add_subplot(gs[1, 1])
        if 5 in cycle_data[massachusetts_cycle] and "size" in cycle_data[massachusetts_cycle][5]:
            n5_size = cycle_data[massachusetts_cycle][5]["size"]
            amplifications = [n5_size / cycle_data[massachusetts_cycle][n]["size"] if cycle_data[massachusetts_cycle][n]["size"] > 0 else 0 for n in n_values]
            ax4.bar(n_values, amplifications, color="#F18F01", alpha=0.7, edgecolor="black")
            ax4.axhline(1, color="red", linestyle="--", alpha=0.5, label="N=5 baseline")
            ax4.set_xlabel("N (Link Index)", fontsize=12)
            ax4.set_ylabel("Amplification vs N=5", fontsize=12)
            ax4.set_title("(D) Massachusetts Size Amplification (N=5 as baseline)", fontsize=13, fontweight="bold")
            ax4.set_yscale("log")
            ax4.legend(fontsize=10)
            ax4.grid(True, alpha=0.3, axis="y")
            ax4.set_xticks(n_values)
        else:
            # If N=5 doesn't exist, show relative sizes normalized to first N value
            baseline_n = n_values[0]
            baseline_size = cycle_data[massachusetts_cycle][baseline_n]["size"]
            relative_sizes = [cycle_data[massachusetts_cycle][n]["size"] / baseline_size if baseline_size > 0 else 0 for n in n_values]
            ax4.bar(n_values, relative_sizes, color="#F18F01", alpha=0.7, edgecolor="black")
            ax4.axhline(1, color="red", linestyle="--", alpha=0.5, label=f"N={baseline_n} baseline")
            ax4.set_xlabel("N (Link Index)", fontsize=12)
            ax4.set_ylabel(f"Size relative to N={baseline_n}", fontsize=12)
            ax4.set_title(f"(D) Massachusetts Size Relative to N={baseline_n}", fontsize=13, fontweight="bold")
            ax4.set_yscale("log")
            ax4.legend(fontsize=10)
            ax4.grid(True, alpha=0.3, axis="y")
            ax4.set_xticks(n_values)

        fig.suptitle(f"Massachusetts ↔ Gulf of Maine: The N=5 Dominance Mystery", fontsize=15, fontweight="bold", y=0.995)

        out_path = REPORT_DIR / "massachusetts_deep_dive.png"
        fig.savefig(out_path, dpi=300, bbox_inches="tight")
        print(f"Saved Massachusetts deep-dive: {out_path}")
        plt.close(fig)

        # Print Massachusetts statistics
        print("Basin Size Evolution:")
        for n in n_values:
            size = cycle_data[massachusetts_cycle][n]["size"]
            dom = dominance[massachusetts_cycle][n]
            mean_d = cycle_data[massachusetts_cycle][n].get("mean_depth", 0)
            max_d = cycle_data[massachusetts_cycle][n].get("max_depth", 0)
            print(f"  N={n}: {size:>9,} nodes ({dom:5.1f}% dominance), mean_depth={mean_d:5.1f}, max_depth={max_d:3d}")

        # Only print amplification factors if N=5 data exists
        if 5 in cycle_data[massachusetts_cycle] and "size" in cycle_data[massachusetts_cycle][5]:
            n5_size = cycle_data[massachusetts_cycle][5]["size"]
            print()
            print("Amplification Factors (relative to N=5):")
            for n in n_values:
                if cycle_data[massachusetts_cycle][n]["size"] > 0:
                    amp = n5_size / cycle_data[massachusetts_cycle][n]["size"]
                    print(f"  N=5 / N={n}: {amp:6.1f}×")
        else:
            # Use first N as baseline
            baseline_n = n_values[0]
            baseline_size = cycle_data[massachusetts_cycle][baseline_n]["size"]
            print()
            print(f"Relative Size Factors (relative to N={baseline_n}):")
            for n in n_values:
                if cycle_data[massachusetts_cycle][n]["size"] > 0 and baseline_size > 0:
                    rel = cycle_data[massachusetts_cycle][n]["size"] / baseline_size
                    print(f"  N={n} / N={baseline_n}: {rel:6.2f}×")


if __name__ == "__main__":
    main()
