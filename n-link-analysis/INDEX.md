# N-Link Analysis Index

**Purpose**: Analysis code and documentation for basin-partition experiments on Wikipedia N-Link sequences
**Last Updated**: 2026-01-01

---

## Core Files (Load when entering directory)

| File | Tier | Purpose | Tokens |
|------|------|---------|--------|
| [implementation.md](implementation.md) | 2 | Analysis architecture: inputs/outputs, core algorithms, run flow | ~4k |
| [scripts-reference.md](scripts-reference.md) | 2 | Complete reference for all analysis scripts (parameters, I/O, theory connections) | ~15k |
| [NEXT-STEPS.md](NEXT-STEPS.md) | 2 | Prioritized next steps: Multi-N analysis, hub connectivity, theory validation | ~6k |
| [future.md](future.md) | 2 | Next steps (Phase 1 experiments, validation, scaling work) | ~1k |
| [session-log.md](session-log.md) | 2 | Cumulative work log + decisions for analysis work | ~2k |
| [empirical-investigations/INDEX.md](empirical-investigations/INDEX.md) | 2 | Question-scoped empirical investigation streams | ~1k |
| [report/overview.md](report/overview.md) | 2 | Human-facing summary report with charts | ~2k |

---

## Deep Dives (Tier 3)

These are substantial, question-scoped writeups and validation artifacts. Most of the new Markdown your friend added lives here.

| File | Tier | Topic | Tokens |
|------|------|-------|--------|
| [FRAMEWORK-TESTING-PLAN.md](FRAMEWORK-TESTING-PLAN.md) | 3 | Systematic framework validation plan + test results (N=2–10 coverage) | ~8k |
| [ENTRY-BREADTH-README.md](ENTRY-BREADTH-README.md) | 3 | Entry-breadth hypothesis: definition, methods, interpretation | ~4k |
| [SANITY-CHECK-ENTRY-BREADTH.md](SANITY-CHECK-ENTRY-BREADTH.md) | 3 | Sanity-check notebook-style writeup for entry-breadth pipeline | ~5k |
| [empirical-investigations/REPRODUCTION-OVERVIEW.md](empirical-investigations/REPRODUCTION-OVERVIEW.md) | 3 | Cross-N reproduction: universality vs N-dependence | ~6k |
| [empirical-investigations/PHASE-TRANSITION-REFINED.md](empirical-investigations/PHASE-TRANSITION-REFINED.md) | 3 | Refined phase transition analysis (why N=4 minimum / N=5 peak) | ~5k |
| [empirical-investigations/MECHANISM-ANALYSIS.md](empirical-investigations/MECHANISM-ANALYSIS.md) | 3 | Mechanism: premature convergence and depth dynamics | ~5k |
| [empirical-investigations/MASSACHUSETTS-CASE-STUDY.md](empirical-investigations/MASSACHUSETTS-CASE-STUDY.md) | 3 | Massachusetts case study (hub connectivity + cycle formation) | ~5k |
| [empirical-investigations/ENTRY-BREADTH-ANALYSIS.md](empirical-investigations/ENTRY-BREADTH-ANALYSIS.md) | 3 | Entry breadth vs basin mass (analysis + model comparison) | ~4k |
| [empirical-investigations/ENTRY-BREADTH-RESULTS.md](empirical-investigations/ENTRY-BREADTH-RESULTS.md) | 3 | Entry breadth results summary (hypothesis outcome) | ~4k |
| [empirical-investigations/DEPTH-SCALING-ANALYSIS.md](empirical-investigations/DEPTH-SCALING-ANALYSIS.md) | 3 | Depth–mass power-law scaling (α estimation) | ~6k |
| [empirical-investigations/DEPTH-DISTRIBUTION-ANALYSIS.md](empirical-investigations/DEPTH-DISTRIBUTION-ANALYSIS.md) | 3 | Depth distribution shapes + predictive metrics | ~6k |

---

## Scripts

**For complete documentation**: See [scripts-reference.md](scripts-reference.md)

