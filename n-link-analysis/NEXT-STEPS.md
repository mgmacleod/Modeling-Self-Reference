# N-Link Analysis - Next Steps

**Last Updated**: 2026-01-01
**Status**: Planning document
**Context**: Harness scripts created and tested, all major empirical investigations complete

---

## Breadcrumb (Matt next session)

~~**Narrative inconsistency fix**~~ ✓ **COMPLETED (2026-01-01)**

The MECHANISM-ANALYSIS.md narrative inconsistency has been fixed:
- Added update notice at top explaining entry breadth hypothesis was refuted
- Changed all "entry breadth dominates" language to "depth dominates"
- Updated formula to `Basin_Mass = Entry_Breadth × Depth^2.5`
- Added cross-references to ENTRY-BREADTH-RESULTS.md and DEPTH-SCALING-ANALYSIS.md
- Updated Next Steps section to mark entry breadth investigation as completed/refuted

Keep an eye on tag consistency when comparing cross-N outputs (e.g., `test_*` vs `multi_n_jan_2026`).

**Tunneling breadcrumb**:

- See [llm-facing-documentation/theories-proofs-conjectures/database-inference-graph-theory.md](../llm-facing-documentation/theories-proofs-conjectures/database-inference-graph-theory.md) (Corollary 3.2) for the “exhaustive labeling shrinks search space” note and the framing that fixed-$N$ basins are 1D slices of a multiplex over $(\text{page}, N)$ connected by tunneling at shared nodes.

## Current State

### Completed Infrastructure ✓
- **26 analysis scripts** documented in [scripts-reference.md](scripts-reference.md)
- **2 harness scripts** for automated batch analysis ([HARNESS-README.md](scripts/HARNESS-README.md))
  - `run-analysis-harness.py` - Complete pipeline for multiple cycles
  - `run-single-cycle-analysis.py` - Deep-dive for single cycles
- **9 empirical investigations** completed (depth, breadth, mechanisms, phase transitions)
- **Reproducibility infrastructure** validated (all scripts run successfully)

### Recent Session (2026-01-01)
- Ran harness scripts successfully on N=5 with 6+ cycles
- Generated comprehensive documentation for harness usage
- All outputs validated: basins, branches, dashboards, visualizations

---

## Prioritized Next Steps

### Tier 1: High-Impact Extensions (1-3 sessions)

#### 1.1 Multi-N Systematic Comparison ✅ COMPLETED (2026-01-01)

**Status**: DONE - Extended analysis to N=8-10

**Findings**:
- N=5 confirmed as unique peak (no other peaks at N=8-10)
- Basin collapse beyond N=5: 10-1000× smaller basins
- N=10 basins: 148-7,867 pages (vs N=5: 60K-1M pages)

**Key Results**:
| Cycle | N=5 Size | N=10 Size | Collapse |
|-------|----------|-----------|----------|
| Massachusetts | 1,009,471 | 5,226 | 193× |
| Autumn__Summer | 162,689 | 148 | 1,100× |
| Sea_salt__Seawater | 265,896 | 4,391 | 61× |

**Data Generated**:
- `branches_n={8,9,10}_*_assignments.parquet` (18 files)
- `multiplex_basin_assignments.parquet` updated for N=3-10

**Investigation doc**: See timeline entry 2026-01-01 (Late Night)

---

#### 1.2 Hub Connectivity Deep-Dive
**Goal**: Test hypothesis that high-degree nodes (hubs) act as depth multipliers

**Why**: Massachusetts has 1,120 outlinks and forms giant basin at N=5. Need to test if:
- High in-degree pages amplify basin mass
- Hub pages extend depth distributions
- Link degree predicts cycle importance

**Approach**:
```python
# Correlate hub metrics with basin properties
python scripts/analyze-hub-connectivity.py \
  --n 5 \
  --cycles-file universal_cycles.tsv \
  --degree-threshold 100 \
  --output hub_analysis_n5.tsv
```

**New script needed**: `scripts/analyze-hub-connectivity.py` (~300 lines)

**Analysis**:
1. Extract in-degree and out-degree for all cycle pages
2. Correlate degree with basin mass, max depth, trunkiness
3. Test if hubs appear disproportionately in large basins
4. Identify hub-driven vs depth-driven basins

**Investigation doc**: Create `empirical-investigations/HUB-CONNECTIVITY-ANALYSIS.md`

---

#### 1.3 Depth Distribution Mixture Models
**Goal**: Fit statistical models to understand bimodal patterns at N=5,7

**Why**: Depth distributions show:
- N=5: Two-phase convergence (85% rapid + 15% deep tail)
- N=7: Similar bimodal pattern
- Need to quantify mixture components

