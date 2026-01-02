# Tunneling/Multiplex Analysis Implementation Roadmap

**Document Type**: Implementation roadmap
**Target Audience**: LLMs and developers
**Purpose**: Phased plan for implementing cross-N tunneling and multiplex analysis
**Created**: 2026-01-01
**Status**: Complete (All 5 phases validated, extended to N=3-10)

---

## Overview

This roadmap extends the N-Link Rule analysis from single-N basin partitions to **cross-N multiplex analysis**. The core insight from [database-inference-graph-theory.md](../llm-facing-documentation/theories-proofs-conjectures/database-inference-graph-theory.md) is that fixed-N basins are 1D "slices" of a higher-dimensional multiplex structure, connected by **tunneling** at shared nodes.

### Key Decisions

| Decision | Choice | Rationale |
|----------|--------|-----------|
| **Tunneling rule** | Reverse identification (Definition 4.1) | Nodes reachable from different basins under different N |
| **Connectivity semantics** | Directed reachability | Respects flow direction; most restrictive and theoretically grounded |
| **Scale scope** | Full N=3-10 | Complete coverage of existing empirical data |

### Theory Foundation

From [database-inference-graph-theory.md](../llm-facing-documentation/theories-proofs-conjectures/database-inference-graph-theory.md):

> **Definition 4.1 (Tunnel Node)**: A node n is a tunnel node between rules I₁ and I₂ if:
> ∃a, b : a ∈ Basin_I₁(Tᵢ) ∧ b ∈ Basin_I₂(Tⱼ) ∧ a →_I₁ n →_I₂ b

> **Corollary 3.2 (Multiplex Interpretation)**: Fixed-N basins are 1D slices of a multiplex over (page, N) connected by tunneling at shared nodes. Exhaustive basin labeling shrinks the remaining search space.

---

## Phase Summary

| Phase | Goal | Scripts | Status | Dependencies |
|-------|------|---------|--------|--------------|
| **1** | Multiplex Data Layer | 3 | ✓ Complete | None |
| **2** | Tunnel Node Identification | 3 | ✓ Complete | Phase 1 |
| **3** | Multiplex Connectivity | 3 | ✓ Complete | Phases 1-2 |
| **4** | Mechanism Classification | 3 | ✓ Complete | Phases 1-3 |
| **5** | Applications & Validation | 3 | ✓ Complete | Phases 1-4 |

**Total**: 15 new scripts (~3,750 lines), 7-11 sessions

---

## Phase 1: Multiplex Data Layer (Foundational)

**Goal**: Build unified data structures joining pages across all N values

### Scripts

#### 1.1 `build-multiplex-table.py` (~200 lines)

**Purpose**: Creates unified multiplex table from per-N basin parquet files

**Input**:
- `data/wikipedia/processed/analysis/branches_n=*_cycle=*_assignments.parquet`

**Output**:
- `data/wikipedia/processed/analysis/multiplex/multiplex_basin_assignments.parquet`

**Schema**:
```
page_id: int64        # Wikipedia page ID
N: int8               # N-link rule (3-10)
cycle_key: string     # Canonical cycle identifier
entry_id: int64       # Entry point page_id for this basin
depth: int32          # Depth from cycle under this N
```

**Algorithm**:
1. Glob all `branches_n=*_assignments.parquet` files
2. Extract N value from filename
3. Normalize cycle_key using canonical mapping
4. Union all into single table with N column
5. Write partitioned parquet (by N)

---

#### 1.2 `normalize-cycle-identity.py` (~150 lines)

**Purpose**: Canonicalizes cycle names across N values

**Problem**: Same cycle appears with different lead members:
- `Massachusetts__Gulf_of_Maine` vs `Gulf_of_Maine__Massachusetts`
- Different tags: `_reproduction_2025-12-31` vs `_multi_n_jan_2026`

**Output**:
- `data/wikipedia/processed/analysis/multiplex/cycle_identity_map.tsv`

**Schema**:
```
raw_cycle_key: string      # Original filename-derived key
canonical_cycle_id: string # Normalized identifier (alphabetically sorted members)
cycle_members: string      # Pipe-separated sorted member list
appears_at_N: string       # Comma-separated N values where cycle exists
```

**Algorithm**:
1. Parse all cycle keys from basin files
2. Extract cycle members (split on `__`, strip tags)
3. Sort members alphabetically → canonical ID
4. Track which N values each canonical cycle appears at

---

#### 1.3 `compute-intersection-matrix.py` (~250 lines)

