# N-Link Basin Analysis: Multi-N Summary Report

**Generated**: 2026-01-01
**Source**: Wikipedia English (enwiki-20251220)
**N Range**: 3-10
**Theory**: N-Link Rule Theory + Database Inference Graph Theory

---

## Executive Summary

This report presents a comprehensive analysis of Wikipedia's link structure under the **N-Link Rule** across N=3 to N=10. The N-Link Rule states that from any Wikipedia page, we deterministically follow the Nth link to form a directed functional graph. Different values of N reveal different structural properties of the knowledge graph.

### Key Findings

| Metric | Value |
|--------|-------|
| Pages in hyperstructure | 2,017,783 |
| Basin assignments (N=3-10) | 2,134,621 |
| Tunnel nodes identified | 41,732 (0.45%) |
| Basins analyzed | 15 |
| Cross-basin flows | 58 |
| N values with phase transition | N=5 (peak), N=6 (collapse) |

### Critical Discovery: N=5 Phase Transition

The N=5 rule exhibits unique structural properties:
- **Maximum basin coverage**: 1.9M+ pages in tracked basins
- **Giant basin emergence**: Massachusetts↔Gulf_of_Maine captures 1M+ pages
- **Phase transition**: Basins collapse by 10-1000× beyond N=5

---

## 1. Phase Transition Analysis

### Basin Size Across N Values

![Phase Transition Chart](assets/phase_transition_n3_n10.png)

The chart above shows basin size (log scale) as a function of N. Key observations:

| N Value | Behavior | Interpretation |
|---------|----------|----------------|
| N=3-4 | Small basins | Insufficient depth for convergence |
| N=5 | **Maximum** | Optimal balance of depth and link diversity |
| N=6-7 | Sharp decline | Transition zone |
| N=8-10 | Minimal | Deep links are often similar, reducing diversity |

### Basin Collapse: N=5 vs N=10

![Basin Collapse Chart](assets/basin_collapse_n5_vs_n10.png)

| Cycle | N=5 Size | N=10 Size | Collapse Factor |
|-------|----------|-----------|-----------------|
| Autumn↔Summer | 162,624 | 141 | **1,153×** |
| Massachusetts↔Gulf_of_Maine | 1,006,218 | 4,549 | 221× |
| Sea_salt↔Seawater | 265,896 | 4,389 | 61× |
| Mountain↔Hill | 188,968 | 765 | 247× |
| Kingdom_(biology)↔Animal | 112,805 | 7,823 | 14× |
| Latvia↔Lithuania | 81,656 | 1,970 | 41× |

**Interpretation**: The extreme collapse (up to 1,000×) confirms that N=5 represents a unique structural peak. Beyond N=5, the graph becomes increasingly deterministic—deep links converge to similar destinations.

---

## 2. Tunneling Analysis

### What is Tunneling?

A page "tunnels" when it belongs to different basins under different N values. Tunneling reveals semantic flexibility—pages that connect multiple knowledge domains.

### Tunnel Node Statistics

| Metric | N=3-7 | N=3-10 | Change |
|--------|-------|--------|--------|
| Total tunnel nodes | 9,018 | 41,732 | **+363%** |
| 2-basin tunnels | 8,909 | 41,372 | +364% |
| 3-basin tunnels | 108 | 359 | +232% |
| Cross-basin flows | 16 | 58 | +263% |

![Tunnel Node Distribution](assets/tunnel_node_distribution.png)

### Tunneling Mechanism

| Mechanism | Frequency | Description |
|-----------|-----------|-------------|
| degree_shift | 99.3% | Different Nth link leads to different basin |
| path_divergence | 0.7% | Same first hop but paths diverge downstream |

### Key Transition Points

| Transition | Tunnel Events | Share |
|------------|---------------|-------|
| N5→N6 | 4,845 | 53.0% |
| N3→N5 | 2,545 | 27.9% |
| N5→N7 | 891 | 9.8% |
| N4→N5 | 853 | 9.3% |

**100% of tunnel transitions involve N=5**, confirming its role as the critical phase transition point.

---

## 3. Depth Distribution

![Depth Distribution by N](assets/depth_distribution_by_n.png)

### Depth Statistics by N

| N | Mean Depth | Median Depth | Max Depth | Basin Coverage |
|---|------------|--------------|-----------|----------------|
| 3 | 3.2 | 3 | 18 | 20,031 |
| 4 | 5.1 | 4 | 28 | 6,739 |
| 5 | 12.8 | 9 | 156 | 1,978,510 |
| 6 | 7.4 | 6 | 52 | 26,882 |
| 7 | 4.9 | 4 | 31 | 6,260 |
| 8-10 | 2-4 | 2-3 | 15-20 | 3,000-24,000 |

**Key insight**: N=5 has the deepest basins (mean depth 12.8, max 156), indicating rich hierarchical structure.

---

## 4. Basin Stability

### Stability Classification

| Stability | Count | Description |
|-----------|-------|-------------|
| Stable | 0 | Identical membership across all N |
| Moderate | 14 | Core persists, edges fluctuate |
| Fragile | 1 | Significant membership changes |

The **Gulf_of_Maine↔Massachusetts** basin is uniquely fragile—it acts as a "sink" at N=6, absorbing pages from multiple other basins.

### Cross-Basin Flow Pattern

At the N=5→N=6 transition, pages flow unidirectionally:

```
Sea_salt        ──┐
Autumn          ──┤
Mountain        ──┼──▶ Gulf_of_Maine (sink)
Kingdom_(bio)   ──┤
Latvia          ──┤
Am_Rev_War      ──┘
```

This explains why Gulf_of_Maine becomes the dominant basin at N=6.

---

## 5. Theory Validation

### Validated Predictions

