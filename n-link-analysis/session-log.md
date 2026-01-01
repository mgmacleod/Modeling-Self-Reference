# N-Link Analysis - Session Log

**Document Type**: Cumulative
**Target Audience**: LLMs + Developers
**Purpose**: Append-only record of analysis decisions, experiments, and outcomes
**Last Updated**: 2026-01-01
**Status**: Active

---

### 2026-01-01 - Harness Infrastructure Creation

**What was tried**:
- Built automated harness scripts to orchestrate complete analysis pipeline
- Created run-analysis-harness.py for batch multi-cycle analysis (15+ scripts, 4 tiers)
- Created run-single-cycle-analysis.py for focused single-cycle deep-dive (5 scripts)
- Tested harness in quick mode with N=5, 2 cycles (Massachusetts ↔ Gulf_of_Maine, Sea_salt ↔ Seawater)
- Ran 10+ individual scripts manually to verify functionality before automation

**What worked**:
- Harness scripts executed successfully end-to-end (~30-60 min for quick mode)
- All Tier 0-2 scripts ran without errors: validation, sampling, path characteristics, basin mapping, branch analysis, dashboards
- Generated 40+ output files with harness_2026-01-01 tag in data/wikipedia/processed/analysis/
- subprocess.run() approach enables clean script execution with proper output capture
- Tag-based output organization allows tracking multiple analysis runs

**What didn't work**:
- Title resolution issue: "Gulf of Maine" needs underscore format "Gulf_of_Maine" (documented in HARNESS-README.md)
- Some interactive scripts (depth explorers) failed due to missing mechanism-tagged depth distribution files (expected, not created by harness)

**Key findings**:
- **Infrastructure milestone**: Reduces 15+ manual commands to 1 command
- **Quick mode practical**: 30-60 min runtime enables rapid iteration vs 2-4 hours full mode
- **Ready for Multi-N**: Infrastructure validated, just change --n parameter for N=8,9,10 analysis
- **Automation patterns established**: Tier 0-4 structure (validation → construction → aggregation → visualization) reusable for future work

**Scripts created**:
- `scripts/run-analysis-harness.py` (370 lines) - complete pipeline orchestration
- `scripts/run-single-cycle-analysis.py` (280 lines) - single-cycle deep-dive
- `scripts/HARNESS-README.md` - comprehensive usage documentation

**Documentation created**:
- `NEXT-STEPS.md` - strategic planning document with 4 prioritized tiers
- Updated `scripts/HARNESS-README.md` with examples, parameters, troubleshooting

**Next steps**:
- Run Multi-N analysis (N=8,9,10) to map complete phase transition curve (PRIORITY 1)
- Hub connectivity deep-dive (test degree amplification hypothesis)
- Depth distribution mixture models (quantify bimodal patterns)

Commits: f78142f, d282a65, b5c1858

---

### 2025-12-31 (Sixth) - Depth Distribution Analysis and Interactive Exploration

**What was tried**:
- Analyzed full depth distributions from path_characteristics files (N=3-7)
- Computed comprehensive depth statistics: mean, median, percentiles, variance, skewness, kurtosis
- Built enhanced interactive depth explorer with 4-tab interface (distributions, basin mass, variance/skewness, statistics)
- Created depth distribution histograms with overlay statistics

**What worked**:
- analyze-depth-distributions.py executed successfully (~30 seconds runtime)
- Generated 4 output files: depth_statistics_by_n.tsv, depth_predictor_correlations.tsv, 2 PNG visualizations
- Interactive explorer (Dash) launches successfully on port 8051 with all tabs functional
- Depth metrics reveal variance explosion at N=5 (σ²=473 vs σ²=121 at N=4)

**What didn't work**:
- Initial port 8050 conflict (resolved by using port 8051)
- dash/dash-bootstrap-components not installed (resolved with pip install)

