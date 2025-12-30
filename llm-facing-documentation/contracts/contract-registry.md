# Contract Registry

**Purpose**: A registry of explicit theory–experiment–evidence contracts.

This is the *primary index* for contract objects, and should be treated as append-only (you can add new entries; avoid rewriting old ones except to mark them deprecated).

**Last Updated**: 2025-12-30

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
  - This contract is intentionally “Wikipedia-first” to preserve cultural salience and reduce concerns of bespoke/system-fit bias.

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