**Purpose**: Computes basin overlap between N values

**Output**:
- `data/wikipedia/processed/analysis/multiplex/basin_intersection_n{N1}_n{N2}.tsv`

**Schema**:
```
cycle_N1: string           # Basin at N1
cycle_N2: string           # Basin at N2
intersection_size: int64   # Pages in both basins
N1_only: int64             # Pages only in N1 basin
N2_only: int64             # Pages only in N2 basin
jaccard: float64           # Intersection / Union
```

**Algorithm**:
1. Load multiplex table for N1 and N2
2. For each (cycle_N1, cycle_N2) pair:
   - Compute page_id set intersection
   - Compute Jaccard similarity
3. Output matrix as TSV

**Use Case**: Identifies which basins are "stable" across N vs which fragment/merge

---

### Phase 1 Outputs

| File | Format | Description |
|------|--------|-------------|
| `multiplex_basin_assignments.parquet` | Parquet | Unified (page_id, N, cycle, depth) table |
| `cycle_identity_map.tsv` | TSV | Canonical cycle ID mapping |
| `basin_intersection_n{N1}_n{N2}.tsv` | TSV | Pairwise basin overlap matrices |

### Phase 1 Reference Files

- [compare-cycle-evolution.py](scripts/compare-cycle-evolution.py) - Template for cross-N aggregation
- [branches_n=5_cycle=Massachusetts__Gulf_of_Maine_*.parquet](../data/wikipedia/processed/analysis/) - Schema reference

---

## Phase 2: Tunnel Node Identification (Core Theory Validation)

**Goal**: Identify and classify nodes enabling cross-N basin transitions per Definition 4.1

### Scripts

#### 2.1 `find-tunnel-nodes.py` (~300 lines)

**Purpose**: For each page, compute which basins it reaches under each N

**Input**:
- `multiplex_basin_assignments.parquet` (from Phase 1)

**Output**:
- `data/wikipedia/processed/analysis/multiplex/tunnel_nodes.parquet`

**Schema**:
```
page_id: int64
basin_at_N3: string       # Which cycle's basin this page belongs to at N=3
basin_at_N4: string       # ... at N=4
basin_at_N5: string       # ... at N=5
...
basin_at_N10: string      # ... at N=10
n_distinct_basins: int8   # Count of unique basins across all N
is_tunnel_node: bool      # True if n_distinct_basins > 1
```

**Algorithm**:
1. Pivot multiplex table: rows=page_id, columns=N, values=cycle_key
2. Count distinct non-null basins per page
3. Flag tunnel nodes (distinct > 1)

---

#### 2.2 `classify-tunnel-types.py` (~200 lines)

**Purpose**: Categorize tunnel nodes by behavior

**Output**:
- `data/wikipedia/processed/analysis/multiplex/tunnel_classification.tsv`

**Tunnel Types**:

| Type | Definition |
|------|------------|
| **Basin-switching** | Different cycle basins under different N |
| **Basin-preserving** | Same cycle basin across all N (not a tunnel) |
| **Partial-tunnel** | Same basin for some N, different for others |
| **HALT-bridging** | Reaches HALT under some N, cycle under others |

**Schema**:
```
page_id: int64
tunnel_type: string       # One of above types
stable_N_range: string    # N values where basin is stable (if any)
switching_transitions: string  # e.g., "N4→N5: Massachusetts→Autumn"
```

---

#### 2.3 `compute-tunnel-frequency.py` (~150 lines)

**Purpose**: Rank nodes by how many basins they bridge

**Output**:
- `data/wikipedia/processed/analysis/multiplex/tunnel_frequency_ranking.tsv`

**Schema**:
```
page_id: int64
page_title: string
n_basins_bridged: int8    # Number of distinct basins across all N
n_transitions: int8       # Number of N→N+1 basin changes
tunnel_score: float64     # Weighted importance metric
```

**Interpretation**: High-frequency tunnel nodes = semantically central entities

---

### Phase 2 Outputs

| File | Format | Description |
|------|--------|-------------|
| `tunnel_nodes.parquet` | Parquet | Basin membership per page per N |
| `tunnel_classification.tsv` | TSV | Tunnel type per node |
| `tunnel_frequency_ranking.tsv` | TSV | Ranked tunnel importance |

### Phase 2 Documentation

Create: `empirical-investigations/TUNNEL-NODE-ANALYSIS.md`

---

## Phase 3: Multiplex Connectivity Analysis (Theory Extension)

