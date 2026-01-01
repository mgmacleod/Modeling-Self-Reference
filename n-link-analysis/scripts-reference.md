# N-Link Analysis Scripts Reference

**Document Type**: Reference
**Target Audience**: LLMs + Developers
**Purpose**: Comprehensive documentation of all analysis scripts - functionality, inputs, outputs, parameters, and theory connections
**Last Updated**: 2026-01-01
**Dependencies**: [implementation.md](implementation.md), [../llm-facing-documentation/theories-proofs-conjectures/n-link-rule-theory.md](../llm-facing-documentation/theories-proofs-conjectures/n-link-rule-theory.md)
**Status**: Active

---

## Overview

This document provides complete reference documentation for all scripts in [scripts/](scripts/). Scripts are organized by their role in the analysis pipeline:

1. **Validation & Exploration**: Single-path traces, random sampling
2. **Basin Construction**: Reverse expansion, preimage computation
3. **Geometry Quantification**: Branch structure, dominant trunk chasing
4. **Aggregation & Metrics**: Dashboards, concentration metrics
5. **Visualization**: 3D trees, reports
6. **Utilities**: Data validation, compatibility shims

**Data Flow Summary**:
```
Wikipedia dump → nlink_sequences.parquet, pages.parquet
                      ↓
    [map-basin-from-cycle.py] → edges_n={N}.duckdb (persistent)
                      ↓
         ┌────────────┴────────────┐
         ↓                          ↓
[branch-basin-analysis.py]  [chase-dominant-upstream.py]
         ↓                          ↓
 branches_*.tsv            dominant_upstream_chain_*.tsv
         ↓                          ↓
         └────────────┬─────────────┘
                      ↓
    [compute-trunkiness-dashboard.py] → trunkiness_dashboard.tsv
                      ↓
    [batch-chase-collapse-metrics.py] → collapse_dashboard.tsv
                      ↓
    [render-human-report.py] → overview.md + PNG charts
    [render-tributary-tree-3d.py] → HTML 3D visualization
```

---

## Reproduction Script

### reproduce-main-findings.py

**Purpose**: Execute the complete analysis pipeline to reproduce all main empirical findings from the project.

**What It Does**:
This is a **meta-script** that orchestrates the execution of multiple analysis scripts in the correct order to reproduce the three main findings:

1. **Heavy-tail basin size distribution** with giant basin candidate (Massachusetts ↔ Gulf_of_Maine: 1M+ nodes)
2. **Single-trunk structure** in many basins (top-1 branch captures >95% of upstream mass)
3. **Dominance collapse patterns** (stable trunks diffuse within 5-20 hops)

**Pipeline Phases**:
1. **Sampling** → Identify frequent terminal cycles (sample-nlink-traces.py)
2. **Basin Mapping** → Compute basin sizes via reverse BFS (map-basin-from-cycle.py)
3. **Branch Analysis** → Quantify tributary structure (branch-basin-analysis.py)
4. **Dashboards** → Aggregate concentration metrics (compute-trunkiness-dashboard.py, batch-chase-collapse-metrics.py)
5. **Report** → Generate human-facing summary with charts (render-human-report.py)

**Usage**:
```bash
# Quick mode (~10-30 minutes, reduced samples)
python n-link-analysis/scripts/reproduce-main-findings.py --quick

# Full reproduction (~2-6 hours, matches original investigation)
python n-link-analysis/scripts/reproduce-main-findings.py

# Custom N-link rule
python n-link-analysis/scripts/reproduce-main-findings.py --n 7

# Resume partial run (skip completed phases)
python n-link-analysis/scripts/reproduce-main-findings.py --skip-sampling --skip-basins
```

**Parameters**:
| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `--quick` | flag | false | Quick mode with reduced sample sizes (500 vs 5000 samples) |
| `--n` | int | 5 | N for N-link rule |
| `--tag` | str | reproduction_YYYY-MM-DD | Tag for output files |
| `--skip-sampling` | flag | false | Skip sampling phase (if already done) |
| `--skip-basins` | flag | false | Skip basin mapping phase |
| `--skip-branches` | flag | false | Skip branch analysis phase |
| `--skip-dashboards` | flag | false | Skip dashboard generation phase |
| `--skip-report` | flag | false | Skip report generation phase |

**Cycles Analyzed**:

Quick mode (6 cycles):
- Massachusetts ↔ Gulf_of_Maine (giant basin)
- Sea_salt ↔ Seawater (large basin)
- Mountain ↔ Hill (large basin)
- Autumn ↔ Summer (high trunkiness)
- Kingdom_(biology) ↔ Animal (low trunkiness contrast)
- Latvia ↔ Lithuania (medium basin)

Full mode (9 cycles, adds):
- Thermosetting_polymer ↔ Curing_(chemistry) (highest trunkiness)
- Precedent ↔ Civil_law (medium trunkiness)
- American_Revolutionary_War ↔ Eastern_United_States (low trunkiness)

**Outputs**:
- All analysis artifacts written to `data/wikipedia/processed/analysis/`
- Human-facing report: `n-link-analysis/report/overview.md`
- Trunkiness dashboard: `branch_trunkiness_dashboard_n={N}_{tag}.tsv`
- Collapse dashboard: `dominance_collapse_dashboard_n={N}_{tag}_seed=dominant_enters_cycle_title_thr=0.5.tsv`

