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
- `n-link-analysis/scripts/branch-basin-analysis.py`
  - branch (depth-1 entry subtree) size distribution for a given cycle; can write membership assignments for top branches
- `n-link-analysis/scripts/chase-dominant-upstream.py`
  - iteratively follows the dominant upstream entry branch (“source of the Nile” chase)
- `n-link-analysis/scripts/compute-trunkiness-dashboard.py`
  - aggregates per-basin branch outputs into a single summary TSV (“trunkiness dashboard”)

### 4.2 Commands Executed (Repo Root)

Sampling (N=5):
- `python n-link-analysis/scripts/sample-nlink-traces.py --n 5 --num 100 --seed0 0 --min-outdegree 50 --max-steps 5000 --top-cycles 10 --resolve-titles`

Bootstrap rerun (N=5):
- `python n-link-analysis/scripts/sample-nlink-traces.py --n 5 --num 50 --seed0 0 --min-outdegree 50 --max-steps 5000 --top-cycles 10 --resolve-titles --out "data/wikipedia/processed/analysis/sample_traces_n=5_num=50_seed0=0_bootstrap_2025-12-30.tsv"`

Large sampling run (N=5, for top-cycle identification):
- `python n-link-analysis/scripts/sample-nlink-traces.py --n 5 --num 5000 --seed0 0 --min-outdegree 50 --max-steps 5000 --top-cycles 30 --resolve-titles --out "data/wikipedia/processed/analysis/sample_traces_n=5_num=5000_seed0=0_minout=50_bootstrap_2025-12-30.tsv"`

Preimage counts (Nth-link indegree under $f_5$):
- `python n-link-analysis/scripts/find-nlink-preimages.py --n 5 --target-title Gulf_of_Maine --target-title Massachusetts`

Full basin mapping (uncapped depth):
- `python n-link-analysis/scripts/map-basin-from-cycle.py --n 5 --cycle-title Massachusetts --cycle-title Gulf_of_Maine --max-depth 0 --log-every 5`

Comparative basins (examples):
- `python n-link-analysis/scripts/map-basin-from-cycle.py --n 5 --cycle-title Sea_salt --cycle-title Seawater --max-depth 0 --log-every 25 --out-prefix "basin_n=5_cycle=Sea_salt__Seawater"`
- `python n-link-analysis/scripts/map-basin-from-cycle.py --n 5 --cycle-title Mountain --cycle-title Hill --max-depth 0 --log-every 25 --out-prefix "basin_n=5_cycle=Mountain__Hill"`
- `python n-link-analysis/scripts/map-basin-from-cycle.py --n 5 --cycle-title Lithic_reduction --cycle-title Stone_tool --max-depth 0 --log-every 25 --out-prefix "basin_n=5_cycle=Lithic_reduction__Stone_tool"`

Additional top 2-cycle basins (from 5000-sample top cycles):
- `python n-link-analysis/scripts/map-basin-from-cycle.py --n 5 --cycle-title Autumn --cycle-title Summer --max-depth 0 --log-every 25 --out-prefix "basin_n=5_cycle=Autumn__Summer"`
- `python n-link-analysis/scripts/map-basin-from-cycle.py --n 5 --cycle-title "Kingdom_(biology)" --cycle-title Animal --max-depth 0 --log-every 25 --out-prefix "basin_n=5_cycle=Kingdom_(biology)__Animal"`
- `python n-link-analysis/scripts/map-basin-from-cycle.py --n 5 --cycle-title Latvia --cycle-title Lithuania --max-depth 0 --log-every 25 --out-prefix "basin_n=5_cycle=Latvia__Lithuania"`

Branch analysis (Massachusetts/Gulf_of_Maine):
- `python n-link-analysis/scripts/branch-basin-analysis.py --n 5 --cycle-title Massachusetts --cycle-title Gulf_of_Maine --max-depth 0 --log-every 25 --top-k 30 --write-membership-top-k 5 --out-prefix "branches_n=5_cycle=Massachusetts__Gulf_of_Maine"`