**Goal**: Build and analyze the multiplex graph with reachability semantics

### Scripts

#### 3.1 `build-multiplex-graph.py` (~350 lines)

**Purpose**: Constructs the multiplex graph structure

**Multiplex Definition**:
- **Nodes**: (page_id, N) tuples
- **Within-N edges**: f_N(page) → successor under N-link rule
- **Tunneling edges**: (page_id, N1) ↔ (page_id, N2) for same page across N

**Output**:
- `data/wikipedia/processed/analysis/multiplex/multiplex_edges.parquet`

**Schema**:
```
src_page_id: int64
src_N: int8
dst_page_id: int64
dst_N: int8
edge_type: string         # "within_N" or "tunnel"
```

**Scale Note**: 17.9M pages × 8 N values = 143M potential nodes. Implementation must handle:
- Chunked processing
- DuckDB for efficient joins
- Optional sampling mode for faster iteration

---

#### 3.2 `compute-multiplex-reachability.py` (~250 lines)

**Purpose**: Computes directed reachability in multiplex

**Output**:
- `data/wikipedia/processed/analysis/multiplex/multiplex_reachability.parquet`

**Analyses**:
1. **Reachability from cycle nodes**: Which (page, N) pairs can reach each cycle?
2. **Cross-N reachability**: Can page A at N=3 reach page B at N=7 via tunneling?
3. **Reachability components**: Partition multiplex by mutual reachability

**Algorithm Options**:
- BFS from seed nodes (cycle members)
- Transitive closure (expensive at scale)
- Sampling-based estimation

---

#### 3.3 `visualize-multiplex-slice.py` (~200 lines)

**Purpose**: Interactive visualization of multiplex structure

**Output**:
- `n-link-analysis/report/assets/multiplex_visualization.html`

**Visualization**:
- Basins as horizontal layers (one per N)
- Within-N edges as layer-internal connections
- Tunneling edges as cross-layer vertical lines
- Color by cycle membership

**Technology**: Plotly 3D scatter with edges

---

### Phase 3 Outputs

| File | Format | Description |
|------|--------|-------------|
| `multiplex_edges.parquet` | Parquet | Full multiplex edge list |
| `multiplex_reachability.parquet` | Parquet | Reachability analysis results |
| `multiplex_visualization.html` | HTML | Interactive 3D visualization |

### Phase 3 Documentation

Create: `empirical-investigations/MULTIPLEX-CONNECTIVITY.md`

---

## Phase 4: Mechanism Classification (Empirical Deep-Dive)

**Goal**: Understand WHY structure changes when switching N

### Scripts

#### 4.1 `analyze-tunnel-mechanisms.py` (~400 lines)

**Purpose**: Classifies the mechanism causing each tunnel transition

**Mechanisms**:

| Mechanism | Description |
|-----------|-------------|
| **Degree shift** | f_N(page) changes because Nth link is different |
| **Path divergence** | Same immediate successor, but paths diverge downstream |
| **HALT creation** | Page has <N links under higher N |
| **Cycle reformation** | Same pages form different cycle structure |

**Output**:
- `data/wikipedia/processed/analysis/multiplex/tunnel_mechanisms.tsv`

---

#### 4.2 `trace-tunneling-paths.py` (~300 lines)

**Purpose**: Traces paths through specified N-sequences

**Example**: Start at "Massachusetts", follow N=5 for 10 hops, switch to N=3, continue

**Output**:
- `data/wikipedia/processed/analysis/multiplex/tunneling_traces.tsv`

**Use Case**: Demonstrates tunneling behavior on specific examples

---

#### 4.3 `quantify-basin-stability.py` (~200 lines)

**Purpose**: Measures how stable basins are to N changes

**Metrics**:
- **Persistence score**: Fraction of pages remaining in same basin across N
- **Fragmentation index**: How many sub-basins a basin splits into
- **Stability range**: Contiguous N values where basin is stable

**Output**:
- `data/wikipedia/processed/analysis/multiplex/basin_stability_scores.tsv`

---

### Phase 4 Outputs

| File | Format | Description |
|------|--------|-------------|
| `tunnel_mechanisms.tsv` | TSV | Mechanism classification |
| `tunneling_traces.tsv` | TSV | Example path traces |
| `basin_stability_scores.tsv` | TSV | Stability metrics per basin |

### Phase 4 Documentation

Create: `empirical-investigations/TUNNEL-MECHANISM-DEEP-DIVE.md`

---

## Phase 5: Applications and Validation (Derived Outputs)

