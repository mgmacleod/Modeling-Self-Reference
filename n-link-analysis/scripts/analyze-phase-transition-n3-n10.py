#!/usr/bin/env python3
"""Analyze phase transition curve from N=3 to N=10.

Generates comprehensive visualizations and statistics for the N-link rule
phase transition discovered in Wikipedia data.
"""

from __future__ import annotations

import argparse
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns

REPO_ROOT = Path(__file__).resolve().parents[2]
ANALYSIS_DIR = REPO_ROOT / "data" / "wikipedia" / "processed" / "analysis"
REPORT_DIR = REPO_ROOT / "n-link-analysis" / "report"
ASSETS_DIR = REPORT_DIR / "assets"


def load_cycle_evolution() -> pd.DataFrame:
    """Load cycle evolution summary."""
    path = ANALYSIS_DIR / "cycle_evolution_summary.tsv"
    df = pd.read_csv(path, sep="\t")

    # Clean up duplicate entries - prefer multi_n_jan_2026 tags
    df["priority"] = df["cycle_name"].apply(
        lambda x: 0 if "multi_n_jan_2026" in x else 1
    )
    df = df.sort_values("priority").drop_duplicates(
        subset=["cycle_name", "N"], keep="first"
    )

    return df


def compute_aggregate_statistics(df: pd.DataFrame) -> pd.DataFrame:
    """Compute aggregate statistics per N value."""
    # Group by N and compute totals
    agg = df.groupby("N").agg({
        "basin_size": ["sum", "mean", "median", "max", "count"]
    }).reset_index()

    agg.columns = ["N", "total_mass", "mean_size", "median_size", "max_size", "num_basins"]
    return agg


def plot_phase_transition_curve(agg: pd.DataFrame, output_path: Path) -> None:
    """Plot the main phase transition curve."""
    fig, axes = plt.subplots(2, 2, figsize=(14, 10))
    fig.suptitle("N-Link Rule Phase Transition Curve (N=3 to N=10)", fontsize=16, fontweight="bold")

    n_values = agg["N"].values

    # Panel 1: Total basin mass (log scale)
    ax = axes[0, 0]
    ax.semilogy(n_values, agg["total_mass"], "o-", linewidth=2, markersize=8, color="darkblue")
    ax.axvline(5, color="red", linestyle="--", alpha=0.5, label="N=5 (Peak)")
    ax.set_xlabel("N (Link Position)", fontsize=12)
    ax.set_ylabel("Total Basin Mass (nodes)", fontsize=12)
    ax.set_title("Total Basin Mass Across N", fontsize=13, fontweight="bold")
    ax.grid(True, alpha=0.3)
    ax.legend()

    # Add annotations
    peak_idx = agg["total_mass"].argmax()
    peak_n = agg.iloc[peak_idx]["N"]
    peak_mass = agg.iloc[peak_idx]["total_mass"]
    ax.annotate(
        f"Peak: N={int(peak_n)}\n{peak_mass:,.0f} nodes",
        xy=(peak_n, peak_mass),
        xytext=(peak_n + 0.5, peak_mass * 2),
        arrowprops=dict(arrowstyle="->", color="red"),
        fontsize=10,
        bbox=dict(boxstyle="round,pad=0.5", facecolor="yellow", alpha=0.7)
    )

    # Panel 2: Amplification factor (relative to N=4)
    ax = axes[0, 1]
    baseline_mass = agg[agg["N"] == 4]["total_mass"].values[0]
    amplification = agg["total_mass"] / baseline_mass
    ax.semilogy(n_values, amplification, "s-", linewidth=2, markersize=8, color="darkgreen")
    ax.axhline(1, color="gray", linestyle=":", alpha=0.5)
    ax.axvline(5, color="red", linestyle="--", alpha=0.5)
    ax.set_xlabel("N (Link Position)", fontsize=12)
    ax.set_ylabel("Amplification Factor (vs N=4)", fontsize=12)
    ax.set_title("Basin Mass Amplification", fontsize=13, fontweight="bold")
    ax.grid(True, alpha=0.3)

    # Add N=5 amplification annotation
    n5_amp = amplification[agg["N"] == 5].values[0]
    ax.annotate(
        f"N=5: {n5_amp:.1f}× amplification",
        xy=(5, n5_amp),
        xytext=(6, n5_amp / 2),
        arrowprops=dict(arrowstyle="->", color="red"),
        fontsize=10,
        bbox=dict(boxstyle="round,pad=0.5", facecolor="yellow", alpha=0.7)
    )

    # Panel 3: Number of basins
    ax = axes[1, 0]
    ax.bar(n_values, agg["num_basins"], color="steelblue", alpha=0.7, edgecolor="black")
    ax.set_xlabel("N (Link Position)", fontsize=12)
    ax.set_ylabel("Number of Basins Observed", fontsize=12)
    ax.set_title("Basin Diversity Across N", fontsize=13, fontweight="bold")
    ax.grid(True, alpha=0.3, axis="y")

    # Panel 4: Mean basin size
    ax = axes[1, 1]
    ax.semilogy(n_values, agg["mean_size"], "^-", linewidth=2, markersize=8, color="purple")
    ax.axvline(5, color="red", linestyle="--", alpha=0.5)
    ax.set_xlabel("N (Link Position)", fontsize=12)
    ax.set_ylabel("Mean Basin Size (nodes)", fontsize=12)
    ax.set_title("Mean Basin Size Across N", fontsize=13, fontweight="bold")
    ax.grid(True, alpha=0.3)

    plt.tight_layout()
    plt.savefig(output_path, dpi=300, bbox_inches="tight")
    print(f"✓ Saved: {output_path}")


