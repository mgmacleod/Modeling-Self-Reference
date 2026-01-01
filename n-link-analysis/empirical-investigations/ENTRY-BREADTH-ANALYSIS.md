# Entry Breadth Analysis: Testing the Basin Mass Formula

**Date**: 2025-12-31
**Investigation**: Entry breadth hypothesis validation
**Theory Connection**: Statistical Mechanics of Deterministic Traversal
**Status**: Ready to run

---

## Executive Summary

This investigation tests a key prediction of the **statistical mechanics framework**:

```
Basin_Mass = Entry_Breadth × Path_Survival × Convergence_Optimality
```

Specifically, we test whether the **Entry_Breadth** component explains the 65× amplification from N=4 to N=5.

**Hypothesis**: Entry_Breadth(N=5) / Entry_Breadth(N=4) ≈ 8-10×

---

## Background

### The Premature Convergence Puzzle

Recent mechanism analysis revealed:
- **N=4**: Fastest convergence (11 steps median) but **smallest basins** (31k)
- **N=5**: Moderate convergence (12 steps median) but **giant basins** (2.0M)

This 65× amplification cannot be explained by convergence speed alone.

### The Entry Breadth Hypothesis

Basin mass depends on **how many starting points can reach the cycle**:

- **Entry breadth** = Count of unique depth=1 nodes (direct predecessors of cycle)
- These are the "entry gates" through which all paths must pass
- More entry gates → more catchment area → larger basin

**Mechanism**:
- N=4 converges TOO FAST → paths commit before exploring widely → few entry points
- N=5 converges OPTIMALLY → paths explore broadly → many entry points

---

## Method

### Script

[`analyze-basin-entry-breadth.py`](../scripts/analyze-basin-entry-breadth.py)

### Algorithm

For each basin at each N:

1. **Reverse BFS** from cycle nodes (depth 0)
2. **Count depth=1 nodes** (direct cycle predecessors)
3. **Compute metrics**:
   - `basin_mass`: Total nodes in basin
   - `entry_breadth`: Count of depth=1 nodes
   - `entry_ratio`: entry_breadth / basin_mass
   - `max_depth`: Maximum depth reached

### Test Cycles

Using the 6 cycles analyzed across N∈{3,4,5,6,7}:
- Massachusetts ↔ Gulf_of_Maine
- Sea_salt ↔ Seawater
- Mountain ↔ Hill
- Autumn ↔ Summer
- Kingdom_(biology) ↔ Animal
- Latvia ↔ Lithuania

### Predictions

1. **Primary**: B₀(N=5) / B₀(N=4) ≈ 8-10×
2. **Secondary**: Basin_Mass ∝ Entry_Breadth^α where α ≈ 1.5-2.5
3. **Tertiary**: Entry_ratio peaks at N=5 (maximum catchment efficiency)

---

## Running the Analysis

### Quick Start

```bash
# From repo root
bash n-link-analysis/scripts/run-entry-breadth-analysis.sh
```

### Manual Execution

```bash
# Single N
python n-link-analysis/scripts/analyze-basin-entry-breadth.py \
    --n 5 \
    --cycles-file n-link-analysis/test-cycles.tsv \
    --tag test

# Cross-N range
python n-link-analysis/scripts/analyze-basin-entry-breadth.py \
    --n-range 3 7 \
    --cycles-file n-link-analysis/test-cycles.tsv \
    --tag cross_n

# Individual cycle
python n-link-analysis/scripts/analyze-basin-entry-breadth.py \
    --n 5 \
    --cycle-title Massachusetts \
    --cycle-title Gulf_of_Maine \
    --tag single_cycle
```

### Expected Runtime

- **Per basin per N**: ~30-60 seconds (depends on basin size)
- **Full cross-N analysis** (6 cycles × 5 N values): ~5-10 minutes

---

## Outputs

All outputs written to `data/wikipedia/processed/analysis/`:

