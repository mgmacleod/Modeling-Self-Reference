# Contract Registry

**Purpose**: A registry of explicit theory–experiment–evidence contracts.

This is the *primary index* for contract objects, and should be treated as append-only (you can add new entries; avoid rewriting old ones except to mark them deprecated).

**Last Updated**: 2026-01-01 (Session: Multi-N Phase Transition Complete N=3-10)

---

## Active Contracts

### NLR-C-0001 — Long-tail basin size under fixed-N traversal (Wikipedia proving ground)

- **Status**: supported (empirical; scope: Wikipedia namespace 0, non-redirect pages)
- **Theory**:
  - [n-link-rule-theory.md](../theories-proofs-conjectures/n-link-rule-theory.md) (basins, cycles, terminals)
  - [unified-inference-theory.md](../theories-proofs-conjectures/unified-inference-theory.md) (integration framing)
- **Experiment**:
  - [map-basin-from-cycle.py](../../n-link-analysis/scripts/map-basin-from-cycle.py) (reverse reachability / basin mapping)
  - [sample-nlink-traces.py](../../n-link-analysis/scripts/sample-nlink-traces.py) (cycle sampling)
- **Evidence**:
  - [long-tail-basin-size.md](../../n-link-analysis/empirical-investigations/long-tail-basin-size.md)
  - Outputs under `data/wikipedia/processed/analysis/`
- **Notes**:
  - This contract is intentionally "Wikipedia-first" to preserve cultural salience and reduce concerns of bespoke/system-fit bias.

---

### NLR-C-0003 — N-dependent phase transition in basin structure (Wikipedia)

- **Status**: supported (empirical; scope: Wikipedia namespace 0, non-redirect pages, N∈{3,4,5,6,7,8,9,10})
- **Theory**:
  - [n-link-rule-theory.md](../theories-proofs-conjectures/n-link-rule-theory.md) (N-link rule definition, basin partitioning)
  - Extends NLR-C-0001 to cross-N comparison
- **Experiment**:
  - [reproduce-main-findings.py](../../n-link-analysis/scripts/reproduce-main-findings.py) (parameterized by N)
  - [compare-across-n.py](../../n-link-analysis/scripts/compare-across-n.py) (cross-N analysis)
  - [map-basin-from-cycle.py](../../n-link-analysis/scripts/map-basin-from-cycle.py) (basin mapping)
  - [sample-nlink-traces.py](../../n-link-analysis/scripts/sample-nlink-traces.py) (cycle sampling)
  - [analyze-path-characteristics.py](../../n-link-analysis/scripts/analyze-path-characteristics.py) (path-level mechanism analysis)
  - [compare-cycle-evolution.py](../../n-link-analysis/scripts/compare-cycle-evolution.py) (individual cycle tracking across N)
  - [analyze-cycle-link-profiles.py](../../n-link-analysis/scripts/analyze-cycle-link-profiles.py) (article link structure analysis)
  - [analyze-basin-entry-breadth.py](../../n-link-analysis/scripts/analyze-basin-entry-breadth.py) (entry breadth measurement and depth analysis)
  - [explore-depth-structure-large-scale.py](../../n-link-analysis/scripts/explore-depth-structure-large-scale.py) (large-scale power-law fitting and visualization)
  - [interactive-depth-explorer.py](../../n-link-analysis/scripts/interactive-depth-explorer.py) (web-based interactive exploration UI)
  - [analyze-depth-distributions.py](../../n-link-analysis/scripts/analyze-depth-distributions.py) (full depth distribution statistics and correlation analysis)
  - [interactive-depth-explorer-enhanced.py](../../n-link-analysis/scripts/interactive-depth-explorer-enhanced.py) (enhanced UI with distribution histograms, variance, and skewness visualization)
  - [analyze-phase-transition-n3-n10.py](../../n-link-analysis/scripts/analyze-phase-transition-n3-n10.py) (comprehensive N=3-10 phase curve analysis and visualization)
