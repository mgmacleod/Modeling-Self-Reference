# Next Session: Scaling Up Depth Mechanics Analysis

**Date**: 2025-12-31
**For**: Next session continuation
**Focus**: Scale up analysis to study depth structures in more detail

---

## Session Goal

**Expand the depth analysis to reveal finer-grained structure and test mechanistic hypotheses at scale.**

Based on current findings:
- ✓ Universal power-law discovered: Basin_Mass ∝ Depth^2.5
- ✓ N=5 confirmed as universal depth peak
- ✓ α varies by cycle: [1.87, 3.06] → cycle-specific geometry
- → **Next**: Understand WHY α varies and WHAT determines depth

---

## Current State Summary

### What We Know

**Universal patterns** (30 data points, 6 cycles):
1. Power-law scaling: α = 2.50 ± 0.48
2. Mean R² = 0.878 (excellent fits)
3. Depth dominates: r = 0.943 vs entry breadth r = 0.127
4. N=5 peak: 7.2× deeper than N=4 (mean across cycles)

**Cycle-specific variation**:
1. α range: [1.87 (Massachusetts) to 3.06 (Autumn)]
2. Depth range at N=5: [31 (Latvia) to 168 (Massachusetts)]
3. Basin mass range at N=5: [83k to 1M nodes]

**Open questions**:
1. Why does α vary? (graph topology? hub structure?)
2. What determines maximum depth? (coverage? convergence? hubs?)
3. Is α predictable from graph properties?
4. Do depth distributions have universal shape?

---

## Scaling Up Strategy

### Dimension 1: More Cycles (Breadth)

**Current**: 6 cycles analyzed
**Target**: 20-50 cycles

**Benefits**:
- Tighter statistical estimates of α distribution
- Identify more α outliers (extreme geometries)
- Test universality across diverse cycle types
- Separate graph-dependent vs N-dependent effects

**Data available**:
- We have ~1000 2-cycles in the Wikipedia data
- Can select representative sample across:
  - Different basin sizes (small/medium/large)
  - Different coverage levels
  - Different hub connectivity patterns

**Computational cost**: ~5-10 minutes for 50 cycles (parallelizable)

### Dimension 2: More N Values (Depth in N-space)

**Current**: N ∈ {3, 4, 5, 6, 7}
**Target**: N ∈ {3, 4, 5, 6, 7, 8, 9, 10}

**Benefits**:
- Test if depth peak continues beyond N=5
- Predict behavior at higher N (extrapolation)
- Understand depth decay after N=5
- Validate power-law at more points per cycle

**Prediction**:
- Depth should decrease after N=5 (return to convergence)
- Basin mass should decrease (fewer entry points + shallower)
- Coverage continues decreasing → higher HALT rate

**Computational cost**: ~30-60 minutes for N=8,9,10 (3 new N values × existing cycles)

### Dimension 3: Full Depth Distributions (Vertical depth)

**Current**: Max depth only (single number per basin)
**Target**: Full depth distribution (histogram of all node depths)

**Benefits**:
- Understand depth distribution shape (exponential? power-law? normal?)
- Test mean depth vs max depth as predictors
- Identify depth bottlenecks (where do paths get stuck?)
- Measure depth variance within basins

**Metrics to compute**:
1. Mean depth (average over all basin nodes)
2. Median depth (50th percentile)
3. 90th percentile depth (captures long tail)
4. Depth variance (spread)
5. Depth skewness (asymmetry)
6. Depth histogram (binned distribution)

**Data source**: Path characteristics already has depth distributions!
- File: `path_characteristics_n={N}_mechanism_depth_distributions.tsv`
- Just need to parse and aggregate

**Computational cost**: Negligible (data already exists)

### Dimension 4: Hub Connectivity (Graph topology)

**Current**: No hub analysis
**Target**: Measure hub degrees along paths, correlate with depth

**Benefits**:
- Test hypothesis: N=5 accesses higher-degree hubs
- Explain WHY N=5 achieves deeper basins mechanistically
- Predict α from hub degree distribution
- Understand path channeling through hubs

**Metrics to compute**:
1. Mean hub degree along paths (by N)
2. Max hub degree encountered
3. Hub degree at depth milestones (depth=10, 20, 50, etc.)
4. Correlation: hub_degree × depth

