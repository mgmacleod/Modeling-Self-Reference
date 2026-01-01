# Entry Breadth Analysis - Quick Start Guide

This guide explains how to run the entry breadth analysis to test the statistical mechanics framework.

---

## What This Tests

**Hypothesis**: Basin mass depends on entry breadth (number of depth=1 entry points into the cycle).

**Prediction**: Entry_Breadth(N=5) / Entry_Breadth(N=4) ≈ 8-10×

This would explain the 65× basin mass amplification from N=4 to N=5.

---

## Prerequisites

1. **Data files must exist**:
   ```bash
   data/wikipedia/processed/nlink_sequences.parquet
   data/wikipedia/processed/pages.parquet
   ```

2. **Edge databases should be materialized** (or will be created automatically):
   ```bash
   data/wikipedia/processed/analysis/edges_n={3,4,5,6,7}.duckdb
   ```

3. **Python environment**:
   ```bash
   source .venv/bin/activate  # If using venv
   ```

---

## Quick Run

### Option 1: Use the helper script (easiest)

```bash
# From repo root
bash n-link-analysis/scripts/run-entry-breadth-analysis.sh
```

This will:
- Run analysis for N∈{3,4,5,6,7}
- Analyze 6 test cycles
- Generate all output files
- Print key comparisons

**Expected runtime**: ~5-10 minutes

---

### Option 2: Manual execution

```bash
# Cross-N analysis (recommended)
python n-link-analysis/scripts/analyze-basin-entry-breadth.py \
    --n-range 3 7 \
    --cycles-file n-link-analysis/test-cycles.tsv \
    --tag my_analysis

# Single N value
python n-link-analysis/scripts/analyze-basin-entry-breadth.py \
    --n 5 \
    --cycles-file n-link-analysis/test-cycles.tsv \
    --tag test_n5

# Single cycle
python n-link-analysis/scripts/analyze-basin-entry-breadth.py \
    --n 5 \
    --cycle-title Massachusetts \
    --cycle-title Gulf_of_Maine \
    --tag massachusetts_only
```

---

## Understanding the Output

### Files Created

All output files are in `data/wikipedia/processed/analysis/`:

#### 1. Per-N Results: `entry_breadth_n={N}_{tag}.tsv`

One file per N value with columns:
- `n`: N-link rule index
- `cycle_label`: Which cycle (e.g., "Massachusetts ↔ Gulf_of_Maine")
- `basin_mass`: Total basin size
- `entry_breadth`: Number of depth=1 entry nodes
- `entry_ratio`: entry_breadth / basin_mass

#### 2. Summary: `entry_breadth_summary_{tag}.tsv`

All results combined, sorted by cycle and N for easy comparison.

#### 3. Correlation: `entry_breadth_correlation_{tag}.tsv`

Aggregated statistics per N:
- Mean entry breadth
- Mean basin mass
- Mean entry ratio

**IMPORTANT**: Look for the "KEY COMPARISONS" section at the end of the output!

---

## Example Output

```
============================================================
KEY COMPARISONS
============================================================

Entry Breadth Amplification (N=4 → N=5):
  N=4 mean entry breadth: 2,456.3
  N=5 mean entry breadth: 21,892.7
  Ratio (N=5 / N=4): 8.91×
  Prediction: 8-10×
  Status: ✓ VALIDATED
```

---

## Interpreting Results

### If N=5/N=4 ratio is 8-10× ✓

**Conclusion**: Entry breadth is the dominant factor in basin mass!

**Next steps**:
1. Fit complete model: `Basin_Mass = f(Entry_Breadth, Path_Survival, Convergence)`
2. Test power-law: `Basin_Mass ∝ Entry_Breadth^α`
3. Extend to other graphs (Spanish Wikipedia, arXiv, etc.)

### If ratio is outside 8-10× range ✗

**Investigate**:
- Which cycles deviate from the pattern?
- Are there hidden factors (hub connectivity, cycle topology)?
- Does the formula need additional terms?

---

## Advanced Usage

### Custom Cycles

Create a TSV file with your cycles:

```tsv
title1	title2
Article_A	Article_B
Article_C	Article_D
```

Then run:
```bash
python n-link-analysis/scripts/analyze-basin-entry-breadth.py \
    --n-range 3 7 \
    --cycles-file my_cycles.tsv \
    --tag my_custom_analysis
```

### Limit BFS Depth

For faster testing on large basins:

```bash
python n-link-analysis/scripts/analyze-basin-entry-breadth.py \
    --n 5 \
    --cycles-file n-link-analysis/test-cycles.tsv \
    --max-depth 100 \
    --tag shallow_test
```

This stops after 100 reverse BFS layers (useful for quick tests).

---

## Troubleshooting

### "Missing edges table"

The script will materialize edge tables automatically. First run takes longer (~2-3 min per N).

### "Could not resolve titles"

Make sure titles match exactly (case-sensitive, underscores for spaces):
- ✓ `Massachusetts`
- ✓ `Gulf_of_Maine`
- ✗ `massachusetts` (wrong case)
- ✗ `Gulf of Maine` (spaces instead of underscores)

### Memory issues

Large basins (like Massachusetts at N=5 with 1M+ nodes) may use significant RAM. If you hit memory limits:
1. Use `--max-depth` to limit BFS depth
2. Analyze fewer cycles at once
3. Run N values sequentially instead of in batch

---

## Next Steps After Running

1. **Review outputs** - Check the correlation file for the N=4/N=5 ratio

2. **Update investigation doc** - Add results to [ENTRY-BREADTH-ANALYSIS.md](empirical-investigations/ENTRY-BREADTH-ANALYSIS.md)

3. **Update contracts** - If validated, update [contract-registry.md](../llm-facing-documentation/contracts/contract-registry.md)

4. **Extend analysis**:
   - Fit complete basin mass model
   - Test on other language Wikipedias
   - Develop percolation framework

---

## Theory Context

This analysis tests a key component of the **statistical mechanics of deterministic traversal** framework:

```
Basin_Mass = Entry_Breadth × Path_Survival × Convergence_Optimality
```

**Entry_Breadth**: How many unique depth=1 nodes feed into the cycle?
- Measures catchment area
- Dominant term in basin mass formula
- Predicted to explain 65× N=4→N=5 amplification

See [empirical-investigations/ENTRY-BREADTH-ANALYSIS.md](empirical-investigations/ENTRY-BREADTH-ANALYSIS.md) for full theoretical background.

---

## Questions?

See the full investigation document: [empirical-investigations/ENTRY-BREADTH-ANALYSIS.md](empirical-investigations/ENTRY-BREADTH-ANALYSIS.md)

Or check the script documentation:
```bash
python n-link-analysis/scripts/analyze-basin-entry-breadth.py --help
```
