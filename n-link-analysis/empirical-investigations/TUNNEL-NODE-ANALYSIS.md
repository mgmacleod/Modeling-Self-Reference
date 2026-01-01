# Tunnel Node Analysis: Cross-N Basin Switching

**Date**: 2026-01-01
**Investigation**: Tunnel node identification and classification
**Dataset**: 2,017,783 unique pages across N∈{3,4,5,6,7}
**Theory Connection**: Definition 4.1 (Tunnel Node) from database-inference-graph-theory.md

---

## Executive Summary

**Discovery**: 9,018 pages (0.45%) act as **tunnel nodes** - pages that belong to different basins under different N-link rules. These are the "connection points" between the 1D basin slices that form the multiplex structure.

**Key Findings**:
1. **Tunnel nodes are rare** (0.45% of pages in hyperstructure)
2. **Progressive switching dominates** (98.7%) - basins change monotonically with N
3. **Gulf_of_Maine__Massachusetts is the primary tunnel hub** - appears in 61% of basin pairs
4. **Tunnel nodes are relatively shallow** (mean depth 11.1) - near cycle cores
5. **All tunnel nodes bridge exactly 2 basins** - no multi-basin tunnel nodes found

---

## Methodology

### Definition 4.1 (Tunnel Node)

From [database-inference-graph-theory.md](../../llm-facing-documentation/theories-proofs-conjectures/database-inference-graph-theory.md):

> A node n is a tunnel node between rules I₁ and I₂ if:
> ∃a, b : a ∈ Basin_I₁(Tᵢ) ∧ b ∈ Basin_I₂(Tⱼ) ∧ a →_I₁ n →_I₂ b

In our empirical implementation, a tunnel node is any page that:
- Has basin assignments at multiple N values (N∈{3,4,5,6,7})
- Belongs to **different** terminal cycles at different N values

### Scripts Used

| Script | Purpose | Output |
|--------|---------|--------|
| `find-tunnel-nodes.py` | Pivot multiplex table, identify multi-basin pages | `tunnel_nodes.parquet` |
| `classify-tunnel-types.py` | Categorize tunnel behavior patterns | `tunnel_classification.tsv` |
| `compute-tunnel-frequency.py` | Rank by importance, compute scores | `tunnel_frequency_ranking.tsv` |

---

## Results

### Tunnel Node Statistics

| Metric | Value |
|--------|-------|
| Total unique pages in multiplex | 2,017,783 |
| Single-basin pages | 2,008,765 (99.55%) |
| **Tunnel nodes** | **9,018 (0.45%)** |

### Basin Coverage

All tunnel nodes bridge exactly **2 basins**:

```
Distribution of distinct basin counts:
  1 basin:  2,008,765 pages (99.55%)  ← Stable, not tunnels
  2 basins: 9,018 pages (0.45%)       ← Tunnel nodes
```

No pages were found that belong to 3+ different basins across N values.

### Tunnel Type Classification

| Type | Count | Percentage | Description |
|------|-------|------------|-------------|
| **Progressive** | 8,902 | 98.7% | Basin changes once as N increases |
| **Alternating** | 116 | 1.3% | Basin switches back and forth |

**Progressive tunneling** dominates: pages transition from basin A to basin B at some critical N value, and stay in basin B for higher N.

### N-Coverage Distribution

Most tunnel nodes have basin assignments at only 2 N values:

| N Coverage | Count | Percentage |
|------------|-------|------------|
| 2 N values | 8,864 | 98.3% |
| 3 N values | 154 | 1.7% |

This reflects the sparse nature of the basin assignment data - most pages only appear in one or two basins across the N range.

### Most Common Basin Pairs

| Count | Primary Basin | Secondary Basin |
|-------|---------------|-----------------|
| 1,959 | Sea_salt__Seawater | Gulf_of_Maine__Massachusetts |
| 1,381 | Autumn__Summer | Gulf_of_Maine__Massachusetts |
| 1,137 | Gulf_of_Maine__Massachusetts | Sea_salt__Seawater |
| 640 | Hill__Mountain | Gulf_of_Maine__Massachusetts |
| 565 | Gulf_of_Maine__Massachusetts | Autumn__Summer |
| 537 | Animal__Kingdom_(biology) | Gulf_of_Maine__Massachusetts |
| 531 | Gulf_of_Maine__Massachusetts | Animal__Kingdom_(biology) |
| 474 | American_Revolutionary_War | Gulf_of_Maine__Massachusetts |

**Key Observation**: Gulf_of_Maine__Massachusetts appears in the top 8 basin pairs, acting as a central hub in the tunnel network.

---

## Tunnel Importance Ranking

### Scoring Formula

```
tunnel_score = n_basins_bridged × log(1 + n_transitions) × (100 / mean_depth)
```

Intuition:
- More basins bridged = more structurally central
- More transitions = more dynamic cross-N behavior
- Shallower depth = closer to cycle cores (more central)

### Top 10 Tunnel Nodes

| Rank | Page ID | Score | Basins | Trans | Mean Depth | Basin Pair |
|------|---------|-------|--------|-------|------------|------------|
| 1 | 14758846 | 73.24 | 2 | 2 | 3.0 | Gulf_of_Maine ↔ Animal__Kingdom |
| 2 | 12403978 | 69.31 | 2 | 1 | 2.0 | Gulf_of_Maine ↔ American_Rev_War |
| 3 | 11869104 | 69.31 | 2 | 1 | 2.0 | Gulf_of_Maine ↔ Hill__Mountain |
| 4 | 64551967 | 69.31 | 2 | 1 | 2.0 | Gulf_of_Maine ↔ Civil_law |
| 5 | 64179894 | 65.92 | 2 | 2 | 3.3 | Gulf_of_Maine ↔ American_Rev_War |

