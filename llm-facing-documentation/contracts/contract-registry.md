# Contract Registry

**Purpose**: A registry of explicit theory–experiment–evidence contracts.

This is the *primary index* for contract objects, and should be treated as append-only (you can add new entries; avoid rewriting old ones except to mark them deprecated).

**Last Updated**: 2025-12-31

---

## Active Contracts

### NLR-C-0001 — Long-tail basin size under fixed-N traversal (Wikipedia proving ground)

- **Status**: supported (empirical; scope: Wikipedia namespace 0, non-redirect pages)
- **Theory**:
  - [n-link-rule-theory.md](../theories-proofs-conjectures/n-link-rule-theory.md) (basins, cycles, terminals)
  - [unified-inference-theory.md](../theories-proofs-conjectures/unified-inference-theory.md) (integration framing)
- **Experiment**:
  - [map-basin-from-cycle.py](../../n-link-analysis/scripts/map-basin-from-cycle.py) (reverse reachability / basin mapping)
  - [sample-nlink-traces.py](../../n-link-analysis/scripts/sample-nlink-traces.py) (cycle sampling)
- **Evidence**:
  - [long-tail-basin-size.md](../../n-link-analysis/empirical-investigations/long-tail-basin-size.md)
  - Outputs under `data/wikipedia/processed/analysis/`
- **Notes**:
  - This contract is intentionally "Wikipedia-first" to preserve cultural salience and reduce concerns of bespoke/system-fit bias.

---

### NLR-C-0003 — N-dependent phase transition in basin structure (Wikipedia)

- **Status**: supported (empirical; scope: Wikipedia namespace 0, non-redirect pages, N∈{3,5,7})
- **Theory**:
  - [n-link-rule-theory.md](../theories-proofs-conjectures/n-link-rule-theory.md) (N-link rule definition, basin partitioning)
  - Extends NLR-C-0001 to cross-N comparison
- **Experiment**:
  - [reproduce-main-findings.py](../../n-link-analysis/scripts/reproduce-main-findings.py) (parameterized by N)
  - [compare-across-n.py](../../n-link-analysis/scripts/compare-across-n.py) (cross-N analysis)
  - [map-basin-from-cycle.py](../../n-link-analysis/scripts/map-basin-from-cycle.py) (basin mapping)
  - [sample-nlink-traces.py](../../n-link-analysis/scripts/sample-nlink-traces.py) (cycle sampling)
- **Evidence**:
  - [REPRODUCTION-OVERVIEW.md](../../n-link-analysis/REPRODUCTION-OVERVIEW.md) (comprehensive session summary)
  - [CROSS-N-FINDINGS.md](../../CROSS-N-FINDINGS.md) (publication-quality discovery summary)
  - Cross-N visualizations: `n-link-analysis/report/assets/cross_n_*.png` (6 charts)
  - Data outputs: `data/wikipedia/processed/analysis/*_n={3,5,7}_*` (~60 files)
- **Key Finding**:
  - N=5 exhibits 20-60× larger basins than N∈{3,7} with extreme single-trunk structure (67% of basins >95% concentration)
  - Same 6 terminal cycles persist across N with radically different properties (up to 4289× size variation)
  - Hypothesis: N=5 sits at critical point (33% page coverage threshold) in phase transition analogous to percolation phenomena
- **Theory Claim Evaluated**:
  - **Refuted**: "Basin structure is universal across N" → Structure is rule-dependent, not graph-intrinsic
  - **Supported**: "Finite self-referential graphs partition into basins under deterministic rules" → Holds for all N∈{3,5,7}
- **Notes**:
  - This discovery suggests basin properties emerge from rule-graph coupling, not graph topology alone
  - Critical phenomena framework may apply (percolation-like phase transition at N=5)
  - Next steps: Finer N resolution (N∈{4,6,8,9,10}), other language Wikipedias, theoretical modeling

---

### NLR-C-0002 — Citation & integration lineage for sqsd.html → N-Link theory

- **Status**: proposed
- **Goal**: Ensure every usage of `sqsd.html` is explicitly attributed, scoped, and linked into the theory–experiment–evidence chain without “stealth integration” into canonical theory.
- **External Artifact (source)**:
  - [sqsd.html](../theories-proofs-conjectures/sqsd.html) — Ryan Querin (external)
- **Theory (targets / touchpoints)**:
  - [n-link-rule-theory.md](../theories-proofs-conjectures/n-link-rule-theory.md) (if/when SQSD concepts are cited)
  - [database-inference-graph-theory.md](../theories-proofs-conjectures/database-inference-graph-theory.md) (if/when SQSD concepts are cited)
  - [unified-inference-theory.md](../theories-proofs-conjectures/unified-inference-theory.md) (if/when SQSD concepts are cited)
- **Evidence**:
  - Add a dedicated investigation doc when SQSD is first used for an empirical argument (e.g., under `n-link-analysis/empirical-investigations/`).
- **Operational rules**:
  - Do not quote or embed large portions of `sqsd.html` into canonical theory; prefer high-level references.
  - Any canonical-theory citation should be additive (append-only) and must include author credit.
  - Before broader redistribution, record explicit permission/license terms for `sqsd.html` under `EXT-A-0001`.

---

## External / Third-Party Artifacts (Referenced by Contracts)

### EXT-A-0001 — sqsd.html (Structural Query Semantics as a Deterministic Space)

- **Status**: referenced (not yet integrated into canonical theory)
- **Artifact**: [sqsd.html](../theories-proofs-conjectures/sqsd.html)
- **Author**: Ryan Querin
- **Relationship**: authored externally; explicitly based on (and extending) project work
- **Redistribution / License**: TODO — record explicit permission and license terms before wider distribution
- **Integration policy**:
  - Do not treat as canonical theory.
  - When used, reference via explicit contract entries (and cite author).