**Key findings**:
- **Variance explosion at N=5**: σ²=473 (4× higher than N=4), drives basin mass amplification
- **Bimodal-like distribution at N=5**: Two-phase convergence (85% rapid + 15% deep exploratory tail)
- **Extreme right-skewness at N=5**: Skewness=1.88 (highest across all N), tail dominates
- **p90/median tail ratio at N=5**: 5.3× (strongest tail effect; N=4 only 2.5×)
- **Max depth correlation**: r=0.942, R²=0.888 (validates power-law, outperforms mean/median)
- **Non-monotonic N trajectory**: Alternating high-low pattern (N=3: 16.8 → N=4: 13.6 → N=5: 19.4 → N=6: 13.4 → N=7: 24.7)
- **Universality classes**: Low-variance (N=4,6), high-variance (N=5,7), symmetric (N=3)

**Next investigations**:
- Parse per-cycle depth distributions (test mean vs p90 vs max predictors)
- Extend to N=8 (test variance decay hypothesis)
- Add animation/3D visualization to explorer
- Fit mixture models to N=5/N=7 distributions
- Hub connectivity analysis (explain bimodal pattern)

Commit: (pending end-of-session)

---

### 2025-12-31 (Fourth) - Entry Breadth Hypothesis Testing and Depth Discovery

**What was tried**:
- Developed statistical mechanics framework with entry breadth hypothesis
- Created analyze-basin-entry-breadth.py to measure depth=1 entry nodes
- Ran full analysis on 6 cycles × 5 N values (30 measurements)
- Tested prediction: Entry_Breadth(N=5) / Entry_Breadth(N=4) ≈ 8-10×

**What worked**:
- Script executed successfully, all 30 measurements completed in ~20 seconds
- Entry breadth measured accurately (decreases monotonically: 871 → 429 → 307)
- Max depth captured per basin (peaks at N=5: mean ~74 steps vs ~13 at N=4)
- Infrastructure reused patterns from existing scripts (branch-basin-analysis.py)

**What didn't work**:
- Entry breadth hypothesis REFUTED (predicted 8-10× increase, measured 0.75× decrease)

**Key findings**:
- **DEPTH dominates basin mass, not breadth** (13× increase N=4→N=5)
- **Depth power-law**: Basin_Mass ≈ Entry_Breadth × Depth^α where α ≈ 2.0-2.5
- **Quantitative validation**: 0.81 × 13² ≈ 137× vs observed 94× amplification
- **Karst sinkhole model**: Narrow openings (low entry breadth) + deep shafts (high max depth) = huge volumes
- **Premature convergence refined**: N=4 limits DEPTH (13 steps max), not just breadth
- **Massachusetts case**: Entry breadth DOWN 19%, depth UP 1,200%, basin mass UP 9,400%

**Scripts created**:
- `scripts/analyze-basin-entry-breadth.py` (480 lines)
- `scripts/run-entry-breadth-analysis.sh` (helper wrapper)

**Documentation created**:
- `empirical-investigations/ENTRY-BREADTH-ANALYSIS.md` (investigation spec)
- `empirical-investigations/ENTRY-BREADTH-RESULTS.md` (hypothesis refutation + discovery)
- `ENTRY-BREADTH-README.md` (usage guide)
- `SANITY-CHECK-ENTRY-BREADTH.md` (validation tests)
- `SESSION-SUMMARY-STAT-MECH.md` (framework overview)
- `ENTRY-BREADTH-SESSION-SUMMARY.md` (session results)
- `NEXT-SESSION-DEPTH-MECHANICS.md` (comprehensive handoff)
- `QUICK-START-NEXT-SESSION.md` (fast onboarding)

**Data files created** (30 measurements):
- `data/../analysis/entry_breadth_n={3,4,5,6,7}_full_analysis_2025_12_31.tsv`
- `data/../analysis/entry_breadth_summary_full_analysis_2025_12_31.tsv`
- `data/../analysis/entry_breadth_correlation_full_analysis_2025_12_31.tsv`

**Contract updates**:
- Updated NLR-C-0003 with refuted claim (entry breadth dominance)
- Added supported claim (depth dominance with power-law)
- Added new hypothesis for testing: α ≈ 2.0-2.5

**Next steps**:
- Fit power-law: log(Basin_Mass) vs log(Max_Depth) → extract α
- Analyze depth distributions (mean, median, 90th percentile)
- Test coverage-depth relationship (why does N=5 maximize depth?)
- Investigate hub connectivity hypothesis (high-degree nodes as depth multipliers)