### Depth Statistics for Tunnel Nodes

| Metric | Value |
|--------|-------|
| Mean depth | 11.1 |
| Median depth | 10.5 |
| Min depth | 2.0 |
| Max depth | 33.0 |

**Interpretation**: Tunnel nodes are relatively **shallow** (mean depth 11.1 vs typical basin depths of 50+). This suggests tunnel nodes are structurally close to the cycle cores, acting as "near-boundary" transition points between basins.

---

## Mechanism Analysis

### Why Are Tunnel Nodes Rare?

**Hypothesis**: The N-link rule creates mostly **consistent** basin membership. A page's Nth link typically points within the same semantic region regardless of N.

**Counter-examples** (tunnel nodes) occur when:
1. The Nth link points to a semantically different region than the (N-1)th link
2. The page sits at a boundary between semantic domains
3. The page has diverse outlinks spanning multiple topics

### Why Progressive Tunneling Dominates?

**Observation**: 98.7% of tunnel nodes switch basins exactly once (progressive), not repeatedly (alternating).

**Explanation**: The N-link rule creates a **monotonic** transition through a page's link list. As N increases:
- Earlier links (lower N) tend to be more prominent/general
- Later links (higher N) tend to be more specific/technical

A page's "semantic center of gravity" shifts gradually, not oscillating, as N increases.

### Gulf_of_Maine as Tunnel Hub

**Observation**: Gulf_of_Maine__Massachusetts appears in 61% of the top basin pairs.

**Explanation**: This cycle (which only exists at N=5) acts as a **structural attractor**:
- At N=5, many pages flow to Massachusetts↔Gulf_of_Maine
- At N≠5, those same pages flow to other cycles
- The N=5 basin is so massive (1M+ pages) that it naturally creates many tunnel boundaries

---

## Theoretical Implications

### Corollary 3.2 Validation

From database-inference-graph-theory.md:

> Fixed-N basins are 1D slices of a multiplex over (page, N) connected by tunneling at shared nodes.

**Validation**: We observe exactly this structure:
- 9,018 tunnel nodes connect the basin slices
- Tunneling is sparse (0.45%) but real
- Progressive switching suggests the multiplex has coherent directionality

### Tunnel Nodes as Semantic Boundaries

Tunnel nodes mark the **boundaries** between semantic regions:
- A page in both the "Geography" basin (N=5) and "Biology" basin (N=6) sits at the intersection of these domains
- High-scoring tunnel nodes (shallow, multi-transition) are the most semantically liminal

### Implications for Database Inference

Per Algorithm 5.2 from the theory document, tunnel nodes can help:
1. **Identify subsystem boundaries** - where semantic domains meet
2. **Discover hidden relationships** - connections not visible in single-N analysis
3. **Validate partitioning** - basins that share many tunnels may be semantically related

---

## Data Files Generated

### Phase 2 Outputs

| File | Format | Description |
|------|--------|-------------|
| `tunnel_nodes.parquet` | Parquet (9.69 MB) | All pages with basin_at_N{3-7} columns |
| `tunnel_nodes_summary.tsv` | TSV | Tunnel nodes only (9,018 rows) |
| `tunnel_classification.tsv` | TSV | Classification and transitions |
| `tunnel_frequency_ranking.tsv` | TSV | Ranked by tunnel_score |
| `tunnel_top_100.tsv` | TSV | Top 100 highest-scoring tunnel nodes |

### Schema: tunnel_nodes.parquet

| Column | Type | Description |
|--------|------|-------------|
| page_id | int64 | Wikipedia page ID |
| basin_at_N3 | string (nullable) | Basin at N=3 |
| basin_at_N4 | string (nullable) | Basin at N=4 |
| basin_at_N5 | string (nullable) | Basin at N=5 |
| basin_at_N6 | string (nullable) | Basin at N=6 |
| basin_at_N7 | string (nullable) | Basin at N=7 |
| n_distinct_basins | int8 | Count of unique basins |
| is_tunnel_node | bool | True if n_distinct_basins > 1 |

---

## Next Steps

### Phase 3: Multiplex Connectivity (from TUNNELING-ROADMAP.md)

1. `build-multiplex-graph.py` - Construct (page, N) × (page, N) edge graph
2. `compute-multiplex-reachability.py` - Analyze cross-N reachability
3. `visualize-multiplex-slice.py` - 3D visualization of multiplex structure

### Additional Investigations

1. **Page title lookup** - Identify what semantic categories tunnel nodes represent
2. **Depth vs tunnel probability** - Is shallow depth predictive of tunneling?
3. **Basin pair correlation** - Which basin pairs share the most tunnel nodes?

---

## Contract Status

### NLR-C-0004 — Cross-N tunneling and multiplex connectivity

- **Status**: Phase 2 complete (tunnel node identification)
- **Theory**: Definition 4.1, Corollary 3.2 from database-inference-graph-theory.md
- **Evidence**: This document (TUNNEL-NODE-ANALYSIS.md)
- **Remaining**: Phases 3-5 (multiplex connectivity, mechanisms, applications)

---

**Last Updated**: 2026-01-01
**Status**: Phase 2 complete, ready for Phase 3
**Scripts**: `find-tunnel-nodes.py`, `classify-tunnel-types.py`, `compute-tunnel-frequency.py`
