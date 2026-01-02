# Wikipedia N-Link Basin Analysis Dataset

**Dataset for**: Hugging Face
**Version**: 1.0.0
**Created**: 2026-01-01
**Source**: English Wikipedia (enwiki-20251220)
**License**: CC BY-SA 4.0 (same as Wikipedia)

---

## Overview

This dataset contains the complete **N-Link Rule analysis** of English Wikipedia's internal link graph. It demonstrates that Wikipedia's 17.9 million pages partition into deterministic "basins of attraction" under simple traversal rules, with a dramatic phase transition at N=5.

### What is the N-Link Rule?

For any Wikipedia page, follow the **Nth link** in the article body repeatedly. Every page eventually reaches a **cycle** (closed loop). All pages flowing to the same cycle form its **basin of attraction**.

### Key Findings

| Finding | Value |
|---------|-------|
| Total pages analyzed | 17,972,018 |
| Phase transition peak | N=5 |
| Basin collapse factor | 10-1000× (N=5 vs N=10) |
| Tunnel nodes | 9,018 (switch basins across N) |
| Dominant tunneling mechanism | 99.3% degree_shift |

---

## Dataset Structure

```
wikipedia-nlink-basins/
├── source/                      # Foundation data
│   ├── nlink_sequences.parquet  # Core: page_id → first 3873 links
│   └── pages.parquet            # Page metadata (id, title, namespace)
├── analysis/                    # Per-N basin assignments
│   └── branches_n=*_*.parquet   # Individual basin memberships
└── multiplex/                   # Cross-N analysis (main dataset)
    ├── multiplex_basin_assignments.parquet
    ├── tunnel_nodes.parquet
    ├── multiplex_edges.parquet
    └── *.tsv                    # Human-readable summaries
```

---

## Core Files

### 1. Source Data

#### `nlink_sequences.parquet` (687 MB, 17.97M rows)

The foundation dataset: every Wikipedia page with its ordered link sequence.

| Column | Type | Description |
|--------|------|-------------|
| `page_id` | int64 | Wikipedia page ID |
| `link_sequence` | list[int64] | Ordered list of linked page_ids (first N links in article) |

**Usage**: Compute basin membership for any N by following `link_sequence[N-1]` repeatedly.

```python
import pandas as pd
df = pd.read_parquet('nlink_sequences.parquet')
# Get 5th link for page 12345
fifth_link = df[df.page_id == 12345]['link_sequence'].iloc[0][4]
```

#### `pages.parquet` (940 MB, 64.7M rows)

Page metadata for resolving IDs to titles.

| Column | Type | Description |
|--------|------|-------------|
| `page_id` | int32 | Wikipedia page ID |
| `namespace` | int16 | Wikipedia namespace (0 = main article) |
| `title` | string | Page title |
| `is_redirect` | bool | Whether page is a redirect |

---

### 2. Multiplex Analysis (Primary Dataset)

#### `multiplex_basin_assignments.parquet` (11.7 MB, 2.13M rows)

Unified table of basin assignments across all N values.

| Column | Type | Description |
|--------|------|-------------|
| `page_id` | int64 | Wikipedia page ID |
| `N` | int8 | N-link rule value (3-10) |
| `cycle_key` | string | Basin/cycle identifier |
| `canonical_cycle_id` | string | Normalized cycle name |
| `entry_id` | int64 | Entry point page_id |
| `depth` | int32 | Steps from cycle under this N |

**Note**: Only pages with analyzed cycles are included (~2M pages across N=3-10).

#### `tunnel_nodes.parquet` (9.7 MB, 2.02M rows)

Per-page basin membership across N values, identifying tunnel nodes.

| Column | Type | Description |
|--------|------|-------------|
| `page_id` | int64 | Wikipedia page ID |
| `basin_at_N3` | string | Basin membership at N=3 (null if not analyzed) |
| `basin_at_N4` | string | Basin membership at N=4 |
| `basin_at_N5` | string | Basin membership at N=5 |
| `basin_at_N6` | string | Basin membership at N=6 |
| `basin_at_N7` | string | Basin membership at N=7 |
| `n_distinct_basins` | int8 | Count of unique basins across N |
| `is_tunnel_node` | bool | True if page switches basins |

**Key Statistic**: 9,018 pages are tunnel nodes (0.45%).

#### `multiplex_edges.parquet` (87 MB, 9.69M edges)

The multiplex graph structure with both within-N and tunnel edges.

| Column | Type | Description |
|--------|------|-------------|
| `src_page_id` | int64 | Source page ID |
| `src_N` | int8 | Source N value |
| `dst_page_id` | int64 | Destination page ID |
| `dst_N` | int8 | Destination N value |
| `edge_type` | string | "within_N" or "tunnel" |

---

### 3. Human-Readable Summaries (TSV)

| File | Rows | Description |
|------|------|-------------|
| `tunnel_frequency_ranking.tsv` | 9,018 | Ranked tunnel nodes by importance score |
| `tunnel_classification.tsv` | 9,018 | Tunnel type per node |
| `tunnel_mechanisms.tsv` | 9,134 | Mechanism (degree_shift vs path_divergence) per transition |
| `basin_flows.tsv` | 16 | Cross-basin page flow counts |
| `basin_stability_scores.tsv` | 9 | Per-basin stability metrics |
| `cycle_identity_map.tsv` | 15 | Canonical cycle name mapping |

---

## Key Cycles/Basins