def plot_massachusetts_evolution(df: pd.DataFrame, output_path: Path) -> None:
    """Plot Massachusetts basin evolution across N."""
    mass_df = df[df["cycle_name"].str.contains("Massachusetts", na=False)]

    # Clean duplicates
    mass_df = mass_df.sort_values("basin_size", ascending=False).drop_duplicates(
        subset=["N"], keep="first"
    )
    mass_df = mass_df.sort_values("N")

    if mass_df.empty:
        print("Warning: No Massachusetts data found")
        return

    fig, axes = plt.subplots(2, 2, figsize=(14, 10))
    fig.suptitle("Massachusetts Basin Evolution (N=3 to N=10)", fontsize=16, fontweight="bold")

    n_vals = mass_df["N"].values

    # Panel 1: Basin size
    ax = axes[0, 0]
    ax.semilogy(n_vals, mass_df["basin_size"], "o-", linewidth=3, markersize=10, color="darkred")
    ax.axvline(5, color="blue", linestyle="--", alpha=0.5)
    ax.set_xlabel("N", fontsize=12)
    ax.set_ylabel("Basin Size (nodes)", fontsize=12)
    ax.set_title("Basin Size Evolution", fontsize=13, fontweight="bold")
    ax.grid(True, alpha=0.3)

    # Annotate peak
    peak_idx = mass_df["basin_size"].argmax()
    peak_n = mass_df.iloc[peak_idx]["N"]
    peak_size = mass_df.iloc[peak_idx]["basin_size"]
    ax.annotate(
        f"Peak: {peak_size:,.0f} nodes\n(25% of Wikipedia)",
        xy=(peak_n, peak_size),
        xytext=(peak_n - 1, peak_size * 5),
        arrowprops=dict(arrowstyle="->", color="red", lw=2),
        fontsize=10,
        bbox=dict(boxstyle="round,pad=0.5", facecolor="yellow", alpha=0.8)
    )

    # Panel 2: Mean depth
    ax = axes[0, 1]
    ax.plot(n_vals, mass_df["mean_depth"], "s-", linewidth=3, markersize=10, color="darkgreen")
    ax.axvline(5, color="blue", linestyle="--", alpha=0.5)
    ax.set_xlabel("N", fontsize=12)
    ax.set_ylabel("Mean Depth (steps)", fontsize=12)
    ax.set_title("Mean Convergence Depth", fontsize=13, fontweight="bold")
    ax.grid(True, alpha=0.3)

    # Panel 3: Max depth
    ax = axes[1, 0]
    ax.plot(n_vals, mass_df["max_depth"], "^-", linewidth=3, markersize=10, color="purple")
    ax.axvline(5, color="blue", linestyle="--", alpha=0.5)
    ax.set_xlabel("N", fontsize=12)
    ax.set_ylabel("Max Depth (steps)", fontsize=12)
    ax.set_title("Maximum Convergence Depth", fontsize=13, fontweight="bold")
    ax.grid(True, alpha=0.3)

    # Panel 4: Dominance percentage
    ax = axes[1, 1]
    ax.plot(n_vals, mass_df["dominance_pct"], "d-", linewidth=3, markersize=10, color="orange")
    ax.axvline(5, color="blue", linestyle="--", alpha=0.5)
    ax.set_xlabel("N", fontsize=12)
    ax.set_ylabel("Dominance (%)", fontsize=12)
    ax.set_title("Basin Dominance (% of Total)", fontsize=13, fontweight="bold")
    ax.grid(True, alpha=0.3)

    plt.tight_layout()
    plt.savefig(output_path, dpi=300, bbox_inches="tight")
    print(f"✓ Saved: {output_path}")


