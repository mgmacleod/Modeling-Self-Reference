# Self-Referential Documentation System - Implementation Guide

**Document Type**: Crystallized Specification  
**Target Audience**: LLMs + Developers  
**Purpose**: Define the complete architecture of the documentation system  
**Last Updated**: 2025-12-12  
**Dependencies**: [documentation-standards.md](../llm-facing-documentation/llm-project-management-instructions/documentation-standards.md), [project-management-practices.md](../llm-facing-documentation/llm-project-management-instructions/project-management-practices.md)  
**Status**: Stable

---

## Overview

This document describes a **self-referential, recursive documentation system** designed for LLM-facing projects. The system solves the "snapshot staleness" problem through cumulative, append-only documentation with progressive context loading.

**Key Principle**: Documentation that grows over time without requiring full re-reads each session.

---

## Architecture

### Three-Tier Information Pyramid

```
Tier 1: Universal (llm-facing-documentation/)
├── Read every session (~8-12k tokens)
├── Meta-docs: How to write/maintain docs
├── Timeline: Changelog-style index with drill-down links
└── Theory: Foundational papers (never change)

Tier 2: Contextual (data-pipeline/, meta-maintenance/, n-link-analysis/, etc.)
├── Read only when working in that directory
├── session-log.md: Working history, decisions, discoveries
├── implementation.md: Crystallized spec (this document)
├── data-sources.md: Reference materials, external links
└── future.md: TODOs, open questions, next steps

Tier 3: Granular (Tier 2 subdirectories)
├── Read only when debugging specific subsystem
├── Same structure as Tier 2 (session-log, future, etc.)
└── Maximum depth: No Tier 4 (use code comments instead)
```

**Information Flow**:
- **Documentation** (UP): Tier 3 debugging notes → Tier 2 summaries → Tier 1 timeline
- **Reading** (DOWN): Tier 1 index → Tier 2 specs → Tier 3 details

---

## Standard Directory Files

Every Tier 2/3 directory follows this pattern:

### `session-log.md` (Cumulative, Append-Only)
**Purpose**: Working notes, decisions, trial-and-error  
**Updated**: After commits, at session ends  
**Format**: Reverse chronological, latest first  
**Content**:
- What we tried (even if it failed)
- Why we chose approach X over Y
- Blockers encountered and resolved
- Commit references

**Example**:
```markdown
### 2025-12-15 - Template Stripper Optimization
Tried regex approach → failed on nested braces.
Switched to recursive parser → worked but slow.
Added early termination → 10x speedup.
Commit: abc123f
```

### `implementation.md` (Crystallized Spec)
**Purpose**: Clean, structured overview of how the system works  
**Updated**: At major milestones (user-prompted)  
**Format**: Hierarchical with subsections  
**Content**:
- Architecture overview
- Key algorithms/approaches
- File formats and specifications
- Usage examples
- Evolution notes (if design changed significantly)

**This document is an example** of `implementation.md`.

### `data-sources.md` / `*-resources.md` (Cumulative Reference)
**Purpose**: External resources that informed the work  
**Updated**: As discovered  
**Format**: Annotated links with discovery dates  
**Content**:
- URLs to documentation, papers, APIs
- Why each resource was useful
- Key findings from each resource

### `future.md` (TODO List)
**Purpose**: Next steps, open questions, planned work  
**Updated**: At session ends, user prompts  
**Format**: Checklist with priority sections  
**Content**:
- High/Medium/Low priority tasks
- Research questions
- Rejected ideas (with rationale)

---

## Directory-Based Discovery

**No central registry.** Documentation is discovered via directory structure:

1. Session starts → Load Tier 1 (`llm-facing-documentation/`)
2. User says "work on Wikipedia extraction" → Load `data-pipeline/wikipedia-decomposition/*.md`
3. User says "debug template stripper" → Load `data-pipeline/wikipedia-decomposition/template-stripping/*.md`

**Benefits**:
- Self-organizing: Docs live with code
- Scales infinitely: No bottleneck
- Never stale: No central index to maintain

---

## Cross-Cutting References

Use **Wikipedia-style subsection links** across directories:

