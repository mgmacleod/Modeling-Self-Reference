# Analysis Harness Scripts

This directory contains two harness scripts that automate running the N-link analysis pipeline with sensible defaults.

## Quick Start

```bash
# Run complete analysis for N=5 in quick mode (6 cycles, reduced samples)
python run-analysis-harness.py --quick --n 5

# Run complete analysis for N=5 in full mode (9 cycles, full samples)
python run-analysis-harness.py --n 5

# Analyze a single specific cycle in detail
python run-single-cycle-analysis.py --n 5 --cycle-title Massachusetts --cycle-title "Gulf_of_Maine"
```

---

## run-analysis-harness.py

**Purpose**: Run the complete analysis pipeline for multiple cycles with all scripts.

**What it does**:
1. Validates data dependencies
2. Samples random traces to identify frequent cycles
3. For each configured cycle:
   - Maps the complete basin
   - Analyzes branch structure
   - Chases dominant upstream trunks
   - Finds preimages
4. Aggregates metrics into dashboards
5. Generates visualizations and reports

**Usage**:

```bash
# Quick mode (recommended for testing): 6 cycles, reduced samples, ~30-60 minutes
python run-analysis-harness.py --quick --n 5

# Full mode: 9 cycles, full samples, ~2-4 hours
python run-analysis-harness.py --n 5

# Analyze specific number of cycles
python run-analysis-harness.py --quick --max-cycles 3 --n 5

# Custom tag for outputs
python run-analysis-harness.py --quick --n 5 --tag my_analysis_2026-01-01
```

**Parameters**:

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `--n` | int | 5 | N for N-link rule |
| `--tag` | str | harness_YYYY-MM-DD | Tag for output files |
| `--skip-existing` | flag | false | Skip scripts if outputs exist (not fully implemented) |
| `--quick` | flag | false | Quick mode with reduced samples (6 cycles vs 9) |
| `--max-cycles` | int | 9 (6 in quick) | Maximum number of cycles to analyze |

**Cycles Analyzed** (in order):

Quick mode (6 cycles):
1. Massachusetts ↔ Gulf_of_Maine (giant basin, 1M+ nodes)
2. Sea_salt ↔ Seawater (large basin)
3. Mountain ↔ Hill (large basin)
4. Autumn ↔ Summer (high trunkiness)
5. Kingdom_(biology) ↔ Animal (low trunkiness contrast)
6. Latvia ↔ Lithuania (medium basin)

Full mode adds:
7. Thermosetting_polymer ↔ Curing_(chemistry) (highest trunkiness)
8. Precedent ↔ Civil_law (medium trunkiness)
9. American_Revolutionary_War ↔ Eastern_United_States (low trunkiness)

**Scripts Run** (in order):

**Tier 0: Validation & Sampling**
1. `validate-data-dependencies.py` - Validate data files
2. `sample-nlink-traces.py` - Sample random traces (100 quick / 500 full)
3. `trace-nlink-path.py` - Single path sanity check
4. `analyze-path-characteristics.py` - Path convergence analysis (50 quick / 200 full)

**Tier 1: Per-Cycle Analysis** (for each cycle)
5. `map-basin-from-cycle.py` - Map complete basin
6. `branch-basin-analysis.py` - Quantify branch structure
7. `chase-dominant-upstream.py` - Chase dominant trunk (20 hops quick / 40 full)
8. `find-nlink-preimages.py` - Find direct predecessors

**Tier 2: Aggregation**
9. `compute-trunkiness-dashboard.py` - Aggregate concentration metrics
10. `batch-chase-collapse-metrics.py` - Measure dominance collapse

**Tier 3: Cross-Analysis**
11. `compare-cycle-evolution.py` - Analyze cycle stability
12. `analyze-cycle-link-profiles.py` - Examine link sequences

**Tier 4: Visualization**
13. `visualize-mechanism-comparison.py` - Generate comparison charts
14. `render-human-report.py` - Create summary report
15. `render-tributary-tree-3d.py` - 3D visualization (full mode only, first cycle)

**Outputs**:
- All analysis files: `data/wikipedia/processed/analysis/`
- Human report: `n-link-analysis/report/overview.md`
- Charts: `n-link-analysis/report/assets/*.png`
- 3D trees: `n-link-analysis/report/assets/*.html`

**Example Session**:

```bash
# First time: validate data
python validate-data-dependencies.py

# Quick test run with 2 cycles (~10-15 minutes)
python run-analysis-harness.py --quick --max-cycles 2 --n 5

# Review results
cat ../report/overview.md

# Full analysis if satisfied with quick run
python run-analysis-harness.py --n 5
```

---

## run-single-cycle-analysis.py

**Purpose**: Run complete analysis pipeline for a single specific cycle in detail.

**What it does**:
1. Maps the complete basin for the specified cycle
2. Analyzes branch structure
3. Chases dominant upstream trunk
4. Finds preimages for cycle nodes
5. Optionally renders 3D tributary tree

**Usage**:

```bash
# Using cycle titles (recommended)
python run-single-cycle-analysis.py --n 5 \
  --cycle-title Massachusetts \
  --cycle-title "Gulf_of_Maine"

# Using page IDs
python run-single-cycle-analysis.py --n 5 \
  --cycle-page-id 1645518 \
  --cycle-page-id 714653

# With 3D visualization (slow but beautiful)
python run-single-cycle-analysis.py --n 5 \
  --cycle-title Massachusetts \
  --cycle-title "Gulf_of_Maine" \
  --render-3d

# Limit basin depth for speed
python run-single-cycle-analysis.py --n 5 \
  --cycle-title Autumn \
  --cycle-title Summer \
  --max-depth 20

# Custom tag and parameters
python run-single-cycle-analysis.py --n 5 \
  --cycle-title "Sea_salt" \
  --cycle-title Seawater \
  --tag seawater_deep_dive_2026-01-01 \
  --max-hops 50 \
  --top-k 100
```

