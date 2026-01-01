#!/usr/bin/env python3
"""
Analyze depth distributions from path characteristics data.

Computes comprehensive depth statistics (mean, median, percentiles, variance)
and tests which depth metric best predicts basin mass.

This extends the max-depth-only analysis by examining full distributions.
"""

import argparse
import pandas as pd
import numpy as np
from pathlib import Path
from typing import Dict, List, Tuple
import matplotlib.pyplot as plt
from scipy import stats
import seaborn as sns

# Configure visualization
sns.set_style("whitegrid")
plt.rcParams['figure.figsize'] = (12, 8)
plt.rcParams['font.size'] = 10


def load_depth_distribution(n: int, data_dir: Path) -> pd.DataFrame:
    """
    Load depth distribution from path characteristics file.

    Args:
        n: N-link rule value
        data_dir: Directory containing analysis files

    Returns:
        DataFrame with depth, convergence_count, halt_count columns
    """
    filepath = data_dir / f"path_characteristics_n={n}_mechanism_depth_distributions.tsv"

    if not filepath.exists():
        raise FileNotFoundError(f"Depth distribution file not found: {filepath}")

    df = pd.read_csv(filepath, sep='\t')
    return df


def compute_depth_statistics(depth_dist: pd.DataFrame) -> Dict[str, float]:
    """
    Compute comprehensive statistics from depth distribution.

    Args:
        depth_dist: DataFrame with depth, convergence_count, halt_count

    Returns:
        Dictionary of depth statistics
    """
    # Expand distribution: create one row per observation
    depths = []
    for _, row in depth_dist.iterrows():
        depth = row['depth']
        count = row['convergence_count']  # Only count convergence, not halts
        depths.extend([depth] * int(count))

    depths = np.array(depths)

    if len(depths) == 0:
        return {
            'mean': 0,
            'median': 0,
            'p10': 0,
            'p25': 0,
            'p50': 0,
            'p75': 0,
            'p90': 0,
            'p95': 0,
            'p99': 0,
            'max': 0,
            'std': 0,
            'variance': 0,
            'skewness': 0,
            'kurtosis': 0,
            'count': 0
        }

    return {
        'mean': float(np.mean(depths)),
        'median': float(np.median(depths)),
        'p10': float(np.percentile(depths, 10)),
        'p25': float(np.percentile(depths, 25)),
        'p50': float(np.percentile(depths, 50)),
        'p75': float(np.percentile(depths, 75)),
        'p90': float(np.percentile(depths, 90)),
        'p95': float(np.percentile(depths, 95)),
        'p99': float(np.percentile(depths, 99)),
        'max': float(np.max(depths)),
        'std': float(np.std(depths)),
        'variance': float(np.var(depths)),
        'skewness': float(stats.skew(depths)),
        'kurtosis': float(stats.kurtosis(depths)),
        'count': len(depths)
    }


def load_basin_data(n: int, data_dir: Path) -> pd.DataFrame:
    """
    Load basin mass and entry breadth data for correlation analysis.

    Args:
        n: N-link rule value
        data_dir: Directory containing analysis files

    Returns:
        DataFrame with cycle_label, basin_mass, entry_breadth, max_depth
    """
    filepath = data_dir / f"entry_breadth_n={n}_full_analysis_2025_12_31.tsv"

    if not filepath.exists():
        raise FileNotFoundError(f"Basin data file not found: {filepath}")

    df = pd.read_csv(filepath, sep='\t')
    return df[['cycle_label', 'basin_mass', 'entry_breadth', 'max_depth']]


