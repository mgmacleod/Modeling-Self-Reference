# Document Archaeology Survey

**Document Type**: Analysis report
**Target Audience**: Both (LLMs and humans)
**Purpose**: Inventory all markdown documents, assess conformance to project specs, recommend cleanup
**Last Updated**: 2026-01-03
**Status**: Active

---

## Executive Summary

**Total markdown files found**: 95+
**Files conforming to spec**: ~35 (37%)
**Files needing attention**: ~60 (63%)

**Key issues identified**:
1. UPPERCASE file naming (violates kebab-case standard)
2. Missing metadata blocks
3. Ad-hoc working documents outside proper structure
4. Duplicate/overlapping content across locations
5. Context handoff documents that should be ephemeral

---

## Document Inventory by Location

### 1. `llm-facing-documentation/` (Tier 1 - Conforming) ✓

**Status**: Well-organized, follows standards

| File | Metadata | Naming | Notes |
|------|----------|--------|-------|
| README.md | ✓ | ✓ | Bootstrap entry point |
| development-arc-summary.md | ✓ | ✓ | High-level project evolution |
| project-timeline.md | ✓ | ✓ | Cumulative history |
| end-of-session-protocol.md | ✓ | ✓ | Procedure doc |
| llm-project-management-instructions/*.md | ✓ | ✓ | Standards and practices |
| theories-proofs-conjectures/*.md | ✓ | ✓ | Theory documents |
| contracts/*.md | ✓ | ✓ | Theory-evidence linkages |

**Recommendation**: No changes needed.

---

### 2. `working/` (Non-Conforming) ⚠️

**Status**: Ad-hoc working notes, not in spec

| File | Issues |
|------|--------|
| QUICK-START-NEXT-SESSION.md | UPPERCASE, no metadata, uses emojis |
| CROSS-N-FINDINGS.md | UPPERCASE, no metadata, findings doc |
| ENTRY-BREADTH-SESSION-SUMMARY.md | UPPERCASE, no metadata |
| NEXT-SESSION-DEPTH-MECHANICS.md | UPPERCASE, no metadata, planning doc |
| NEXT-SESSION-SCALING-UP.md | UPPERCASE, no metadata |
| SESSION-SUMMARY-STAT-MECH.md | UPPERCASE, no metadata |

**Problem**: These appear to be inter-session handoff documents created during active work, but:
- They don't follow the tiered documentation system
- They duplicate content that should be in `project-timeline.md` or `empirical-investigations/`
- CROSS-N-FINDINGS.md contains substantive findings that belong in `report/` or `empirical-investigations/`

**Recommendation**:
1. **Consolidate findings** from CROSS-N-FINDINGS.md → `n-link-analysis/report/` or `empirical-investigations/`
2. **Delete or archive** session handoff docs after merging key content into timeline
3. **Do not create future** `working/NEXT-SESSION-*.md` files - use the timeline's "Next Steps" pattern instead

---

### 3. `notes/` (Non-Conforming) ⚠️

**Status**: Single handoff document

| File | Issues |
|------|--------|
| context-handoff.md | No metadata, very long (~375 lines), Claude-to-Claude context dump |

**Problem**: This is a context continuation summary for when a session ran out of context. It's a transcript/summary, not proper documentation.

**Recommendation**:
1. **Delete** after extracting any key decisions/findings to timeline
2. **Don't create these in future** - use `/end-session` slash command or end-of-session protocol instead

---

### 4. `n-link-analysis/` (Mixed Conformance) ⚠️

**Well-organized files (✓)**:
- INDEX.md
- implementation.md
- scripts-reference.md
- future.md
- empirical-investigations/INDEX.md

**UPPERCASE naming violations**:

| Current Name | Should Be |
|--------------|-----------|
| NEXT-STEPS.md | next-steps.md |
| FRAMEWORK-TESTING-PLAN.md | framework-testing-plan.md |
| SANITY-CHECK-ENTRY-BREADTH.md | *(merge into investigation doc)* |
| VIZ-DATA-GAP-ANALYSIS.md | viz-data-gap-analysis.md |
| ENTRY-BREADTH-README.md | *(merge into scripts-reference.md)* |
| TUNNELING-ROADMAP.md | tunneling-roadmap.md |

**`empirical-investigations/` subdirectory** (17 files, all UPPERCASE):
- All files use UPPERCASE-WITH-HYPHENS.md pattern
- Most have proper internal structure but no metadata blocks
- Some have Last Updated fields but not full metadata

**`report/` subdirectory** (10 files, all UPPERCASE):
- DATASET_CARD.md, PROJECT-WRAP-UP.md, TUNNELING-FINDINGS.md, etc.
- Mixed metadata conformance

**`viz/` subdirectory**:
- VIZ-CONSOLIDATION-PLAN.md - Has metadata ✓
- NEXT-SESSION-VIZ-CONSOLIDATION.md - UPPERCASE, planning doc
- MULTIPLEX-EXPLORER-GUIDE.md - UPPERCASE
- tunneling/README.md - lowercase, good

**`scripts/` subdirectory**:
- HARNESS-README.md - UPPERCASE
- INTERACTIVE-EXPLORER-GUIDE.md - UPPERCASE
- ENHANCED-EXPLORER-GUIDE.md - UPPERCASE
- tunneling/README.md - lowercase, good

**Recommendation**:
1. **Rename all UPPERCASE files** to kebab-case
2. **Add metadata blocks** to all investigation and report documents
3. **Consider consolidating** README-type files into scripts-reference.md

---

### 5. `nlink_api/` (Partial Conformance)

| File | Status |
|------|--------|
| README.md | No metadata block (typical for README) |
| NEXT-SESSION.md | Has metadata ✓, good format, but UPPERCASE |

**Recommendation**: Rename NEXT-SESSION.md → next-session.md

---

### 6. `data-pipeline/` (Conforming) ✓

| File | Status |
|------|--------|
| INDEX.md | ✓ |
| wikipedia-decomposition/INDEX.md | ✓ |
| wikipedia-decomposition/implementation-guide.md | ✓ |
| wikipedia-decomposition/data-sources.md | ✓ |
| wikipedia-decomposition/downloaded-and-derived-file-index.md | ✓ |
| wikipedia-decomposition/scripts/deprecated/README.md | ✓ |

**Recommendation**: No changes needed.

---

### 7. `meta-maintenance/` (Conforming) ✓

| File | Status |
|------|--------|
| INDEX.md | ✓ |
| implementation.md | ✓ |
| writing-guide.md | ✓ |
| data-sources.md | ✓ |
| session-log.md | ✓ |
| future.md | ✓ |

**Recommendation**: No changes needed.

---

### 8. `human-facing-documentation/` (Conforming) ✓

All files have proper metadata and naming.

**Recommendation**: No changes needed.

---

### 9. Root-Level Files (Mixed)

| File | Status | Notes |
|------|--------|-------|
| CLAUDE.md | N/A | Special file for Claude Code |
| README.md | No metadata | Standard for root README |
| initialization.md | Has metadata ✓ | Good |
| VISUALIZATION-GUIDE.md | No metadata, UPPERCASE | Should be lowercase, add metadata |

**Recommendation**: Rename VISUALIZATION-GUIDE.md → visualization-guide.md, add metadata

---

### 10. `.claude/commands/` (Conforming) ✓

| File | Status |
|------|--------|
| end-session.md | Slash command definition |
| init-workspace.md | Slash command definition |

**Recommendation**: No changes needed.

---

## Conformance Summary

### By Naming Convention

| Category | Count | % |
|----------|-------|---|
| Correct kebab-case | ~40 | 42% |
| UPPERCASE (violation) | ~50 | 53% |
| Other (README.md, etc.) | ~5 | 5% |

### By Metadata Presence

| Category | Count | % |
|----------|-------|---|
| Full metadata block | ~35 | 37% |
| Partial metadata | ~15 | 16% |
| No metadata | ~45 | 47% |

---

## Prioritized Cleanup Recommendations

### Tier 1: High Priority (Structural Issues)

1. **Delete/archive `working/` directory contents**
   - Extract findings from CROSS-N-FINDINGS.md to proper location
   - Merge session summaries into timeline
   - These are ephemeral handoff documents, not canonical documentation

2. **Delete `notes/context-handoff.md`**
   - This is a one-time context dump, not documentation
   - Extract any key content to timeline first

3. **Consolidate redundant content**
   - ENTRY-BREADTH-README.md → merge into scripts-reference.md
   - SANITY-CHECK-ENTRY-BREADTH.md → merge into empirical investigation

### Tier 2: Medium Priority (Naming Violations)

1. **Rename all UPPERCASE files in `n-link-analysis/`**
   - 40+ files need renaming
   - Can be done with a batch script

2. **Rename root-level VISUALIZATION-GUIDE.md**

3. **Rename `nlink_api/NEXT-SESSION.md`**

### Tier 3: Lower Priority (Metadata Gaps)

1. **Add metadata blocks to `empirical-investigations/` files**
   - 17 investigation documents
   - Use standard template

2. **Add metadata blocks to `report/` files**
   - 10 report documents

3. **Add metadata to guide/README files in scripts/, viz/**

---

## Proposed Batch Rename Script

```bash
#!/bin/bash
# Run from project root

# n-link-analysis main directory
for f in n-link-analysis/NEXT-STEPS.md \
         n-link-analysis/FRAMEWORK-TESTING-PLAN.md \
         n-link-analysis/SANITY-CHECK-ENTRY-BREADTH.md \
         n-link-analysis/VIZ-DATA-GAP-ANALYSIS.md \
         n-link-analysis/ENTRY-BREADTH-README.md \
         n-link-analysis/TUNNELING-ROADMAP.md; do
    if [ -f "$f" ]; then
        newname=$(echo "$f" | tr '[:upper:]' '[:lower:]')
        git mv "$f" "$newname"
    fi
done

# Similar patterns for subdirectories...
```

---

## Future Prevention

To prevent document sprawl in the future:

1. **Use end-of-session protocol** instead of creating NEXT-SESSION files
2. **Add findings directly to timeline** with proper date headers
3. **Create investigation docs in `empirical-investigations/`** from the start
4. **Review naming before committing** - no UPPERCASE

---

## Summary Statistics

| Metric | Value |
|--------|-------|
| Total .md files | 95+ |
| Directories with docs | 12 |
| Files needing rename | ~50 |
| Files needing metadata | ~45 |
| Files to delete/archive | ~7 |
| Directories fully conforming | 5 |

---

## Changelog

### 2026-01-03
- Initial document archaeology survey
- Inventoried 95+ markdown files across 12 directories
- Identified naming, metadata, and structural conformance issues
- Proposed prioritized cleanup plan

---

**END OF DOCUMENT**