**Goal**: Apply tunneling insights and validate theory predictions

### Scripts

#### 5.1 `compute-semantic-model.py` (~350 lines)

**Purpose**: Implements Algorithm 5.2 from database-inference-graph-theory.md

**Extracts**:
- **Central entities**: High tunnel frequency across N
- **Subsystem boundaries**: Basins persistent across multiple N
- **Hidden relationships**: Tunnels not predicted by single-N analysis

**Output**:
- `data/wikipedia/processed/analysis/multiplex/semantic_model_wikipedia.json`

---

#### 5.2 `validate-tunneling-predictions.py` (~250 lines)

**Purpose**: Tests theory claims empirically

**Validations**:
1. Does tunnel structure predict basin behavior?
2. Do high-degree hubs form more tunnels?
3. Does tunnel frequency correlate with semantic centrality?

**Output**:
- `data/wikipedia/processed/analysis/multiplex/tunneling_validation_metrics.tsv`

---

#### 5.3 `generate-tunneling-report.py` (~200 lines)

**Purpose**: Human-readable summary with visualizations

**Output**:
- `n-link-analysis/report/TUNNELING-FINDINGS.md`

**Contents**:
- Key tunnel nodes ranked by significance
- Cross-N connectivity statistics
- Visualization gallery
- Theory validation results

---

### Phase 5 Outputs

| File | Format | Description |
|------|--------|-------------|
| `semantic_model_wikipedia.json` | JSON | Extracted semantic structure |
| `tunneling_validation_metrics.tsv` | TSV | Validation results |
| `report/TUNNELING-FINDINGS.md` | Markdown | Publication-ready summary |

### Phase 5 Contract

Add to `llm-facing-documentation/contracts/contract-registry.md`:

```markdown
### NLR-C-0004 — Cross-N tunneling and multiplex connectivity (Wikipedia)

- **Status**: [pending validation]
- **Theory**: database-inference-graph-theory.md (Definition 4.1, Corollary 3.2, Algorithm 5.2)
- **Experiment**: Tunneling analysis scripts (Phase 1-5)
- **Evidence**: TUNNEL-NODE-ANALYSIS.md, MULTIPLEX-CONNECTIVITY.md, TUNNEL-MECHANISM-DEEP-DIVE.md
```

---

## Infrastructure Reuse

| Existing Script | Reuse For |
|----------------|-----------|
| [compare-cycle-evolution.py](scripts/compare-cycle-evolution.py) | Cross-N aggregation pattern |
| [map-basin-from-cycle.py](scripts/map-basin-from-cycle.py) | DuckDB edge materialization |
| [branch-basin-analysis.py](scripts/branch-basin-analysis.py) | Per-basin depth/entry analysis |
| [analyze-path-characteristics.py](scripts/analyze-path-characteristics.py) | Path tracing logic |
| [render-tributary-tree-3d.py](scripts/render-tributary-tree-3d.py) | 3D visualization pattern |

---

## Script Index (All 15 New Scripts)

### Phase 1: Multiplex Data Layer
| Script | Lines | Input | Output |
|--------|-------|-------|--------|
| `build-multiplex-table.py` | ~200 | Per-N parquets | `multiplex_basin_assignments.parquet` |
| `normalize-cycle-identity.py` | ~150 | Basin files | `cycle_identity_map.tsv` |
| `compute-intersection-matrix.py` | ~250 | Multiplex table | `basin_intersection_*.tsv` |

### Phase 2: Tunnel Node Identification
| Script | Lines | Input | Output |
|--------|-------|-------|--------|
| `find-tunnel-nodes.py` | ~300 | Multiplex table | `tunnel_nodes.parquet` |
| `classify-tunnel-types.py` | ~200 | Tunnel nodes | `tunnel_classification.tsv` |
| `compute-tunnel-frequency.py` | ~150 | Tunnel nodes | `tunnel_frequency_ranking.tsv` |

### Phase 3: Multiplex Connectivity
| Script | Lines | Input | Output |
|--------|-------|-------|--------|
| `build-multiplex-graph.py` | ~350 | Multiplex table + edges | `multiplex_edges.parquet` |
| `compute-multiplex-reachability.py` | ~250 | Multiplex graph | `multiplex_reachability.parquet` |
| `visualize-multiplex-slice.py` | ~200 | Multiplex data | `multiplex_visualization.html` |