- **Evidence**:
  - [REPRODUCTION-OVERVIEW.md](../../n-link-analysis/empirical-investigations/REPRODUCTION-OVERVIEW.md) (N∈{3,5,7} comprehensive summary)
  - [PHASE-TRANSITION-REFINED.md](../../n-link-analysis/empirical-investigations/PHASE-TRANSITION-REFINED.md) (N∈{3,4,5,6,7} refined analysis)
  - [MULTI-N-PHASE-MAP.md](../../n-link-analysis/empirical-investigations/MULTI-N-PHASE-MAP.md) (N∈{3,4,5,6,7,8,9,10} complete phase transition curve)
  - [MECHANISM-ANALYSIS.md](../../n-link-analysis/empirical-investigations/MECHANISM-ANALYSIS.md) (premature convergence mechanism, path characteristics)
  - [MASSACHUSETTS-CASE-STUDY.md](../../n-link-analysis/empirical-investigations/MASSACHUSETTS-CASE-STUDY.md) (cycle formation + hub connectivity case study)
  - [ENTRY-BREADTH-RESULTS.md](../../n-link-analysis/empirical-investigations/ENTRY-BREADTH-RESULTS.md) (entry breadth hypothesis refuted, depth dominance discovered)
  - [DEPTH-SCALING-ANALYSIS.md](../../n-link-analysis/empirical-investigations/DEPTH-SCALING-ANALYSIS.md) (universal power-law: Basin_Mass ∝ Depth^2.5, α distribution across cycles)
  - [DEPTH-DISTRIBUTION-ANALYSIS.md](../../n-link-analysis/empirical-investigations/DEPTH-DISTRIBUTION-ANALYSIS.md) (depth distribution statistics, variance explosion at N=5, bimodal patterns, skewness analysis)
  - [CROSS-N-FINDINGS.md](../../CROSS-N-FINDINGS.md) (publication-quality discovery summary)
  - Phase transition visualizations: `n-link-analysis/report/assets/phase_transition_n3_to_n10_comprehensive.png`, `massachusetts_evolution_n3_to_n10.png`, `universal_cycles_heatmap_n3_to_n10.png`
  - Coverage analysis: `n-link-analysis/report/assets/coverage_vs_basin_mass.png`, `coverage_zones_analysis.png`
  - Cross-N visualizations: `n-link-analysis/report/assets/cross_n_*.png` (6 charts)
  - Mechanism visualizations: `n-link-analysis/report/assets/mechanism_comparison_n3_to_n7.png`, `bottleneck_analysis_n3_to_n7.png`
  - Cycle visualizations: `n-link-analysis/report/assets/cycle_evolution_basin_sizes.png`, `cycle_dominance_evolution.png`, `massachusetts_deep_dive.png`
  - Path characteristics data: `data/wikipedia/processed/analysis/path_characteristics_n={3,4,5,6,7,8,9,10}_*` (24 files)
  - Cycle evolution data: `data/wikipedia/processed/analysis/cycle_evolution_summary.tsv` (111 rows, N=3-10), `cycle_dominance_matrix.tsv`, `phase_transition_statistics_n3_to_n10.tsv`
  - Data outputs: `data/wikipedia/processed/analysis/*_n={3,4,5,6,7,8,9,10}_*` (~150+ files total)
  - Link degree distribution: `data/wikipedia/processed/analysis/link_degree_distribution*.tsv`
  - Entry breadth data: `data/wikipedia/processed/analysis/entry_breadth_n={3,4,5,6,7}_full_analysis_2025_12_31.tsv`, `entry_breadth_summary_*.tsv`
  - Depth scaling analysis: `data/wikipedia/processed/analysis/depth_exploration/power_law_fit_parameters.tsv`, 6 visualization PNGs
  - Depth distribution data: `data/wikipedia/processed/analysis/depth_distributions/depth_statistics_by_n.tsv`, `depth_predictor_correlations.tsv`, 2 visualization PNGs
- **Key Finding**:
  - **Validated N=3-10**: N=5 is isolated spike (62.6× amplification from N=4 to 3.85M nodes), NOT a plateau
  - **Phase cliff confirmed**: N=5 → N=9 collapse is 112× (sharpest drop), N=5 → N=8 is 43.5×, N=5 → N=10 is 91.9×
  - **N=4 local minimum**: 61k nodes - smaller than N=3 (407k) by 6.6×! Asymmetric curve: sharp rise (62.6×), sharp fall (43-112×)
  - **Massachusetts 315× collapse**: 1,009,471 nodes (N=5) → 3,205 nodes (N=9), mean depth 51.3 → 3.2 steps
  - N=5 captures **21.5% of Wikipedia** (3.85M/17.9M nodes) in basin structures
  - N=5 peak aligns precisely with 32.6% page coverage (5.9M pages with ≥5 links)
  - Coverage vs basin mass: near-zero correlation (r=-0.042) confirms non-monotonic relationship
  - **One of sharpest phase transitions in network science** (comparable to thermodynamic transitions)
  - **Mechanism identified**: Premature convergence at N=4 (paths converge in 11 steps, too fast for broad exploration)
  - **Optimal exploration at N=5**: Paths converge in 12 steps median, but 14% take >50 steps (broadest catchment)
  - **Cycle position matters**: Massachusetts forms 2-cycle ONLY at N=5 (5th link → Gulf_of_Maine → 5th link → Massachusetts)
  - **Hub connectivity amplifies**: Massachusetts has 1,120 outlinks, major geographic/political hub, mean basin depth 51.3 steps at N=5 vs 3.2 at N=4
  - Same 6 terminal cycles persist across N with radically different properties (up to 4289× size variation)