```markdown
## Data Dependencies

Requires clean link data from the 
[Wikipedia decomposition pipeline](../data-pipeline/wikipedia-decomposition/implementation.md#extraction-pipeline).

Specifically:
- [pages.tsv](../data-pipeline/wikipedia-decomposition/implementation.md#pagestsvspec)
- [links_ordered.tsv](../data-pipeline/wikipedia-decomposition/implementation.md#links_orderedtsv)
```

VSCode/Markdown renders these as **clickable deep links** directly to subsections.

**Avoid**:
- Duplicating content across directories
- Copying specs instead of linking
- Stale copies that diverge

---

## Self-Healing Protocol

### Lazy Validation

**Philosophy**: Fix broken references on encounter, not proactively.

**When LLM encounters broken link**:

1. **Try `file_search`**:
   ```
   file_search("filename.md")
   ```

2. **Check git history**:
   ```powershell
   git log --all --full-history -- '**/filename.md'
   ```

3. **Update document** with correct path

4. **Log the fix** to project-timeline.md:
   ```markdown
   ### 2025-12-12 - Documentation Maintenance
   **Fixed**: Broken reference to `old-path.md` → updated to `new-path.md`
   **Reason**: File renamed in commit abc123f
   ```

5. **Update "Last Updated"** in metadata

### Git as Source of Truth

- Git tracks all file moves/renames automatically
- `git log --follow <file>` shows complete history
- No preemptive validation needed
- VSCode auto-updates relative markdown links on file rename

---

## Update Workflows

### Daily Work Session

1. **Start**: Load Tier 1 (~8-12k tokens)
2. **Navigate**: User specifies work area → Load relevant Tier 2
3. **Work**: Make progress, commit code
4. **Document**: Append to `session-log.md` (manual or prompted)
5. **End**: Update `future.md` with next steps

**Total context**: ~15-20k tokens (manageable)

### Major Milestone

When completing a significant feature:

1. **Update `implementation.md`** (user-prompted):
   - Mark section complete
   - Add evolution notes if design changed
   - Update "Current Status"

2. **Update Tier 1 timeline**:
   ```markdown
   ### 2025-12-15 - Wikipedia Extraction Complete
   Completed decomposition pipeline with template stripping.
   See: [implementation.md](../data-pipeline/wikipedia-decomposition/implementation.md)
   ```

3. **Commit with milestone tag**:
   ```bash
   git commit -m "Complete Wikipedia extraction [timeline: Extraction pipeline done]"
   ```

### Session End

User says "wrap up":

1. Review conversation history
2. Update `future.md` with next steps
3. Append to `session-log.md` with summary
4. Optionally update Tier 1 timeline
5. Suggest git commit if uncommitted work

---

## Tier 1 Structure

`llm-facing-documentation/` contains **ONLY** universal, read-every-session docs:

```
llm-facing-documentation/
├── llm-project-management-instructions/
│   ├── documentation-standards.md     [How to write docs]
│   └── project-management-practices.md [How to maintain project]
├── project-timeline.md                [Changelog-style index]
└── theories-proofs-conjectures/       [Foundational theory papers]
```

**Constraints**:
- Must stay under ~12k tokens total
- No working notes (those go in Tier 2)
- No code specs (those go in Tier 2)
- Only meta-rules and high-level timeline

**Why**: This project will become incredibly expansive. Tier 1 must stay lean so new sessions don't drown in context.

---

## Example Project Structure

```
project-root/
├── llm-facing-documentation/           [Tier 1: Universal]
│   ├── llm-project-management-instructions/
│   ├── project-timeline.md
│   └── theories-proofs-conjectures/
│
├── meta-maintenance/                   [Tier 2: Doc system work]
│   ├── session-log.md
│   ├── implementation.md              ← This document
│   └── future.md
│
├── data-pipeline/                      [Tier 2: Data extraction]
│   └── wikipedia-decomposition/
│       ├── session-log.md
│       ├── implementation.md
│       ├── data-sources.md
│       ├── future.md
│       └── template-stripping/         [Tier 3: If needed]
│           ├── session-log.md
│           └── future.md
│
└── n-link-analysis/                    [Tier 2: Analysis work]
    ├── session-log.md
    ├── implementation.md
    ├── future.md
    └── basin-partitioning/             [Tier 3: If needed]
```

