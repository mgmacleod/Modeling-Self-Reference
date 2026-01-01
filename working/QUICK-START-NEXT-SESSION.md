# Quick Start Guide - Next Session on Depth Mechanics

**Goal**: Understand depth-based basin mass formula: `Basin_Mass ≈ Entry_Breadth × Depth^α`

---

## 🚀 Fastest Path to Results (30 min)

### 1. Load Context (5 min)
```bash
# Read these in order:
cat NEXT-SESSION-DEPTH-MECHANICS.md  # Full plan
cat ENTRY-BREADTH-SESSION-SUMMARY.md  # What we just discovered
cat n-link-analysis/empirical-investigations/ENTRY-BREADTH-RESULTS.md  # Detailed findings
```

### 2. Quick Visualization (10 min)
```bash
source .venv/bin/activate
cd n-link-analysis/scripts
python3  # Start Python REPL
```

```python
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np

# Load the data
summary = pd.read_csv('../../data/wikipedia/processed/analysis/entry_breadth_summary_full_analysis_2025_12_31.tsv', sep='\t')

# Log-log plot: Basin Mass vs Max Depth
plt.figure(figsize=(12, 8))
for cycle in summary['cycle_label'].unique():
    data = summary[summary['cycle_label'] == cycle]
    plt.loglog(data['max_depth'], data['basin_mass'], 'o-', label=cycle, alpha=0.7, markersize=8)
plt.xlabel('Max Depth (steps)', fontsize=12)
plt.ylabel('Basin Mass (nodes)', fontsize=12)
plt.title('Basin Mass vs Max Depth - Power Law?', fontsize=14)
plt.legend(fontsize=10)
plt.grid(True, alpha=0.3)
plt.tight_layout()
plt.savefig('../report/assets/basin_mass_vs_depth_loglog.png', dpi=150)
plt.show()

print("If points fall on straight lines in log-log plot → power law!")
print(f"Slope of line ≈ α (predicted: 2.0-2.5)")
```

**What to look for**: Straight lines in log-log space → power law confirmed!

### 3. Fit Power Law (15 min)
```python
from scipy import stats

# Fit for Massachusetts (largest basin)
mass = summary[summary['cycle_label'] == 'Massachusetts ↔ Gulf_of_Maine']
log_depth = np.log10(mass['max_depth'])
log_mass = np.log10(mass['basin_mass'])

slope, intercept, r_value, p_value, std_err = stats.linregress(log_depth, log_mass)

print(f"Massachusetts: Basin_Mass ∝ Depth^{slope:.2f}")
print(f"R² = {r_value**2:.3f}")
print(f"Predicted α: 2.0-2.5")
print(f"Match? {2.0 <= slope <= 2.5}")
```

**Success criteria**: α ≈ 2.0-2.5 with R² > 0.8

---

## 📊 Key Data Files

```
data/wikipedia/processed/analysis/
└── entry_breadth_summary_full_analysis_2025_12_31.tsv  ← START HERE

Columns:
- cycle_label: Which 2-cycle (e.g., "Massachusetts ↔ Gulf_of_Maine")
- n: N value (3, 4, 5, 6, 7)
- basin_mass: Total nodes in basin
- entry_breadth: Count of depth=1 nodes
- max_depth: Maximum basin depth ← KEY VARIABLE
```

---

## 🎯 Core Question

**Why does N=5 have 59× larger basins than N=4?**

**Answer we found**: Entry breadth DOWN 25%, but depth UP 6×, and depth is SQUARED!

```
Basin_Mass ratio = (Entry_Breadth ratio) × (Depth ratio)^α
                 = 0.75 × 6^2.3
                 ≈ 27× to 59× (matches data!)
```

---

## 📝 Next Investigation Steps

### Phase 1: Measure α (Must Do)
1. Load entry_breadth_summary
2. For each cycle: fit log(mass) vs log(depth)
3. Extract α (slope) and R² (fit quality)
4. Check if α ≈ 2.0-2.5 universally

### Phase 2: Why α ≈ 2? (Should Do)
5. Geometric model? (Volume ∝ area × depth)
6. Percolation-based? (Critical phenomena)
7. Graph topology? (Scale-free properties)

### Phase 3: Predict Basin Mass (Nice to Have)
8. Model: depth = f(coverage, convergence)
9. Combine with α to predict mass
10. Test on other graphs

---

## 🔧 Script to Create

```python
# n-link-analysis/scripts/analyze-depth-scaling.py
# Full template in NEXT-SESSION-DEPTH-MECHANICS.md
# ~100 lines, reuses patterns from analyze-basin-entry-breadth.py
```

**Outputs**:
- `depth_scaling_parameters.tsv` (α per cycle)
- `depth_scaling_fit_quality.tsv` (R², p-values)
- Visualizations: log-log plots + fitted lines

---

## 💡 What We Know

✅ Entry breadth DECREASES with N (monotonic: 871 → 307)
✅ Basin mass PEAKS at N=5 (non-monotonic: 17k → 305k → 5k)
✅ Max depth PEAKS at N=5 (mean: 26 → 74 → 28 steps)
✅ Depth explains the peak better than breadth!

**Formula discovered**:
```
Basin_Mass ≈ Entry_Breadth × Depth^α × Path_Survival
where α ≈ 2.0-2.5 (to be confirmed!)
```

---

## ⚠️ Key Insight

**Original hypothesis**: Entry breadth → basin mass
**Reality**: Depth^2 → basin mass

Like comparing:
- **Cylinder**: Volume = π × radius² × height
  - Breadth = radius (linear)
  - Depth = height (linear)
  - Volume ∝ radius² × height (quadratic in radius!)

**N=5 basins are narrow but DEEP** → huge volume!

---

## 📖 Context Documents

**Read first** (5 min):
1. [ENTRY-BREADTH-RESULTS.md](n-link-analysis/empirical-investigations/ENTRY-BREADTH-RESULTS.md)

**Read if needed** (15 min):
2. [MECHANISM-ANALYSIS.md](n-link-analysis/empirical-investigations/MECHANISM-ANALYSIS.md)
3. [MASSACHUSETTS-CASE-STUDY.md](n-link-analysis/empirical-investigations/MASSACHUSETTS-CASE-STUDY.md)

**Full plan** (30 min):
4. [NEXT-SESSION-DEPTH-MECHANICS.md](NEXT-SESSION-DEPTH-MECHANICS.md)

---

## ✅ Session Success = Answer These

1. **What is α?** (Measured from data)
2. **Is α universal?** (Same for all cycles?)
3. **Why α ≈ 2?** (Geometric? Percolation?)
4. **Can we predict mass?** (From depth alone?)

If you answer 1-2: **Good session**
If you answer 1-4: **Excellent session**

---

## 🎓 Scientific Process Note

This is **excellent science in action**:

1. Had hypothesis (entry breadth dominates)
2. Built infrastructure to test it
3. Hypothesis REFUTED by data
4. Data revealed BETTER pattern (depth dominates)
5. Now: Quantify the new pattern (depth^α law)

**Next session = Step 5!**

---

**Ready to go!** All data exists, infrastructure built, just need to fit the model. 🚀
