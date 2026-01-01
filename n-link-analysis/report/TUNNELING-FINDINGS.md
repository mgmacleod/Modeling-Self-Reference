# Tunneling Analysis Findings

**Generated**: 2026-01-01 17:30
**Source**: Wikipedia English (enwiki-20251220)
**N Range**: 3-7
**Theory**: N-Link Rule Theory + Database Inference Graph Theory

---

## Executive Summary

This report presents findings from a comprehensive analysis of **tunneling** in Wikipedia's
link graph under the N-link rule. Tunneling occurs when a page belongs to different basins
(terminal cycles) under different values of N.

### Key Findings

| Metric | Value |
|--------|-------|
| Pages in hyperstructure | 2,017,783 |
| Tunnel nodes | 9,018 (0.45%) |
| Basins analyzed | 9 |
| Cross-basin flows | 16 |

### Validated Theory Predictions

**Confirmed**:
- Shallow nodes (low depth) have higher tunnel scores
- Tunnel transitions concentrate around N=5 (phase transition)
- degree_shift (different Nth link) dominates mechanisms

**Refuted**:
- Tunnel nodes have higher out-degree than non-tunnel nodes

---

## 1. Mechanism Analysis

### What Causes Tunneling?

When a page switches between basins as N changes, what is the root cause?

| Mechanism | Count | Percentage |
|-----------|-------|------------|
| degree_shift | 9,074 | 99.3% |
| path_divergence | 60 | 0.7% |

**Interpretation**: The overwhelming dominance of `degree_shift` (>99%) confirms that
tunneling is primarily a direct consequence of the N-link rule: different N values select
different target links, which lead to different terminal cycles.

### Transition Distribution

| Transition | Count | Percentage |
|------------|-------|------------|
| N5→N6 | 4,845 | 53.0% |
| N3→N5 | 2,545 | 27.9% |
| N5→N7 | 891 | 9.8% |
| N4→N5 | 853 | 9.3% |

**Key Insight**: The N=5→N=6 transition accounts for the majority of tunneling events,
consistent with N=5 being the phase transition point where basin structure changes dramatically.

---

## 2. Basin Stability

### How Stable Are Basins Across N?

| Basin | Stability | Persistence | Jaccard | Pages |
|-------|-----------|-------------|---------|-------|
| Gulf_of_Maine__Massachusetts | fragile | 0.00 | 0.00 | 1,053,249 |
| American_Revolutionary_War__Eastern | moderate | 1.00 | 0.50 | 43,959 |
| Autumn__Summer | moderate | 1.00 | 0.50 | 162,624 |
| Animal__Kingdom_(biology) | moderate | 1.00 | 0.50 | 112,805 |
| Latvia__Lithuania | moderate | 1.00 | 0.50 | 81,656 |
| Hill__Mountain | moderate | 1.00 | 0.50 | 188,968 |
| Civil_law__Precedent | moderate | 1.00 | 0.50 | 56,295 |
| Sea_salt__Seawater | moderate | 1.00 | 0.50 | 265,896 |
| Curing_(chemistry)__Thermosetting_p | moderate | 1.00 | 0.50 | 61,349 |

**Interpretation**: Most basins show "moderate" stability - their core pages persist
across N values, but membership fluctuates significantly. Gulf_of_Maine is uniquely
"fragile" because it acts as a **sink basin** at certain N values.

### Cross-Basin Flows