**Expected Runtime**:
- **Quick mode**: 10-30 minutes (reduced samples, 6 cycles)
- **Full mode**: 2-6 hours (complete reproduction, 9 cycles)
- Runtime varies based on hardware (CPU cores, RAM, disk I/O)

**Use Cases**:
- **Onboarding**: Reproduce main findings to understand the project
- **Validation**: Verify analysis pipeline after code changes
- **Extension**: Use as template for investigating different N values
- **Comparison**: Generate new results with updated Wikipedia dumps

**Example Session**:
```bash
# 1. Validate data
python n-link-analysis/scripts/validate-data-dependencies.py

# 2. Quick reproduction (recommended first time)
python n-link-analysis/scripts/reproduce-main-findings.py --quick

# 3. Review results
cat n-link-analysis/report/overview.md

# 4. Full reproduction (if quick results look good)
python n-link-analysis/scripts/reproduce-main-findings.py

# 5. Explore specific basin interactively
python n-link-analysis/scripts/render-tributary-tree-3d.py \
  --n 5 --cycle-title Massachusetts --cycle-title Gulf_of_Maine
```

**Theory Connection**:
This script empirically validates the core predictions of N-Link Rule Theory:
- Basin partitioning theorem (all pages partition into basins)
- Terminal cycle concentration (some cycles attract large basins)
- Tributary structure (basins exhibit hierarchical geometry)

---

## Common Patterns Across All Scripts

### Data Inputs
- **Primary**: `data/wikipedia/processed/nlink_sequences.parquet` (page_id, link_sequence)
- **Secondary**: `data/wikipedia/processed/pages.parquet` (page_id, title, namespace, is_redirect)
- **Analysis DB**: `data/wikipedia/processed/analysis/edges_n={N}.duckdb` (created by map-basin-from-cycle.py)

### Output Directory
- `data/wikipedia/processed/analysis/` (gitignored)

### Title Resolution
Most scripts support:
- `--namespace N`: Filter to namespace (default: 0 = main articles)
- `--allow-redirects`: Allow redirect pages (default: false)

### Common Parameters
- `--n N`: N-link rule index (1-indexed; default varies by script)
- `--max-depth D`: Reverse expansion depth limit (0 = unlimited)
- `--tag TAG`: Organize multiple analysis runs

---

## Validation & Exploration Scripts

### trace-nlink-path.py

**Purpose**: Trace a single N-link path from a starting page (sanity check / manual exploration).

**Theory Connection**: Validates that f_N produces deterministic paths terminating in HALT or CYCLE states.

**Algorithm**:
1. Load successor arrays: `succ[page_id] = link_sequence[N-1]` for all pages with ≥N links
2. Starting from seed page, follow f_N iteratively: `page := succ[page]`
3. Detect termination: HALT (no successor), CYCLE (revisited node), or MAX_STEPS

**Usage**:
```bash
python n-link-analysis/scripts/trace-nlink-path.py \
  --n 5 \
  --start-page-id 12345 \
  [--min-outdegree 50] \
  [--seed 0] \
  [--max-steps 5000] \
  [--print-max 200] \
  [--no-save]
```

**Parameters**:
| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `--n` | int | 5 | N for N-link rule (1-indexed) |
| `--start-page-id` | int | auto | Explicit starting page_id (if omitted, random selection) |
| `--min-outdegree` | int | 50 | Minimum out-degree for auto-selected start pages |
| `--seed` | int | 0 | RNG seed for reproducible random start selection |
| `--max-steps` | int | 5000 | Maximum path steps before stopping |
| `--print-max` | int | 200 | Maximum rows to print to console |
| `--no-save` | flag | false | Don't write output file |

**Inputs**:
- `data/wikipedia/processed/nlink_sequences.parquet`
- `data/wikipedia/processed/pages.parquet`

**Outputs**:
- **File**: `data/wikipedia/processed/analysis/trace_n={N}_start={page_id}.tsv`
- **Columns**: `step` (int), `page_id` (int), `title` (str)
- **Console**: Summary with terminal type (HALT/CYCLE), cycle info, path preview

**Example Output** (console):
```
Terminal type: CYCLE
Cycle: [Philosophy, Existence, Reality, Philosophy]
Steps to terminal: 42
Total path length: 45
```

---

### sample-nlink-traces.py

**Purpose**: Sample many random N-link traces to quantify terminal statistics without full basin decomposition.

**Theory Connection**: Empirically validates basin partitioning theorem by measuring frequency of cycles vs. HALTs and identifying dominant attractors.

**Algorithm**:
1. Load successor arrays for fixed N
2. Draw `num` random starting pages (with out-degree ≥ min_outdegree)
3. Trace each to termination (HALT/CYCLE)
4. Canonicalize cycles (rotate to lexicographic minimum) for frequency counting
5. Aggregate: terminal type distribution, top-K cycles by frequency

**Usage**:
```bash
python n-link-analysis/scripts/sample-nlink-traces.py \
  --n 5 \
  --num 1000 \
  [--seed0 0] \
  [--min-outdegree 50] \
  [--max-steps 5000] \
  [--top-cycles 10] \
  [--resolve-titles] \
  [--out path/to/output.tsv]
```

**Parameters**:
| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `--n` | int | 5 | N for N-link rule |
| `--num` | int | 100 | Number of random samples |
| `--seed0` | int | 0 | First RNG seed (incremented per sample) |
| `--min-outdegree` | int | 50 | Minimum out-degree filter |
| `--max-steps` | int | 5000 | Steps before giving up on a trace |
| `--top-cycles` | int | 10 | Number of top cycles to report |
| `--resolve-titles` | flag | false | Resolve titles for cycle nodes (slower) |
| `--out` | path | auto | Optional custom output path |

