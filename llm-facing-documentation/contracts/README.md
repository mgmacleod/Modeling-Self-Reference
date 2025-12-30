# Theory–Experiment–Evidence Contracts

**Purpose**: Provide *bi-directional, explicit contracts* between:
- Theory claims (stable, canonical theory docs)
- Experiments (scripts, datasets, parameters)
- Evidence (outputs + summarized findings)

This layer exists to avoid “stealth edits” to theory documents while still allowing rapid empirical iteration.

**Design constraints**
- Canonical theory documents are **append-only** for routine evolution.
- Any substantial rewrite must use **deprecation + replacement**, not silent modification.
- Contracts are the *operational glue*: theory ↔ experiments ↔ evidence.
- This directory is intentionally **distinct** from the project’s INDEX-based meta-documentation system.

**How to use**
- Add a contract entry in `contract-registry.md` when a theory claim is tested or when an empirical finding is promoted to evidence.
- Keep contracts small, explicit, and link-heavy.

**Required fields (minimum viable contract)**
- Contract ID (stable)
- Theory reference(s) (doc + section name or anchor)
- Experiment reference(s) (script path + invocation + parameters)
- Evidence reference(s) (investigation doc + output paths)
- Status (`proposed` | `running` | `supported` | `refuted` | `inconclusive` | `deprecated`)
- Provenance (who/when)

**Naming**
- Contract IDs should be short and stable, e.g. `NLR-C-0001` (N-Link Rule, Contract).

## How to Cite External Artifacts

When referencing third-party or externally authored work (including artifacts stored in this repo), use this process:

- Create or update an `EXT-*` entry in `contract-registry.md` with **author**, **artifact link**, and **redistribution/license** status.
- Create a corresponding `NLR-C-*` (or relevant domain) contract that records:
	- where the artifact is cited (theory doc touchpoints)
	- what it is used for (motivation, definition, proof sketch, empirical interpretation)
	- what evidence (if any) depends on it
- In canonical theory documents, keep references **additive** (append-only) and include **explicit author credit**.

This is intended to make attribution unambiguous and prevent “silent integration” of external work.

**Last Updated**: 2025-12-30