| From → To | N Transition | Pages |
|-----------|--------------|-------|
| Sea_salt__Seawater → Gulf_of_Maine__Massa | N5→N6 | 1,659 |
| Autumn__Summer → Gulf_of_Maine__Massa | N5→N6 | 1,276 |
| Hill__Mountain → Gulf_of_Maine__Massa | N5→N6 | 571 |
| Animal__Kingdom_(bio → Gulf_of_Maine__Massa | N5→N6 | 427 |
| Gulf_of_Maine__Massa → Sea_salt__Seawater | N4→N5 | 346 |
| American_Revolutiona → Gulf_of_Maine__Massa | N5→N6 | 283 |
| Latvia__Lithuania → Gulf_of_Maine__Massa | N5→N6 | 267 |
| Curing_(chemistry)__ → Gulf_of_Maine__Massa | N5→N6 | 189 |

**Key Pattern**: At the N=5→N=6 transition, pages flow **unidirectionally** from
multiple basins INTO Gulf_of_Maine. This explains the phase transition behavior.

---

## 3. Central Entities

### Most Important Tunnel Nodes

Pages that bridge multiple basins are semantically central in the knowledge graph.

| Rank | Page | Tunnel Score | Basins Bridged | Depth |
|------|------|--------------|----------------|-------|
| 1 | Kidder_family | 73.2 | 2 | 3.0 |
| 2 | Donald_B._Cole | 69.3 | 2 | 2.0 |
| 3 | Lincoln_Gap_(Vermont) | 69.3 | 2 | 2.0 |
| 4 | Murder_in_New_Hampshire_law | 69.3 | 2 | 2.0 |
| 5 | 1885_Massachusetts_legislature | 65.9 | 2 | 3.3 |
| 6 | Daniel_McMaster | 65.9 | 2 | 3.3 |
| 7 | 1886_Massachusetts_legislature | 65.9 | 2 | 3.3 |
| 8 | Tallulah_Morgan | 59.9 | 2 | 3.7 |
| 9 | Plax | 55.5 | 2 | 2.5 |
| 10 | Ribes_americanum | 55.5 | 2 | 2.5 |
| 11 | WVEI-FM | 55.5 | 2 | 2.5 |
| 12 | Sherburne_Pass | 55.5 | 2 | 2.5 |
| 13 | Malachy_Salter | 55.5 | 2 | 2.5 |
| 14 | Hunkydory_Creek | 55.5 | 2 | 2.5 |
| 15 | Come_into_My_Cellar | 55.5 | 2 | 2.5 |

**Interpretation**: Central tunnel nodes tend to be:
1. **Shallow** (mean depth ~11 vs typical 50+)
2. **Geographically or topically central** (Massachusetts-related entities prominent)
3. **Bridges between knowledge domains** (connecting different subject areas)

---

## 4. Semantic Model

### Subsystem Boundaries

Stable basins represent coherent knowledge subsystems in Wikipedia.

- **American_Revolutionary_War__Eastern_United_States**: moderate (persistence=1.00, 43,959 pages)
- **Autumn__Summer**: moderate (persistence=1.00, 162,624 pages)
- **Animal__Kingdom_(biology)**: moderate (persistence=1.00, 112,805 pages)
- **Latvia__Lithuania**: moderate (persistence=1.00, 81,656 pages)
- **Hill__Mountain**: moderate (persistence=1.00, 188,968 pages)
- **Civil_law__Precedent**: moderate (persistence=1.00, 56,295 pages)
- **Sea_salt__Seawater**: moderate (persistence=1.00, 265,896 pages)
- **Curing_(chemistry)__Thermosetting_polymer**: moderate (persistence=1.00, 61,349 pages)
- **Gulf_of_Maine__Massachusetts**: fragile (persistence=0.00, 1,053,249 pages)


### Hidden Relationships

Cross-N analysis reveals connections invisible at any single N:

1. **Gulf_of_Maine as universal attractor** at N=6 (absorbs from all other basins)
2. **Geographic clustering** (Massachusetts-centric structure)
3. **Semantic domain boundaries** visible as stable basin partitions

---

## 5. Theory Validation

### Validated Claims

1. **depth_tunnel_correlation**: Shallow nodes (low depth) have higher tunnel scores
1. **transition_concentration**: Tunnel transitions concentrate around N=5 (phase transition)
1. **mechanism_distribution**: degree_shift (different Nth link) dominates mechanisms


### Refuted Claims

1. **hub_tunnel_correlation**: Tunnel nodes have higher out-degree than non-tunnel nodes
   - *Finding*: Tunnel nodes have slightly LOWER out-degree than non-tunnel nodes
   - *Implication*: Tunneling is not caused by having more link options


---

## 6. Conclusions

### Summary of Findings

1. **Tunneling is common but structured**: 0.45% of pages tunnel, concentrated at phase transition
2. **Mechanism is simple**: 99.3% of transitions are direct degree shifts (different Nth link)
3. **N=5 is critical**: 100% of tunnel transitions involve N=5
4. **Depth predicts tunneling**: Shallow nodes (near cycle cores) tunnel more (r=-0.83)
5. **Hub hypothesis refuted**: High-degree nodes do NOT tunnel more than average

### Implications for Theory

- The phase transition at N=5 is real and dominates tunneling behavior
- Basin structure is determined by local link choices, not global graph properties
- The multiplex interpretation (Corollary 3.2) is empirically validated

### Future Work

1. Extend analysis to N=8-10 for complete phase transition mapping
2. Investigate semantic content of central tunnel nodes
3. Apply tunneling analysis to other self-referential graphs (citations, code)

---

## Data Files

| File | Description |
|------|-------------|
| `multiplex_basin_assignments.parquet` | Unified page-basin assignments across N |
| `tunnel_nodes.parquet` | All pages with basin membership per N |
| `tunnel_classification.tsv` | Tunnel type classification |
| `tunnel_frequency_ranking.tsv` | Ranked tunnel nodes by importance |
| `tunnel_mechanisms.tsv` | Mechanism causing each transition |
| `basin_stability_scores.tsv` | Per-basin stability metrics |
| `basin_flows.tsv` | Cross-basin page flows |
| `semantic_model_wikipedia.json` | Extracted semantic structure |
| `tunneling_validation_metrics.tsv` | Theory validation results |

---

## References

- N-Link Rule Theory: `llm-facing-documentation/theories-proofs-conjectures/n-link-rule-theory.md`
- Database Inference Graph Theory: `llm-facing-documentation/theories-proofs-conjectures/database-inference-graph-theory.md`
- Implementation Roadmap: `n-link-analysis/TUNNELING-ROADMAP.md`

---

**Report generated by**: `generate-tunneling-report.py`
**Contract**: NLR-C-0004 (Cross-N tunneling and multiplex connectivity)
