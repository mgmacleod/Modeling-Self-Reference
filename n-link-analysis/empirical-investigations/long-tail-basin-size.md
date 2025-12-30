# Empirical Investigation: Long-Tail Basin Size (N=5)

**Document Type**: Empirical Investigation (question-scoped)  
**Target Audience**: LLMs + Developers  
**Purpose**: Reproducible evidence linked to specific conjectures/theory claims  
**Last Updated**: 2025-12-30  
**Status**: Active

---

## 1. Question

Under the fixed-$N$ rule $f_N$, do basin sizes exhibit a heavy-tail distribution with a small number of extremely large attractor basins?

Operationally (for fixed $N$):
- pick terminal cycles $C$,
- compute basin size $|\mathcal{B}(C)|$ (reverse-reachable set into $C$),
- compare sizes across multiple observed cycles.

---

## 2. Theory Linkage

Primary theory reference:
- [N-Link Rule Theory](../../llm-facing-documentation/theories-proofs-conjectures/n-link-rule-theory.md)

This investigation targets the “basin size distribution / long-tail” conjecture family (informal in the theory docs; to be formalized there as needed).

---

## 3. Dataset + Semantics

Inputs (pipeline output):
- `data/wikipedia/processed/nlink_sequences.parquet`
  - schema: `(page_id: int64, link_sequence: list<int64>)`
  - `out_degree := list_count(link_sequence)`
- `data/wikipedia/processed/pages.parquet` (labeling and title→page_id resolution)

Important semantic note:
- `link_sequence` is the pipeline’s extracted *ordered prose links* (not “all wikilinks”).
- Redirect pages typically have no prose body; they therefore tend to have very small extracted `out_degree`.

---

## 4. Reproducibility Trace

### 4.1 Scripts Used

- `n-link-analysis/scripts/sample-nlink-traces.py`
  - random start sampling + terminal/cycle frequency summary
- `n-link-analysis/scripts/find-nlink-preimages.py`
  - preimage counts: how many pages have their Nth link pointing to a target
- `n-link-analysis/scripts/map-basin-from-cycle.py`
  - full basin mapping (reverse BFS set expansion) from a given cycle

### 4.2 Commands Executed (Repo Root)

Sampling (N=5):
- `python n-link-analysis/scripts/sample-nlink-traces.py --n 5 --num 100 --seed0 0 --min-outdegree 50 --max-steps 5000 --top-cycles 10 --resolve-titles`

Preimage counts (Nth-link indegree under $f_5$):
- `python n-link-analysis/scripts/find-nlink-preimages.py --n 5 --target-title Gulf_of_Maine --target-title Massachusetts`

Full basin mapping (uncapped depth):
- `python n-link-analysis/scripts/map-basin-from-cycle.py --n 5 --cycle-title Massachusetts --cycle-title Gulf_of_Maine --max-depth 0 --log-every 5`

Comparative basins (examples):
- `python n-link-analysis/scripts/map-basin-from-cycle.py --n 5 --cycle-title Sea_salt --cycle-title Seawater --max-depth 0 --log-every 25 --out-prefix "basin_n=5_cycle=Sea_salt__Seawater"`
- `python n-link-analysis/scripts/map-basin-from-cycle.py --n 5 --cycle-title Mountain --cycle-title Hill --max-depth 0 --log-every 25 --out-prefix "basin_n=5_cycle=Mountain__Hill"`
- `python n-link-analysis/scripts/map-basin-from-cycle.py --n 5 --cycle-title Lithic_reduction --cycle-title Stone_tool --max-depth 0 --log-every 25 --out-prefix "basin_n=5_cycle=Lithic_reduction__Stone_tool"`

### 4.3 Output Artifacts Produced

All outputs were written under:
- `data/wikipedia/processed/analysis/`

Key artifacts:
- `sample_traces_n=5_num=100_seed0=0.tsv`
- `preimages_n=5.tsv`
- `preimages_n=5_massachusetts.tsv` (limited list with titles)
- `edges_n=5.duckdb` (materialized edge table for reverse expansions)
- `basin_from_cycle_n=5_layers.tsv` (Massachusetts/Gulf_of_Maine)
- `basin_n=5_cycle=Sea_salt__Seawater_layers.tsv`
- `basin_n=5_cycle=Mountain__Hill_layers.tsv`
- `basin_n=5_cycle=Lithic_reduction__Stone_tool_layers.tsv`

---

## 5. Findings

### 5.1 Cycle Prevalence Under N=5 Sampling

From 100 sampled starts (with `min_outdegree=50` to avoid trivial early halts):
- terminal counts: `CYCLE = 97`, `HALT = 3`
- 2-cycles were common among cycle outcomes (majority in this sample)

One notably frequent 2-cycle observed:
- `Gulf_of_Maine ↔ Massachusetts`: observed **22 / 100** sample traces terminating in this cycle.

### 5.2 Massive Basin Identified: Massachusetts ↔ Gulf_of_Maine

The cycle was confirmed by successor lookup under $f_5$:
- `Gulf_of_Maine → Massachusetts`
- `Massachusetts → Gulf_of_Maine`

Full basin computation (reverse BFS set expansion) produced:
- basin size (unique nodes): **1,009,471**
- reverse-depth to exhaustion: **168**

Interpretation:
- This is a plausible “giant basin” candidate under $f_5$.

### 5.3 Basin Size Comparison (Partial)

Other N=5 2-cycle basins computed (full, not depth-capped):
- `Sea_salt ↔ Seawater`: **265,940**
- `Mountain ↔ Hill`: **189,269**
- `Lithic_reduction ↔ Stone_tool`: **60,159**

Observation:
- Basin sizes differ by an order-of-magnitude scale in a small sample of cycles.
- The Massachusetts/Gulf_of_Maine basin is ~3.8× larger than the next tested basin.

### 5.4 Out-degree / Redirect Context (Why “<5 links” is plausible)

From `nlink_sequences.parquet`:
- total pages with at least 1 extracted link: **17,972,018**
- pages with `<5` extracted links: **12,109,171**
- pages with `>=5` extracted links: **5,862,847**

Joined with `pages.parquet` (namespace 0):
- namespace 0 redirects: **10,883,640** pages; almost all have `<5` extracted links
- namespace 0 non-redirect: **7,088,270** pages; **5,862,604** have `>=5` extracted links (~82.7%)

---

## 6. Open Questions / Next Steps

- Confirm whether Massachusetts/Gulf_of_Maine is the *largest* $f_5$ basin by evaluating basin sizes for a larger set of observed frequent cycles (e.g. top-K from sampling).
- Formalize the “heavy tail / giant component basin” conjecture in the theory docs with explicit testable statements (e.g. tail exponent fits, scaling across $N$).
- Add “article-only” denominators (namespace 0, non-redirect) when reporting basin proportions.