| Claim | Hypothesis | Result | Evidence |
|-------|------------|--------|----------|
| depth_tunnel_correlation | Shallow nodes tunnel more | **VALIDATED** | r = -0.83 |
| transition_concentration | Transitions at N=5 | **VALIDATED** | 100% involve N=5 |
| mechanism_distribution | degree_shift dominates | **VALIDATED** | 99.3% |

### Refuted Predictions

| Claim | Hypothesis | Result | Evidence |
|-------|------------|--------|----------|
| hub_tunnel_correlation | High-degree hubs tunnel more | **REFUTED** | Tunnel nodes have LOWER degree (31.8 vs 34.0, p=0.04) |

**Key theoretical insight**: Tunneling is about position (depth), not options (degree). Being close to the cycle core makes a page more likely to tunnel.

---

## 6. Semantic Structure

### Central Tunnel Nodes (Top 15)

| Rank | Page | Score | Basins | Depth |
|------|------|-------|--------|-------|
| 1 | Kidder_family | 73.2 | 2 | 3.0 |
| 2 | Donald_B._Cole | 69.3 | 2 | 2.0 |
| 3 | Lincoln_Gap_(Vermont) | 69.3 | 2 | 2.0 |
| 4 | Murder_in_New_Hampshire_law | 69.3 | 2 | 2.0 |
| 5 | 1885_Massachusetts_legislature | 65.9 | 2 | 3.3 |
| 6-10 | *(Massachusetts-related)* | 55-66 | 2 | 2-4 |
| 11-15 | *(Mixed regional/topical)* | 55-60 | 2 | 2-3 |

**Pattern**: Central tunnel nodes are predominantly Massachusetts-related, reflecting the geographic clustering of the giant N=5 basin.

### Knowledge Domain Boundaries

The 15 stable basins represent coherent semantic regions:

| Domain | Representative Basins |
|--------|----------------------|
| Geography/Politics | Massachusetts, Latvia, American_Revolutionary_War |
| Natural Science | Kingdom_(biology), Sea_salt, Mountain |
| Temporal | Autumn↔Summer |
| Industrial | Thermosetting_polymer |
| Legal | Precedent↔Civil_law |

---

## 7. Figures and Visualizations

### Static Figures (report/assets/)

| Figure | Description |
|--------|-------------|
| [phase_transition_n3_n10.png](assets/phase_transition_n3_n10.png) | Basin size vs N (log scale) |
| [basin_collapse_n5_vs_n10.png](assets/basin_collapse_n5_vs_n10.png) | Collapse factor comparison |
| [tunnel_node_distribution.png](assets/tunnel_node_distribution.png) | Tunnel nodes by basin count |
| [depth_distribution_by_n.png](assets/depth_distribution_by_n.png) | Depth statistics across N |
| [tunneling_sankey.html](assets/tunneling_sankey.html) | Interactive flow diagram |

### Interactive Dashboards

| Tool | Port | Description |
|------|------|-------------|
| Tunneling Dashboard | 8060 | 5-tab exploration of tunneling results |
| Path Tracer | 8061 | Per-page basin membership timeline |
| Multiplex Explorer | 8056 | Cross-N connectivity analysis |
| Basin Geometry Viewer | 8055 | 3D point cloud visualization |

### Summary Table

[View interactive summary table](assets/multi_n_summary_table.html)

---

## 8. Data Files

### Primary Data (data/wikipedia/processed/multiplex/)

| File | Size | Description |
|------|------|-------------|
| multiplex_basin_assignments.parquet | 11.8 MB | Page-basin assignments N=3-10 |
| tunnel_nodes.parquet | 10.8 MB | Basin membership per page |
| tunnel_classification.tsv | 7.9 MB | 41,732 tunnel node classifications |
| tunnel_frequency_ranking.tsv | 4.9 MB | Ranked by importance score |
| basin_flows.tsv | 3.9 KB | 58 cross-basin flows |
| basin_stability_scores.tsv | 1.4 KB | 15 basin stability metrics |
| semantic_model_wikipedia.json | 44 KB | Extracted semantic structure |

### Analysis Artifacts (data/wikipedia/processed/analysis/)

- Branch assignment parquets for N=3-10
- Basin pointclouds for N=5 (9 cycles)
- Dominance chase TSVs
- Trunkiness dashboards

---

## 9. Methodology

### Pipeline Overview

1. **Data Extraction**: Parse Wikipedia XML dump, extract Nth links
2. **Cycle Detection**: Find terminal 2-cycles under each N
3. **Basin Mapping**: Reverse BFS from cycles to map full basins
4. **Tunneling Analysis**: Compare basin membership across N values
5. **Validation**: Test theory predictions against empirical data

### Reproducibility

```bash
# Regenerate all figures
python n-link-analysis/viz/generate-multi-n-figures.py --all

# Run full tunneling pipeline
python n-link-analysis/scripts/tunneling/run-tunneling-pipeline.py

# Start visualization servers
python n-link-analysis/viz/tunneling/launch-tunneling-viz.py --all
```

---

## 10. References

- **N-Link Rule Theory**: [n-link-rule-theory.md](../../llm-facing-documentation/theories-proofs-conjectures/n-link-rule-theory.md)
- **Database Inference Graph Theory**: [database-inference-graph-theory.md](../../llm-facing-documentation/theories-proofs-conjectures/database-inference-graph-theory.md)
- **Tunneling Implementation**: [TUNNELING-ROADMAP.md](../TUNNELING-ROADMAP.md)
- **Contract**: NLR-C-0004 (Cross-N tunneling and multiplex connectivity)

---

**Report generated by**: `generate-multi-n-figures.py` + manual consolidation
**Last Updated**: 2026-01-01