Branch analysis (additional frequent 2-cycles):
- `python n-link-analysis/scripts/branch-basin-analysis.py --n 5 --cycle-title Sea_salt --cycle-title Seawater --max-depth 0 --log-every 0 --top-k 30 --write-membership-top-k 0 --out-prefix "branches_n=5_cycle=Sea_salt__Seawater"`
- `python n-link-analysis/scripts/branch-basin-analysis.py --n 5 --cycle-title Mountain --cycle-title Hill --max-depth 0 --log-every 0 --top-k 30 --write-membership-top-k 0 --out-prefix "branches_n=5_cycle=Mountain__Hill"`
- `python n-link-analysis/scripts/branch-basin-analysis.py --n 5 --cycle-title Autumn --cycle-title Summer --max-depth 0 --log-every 0 --top-k 30 --write-membership-top-k 0 --out-prefix "branches_n=5_cycle=Autumn__Summer"`
- `python n-link-analysis/scripts/branch-basin-analysis.py --n 5 --cycle-title "Kingdom_(biology)" --cycle-title Animal --max-depth 0 --log-every 0 --top-k 30 --write-membership-top-k 0 --out-prefix "branches_n=5_cycle=Kingdom_(biology)__Animal"`
- `python n-link-analysis/scripts/branch-basin-analysis.py --n 5 --cycle-title Latvia --cycle-title Lithuania --max-depth 0 --log-every 0 --top-k 30 --write-membership-top-k 0 --out-prefix "branches_n=5_cycle=Latvia__Lithuania"`
- `python n-link-analysis/scripts/branch-basin-analysis.py --n 5 --cycle-title Thermosetting_polymer --cycle-title "Curing_(chemistry)" --max-depth 0 --log-every 0 --top-k 30 --write-membership-top-k 0 --out-prefix "branches_n=5_cycle=Thermosetting_polymer__Curing_(chemistry)"`
- `python n-link-analysis/scripts/branch-basin-analysis.py --n 5 --cycle-title Precedent --cycle-title Civil_law --max-depth 0 --log-every 0 --top-k 30 --write-membership-top-k 0 --out-prefix "branches_n=5_cycle=Precedent__Civil_law"`
- `python n-link-analysis/scripts/branch-basin-analysis.py --n 5 --cycle-title American_Revolutionary_War --cycle-title Eastern_United_States --max-depth 0 --log-every 0 --top-k 30 --write-membership-top-k 0 --out-prefix "branches_n=5_cycle=American_Revolutionary_War__Eastern_United_States"`

Branch “trunkiness dashboard” aggregation:
- `python n-link-analysis/scripts/compute-trunkiness-dashboard.py --tag "bootstrap_2025-12-30"`

Dominance-collapse batch run (across multiple basins):
- `python n-link-analysis/scripts/batch-chase-collapse-metrics.py --n 5 --dashboard "data/wikipedia/processed/analysis/branch_trunkiness_dashboard_n=5_bootstrap_2025-12-30.tsv" --seed-from dominant_enters_cycle_title --max-hops 50 --max-depth 0 --dominance-threshold 0.5 --tag "bootstrap_2025-12-30_seed=dominant_enters_cycle_title_thr=0.5"`

Upstream branch-chase ("source of the Nile" exploration):
- `python n-link-analysis/scripts/branch-basin-analysis.py --n 5 --cycle-title Connecticut --max-depth 0 --log-every 25 --top-k 50 --write-membership-top-k 10 --out-prefix "branches_n=5_seed=Connecticut"`
- `python n-link-analysis/scripts/branch-basin-analysis.py --n 5 --cycle-title "East_Coast_of_the_United_States" --max-depth 0 --log-every 25 --top-k 50 --write-membership-top-k 10 --out-prefix "branches_n=5_seed=East_Coast_of_the_United_States"`
- `python n-link-analysis/scripts/branch-basin-analysis.py --n 5 --cycle-title Virginia --max-depth 0 --log-every 25 --top-k 50 --write-membership-top-k 10 --out-prefix "branches_n=5_seed=Virginia"`

Dominant-upstream chase (least-trunk-like contrast runs):
- `python n-link-analysis/scripts/chase-dominant-upstream.py --n 5 --seed-title "Animal" --max-hops 40 --max-depth 0 --log-every 0 --dominance-threshold 0.0 --out "data/wikipedia/processed/analysis/dominant_upstream_chain_n=5_from=Animal_leasttrunk_bootstrap_2025-12-30.tsv"`
- `python n-link-analysis/scripts/chase-dominant-upstream.py --n 5 --seed-title "American_Revolutionary_War" --max-hops 40 --max-depth 0 --log-every 0 --dominance-threshold 0.0 --out "data/wikipedia/processed/analysis/dominant_upstream_chain_n=5_from=American_Revolutionary_War_leasttrunk_bootstrap_2025-12-30.tsv"`

### 4.3 Output Artifacts Produced

All outputs were written under:
- `data/wikipedia/processed/analysis/`

