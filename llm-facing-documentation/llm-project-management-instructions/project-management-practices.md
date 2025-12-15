# Project Management Practices

**Document Type**: Meta-documentation  
**Target Audience**: LLMs  
**Purpose**: How LLMs should maintain project documentation, create new directories, and track progress  
**Last Updated**: 2025-12-15  
**Dependencies**: [documentation-standards.md](./documentation-standards.md), [../../meta-maintenance/implementation.md](../../meta-maintenance/implementation.md)  
**Status**: Active

---

## Core Philosophy

This project uses **cumulative, sparse documentation** that grows over time rather than rewriting "current status" snapshots. Each session appends new information to living documents rather than replacing what came before.

**For complete architecture specification**: See [../../meta-maintenance/implementation.md](../../meta-maintenance/implementation.md)

---

## Three-Tier Documentation System (Quick Reference)

| Tier | Purpose | Read When | Token Budget | Update Pattern |
|------|---------|-----------|--------------|----------------|
| **Tier 1** | Universal orientation | Every session | <12k total | Rare (user prompt) |
| **Tier 2** | Context-specific details | Working in directory | <20k per session | Per feature/milestone |
| **Tier 3** | Granular debugging | Deep-dive needed | No limit | As needed |

**Heuristic**: Read Tier 1 always. Read Tier 2 docs in the directory you're working in. Read Tier 3 only when debugging specific issues.

**For detailed tier definitions and workflows**: See [../../meta-maintenance/implementation.md](../../meta-maintenance/implementation.md)

---

## Starting a New Session (Bootstrap Instructions)

**Step 1: Read Tier 1 (Universal Context)**
1. [project-timeline.md](../project-timeline.md) - Recent history, latest 3-5 entries
2. [documentation-standards.md](./documentation-standards.md) - How to write docs
3. This document - How to maintain project

**Step 2: Identify Current Work**
- Check timeline for active tasks
- User will provide context

**Step 3: Load Tier 2 (Directory-Specific Context)**
- Navigate to working directory
- Read `implementation.md`, `data-sources.md`, etc. in that directory
- No central registry needed - docs co-located with code

**Step 4: Load Tier 3 (If Debugging)**
- Read granular debugging docs in subdirectories
- Max depth: 3 levels

**Total tokens loaded**: ~8-12k (Tier 1) + ~10-20k (Tier 2) = 18-32k typical session

---

## Creating a New Directory with Documentation

**Template for new directory** (copy-paste ready):

```
new-directory-name/
├── implementation.md       # WHAT + HOW (required)
├── data-sources.md         # External resources (optional)
├── session-log.md          # Working history (optional)
└── future.md               # TODOs (optional)
```

**Minimum Required**: `implementation.md` with this structure:

```markdown
# [Directory Purpose] Implementation

**Document Type**: Implementation  
**Target Audience**: LLMs  
**Purpose**: [One-sentence description]  
**Last Updated**: YYYY-MM-DD  
**Status**: [draft | active | deprecated]

---

## Overview

Brief description of what this directory contains and why it exists.

---

## Architecture

High-level design decisions, data flow, component relationships.

---

## Implementation Details

Specific algorithms, data structures, file formats.

---

## Usage Examples

How to use code in this directory.

---

## Open Questions

- [ ] Question 1
- [ ] Question 2

---

## Changelog

### YYYY-MM-DD
- Initial creation
```

**When to create new directory**:
- Starting a new subsystem (e.g., `data-pipeline/`, `graph-analysis/`)
- Grouping related functionality
- Need Tier 2 context isolation

