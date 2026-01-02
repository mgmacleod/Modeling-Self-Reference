# LLM-Facing Documentation for Self Reference Modeling Project

**Quick Start**: This directory contains documentation optimized for AI assistants working on this project.

## Project Summary

This project applies **formal graph theory to self-referential systems** (Wikipedia, databases, code) to discover hidden structure through deterministic traversal rules. We prove that finite self-referential graphs partition into "basins of attraction" under any deterministic rule, and that switching between rules ("tunneling") reveals semantic relationships invisible to single-rule analysis. Current implementation focus: extracting and analyzing Wikipedia's link graph to validate N-Link Rule Theory empirically.

## For New Sessions: Bootstrap Instructions

**Step 1 - Read universal context** (Tier 1, ~8-10k tokens):
1. This README.md - Project overview and navigation guide
2. [development-arc-summary.md](development-arc-summary.md) - High-level project evolution and key discoveries
3. [project-timeline.md](project-timeline.md) - Read latest 3-5 entries for current state
4. [llm-project-management-instructions/documentation-standards.md](llm-project-management-instructions/documentation-standards.md) - How to write documentation
5. [llm-project-management-instructions/project-management-practices.md](llm-project-management-instructions/project-management-practices.md) - How to maintain the project
6. [contracts/README.md](contracts/README.md) - Theory ↔ experiment ↔ evidence contracts (prevents stealth edits)

**Step 2 - Load working context** (Tier 2, ~10-20k tokens):
- **If working on theory**: Load [theories-proofs-conjectures/INDEX.md](theories-proofs-conjectures/INDEX.md), then specific theory docs as needed
- **If working on implementation**: Navigate to working directory, read `implementation.md`, `data-sources.md`, etc.
- **If linking theory ↔ empirics**: Use [contracts/contract-registry.md](contracts/contract-registry.md) as the authoritative index of theory–experiment–evidence linkages
- **If resuming empirical work**: Load [../n-link-analysis/INDEX.md](../n-link-analysis/INDEX.md) and the relevant investigation doc(s) under `n-link-analysis/empirical-investigations/`
- These are co-located with code - no central registry needed

**Note**: The contracts registry is an intentional exception: it is a cross-cutting index used to bind theory, experiments, and evidence without rewriting canonical theory documents.

**Step 3 - Deep dive if needed** (Tier 3, no token limit):
- Read granular debugging documentation only when troubleshooting specific issues

**Note**: Theory documents are Tier 2 (load when needed), not Tier 1. The project summary above provides sufficient orientation without mathematical details.

## Theory Overview (Tier 2 - Load When Working on Theory)

The mathematical foundation is documented in [theories-proofs-conjectures/](theories-proofs-conjectures/):

- **[INDEX.md](theories-proofs-conjectures/INDEX.md)** - Load this first for theory context (points to active documents)
- **[unified-inference-theory.md](theories-proofs-conjectures/unified-inference-theory.md)** - Comprehensive integration of all formal theories
- **[n-link-rule-theory.md](theories-proofs-conjectures/n-link-rule-theory.md)** - Foundational theorems for deterministic traversal on finite graphs
- **[database-inference-graph-theory.md](theories-proofs-conjectures/database-inference-graph-theory.md)** - Extension to typed database graphs and multi-rule tunneling

**When to load**: Only when actively working on theory development or applying theoretical insights to implementation. The project summary above provides sufficient context for most work.

## Documentation Philosophy

This project uses **cumulative, sparse documentation** that grows over time rather than status snapshots. Documentation is LLM-first: structured over narrative, explicit over implicit, optimized for machine parsing and reasoning. See [llm-project-management-instructions/documentation-standards.md](llm-project-management-instructions/documentation-standards.md) for complete guidelines.

---

**Last Updated**: 2026-01-01
**Status**: Active development
