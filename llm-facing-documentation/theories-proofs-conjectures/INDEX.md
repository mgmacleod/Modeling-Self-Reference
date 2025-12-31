# Theory Documents Index

**Purpose**: Mathematical foundations for self-referential graph analysis  
**Last Updated**: 2025-12-30

---

## All Files Tier 2 (Load all when working on theory)

| Document | Purpose | Tokens |
|----------|---------|--------|
| [unified-inference-theory.md](unified-inference-theory.md) | Comprehensive integration of all formal theories | ~5k |
| [n-link-rule-theory.md](n-link-rule-theory.md) | Foundational theorems for deterministic traversal | ~10k |
| [database-inference-graph-theory.md](database-inference-graph-theory.md) | Extension to typed graphs and multi-rule tunneling | ~10k |

**Total**: ~25k tokens (formalized = lightweight)

---

## External / Non-canonical Artifacts

These are reference artifacts and must not be treated as canonical theory.

- [sqsd.html](sqsd.html) — **Author**: Ryan Querin. External artifact explicitly based on project work; integrate only via explicit contract entries in [llm-facing-documentation/contracts/contract-registry.md](../contracts/contract-registry.md).

---

## Deprecated Documents

**Location**: [deprecated/](deprecated/)
- `inference-summary.md` - Superseded by unified-inference-theory.md
- `inference-summary-with-event-tunneling.md` - Superseded by unified-inference-theory.md

**Never load** documents in deprecated/ directory.

---

## Usage

**When working on theory**: Load all three active documents for complete mathematical context

**When NOT to load**: Regular implementation work (use project summary in README.md instead)

**Load order**:
1. unified-inference-theory.md (overview)
2. n-link-rule-theory.md + database-inference-graph-theory.md (details)

---