**Inputs**:
- `data/wikipedia/processed/nlink_sequences.parquet`
- `data/wikipedia/processed/pages.parquet` (if --resolve-titles)

**Outputs**:
- **File**: `data/wikipedia/processed/analysis/sample_traces_n={N}_num={num}_seed0={seed}.tsv`
- **Columns**: `seed` (int), `start_page_id` (int), `terminal_type` (str), `steps` (int), `path_len` (int), `transient_len` (int), `cycle_len` (int)
- **Console**: Terminal counts (HALT/CYCLE), top-K frequent cycles with titles

**Example Output** (console):
```
Terminal distribution:
  HALT: 234 (23.4%)
  CYCLE: 766 (76.6%)

Top 10 cycles by frequency:
  1. [Philosophy → Existence → Reality] (342 occurrences)
  2. [Science → Knowledge] (89 occurrences)
  ...
```

---

## Basin Construction Scripts

### find-nlink-preimages.py

**Purpose**: Find all pages whose Nth link points to a target page (reverse mapping: compute f_N^{-1}(target)).

**Theory Connection**: Fundamental for reverse basin analysis - identifies immediate predecessors (depth-1) in basin construction.

**Algorithm**:
1. Scan `nlink_sequences.parquet` for edges where `link_sequence[N-1] = target_page_id`
2. Compute true preimage counts (in-degree under f_N)
3. Optionally resolve source titles and limit output rows

**Usage**:
```bash
python n-link-analysis/scripts/find-nlink-preimages.py \
  --n 5 \
  --target-page-id 12345 \
  [--target-title "Philosophy"] \
  [--namespace 0] \
  [--allow-redirects] \
  [--resolve-source-titles] \
  [--out path/to/output.tsv] \
  [--limit 1000]
```

**Parameters**:
| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `--n` | int | 5 | N for N-link rule |
| `--target-page-id` | int | - | Target page_id (repeatable) |
| `--target-title` | str | - | Target title (repeatable) |
| `--namespace` | int | 0 | Namespace for title resolution |
| `--allow-redirects` | flag | false | Allow redirect targets |
| `--resolve-source-titles` | flag | false | Resolve titles for source pages (slower) |
| `--out` | path | auto | Optional custom output path |
| `--limit` | int | 0 | Limit rows per target (0 = unlimited) |

**Inputs**:
- `data/wikipedia/processed/nlink_sequences.parquet`
- `data/wikipedia/processed/pages.parquet` (for title resolution)

**Outputs**:
- **File**: `data/wikipedia/processed/analysis/preimages_n={N}.tsv`
- **Columns**: `target_page_id` (int), `src_page_id` (int), `src_title` (str, optional)
- **Console**: In-degree counts per target

**Example Output** (console):
```
Target: Philosophy (page_id=5043)
  In-degree: 1,847 pages
  Sample preimages: [Existence, Metaphysics, Epistemology, ...]
```

---

### map-basin-from-cycle.py

**Purpose**: Map the complete reverse basin (ancestor set) feeding a given cycle under f_N.

**Theory Connection**: Direct implementation of basin construction theorem - computes reverse-reachable set from terminal cycle.

**Algorithm** (Reverse BFS with deduplication):
1. Materialize edges table in DuckDB: `(src_page_id, dst_page_id)` for N-link rule
2. Initialize: `frontier_0 := cycle_nodes`, `seen := cycle_nodes`
3. For each depth d:
   - `frontier_{d+1} := {src : (src → dst) ∧ dst ∈ frontier_d ∧ src ∉ seen}`
   - `seen := seen ∪ frontier_{d+1}`
4. Stop when: `frontier` empty, `max_depth` reached, or `max_nodes` discovered
5. Write layer-by-layer growth statistics

**Usage**:
```bash
python n-link-analysis/scripts/map-basin-from-cycle.py \
  --n 5 \
  --cycle-page-id 5043 \
  --cycle-page-id 38255 \
  [--cycle-title "Philosophy"] \
  [--max-depth 25] \
  [--max-nodes 1000000] \
  [--write-membership] \
  [--log-every 1] \
  [--out-prefix custom_name]
```

**Parameters**:
| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `--n` | int | 5 | N for N-link rule |
| `--cycle-page-id` | int | - | Cycle node page_id (repeatable, required) |
| `--cycle-title` | str | - | Cycle node title (repeatable, alternative to page_id) |
| `--namespace` | int | 0 | Namespace for title resolution |
| `--allow-redirects` | flag | false | Allow redirect resolution |
| `--max-depth` | int | 25 | Stop after N layers (0 = unlimited) |
| `--log-every` | int | 1 | Print progress every N layers |
| `--max-nodes` | int | 0 | Stop after discovering N nodes (0 = unlimited) |
| `--write-membership` | flag | false | Write full node set to Parquet |
| `--out-prefix` | str | auto | Output filename prefix |

**Inputs**:
- `data/wikipedia/processed/nlink_sequences.parquet`
- `data/wikipedia/processed/pages.parquet`

**Outputs**:
- **Database**: `data/wikipedia/processed/analysis/edges_n={N}.duckdb` (persistent, reused by other scripts)
- **File**: `data/wikipedia/processed/analysis/basin_from_cycle_n={N}_layers.tsv`
  - **Columns**: `depth` (int), `nodes_at_depth` (int), `cumulative_nodes` (int)
