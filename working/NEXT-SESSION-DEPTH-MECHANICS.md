# Next Session: Deep Dive into Depth Mechanics

**Date**: 2025-12-31
**For**: Next session continuation
**Focus**: Understanding basin depth mechanics and power-law scaling

---

## Session Goal

**Investigate the depth-based basin mass formula**:
```
Basin_Mass ≈ Entry_Breadth × Depth^α × Path_Survival
```

**Key Questions**:
1. What is the exact exponent α? (Hypothesis: α ≈ 2.0-2.5)
2. Does depth^α hold universally across all cycles?
3. Can we predict basin mass from depth distributions?
4. What graph properties determine maximum depth?

---

## What We Know So Far

### Recent Discovery (This Session)

**Entry breadth hypothesis REFUTED** → Depth dominates!

**Evidence**:
- Entry breadth DECREASES with N (871 → 307)
- Basin mass PEAKS at N=5 (304k average)
- Max depth PEAKS at N=5 (mean ~74 steps vs ~13 at N=4)

**Massachusetts case**:
```
N=4 → N=5:
  Entry breadth: 1,557 → 1,255 (0.81×, DOWN)
  Basin mass: 10,705 → 1,009,471 (94×, UP)
  Max depth: 13 → 168 (13×, UP)

Formula: 0.81 × 13² ≈ 137× predicted vs 94× observed ✓
```

### Data Already Available

**From this session**:
- ✓ Entry breadth for all cycles at N∈{3,4,5,6,7}
- ✓ Basin mass for all cycles
- ✓ Max depth per basin (from entry breadth analysis)

**From previous sessions**:
- ✓ Path characteristics (5,000 samples per N)
- ✓ Convergence depth distributions
- ✓ Path length distributions
- ✓ Cycle evolution tracking

**Location**:
```
data/wikipedia/processed/analysis/
├── entry_breadth_n={3,4,5,6,7}_full_analysis_2025_12_31.tsv
├── path_characteristics_n={3,4,5,6,7}_*.tsv
├── cycle_evolution_summary.tsv
└── [other analysis files]
```

---

## Recommended Investigation Path

### **Phase 1: Fit the Power Law** (1-2 hours)

#### Script to Create: `analyze-depth-scaling.py`

**Purpose**: Fit Basin_Mass ∝ Depth^α and extract exponent

**Algorithm**:
1. Load entry breadth results (already have basin_mass and max_depth)
2. Load path characteristics (get mean depth, depth distributions)
3. For each cycle:
   - Plot log(Basin_Mass) vs log(Max_Depth)
   - Fit linear regression: log(M) = α·log(D) + log(B₀)
   - Extract α (slope)
4. Aggregate across cycles
5. Test residuals and goodness-of-fit

**Expected Outputs**:
- `depth_scaling_parameters.tsv` (α, B₀ per cycle)
- `depth_scaling_fit_quality.tsv` (R², residuals)
- Visualizations: log-log plots with fitted lines

**Prediction**: α ≈ 2.0-2.5 (depth squared or slightly higher)

---

### **Phase 2: Mean Depth Analysis** (30 min - 1 hour)

#### Extend: `analyze-depth-scaling.py` or create new script

**Question**: Is max depth or mean depth more predictive?

**Method**:
1. Compute mean basin depth (average over all nodes in basin)
2. Compare:
   - Basin_Mass vs Max_Depth (R²)
   - Basin_Mass vs Mean_Depth (R²)
3. Test which has tighter correlation

**Data source**: Path characteristics already has depth distributions!
- File: `path_characteristics_n={N}_mechanism_depth_distributions.tsv`

**Expected finding**: Max depth might be better predictor (amplifies extremes)

---

### **Phase 3: Depth Distribution Analysis** (1-2 hours)

#### Script to Create: `analyze-depth-distributions.py`

**Question**: Does the SHAPE of depth distribution matter?

**Metrics to compute**:
1. **Median depth** - Center of distribution
2. **90th percentile depth** - How far do long paths reach?
3. **Depth variance** - How spread out are paths?
4. **Skewness** - Are distributions heavy-tailed?

**Test correlations**:
- Basin_Mass vs 90th percentile depth
- Basin_Mass vs depth variance
- Basin_Mass vs skewness

**Prediction**: Long-tail depth distributions → larger basins

---