- **Theory Claim Evaluated**:
  - **Refuted**: "Basin structure is universal across N" → Structure is rule-dependent, not graph-intrinsic
  - **Refuted**: "Entry breadth dominates basin mass" → Entry breadth DECREASES with N (0.75× from N=4→N=5), opposite of prediction
  - **Supported**: "Finite self-referential graphs partition into basins under deterministic rules" → Holds for all N∈{3,4,5,6,7}
  - **Supported**: "Depth dominates basin mass" → Basin depth increases 13× (N=4→N=5), explains 65× mass amplification
  - **Supported**: "Basin mass = Entry_Breadth × Depth^α × Path_Survival" → Universal power-law confirmed: α = 2.50 ± 0.48 (6 cycles, mean R²=0.878)
  - **Supported**: "Super-quadratic depth scaling" → α > 2 suggests fractal branching or preferential attachment (log correlation r=0.922)
  - **Supported**: "Variance drives basin mass amplification" → N=5 variance explosion (σ²=473, 4× higher than N=4) creates exploratory tail that dominates basin mass
  - **Supported**: "N=5 exhibits bimodal-like convergence" → Two-phase distribution (85% rapid local convergence + 15% deep exploration) confirmed by skewness=1.88
  - **New hypothesis**: Basin mass peaks occur at ~30-35% coverage threshold (potentially universal for scale-free networks)
  - **New hypothesis**: α varies by cycle geometry: Low-α (1.87, broad cones) vs High-α (3.06, narrow funnels), predictable from graph topology
  - **New hypothesis**: Depth variance correlates with α exponent (high variance → low α → broad cone geometry)
- **Notes**:
  - Basin properties emerge from rule-graph coupling (deterministic rule selectivity × graph degree distribution)
  - Critical phenomena framework validated: N=5 exhibits phase transition-like behavior
  - Coverage Paradox documented: Basin mass is non-monotonic function of connectivity
  - Premature convergence regime discovered: Paths can converge TOO FAST, preventing broad exploration
  - Cycle formation position effect: Hub articles forming cycles at optimal N capture maximum basin mass
  - Predictive framework: For any graph, measure degree distribution → find N where coverage ≈ 33% → predict basin peak
  - Next steps: Entry breadth validation, percolation modeling, cross-domain testing (other Wikipedias, citation networks)

---

### NLR-C-0002 — Citation & integration lineage for sqsd.html → N-Link theory

- **Status**: proposed
- **Goal**: Ensure every usage of `sqsd.html` is explicitly attributed, scoped, and linked into the theory–experiment–evidence chain without “stealth integration” into canonical theory.
- **External Artifact (source)**:
  - [sqsd.html](../theories-proofs-conjectures/sqsd.html) — Ryan Querin (external)
- **Theory (targets / touchpoints)**:
  - [n-link-rule-theory.md](../theories-proofs-conjectures/n-link-rule-theory.md) (if/when SQSD concepts are cited)
  - [database-inference-graph-theory.md](../theories-proofs-conjectures/database-inference-graph-theory.md) (if/when SQSD concepts are cited)
  - [unified-inference-theory.md](../theories-proofs-conjectures/unified-inference-theory.md) (if/when SQSD concepts are cited)
- **Evidence**:
  - Add a dedicated investigation doc when SQSD is first used for an empirical argument (e.g., under `n-link-analysis/empirical-investigations/`).
- **Operational rules**:
  - Do not quote or embed large portions of `sqsd.html` into canonical theory; prefer high-level references.
  - Any canonical-theory citation should be additive (append-only) and must include author credit.
  - Before broader redistribution, record explicit permission/license terms for `sqsd.html` under `EXT-A-0001`.

---

## External / Third-Party Artifacts (Referenced by Contracts)

### EXT-A-0001 — sqsd.html (Structural Query Semantics as a Deterministic Space)

- **Status**: referenced (not yet integrated into canonical theory)
- **Artifact**: [sqsd.html](../theories-proofs-conjectures/sqsd.html)
- **Author**: Ryan Querin
- **Relationship**: authored externally; explicitly based on (and extending) project work
- **Redistribution / License**: TODO — record explicit permission and license terms before wider distribution
- **Integration policy**:
  - Do not treat as canonical theory.
  - When used, reference via explicit contract entries (and cite author).
