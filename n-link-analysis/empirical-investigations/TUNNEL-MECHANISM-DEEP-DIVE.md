# Tunnel Mechanism Deep-Dive

**Document Type**: Empirical investigation
**Target Audience**: Researchers, LLMs
**Purpose**: Document Phase 4 findings on WHY tunneling occurs
**Created**: 2026-01-01
**Status**: Active

---

## Overview

This investigation answers the question: **Why do pages switch between basins when N changes?**

Phase 4 of the [TUNNELING-ROADMAP.md](../TUNNELING-ROADMAP.md) classifies the mechanisms causing tunnel transitions and quantifies basin stability across N values.

### Key Questions Addressed

1. What causes a page to end up in different basins under different N?
2. How stable are basins as N changes?
3. Which basins absorb pages from others as N increases?

---

## Phase 4 Scripts

| Script | Purpose | Output |
|--------|---------|--------|
| `analyze-tunnel-mechanisms.py` | Classify WHY each transition occurs | `tunnel_mechanisms.tsv` |
| `trace-tunneling-paths.py` | Trace paths through N-sequences | `tunneling_traces.tsv` |
| `quantify-basin-stability.py` | Measure basin stability metrics | `basin_stability_scores.tsv` |

---

## Mechanism Classification

### Mechanism Types

| Mechanism | Description | Frequency |
|-----------|-------------|-----------|
| **degree_shift** | The Nth link is simply different from the (N-1)th link | ~99% |
| **path_divergence** | Same immediate successor, but paths diverge downstream | ~1% |
| **halt_creation** | Page has fewer than N links, causing HALT at higher N | Rare |
| **link_not_found** | Target page doesn't exist or is a redirect loop | Rare |

### Key Finding: Degree Shift Dominates

The overwhelming majority (~99%) of tunnel transitions are caused by **degree shift**: when N increases from 5 to 6, the page follows a different link (the 6th instead of the 5th), which leads to a different basin.

This is the simplest possible mechanism: the N-link rule directly selects a different target, and that target happens to lead to a different cycle.

### Path Divergence

About 1% of transitions show **path divergence**: both N values follow the same immediate link, but the paths diverge somewhere downstream. This indicates structural properties of the graph that cause convergence to different attractors despite identical first steps.

---

## Basin Stability Analysis

### Stability Metrics

| Metric | Definition |
|--------|------------|
| **Persistence score** | Fraction of pages that remain in the same basin across ALL N values |
| **Mean Jaccard** | Average Jaccard similarity of basin membership between adjacent N values |
| **Max stable range** | Longest contiguous N range with >80% overlap |
| **Stability class** | stable (p≥0.8, j≥0.8), moderate (p≥0.5 or j≥0.5), fragile (otherwise) |

### Findings

Based on analysis of 9 canonical basins across N=3 to N=7:

| Class | Count | Percentage |
|-------|-------|------------|
| stable | 0 | 0% |
| moderate | 8 | 89% |
| fragile | 1 | 11% |

**Interpretation**: Most basins show moderate stability—they retain some pages across N but experience significant membership changes. The one fragile basin is `Gulf_of_Maine__Massachusetts`, which shows near-zero persistence (pages flow out as N changes).

### Per-Basin Stability

| Basin | Persistence | Mean Jaccard | Class |
|-------|-------------|--------------|-------|
| American_Revolutionary_War__Eastern_United_States | 1.000 | 0.500 | moderate |
| Autumn__Summer | 1.000 | 0.500 | moderate |
| Animal__Kingdom_(biology) | 1.000 | 0.500 | moderate |
| Latvia__Lithuania | 1.000 | 0.500 | moderate |
| Hill__Mountain | 1.000 | 0.500 | moderate |
| Sea_salt__Seawater | 1.000 | 0.500 | moderate |
| Civil_law__Precedent | 1.000 | 0.500 | moderate |
| Curing_(chemistry)__Thermosetting_polymer | 1.000 | 0.500 | moderate |
| Gulf_of_Maine__Massachusetts | 0.000 | 0.004 | fragile |

**Note**: High persistence (1.0) with moderate Jaccard (0.5) indicates that the core pages remain, but the basin size fluctuates significantly as N changes.

---

## Cross-Basin Flows

### Major Flow Directions (N=5 → N=6)

| From Basin | To Basin | Pages |
|------------|----------|-------|
| Sea_salt__Seawater | Gulf_of_Maine__Massachusetts | 1,659 |
| Autumn__Summer | Gulf_of_Maine__Massachusetts | 1,276 |
| Hill__Mountain | Gulf_of_Maine__Massachusetts | 571 |
| Animal__Kingdom_(biology) | Gulf_of_Maine__Massachusetts | 427 |
| American_Revolutionary_War | Gulf_of_Maine__Massachusetts | 283 |
| Latvia__Lithuania | Gulf_of_Maine__Massachusetts | 267 |