**Data needed**: Trace sample paths, measure node degrees
- Use existing path tracing infrastructure
- Sample 1000 paths per N per cycle
- Measure in-degree and out-degree at each step

**Computational cost**: ~10-20 minutes (path tracing + degree lookup)

---

## Recommended Scaling Priority

### **Phase 1: Low-Hanging Fruit** (1-2 hours)

Focus on dimensions where data already exists:

1. ✅ **Full depth distributions** (Dimension 3)
   - Parse existing path characteristics files
   - Compute mean, median, 90th percentile depth
   - Test which depth metric best predicts basin mass
   - Expected finding: 90th percentile > max > mean

2. ✅ **Extend to N=8** (Dimension 2 - partial)
   - Run basin analysis for N=8 on existing 6 cycles
   - Test if depth decreases as predicted
   - Validate power-law extrapolation
   - Quick win: 1 new N value × 6 cycles = 6 data points

**Output**:
- Depth distribution analysis document
- Updated power-law fits with more depth metrics
- N=8 validation of depth decay hypothesis

---

### **Phase 2: Moderate Effort** (2-4 hours)

Scale to more cycles and N values:

3. ✅ **Add 14 more cycles** (Dimension 1)
   - Select diverse cycles from existing data:
     - 5 small basins (<10k nodes at N=5)
     - 5 medium basins (10k-100k nodes)
     - 4 large basins (>100k nodes)
   - Run entry breadth + depth analysis
   - Fit power-laws for all 20 cycles total
   - Tighten α distribution estimates

4. ✅ **Extend to N=9, 10** (Dimension 2 - complete)
   - Run for all 20 cycles
   - Test depth decay hypothesis fully
   - Predict basin mass at N=9, 10 using power-law
   - Validate predictions

**Output**:
- 20 cycles × 8 N values = 160 data points
- Robust α distribution (n=20 instead of n=6)
- Complete N trajectory (N=3 to N=10)
- Predictive model validation

---

### **Phase 3: Deep Mechanistic Dive** (4-8 hours)

Understand WHY patterns exist:

5. ✅ **Hub connectivity analysis** (Dimension 4)
   - Trace 1000 sample paths per N per cycle (6 cycles × 5 N = 30k paths)
   - Measure hub degrees at each step
   - Correlate hub connectivity with ultimate depth
   - Test hypothesis: N=5 channels through high-degree hubs

6. ✅ **Predict α from graph properties**
   - Extract graph features: degree distribution, clustering, assortativity
   - Correlate with fitted α values
   - Build regression model: α = f(graph_properties)
   - Predict α for unseen cycles

**Output**:
- Hub connectivity analysis document
- Mechanistic explanation for N=5 depth peak
- Predictive model for α from graph topology
- Publication-ready finding: "Hub channeling explains depth amplification"

---

## Data Requirements

### Already Available

✅ **Entry breadth + max depth**: 6 cycles × 5 N values
- Files: `entry_breadth_n={N}_full_analysis_2025_12_31.tsv`
- Contains: basin_mass, entry_breadth, max_depth, entry_ratio

✅ **Path characteristics**: 6 cycles × 5 N values × 5000 paths
- Files: `path_characteristics_n={N}_mechanism_*.tsv`
- Contains: convergence depth distributions, path lengths, HALT rates

✅ **Cycle evolution**: Cross-N comparison
- File: `cycle_evolution_summary.tsv`
- Contains: How cycles transform across N values

✅ **Power-law fit parameters**: 6 cycles
- File: `power_law_fit_parameters.tsv`
- Contains: α, R², p-values, fit quality

### Need to Generate

📋 **More cycles** (14 additional)
- Run `analyze-basin-entry-breadth.py` on new cycles
- Select from existing basin mappings
- ~10 minutes per cycle

📋 **N=8, 9, 10 data** (3 new N values)
- Run basin mapping for higher N (may already exist)
- Run entry breadth analysis
- ~30-60 minutes total

📋 **Hub degree traces** (new analysis)
- Create `analyze-hub-connectivity.py` script
- Trace paths and measure degrees
- ~10-20 minutes runtime

