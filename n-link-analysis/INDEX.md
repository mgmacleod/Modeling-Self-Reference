# N-Link Analysis Index

**Purpose**: Analysis code and documentation for basin-partition experiments on Wikipedia N-Link sequences  
**Last Updated**: 2025-12-30

---

## Core Files (Load when entering directory)

| File | Tier | Purpose | Tokens |
|------|------|---------|--------|
| [implementation.md](implementation.md) | 2 | Analysis architecture: inputs/outputs, core algorithms, run flow | ~4k |
| [future.md](future.md) | 2 | Next steps (Phase 1 experiments, validation, scaling work) | ~1k |
| [session-log.md](session-log.md) | 2 | Cumulative work log + decisions for analysis work | ~2k |
| [empirical-investigations/INDEX.md](empirical-investigations/INDEX.md) | 2 | Question-scoped empirical investigation streams | ~1k |
| [report/overview.md](report/overview.md) | 2 | Human-facing summary report with charts | ~2k |

---

## Scripts

| Script | Purpose | Status |
|--------|---------|--------|
| [scripts/trace-nlink-path.py](scripts/trace-nlink-path.py) | Trace a single N-link path (sanity check) | Active |
| [scripts/sample-nlink-traces.py](scripts/sample-nlink-traces.py) | Sample many traces; summarize terminal + cycle frequencies | Active |
| [scripts/find-nlink-preimages.py](scripts/find-nlink-preimages.py) | Find preimages under fixed-N (Nth-link indegree) | Active |
| [scripts/map-basin-from-cycle.py](scripts/map-basin-from-cycle.py) | Map basin by reverse expansion from a cycle | Active |
| [scripts/branch-basin-analysis.py](scripts/branch-basin-analysis.py) | Partition a basin into depth-1 entry subtrees (“branches”) and summarize thickness | Active |
| [scripts/chase-dominant-upstream.py](scripts/chase-dominant-upstream.py) | Iteratively follow the dominant upstream branch (“source of the Nile” chase) | Active |
| [scripts/compute-trunkiness-dashboard.py](scripts/compute-trunkiness-dashboard.py) | Aggregate multiple branch tables into a single “trunkiness dashboard” TSV | Active |
| [scripts/batch-chase-collapse-metrics.py](scripts/batch-chase-collapse-metrics.py) | Batch-run chases to a dominance threshold and write a “collapse dashboard” TSV | Active |
| [scripts/dash-tributary-viewer.py](scripts/dash-tributary-viewer.py) | Dash app to interactively render the 3D tributary skeleton (avoid many HTML exports) | Active |
| [scripts/compute-basin-stats.py](scripts/compute-basin-stats.py) | Compute basin/terminal statistics for fixed N set | Placeholder |
| [scripts/compute-universal-attractors.py](scripts/compute-universal-attractors.py) | Aggregate terminals across N to find universal attractors | Placeholder |
| [scripts/quick-queries.py](scripts/quick-queries.py) | DuckDB sanity queries for parquet outputs | Placeholder |

---

## Inputs / Outputs

**Primary input**: `data/wikipedia/processed/nlink_sequences.parquet` (page_id, link_sequence)  
**Outputs** (planned): `data/wikipedia/processed/analysis/` (gitignored)

---

## Usage

**First time here**: Load implementation.md  
**Running analysis**: Use scripts under `scripts/` (to be implemented)

**Empirical session bootstrap (minimal)**:
1. Verify inputs exist: `data/wikipedia/processed/nlink_sequences.parquet` (and optionally `pages.parquet`).
2. Run a small sanity sample (example): `python n-link-analysis/scripts/sample-nlink-traces.py --n 5 --num 100`.
3. Record results in the relevant investigation doc under `empirical-investigations/` and update the contracts registry if the result changes evidence status.