### Phase 4: Mechanism Classification
| Script | Lines | Input | Output |
|--------|-------|-------|--------|
| `analyze-tunnel-mechanisms.py` | ~400 | Tunnel nodes + edges | `tunnel_mechanisms.tsv` |
| `trace-tunneling-paths.py` | ~300 | Multiplex graph | `tunneling_traces.tsv` |
| `quantify-basin-stability.py` | ~200 | Multiplex table | `basin_stability_scores.tsv` |

### Phase 5: Applications
| Script | Lines | Input | Output |
|--------|-------|-------|--------|
| `compute-semantic-model.py` | ~350 | All multiplex data | `semantic_model_wikipedia.json` |
| `validate-tunneling-predictions.py` | ~250 | Multiplex + tunnel data | `tunneling_validation_metrics.tsv` |
| `generate-tunneling-report.py` | ~200 | All outputs | `report/TUNNELING-FINDINGS.md` |

**Total**: ~3,750 lines

---

## Documentation Deliverables

| Document | Phase | Purpose |
|----------|-------|---------|
| `empirical-investigations/TUNNEL-NODE-ANALYSIS.md` | 2 | Tunnel node identification results |
| `empirical-investigations/MULTIPLEX-CONNECTIVITY.md` | 3 | Multiplex graph analysis |
| `empirical-investigations/TUNNEL-MECHANISM-DEEP-DIVE.md` | 4 | Mechanism classification |
| `report/TUNNELING-FINDINGS.md` | 5 | Publication-ready summary |
| Contract `NLR-C-0004` | 5 | Theory-experiment-evidence binding |

---

## Getting Started

### Prerequisites
- Completed N=3-10 basin analyses (existing)
- Virtual environment with dependencies: `source .venv/bin/activate`
- ~2GB free disk space for multiplex outputs

### Quick Start

All tunneling scripts are in `n-link-analysis/scripts/tunneling/`.

```bash
# Run the complete pipeline (all 5 phases)
python n-link-analysis/scripts/tunneling/run-tunneling-pipeline.py

# Run specific phases
python n-link-analysis/scripts/tunneling/run-tunneling-pipeline.py --phase 1 2

# Run from phase 3 onwards
python n-link-analysis/scripts/tunneling/run-tunneling-pipeline.py --from-phase 3

# Dry run (show what would execute)
python n-link-analysis/scripts/tunneling/run-tunneling-pipeline.py --dry-run

# Custom N range
python n-link-analysis/scripts/tunneling/run-tunneling-pipeline.py --n-min 3 --n-max 10
```

### Running Individual Scripts

```bash
# Phase 1: Multiplex Data Layer
python n-link-analysis/scripts/tunneling/build-multiplex-table.py
python n-link-analysis/scripts/tunneling/normalize-cycle-identity.py
python n-link-analysis/scripts/tunneling/compute-intersection-matrix.py

# Phase 2: Tunnel Node Identification
python n-link-analysis/scripts/tunneling/find-tunnel-nodes.py
python n-link-analysis/scripts/tunneling/classify-tunnel-types.py
python n-link-analysis/scripts/tunneling/compute-tunnel-frequency.py

# Phase 3: Multiplex Connectivity
python n-link-analysis/scripts/tunneling/build-multiplex-graph.py
python n-link-analysis/scripts/tunneling/compute-multiplex-reachability.py
python n-link-analysis/scripts/tunneling/visualize-multiplex-slice.py

# Phase 4: Mechanism Classification
python n-link-analysis/scripts/tunneling/analyze-tunnel-mechanisms.py
python n-link-analysis/scripts/tunneling/trace-tunneling-paths.py
python n-link-analysis/scripts/tunneling/quantify-basin-stability.py

# Phase 5: Applications & Validation
python n-link-analysis/scripts/tunneling/compute-semantic-model.py
python n-link-analysis/scripts/tunneling/validate-tunneling-predictions.py
python n-link-analysis/scripts/tunneling/generate-tunneling-report.py
```

---

## Related Documents

- [NEXT-STEPS.md](NEXT-STEPS.md) - Prioritized next steps (references this roadmap)
- [database-inference-graph-theory.md](../llm-facing-documentation/theories-proofs-conjectures/database-inference-graph-theory.md) - Theory foundation
- [MULTI-N-PHASE-MAP.md](empirical-investigations/MULTI-N-PHASE-MAP.md) - Empirical context on N-dependence
- [contract-registry.md](../llm-facing-documentation/contracts/contract-registry.md) - Theory-experiment contracts

---

**Last Updated**: 2026-01-01
**Status**: Complete (all 5 phases implemented and validated)