---

## Technical Infrastructure Needed

### Scripts to Create

1. **`analyze-depth-distributions.py`**
   - Parse existing path characteristics
   - Compute depth distribution statistics
   - Compare mean vs median vs max vs 90th percentile
   - Test which predicts basin mass best

2. **`extend-to-more-cycles.py`**
   - Automated cycle selection (stratified by basin size)
   - Batch run entry breadth analysis
   - Aggregate results into unified dataset

3. **`analyze-hub-connectivity.py`**
   - Trace sample paths through graph
   - Measure node in-degree and out-degree at each step
   - Correlate hub degrees with depth reached
   - Compare N=4 vs N=5 hub accessibility

4. **`predict-alpha-from-topology.py`**
   - Extract graph features per cycle
   - Fit regression: α ~ degree_dist + clustering + assortativity
   - Cross-validate predictions
   - Identify which features matter most

### Scripts to Extend

5. **`explore-depth-structure-large-scale.py`** (already exists)
   - Update to handle 20+ cycles
   - Add N=8, 9, 10 data
   - Regenerate visualizations at scale

6. **`interactive-depth-explorer.py`** (already exists)
   - Update data loader for expanded dataset
   - Add depth distribution view panel
   - Add hub connectivity visualization

---

## Expected Findings

### Depth Distributions

**Hypothesis**: Depth distributions are exponential or heavy-tailed

**Prediction**:
- Mean depth < Median depth < Max depth (right-skewed)
- 90th percentile depth ≈ 0.6 × max depth
- Variance scales with mean: σ² ∝ μ

**Test**: Fit exponential, power-law, log-normal to distributions

### Extended N Values

**Hypothesis**: Depth decreases after N=5

**Prediction**:
- N=8: depth ≈ 20 steps (return to N=6 levels)
- N=9: depth ≈ 15 steps
- N=10: depth ≈ 12 steps (approach N=4 levels)

**Test**: Measure max depth at N=8, 9, 10 and compare to N=6, 7

### Hub Connectivity

**Hypothesis**: N=5 accesses higher-degree hubs than N=4

**Prediction**:
- Mean hub degree at N=5: 500-1000 (high)
- Mean hub degree at N=4: 100-300 (moderate)
- Correlation: hub_degree × depth > 0.7

**Test**: Trace paths, measure degrees, compute correlation

### α Prediction

**Hypothesis**: α correlates with hub degree variance

**Prediction**:
- High variance in hub degrees → high α (narrow funnels)
- Low variance → low α (broad cones)
- R² > 0.6 for regression model

**Test**: Extract degree distributions, fit regression, cross-validate

---

## Session Plan

### **Option A: Incremental Scaling** (Recommended)

Session 1 (next session):
- ✅ Parse depth distributions (Phase 1)
- ✅ Extend to N=8 (Phase 1)
- ✅ Add 5 more cycles (Phase 2 - partial)
- 📊 Results: Tighter α estimates, depth distribution insights

Session 2:
- ✅ Add remaining 9 cycles (Phase 2 - complete)
- ✅ Extend to N=9, 10 (Phase 2 - complete)
- 📊 Results: Complete N trajectory, robust statistics

Session 3:
- ✅ Hub connectivity analysis (Phase 3)
- ✅ Predict α from topology (Phase 3)
- 📊 Results: Mechanistic understanding, predictive model

### **Option B: Deep Dive on Mechanism** (Alternative)

Focus entirely on understanding WHY α varies:

Session 1 (next session):
- ✅ Hub connectivity analysis (all 6 cycles, N=3-7)
- ✅ Extract graph topology features
- ✅ Correlate with α values
- 📊 Results: Mechanistic explanation for α variation

Benefits:
- Deeper understanding before scaling
- Guide cycle selection (choose diverse α values)
- More targeted scaling in later sessions

### **Option C: Breadth First** (Maximum data)

Prioritize data collection over mechanism:

Session 1 (next session):
- ✅ Extend to 20 cycles (all N=3-7)
- ✅ Extend to N=8, 9, 10 (all 20 cycles)
- 📊 Results: 20 × 8 = 160 data points, robust statistics