- **Optional**: `basin_from_cycle_n={N}_members.parquet` (if --write-membership)
  - **Columns**: `page_id` (int), `depth` (int)
- **Console**: Layer-by-layer progress, cycle successor verification

**Example Output** (console):
```
Cycle: [Philosophy, Existence, Reality]
Layer 0: 3 nodes (cycle)
Layer 1: 1,847 nodes (direct predecessors)
Layer 2: 12,394 nodes
Layer 3: 45,821 nodes
...
Total basin size: 2,394,847 nodes
```

**Performance Notes**:
- First run creates `edges_n={N}.duckdb` (~30 seconds for N=5)
- Subsequent runs reuse the database (fast)
- Memory scales with basin size; use `--max-nodes` for safety

---

## Geometry Quantification Scripts

### branch-basin-analysis.py

**Purpose**: Quantify "branch" (tributary) structure feeding a terminal cycle - measures concentration into distinct entry branches.

**Theory Connection**: Operationalizes "tributary tree" structure - validates predictions about basin geometry (concentration vs. diffusion).

**Algorithm** (Reverse BFS with label propagation):
1. Reuse `edges_n={N}.duckdb` from map-basin-from-cycle.py
2. Initialize: `depth_0 := cycle_nodes` (entry_id = NULL)
3. Reverse expansion with branch tracking:
   - Depth 1: `entry_id := src_page_id` (these are "entry branches")
   - Depth >1: `entry_id := parent's entry_id` (propagate branch membership)
4. Group by `entry_id` to compute branch sizes
5. Rank branches by size; report top-K with titles

**Usage**:
```bash
python n-link-analysis/scripts/branch-basin-analysis.py \
  --n 5 \
  --cycle-page-id 5043 \
  --cycle-page-id 38255 \
  [--cycle-title "Philosophy"] \
  [--max-depth 0] \
  [--top-k 25] \
  [--write-membership-top-k 10] \
  [--log-every 10] \
  [--out-prefix custom_name]
```

**Parameters**:
| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `--n` | int | 5 | N for N-link rule |
| `--cycle-page-id` | int | - | Cycle node page_id (repeatable) |
| `--cycle-title` | str | - | Cycle node title (repeatable) |
| `--namespace` | int | 0 | Namespace for title resolution |
| `--allow-redirects` | flag | false | Allow redirect resolution |
| `--max-depth` | int | 0 | Reverse expansion depth cap (0 = unlimited) |
| `--log-every` | int | 10 | Progress logging frequency (layers) |
| `--top-k` | int | 25 | Report top-K branches |
| `--write-membership-top-k` | int | 0 | Write membership for top-K branches (0 = none) |
| `--out-prefix` | str | auto | Output filename prefix |

**Inputs**:
- `data/wikipedia/processed/analysis/edges_n={N}.duckdb` (must exist; run map-basin-from-cycle.py first)
- `data/wikipedia/processed/pages.parquet`

**Outputs**:
- **Files**:
  1. `data/wikipedia/processed/analysis/branches_from_cycle_n={N}_branches_all.tsv`
     - **Columns**: `rank`, `entry_id`, `basin_size`, `max_depth`, `enters_cycle_page_id`
  2. `branches_from_cycle_n={N}_branches_topk.tsv`
     - **Additional columns**: `entry_title`, `enters_cycle_title`
  3. `branches_from_cycle_n={N}_assignments.parquet` (optional, if --write-membership-top-k > 0)
     - **Columns**: `page_id`, `entry_id`, `depth`
- **Console**: Top-K branches with sizes and entry points

**Example Output** (console):
```
Total basin: 2,394,847 nodes
Total branches: 1,847

Top 10 branches:
  1. Existence → Philosophy: 847,293 nodes (35.4%)
  2. Metaphysics → Philosophy: 234,891 nodes (9.8%)
  3. Epistemology → Philosophy: 189,234 nodes (7.9%)
  ...
```

**Use Cases**:
- Measure concentration: is one branch dominant?
- Identify semantic themes: what topics feed the cycle?
- Validate theory: do basins have trunk-like structure?

---

### chase-dominant-upstream.py

**Purpose**: Iteratively follow the dominant (thickest) upstream branch to identify the "main trunk" - traces the "source of the Nile."

**Theory Connection**: Tests hypothesis that basins have "trunk-like" structure with concentration of mass along dominant paths. Measures where/how dominance collapses.

**Algorithm**:
1. For current seed, compute all entry branch sizes (using branch-basin-analysis logic)
2. Select dominant entry: `argmax(branch_size)`
3. Compute `dominance_share := dominant_size / (total_upstream - 1)`
4. Set `seed := dominant_entry`
5. Repeat until: no predecessors, cycle detected, max_hops, or dominance_share < threshold

**Usage**:
```bash
python n-link-analysis/scripts/chase-dominant-upstream.py \
  --n 5 \
  --seed-title "Philosophy" \
  [--max-hops 25] \
  [--max-depth 0] \
  [--dominance-threshold 0.5] \
  [--log-every 0] \
  [--namespace 0] \
  [--allow-redirects] \
  [--out path/to/output.tsv]
```

