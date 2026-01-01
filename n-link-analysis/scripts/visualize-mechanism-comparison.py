#!/usr/bin/env python3
"""Visualize path characteristics comparison across N to reveal mechanisms.

Purpose
-------
Create publication-quality visualizations comparing path characteristics across N∈{3,4,5,6,7}
to explain the N=4 minimum and N=5 peak mechanisms.

Outputs
-------
Multiple PNG charts showing:
1. Convergence depth vs N (concentration indicator)
2. HALT rate vs N (fragmentation indicator)
3. Path length vs N (overall path survival)
4. Bottleneck depth vs N (where concentration occurs)
"""

from pathlib import Path
import matplotlib.pyplot as plt
import matplotlib.gridspec as gridspec

REPO_ROOT = Path(__file__).resolve().parents[2]
ANALYSIS_DIR = REPO_ROOT / "data" / "wikipedia" / "processed" / "analysis"
REPORT_DIR = REPO_ROOT / "n-link-analysis" / "report" / "assets"


def load_summary(n: int, tag: str = "mechanism") -> dict[str, float]:
    """Load summary statistics for a given N."""
    path = ANALYSIS_DIR / f"path_characteristics_n={n}_{tag}_summary.tsv"
    if not path.exists():
        raise FileNotFoundError(f"Missing summary file: {path}")

    data = {}
    for line in path.read_text(encoding="utf-8").strip().split("\n")[1:]:  # Skip header
        key, value = line.split("\t")
        try:
            data[key] = float(value)
        except ValueError:
            data[key] = value

    return data