def plot_universal_cycles_heatmap(df: pd.DataFrame, output_path: Path) -> None:
    """Plot heatmap of universal cycle sizes across N."""
    # Find cycles that appear in at least 5 N values
    cycle_counts = df.groupby("cycle_name")["N"].nunique()
    universal_cycles = cycle_counts[cycle_counts >= 5].index

    # Filter to universal cycles and extract base names
    df_universal = df[df["cycle_name"].str.contains("|".join([
        "Massachusetts__Gulf_of_Maine",
        "Kingdom_(biology)__Animal",
        "Sea_salt__Seawater",
        "Mountain__Hill",
        "Latvia__Lithuania",
        "Autumn__Summer"
    ]), na=False)]

    # Extract base cycle name
    df_universal["base_cycle"] = df_universal["cycle_name"].str.extract(
        r"(Massachusetts__Gulf_of_Maine|Kingdom_\(biology\)__Animal|Sea_salt__Seawater|Mountain__Hill|Latvia__Lithuania|Autumn__Summer)"
    )[0]

    # Clean duplicates
    df_universal = df_universal.sort_values("basin_size", ascending=False).drop_duplicates(
        subset=["base_cycle", "N"], keep="first"
    )

    # Pivot to matrix
    pivot = df_universal.pivot(index="base_cycle", columns="N", values="basin_size")
    pivot = pivot.fillna(0).astype(int)

    # Create heatmap
    fig, ax = plt.subplots(figsize=(12, 6))

    # Log-scale the values for better visualization
    pivot_log = np.log10(pivot + 1)

    sns.heatmap(
        pivot_log,
        annot=pivot.applymap(lambda x: f"{x:,}" if x > 0 else ""),
        fmt="s",
        cmap="YlOrRd",
        linewidths=0.5,
        ax=ax,
        cbar_kws={"label": "log10(Basin Size + 1)"}
    )

    ax.set_title("Universal Cycle Basin Sizes (N=3 to N=10)", fontsize=14, fontweight="bold")
    ax.set_xlabel("N (Link Position)", fontsize=12)
    ax.set_ylabel("Cycle", fontsize=12)

    plt.tight_layout()
    plt.savefig(output_path, dpi=300, bbox_inches="tight")
    print(f"✓ Saved: {output_path}")


