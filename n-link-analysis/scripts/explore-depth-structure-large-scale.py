#!/usr/bin/env python3
"""Large-scale exploration of depth mechanics across all cycles and N values.

This script creates comprehensive visualizations to reveal universal structural
patterns in basin mass vs depth relationships.

Visualizations created:
1. Log-log plot: Basin mass vs max depth (all cycles overlaid)
2. Power-law fit panel: Individual cycles with fitted lines
3. Scaling exponent distribution: α values across cycles
4. Multi-dimensional view: Basin mass vs N, colored by depth
5. Depth distributions: How max depth varies with N
6. Entry breadth vs depth correlation
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from scipy import stats
from pathlib import Path
import seaborn as sns

# Set up publication-quality plotting
plt.rcParams['figure.dpi'] = 150
plt.rcParams['font.size'] = 10
plt.rcParams['axes.labelsize'] = 11
plt.rcParams['axes.titlesize'] = 12
plt.rcParams['legend.fontsize'] = 9
sns.set_palette("husl")

# Data directory
ANALYSIS_DIR = Path("data/wikipedia/processed/analysis")
OUTPUT_DIR = Path("data/wikipedia/processed/analysis/depth_exploration")
OUTPUT_DIR.mkdir(exist_ok=True)

print("=" * 80)
print("LARGE-SCALE DEPTH STRUCTURE EXPLORATION")
print("=" * 80)
print()

# Load all individual N-value files to get max_depth
print("Loading data files...")
all_data = []
for n in [3, 4, 5, 6, 7]:
    file_path = ANALYSIS_DIR / f"entry_breadth_n={n}_full_analysis_2025_12_31.tsv"
    df = pd.read_csv(file_path, sep="\t")
    all_data.append(df)

data = pd.concat(all_data, ignore_index=True)
print(f"Loaded {len(data)} data points from {data['cycle_label'].nunique()} cycles")
print(f"N values: {sorted(data['n'].unique())}")
print(f"Cycles: {sorted(data['cycle_label'].unique())}")
print()

# ============================================================================
# VISUALIZATION 1: Master log-log plot (all data)
# ============================================================================

print("Creating master log-log plot...")
fig, ax = plt.subplots(figsize=(12, 8))

cycles = sorted(data['cycle_label'].unique())
colors = sns.color_palette("husl", len(cycles))

for cycle, color in zip(cycles, colors):
    cycle_data = data[data['cycle_label'] == cycle].sort_values('n')

    # Plot with N labels
    ax.loglog(cycle_data['max_depth'], cycle_data['basin_mass'],
              'o-', label=cycle, color=color, markersize=8, alpha=0.7, linewidth=2)

    # Add N labels next to points
    for _, row in cycle_data.iterrows():
        ax.text(row['max_depth'] * 1.15, row['basin_mass'],
                f"N={row['n']}", fontsize=7, alpha=0.6)

# Add reference power-law lines
depth_range = np.array([1, 200])
for alpha in [1.5, 2.0, 2.5, 3.0]:
    # Normalize to pass through approximate middle of data
    baseline = 1000
    ax.loglog(depth_range, baseline * depth_range**alpha,
              '--', color='gray', alpha=0.3, linewidth=1)
    ax.text(depth_range[-1] * 1.1, baseline * depth_range[-1]**alpha,
            f'α={alpha}', fontsize=8, color='gray', alpha=0.5)

ax.set_xlabel('Max Depth (steps)', fontsize=12, fontweight='bold')
ax.set_ylabel('Basin Mass (nodes)', fontsize=12, fontweight='bold')
ax.set_title('Basin Mass vs Max Depth: All Cycles and N Values\n(Log-Log Scale)',
             fontsize=14, fontweight='bold')
ax.legend(loc='upper left', framealpha=0.9, fontsize=8)
ax.grid(True, alpha=0.3, which='both')

plt.tight_layout()
plt.savefig(OUTPUT_DIR / 'master_loglog_all_cycles.png', dpi=300, bbox_inches='tight')
print(f"  → Saved: master_loglog_all_cycles.png")
plt.close()

# ============================================================================
# VISUALIZATION 2: Individual cycle power-law fits
# ============================================================================

print("Fitting power-laws for each cycle...")
fit_results = []

fig, axes = plt.subplots(2, 3, figsize=(15, 10))
axes = axes.flatten()

for idx, cycle in enumerate(cycles):
    cycle_data = data[data['cycle_label'] == cycle].copy()

    # Filter out points with depth < 2 to avoid log(small numbers) issues
    cycle_data = cycle_data[cycle_data['max_depth'] >= 2]

    if len(cycle_data) < 3:
        print(f"  Skipping {cycle}: insufficient data")
        continue

    # Log-log linear regression
    log_depth = np.log10(cycle_data['max_depth'])
    log_mass = np.log10(cycle_data['basin_mass'])

    slope, intercept, r_value, p_value, std_err = stats.linregress(log_depth, log_mass)

    fit_results.append({
        'cycle': cycle,
        'alpha': slope,
        'log_B0': intercept,
        'B0': 10**intercept,
        'r_squared': r_value**2,
        'p_value': p_value,
        'std_err': std_err,
        'n_points': len(cycle_data),
        'depth_range': f"{cycle_data['max_depth'].min()}-{cycle_data['max_depth'].max()}",
        'mass_range': f"{cycle_data['basin_mass'].min()}-{cycle_data['basin_mass'].max()}"
    })

    # Plot
    ax = axes[idx]
    ax.loglog(cycle_data['max_depth'], cycle_data['basin_mass'],
              'o', markersize=10, alpha=0.7, label='Data')

    # Plot fitted line
    depth_fit = np.logspace(np.log10(cycle_data['max_depth'].min()),
                            np.log10(cycle_data['max_depth'].max()), 100)
    mass_fit = 10**(intercept + slope * np.log10(depth_fit))
    ax.loglog(depth_fit, mass_fit, 'r-', linewidth=2,
              label=f'Fit: M ∝ D^{slope:.2f}')

    # Annotate with N values
    for _, row in cycle_data.iterrows():
        ax.text(row['max_depth'] * 1.2, row['basin_mass'],
                f"N={row['n']}", fontsize=8, alpha=0.6)

    ax.set_xlabel('Max Depth')
    ax.set_ylabel('Basin Mass')
    ax.set_title(f"{cycle}\nα={slope:.2f}, R²={r_value**2:.3f}", fontsize=10)
    ax.legend(fontsize=8)
    ax.grid(True, alpha=0.3, which='both')

# Hide unused subplots
for idx in range(len(cycles), len(axes)):
    axes[idx].axis('off')

plt.suptitle('Power-Law Fits by Cycle: Basin_Mass ∝ Depth^α',
             fontsize=14, fontweight='bold', y=1.00)
plt.tight_layout()
plt.savefig(OUTPUT_DIR / 'power_law_fits_per_cycle.png', dpi=300, bbox_inches='tight')
print(f"  → Saved: power_law_fits_per_cycle.png")
plt.close()

# Save fit results
fit_df = pd.DataFrame(fit_results)
fit_df.to_csv(OUTPUT_DIR / 'power_law_fit_parameters.tsv', sep='\t', index=False)
print(f"  → Saved: power_law_fit_parameters.tsv")
print()

# Print summary statistics
print("POWER-LAW FIT SUMMARY")
print("-" * 80)
print(f"Mean α: {fit_df['alpha'].mean():.3f} ± {fit_df['alpha'].std():.3f}")
print(f"Median α: {fit_df['alpha'].median():.3f}")
print(f"Range: [{fit_df['alpha'].min():.3f}, {fit_df['alpha'].max():.3f}]")
print(f"Mean R²: {fit_df['r_squared'].mean():.3f}")
print()
print("Per-cycle results:")
for _, row in fit_df.iterrows():
    print(f"  {row['cycle']:40s} α={row['alpha']:5.2f}  R²={row['r_squared']:.3f}  (n={row['n_points']})")
print()

# ============================================================================
# VISUALIZATION 3: Scaling exponent distribution
# ============================================================================

print("Creating scaling exponent distribution plot...")
fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 5))

# Histogram
ax1.hist(fit_df['alpha'], bins=10, edgecolor='black', alpha=0.7)
ax1.axvline(fit_df['alpha'].mean(), color='red', linestyle='--', linewidth=2,
            label=f'Mean: {fit_df["alpha"].mean():.2f}')
ax1.axvline(fit_df['alpha'].median(), color='blue', linestyle='--', linewidth=2,
            label=f'Median: {fit_df["alpha"].median():.2f}')
ax1.set_xlabel('Power-Law Exponent α', fontweight='bold')
ax1.set_ylabel('Count', fontweight='bold')
ax1.set_title('Distribution of α Across Cycles')
ax1.legend()
ax1.grid(True, alpha=0.3)

# R² vs α
ax2.scatter(fit_df['alpha'], fit_df['r_squared'], s=100, alpha=0.6, edgecolors='black')
for _, row in fit_df.iterrows():
    ax2.text(row['alpha'] + 0.05, row['r_squared'],
             row['cycle'].split(' ↔ ')[0][:10], fontsize=7, alpha=0.7)
ax2.set_xlabel('Power-Law Exponent α', fontweight='bold')
ax2.set_ylabel('R² (Goodness of Fit)', fontweight='bold')
ax2.set_title('Fit Quality vs Exponent')
ax2.grid(True, alpha=0.3)
ax2.axhline(0.8, color='red', linestyle='--', alpha=0.3, label='R²=0.8')
ax2.legend()

plt.tight_layout()
plt.savefig(OUTPUT_DIR / 'scaling_exponent_distribution.png', dpi=300, bbox_inches='tight')
print(f"  → Saved: scaling_exponent_distribution.png")
plt.close()

# ============================================================================
# VISUALIZATION 4: Multi-dimensional view (Mass vs N, colored by depth)
# ============================================================================

print("Creating multi-dimensional structure view...")
fig, axes = plt.subplots(2, 3, figsize=(15, 10))
axes = axes.flatten()

for idx, cycle in enumerate(cycles):
    cycle_data = data[data['cycle_label'] == cycle].sort_values('n')

    ax = axes[idx]

    # Create scatter with color based on depth
    scatter = ax.scatter(cycle_data['n'], cycle_data['basin_mass'],
                         c=cycle_data['max_depth'], s=200,
                         cmap='viridis', edgecolors='black', linewidth=1.5,
                         norm=plt.matplotlib.colors.LogNorm())

    # Connect points to show trajectory
    ax.plot(cycle_data['n'], cycle_data['basin_mass'],
            'k--', alpha=0.3, linewidth=1)

    # Annotate with depth values
    for _, row in cycle_data.iterrows():
        ax.text(row['n'], row['basin_mass'] * 1.3,
                f"d={row['max_depth']}", fontsize=8,
                ha='center', alpha=0.7)

    ax.set_yscale('log')
    ax.set_xlabel('N (Link Rule Index)', fontweight='bold')
    ax.set_ylabel('Basin Mass', fontweight='bold')
    ax.set_title(cycle, fontsize=10)
    ax.set_xticks([3, 4, 5, 6, 7])
    ax.grid(True, alpha=0.3)

    plt.colorbar(scatter, ax=ax, label='Max Depth')

# Hide unused subplots
for idx in range(len(cycles), len(axes)):
    axes[idx].axis('off')

plt.suptitle('Basin Mass vs N: Colored by Max Depth\n(Reveals depth-mass coupling)',
             fontsize=14, fontweight='bold', y=1.00)
plt.tight_layout()
plt.savefig(OUTPUT_DIR / 'multidimensional_structure.png', dpi=300, bbox_inches='tight')
print(f"  → Saved: multidimensional_structure.png")
plt.close()

# ============================================================================
# VISUALIZATION 5: Depth vs N across all cycles
# ============================================================================

print("Creating depth distribution analysis...")
fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 6))

# Plot 1: Depth vs N (all cycles)
for cycle in cycles:
    cycle_data = data[data['cycle_label'] == cycle].sort_values('n')
    ax1.plot(cycle_data['n'], cycle_data['max_depth'],
             'o-', label=cycle, markersize=8, linewidth=2, alpha=0.7)

ax1.set_xlabel('N (Link Rule Index)', fontweight='bold')
ax1.set_ylabel('Max Depth (steps)', fontweight='bold')
ax1.set_title('Max Depth vs N: All Cycles')
ax1.legend(fontsize=8)
ax1.set_xticks([3, 4, 5, 6, 7])
ax1.grid(True, alpha=0.3)
ax1.axvline(5, color='red', linestyle='--', alpha=0.3, label='N=5 (peak)')

# Plot 2: Depth distribution by N (box plot)
depth_by_n = [data[data['n'] == n]['max_depth'].values for n in [3, 4, 5, 6, 7]]
bp = ax2.boxplot(depth_by_n, positions=[3, 4, 5, 6, 7], widths=0.6,
                 patch_artist=True, showmeans=True)

# Color boxes
colors_box = ['lightblue', 'lightgreen', 'coral', 'lightyellow', 'plum']
for patch, color in zip(bp['boxes'], colors_box):
    patch.set_facecolor(color)

ax2.set_xlabel('N (Link Rule Index)', fontweight='bold')
ax2.set_ylabel('Max Depth (steps)', fontweight='bold')
ax2.set_title('Max Depth Distribution by N')
ax2.set_xticks([3, 4, 5, 6, 7])
ax2.grid(True, alpha=0.3, axis='y')

# Add statistics
for n, depths in zip([3, 4, 5, 6, 7], depth_by_n):
    ax2.text(n, max(depths) * 1.1,
             f"μ={np.mean(depths):.0f}",
             ha='center', fontsize=8, fontweight='bold')

plt.tight_layout()
plt.savefig(OUTPUT_DIR / 'depth_vs_n_analysis.png', dpi=300, bbox_inches='tight')
print(f"  → Saved: depth_vs_n_analysis.png")
plt.close()

# ============================================================================
# VISUALIZATION 6: Entry breadth vs depth correlation
# ============================================================================

print("Creating entry breadth vs depth correlation...")
fig, axes = plt.subplots(1, 3, figsize=(15, 5))

# Plot 1: Entry breadth vs max depth (log-log)
ax = axes[0]
for cycle in cycles:
    cycle_data = data[data['cycle_label'] == cycle]
    ax.loglog(cycle_data['entry_breadth'], cycle_data['max_depth'],
              'o', label=cycle, markersize=8, alpha=0.7)

ax.set_xlabel('Entry Breadth', fontweight='bold')
ax.set_ylabel('Max Depth', fontweight='bold')
ax.set_title('Entry Breadth vs Max Depth\n(Negative correlation?)')
ax.legend(fontsize=7, loc='best')
ax.grid(True, alpha=0.3, which='both')

# Plot 2: Entry breadth vs N
ax = axes[1]
for cycle in cycles:
    cycle_data = data[data['cycle_label'] == cycle].sort_values('n')
    ax.plot(cycle_data['n'], cycle_data['entry_breadth'],
            'o-', label=cycle, markersize=8, linewidth=2, alpha=0.7)

ax.set_xlabel('N (Link Rule Index)', fontweight='bold')
ax.set_ylabel('Entry Breadth', fontweight='bold')
ax.set_title('Entry Breadth Decreases with N')
ax.legend(fontsize=7, loc='best')
ax.set_xticks([3, 4, 5, 6, 7])
ax.grid(True, alpha=0.3)

# Plot 3: Product (Entry × Depth^2) vs Basin Mass
ax = axes[2]
data['predicted_mass'] = data['entry_breadth'] * data['max_depth']**2

for cycle in cycles:
    cycle_data = data[data['cycle_label'] == cycle]
    ax.loglog(cycle_data['predicted_mass'], cycle_data['basin_mass'],
              'o', label=cycle, markersize=8, alpha=0.7)

# Add perfect prediction line
pred_range = np.array([data['predicted_mass'].min(), data['predicted_mass'].max()])
ax.loglog(pred_range, pred_range, 'k--', linewidth=2, label='Perfect prediction')

ax.set_xlabel('Entry_Breadth × Depth²', fontweight='bold')
ax.set_ylabel('Basin Mass (actual)', fontweight='bold')
ax.set_title('Testing: Mass = Entry × Depth²')
ax.legend(fontsize=7, loc='best')
ax.grid(True, alpha=0.3, which='both')

plt.tight_layout()
plt.savefig(OUTPUT_DIR / 'entry_depth_correlation.png', dpi=300, bbox_inches='tight')
print(f"  → Saved: entry_depth_correlation.png")
plt.close()

# ============================================================================
# SUMMARY STATISTICS
# ============================================================================

print()
print("=" * 80)
print("SUMMARY STATISTICS")
print("=" * 80)
print()

# Depth statistics by N
print("DEPTH STATISTICS BY N")
print("-" * 80)
for n in [3, 4, 5, 6, 7]:
    n_data = data[data['n'] == n]['max_depth']
    print(f"N={n}: mean={n_data.mean():6.1f}  median={n_data.median():5.0f}  "
          f"std={n_data.std():6.1f}  range=[{n_data.min()}-{n_data.max()}]")
print()

# Basin mass statistics by N
print("BASIN MASS STATISTICS BY N")
print("-" * 80)
for n in [3, 4, 5, 6, 7]:
    n_data = data[data['n'] == n]['basin_mass']
    print(f"N={n}: mean={n_data.mean():10.0f}  median={n_data.median():8.0f}  "
          f"range=[{n_data.min():.0f}-{n_data.max():.0f}]")
print()

# Correlation analysis
print("CORRELATION ANALYSIS")
print("-" * 80)
print(f"Basin Mass vs Max Depth:    r = {data['basin_mass'].corr(data['max_depth']):.3f}")
print(f"Basin Mass vs Entry Breadth: r = {data['basin_mass'].corr(data['entry_breadth']):.3f}")
print(f"Max Depth vs Entry Breadth:  r = {data['max_depth'].corr(data['entry_breadth']):.3f}")
print()

# Test prediction formula: Mass = Entry × Depth^α
for alpha in [1.5, 2.0, 2.5]:
    data[f'pred_alpha_{alpha}'] = data['entry_breadth'] * data['max_depth']**alpha
    corr = np.corrcoef(np.log10(data['basin_mass']),
                       np.log10(data[f'pred_alpha_{alpha}']))[0, 1]
    print(f"Log correlation (Mass vs Entry×Depth^{alpha}): r = {corr:.3f}")
print()

print("=" * 80)
print(f"All outputs saved to: {OUTPUT_DIR}/")
print("=" * 80)