def main() -> None:
    # Load data for N=3,4,5,6,7
    ns = [3, 4, 5, 6, 7]
    summaries = {n: load_summary(n) for n in ns}

    # Extract key metrics
    halt_rates = [summaries[n]["halt_pct"] for n in ns]
    mean_convergence_depths = [summaries[n]["mean_convergence_depth"] for n in ns]
    median_convergence_depths = [summaries[n]["median_convergence_depth"] for n in ns]
    mean_path_lens = [summaries[n]["mean_path_len"] for n in ns]
    median_path_lens = [summaries[n]["median_path_len"] for n in ns]
    early_halt_rates = [summaries[n]["early_halt_pct"] for n in ns]
    rapid_convergence_rates = [summaries[n]["rapid_convergence_pct"] for n in ns]
    mean_bottleneck_depths = [summaries[n]["mean_bottleneck_depth"] for n in ns]
    mean_min_outdegrees = [summaries[n]["mean_min_outdegree"] for n in ns]

    # Create comprehensive figure
    REPORT_DIR.mkdir(parents=True, exist_ok=True)

    # Figure 1: 4-panel mechanism comparison
    fig = plt.figure(figsize=(14, 10))
    gs = gridspec.GridSpec(2, 2, hspace=0.3, wspace=0.3)

    # Panel 1: Convergence depth (concentration indicator)
    ax1 = fig.add_subplot(gs[0, 0])
    ax1.plot(ns, median_convergence_depths, "o-", linewidth=2, markersize=8, color="#2E86AB", label="Median")
    ax1.plot(ns, mean_convergence_depths, "s--", linewidth=1.5, markersize=6, color="#A23B72", label="Mean", alpha=0.7)
    ax1.axvline(5, color="red", linestyle=":", alpha=0.3, label="N=5 peak")
    ax1.set_xlabel("N (Link Index)", fontsize=12)
    ax1.set_ylabel("Convergence Depth (steps to cycle)", fontsize=12)
    ax1.set_title("(A) Convergence Depth: Concentration Speed", fontsize=13, fontweight="bold")
    ax1.legend(fontsize=10)
    ax1.grid(True, alpha=0.3)
    ax1.set_xticks(ns)

    # Panel 2: HALT rate (fragmentation indicator)
    ax2 = fig.add_subplot(gs[0, 1])
    ax2.plot(ns, halt_rates, "o-", linewidth=2, markersize=8, color="#F18F01")
    ax2.axvline(5, color="red", linestyle=":", alpha=0.3, label="N=5 peak")
    ax2.set_xlabel("N (Link Index)", fontsize=12)
    ax2.set_ylabel("HALT Rate (%)", fontsize=12)
    ax2.set_title("(B) HALT Rate: Fragmentation Indicator", fontsize=13, fontweight="bold")
    ax2.legend(fontsize=10)
    ax2.grid(True, alpha=0.3)
    ax2.set_xticks(ns)

    # Panel 3: Path length (overall survival)
    ax3 = fig.add_subplot(gs[1, 0])
    ax3.plot(ns, median_path_lens, "o-", linewidth=2, markersize=8, color="#06A77D", label="Median")
    ax3.plot(ns, mean_path_lens, "s--", linewidth=1.5, markersize=6, color="#D81E5B", label="Mean", alpha=0.7)
    ax3.axvline(5, color="red", linestyle=":", alpha=0.3, label="N=5 peak")
    ax3.set_xlabel("N (Link Index)", fontsize=12)
    ax3.set_ylabel("Path Length (total steps)", fontsize=12)
    ax3.set_title("(C) Path Length: Overall Path Survival", fontsize=13, fontweight="bold")
    ax3.legend(fontsize=10)
    ax3.grid(True, alpha=0.3)
    ax3.set_xticks(ns)

    # Panel 4: Rapid convergence rate (concentration success)
    ax4 = fig.add_subplot(gs[1, 1])
    ax4.plot(ns, rapid_convergence_rates, "o-", linewidth=2, markersize=8, color="#9B59B6")
    ax4.axvline(5, color="red", linestyle=":", alpha=0.3, label="N=5 peak")
    ax4.set_xlabel("N (Link Index)", fontsize=12)
    ax4.set_ylabel("Rapid Convergence Rate (% <50 steps)", fontsize=12)
    ax4.set_title("(D) Rapid Convergence: Fast Path Concentration", fontsize=13, fontweight="bold")
    ax4.legend(fontsize=10)
    ax4.grid(True, alpha=0.3)
    ax4.set_xticks(ns)

    fig.suptitle("Path Mechanism Comparison Across N: Fragmentation vs Concentration", fontsize=15, fontweight="bold", y=0.995)

    out_path = REPORT_DIR / "mechanism_comparison_n3_to_n7.png"
    fig.savefig(out_path, dpi=300, bbox_inches="tight")
    print(f"Saved mechanism comparison: {out_path}")
    plt.close(fig)

    # Figure 2: Bottleneck analysis
    fig2, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 5))

    # Bottleneck depth
    ax1.plot(ns, mean_bottleneck_depths, "o-", linewidth=2, markersize=8, color="#E63946")
    ax1.axvline(5, color="red", linestyle=":", alpha=0.3, label="N=5 peak")
    ax1.set_xlabel("N (Link Index)", fontsize=12)
    ax1.set_ylabel("Mean Bottleneck Depth (steps)", fontsize=12)
    ax1.set_title("(A) Bottleneck Depth: Where Concentration Occurs", fontsize=13, fontweight="bold")
    ax1.legend(fontsize=10)
    ax1.grid(True, alpha=0.3)
    ax1.set_xticks(ns)

    # Minimum outdegree (bottleneck intensity)
    ax2.plot(ns, mean_min_outdegrees, "o-", linewidth=2, markersize=8, color="#457B9D")
    ax2.axvline(5, color="red", linestyle=":", alpha=0.3, label="N=5 peak")
    ax2.set_xlabel("N (Link Index)", fontsize=12)
    ax2.set_ylabel("Mean Min Outdegree (bottleneck width)", fontsize=12)
    ax2.set_title("(B) Bottleneck Intensity: Narrowest Point", fontsize=13, fontweight="bold")
    ax2.legend(fontsize=10)
    ax2.grid(True, alpha=0.3)
    ax2.set_xticks(ns)

    fig2.suptitle("Bottleneck Analysis: Path Concentration Points", fontsize=15, fontweight="bold")
    fig2.tight_layout()

    out_path2 = REPORT_DIR / "bottleneck_analysis_n3_to_n7.png"
    fig2.savefig(out_path2, dpi=300, bbox_inches="tight")
    print(f"Saved bottleneck analysis: {out_path2}")
    plt.close(fig2)

    # Print comparative table
    print()
    print("=== Path Characteristics Comparison ===")
    print()
    print("| N | HALT % | Med Conv | Med Path | Rapid Conv % | Bottleneck Depth |")
    print("|---|--------|----------|----------|--------------|------------------|")
    for n in ns:
        s = summaries[n]
        print(f"| {n} | {s['halt_pct']:.1f}% | {s['median_convergence_depth']:.1f} | {s['median_path_len']:.1f} | {s['rapid_convergence_pct']:.1f}% | {s['mean_bottleneck_depth']:.1f} |")

    print()
    print("=== Key Mechanism Insights ===")
    print()
    print("1. HALT RATE (Fragmentation):")
    print(f"   - N=3: {halt_rates[0]:.1f}% (low fragmentation)")
    print(f"   - N=4: {halt_rates[1]:.1f}% (still low)")
    print(f"   - N=5: {halt_rates[2]:.1f}% (lowest!)")
    print(f"   - N=6: {halt_rates[3]:.1f}% (4× increase)")
    print(f"   - N=7: {halt_rates[4]:.1f}% (5× increase from N=5)")
    print()
    print("2. CONVERGENCE DEPTH (Concentration Speed):")
    print(f"   - N=3: {median_convergence_depths[0]:.1f} steps (slower)")
    print(f"   - N=4: {median_convergence_depths[1]:.1f} steps (fastest!)")
    print(f"   - N=5: {median_convergence_depths[2]:.1f} steps (slightly slower)")
    print(f"   - N=6: {median_convergence_depths[3]:.1f} steps (fast)")
    print(f"   - N=7: {median_convergence_depths[4]:.1f} steps (slowest)")
    print()
    print("3. PATH LENGTH (Overall Survival):")
    print(f"   - N=3: {median_path_lens[0]:.1f} steps")
    print(f"   - N=4: {median_path_lens[1]:.1f} steps (shortest!)")
    print(f"   - N=5: {median_path_lens[2]:.1f} steps")
    print(f"   - N=6: {median_path_lens[3]:.1f} steps")
    print(f"   - N=7: {median_path_lens[4]:.1f} steps (longest!)")
    print()
    print("4. RAPID CONVERGENCE RATE (<50 steps):")
    print(f"   - N=3: {rapid_convergence_rates[0]:.1f}% (very high)")
    print(f"   - N=4: {rapid_convergence_rates[1]:.1f}% (very high)")
    print(f"   - N=5: {rapid_convergence_rates[2]:.1f}% (lowest!)")
    print(f"   - N=6: {rapid_convergence_rates[3]:.1f}% (lower)")
    print(f"   - N=7: {rapid_convergence_rates[4]:.1f}% (much lower)")


if __name__ == "__main__":
    main()