def print_statistics(agg: pd.DataFrame, df: pd.DataFrame) -> None:
    """Print summary statistics."""
    print("\n" + "=" * 80)
    print("PHASE TRANSITION STATISTICS (N=3 to N=10)")
    print("=" * 80)

    print("\nAggregate Basin Mass by N:")
    print(agg.to_string(index=False))

    # Find peak
    peak_idx = agg["total_mass"].argmax()
    peak_n = agg.iloc[peak_idx]["N"]
    peak_mass = agg.iloc[peak_idx]["total_mass"]

    print(f"\n{'Peak Configuration:':<30} N={int(peak_n)}")
    print(f"{'Peak Total Mass:':<30} {peak_mass:,.0f} nodes")
    print(f"{'Peak as % of Wikipedia:':<30} {peak_mass / 17.9e6 * 100:.1f}%")

    # Compute amplification factors
    baseline_n4 = agg[agg["N"] == 4]["total_mass"].values[0]
    peak_amp = peak_mass / baseline_n4
    print(f"\n{'Amplification vs N=4:':<30} {peak_amp:.1f}×")

    # Compute drop-offs
    n8_mass = agg[agg["N"] == 8]["total_mass"].values[0]
    n9_mass = agg[agg["N"] == 9]["total_mass"].values[0]
    n10_mass = agg[agg["N"] == 10]["total_mass"].values[0]

    print(f"{'N=8 mass (vs N=5):':<30} {n8_mass:,.0f} ({peak_mass / n8_mass:.1f}× drop)")
    print(f"{'N=9 mass (vs N=5):':<30} {n9_mass:,.0f} ({peak_mass / n9_mass:.1f}× drop)")
    print(f"{'N=10 mass (vs N=5):':<30} {n10_mass:,.0f} ({peak_mass / n10_mass:.1f}× drop)")

    # Massachusetts specific
    mass_df = df[df["cycle_name"].str.contains("Massachusetts", na=False)]
    mass_df = mass_df.sort_values("basin_size", ascending=False).drop_duplicates(
        subset=["N"], keep="first"
    )

    print("\n" + "=" * 80)
    print("MASSACHUSETTS BASIN EVOLUTION")
    print("=" * 80)

    for _, row in mass_df.sort_values("N").iterrows():
        n = int(row["N"])
        size = int(row["basin_size"])
        depth = row["mean_depth"]
        max_d = int(row["max_depth"])
        dom = row["dominance_pct"]
        print(f"N={n:2d}: {size:>10,} nodes ({dom:5.2f}% dom), "
              f"mean_depth={depth:5.1f}, max_depth={max_d:3d}")

    print("\n" + "=" * 80)


def main():
    parser = argparse.ArgumentParser(
        description="Analyze N=3 to N=10 phase transition"
    )
    args = parser.parse_args()

    # Load data
    print("Loading cycle evolution data...")
    df = load_cycle_evolution()

    # Compute aggregate statistics
    agg = compute_aggregate_statistics(df)

    # Generate plots
    ASSETS_DIR.mkdir(parents=True, exist_ok=True)

    print("\nGenerating visualizations...")
    plot_phase_transition_curve(
        agg,
        ASSETS_DIR / "phase_transition_n3_to_n10_comprehensive.png"
    )

    plot_massachusetts_evolution(
        df,
        ASSETS_DIR / "massachusetts_evolution_n3_to_n10.png"
    )

    plot_universal_cycles_heatmap(
        df,
        ASSETS_DIR / "universal_cycles_heatmap_n3_to_n10.png"
    )

    # Print statistics
    print_statistics(agg, df)

    # Save summary table
    output_path = ANALYSIS_DIR / "phase_transition_statistics_n3_to_n10.tsv"
    agg.to_csv(output_path, sep="\t", index=False)
    print(f"\n✓ Saved statistics: {output_path}")

    print("\n" + "=" * 80)
    print("✓ PHASE TRANSITION ANALYSIS COMPLETE")
    print("=" * 80)


if __name__ == "__main__":
    main()