**Parameters**:
| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `--n` | int | 5 | N for N-link rule |
| `--seed-title` | str | required | Starting title |
| `--namespace` | int | 0 | Namespace for title resolution |
| `--allow-redirects` | flag | false | Allow redirect resolution |
| `--max-hops` | int | 25 | Maximum chase iterations |
| `--max-depth` | int | 0 | Reverse depth per hop (0 = unlimited) |
| `--log-every` | int | 0 | Logging frequency within each hop (0 = quiet) |
| `--dominance-threshold` | float | 0 | Stop if share < threshold (0 = disabled) |
| `--out` | path | auto | Optional custom output path |

**Inputs**:
- `data/wikipedia/processed/analysis/edges_n={N}.duckdb` (must exist)
- `data/wikipedia/processed/pages.parquet`

**Outputs**:
- **File**: `data/wikipedia/processed/analysis/dominant_upstream_chain_n={N}_from={seed}.tsv`
- **Columns**:
  - `hop` (int): Iteration number
  - `seed_page_id` (int): Current seed page_id
  - `seed_title` (str): Current seed title
  - `basin_total_including_seed` (int): Total upstream basin size
  - `dominant_entry_page_id` (int): Dominant branch entry page_id
  - `dominant_entry_title` (str): Dominant branch entry title
  - `dominant_entry_size` (int): Dominant branch size
  - `dominant_share_of_upstream` (float): Fraction of upstream in dominant branch

**Example Output** (TSV excerpt):
```
hop  seed_title       basin_total  dominant_entry_title  dominant_share
0    Philosophy       2394847      Existence             0.354
1    Existence        1547554      Being                 0.421
2    Being            1093394      Entity                0.389
3    Entity           704001       Object                0.287  ← collapse?
4    Object           502394       Thing                 0.192  ← diffuse
```

**Interpretation**:
- High `dominant_share` (>0.3): Strong trunk structure
- Declining `dominant_share`: Approaching diffuse region
- Threshold crossing: Identifies "collapse point"

---

## Aggregation & Metrics Scripts

### compute-trunkiness-dashboard.py

**Purpose**: Compute summary concentration metrics (Gini, HH index, entropy, effective branches) from branch-basin-analysis outputs.

**Theory Connection**: Quantifies basin geometry predictions - are basins "single-trunk" (high top1_share, low effective_branches) or diffuse (low Gini, high entropy)?

**Algorithm**:
1. Read all `branches_n={N}_cycle=*_branches_all.tsv` files (filtered by --n parameter)
2. For each cycle, compute:
   - **Gini coefficient**: Inequality measure (0 = perfect equality, 1 = one branch has all mass)
   - **Herfindahl-Hirschman index (HH)**: Sum of squared shares → effective branches = 1/HH
   - **Normalized Shannon entropy**: Randomness measure (0 = single branch, 1 = uniform)
   - **Top-K shares**: Cumulative share of top 1, 5, 10 branches
3. Join with topk files to add titles for dominant entries
4. Write consolidated dashboard TSV

**Usage**:
```bash
python n-link-analysis/scripts/compute-trunkiness-dashboard.py \
  [--n 5] \
  [--analysis-dir data/wikipedia/processed/analysis] \
  [--tag bootstrap_2025-12-30]
```

**Parameters**:
| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `--n` | int | 5 | N value for N-link rule (filters which branch files to process) |
| `--analysis-dir` | path | data/wikipedia/processed/analysis | Directory with branch outputs |
| `--tag` | str | bootstrap_2025-12-30 | Tag for output filename |

**Inputs**:
- `data/wikipedia/processed/analysis/branches_n={N}_cycle=*_branches_all.tsv` (filtered by --n)
- `data/wikipedia/processed/analysis/branches_n={N}_cycle=*_branches_topk.tsv` (filtered by --n)

**Outputs**:
- **File**: `data/wikipedia/processed/analysis/branch_trunkiness_dashboard_n={N}_{tag}.tsv`
- **Columns**:
  - `cycle_key` (str): Canonical cycle identifier
  - `cycle_len` (int): Cycle length
  - `total_basin_nodes` (int): Total basin size
  - `n_branches` (int): Number of distinct entry branches
  - `top1_branch_size` (int): Largest branch size
  - `top1_share_total` (float): Fraction of basin in largest branch
  - `top5_share_total` (float): Cumulative share of top 5 branches
  - `top10_share_total` (float): Cumulative share of top 10 branches
  - `effective_branches` (float): 1 / HH index
  - `gini_branch_sizes` (float): Gini coefficient [0, 1]
  - `entropy_norm` (float): Normalized Shannon entropy [0, 1]
  - `dominant_entry_title` (str): Title of largest entry branch
  - `dominant_enters_cycle_title` (str): Cycle node the dominant branch enters
  - `dominant_max_depth` (int): Maximum depth in dominant branch
  - `branches_all_path` (str): Path to source branches_all.tsv file

**Example Output** (TSV excerpt):
```
cycle_key                  top1_share  effective_branches  gini   entropy_norm  dominant_entry_title
Philosophy__Existence      0.354       4.2                 0.73   0.42          Existence
Science__Knowledge         0.621       2.1                 0.85   0.28          Scientific_method
United_States__Country     0.189       12.7                0.51   0.68          Nation
```

**Interpretation**:
- **High top1_share, low effective_branches, high Gini**: Strong trunk (e.g., Philosophy)
- **Low top1_share, high effective_branches, low Gini**: Diffuse (e.g., United_States)
- **Moderate values**: Hybrid structure

---

### batch-chase-collapse-metrics.py

**Purpose**: Batch-run dominant-upstream chases and measure where dominance "collapses" below a threshold.