Key artifacts:
- `sample_traces_n=5_num=100_seed0=0.tsv`
- `sample_traces_n=5_num=50_seed0=0_bootstrap_2025-12-30.tsv`
- `sample_traces_n=5_num=5000_seed0=0_minout=50_bootstrap_2025-12-30.tsv`
- `preimages_n=5.tsv`
- `preimages_n=5_massachusetts.tsv` (limited list with titles)
- `edges_n=5.duckdb` (materialized edge table for reverse expansions)
- `basin_from_cycle_n=5_layers.tsv` (Massachusetts/Gulf_of_Maine)
- `basin_n=5_cycle=Sea_salt__Seawater_layers.tsv`
- `basin_n=5_cycle=Mountain__Hill_layers.tsv`
- `basin_n=5_cycle=Lithic_reduction__Stone_tool_layers.tsv`
- `basin_n=5_cycle=Autumn__Summer_layers.tsv`
- `basin_n=5_cycle=Kingdom_(biology)__Animal_layers.tsv`
- `basin_n=5_cycle=Latvia__Lithuania_layers.tsv`
- `basin_sizes_n=5_summary_bootstrap_2025-12-30.tsv`
- `branches_n=5_cycle=Massachusetts__Gulf_of_Maine_branches_all.tsv`
- `branches_n=5_cycle=Massachusetts__Gulf_of_Maine_branches_topk.tsv`
- `branches_n=5_cycle=Massachusetts__Gulf_of_Maine_assignments.parquet` (membership assignments for top entry branches)
- `branches_n=5_seed=Connecticut_branches_all.tsv`
- `branches_n=5_seed=Connecticut_branches_topk.tsv`
- `branches_n=5_seed=Connecticut_assignments.parquet`
- `branches_n=5_seed=East_Coast_of_the_United_States_branches_all.tsv`
- `branches_n=5_seed=East_Coast_of_the_United_States_branches_topk.tsv`
- `branches_n=5_seed=East_Coast_of_the_United_States_assignments.parquet`
- `branches_n=5_seed=Virginia_branches_all.tsv`
- `branches_n=5_seed=Virginia_branches_topk.tsv`
- `branches_n=5_seed=Virginia_assignments.parquet`
- `branches_n=5_cycle=Sea_salt__Seawater_branches_all.tsv`
- `branches_n=5_cycle=Sea_salt__Seawater_branches_topk.tsv`
- `branches_n=5_cycle=Mountain__Hill_branches_all.tsv`
- `branches_n=5_cycle=Mountain__Hill_branches_topk.tsv`
- `branches_n=5_cycle=Autumn__Summer_branches_all.tsv`
- `branches_n=5_cycle=Autumn__Summer_branches_topk.tsv`
- `branches_n=5_cycle=Kingdom_(biology)__Animal_branches_all.tsv`
- `branches_n=5_cycle=Kingdom_(biology)__Animal_branches_topk.tsv`
- `branches_n=5_cycle=Latvia__Lithuania_branches_all.tsv`
- `branches_n=5_cycle=Latvia__Lithuania_branches_topk.tsv`
- `branches_n=5_cycle=Thermosetting_polymer__Curing_(chemistry)_branches_all.tsv`
- `branches_n=5_cycle=Thermosetting_polymer__Curing_(chemistry)_branches_topk.tsv`
- `branches_n=5_cycle=Precedent__Civil_law_branches_all.tsv`
- `branches_n=5_cycle=Precedent__Civil_law_branches_topk.tsv`
- `branches_n=5_cycle=American_Revolutionary_War__Eastern_United_States_branches_all.tsv`
- `branches_n=5_cycle=American_Revolutionary_War__Eastern_United_States_branches_topk.tsv`
- `branch_trunkiness_dashboard_n=5_bootstrap_2025-12-30.tsv`
- `dominant_upstream_chain_n=5_from=Animal_leasttrunk_bootstrap_2025-12-30.tsv`
- `dominant_upstream_chain_n=5_from=American_Revolutionary_War_leasttrunk_bootstrap_2025-12-30.tsv`
- `dominant_upstream_chain_n=5_from=Eastern_United_States_control_bootstrap_2025-12-30.tsv`
- `dominance_collapse_dashboard_n=5_bootstrap_2025-12-30_seed=dominant_enters_cycle_title_thr=0.5.tsv`

---

## 5. Findings

### 5.1 Cycle Prevalence Under N=5 Sampling

From 100 sampled starts (with `min_outdegree=50` to avoid trivial early halts):
- terminal counts: `CYCLE = 97`, `HALT = 3`
- 2-cycles were common among cycle outcomes (majority in this sample)

One notably frequent 2-cycle observed:
- `Gulf_of_Maine ↔ Massachusetts`: observed **22 / 100** sample traces terminating in this cycle.

Bootstrap rerun corroboration (50 samples):
- terminal counts: `CYCLE = 49`, `HALT = 1`
- `Gulf_of_Maine ↔ Massachusetts`: observed **11 / 50**

Large sampling run corroboration (5000 samples):
- terminal counts: `CYCLE = 4848`, `HALT = 152`
- top observed cycles included many 2-cycles; `Gulf_of_Maine ↔ Massachusetts` remained dominant (**913 / 5000**), with `Sea_salt ↔ Seawater` next (**194 / 5000**).