**For more standard files and patterns**: See [../../meta-maintenance/implementation.md#standard-files](../../meta-maintenance/implementation.md#standard-files)

---

## Document Deprecation Policy

### When to Deprecate vs. Git Version

**Deprecate (create deprecated/ subdirectory)**:
- **Theory documents** undergoing major revision/merger
  - Example: Multiple theory summaries → unified comprehensive document
  - Rationale: Substantial divergence from original; old version may confuse if accidentally loaded
  - Pattern: Major conceptual evolution, not incremental improvement

**Use git version history (no deprecation)**:
- **Code files** (Python, scripts, notebooks)
  - Rationale: Git tracks changes; old versions not in namespace
- **Implementation documentation** (iterative updates)
  - Rationale: In-place edits with decision log; git shows history
- **Project management docs** (standards, practices)
  - Rationale: Rare updates; git sufficient for historical reference

### Deprecation Procedure

**When deprecating a document**:

1. **Create deprecated/ subdirectory** in document's directory
   ```
   theories-proofs-conjectures/
   ├── active-doc.md
   ├── deprecated/
   │   └── old-doc.md
   ```

2. **Move superseded document(s)** to deprecated/
   ```powershell
   mv old-doc.md deprecated/
   ```

3. **Add deprecation notice** to moved document:
   ```markdown
   **DEPRECATED**: This document has been superseded by [new-doc.md](../new-doc.md)
   **Date Deprecated**: YYYY-MM-DD
   **Reason**: [Brief explanation]
   **Location**: Moved to deprecated/ subdirectory to reduce context pollution
   ```

4. **Create INDEX.md** (if first deprecation in directory):
   ```markdown
   # [Directory Name] Index
   
   ## Active Documents
   - [active-doc.md](active-doc.md) - Description
   
   ## Deprecated Documents
   **Location**: [deprecated/](deprecated/)
   - `old-doc.md` - Superseded by active-doc.md
   
   **Never load** documents in deprecated/ directory.
   ```

5. **Update cross-references** in other documents pointing to deprecated doc

6. **Log to timeline** with:
   - What was deprecated and why
   - Token savings (if applicable)
   - Pattern established for future

### INDEX.md Pattern

**Purpose**: Guide LLMs to load only active documents

**Create INDEX.md when**:
- First deprecation occurs in a directory
- Directory has multiple related documents (theory, implementation guides)
- Need to prevent accidental loading of deprecated content

**INDEX.md structure**:
- List of active documents with brief descriptions
- List of deprecated documents (location only, not content)
- Explicit "never load deprecated/" instruction
- Token budget guidance if applicable

**Example**: See [../theories-proofs-conjectures/INDEX.md](../theories-proofs-conjectures/INDEX.md)

### Git vs. Deprecation Decision Tree

```
Does document need major revision?
├─ YES: Is it theory/foundational?
│  ├─ YES: Deprecate old version
│  │  └─ Action: Create deprecated/, move old, update links
│  └─ NO: Is it code/implementation?
│     └─ Action: Edit in place, git tracks history
└─ NO: Minor update?
   └─ Action: Edit in place, update timestamp
```

**Philosophy**: Deprecation for namespace hygiene (prevent wrong document loading), git for change history (understand evolution).

---

## Update Triggers & Procedures

### User-Prompted Updates

**Trigger**: User says "update the timeline" or "log this decision"

**Action**:
1. Identify target document (usually [project-timeline.md](../project-timeline.md))
2. If cumulative: Append new entry with timestamp
3. If static: Modify relevant section
4. Always update "Last Updated" metadata

**Example**: "Add to timeline that we completed template stripping algorithm"

---

### End-of-Session Updates

**Trigger**: User says "wrap up" or "summarize what we did"

**Action**:
1. Extract from conversation:
   - Completed tasks
   - Key decisions made
   - Blockers encountered
   - Next steps
2. Append to [project-timeline.md](../project-timeline.md) using template below
3. Update any active working documents
4. Suggest git commit message

**Timeline Entry Template** (copy-paste ready):
```markdown
### Session: YYYY-MM-DD [Optional Title]

**Completed**:
- Item 1
- Item 2

**Decisions Made**:
- Decision A: Rationale
- Decision B: Rationale

**Blockers/Discoveries**:
- Issue X: Description

**Next Steps**:
- Task 1
- Task 2
```

---

### Milestone-Triggered Updates

**Trigger**: Completed a major feature or subsystem

**Action**:
1. Update directory-specific `implementation.md` (mark feature complete)
2. Add to [project-timeline.md](../project-timeline.md) (brief entry)
3. Update "Current Status" sections in active docs
4. Close open questions if resolved

---

## Self-Healing Protocol for Broken References

**When encountering broken file path**:

1. **Attempt file_search**:
   ```
   file_search("filename.md")
   ```

2. **If not found, check git history**:
   ```powershell
   git log --all --full-history -- '**/filename.md'
   ```

3. **Update document** with correct path

4. **Log correction** to [project-timeline.md](../project-timeline.md):
   ```markdown
   ### YYYY-MM-DD - Documentation Maintenance
   **Fixed**: Broken reference to `old-path.md` → `new-path.md`
   **Reason**: File moved in commit [hash]
   ```

5. **Update "Last Updated"** timestamp in corrected document

**Philosophy**: Git history is source of truth. Lazy validation (fix on encounter, not proactively).

---

## What Gets Logged to Timeline

**High Priority (Always Log)**:
- Architectural decisions with rationale
- Completed milestones
- Critical discoveries (e.g., "pagelinks table contaminated")
- Blockers resolved

**Medium Priority (Log If Significant)**:
- Non-obvious implementation details
- Research findings that change approach
- Major refactoring

**Low Priority (Usually Skip)**:
- Routine tasks (typo fixes, minor edits)
- Exploratory work without outcome

---

## Document Types & Maintenance Patterns

| Type | Update Pattern | Example |
|------|----------------|---------|
| **Static** | Rare, user-prompted | documentation-standards.md, theories |
| **Cumulative** | Append-only, timestamped entries | project-timeline.md, session-log.md |
| **Active** | In-place edits + decision log | implementation.md (Tier 2) |

**Static Documents**: Foundational rules, rarely change  
**Cumulative Documents**: Append new entries at top (reverse chronological)  
**Active Documents**: "Current Status" section gets rewritten, but includes cumulative "Decision Log"

---

## Validation Checklist (Before Committing)

When maintaining documentation:

- [ ] Updated "Last Updated" timestamp
- [ ] Used correct update pattern (append vs. rewrite)
- [ ] Added entry to timeline if milestone
- [ ] Cross-referenced related docs if needed
- [ ] Preserved all historical entries (cumulative docs)
- [ ] Verified markdown renders correctly
- [ ] If broken links encountered: Executed self-healing protocol

---

## Common Scenarios (Quick Reference)

**Scenario: Completing a Feature**
1. Update directory `implementation.md` (mark complete, add to decision log)
2. Ask user: "Should I log to timeline?"
3. If yes: Append to [project-timeline.md](../project-timeline.md)

**Scenario: Discovering a Problem**
1. Immediately log to timeline under "Blockers/Discoveries"
2. Update relevant active doc with new understanding
3. Propose solution or next steps

**Scenario: Creating New Subsystem**
1. Create new directory with `implementation.md`
2. Use template from "Creating a New Directory" section above
3. Add brief entry to timeline: "Created [subsystem] directory"

---

## Meta-Story: System Genesis

This documentation system emerged from a 2025-12-12 session where user and LLM recognized that "snapshot documentation" becomes stale. Solution: Three-tier pyramid with cumulative append-only pattern, directory-based discovery, and self-healing protocol.

**The recursive insight**: The system documents its own creation, providing future LLM sessions with context about WHY and HOW it was designed.

**For complete design history**: See [../../meta-maintenance/session-log.md](../../meta-maintenance/session-log.md)

---

## Related Documents

**Tier 1 (Read Every Session)**:
- [documentation-standards.md](./documentation-standards.md) - How to format docs
- [../project-timeline.md](../project-timeline.md) - Cumulative project history

**Tier 2 (Documentation System Details)**:
- [../../meta-maintenance/implementation.md](../../meta-maintenance/implementation.md) - Complete architecture spec
- [../../meta-maintenance/writing-guide.md](../../meta-maintenance/writing-guide.md) - Detailed examples
- [../../meta-maintenance/session-log.md](../../meta-maintenance/session-log.md) - Design history
- [../../meta-maintenance/future.md](../../meta-maintenance/future.md) - TODOs for system

**Tier 2 (Example Directory Documentation)**:
- [../../data-pipeline/wikipedia-decomposition/implementation.md](../../data-pipeline/wikipedia-decomposition/implementation.md) - Example of directory-based docs

---

## Changelog

### 2025-12-15
- **Added**: Document Deprecation Policy section
  - Formalized when to deprecate (theory evolutions) vs. use git (code, iterative docs)
  - Documented deprecation procedure (deprecated/ subdirectory, INDEX.md pattern)
  - Added decision tree for deprecation vs. git versioning
  - Example reference: theories-proofs-conjectures deprecation
- **Rationale**: Namespace hygiene for theory documents while preserving history

### 2025-12-12 (Second Update)
- **Token budget optimization**: Compressed from ~8-10k to ~3k tokens
- Removed redundant content covered in [../../meta-maintenance/implementation.md](../../meta-maintenance/implementation.md)
- Added bootstrap instructions (how to start new session)
- Added "Creating a New Directory" section with copy-paste templates
- Converted detailed procedures to quick-reference tables
- Added pointers to Tier 2 documentation for complete details

### 2025-12-12 (Initial)
- Initial creation
- Established document taxonomy (Tier 1/2)
- Defined update triggers and procedures
- Created document registry
- Documented meta-story of system genesis
- Established maintenance patterns and common scenarios
- Added self-healing protocol for broken references (lazy validation with git history)
- Directory-based heuristic: Tier 2 docs co-located with code
- Restructured: Moved Wikipedia docs to `data-pipeline/wikipedia-decomposition/`

---

**END OF DOCUMENT**