**Key Insight**: At the N=5 → N=6 transition, Gulf_of_Maine__Massachusetts acts as a **sink basin**—it absorbs pages from all other basins. This explains its fragile stability score: it has many pages at some N values but loses them at others.

### Flow Pattern

```
N=5 basins:                    N=6 basin:
  Sea_salt__Seawater ────────┐
  Autumn__Summer ────────────┤
  Hill__Mountain ────────────┼──► Gulf_of_Maine__Massachusetts
  Animal__Kingdom ───────────┤
  Latvia__Lithuania ─────────┘
```

This unidirectional flow from multiple N=5 basins to a single N=6 basin is a hallmark of the **phase transition** observed at N=5.

---

## Theoretical Interpretation

### Why Degree Shift Dominates

The N-link rule `f_N(page) = page's Nth link` deterministically selects a target. When N changes:
- The new target is typically unrelated to the old target
- Links are ordered by position in the article, which reflects editorial/stylistic choices
- The Nth link vs (N+1)th link often point to semantically different concepts

This explains why **tunneling is common but not chaotic**: the link ordering in Wikipedia articles creates structured patterns that cause pages to cluster into specific basins at each N.

### Basin Absorption at Phase Transition

The flow analysis reveals that N=5 → N=6 is a **collapse transition**:
- At N=5, pages are distributed across multiple basins
- At N=6, pages consolidate into fewer basins (primarily Gulf_of_Maine)
- This matches the phase transition observed in [MULTI-N-PHASE-MAP.md](MULTI-N-PHASE-MAP.md)

---

## Data Files

### Primary Outputs

| File | Location | Description |
|------|----------|-------------|
| `tunnel_mechanisms.tsv` | `multiplex/` | Per-transition mechanism classification |
| `tunnel_mechanism_summary.tsv` | `multiplex/` | Aggregated mechanism statistics |
| `tunneling_traces.tsv` | `multiplex/` | Example path traces through N-sequences |
| `basin_stability_scores.tsv` | `multiplex/` | Per-basin stability metrics |
| `basin_flows.tsv` | `multiplex/` | Cross-basin page flows |

### Schema: tunnel_mechanisms.tsv

| Column | Type | Description |
|--------|------|-------------|
| page_id | int64 | Wikipedia page ID |
| page_title | string | Page title |
| transition | string | e.g., "N5→N6" |
| from_basin | string | Basin at lower N |
| to_basin | string | Basin at higher N |
| mechanism | string | degree_shift, path_divergence, etc. |
| nth_link_at_low_n | string | Target of Nth link at lower N |
| nth_link_at_high_n | string | Target of Nth link at higher N |
| out_degree | int | Number of outgoing links |
| explanation | string | Human-readable description |

### Schema: basin_stability_scores.tsv

| Column | Type | Description |
|--------|------|-------------|
| canonical_cycle_id | string | Basin identifier |
| n_values_present | int | N values where basin exists |
| total_pages | int | Total unique pages |
| persistence_score | float | Fraction stable across all N |
| max_stable_range | int | Longest stable N range |
| mean_jaccard | float | Mean adjacent Jaccard |
| stability_class | string | stable/moderate/fragile |
| pages_at_n{X} | int | Page count at each N |

---

## Contracts

This investigation provides evidence for:

- **NLR-C-0004** — Cross-N tunneling and multiplex connectivity (Phase 4)

---

## Next Steps (Phase 5)

Per [TUNNELING-ROADMAP.md](../TUNNELING-ROADMAP.md):

1. `compute-semantic-model.py` — Extract central entities and subsystem boundaries
2. `validate-tunneling-predictions.py` — Test theory claims empirically
3. `generate-tunneling-report.py` — Create publication-ready summary

---

## Related Documents

- [TUNNELING-ROADMAP.md](../TUNNELING-ROADMAP.md) — Implementation plan
- [TUNNEL-NODE-ANALYSIS.md](TUNNEL-NODE-ANALYSIS.md) — Phase 2 tunnel identification
- [MULTIPLEX-CONNECTIVITY.md](MULTIPLEX-CONNECTIVITY.md) — Phase 3 graph analysis
- [database-inference-graph-theory.md](../../llm-facing-documentation/theories-proofs-conjectures/database-inference-graph-theory.md) — Theoretical foundation

---

**Last Updated**: 2026-01-01
**Status**: Active