### **Phase 4: Mechanistic Understanding** (2-3 hours)

#### Question: WHY does N=5 achieve maximum depth?

**Hypotheses to test**:

1. **Coverage threshold hypothesis**:
   - N=5 has c=32.6% coverage (critical percolation)
   - Below: Paths HALT too often (fragmentation)
   - Above: Paths diffuse (don't concentrate)
   - At threshold: Paths survive AND concentrate → go deep

2. **Convergence speed hypothesis**:
   - N=4: Converges in 11 steps (TOO FAST for deep exploration)
   - N=5: Converges in 12 steps median, but 14% take >50 steps
   - N=7: Converges in 20 steps but HALTs (wastes exploration)

3. **Hub accessibility hypothesis**:
   - N=5 links point to high-degree hubs at optimal distance
   - Hubs have many incoming links → act as "depth multipliers"
   - Test: Correlate link degree of intermediate nodes with depth

**Analysis approach**:
- Extract actual path traces at N=4, N=5, N=7
- Measure link degree along paths
- Correlate hub connectivity with ultimate depth reached

---

### **Phase 5: Predictive Model** (2-4 hours)

#### Goal: Predict basin mass from graph properties

**Model**:
```python
def predict_basin_mass(N, graph_properties):
    coverage = compute_coverage(graph_properties, N)
    expected_depth = depth_model(coverage, convergence_rate)
    entry_breadth = breadth_model(coverage)
    path_survival = 1 - halt_rate(coverage)

    return entry_breadth * expected_depth**alpha * path_survival
```

**Components to develop**:
1. `depth_model(coverage, convergence_rate)` - Predict max depth from coverage
2. `breadth_model(coverage)` - Predict entry breadth (we now know this decreases linearly)
3. Combine with existing path survival data

**Validation**:
- Train on N∈{3,4,5,6,7} Wikipedia data
- Predict for N∈{8,9,10}
- Test on Spanish/German Wikipedia (cross-domain)

---

## Quick Wins (Start Here!)

### **Immediate: Visualize What We Have** (15-30 min)

Create quick plots from existing data:

```python
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np

# Load data
summary = pd.read_csv('data/wikipedia/processed/analysis/entry_breadth_summary_full_analysis_2025_12_31.tsv', sep='\t')

# Plot 1: Basin mass vs max depth (log-log)
plt.figure(figsize=(10, 6))
for cycle in summary['cycle_label'].unique():
    data = summary[summary['cycle_label'] == cycle]
    plt.loglog(data['max_depth'], data['basin_mass'], 'o-', label=cycle, alpha=0.7)
plt.xlabel('Max Depth (steps)')
plt.ylabel('Basin Mass (nodes)')
plt.title('Basin Mass vs Max Depth (Log-Log)')
plt.legend()
plt.grid(True, alpha=0.3)
plt.savefig('basin_mass_vs_depth_loglog.png', dpi=150)

# Plot 2: Entry breadth vs N
plt.figure(figsize=(10, 6))
correlation = pd.read_csv('data/wikipedia/processed/analysis/entry_breadth_correlation_full_analysis_2025_12_31.tsv', sep='\t')
plt.plot(correlation['n'], correlation['mean_entry_breadth'], 'o-', linewidth=2, markersize=8)
plt.xlabel('N (Link Rule Index)')
plt.ylabel('Mean Entry Breadth')
plt.title('Entry Breadth Decreases Monotonically with N')
plt.grid(True, alpha=0.3)
plt.savefig('entry_breadth_vs_n.png', dpi=150)

print("Quick plots created!")
```

**Run this first** to see the patterns visually!

---

## Data Files Reference

### From This Session

```
data/wikipedia/processed/analysis/
├── entry_breadth_n=3_full_analysis_2025_12_31.tsv
├── entry_breadth_n=4_full_analysis_2025_12_31.tsv
├── entry_breadth_n=5_full_analysis_2025_12_31.tsv
├── entry_breadth_n=6_full_analysis_2025_12_31.tsv
├── entry_breadth_n=7_full_analysis_2025_12_31.tsv
├── entry_breadth_summary_full_analysis_2025_12_31.tsv  ← START HERE
└── entry_breadth_correlation_full_analysis_2025_12_31.tsv
```

**Columns** (summary file):
- `cycle_label` - Which 2-cycle
- `n` - N value
- `basin_mass` - Total nodes in basin
- `entry_breadth` - Count of depth=1 nodes
- `entry_ratio` - entry_breadth / basin_mass
- **`max_depth`** - Maximum basin depth ← KEY FOR DEPTH ANALYSIS

### From Previous Sessions

```
data/wikipedia/processed/analysis/
├── path_characteristics_n=3_mechanism_*.tsv
├── path_characteristics_n=4_mechanism_*.tsv
├── path_characteristics_n=5_mechanism_*.tsv
├── path_characteristics_n=6_mechanism_*.tsv
├── path_characteristics_n=7_mechanism_*.tsv
└── cycle_evolution_summary.tsv
```

**Path characteristics contains**:
- Convergence depth distributions
- Path length statistics
- HALT rates
- Percentile data (median, 90th, etc.)

---

## Key Hypotheses to Test

### H1: Power-Law Exponent

**Claim**: Basin_Mass ∝ Depth^α where α ≈ 2.0-2.5

**Test**:
- Linear regression on log-log plot
- Check R² > 0.8
- Extract α from slope

**Success criteria**: α consistent across cycles, good R²

---

### H2: Depth Distribution Matters

**Claim**: Long-tail depth distributions → larger basins

**Test**:
- Compute 90th percentile depth
- Correlate with basin mass
- Compare to max depth correlation

**Success criteria**: Strong correlation, maybe stronger than max depth

---

### H3: Coverage Determines Depth

**Claim**: Depth peaks at c ≈ 0.326 (32.6% coverage)

**Test**:
- Plot max_depth vs coverage for N∈{3,4,5,6,7}
- Should show peak at c ≈ 0.33

**Success criteria**: Clear peak visible

---

### H4: Hub Connectivity Amplifies Depth

**Claim**: Paths through high-degree hubs reach deeper

**Test**:
- Extract link degrees along sample paths
- Correlate average hub degree with ultimate depth
- Compare N=4 vs N=5 hub accessibility

**Success criteria**: N=5 accesses higher-degree hubs

---

## Questions to Answer

### Fundamental

1. **What is α exactly?** (Is it 2? 2.5? Variable?)
2. **Why is depth squared?** (Geometric? Percolation-based?)
3. **What determines maximum depth?** (Coverage? Convergence? Both?)
4. **Is this universal?** (Other graphs? Other N values?)

### Practical

5. **Can we predict N* for arbitrary graphs?** (Given P(k), predict optimal N)
6. **Can we predict basin mass?** (From graph properties alone)
7. **Is mean or max depth more fundamental?** (Which correlates better?)
8. **Do depth distributions have universal shape?** (Power-law? Exponential?)

---

## Recommended Session Flow

### **Start** (15 min)
1. Read this document
2. Read [ENTRY-BREADTH-RESULTS.md](n-link-analysis/empirical-investigations/ENTRY-BREADTH-RESULTS.md)
3. Load context from recent timeline entries

### **Explore** (30 min)
4. Run quick visualization script (above)
5. Examine entry_breadth_summary file
6. Spot-check Massachusetts data

### **Analyze** (2-3 hours)
7. Create `analyze-depth-scaling.py`
8. Fit power-law, extract α
9. Test goodness-of-fit
10. Generate visualizations

### **Extend** (1-2 hours)
11. Analyze depth distributions
12. Test coverage hypothesis
13. Investigate hub connectivity

### **Document** (30 min)
14. Create `DEPTH-SCALING-ANALYSIS.md`
15. Update contract registry
16. Note findings in session log

---

## Infrastructure Already Built

✅ **Scripts available**:
- `analyze-basin-entry-breadth.py` - Entry breadth measurement
- `analyze-path-characteristics.py` - Path-level statistics
- `compare-cycle-evolution.py` - Cycle tracking across N
- `compare-across-n.py` - Cross-N comparison

✅ **Data available**:
- Entry breadth + max depth for 30 basins
- Path characteristics for 25,000 samples
- Cycle evolution across N
- Full basin mappings

✅ **Can reuse patterns from**:
- Entry breadth script structure
- Path characteristics analysis
- Visualization code

---

## Expected Outcomes

### Best Case
- ✓ Confirm α ≈ 2.0-2.5 with high R²
- ✓ Explain WHY depth is squared (geometric model)
- ✓ Predict basin mass from graph properties
- ✓ Publish-ready finding: "Depth power-law in deterministic graph traversal"

### Most Likely
- ✓ Measure α accurately
- ✓ Show depth dominates breadth
- ✓ Identify coverage-depth relationship
- → Need more work on predictive model

### Worst Case (Still Valuable)
- α varies by cycle (need to understand why)
- Depth alone insufficient (need additional factors)
- → Leads to more refined model

---

## Resources

### Documentation to Read
1. [ENTRY-BREADTH-RESULTS.md](n-link-analysis/empirical-investigations/ENTRY-BREADTH-RESULTS.md) - This session's findings
2. [MECHANISM-ANALYSIS.md](n-link-analysis/empirical-investigations/MECHANISM-ANALYSIS.md) - Premature convergence
3. [MASSACHUSETTS-CASE-STUDY.md](n-link-analysis/empirical-investigations/MASSACHUSETTS-CASE-STUDY.md) - Hub connectivity

### Theory Background
4. [n-link-rule-theory.md](llm-facing-documentation/theories-proofs-conjectures/n-link-rule-theory.md) - Basin partition theorems
5. [unified-inference-theory.md](llm-facing-documentation/theories-proofs-conjectures/unified-inference-theory.md) - Statistical mechanics

### Scripts to Reference
6. `n-link-analysis/scripts/analyze-basin-entry-breadth.py` - Template for new analysis
7. `n-link-analysis/scripts/analyze-path-characteristics.py` - Depth distribution extraction

---

## Success Metrics

By end of next session, should have:

✅ **Quantitative**: α measured with confidence intervals
✅ **Visual**: Log-log plots showing power-law
✅ **Mechanistic**: Explanation for why α ≈ 2
✅ **Predictive**: Model relating coverage → depth → basin mass
✅ **Documented**: New investigation file with findings

---

## Priority Ranking

**Must Do** (Core findings):
1. Fit power-law: Basin_Mass ∝ Depth^α
2. Measure α per cycle
3. Visualize log-log plots

**Should Do** (Understanding):
4. Analyze depth distributions
5. Test coverage-depth relationship
6. Compare mean vs max depth

**Nice to Have** (Extensions):
7. Hub connectivity analysis
8. Predictive model development
9. Cross-domain testing prep

---

## Code Snippet to Start

```python
#!/usr/bin/env python3
"""Analyze depth scaling: Basin_Mass ∝ Depth^α

This script:
1. Loads entry breadth results (basin_mass, max_depth)
2. Fits power-law: log(M) = α·log(D) + log(B₀)
3. Extracts exponent α per cycle
4. Tests goodness-of-fit
5. Generates visualizations
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from scipy import stats
from pathlib import Path

# Load data
ANALYSIS_DIR = Path("data/wikipedia/processed/analysis")
summary = pd.read_csv(
    ANALYSIS_DIR / "entry_breadth_summary_full_analysis_2025_12_31.tsv",
    sep="\t"
)

# Filter to cycles with sufficient data points
cycles = summary.groupby('cycle_label').filter(lambda x: len(x) >= 4)

# Fit power-law per cycle
results = []
for cycle_name, cycle_data in cycles.groupby('cycle_label'):
    # Log-log transformation
    log_depth = np.log10(cycle_data['max_depth'])
    log_mass = np.log10(cycle_data['basin_mass'])

    # Linear regression in log-space
    slope, intercept, r_value, p_value, std_err = stats.linregress(log_depth, log_mass)

    results.append({
        'cycle': cycle_name,
        'alpha': slope,
        'log_B0': intercept,
        'r_squared': r_value**2,
        'p_value': p_value,
        'std_err': std_err,
        'n_points': len(cycle_data)
    })

    print(f"{cycle_name}:")
    print(f"  α = {slope:.3f} ± {std_err:.3f}")
    print(f"  R² = {r_value**2:.3f}")
    print()

# Save results
results_df = pd.DataFrame(results)
results_df.to_csv(ANALYSIS_DIR / "depth_scaling_parameters.tsv", sep="\t", index=False)

print(f"Mean α across cycles: {results_df['alpha'].mean():.3f} ± {results_df['alpha'].std():.3f}")
```

Save as: `n-link-analysis/scripts/analyze-depth-scaling.py`

---

**Ready for next session!** 🚀

This document provides complete context, clear direction, and concrete starting points for continuing the depth mechanics investigation.