**Theory Connection**: Tests whether high-dominance regions are stable or collapse upstream. Measures extent of "trunk" before diffusion dominates.

**Algorithm**:
1. Read trunkiness dashboard TSV
2. For each row, extract seed title (from cycle, dominant entry, or cycle nodes)
3. Run chase-dominant-upstream logic until:
   - `dominance_share < threshold`, OR
   - No predecessors, OR
   - Max hops reached
4. Record: `first_below_threshold_hop`, `min_share`, `stop_reason`, `stop_at_title`

**Usage**:
```bash
python n-link-analysis/scripts/batch-chase-collapse-metrics.py \
  --n 5 \
  --dashboard path/to/trunkiness_dashboard.tsv \
  [--seed-from dominant_enters_cycle_title] \
  [--max-hops 40] \
  [--max-depth 0] \
  [--dominance-threshold 0.5] \
  [--namespace 0] \
  [--allow-redirects] \
  [--tag bootstrap_2025-12-30]
```

**Parameters**:
| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `--n` | int | 5 | N for N-link rule |
| `--dashboard` | path | required | Input trunkiness dashboard TSV path |
| `--seed-from` | choice | dominant_enters_cycle_title | Which field to use as seed (dominant_enters_cycle_title, cycle_first, cycle_second) |
| `--namespace` | int | 0 | Namespace for title resolution |
| `--allow-redirects` | flag | false | Allow redirect resolution |
| `--max-hops` | int | 40 | Maximum chase iterations |
| `--max-depth` | int | 0 | Reverse depth per hop (0 = unlimited) |
| `--dominance-threshold` | float | 0.5 | Stop when share < threshold (0 = disabled) |
| `--tag` | str | bootstrap_2025-12-30 | Output tag |

**Inputs**:
- Trunkiness dashboard TSV (from compute-trunkiness-dashboard.py)
- `data/wikipedia/processed/analysis/edges_n={N}.duckdb`
- `data/wikipedia/processed/pages.parquet`

**Outputs**:
- **File**: `data/wikipedia/processed/analysis/dominance_collapse_dashboard_n={N}_{tag}.tsv`
- **Columns**:
  - `seed_title` (str): Starting title
  - `resolved` (bool): Whether seed title resolved to page_id
  - `hops_executed` (int): Number of chase hops completed
  - `min_share` (float): Minimum dominance share observed
  - `first_below_threshold_hop` (int or empty): First hop where share < threshold
  - `stop_reason` (str): Reason for stopping (share_below_{threshold}, no_predecessors, max_hops)
  - `stop_at_title` (str): Final title reached

**Example Output** (TSV excerpt):
```
seed_title     resolved  hops_executed  min_share  first_below_threshold_hop  stop_reason          stop_at_title
Existence      true      5              0.287      3                          share_below_0.5      Object
Science        true      12             0.421      -                          no_predecessors      -
United_States  true      2              0.189      0                          share_below_0.5      United_States
```

**Interpretation**:
- **Large hops_executed, late collapse**: Stable trunk
- **Early collapse**: Diffuse basin structure
- **no_predecessors before collapse**: Reached HALT or isolated node

---

## Visualization Scripts

### render-tributary-tree-3d.py

**Purpose**: Render a 3D interactive visualization of basin summary as a hierarchical tributary tree.

**Theory Connection**: Visualizes basin geometry as hierarchical tributary structure. Makes "river network" metaphor concrete and inspectable.

**Algorithm**:
1. Start from terminal cycle (level 0)
2. For each target set at level L:
   - Compute top-K entry branches (using branch-basin-analysis logic)
   - Add edges: `entry → cycle_node`
   - Treat top-K entries as new targets for level L+1
3. Build directed graph (entry → target edges) with branch sizes as node weights
4. Use NetworkX spring layout in 3D for positioning
5. Render with Plotly: nodes sized by basin, edges colored by level, hover shows titles

**Usage**:
```bash
python n-link-analysis/scripts/render-tributary-tree-3d.py \
  --n 5 \
  --cycle-title "Philosophy" \
  --cycle-title "Existence" \
  [--top-k 5] \
  [--max-levels 5] \
  [--max-depth 12] \
  [--namespace 0] \
  [--allow-redirects] \
  [--out path/to/output.html]
```

**Parameters**:
| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `--n` | int | 5 | N for N-link rule |
| `--cycle-title` | str | required | Terminal cycle titles (repeatable) |
| `--namespace` | int | 0 | Namespace for title resolution |
| `--allow-redirects` | flag | false | Allow redirect resolution |
| `--top-k` | int | 5 | Top-K branches per level (branching factor) |
| `--max-levels` | int | 5 | Maximum tree depth |
| `--max-depth` | int | 12 | Reverse expansion cap per level |
| `--out` | path | auto | Optional custom output HTML path |

**Inputs**:
- `data/wikipedia/processed/analysis/edges_n={N}.duckdb`
- `data/wikipedia/processed/pages.parquet`

**Outputs**:
- **File**: `n-link-analysis/report/assets/tributary_tree_3d_n={N}_cycle={titles}_k={k}_levels={levels}_depth={depth}.html`
- **Sidecar**: JSON file with nodes/edges for debugging
- **Format**: Interactive 3D HTML with Plotly (pan, zoom, rotate, hover)

**Example Interaction**:
- **Nodes**: Sized by basin size, colored by level
- **Edges**: Directed from entry to target, colored by level
- **Hover**: Shows title, basin size, level
- **Rotation**: 3D perspective reveals hierarchical structure