### 1. Per-N Results: `entry_breadth_n={N}_{tag}.tsv`

Columns:
- `n`: N-link rule index
- `cycle_label`: Cycle identifier (e.g., "Massachusetts ↔ Gulf_of_Maine")
- `cycle_size`: Number of nodes in cycle
- `basin_mass`: Total basin size
- `entry_breadth`: Count of depth=1 entry nodes
- `entry_ratio`: entry_breadth / basin_mass
- `max_depth`: Maximum basin depth

### 2. Cross-N Summary: `entry_breadth_summary_{tag}.tsv`

All cycles, all N values, sorted for comparison.

### 3. Correlation Analysis: `entry_breadth_correlation_{tag}.tsv`

Aggregated statistics per N:
- `n`: N value
- `total_basins`: Number of basins analyzed
- `mean_entry_breadth`: Average entry breadth across basins
- `mean_basin_mass`: Average basin mass
- `mean_entry_ratio`: Average entry ratio

Includes **KEY COMPARISON** section with N=4 vs N=5 amplification ratio.

---

## Success Criteria

### Validation Thresholds

| Metric | Target | Status |
|--------|--------|--------|
| Entry breadth ratio (N=5/N=4) | 8-10× | TBD |
| Basin mass correlation with entry breadth | R² > 0.7 | TBD |
| Entry ratio peak | At N=5 | TBD |

### Expected Outcomes

**If hypothesis validated** (8-10× amplification):
- Confirms Entry_Breadth is dominant term in basin mass formula
- Supports statistical mechanics framework
- Enables predictive modeling for other graphs

**If hypothesis refuted** (<8× or >10× amplification):
- Need to refine basin mass formula
- May indicate additional hidden factors
- Investigate: cycle topology, hub connectivity, graph structure

---

## Next Steps After Analysis

### 1. If Validated

- **Fit complete model**: Basin_Mass = f(Entry_Breadth, Path_Survival, Convergence)
- **Test power-law**: Basin_Mass ∝ Entry_Breadth^α
- **Extend to other graphs**: Spanish Wikipedia, German Wikipedia, arXiv

### 2. If Needs Refinement

- **Investigate deviations**: Which cycles don't follow pattern?
- **Add covariates**: Hub connectivity, cycle position, graph centrality
- **Refine formula**: Additional multiplicative or additive terms

### 3. Theoretical Development

- **Percolation model**: Derive entry breadth from degree distribution
- **Mathematical proof**: Can we predict optimal N from P(k)?
- **Universal constants**: Is 8-10× amplification universal?

---

## Integration with Contract Registry

Once analysis completes:

1. **Create evidence entry** in `llm-facing-documentation/contracts/contract-registry.md`
2. **Update NLR-C-0003** with entry breadth findings
3. **Add new hypothesis** (if validated): Entry breadth scaling law

---

## References

### Theory Documents
- [unified-inference-theory.md](../../llm-facing-documentation/theories-proofs-conjectures/unified-inference-theory.md)
- [n-link-rule-theory.md](../../llm-facing-documentation/theories-proofs-conjectures/n-link-rule-theory.md)

### Related Investigations
- [MECHANISM-ANALYSIS.md](MECHANISM-ANALYSIS.md) - Premature convergence mechanism
- [PHASE-TRANSITION-REFINED.md](PHASE-TRANSITION-REFINED.md) - N=4 minimum, N=5 peak
- [MASSACHUSETTS-CASE-STUDY.md](MASSACHUSETTS-CASE-STUDY.md) - Hub connectivity case study

### Scripts
- [`analyze-basin-entry-breadth.py`](../scripts/analyze-basin-entry-breadth.py)
- [`run-entry-breadth-analysis.sh`](../scripts/run-entry-breadth-analysis.sh)

---

**Status**: Ready to execute
**Priority**: HIGH - Key test of statistical mechanics framework
**Effort**: LOW - Data and infrastructure exist, ~10 min runtime