The analysis focuses on 9 major basins that capture ~2M pages at N=5:

| Basin | N=5 Size | N=10 Size | Collapse |
|-------|----------|-----------|----------|
| Massachusetts ↔ Gulf_of_Maine | 1,009,471 | 5,226 | 193× |
| Sea_salt ↔ Seawater | 265,896 | 4,391 | 61× |
| Mountain ↔ Hill | 188,968 | 801 | 236× |
| Autumn ↔ Summer | 162,689 | 148 | 1,100× |
| Kingdom_(biology) ↔ Animal | 112,805 | 7,867 | 14× |
| Latvia ↔ Lithuania | 81,656 | 2,499 | 33× |

---

## Empirical Findings

### Phase Transition at N=5

N=5 produces uniquely large basins. Basin sizes collapse by 10-1000× when moving to N=10.

### Tunneling Behavior

- **9,018 pages** switch basins as N changes
- **99.3%** of tunneling caused by "degree_shift" (different Nth link)
- **N=5→N=6** transition accounts for 53% of all tunneling
- Shallow nodes (low depth) tunnel more than deep nodes (r = -0.83)

### Hub Hypothesis Refuted

Tunnel nodes have **lower** average out-degree (31.8) than non-tunnel nodes (34.0). Tunneling is about position (depth), not connectivity.

---

## Theory Foundation

This dataset validates predictions from **N-Link Rule Theory**:

1. **Basin Partition Theorem**: Every finite graph partitions into disjoint basins under any deterministic traversal rule.

2. **Multiplex Interpretation**: Fixed-N basins are 1D slices of a higher-dimensional multiplex structure connected by "tunneling" at shared nodes.

3. **Phase Transition**: There exists a critical N value where basin structure changes dramatically (empirically: N=5 for Wikipedia).

---

## Usage Examples

### Find basin for any page at N=5

```python
import pandas as pd

# Load data
basins = pd.read_parquet('multiplex/multiplex_basin_assignments.parquet')

# Find basin for page_id 12345 at N=5
result = basins[(basins.page_id == 12345) & (basins.N == 5)]
print(result['canonical_cycle_id'].values)
```

### Identify tunnel nodes

```python
tunnels = pd.read_parquet('multiplex/tunnel_nodes.parquet')
tunnel_pages = tunnels[tunnels.is_tunnel_node]
print(f"Tunnel nodes: {len(tunnel_pages):,}")
```

### Trace N-link path

```python
import pandas as pd

seqs = pd.read_parquet('source/nlink_sequences.parquet')
pages = pd.read_parquet('source/pages.parquet')

def trace_path(start_id, n, max_steps=50):
    """Follow Nth link from start_id."""
    path = [start_id]
    current = start_id
    for _ in range(max_steps):
        row = seqs[seqs.page_id == current]
        if row.empty:
            break
        links = row['link_sequence'].iloc[0]
        if len(links) < n:
            break  # HALT: not enough links
        current = links[n-1]
        if current in path:
            return path, current  # CYCLE found
        path.append(current)
    return path, None

path, cycle_entry = trace_path(12345, n=5)
```

---

## Reproducibility

### Source Data

- **Wikipedia dump**: enwiki-20251220 (December 2025)
- **Extraction**: Custom Python pipeline extracting first N links from article prose

### Analysis Scripts

All analysis scripts available at: `n-link-analysis/scripts/`

Key scripts:
- `trace-nlink-path.py` - Trace individual paths
- `map-basin-from-cycle.py` - Map complete basin from cycle
- `tunneling/run-tunneling-pipeline.py` - Complete tunneling analysis

### Dependencies

```
python >= 3.10
pandas >= 2.0
pyarrow >= 14.0
duckdb >= 0.9
plotly >= 5.0 (for visualization)
dash >= 2.0 (for interactive tools)
```

---

## File Sizes Summary

| Category | Size | Files |
|----------|------|-------|
| Source data | 1.6 GB | 2 |
| Per-N analysis | 50 MB | ~50 |
| Multiplex analysis | 110 MB | 20 |
| **Total (minimal)** | **120 MB** | **5 core files** |
| **Total (complete)** | **1.8 GB** | **~75 files** |

### Minimal Dataset (Recommended for HF)

For most use cases, only the multiplex directory is needed:
- `multiplex_basin_assignments.parquet` (12 MB)
- `tunnel_nodes.parquet` (10 MB)
- `multiplex_edges.parquet` (87 MB)
- TSV summaries (~5 MB)

**Total: ~115 MB**

### Full Dataset

Include `nlink_sequences.parquet` (687 MB) for complete reproducibility.

---

## Citation

If you use this dataset, please cite:

```bibtex
@dataset{wikipedia_nlink_basins_2026,
  title={Wikipedia N-Link Basin Analysis Dataset},
  author={[Your Name]},
  year={2026},
  publisher={Hugging Face},
  url={https://huggingface.co/datasets/[your-username]/wikipedia-nlink-basins}
}
```

---

## Related Work

- **N-Link Rule Theory**: Formal proofs in `theories-proofs-conjectures/n-link-rule-theory.md`
- **Database Inference Graph Theory**: Extension to typed graphs in `database-inference-graph-theory.md`
- **Tunneling Analysis Report**: Detailed findings in `n-link-analysis/report/TUNNELING-FINDINGS.md`

---

## Contact

[Your contact information]

---

**Last Updated**: 2026-01-01