**Performance Notes**:
- Computational cost: O(top_k^max_levels) basin expansions
- Recommended limits: `top_k ≤ 5`, `max_levels ≤ 5`, `max_depth ≤ 15`
- High-degree cycles may have long render times

---

### render-human-report.py

**Purpose**: Generate human-facing Markdown report with charts from analysis TSV artifacts.

**Theory Connection**: Communicates empirical findings to humans - validates/refutes theoretical predictions about basin structure.

**Algorithm**:
1. Read trunkiness and collapse dashboards
2. Generate matplotlib charts:
   - Bar plot: Top-N cycles by basin size
   - Scatter: Gini vs. effective branches (geometric classification)
   - Line overlay: Dominant share vs. hop for multiple chases
3. Save charts as PNG in `report/assets/`
4. Render Markdown with embedded image references
5. Write to `n-link-analysis/report/overview.md`

**Usage**:
```bash
python n-link-analysis/scripts/render-human-report.py \
  [--tag bootstrap_2025-12-30]
```

**Parameters**:
| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `--tag` | str | bootstrap_2025-12-30 | Preferred dashboard tag to use |

**Inputs**:
- `data/wikipedia/processed/analysis/branch_trunkiness_dashboard_n=5_*.tsv`
- `data/wikipedia/processed/analysis/dominance_collapse_dashboard_n=5_*.tsv`
- `data/wikipedia/processed/analysis/dominant_upstream_chain_n=5_from=*.tsv`

**Outputs**:
- **File**: `n-link-analysis/report/overview.md` (human-facing summary)
- **Assets**: `n-link-analysis/report/assets/*.png` (charts)

**Generated Charts**:
1. **Basin size distribution**: Bar chart of top cycles
2. **Geometry classification**: Scatter plot (Gini vs. effective branches)
3. **Dominance decay**: Line plots of share vs. hop for selected chases
4. **Top-K share distribution**: Histogram or boxplot

**Use Cases**:
- Share findings with collaborators
- Validate theory predictions visually
- Identify outliers or unexpected patterns

---

## Utility Scripts

### dash-tributary-viewer.py

**Purpose**: Compatibility shim redirecting to [n-link-analysis/viz/dash-basin-geometry-viewer.py](../viz/dash-basin-geometry-viewer.py).

**Status**: Active (maintains backward compatibility)

**Algorithm**: Uses `runpy.run_path()` to execute the new location.

**Usage**:
```bash
python n-link-analysis/scripts/dash-tributary-viewer.py
# Equivalent to:
python n-link-analysis/viz/dash-basin-geometry-viewer.py
```

**Outputs**: None (delegates to target script)

---

### quick-queries.py

**Purpose**: Quick DuckDB sanity checks for analysis inputs/outputs.

**Status**: Placeholder (not yet implemented)

**Planned Functionality**:
- Verify `nlink_sequences.parquet` schema
- Print row counts and basic stats
- Check for NULL values or malformed data
- Validate edges_n={N}.duckdb schema

**Usage** (planned):
```bash
python n-link-analysis/scripts/quick-queries.py \
  [--n 5]
```

**Implementation Status**: Raises `NotImplementedError`

---

### compute-basin-stats.py

**Purpose**: Compute global basin/terminal statistics for fixed N-link rules.

**Status**: Placeholder (not yet implemented)

**Planned Functionality**:
- For each N in a configured set, build f_N
- Trace all pages to termination (HALT or CYCLE)
- Compute per-terminal metrics: terminal_id, type, basin_size, cycle_length
- Write per-N summary stats: P_HALT, num_terminals, largest_basin, etc.

**Theory Connection**: Global basin decomposition - would validate theorem that finite graphs partition into basins.

**Usage** (planned):
```bash
python n-link-analysis/scripts/compute-basin-stats.py \
  --n 5 \
  [--out-dir data/wikipedia/processed/analysis]
```

**Outputs** (planned):
- `basin_stats_N={N}.parquet`: Per-terminal metrics
- `summary_over_N.parquet`: One row per N with aggregates

**Implementation Status**: Raises `NotImplementedError`

---

### compute-universal-attractors.py

**Purpose**: Aggregate terminals across N to identify universal attractors (pages that are attractors for many N values).

**Status**: Placeholder (not yet implemented)

**Planned Functionality**:
- Read per-N terminal outputs from compute-basin-stats.py
- Compute terminal frequency across N values: `freq[page_id] := |{N : page_id is a terminal for N}|`
- Identify pages with high cross-N frequency
- Test multi-rule tunneling hypothesis

**Theory Connection**: Tests multi-rule tunneling hypothesis - do certain pages act as semantic "sinks" across rule changes?

**Usage** (planned):
```bash
python n-link-analysis/scripts/compute-universal-attractors.py \
  --analysis-dir data/wikipedia/processed/analysis \
  [--out universal_attractors.parquet]
```

**Outputs** (planned):
- `universal_attractors.parquet`: Columns: `page_id`, `title`, `n_values_count`, `basin_sizes` (list)

**Implementation Status**: Raises `NotImplementedError`

---

## Common Troubleshooting

