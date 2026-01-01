# N-Link Analysis - Session Log

**Document Type**: Cumulative  
**Target Audience**: LLMs + Developers  
**Purpose**: Append-only record of analysis decisions, experiments, and outcomes  
**Last Updated**: 2025-12-31
**Status**: Active

---

### 2025-12-31 - Cross-N Reproduction and Phase Transition Discovery

**Completed**:
- Created comprehensive reproduction infrastructure:
  - `scripts/validate-data-dependencies.py` - Schema/integrity validation
  - `scripts/reproduce-main-findings.py` - Complete pipeline orchestration (parameterized by N)
  - `scripts/compare-across-n.py` - Cross-N comparison analysis
  - `scripts-reference.md` - Complete documentation for all 14 analysis scripts (~15k tokens)
- Executed full reproduction for N=5 (9 terminal cycles, 1.99M total basin mass)
- Expanded to N∈{3,5,7} to test universality hypothesis
- Generated 9 visualizations (3 interactive 3D HTML trees, 6 cross-N PNG comparison charts)
- Created publication-quality documentation:
  - `empirical-investigations/REPRODUCTION-OVERVIEW.md` - Comprehensive session summary
  - `CROSS-N-FINDINGS.md` (root) - Discovery summary
  - `VISUALIZATION-GUIDE.md` (root) - Visualization index

**Major Discovery**:
- **N=5 exhibits unique phase transition**: 20-60× larger basins than N∈{3,7}
- Same 6 cycles persist across all N but with radically different properties (up to 4289× size variation)
- Only N=5 shows extreme single-trunk structure (67% of basins >95% concentration)
- Hypothesis: N=5 sits at critical 33% page coverage threshold (percolation-like phenomenon)

**Theory Claim Evaluated**:
- **REFUTED**: "Basin structure is universal across N" → Structure is rule-dependent, emerges from rule-graph coupling
- **SUPPORTED**: "Finite self-referential graphs partition into basins" → Holds for all N∈{3,5,7}

**Data Generated** (~60 files in `data/wikipedia/processed/analysis/`):
- Sample traces: N∈{3,5,7}, 500 random starts each
- Basin layers: depth-stratified basin sizes for all cycles
- Branch analysis: tributary structure for all basins
- Dashboards: trunkiness metrics, dominance collapse (N=5 only)
- Dominant chains: upstream trunk paths (N=5 only)

**Contract Update**:
- Added NLR-C-0003 to contract registry (N-dependent phase transition, status: supported)

**Next Steps**:
- Finer N resolution (N∈{4,6,8,9,10}) to map transition curve
- Link degree distribution correlation analysis
- Test on other graphs (different language Wikipedias, citation networks)

Commit: (pending)

---

### 2025-12-31 - Basin Geometry Viewer Reclassified as Visualization

**Completed**:
- Split human-facing visualization tooling out of `scripts/` into `viz/`.
- Added:
	- `viz/dash-basin-geometry-viewer.py`
	- `viz/render-full-basin-geometry.py`
- Updated `INDEX.md` to document the new layout.

**Decision**:
- Treat the Dash basin viewer as a visualization workbench that consumes precomputed Parquet artifacts (no live reverse-expansion).

Commit: 722e63d

---

### 2025-12-29 - Directory Initialized

**Completed**:
- Created new Tier 2 analysis directory with standard docs and script placeholders

**Decisions**:
- Keep analysis scripts out of initial scaffolding; start with placeholders and crystallize algorithms after first benchmarks

**Next Steps**:
- Implement Phase 1 fixed-N basin statistics computation

---

### 2025-12-30 - Empirical Investigation Streams Introduced

**Decision**:
- Empirical findings are recorded in distinct, question-scoped documents under `empirical-investigations/`.
- `session-log.md` references those documents rather than duplicating results.

**New Investigation**:
- [Long-tail basin size (N=5)](empirical-investigations/long-tail-basin-size.md)

**Reproducibility Artifacts (generated outputs)**:
- Output directory: `data/wikipedia/processed/analysis/` (gitignored)
- Edge DB materialized for N=5 reverse expansions: `data/wikipedia/processed/analysis/edges_n=5.duckdb`

---

### 2025-12-30 - Empirical Session Bootstrap (Fixed N=5 sampling)

**Executed**:
- Ran a minimal sanity sampling run for fixed $N=5$ to confirm the analysis scripts work end-to-end and to create a fresh reproducibility artifact.

**Command**:
- `python n-link-analysis/scripts/sample-nlink-traces.py --n 5 --num 50 --seed0 0 --min-outdegree 50 --max-steps 5000 --top-cycles 10 --resolve-titles --out "data/wikipedia/processed/analysis/sample_traces_n=5_num=50_seed0=0_bootstrap_2025-12-30.tsv"`

**Observed Summary (high level)**:
- Terminal counts: `CYCLE = 49`, `HALT = 1` (with `min_outdegree=50`)
- Most frequent cycle in this run: `Gulf_of_Maine ↔ Massachusetts` (11 / 50)

**Primary Investigation Stream**:
- Results are consistent with and recorded under: [Long-tail basin size (N=5)](empirical-investigations/long-tail-basin-size.md)

---

### 2025-12-30 - Branch / Trunk Structure + Dominance Collapse (N=5)

**Executed**:
- Implemented and ran “branch analysis” on multiple $f_5$ basins (partitioning each basin by depth-1 entry subtree size).
- Implemented and ran “dominant-upstream chase” (“source of the Nile”) from multiple seeds.
- Aggregated cross-basin summaries into a trunkiness dashboard and a dominance-collapse dashboard.

**New Scripts**:
- `n-link-analysis/scripts/branch-basin-analysis.py`
- `n-link-analysis/scripts/chase-dominant-upstream.py`
- `n-link-analysis/scripts/compute-trunkiness-dashboard.py`
- `n-link-analysis/scripts/batch-chase-collapse-metrics.py`

**Key Artifacts** (under `data/wikipedia/processed/analysis/`):
- `branch_trunkiness_dashboard_n=5_bootstrap_2025-12-30.tsv`
- `dominance_collapse_dashboard_n=5_bootstrap_2025-12-30_seed=dominant_enters_cycle_title_thr=0.5.tsv`
- `dominant_upstream_chain_n=5_from=Animal_leasttrunk_bootstrap_2025-12-30.tsv`
- `dominant_upstream_chain_n=5_from=American_Revolutionary_War_leasttrunk_bootstrap_2025-12-30.tsv`
- `dominant_upstream_chain_n=5_from=Eastern_United_States_control_bootstrap_2025-12-30.tsv`

**Findings (high-level)**:
- Many tested $f_5$ basins exhibit extreme depth-1 entry concentration (“single-trunk” behavior), but not all.
- Even for a comparatively “non-trunk-like” basin at hop 0 (e.g., `Animal`), the dominant-upstream chase can rapidly enter highly trunk-like regimes upstream.
- The `Eastern_United_States` control chase immediately steps into `American_Revolutionary_War` with ~99% dominance, then matches the prior `American_Revolutionary_War` chain.

**Primary Investigation Stream**:
- Details (commands, outputs, and numeric summaries) are recorded under: [Long-tail basin size (N=5)](empirical-investigations/long-tail-basin-size.md)