**Commit**: (pending)

---

### 2025-12-31 (Third) - Mechanism Understanding and Massachusetts Case Study

**What was tried**:
- Built path characteristics analyzer (5,000 samples across N∈{3,4,5,6,7})
- Built cycle evolution tracker (6 universal cycles across N)
- Built link profile analyzer (investigated actual Wikipedia article structures)
- Deep-dive on Massachusetts basin (why 94× larger at N=5 than N=4)

**What worked**:
- Path analysis revealed N=4 premature convergence (11 steps median, fastest)
- N=5 has slowest rapid convergence rate (85.9% <50 steps) = broadest exploration
- Cycle evolution tracking identified all 6 universal cycles with size ranges 10× to 1,285×
- Massachusetts link profile: 1,120 outlinks, forms 2-cycle ONLY at N=5 (position 5 → Gulf_of_Maine)
- Mean depth strongly correlates with basin mass (51.3 steps at N=5 vs 3.2 at N=4)

**Key findings**:
- **Premature convergence mechanism**: N=4 converges too fast for broad exploration
- **Optimal exploration time**: N=5's 14% of paths taking >50 steps creates broad catchment
- **Cycle position effect**: Massachusetts forms cycle only at N=5; points to non-cycling articles at other N
- **Hub connectivity amplification**: 1,120 outlinks + cycle formation + optimal exploration = 94× amplification
- Refined basin mass formula: Entry_Breadth × Path_Survival × Convergence_Optimality

**Scripts created**:
- `scripts/analyze-path-characteristics.py` (400 lines)
- `scripts/visualize-mechanism-comparison.py` (200 lines)
- `scripts/compare-cycle-evolution.py` (350 lines)
- `scripts/analyze-cycle-link-profiles.py` (250 lines)

**Documentation created**:
- `empirical-investigations/MECHANISM-ANALYSIS.md` (~12k tokens)
- `empirical-investigations/MASSACHUSETTS-CASE-STUDY.md` (~10k tokens)
- Updated `empirical-investigations/INDEX.md` with 3 new completed investigations

**Visualizations**:
- `report/assets/mechanism_comparison_n3_to_n7.png` (4-panel path mechanisms)
- `report/assets/bottleneck_analysis_n3_to_n7.png` (2-panel concentration)
- `report/assets/cycle_evolution_basin_sizes.png` (universal cycles)
- `report/assets/cycle_dominance_evolution.png` (dominance trends)
- `report/assets/massachusetts_deep_dive.png` (4-panel case study)

**Commit**: (pending)

---

### 2025-12-31 (Second) - Link Degree Analysis and Coverage Threshold Discovery

**What was tried**:
- Extended cross-N analysis to N∈{3,4,5,6,7} (added N=4, N=6)
- Extracted Wikipedia link degree distribution (17.9M pages via DuckDB)
- Correlated coverage percentage with basin mass

**What worked**:
- N=4 and N=6 reproduction pipelines ran successfully (~25 min total)
- DuckDB query for link degrees succeeded (Parquet has corruption issues)
- Discovered N=4 is local minimum (30k nodes, smaller than N=3!)
- Found 32.6% coverage threshold aligns perfectly with N=5 peak
- Near-zero correlation (r=-0.042) confirms non-monotonic relationship

**Key findings**:
- N=5 is isolated spike (65× from N=4), not plateau
- Asymmetric curve: sharp rise (65×) vs gradual fall (7-9×)
- Coverage Paradox: Two competing mechanisms identified
- Predictive hypothesis: Basin peaks at ~30-35% coverage

**Files created**:
- `empirical-investigations/PHASE-TRANSITION-REFINED.md`
- `report/assets/phase_transition_n3_to_n7.png`
- `report/assets/coverage_vs_basin_mass.png`
- `report/assets/coverage_zones_analysis.png`
- `data/../analysis/link_degree_distribution*.tsv` (2 files)
- `data/../analysis/coverage_vs_basin_mass.tsv`

**Commit**: (pending)

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
