# Hyperstructure Analysis: Massachusetts Basin Across N=3-10

**Document Type**: Empirical Investigation Results
**Target Audience**: LLMs + Researchers
**Status**: Complete
**Created**: 2026-01-02
**Context**: Follow-up to WH's speculation in `wh-mm_on-pr.md`

---

## Executive Summary

The **Massachusetts hyperstructure** — the union of all pages that reach the Massachusetts↔Gulf_of_Maine cycle at ANY N value (3-10) — contains **1,062,344 pages**.

This represents:
- **5.91%** of full Wikipedia (17.97M pages)
- **14.96%** of WH's "canonical 7.1M" articles

**WH's guess of "2/3 of Wikipedia" was optimistic by ~50 percentage points.** The actual hyperstructure is much smaller, but still substantial — over 1 million pages funnel to Massachusetts across all N values.

---

## Key Findings

### 1. Hyperstructure Size

| Metric | Value |
|--------|-------|
| Hyperstructure size | 1,062,344 pages |
| % of Wikipedia (17.97M) | 5.91% |
| % of canonical (7.1M) | 14.96% |
| WH's guess | 66.7% (~4.73M) |
| Actual vs guess | 4.5× smaller |

### 2. N=5 Dominates

N=5 alone accounts for **94.7%** of the hyperstructure:

| N | Pages in Basin | Cumulative Hyperstructure | New Pages Added |
|---|----------------|--------------------------|-----------------|
| 3 | 20,031 | 20,031 | 20,031 |
| 4 | 6,739 | 26,546 | 6,515 |
| **5** | **1,006,218** | **1,027,225** | **1,000,679** |
| 6 | 26,882 | 1,048,435 | 21,210 |
| 7 | 6,260 | 1,053,249 | 4,814 |
| 8 | 5,423 | 1,057,124 | 3,875 |
| 9 | 2,379 | 1,058,817 | 1,693 |
| 10 | 4,549 | 1,062,344 | 3,527 |

**Only 56,126 pages (5.3%)** are reachable via non-N=5 paths alone.

### 3. Why WH's Guess Was Optimistic

WH's hypothesis that "2/3 of canonical pages" are in the Massachusetts hyperstructure was based on intuition about how traversal rules might connect most of Wikipedia. However:

1. **N=5 is the peak, not a representative sample**
   - At N=5, the Massachusetts basin captures 1M pages (25% of Wikipedia's 17.9M)
   - But other N values contribute very little new coverage
   - The union across N doesn't multiply coverage — it barely adds 5%

2. **Basin coverage is sparse outside the peak**
   - At N=3-4, N=6-10: basins are ~10-100× smaller than N=5
   - These pages mostly OVERLAP with N=5, not extend beyond it

3. **Self-referential structure is more constrained than expected**
   - Not every path reaches Massachusetts
   - Other cycles (Sea_salt, Hill, Autumn, etc.) capture disjoint regions
   - The "funneling" effect is real but localized

---

## Hyperstructure Overlap Analysis

The top 6 hyperstructures overlap significantly:

| Pair | Overlap |
|------|---------|
| Massachusetts ∩ Animal/Kingdom | 8,646 |
| Massachusetts ∩ Sea_salt/Seawater | 5,670 |
| Massachusetts ∩ Autumn/Summer | 3,829 |
| Massachusetts ∩ Hill/Mountain | 3,288 |

These overlaps represent **tunnel nodes** — pages that switch between basins as N changes.

---

## Implications

### For WH's Hyperstructure Speculation

The "hyperstructure touch themselves" insight remains valid, but:
- The Massachusetts hyperstructure covers ~6% of Wikipedia, not 66%
- The N=5 peak IS the hyperstructure (94.7% contribution)
- Multi-N traversal adds marginal coverage beyond the single optimal N

### For Semantic Analysis

The 56,126 pages reachable ONLY via non-N=5 paths are especially interesting:
- These pages are semantically connected to Massachusetts but via longer paths
- They represent the "extended basin" that only appears at suboptimal N values
- Candidates for deeper semantic tunneling analysis

### For Hyperstructure Theory

A hyperstructure's size is dominated by its **peak N**:
- Union across N ≈ 1.05× peak N size
- Multi-N coverage adds ~5% marginal pages
- This suggests hyperstructures are "mostly flat" in the N dimension

---

## Data Sources

- `branches_n={3-10}_cycle=Massachusetts__Gulf_of_Maine_*_assignments.parquet`
- Tags: `reproduction_2025-12-31`, `tunneling_n{8,9,10}_2026-01-01`
- Script: `n-link-analysis/scripts/compute-hyperstructure-size.py`

---

## Related Documents

- [wh-mm_on-pr.md](../../human-facing-documentation/human-collaboration/wh-mm_on-pr.md) — WH's original speculation
- [MULTI-N-PHASE-MAP.md](MULTI-N-PHASE-MAP.md) — N=3-10 phase transition
- [TUNNELING-FINDINGS.md](../report/TUNNELING-FINDINGS.md) — Tunnel node analysis

---

**END OF DOCUMENT**
