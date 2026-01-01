# Visualization Guide - Full Reproduction Results

**Generated**: 2025-12-31
**Analysis**: 9 Wikipedia basins under N=5 link rule
**Total Basin Mass**: 1,991,874 nodes

---

## Quick Links to Visualizations

### **Interactive 3D Trees** (Open in Browser)

1. **Giant Basin** - Massachusetts ↔ Gulf_of_Maine (1M nodes, 98.9% trunk)
   - [3-branch, 3-level view](n-link-analysis/report/assets/tributary_tree_3d_n=5_cycle=Massachusetts__Gulf_of_Maine_k=3_levels=3_depth=10.html)
   - [5-branch, 5-level view](n-link-analysis/report/assets/tributary_tree_3d_n=5_cycle=Massachusetts__Gulf_of_Maine_k=5_levels=5_depth=8.html)

2. **Highest Trunkiness** - Thermosetting_polymer ↔ Curing_(chemistry) (61K nodes, 99.97% trunk)
   - [3-branch, 3-level view](n-link-analysis/report/assets/tributary_tree_3d_n=5_cycle=Thermosetting_polymer__Curing_(chemistry)_k=3_levels=3_depth=10.html)

3. **Lowest Trunkiness** - Kingdom_(biology) ↔ Animal (117K nodes, 36.6% trunk)
   - [5-branch, 3-level view](n-link-analysis/report/assets/tributary_tree_3d_n=5_cycle=Kingdom_(biology)__Animal_k=5_levels=3_depth=10.html)

### **Static Charts** (PNG)

Open these in any image viewer:

- **Trunkiness Analysis**
  - [Top-1 Share Bar Chart](n-link-analysis/report/assets/trunkiness_top1_share.png)
  - [Size vs Share Scatter](n-link-analysis/report/assets/trunkiness_scatter_size_vs_top1.png)

- **Dominance Collapse**
  - [First Below Threshold Hop](n-link-analysis/report/assets/dominance_collapse_first_below_hop.png)
  - [Chase Overlay Comparison](n-link-analysis/report/assets/chase_overlay_dominant_share.png)

- **Individual Chases**
  - [Animal Basin - Share vs Hop](n-link-analysis/report/assets/chase_dominant_upstream_chain_n=5_from=Animal_leasttrunk_bootstrap_2025-12-30_share.png)
  - [Animal Basin - Size vs Hop](n-link-analysis/report/assets/chase_dominant_upstream_chain_n=5_from=Animal_leasttrunk_bootstrap_2025-12-30_basin.png)
  - [Eastern US - Share vs Hop](n-link-analysis/report/assets/chase_dominant_upstream_chain_n=5_from=Eastern_United_States_control_bootstrap_2025-12-30_share.png)
  - [Eastern US - Size vs Hop](n-link-analysis/report/assets/chase_dominant_upstream_chain_n=5_from=Eastern_United_States_control_bootstrap_2025-12-30_basin.png)

---

## Key Findings Visualized

### **1. Heavy-Tail Basin Distribution**

**See**: `trunkiness_scatter_size_vs_top1.png`

- Massachusetts basin: **1,009,471 nodes** (50.7% of total mass)
- 21.7x size difference between largest and smallest basin
- Clear power-law distribution across 9 basins

**Interactive**: Compare Massachusetts 3D tree (massive) vs American_Revolutionary_War (smaller)

---

### **2. Single-Trunk Structure**

**See**: `trunkiness_top1_share.png`

- **6/9 basins** have >95% concentration in top branch
- Thermosetting_polymer basin: **99.97%** in single tributary (most extreme)
- Kingdom_(biology)__Animal: **36.6%** (diffuse, multi-tributary structure)

**Interactive**:
- Open Thermosetting_polymer 3D tree → see almost pure single-trunk (19 nodes, linear)
- Compare to Animal 3D tree → see branching structure (133 nodes, complex)

---

### **3. Dominance Collapse Patterns**

**See**: `dominance_collapse_first_below_hop.png`, `chase_overlay_dominant_share.png`

- Massachusetts: **NO COLLAPSE** - maintains 76.3% share for 50+ hops (unique)
- Median collapse: **13 hops** before dominance drops below 50%
- Animal: **Immediate collapse** (0 hops) - never dominant