Session 2:
- ✅ Analyze depth distributions
- ✅ Hub connectivity on subset (5 representative cycles)
- 📊 Results: Complete picture, mechanism for key cases

---

## Quick Wins for Next Session

If you want to start immediately and build momentum:

### **Quick Win 1: Depth Distribution Analysis** (30 min)

Already have the data in `path_characteristics_n={N}_mechanism_*.tsv`!

```python
# Pseudocode
for n in [3, 4, 5, 6, 7]:
    depths = load_depth_distribution(n)
    print(f"N={n}:")
    print(f"  Mean: {depths.mean()}")
    print(f"  Median: {depths.median()}")
    print(f"  90th: {depths.quantile(0.9)}")
    print(f"  Max: {depths.max()}")
```

**Output**: Table comparing depth metrics across N

### **Quick Win 2: N=8 Validation** (1 hour)

Run existing pipeline on N=8:

```bash
python analyze-basin-entry-breadth.py --n=8 --cycles=Massachusetts,Latvia,Autumn
```

**Output**: Test if depth decreases as predicted

### **Quick Win 3: Select 5 More Cycles** (30 min)

Stratified sampling:

```python
# Pick cycles with diverse basin sizes at N=5
small = cycles[mass < 100k]      # Pick 2
medium = cycles[100k < mass < 500k]  # Pick 2
large = cycles[mass > 500k]      # Pick 1
```

**Output**: Diversified cycle portfolio for analysis

---

## Success Metrics

By end of next session, should have:

✅ **Depth distribution analysis**:
- Mean vs median vs max depth comparisons
- Best depth metric identified (for prediction)
- Depth distribution shape characterized

✅ **Extended N coverage**:
- At least N=8 data for existing cycles
- Validation of depth decay hypothesis
- Updated power-law plots

✅ **Expanded cycle coverage** (optional):
- At least 10 cycles total (up from 6)
- More robust α distribution
- Identified extreme α outliers

✅ **Documentation**:
- New investigation document
- Updated visualizations
- Next steps clearly defined

---

## Resources

### Scripts Available

- `analyze-basin-entry-breadth.py` - Entry breadth + max depth measurement
- `analyze-path-characteristics.py` - Path-level statistics (has depth distributions!)
- `explore-depth-structure-large-scale.py` - Large-scale visualization
- `interactive-depth-explorer.py` - Interactive UI

### Data Available

```
data/wikipedia/processed/
├── basins/
│   └── n={N}/
│       └── basins_*.tsv  # Full basin mappings (all N values)
├── analysis/
│   ├── entry_breadth_*.tsv  # Current 6 cycles × 5 N
│   ├── path_characteristics_*.tsv  # Has depth distributions!
│   └── depth_exploration/
│       ├── power_law_fit_parameters.tsv
│       └── *.png  # Visualizations
```

### Documentation

- [DEPTH-SCALING-ANALYSIS.md](../n-link-analysis/empirical-investigations/DEPTH-SCALING-ANALYSIS.md) - Current findings
- [ENTRY-BREADTH-RESULTS.md](../n-link-analysis/empirical-investigations/ENTRY-BREADTH-RESULTS.md) - Discovery of depth dominance
- [MECHANISM-ANALYSIS.md](../n-link-analysis/empirical-investigations/MECHANISM-ANALYSIS.md) - Premature convergence
- [INTERACTIVE-EXPLORER-GUIDE.md](../n-link-analysis/scripts/INTERACTIVE-EXPLORER-GUIDE.md) - UI usage

---

## Recommendation

**Start with Option A (Incremental Scaling) + Quick Win 1**:

1. Begin next session by parsing depth distributions (30 min, easy win)
2. Extend to N=8 for existing cycles (1 hour, tests predictions)
3. Add 5 diverse cycles (1-2 hours, improves statistics)
4. Document findings and plan hub analysis for following session

**Rationale**:
- Builds momentum with quick wins
- Tests key predictions (depth decay at N>5)
- Improves statistical robustness incrementally
- Leaves mechanism dive for when you have more data to guide it

---

**Ready for next session!** 🚀

This document provides complete context for scaling up the analysis systematically, with clear priorities, concrete next steps, and measurable success criteria.
