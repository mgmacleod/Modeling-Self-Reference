# N-Link Basin Analysis - Implementation

**Document Type**: Implementation  
**Target Audience**: LLMs + Developers  
**Purpose**: Define how to compute basin partitions and validation metrics from Wikipedia N-Link sequences  
**Last Updated**: 2025-12-31  
**Dependencies**: [../data-pipeline/wikipedia-decomposition/INDEX.md](../data-pipeline/wikipedia-decomposition/INDEX.md), [../llm-facing-documentation/theories-proofs-conjectures/n-link-rule-theory.md](../llm-facing-documentation/theories-proofs-conjectures/n-link-rule-theory.md)  
**Status**: Draft

---

## Overview

This directory is the **analysis layer** for empirically validating N-Link Rule Theory using the pipeline output:
- `data/wikipedia/processed/nlink_sequences.parquet` with schema `(page_id: int64, link_sequence: list<int64>)`.

For a fixed $N$ (1-indexed), the induced deterministic map is:
$$
  f_N(\text{page}) =
  \begin{cases}
    \text{link\_sequence}[N-1] & \text{if } |\text{link\_sequence}| \ge N \\
    \text{HALT} & \text{otherwise.}
  \end{cases}
$$

The analysis goal is to compute:
- terminal classification (HALT vs CYCLE),
- basin partition statistics (terminal counts, basin size distribution),
- within-basin structure metrics (depth-1 entry branch concentration; dominant-upstream “trunk” behavior),
- cross-$N$ comparisons (terminal overlap, universal attractors),
- conjecture checks (monotone $P_{HALT}(N)$, heavy-tail basin sizes, candidate $N^*$).

---

## Data Sources

Analysis scripts support two data sources via the `data_loader.py` module:

### Local Data (Default)
- **Location**: `data/wikipedia/processed/`
- **Usage**: Default behavior, no flags needed
- **Files**:
  - `nlink_sequences.parquet` - Link sequences per page
  - `pages.parquet` - Page ID to title mapping
  - `multiplex/` - Pre-computed cross-N analysis results

### HuggingFace Dataset
- **Repository**: `mgmacleod/wikidata1`
- **Usage**: Add `--data-source huggingface` to any script
- **Cache**: Downloaded to `~/.cache/wikipedia-nlink-basins/`
- **Files**: Same structure as local, under `data/source/` and `data/multiplex/`

### Data Loader Module

The `scripts/data_loader.py` module provides a unified interface:

```python
from data_loader import get_data_loader, add_data_source_args

# In script main():
parser = argparse.ArgumentParser()
add_data_source_args(parser)  # Adds --data-source, --hf-repo, etc.
args = parser.parse_args()

loader = get_data_loader_from_args(args)
nlink_path = loader.nlink_sequences_path
pages_path = loader.pages_path
```

**Environment Variables**:
- `DATA_SOURCE`: "local" or "huggingface"
- `HF_DATASET_REPO`: Override HuggingFace repo ID
- `HF_CACHE_DIR`: Custom cache directory

---

## Inputs

### Required

- `nlink_sequences.parquet` (from local or HuggingFace)
  - Columns: `page_id`, `link_sequence` (list of resolved target page_ids)

### Optional (for labeling / interpretation)

- `pages.parquet` (title lookup for reporting)

---

## Outputs

Write analysis results to a new folder (gitignored):
- `data/wikipedia/processed/analysis/`

Empirical findings are documented separately (not in `session-log.md`):
- `n-link-analysis/empirical-investigations/` (question-scoped streams)

Each investigation document should include:
- the exact script(s) used,
- the exact commands/parameters used,
- the output artifact paths,
- and the formalized findings tied back to specific theory questions/conjectures.

Planned artifacts (format: Parquet):
- `basin_stats_N={N}.parquet`: per-terminal metrics (terminal_id, type, basin_size, cycle_length)
- `summary_over_N.parquet`: one row per N (P_HALT, num_terminals, largest_basin, etc.)
- `universal_attractors.parquet`: terminal frequency across N

### Visualization Artifacts (Human-Facing)

Some workflows export a *basin point cloud* artifact for interactive inspection:
- Parquet schema: `(page_id, parent_id, depth, x, y, z)`
- Output location: `data/wikipedia/processed/analysis/` (gitignored)

Visualization tooling lives in `n-link-analysis/viz/` and is intentionally Parquet-first:
- `viz/render-full-basin-geometry.py` exports the artifact.
- `viz/dash-basin-geometry-viewer.py` renders it (3D + 2D views).

---

## Core Computation Strategy (Performance Constraint)

### Functional Graph View

For each fixed $N$, $f_N$ defines a **functional graph** over nodes that do not HALT.
This enables linear-time algorithms (in number of nodes) for:
- cycle detection,
- assigning each node to its terminal,
- aggregating basin sizes.

### Scale Constraint

The dataset is large (~18M pages with sequences). Any implementation must avoid:
- per-node Python traversal loops over full paths,
- repeated random access into nested Python lists,
- building huge Python dicts without careful memory accounting.

This document intentionally does not specify the exact algorithmic implementation yet; it will be crystallized once the first analysis scripts are implemented and benchmarked.

---

## Planned Experiments (Baseline)

### Phase 1: Fixed-N Rules

Run $N \in \{1,2,3,4,5,10,20\}$ and measure:
- $|\mathcal{T}_N|$ (terminal count)
- $P_{HALT}(N)$ and $P_{CYCLE}(N)$
- basin size distribution
- top terminal identities

### Phase 2+: Generalized Rules

Implement and evaluate non-fixed rules (mod-K, adaptive depth, cycle-avoiding), as defined in the theory docs.

---

## Scripts

Scripts live in `scripts/` and are intended to be runnable from repo root with the configured venv.

- `scripts/compute-basin-stats.py` (placeholder)
- `scripts/compute-universal-attractors.py` (placeholder)
- `scripts/quick-queries.py` (placeholder)