**Interactive**: Animal chase charts show share plummeting immediately

---

## How to View Visualizations

### **Option 1: Web Browser (3D Interactive)**

```bash
# On Linux
xdg-open n-link-analysis/report/assets/tributary_tree_3d_n=5_cycle=Massachusetts__Gulf_of_Maine_k=3_levels=3_depth=10.html

# On macOS
open n-link-analysis/report/assets/tributary_tree_3d_n=5_cycle=Massachusetts__Gulf_of_Maine_k=3_levels=3_depth=10.html

# Or navigate to file in file browser and double-click
```

**3D Controls**:
- **Rotate**: Click and drag
- **Zoom**: Scroll wheel
- **Pan**: Right-click and drag
- **Hover**: See page titles and basin sizes

---

### **Option 2: Image Viewer (Static Charts)**

```bash
# View all charts
eog n-link-analysis/report/assets/*.png       # Linux (Eye of GNOME)
feh n-link-analysis/report/assets/*.png       # Linux (feh)
open n-link-analysis/report/assets/*.png      # macOS
```

---

## Data Analysis (TSV Files)

### **Trunkiness Dashboard**

```bash
# Load in Python
import pandas as pd
trunk = pd.read_csv('data/wikipedia/processed/analysis/branch_trunkiness_dashboard_n=5_reproduction_2025-12-31.tsv', sep='\t')
print(trunk.sort_values('top1_share_total', ascending=False))
```

**Columns**:
- `cycle_key`: Basin identifier
- `total_basin_nodes`: Basin size
- `top1_share_total`: Fraction in dominant branch
- `effective_branches`: 1 / Herfindahl-Hirschman index
- `gini_branch_sizes`: Inequality measure (0=equal, 1=single branch)
- `dominant_entry_title`: Page that is dominant tributary

---

### **Collapse Dashboard**

```bash
# Load in Python
collapse = pd.read_csv('data/wikipedia/processed/analysis/dominance_collapse_dashboard_n=5_reproduction_2025-12-31_seed=dominant_enters_cycle_title_thr=0.5.tsv', sep='\t')
print(collapse.sort_values('hops_executed', ascending=False))
```

**Columns**:
- `seed_title`: Starting page
- `hops_executed`: Total chase iterations
- `min_share`: Minimum dominance observed
- `first_below_threshold_hop`: When dominance dropped below 50%
- `stop_reason`: Why chase ended

---

## Generate More Visualizations

### **Create 3D Tree for Any Basin**

```bash
source .venv/bin/activate

# Template
python n-link-analysis/scripts/render-tributary-tree-3d.py \
  --n 5 \
  --cycle-title "CYCLE_PAGE_A" \
  --cycle-title "CYCLE_PAGE_B" \
  --top-k 5 \
  --max-levels 4 \
  --max-depth 12

# Example: Sea_salt ↔ Seawater
python n-link-analysis/scripts/render-tributary-tree-3d.py \
  --n 5 \
  --cycle-title "Sea_salt" \
  --cycle-title "Seawater" \
  --top-k 5 \
  --max-levels 4 \
  --max-depth 12
```

---

## Next Steps

1. **Explore the 3D trees** - Most intuitive visualization
2. **Compare high vs low trunkiness** - Thermosetting_polymer vs Animal
3. **Investigate collapse points** - What pages cause dominance to fail?
4. **Custom analysis** - Load TSV files and create your own plots

---

## Summary Statistics

| Metric | Value |
|--------|-------|
| Total Basins Analyzed | 9 |
| Total Nodes | 1,991,874 |
| Giant Basin Size | 1,009,471 (50.7%) |
| High-Trunk Basins (>95%) | 6 (67%) |
| Stable Basins (no collapse) | 1 (Massachusetts) |
| Median Collapse Point | 13 hops |

**All three main findings confirmed!** ✓

---

**Generated from**: `python n-link-analysis/scripts/reproduce-main-findings.py`
**Report**: [n-link-analysis/report/overview.md](n-link-analysis/report/overview.md)
**Raw Data**: `data/wikipedia/processed/analysis/`
