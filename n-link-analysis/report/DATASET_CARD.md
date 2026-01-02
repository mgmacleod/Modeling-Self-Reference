---
license: cc-by-sa-4.0
task_categories:
  - graph-ml
  - feature-extraction
language:
  - en
tags:
  - wikipedia
  - graph-theory
  - network-analysis
  - basins-of-attraction
  - phase-transition
  - knowledge-graph
size_categories:
  - 10M<n<100M
---

# Wikipedia N-Link Basins

A novel graph-theoretic analysis of Wikipedia's internal link structure, revealing deterministic "basins of attraction" under N-link traversal rules.

## Dataset Description

This dataset demonstrates that Wikipedia's 17.9 million pages partition into coherent regions when following a simple rule: from any page, always follow the Nth link. Every page eventually reaches a cycle, and pages sharing the same terminal cycle form a **basin of attraction**.

### Key Discovery: Phase Transition at N=5

At N=5, Wikipedia's link graph exhibits a dramatic phase transition where basin sizes peak, then collapse by 10-1000× at higher N values.

## Dataset Structure

### Configurations

#### `default` (Recommended, 1.8 GB)
Full reproducibility package - everything needed to regenerate all reports, figures, and visualizations.

#### `multiplex` (125 MB)
Cross-N analysis results only. Sufficient for exploring findings.

#### `source` (1.6 GB)
Raw link sequences for computing any N value from scratch.

#### `analysis` (44 MB)
Per-N basin assignments and 3D geometry data for visualizations.

### Data Files

| Split | File | Rows | Description |
|-------|------|------|-------------|
| source | `nlink_sequences.parquet` | 18.0M | Link sequences per page (up to 3873 links) |
| source | `pages.parquet` | 64.7M | Page ID to title mapping |
| multiplex | `multiplex_basin_assignments.parquet` | 2.1M | Basin membership per page per N |
| multiplex | `tunnel_nodes.parquet` | 2.1M | Pages that switch basins across N |
| multiplex | `multiplex_edges.parquet` | 9.7M | Multiplex graph edges |
| analysis | `branches_n={3-10}_*_assignments.parquet` | varies | Per-N basin assignments |
| analysis | `basin_pointcloud_*.parquet` | varies | 3D geometry for visualizations |

### Data Fields

#### `multiplex_basin_assignments`
- `page_id` (int64): Wikipedia page identifier
- `N` (int8): N-link rule value (3-10)
- `cycle_key` (string): Raw cycle identifier for this N
- `canonical_cycle_id` (string): Normalized basin identifier (stable across N)
- `entry_id` (int64): Page ID of entry point into terminal cycle
- `depth` (int32): Distance from terminal cycle

#### `tunnel_nodes`
- `page_id` (int64): Wikipedia page identifier
- `basin_at_N3` through `basin_at_N10` (string): Basin assignment at each N value (null if page not in any basin at that N)
- `n_distinct_basins` (int8): Number of unique basins this page belongs to across N values
- `is_tunnel_node` (bool): True if page switches basins across N values

## Dataset Statistics

| Metric | Value |
|--------|-------|
| Total Wikipedia pages | 17,972,018 |
| Pages in analysis | 2,079,289 |
| Basins tracked | 9 major cycles |
| Tunnel nodes | 9,018 (0.45%) |
| N range | 3-10 |

### Basin Sizes at N=5 (Phase Transition Peak)

| Basin | Pages |
|-------|-------|
| Massachusetts ↔ Gulf_of_Maine | 1,009,471 |
| Sea_salt ↔ Seawater | 265,896 |
| Mountain ↔ Hill | 188,968 |
| Autumn ↔ Summer | 162,689 |
| Kingdom_(biology) ↔ Animal | 112,805 |

## Usage

```python
from datasets import load_dataset

# Load multiplex configuration
ds = load_dataset("your-username/wikipedia-nlink-basins", "multiplex")

# Access basin assignments
basins = ds['train'].to_pandas()
n5_basins = basins[basins.N == 5]

# Find tunnel nodes
tunnels = ds['tunnel_nodes'].to_pandas()
tunnel_pages = tunnels[tunnels.is_tunnel_node]
print(f"Pages that switch basins: {len(tunnel_pages):,}")
```

## Curation Rationale

This dataset was created to:
1. **Validate N-Link Rule Theory** - Prove that finite graphs partition into disjoint basins under deterministic rules
2. **Discover phase transitions** - Identify critical N values where structure changes dramatically
3. **Enable graph ML research** - Provide labeled basin memberships for GNN experiments
4. **Support knowledge graph analysis** - Study Wikipedia's semantic structure through graph dynamics

## Source Data

**Wikipedia Dump**: enwiki-20251220 (English Wikipedia, December 2025)

**Processing Pipeline**:
1. Extract internal links from article prose (excluding navigation, infoboxes)
2. Resolve redirects to canonical page IDs
3. Store ordered link sequences per page
4. Trace N-link paths to terminal cycles
5. Assign basin membership

## Considerations for Using the Data

### Social Impact
This dataset reveals structural properties of Wikipedia's knowledge organization. Findings could inform:
- Information navigation and search
- Knowledge graph construction
- Understanding editorial link patterns

### Limitations
- English Wikipedia only (cross-language validation pending)
- Link structure reflects December 2025 snapshot
- Basin analysis covers 9 major cycles (not exhaustive)

### Bias
Wikipedia's link structure reflects editorial decisions and systemic biases present in the encyclopedia.

## Additional Information

### Licensing
CC BY-SA 4.0 (same as Wikipedia source)

### Citation

```bibtex
@dataset{wikipedia_nlink_basins_2026,
  title={Wikipedia N-Link Basins: Phase Transitions in Knowledge Graph Structure},
  year={2026},
  publisher={Hugging Face Datasets},
  howpublished={\url{https://huggingface.co/datasets/wikipedia-nlink-basins}}
}
```

### Contact
[Your contact information]

### Dataset Card Authors
[Your name]