---

## Metadata Blocks

Every documentation file starts with:

```markdown
# Document Title

**Document Type**: [Crystallized Specification | Cumulative | TODO List | etc.]
**Target Audience**: [LLMs | Developers | Both]
**Purpose**: [One-line description]
**Last Updated**: YYYY-MM-DD
**Dependencies**: [Links to prerequisite docs]
**Status**: [Active | Stable | Archived]
```

**Benefits**:
- Quick context for LLMs
- Tracks freshness
- Shows relationships
- Indicates stability

---

## Token Budget

**Design target**: <20k tokens per session

| Context | Token Budget |
|---------|--------------|
| Tier 1 (universal) | ~8-12k |
| Tier 2 (single directory) | ~5-10k |
| Tier 3 (subdirectory, rare) | ~3-5k |
| **Total per session** | **~15-20k** |

**How to stay within budget**:
- Archive old session-log entries after 6 months
- Keep implementation.md concise (link to details instead of duplicating)
- Don't load Tier 3 unless debugging specific subsystem
- Use code comments for fine-grained details (not docs)

---

## Depth Limit: 3 Tiers Maximum

```
Tier 1: project-root/llm-facing-documentation/
Tier 2: project-root/data-pipeline/wikipedia-decomposition/
Tier 3: project-root/data-pipeline/wikipedia-decomposition/template-stripping/
Tier 4: ❌ NO - Use code comments instead
```

**Rationale**: If you need more granularity than Tier 3, the code itself should be self-documenting with comments and well-named functions.

---

## Maintenance Patterns

### Append-Only (session-log.md, data-sources.md, future.md completed tasks)

**Rules**:
- Never delete entries (unless factual errors)
- New entries at top (reverse chronological)
- Timestamp every entry
- Archive old entries after 6 months

### Rewrite-in-Place (implementation.md sections, future.md open tasks)

**Rules**:
- "Current Status" section rewritten each update
- Main content sections updated as understanding evolves
- Keep "Decision Log" cumulative (append-only subsection)
- Mark completed tasks instead of deleting

### Static (Tier 1 meta-docs, theory papers)

**Rules**:
- Only update when fundamental approach changes
- User-prompted updates only
- Major version bumps if philosophy shifts

---

## Key Decisions & Rationale

| Decision | Rationale | Alternatives Rejected |
|----------|-----------|----------------------|
| Lazy self-healing | Git is authoritative source of truth | Preemptive validation scripts |
| Directory-based discovery | Scales infinitely, never stale | Central document registry |
| 3-tier max depth | Prevents doc explosion | Unlimited depth, 2-tier only |
| Wikipedia-style links | Cross-reference without duplication | Copy content, maintain summaries |
| Cumulative + crystallized | Separates "what happened" from "how it works" | Single unified doc |
| Tier 1 universal only | Project will expand massively | Mix universal and contextual |

---

## Evolution Notes

### 2025-12-12 - Initial Design
- Established three-tier pyramid
- Created directory-based discovery heuristic
- Implemented lazy self-healing protocol
- Separated Tier 1 (universal) from Tier 2/3 (contextual)
- System became fully self-referential

---

## Validation

**System is working correctly if**:
- ✅ New sessions load <20k tokens
- ✅ Context discovery takes <2 minutes
- ✅ Documentation maintenance <10% of dev time
- ✅ No central registry to maintain
- ✅ Broken links self-heal when encountered
- ✅ Tier 1 stays lean (<12k tokens) as project grows

**Red flags**:
- ❌ Tier 1 exceeds 15k tokens
- ❌ Can't find relevant context without grep
- ❌ Documenting takes >20% of session time
- ❌ Broken links accumulate unfixed
- ❌ Need Tier 4+ directories

---

## Related Documents

- [Documentation Standards](../llm-facing-documentation/llm-project-management-instructions/documentation-standards.md) - Formatting and style rules
- [Project Management Practices](../llm-facing-documentation/llm-project-management-instructions/project-management-practices.md) - Maintenance procedures
- [Session Log](./session-log.md) - Design history and decisions
- [Future Enhancements](./future.md) - Planned improvements

---

**END OF DOCUMENT**