def analyze_across_n_values(n_values: List[int], data_dir: Path, output_dir: Path) -> pd.DataFrame:
    """
    Analyze depth distributions across N values.

    Args:
        n_values: List of N values to analyze
        data_dir: Directory containing analysis files
        output_dir: Directory for output files

    Returns:
        DataFrame with depth statistics per N
    """
    results = []

    for n in n_values:
        print(f"\nAnalyzing N={n}...")

        try:
            depth_dist = load_depth_distribution(n, data_dir)
            stats_dict = compute_depth_statistics(depth_dist)
            stats_dict['n'] = n
            results.append(stats_dict)

            print(f"  Mean depth: {stats_dict['mean']:.2f}")
            print(f"  Median depth: {stats_dict['median']:.2f}")
            print(f"  90th percentile: {stats_dict['p90']:.2f}")
            print(f"  Max depth: {stats_dict['max']:.2f}")
            print(f"  Std dev: {stats_dict['std']:.2f}")
            print(f"  Skewness: {stats_dict['skewness']:.2f}")

        except FileNotFoundError as e:
            print(f"  Skipping N={n}: {e}")
            continue

    # Convert to DataFrame
    df = pd.DataFrame(results)

    # Reorder columns
    cols = ['n', 'mean', 'median', 'p10', 'p25', 'p50', 'p75', 'p90', 'p95', 'p99',
            'max', 'std', 'variance', 'skewness', 'kurtosis', 'count']
    df = df[cols]

    # Save results
    output_file = output_dir / "depth_statistics_by_n.tsv"
    df.to_csv(output_file, sep='\t', index=False, float_format='%.3f')
    print(f"\n✓ Saved depth statistics to {output_file}")

    return df


def test_depth_predictors(n_values: List[int], data_dir: Path, output_dir: Path) -> pd.DataFrame:
    """
    Test which depth metric best predicts basin mass.

    Compares mean, median, p90, p95, and max depth as predictors.

    Args:
        n_values: List of N values to analyze
        data_dir: Directory containing analysis files
        output_dir: Directory for output files

    Returns:
        DataFrame with correlation results
    """
    all_data = []

    for n in n_values:
        try:
            # Load depth distribution
            depth_dist = load_depth_distribution(n, data_dir)
            depth_stats = compute_depth_statistics(depth_dist)

            # Load basin data
            basin_data = load_basin_data(n, data_dir)

            # Note: We only have aggregate depth stats, not per-cycle
            # So we'll use the summary statistics for this N value
            for _, row in basin_data.iterrows():
                all_data.append({
                    'n': n,
                    'cycle_label': row['cycle_label'],
                    'basin_mass': row['basin_mass'],
                    'entry_breadth': row['entry_breadth'],
                    'max_depth': row['max_depth'],
                    'mean_depth_aggregate': depth_stats['mean'],
                    'median_depth_aggregate': depth_stats['median'],
                    'p90_depth_aggregate': depth_stats['p90'],
                    'p95_depth_aggregate': depth_stats['p95']
                })
        except FileNotFoundError:
            continue

    df = pd.DataFrame(all_data)

    # Compute correlations on log scale (since we expect power-law)
    correlations = {}

    # Test max_depth (per-cycle metric we already have)
    log_basin_mass = np.log10(df['basin_mass'])
    log_max_depth = np.log10(df['max_depth'] + 1)  # +1 to avoid log(0)

    r_max, p_max = stats.pearsonr(log_max_depth, log_basin_mass)
    correlations['max_depth'] = {'r': r_max, 'p_value': p_max, 'r_squared': r_max**2}

    print(f"\nCorrelation Analysis (log-log scale):")
    print(f"  Max depth: r={r_max:.4f}, R²={r_max**2:.4f}, p={p_max:.4e}")

    # Note: Aggregate depth metrics are constant per N, so correlation within N is zero
    # We need per-cycle depth distributions to test mean/median/p90 properly

    # Save correlation results
    corr_df = pd.DataFrame([
        {'depth_metric': 'max_depth', 'correlation_r': r_max,
         'r_squared': r_max**2, 'p_value': p_max}
    ])

    output_file = output_dir / "depth_predictor_correlations.tsv"
    corr_df.to_csv(output_file, sep='\t', index=False, float_format='%.6f')
    print(f"\n✓ Saved correlation results to {output_file}")

    return df