### Script fails with "Missing: edges_n={N}.duckdb"
**Solution**: Run [map-basin-from-cycle.py](#map-basin-from-cyclepy) first to create the edges database:
```bash
python n-link-analysis/scripts/map-basin-from-cycle.py --n 5 --cycle-title "Philosophy"
```

### Title resolution fails
**Solution**: Check namespace and redirect settings:
- Use `--namespace 0` for main articles
- Use `--allow-redirects` if target might be a redirect
- Verify title spelling matches Wikipedia exactly (case-sensitive, underscores for spaces)

### Out of memory during basin expansion
**Solution**: Use depth/node limits:
```bash
--max-depth 20  # Limit reverse expansion depth
--max-nodes 1000000  # Stop after 1M nodes discovered
```

### Output files not found
**Solution**: All outputs go to `data/wikipedia/processed/analysis/` (gitignored). Ensure:
- Directory exists (created automatically by most scripts)
- You have write permissions
- No `--out` override pointing to invalid path

### Performance is slow
**Solution**: Optimization strategies:
1. Use `--max-depth` to limit reverse expansion
2. Reduce `--top-k` in visualization scripts
3. Reuse `edges_n={N}.duckdb` across runs (don't recreate)
4. Use `--write-membership` sparingly (large Parquet files)

---

## Script Dependency Graph

```
Tier 0 (No dependencies):
  - trace-nlink-path.py
  - sample-nlink-traces.py
  - find-nlink-preimages.py
  - map-basin-from-cycle.py ← Creates edges_n={N}.duckdb

Tier 1 (Requires edges DB):
  - branch-basin-analysis.py → branches_*.tsv
  - chase-dominant-upstream.py → dominant_upstream_chain_*.tsv

Tier 2 (Requires Tier 1 outputs):
  - compute-trunkiness-dashboard.py (requires branches_*.tsv) → trunkiness_dashboard.tsv
  - render-tributary-tree-3d.py (uses edges DB directly)

Tier 3 (Requires Tier 2 outputs):
  - batch-chase-collapse-metrics.py (requires trunkiness_dashboard.tsv) → collapse_dashboard.tsv

Tier 4 (Reporting):
  - render-human-report.py (requires trunkiness + collapse dashboards) → overview.md + PNG
```

**Typical Analysis Workflow**:
1. Run `map-basin-from-cycle.py` once for target cycle → creates edges DB
2. Run `branch-basin-analysis.py` for same cycle → creates branches_*.tsv
3. Run `compute-trunkiness-dashboard.py` → aggregates metrics
4. Run `batch-chase-collapse-metrics.py` → tests dominance stability
5. Run `render-human-report.py` → generates summary with charts
6. (Optional) Run `render-tributary-tree-3d.py` → interactive 3D visualization

---

## Quick Reference Table

| Script | Status | Input | Output | Key Parameters |
|--------|--------|-------|--------|----------------|
| trace-nlink-path.py | ✓ | nlink_sequences | trace_*.tsv | --n, --start-page-id, --max-steps |
| sample-nlink-traces.py | ✓ | nlink_sequences | sample_traces_*.tsv | --n, --num, --seed0 |
| find-nlink-preimages.py | ✓ | nlink_sequences | preimages_*.tsv | --n, --target-page-id, --limit |
| map-basin-from-cycle.py | ✓ | nlink_sequences | edges_*.duckdb, basin_*_layers.tsv | --n, --cycle-page-id, --max-depth |
| branch-basin-analysis.py | ✓ | edges DB | branches_*.tsv | --n, --cycle-page-id, --top-k |
| chase-dominant-upstream.py | ✓ | edges DB | dominant_upstream_chain_*.tsv | --n, --seed-title, --max-hops |
| compute-trunkiness-dashboard.py | ✓ | branches_*.tsv | trunkiness_dashboard.tsv | --n, --tag, --analysis-dir |
| batch-chase-collapse-metrics.py | ✓ | trunkiness dashboard | collapse_dashboard.tsv | --n, --dashboard, --dominance-threshold |
| render-tributary-tree-3d.py | ✓ | edges DB | HTML 3D tree | --n, --cycle-title, --top-k, --max-levels |
| render-human-report.py | ✓ | dashboards | overview.md + PNG | --tag |
| dash-tributary-viewer.py | ✓ | (shim) | (delegates) | (none) |
| quick-queries.py | ✗ | (planned) | (planned) | --n |
| compute-basin-stats.py | ✗ | (planned) | basin_stats_*.parquet | --n |
| compute-universal-attractors.py | ✗ | (planned) | universal_attractors.parquet | (none) |

**Legend**: ✓ = Implemented, ✗ = Placeholder

---

## Related Documentation

- [INDEX.md](INDEX.md) - N-Link Analysis directory index
- [implementation.md](implementation.md) - Analysis architecture and algorithms
- [../llm-facing-documentation/theories-proofs-conjectures/n-link-rule-theory.md](../llm-facing-documentation/theories-proofs-conjectures/n-link-rule-theory.md) - Mathematical foundation
- [empirical-investigations/INDEX.md](empirical-investigations/INDEX.md) - Question-scoped investigation streams
- [report/overview.md](report/overview.md) - Human-facing summary report

---

## Changelog

### 2026-01-01
- Updated `compute-trunkiness-dashboard.py` documentation: Added `--n` parameter for Multi-N support
- Script now filters branch files by N value (enables systematic Multi-N comparison)
- Updated quick reference table with new parameters

### 2025-12-31
- Initial creation: Comprehensive documentation of all 14 scripts
- Organized by analysis pipeline tier (validation → construction → quantification → aggregation → visualization)
- Documented all parameters, inputs, outputs, and theory connections
- Added troubleshooting section and dependency graph
- Included quick reference table and usage examples

---

**END OF DOCUMENT**