### 5.2 Massive Basin Identified: Massachusetts ↔ Gulf_of_Maine

The cycle was confirmed by successor lookup under $f_5$:
- `Gulf_of_Maine → Massachusetts`
- `Massachusetts → Gulf_of_Maine`

Full basin computation (reverse BFS set expansion) produced:
- basin size (unique nodes): **1,009,471**
- reverse-depth to exhaustion: **168**

Interpretation:
- This is a plausible “giant basin” candidate under $f_5$.

Downstream / aggregation note (what is “special”):
- Branch analysis shows an extreme concentration into a single depth-1 entry node.
- The dominant entry branch is `Connecticut → Massachusetts` and contains **998,762** upstream nodes (≈ **98.94%** of the upstream basin, excluding the 2 cycle nodes).
- The remaining **1,254** entry branches are mostly tiny (`916` singleton branches; `1202` branches of size ≤ 10).

Operational interpretation:
- The Massachusetts loop is likely not “special” intrinsically; it is a downstream sink for at least one extremely high-aggregation predecessor (here: `Connecticut`).

Upstream "source" chase (what is upstream of Connecticut?):
- `East_Coast_of_the_United_States → Connecticut` captures **994,062 / 998,761** upstream nodes (≈ **99.53%**).
- `Virginia → East_Coast_of_the_United_States` captures **993,316 / 994,061** upstream nodes (≈ **99.93%**).
- `Washington,_D.C. → Virginia` captures **954,558 / 993,315** upstream nodes (≈ **96.10%**).

Extended chase (continuation starting from `Washington,_D.C.`):
- The dominant-trunk chase does not stay purely geographic; it quickly tunnels through high-centrality administrative/abstract pages.
- Example chain prefix:
  - `2020_United_States_census → Washington,_D.C.` (≈ **76.27%** of upstream mass)
  - `Bedminster,_New_Jersey → 2020_United_States_census` (≈ **89.47%**)
  - `Somerset_Hills → Bedminster,_New_Jersey` (≈ **100%**)
  - `… → Rights` (continuing)

Exhaustion example (continuation starting from `Rights`):
- A continued chase from `Rights` eventually reached a node with no predecessors under $f_5$ (termination):
  - `… → Warawarani → (no predecessors)`

### 5.3 Basin Size Comparison (Partial)

Other N=5 2-cycle basins computed (full, not depth-capped):
- `Sea_salt ↔ Seawater`: **265,940**
- `Mountain ↔ Hill`: **189,269**
- `Lithic_reduction ↔ Stone_tool`: **60,159**

Additional N=5 2-cycle basins computed (full, not depth-capped):
- `Autumn ↔ Summer`: **162,689**
- `Kingdom_(biology) ↔ Animal`: **116,998**
- `Latvia ↔ Lithuania`: **83,403**
- `Thermosetting_polymer ↔ Curing_(chemistry)`: **61,353**
- `Precedent ↔ Civil_law`: **56,314**
- `American_Revolutionary_War ↔ Eastern_United_States`: **46,437**

### 5.4 Branch “Trunkiness” Across Basins (Depth-1 Entry Concentration)

A compact summary table was generated:
- `data/wikipedia/processed/analysis/branch_trunkiness_dashboard_n=5_bootstrap_2025-12-30.tsv`

In this batch, many basins show extreme concentration into a single depth-1 entry branch (largest branch share of *total basin*, i.e. including the cycle nodes):
- `Thermosetting_polymer ↔ Curing_(chemistry)`: top-1 share ≈ **0.9997** (dominant entry: `Concrete`)
- `Autumn ↔ Summer`: top-1 share ≈ **0.9948** (dominant entry: `Mediterranean_basin`)
- `Massachusetts ↔ Gulf_of_Maine`: top-1 share ≈ **0.9894** (dominant entry: `Connecticut`)
- `Mountain ↔ Hill`: top-1 share ≈ **0.9786** (dominant entry: `Mountain_range`)
- `Sea_salt ↔ Seawater`: top-1 share ≈ **0.9770** (dominant entry: `Fast_ice`)
- `Latvia ↔ Lithuania`: top-1 share ≈ **0.9692** (dominant entry: `Poland`)

Not all tested basins are “single-trunk”:
- `Precedent ↔ Civil_law`: top-1 share ≈ **0.8888** (dominant entry: `Constitution`)
- `American_Revolutionary_War ↔ Eastern_United_States`: top-1 share ≈ **0.7379** (dominant entry: `George_Washington`)
- `Kingdom_(biology) ↔ Animal`: top-1 share ≈ **0.3658** (dominant entry: `Brain`)

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