def visualize_depth_statistics(stats_df: pd.DataFrame, output_dir: Path):
    """
    Create visualizations of depth statistics across N values.

    Args:
        stats_df: DataFrame with depth statistics by N
        output_dir: Directory for output visualizations
    """
    fig, axes = plt.subplots(2, 2, figsize=(14, 10))

    # Plot 1: Depth metrics across N
    ax = axes[0, 0]
    ax.plot(stats_df['n'], stats_df['mean'], 'o-', label='Mean', linewidth=2, markersize=8)
    ax.plot(stats_df['n'], stats_df['median'], 's-', label='Median', linewidth=2, markersize=8)
    ax.plot(stats_df['n'], stats_df['p90'], '^-', label='90th percentile', linewidth=2, markersize=8)
    ax.plot(stats_df['n'], stats_df['max'], 'd-', label='Max', linewidth=2, markersize=8)
    ax.set_xlabel('N (link position)', fontsize=12)
    ax.set_ylabel('Depth (steps)', fontsize=12)
    ax.set_title('Depth Metrics vs N', fontsize=14, fontweight='bold')
    ax.legend()
    ax.grid(True, alpha=0.3)

    # Plot 2: Depth spread (std dev, variance)
    ax = axes[0, 1]
    ax.plot(stats_df['n'], stats_df['std'], 'o-', color='purple', linewidth=2, markersize=8)
    ax.set_xlabel('N (link position)', fontsize=12)
    ax.set_ylabel('Standard Deviation', fontsize=12)
    ax.set_title('Depth Variability vs N', fontsize=14, fontweight='bold')
    ax.grid(True, alpha=0.3)

    # Plot 3: Skewness
    ax = axes[1, 0]
    ax.plot(stats_df['n'], stats_df['skewness'], 'o-', color='red', linewidth=2, markersize=8)
    ax.axhline(y=0, color='black', linestyle='--', alpha=0.3)
    ax.set_xlabel('N (link position)', fontsize=12)
    ax.set_ylabel('Skewness', fontsize=12)
    ax.set_title('Distribution Skewness vs N', fontsize=14, fontweight='bold')
    ax.grid(True, alpha=0.3)
    ax.text(0.02, 0.98, 'Positive = right-skewed\nNegative = left-skewed',
            transform=ax.transAxes, verticalalignment='top',
            bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.5))

    # Plot 4: Percentile comparison
    ax = axes[1, 1]
    ax.plot(stats_df['n'], stats_df['p10'], 'o-', label='10th', linewidth=2, markersize=6)
    ax.plot(stats_df['n'], stats_df['p25'], 's-', label='25th', linewidth=2, markersize=6)
    ax.plot(stats_df['n'], stats_df['p50'], '^-', label='50th', linewidth=2, markersize=6)
    ax.plot(stats_df['n'], stats_df['p75'], 'd-', label='75th', linewidth=2, markersize=6)
    ax.plot(stats_df['n'], stats_df['p90'], 'v-', label='90th', linewidth=2, markersize=6)
    ax.set_xlabel('N (link position)', fontsize=12)
    ax.set_ylabel('Depth (steps)', fontsize=12)
    ax.set_title('Depth Percentiles vs N', fontsize=14, fontweight='bold')
    ax.legend(loc='best')
    ax.grid(True, alpha=0.3)

    plt.tight_layout()

    output_file = output_dir / "depth_statistics_by_n.png"
    plt.savefig(output_file, dpi=300, bbox_inches='tight')
    print(f"✓ Saved visualization to {output_file}")
    plt.close()


def visualize_depth_distributions(n_values: List[int], data_dir: Path, output_dir: Path):
    """
    Create histogram visualization of depth distributions across N values.

    Args:
        n_values: List of N values to visualize
        data_dir: Directory containing analysis files
        output_dir: Directory for output visualizations
    """
    fig, axes = plt.subplots(len(n_values), 1, figsize=(14, 4 * len(n_values)))

    if len(n_values) == 1:
        axes = [axes]

    for idx, n in enumerate(n_values):
        try:
            depth_dist = load_depth_distribution(n, data_dir)

            ax = axes[idx]

            # Plot histogram
            ax.bar(depth_dist['depth'], depth_dist['convergence_count'],
                   color='steelblue', alpha=0.7, edgecolor='black', linewidth=0.5)

            # Compute statistics
            stats_dict = compute_depth_statistics(depth_dist)

            # Add vertical lines for key statistics
            ax.axvline(stats_dict['mean'], color='red', linestyle='--',
                      linewidth=2, label=f"Mean: {stats_dict['mean']:.1f}")
            ax.axvline(stats_dict['median'], color='green', linestyle='--',
                      linewidth=2, label=f"Median: {stats_dict['median']:.1f}")
            ax.axvline(stats_dict['p90'], color='orange', linestyle='--',
                      linewidth=2, label=f"90th: {stats_dict['p90']:.1f}")

            ax.set_xlabel('Depth (steps to convergence)', fontsize=12)
            ax.set_ylabel('Number of paths', fontsize=12)
            ax.set_title(f'N={n} Depth Distribution (n={stats_dict["count"]} paths)',
                        fontsize=14, fontweight='bold')
            ax.legend(loc='upper right')
            ax.grid(True, alpha=0.3, axis='y')

            # Add statistics text box
            stats_text = (
                f"Std Dev: {stats_dict['std']:.2f}\n"
                f"Skewness: {stats_dict['skewness']:.2f}\n"
                f"Max: {stats_dict['max']:.0f}"
            )
            ax.text(0.98, 0.98, stats_text, transform=ax.transAxes,
                   verticalalignment='top', horizontalalignment='right',
                   bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.8),
                   fontsize=10)

        except FileNotFoundError:
            continue

    plt.tight_layout()

    output_file = output_dir / "depth_distributions_histograms.png"
    plt.savefig(output_file, dpi=300, bbox_inches='tight')
    print(f"✓ Saved depth distribution histograms to {output_file}")
    plt.close()