**Parameters**:

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `--n` | int | 5 | N for N-link rule |
| `--cycle-title` | str | - | Cycle node title (repeatable, need 2) |
| `--cycle-page-id` | int | - | Cycle node page_id (repeatable, need 2) |
| `--tag` | str | single_cycle_YYYY-MM-DD | Tag for output files |
| `--max-depth` | int | 0 | Max basin depth (0 = unlimited) |
| `--max-hops` | int | 25 | Max dominant upstream chase hops |
| `--top-k` | int | 50 | Number of top branches to analyze |
| `--render-3d` | flag | false | Generate 3D tributary tree visualization |

**Scripts Run** (in order):

1. `map-basin-from-cycle.py` - Map complete basin
2. `branch-basin-analysis.py` - Quantify branch structure
3. `chase-dominant-upstream.py` - Chase dominant trunk (if title provided)
4. `find-nlink-preimages.py` - Find direct predecessors (if title provided)
5. `render-tributary-tree-3d.py` - 3D visualization (if --render-3d)

**Outputs**:
- Basin layers: `basin_n={N}_cycle={key}_{tag}_layers.tsv`
- Branches: `branches_n={N}_cycle={key}_{tag}_branches_all.tsv`
- Branch top-K: `branches_n={N}_cycle={key}_{tag}_branches_topk.tsv`
- Dominant chain: `dominant_upstream_chain_n={N}_from={title}.tsv`
- Preimages: `preimages_n={N}.tsv`
- 3D tree: `n-link-analysis/report/assets/tributary_tree_3d_*.html`

**Use Cases**:

1. **Deep-dive investigation**: Analyze a specific cycle in detail
2. **Custom parameters**: Use non-default depth limits or hop counts
3. **New cycle discovery**: Investigate a cycle you found via sampling
4. **Visualization**: Generate 3D tree for a specific cycle
5. **Incremental analysis**: Run just the steps you need for a single cycle

**Example Session**:

```bash
# 1. Sample to find interesting cycles
python sample-nlink-traces.py --n 5 --num 500 --resolve-titles

# 2. Analyze a specific cycle you found
python run-single-cycle-analysis.py --n 5 \
  --cycle-title "Your_Cycle" \
  --cycle-title "Other_Node" \
  --render-3d

# 3. View the 3D visualization
# Open n-link-analysis/report/assets/tributary_tree_3d_*.html in browser
```

---

## Comparison: When to Use Each Script

### Use `run-analysis-harness.py` when:
- You want to reproduce the main findings
- You're analyzing multiple cycles systematically
- You want dashboards and aggregated metrics
- You need a comprehensive report

### Use `run-single-cycle-analysis.py` when:
- You're investigating one specific cycle in detail
- You found an interesting cycle via sampling
- You want custom parameters for a single cycle
- You need a 3D visualization for a specific case

### Use `reproduce-main-findings.py` when:
- You want the canonical reproduction pipeline
- You're validating the analysis after code changes
- You want the exact same cycles as the original investigation

---

## Performance Notes

### Quick Mode
- **Runtime**: 30-60 minutes (6 cycles, reduced samples)
- **Cycles**: First 6 known cycles
- **Samples**: 100 traces, 50 path characteristics
- **Chase hops**: 20
- **Basin depth**: Limited to 30 for first cycle

### Full Mode
- **Runtime**: 2-4 hours (9 cycles, full samples)
- **Cycles**: All 9 known cycles
- **Samples**: 500 traces, 200 path characteristics
- **Chase hops**: 40
- **Basin depth**: Unlimited (exhaustive)

### Single Cycle
- **Runtime**: 5-30 minutes per cycle (depends on basin size)
- **Massachusetts**: ~10 minutes (1M nodes)
- **Autumn ↔ Summer**: ~2 minutes (smaller basin)
- **3D rendering**: +5-10 minutes (if --render-3d)

---

## Troubleshooting

### "Could not resolve titles"
- Check spelling: titles must match Wikipedia exactly
- Use underscores for spaces: `Gulf_of_Maine` not `Gulf of Maine`
- Try `--allow-redirects` if the title might be a redirect

### "Missing: edges_n={N}.duckdb"
- The database is created by `map-basin-from-cycle.py`
- If harness fails early, the DB might not exist yet
- Run `map-basin-from-cycle.py` manually for one cycle first

### Out of memory
- Use `--quick` mode
- Use `--max-depth 20` to limit basin depth
- Reduce `--max-cycles` to analyze fewer cycles

### Scripts taking too long
- Use `--quick` mode
- Reduce `--max-hops` for dominant chases
- Skip 3D rendering (it's slow)
- Use `--max-depth` to limit basin expansion

---

## Related Documentation

- [scripts-reference.md](scripts-reference.md) - Detailed reference for all individual scripts
- [INDEX.md](../INDEX.md) - N-link analysis directory overview
- [implementation.md](../implementation.md) - Analysis architecture
- [report/overview.md](../report/overview.md) - Human-facing summary report

---

**Last Updated**: 2026-01-01
