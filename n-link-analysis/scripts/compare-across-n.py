#!/usr/bin/env python3
"""Compare basin structure across different N-link rules.

Analyzes how basin sizes, trunkiness, and dominance patterns vary with N.

Usage:
    python n-link-analysis/scripts/compare-across-n.py --n-values 3 5 7

Output:
    Cross-N comparison tables and charts
"""

from __future__ import annotations

import argparse
from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd


REPO_ROOT = Path(__file__).resolve().parents[2]
ANALYSIS_DIR = REPO_ROOT / "data" / "wikipedia" / "processed" / "analysis"
REPORT_DIR = REPO_ROOT / "n-link-analysis" / "report"
ASSETS_DIR = REPORT_DIR / "assets"


def load_dashboards(n_values: list[int], tag: str) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Load trunkiness and collapse dashboards for multiple N values."""
    trunk_dfs = []
    collapse_dfs = []

    for n in n_values:
        trunk_path = ANALYSIS_DIR / f"branch_trunkiness_dashboard_n={n}_{tag}.tsv"
        if trunk_path.exists():
            df = pd.read_csv(trunk_path, sep="\t")
            df["n"] = n
            trunk_dfs.append(df)

        collapse_path = ANALYSIS_DIR / f"dominance_collapse_dashboard_n={n}_{tag}_seed=dominant_enters_cycle_title_thr=0.5.tsv"
        if collapse_path.exists():
            df = pd.read_csv(collapse_path, sep="\t")
            df["n"] = n
            collapse_dfs.append(df)

    trunk_all = pd.concat(trunk_dfs, ignore_index=True) if trunk_dfs else None
    collapse_all = pd.concat(collapse_dfs, ignore_index=True) if collapse_dfs else None

    return trunk_all, collapse_all


def compare_basin_sizes(trunk_all: pd.DataFrame) -> None:
    """Compare basin size distributions across N values."""
    print("=" * 80)
    print("BASIN SIZE COMPARISON ACROSS N")
    print("=" * 80)

    for n in sorted(trunk_all["n"].unique()):
        df_n = trunk_all[trunk_all["n"] == n]
        print(f"\nN={n}:")
        print(f"  Total basins analyzed: {len(df_n)}")
        print(f"  Total nodes: {df_n['total_basin_nodes'].sum():,}")
        print(f"  Largest basin: {df_n['total_basin_nodes'].max():,}")
        print(f"  Median basin: {df_n['total_basin_nodes'].median():,.0f}")
        print(f"  Size range: {df_n['total_basin_nodes'].max() / df_n['total_basin_nodes'].min():.1f}x")

    # Chart: Basin size distributions
    fig, ax = plt.subplots(figsize=(12, 6))
    for n in sorted(trunk_all["n"].unique()):
        df_n = trunk_all[trunk_all["n"] == n].sort_values("total_basin_nodes", ascending=False)
        ax.plot(range(len(df_n)), df_n["total_basin_nodes"], marker="o", label=f"N={n}")

    ax.set_xlabel("Basin Rank")
    ax.set_ylabel("Basin Size (nodes)")
    ax.set_yscale("log")
    ax.legend()
    ax.grid(True, alpha=0.3)
    ax.set_title("Basin Size Distribution Across N Values")

    chart_path = ASSETS_DIR / "cross_n_basin_sizes.png"
    plt.savefig(chart_path, dpi=150, bbox_inches="tight")
    plt.close()
    print(f"\n✓ Saved chart: {chart_path}")


def compare_trunkiness(trunk_all: pd.DataFrame) -> None:
    """Compare trunkiness metrics across N values."""
    print("\n" + "=" * 80)
    print("TRUNKINESS COMPARISON ACROSS N")
    print("=" * 80)

    for n in sorted(trunk_all["n"].unique()):
        df_n = trunk_all[trunk_all["n"] == n]
        high_trunk = (df_n["top1_share_total"] > 0.95).sum()
        print(f"\nN={n}:")
        print(f"  High-trunk basins (>95%): {high_trunk}/{len(df_n)} ({100*high_trunk/len(df_n):.0f}%)")
        print(f"  Mean top1_share: {df_n['top1_share_total'].mean():.2%}")
        print(f"  Median effective_branches: {df_n['effective_branches'].median():.2f}")

    # Chart: Trunkiness distribution
    fig, axes = plt.subplots(1, 2, figsize=(14, 6))

    # Box plot: top1_share by N
    n_values = sorted(trunk_all["n"].unique())
    data_by_n = [trunk_all[trunk_all["n"] == n]["top1_share_total"].values for n in n_values]
    axes[0].boxplot(data_by_n, labels=[f"N={n}" for n in n_values])
    axes[0].set_xlabel("N (link rule)")
    axes[0].set_ylabel("Top-1 Share")
    axes[0].set_title("Trunk Concentration Distribution")
    axes[0].axhline(0.95, color="red", linestyle="--", alpha=0.5, label="95% threshold")
    axes[0].legend()
    axes[0].grid(True, alpha=0.3)

    # Box plot: effective_branches by N
    data_by_n = [trunk_all[trunk_all["n"] == n]["effective_branches"].values for n in n_values]
    axes[1].boxplot(data_by_n, labels=[f"N={n}" for n in n_values])
    axes[1].set_xlabel("N (link rule)")
    axes[1].set_ylabel("Effective Branches")
    axes[1].set_title("Branch Diversity Distribution")
    axes[1].grid(True, alpha=0.3)

    chart_path = ASSETS_DIR / "cross_n_trunkiness.png"
    plt.savefig(chart_path, dpi=150, bbox_inches="tight")
    plt.close()
    print(f"\n✓ Saved chart: {chart_path}")


def compare_collapse(collapse_all: pd.DataFrame) -> None:
    """Compare dominance collapse patterns across N values."""
    print("\n" + "=" * 80)
    print("DOMINANCE COLLAPSE COMPARISON ACROSS N")
    print("=" * 80)

    for n in sorted(collapse_all["n"].unique()):
        df_n = collapse_all[collapse_all["n"] == n]
        median_hop = df_n[df_n["first_below_threshold_hop"].notna()]["first_below_threshold_hop"].median()
        stable = (df_n["stop_reason"] == "max_hops").sum()
        print(f"\nN={n}:")
        print(f"  Stable basins (no collapse): {stable}/{len(df_n)}")
        print(f"  Median collapse hop: {median_hop:.0f}")
        print(f"  Mean min_share: {df_n['min_share'].mean():.2%}")

    # Chart: Collapse timing
    fig, ax = plt.subplots(figsize=(10, 6))
    df_plot = collapse_all[collapse_all["first_below_threshold_hop"].notna()]
    n_values = sorted(df_plot["n"].unique())
    data_by_n = [df_plot[df_plot["n"] == n]["first_below_threshold_hop"].values for n in n_values]
    ax.boxplot(data_by_n, labels=[f"N={n}" for n in n_values])
    ax.set_xlabel("N (link rule)")
    ax.set_ylabel("Hops to Collapse (< 50% share)")
    ax.set_title("Dominance Stability Across N Values")
    ax.grid(True, alpha=0.3)

    chart_path = ASSETS_DIR / "cross_n_collapse.png"
    plt.savefig(chart_path, dpi=150, bbox_inches="tight")
    plt.close()
    print(f"\n✓ Saved chart: {chart_path}")


def identify_universal_patterns(trunk_all: pd.DataFrame) -> None:
    """Identify cycles that appear across multiple N values."""
    print("\n" + "=" * 80)
    print("UNIVERSAL BASIN PATTERNS")
    print("=" * 80)

    # Extract base cycle name (remove tag)
    trunk_all["cycle_base"] = trunk_all["cycle_key"].str.replace(r"_reproduction_\d{4}-\d{2}-\d{2}", "", regex=True)

    # Find cycles present in multiple N values
    cycle_counts = trunk_all.groupby("cycle_base")["n"].nunique()
    multi_n_cycles = cycle_counts[cycle_counts > 1].sort_values(ascending=False)

    if len(multi_n_cycles) > 0:
        print(f"\nCycles observed across multiple N values:")
        for cycle, count in multi_n_cycles.items():
            print(f"\n  {cycle} (present in {count} N values):")
            cycle_data = trunk_all[trunk_all["cycle_base"] == cycle][["n", "total_basin_nodes", "top1_share_total"]]
            for _, row in cycle_data.iterrows():
                print(f"    N={int(row['n'])}: {row['total_basin_nodes']:,} nodes, {row['top1_share_total']:.1%} trunk")
    else:
        print("\nNo cycles observed across multiple N values (different basins sampled per N)")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--n-values", nargs="+", type=int, default=[3, 5, 7], help="N values to compare")
    parser.add_argument("--tag", type=str, default="reproduction_2025-12-31", help="Tag for input files")
    args = parser.parse_args()

    print("=" * 80)
    print(f"CROSS-N ANALYSIS: Comparing N={', '.join(map(str, args.n_values))}")
    print("=" * 80)

    # Load data
    trunk_all, collapse_all = load_dashboards(args.n_values, args.tag)

    if trunk_all is None or len(trunk_all) == 0:
        print("\n✗ No data found. Run reproduce-main-findings.py for each N first.")
        return 1

    print(f"\nLoaded data for N values: {sorted(trunk_all['n'].unique().tolist())}")

    # Run comparisons
    compare_basin_sizes(trunk_all)
    compare_trunkiness(trunk_all)

    if collapse_all is not None and len(collapse_all) > 0:
        compare_collapse(collapse_all)

    identify_universal_patterns(trunk_all)

    print("\n" + "=" * 80)
    print("✓ CROSS-N ANALYSIS COMPLETE")
    print("=" * 80)
    print(f"\nCharts saved to: {ASSETS_DIR}")
    print("  - cross_n_basin_sizes.png")
    print("  - cross_n_trunkiness.png")
    print("  - cross_n_collapse.png")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