**Approach**:
```python
# Fit Gaussian mixture models
python scripts/fit-depth-mixture-models.py \
  --n-values 3 4 5 6 7 \
  --n-components 2 \
  --output mixture_models_2026_01_01.json
```

**New script needed**: `scripts/fit-depth-mixture-models.py` (~250 lines)

**Analysis**:
1. Fit 2-component Gaussian mixtures to depth distributions
2. Extract component weights (rapid vs exploratory)
3. Compare component means and variances across N
4. Test if rapid component is universal (similar across N)

**Investigation doc**: Extend `empirical-investigations/DEPTH-DISTRIBUTION-ANALYSIS.md`

---

### Tier 2: Theory Validation (2-4 sessions)

#### 2.1 Power-Law Validation Across N
**Goal**: Measure depth-mass power-law exponent α for all N∈{3-10}

**Why**: Current finding (α ≈ 2.0-2.5 at N=5) needs cross-N validation:
- Is α universal or N-dependent?
- Does α correlate with phase transition?
- Test if Basin_Mass ∝ Depth^α holds universally

**Approach**:
```bash
# Already have depth data from path characteristics
python scripts/fit-power-law-across-n.py \
  --n-range 3 10 \
  --output power_law_exponents.tsv
```

**New script needed**: `scripts/fit-power-law-across-n.py` (~200 lines)

**Validation**:
1. Extract (max_depth, basin_mass) pairs for all cycles × N
2. Fit log-log regression: log(Basin_Mass) ~ α × log(Max_Depth) + const
3. Compute R² and confidence intervals for α
4. Test if α varies systematically with N

**Investigation doc**: Extend `empirical-investigations/DEPTH-SCALING-ANALYSIS.md`

---

#### 2.2 Tunneling/Multiplex Analysis (ROADMAP AVAILABLE)

**Status**: Full implementation roadmap created - see [TUNNELING-ROADMAP.md](TUNNELING-ROADMAP.md)

**Goal**: Implement cross-N tunneling and multiplex analysis per Definition 4.1

**Summary**: 5-phase roadmap with 15 new scripts (~3,750 lines):
1. **Phase 1**: Multiplex Data Layer (unified cross-N tables)
2. **Phase 2**: Tunnel Node Identification (core theory validation)
3. **Phase 3**: Multiplex Connectivity (graph + reachability analysis)
4. **Phase 4**: Mechanism Classification (understand WHY structure changes)
5. **Phase 5**: Applications & Validation (semantic model, validation, report)

**Key Decisions Made**:
- Tunneling rule: Reverse identification (Definition 4.1)
- Connectivity: Directed reachability
- Scale: Full N=3-10 coverage

**Effort**: 7-11 sessions total

**To start**: Begin with Phase 1 scripts in [TUNNELING-ROADMAP.md](TUNNELING-ROADMAP.md)

---

#### 2.3 Basin Boundary Analysis
**Goal**: Understand what prevents pages from entering basins (why HALT vs CYCLE?)

**Why**: 2-3% HALT rate at N=5 needs explanation:
- Are HALT pages low-degree dead-ends?
- Do they cluster in specific semantic regions?
- What prevents them from reaching cycles?

**Approach**:
```python
# Analyze HALT characteristics
python scripts/analyze-halt-characteristics.py \
  --n 5 \
  --num-samples 1000 \
  --output halt_analysis_n5.tsv
```

**New script needed**: `scripts/analyze-halt-characteristics.py` (~300 lines)

**Analysis**:
1. Sample 1000 paths, track which HALT
2. Extract link degree for HALT pages
3. Measure distance from HALTs to nearest cycle
4. Test if HALTs cluster by Wikipedia category

**Investigation doc**: Create `empirical-investigations/HALT-BOUNDARY-ANALYSIS.md`

---

### Tier 3: Cross-Dataset Validation (3-6 sessions)

#### 3.1 Multi-Language Wikipedia
**Goal**: Test if N=5 peak is universal or English-Wikipedia-specific

**Why**: Need to validate findings on independent graphs:
- German Wikipedia (de.wiki)
- Spanish Wikipedia (es.wiki)
- Does N=5 peak appear in all languages?

**Approach**:
1. Download German Wikipedia dump (~25GB compressed)
2. Run extraction pipeline (link parsing, sequence generation)
3. Execute harness for N∈{3,4,5,6,7}
4. Compare phase transition curves

**Timeline**: ~2-3 sessions (data processing is slow)

**Investigation doc**: Create `empirical-investigations/MULTI-LANGUAGE-VALIDATION.md`

---

#### 3.2 Citation Network Analysis
**Goal**: Test N-link theory on directed citation graphs

