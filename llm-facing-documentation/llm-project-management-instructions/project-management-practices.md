# Project Management Practices

**Document Type**: Meta-documentation  
**Target Audience**: LLMs  
**Purpose**: How LLMs should maintain project documentation, create new directories, and track progress  
**Last Updated**: 2025-12-12  
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