def main():
    parser = argparse.ArgumentParser(
        description="Analyze depth distributions from path characteristics data",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Analyze default N values (3-7)
  python analyze-depth-distributions.py

  # Analyze specific N values
  python analyze-depth-distributions.py --n-values 3 4 5 6 7 8

  # Custom data directory
  python analyze-depth-distributions.py --data-dir custom/path
        """
    )

    parser.add_argument(
        '--n-values',
        type=int,
        nargs='+',
        default=[3, 4, 5, 6, 7],
        help='N values to analyze (default: 3 4 5 6 7)'
    )

    parser.add_argument(
        '--data-dir',
        type=Path,
        default=Path('data/wikipedia/processed/analysis'),
        help='Directory containing analysis files'
    )

    parser.add_argument(
        '--output-dir',
        type=Path,
        default=Path('data/wikipedia/processed/analysis/depth_distributions'),
        help='Output directory for results'
    )

    args = parser.parse_args()

    # Create output directory
    args.output_dir.mkdir(parents=True, exist_ok=True)

    print("=" * 80)
    print("DEPTH DISTRIBUTION ANALYSIS")
    print("=" * 80)
    print(f"\nN values: {args.n_values}")
    print(f"Data directory: {args.data_dir}")
    print(f"Output directory: {args.output_dir}")

    # Analyze depth statistics across N values
    print("\n" + "=" * 80)
    print("COMPUTING DEPTH STATISTICS")
    print("=" * 80)
    stats_df = analyze_across_n_values(args.n_values, args.data_dir, args.output_dir)

    # Create visualizations
    print("\n" + "=" * 80)
    print("CREATING VISUALIZATIONS")
    print("=" * 80)
    visualize_depth_statistics(stats_df, args.output_dir)
    visualize_depth_distributions(args.n_values, args.data_dir, args.output_dir)

    # Test depth predictors
    print("\n" + "=" * 80)
    print("TESTING DEPTH PREDICTORS")
    print("=" * 80)
    test_data = test_depth_predictors(args.n_values, args.data_dir, args.output_dir)

    print("\n" + "=" * 80)
    print("ANALYSIS COMPLETE")
    print("=" * 80)
    print(f"\nGenerated {len(list(args.output_dir.glob('*')))} output files in {args.output_dir}")
    print("\nKey Findings Summary:")
    print("-" * 80)

    # Print summary table
    print(f"\n{'N':<5} {'Mean':<10} {'Median':<10} {'90th':<10} {'Max':<10} {'Std':<10}")
    print("-" * 60)
    for _, row in stats_df.iterrows():
        print(f"{int(row['n']):<5} {row['mean']:<10.2f} {row['median']:<10.2f} "
              f"{row['p90']:<10.2f} {row['max']:<10.2f} {row['std']:<10.2f}")

    # Key insights
    n5_row = stats_df[stats_df['n'] == 5].iloc[0] if 5 in stats_df['n'].values else None
    n4_row = stats_df[stats_df['n'] == 4].iloc[0] if 4 in stats_df['n'].values else None

    if n5_row is not None and n4_row is not None:
        mean_increase = n5_row['mean'] / n4_row['mean']
        max_increase = n5_row['max'] / n4_row['max']
        print(f"\n✓ N=5 mean depth: {mean_increase:.2f}× deeper than N=4")
        print(f"✓ N=5 max depth: {max_increase:.2f}× deeper than N=4")
        print(f"✓ N=5 skewness: {n5_row['skewness']:.2f} (positive = right-skewed distribution)")


if __name__ == "__main__":
    main()