**Why**: Wikipedia is one example; need to validate on other self-referential systems:
- arXiv citation network
- US patent citations
- Academic paper citations (Semantic Scholar)

**Approach**:
1. Extract citation graph (paper → references[N])
2. Adapt scripts to citation semantics
3. Measure basin properties for N∈{3,5,7}
4. Compare phase transition behavior

**Timeline**: ~4-6 sessions (new dataset, different structure)

**Investigation doc**: Create `empirical-investigations/CITATION-NETWORK-VALIDATION.md`

---

### Tier 4: Tooling & Visualization (1-2 sessions)

#### 4.1 Interactive Basin Explorer
**Goal**: Build web app for exploring basins interactively

**Why**: Current tools require running scripts; need user-friendly interface:
- Select cycle, visualize basin
- Adjust N, see phase transition
- Click nodes to explore neighborhoods

**Approach**:
```python
# Extend existing Dash viewer
python viz/dash-basin-explorer-enhanced.py \
  --port 8052 \
  --preload-n-range 3 7
```

**Extension needed**: Add to `viz/dash-basin-geometry-viewer.py`:
- N-selector dropdown
- Cycle selector with autocomplete
- Real-time basin rendering (use cached edges DB)

**Timeline**: ~1 session (extend existing Dash app)

---

#### 4.2 Animated Phase Transition
**Goal**: Create video/animation showing N=3→N=10 evolution

**Why**: Static charts don't convey dynamics; animation would:
- Show basin growth as N increases
- Highlight N=5 spike visually
- Make findings accessible to broader audience

**Approach**:
```python
# Generate frame-by-frame PNGs
python scripts/render-phase-transition-animation.py \
  --n-range 3 10 \
  --fps 2 \
  --output phase_transition.mp4
```

**New script needed**: `scripts/render-phase-transition-animation.py` (~200 lines)

**Timeline**: ~1 session (use matplotlib animation)

---

## Quick Wins (Can Do in Current Session)

### Q1: Fix Gulf_of_Maine Title Resolution
**Problem**: `map-basin-from-cycle.py` failed with "Gulf of Maine" (underscore issue)

**Fix**:
```bash
# Test correct title
python scripts/find-nlink-preimages.py --n 5 --target-title "Gulf_of_Maine" --limit 10
```

**Action**: Document correct title format in HARNESS-README.md

---

### Q2: Generate Updated Report
**Problem**: `report/overview.md` may be stale after harness run

**Fix**:
```bash
python scripts/render-human-report.py --tag harness_2026-01-01
```

**Action**: Regenerate report with latest harness outputs

---

### Q3: Archive Harness Outputs
**Problem**: New harness outputs (harness_2026-01-01 tag) should be documented

**Fix**:
1. Count files: `ls data/wikipedia/processed/analysis/ | grep harness_2026-01-01 | wc -l`
2. Document in session-log.md
3. Commit: "Add harness infrastructure and 2026-01-01 test run"

---

## Decision Points

### Should we prioritize?
1. **Breadth** (Tier 1.1: Multi-N) - Maps full phase curve, high impact
2. **Depth** (Tier 1.2: Hubs) - Tests specific mechanism hypothesis
3. **Validation** (Tier 3.1: Multi-language) - Ensures findings generalize

**Recommendation**: Start with Tier 1.1 (Multi-N) since:
- Infrastructure is ready (just run harness for N∈{8,9,10})
- Answers most pressing question (is N=5 unique?)
- Quick turnaround (~1 session for quick mode)

---

## Long-Term Vision (Beyond Next Steps)

### Publication Path
Once Tier 1-2 complete:
1. Write paper draft (5-10 pages)
2. Submit to graph theory or complex systems venue
3. Open-source complete reproduction pipeline

### Theory Extensions
- Extend proofs to random graphs (Erdős-Rényi, preferential attachment)
- Prove percolation threshold exists
- Connect to dynamical systems theory (basins of attraction)

### Applications
- Search ranking (PageRank-like but with N-link rules)
- Recommendation systems (multi-rule tunneling for exploration)
- Knowledge graph analysis (semantic basins)

---

## Related Documentation

- [session-log.md](session-log.md) - Cumulative session history
- [empirical-investigations/INDEX.md](empirical-investigations/INDEX.md) - Investigation registry
- [scripts/HARNESS-README.md](scripts/HARNESS-README.md) - Harness usage guide
- [scripts-reference.md](scripts-reference.md) - Complete script documentation

---

**Next Session Bootstrap**:
1. Read this file
2. Choose Tier (1, 2, 3, or 4)
3. Follow approach outlined above
4. Update session-log.md when done

---

**END OF DOCUMENT**