| Script | Purpose | Status |
|--------|---------|--------|
| [scripts/validate-data-dependencies.py](scripts/validate-data-dependencies.py) | Validate data files and schema (run first) | Active |
| [scripts/reproduce-main-findings.py](scripts/reproduce-main-findings.py) | **Reproduce all main empirical findings** (complete pipeline) | Active |
| [scripts/trace-nlink-path.py](scripts/trace-nlink-path.py) | Trace a single N-link path (sanity check) | Active |
| [scripts/sample-nlink-traces.py](scripts/sample-nlink-traces.py) | Sample many traces; summarize terminal + cycle frequencies | Active |
| [scripts/find-nlink-preimages.py](scripts/find-nlink-preimages.py) | Find preimages under fixed-N (Nth-link indegree) | Active |
| [scripts/map-basin-from-cycle.py](scripts/map-basin-from-cycle.py) | Map basin by reverse expansion from a cycle | Active |
| [scripts/branch-basin-analysis.py](scripts/branch-basin-analysis.py) | Partition a basin into depth-1 entry subtrees ("branches") and summarize thickness | Active |
| [scripts/chase-dominant-upstream.py](scripts/chase-dominant-upstream.py) | Iteratively follow the dominant upstream branch ("source of the Nile" chase) | Active |
| [scripts/compute-trunkiness-dashboard.py](scripts/compute-trunkiness-dashboard.py) | Aggregate multiple branch tables into a single "trunkiness dashboard" TSV | Active |
| [scripts/batch-chase-collapse-metrics.py](scripts/batch-chase-collapse-metrics.py) | Batch-run chases to a dominance threshold and write a "collapse dashboard" TSV | Active |
| [scripts/render-tributary-tree-3d.py](scripts/render-tributary-tree-3d.py) | Render an interactive 3D tributary skeleton (HTML export) | Active |
| [scripts/compute-basin-stats.py](scripts/compute-basin-stats.py) | Compute basin/terminal statistics for fixed N set | Placeholder |
| [scripts/compute-universal-attractors.py](scripts/compute-universal-attractors.py) | Aggregate terminals across N to find universal attractors | Placeholder |
| [scripts/quick-queries.py](scripts/quick-queries.py) | DuckDB sanity queries for parquet outputs | Placeholder |

---

## Visualization (Human-Facing)

**For complete documentation**: See [viz/README.md](viz/README.md)

| Tool | Purpose | Status |
|------|---------|--------|
| [viz/batch-render-basin-images.py](viz/batch-render-basin-images.py) | Batch render basin visualizations as static images (PNG/SVG/PDF) with customizable styles | Active |
| [viz/generate-publication-figures.sh](viz/generate-publication-figures.sh) | One-click generation of complete publication figure set (multiple resolutions and colorscales) | Active |
| [viz/generate-style-variants.sh](viz/generate-style-variants.sh) | Generate 5 colorscale variants per basin (Viridis, Plasma, Inferno, Cividis, Greys) | Active |
| [viz/create-visualization-gallery.py](viz/create-visualization-gallery.py) | Generate responsive HTML gallery for browsing all visualizations | Active |
| [viz/render-full-basin-geometry.py](viz/render-full-basin-geometry.py) | Map a basin exhaustively and export 3D point-cloud (Parquet + optional HTML preview) | Active |
| [viz/dash-basin-geometry-viewer.py](viz/dash-basin-geometry-viewer.py) | Interactive Dash app for exploring basin geometry (3D violin, 2D interval, 2D fan+edges) | Active |

---

## Inputs / Outputs

**Primary input**: `data/wikipedia/processed/nlink_sequences.parquet` (page_id, link_sequence)  
**Outputs** (planned): `data/wikipedia/processed/analysis/` (gitignored)

---

## Usage

**First time here**: Load [implementation.md](implementation.md)
**Running analysis**: See [scripts-reference.md](scripts-reference.md) for complete script documentation

**Empirical session bootstrap**:

1. **Validate data** (always run first):
   ```bash
   source .venv/bin/activate
   python n-link-analysis/scripts/validate-data-dependencies.py
   ```

2. **Reproduce main findings** (complete pipeline):
   ```bash
   # Quick mode (~10-30 min)
   python n-link-analysis/scripts/reproduce-main-findings.py --quick

   # Full reproduction (~2-6 hours)
   python n-link-analysis/scripts/reproduce-main-findings.py
   ```

3. **Manual exploration** (individual scripts):
   - See [scripts-reference.md](scripts-reference.md) for detailed documentation
   - Example: `python n-link-analysis/scripts/sample-nlink-traces.py --n 5 --num 100`

4. **Document findings**:
   - Record results in investigation docs under `empirical-investigations/`
   - Update contracts registry if evidence status changes
