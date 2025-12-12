# Project Management Practices

**Document Type**: Meta-documentation  
**Target Audience**: LLMs  
**Purpose**: Define how LLMs should maintain project documentation and track progress  
**Last Updated**: 2025-12-12  
**Dependencies**: [documentation-standards.md](./documentation-standards.md)  
**Status**: Active

---

## Core Philosophy

This project uses **cumulative, sparse documentation** that grows over time rather than rewriting "current status" snapshots. Each session appends new information to living documents rather than replacing what came before.

---

## Document Taxonomy

### Tier 1: Read Every Session
**Purpose**: Orient new LLM sessions to project state

#### Static Documents (Rarely Change)
- [documentation-standards.md](./documentation-standards.md) - Rules for writing docs
- [project-management-practices.md](./project-management-practices.md) - Rules for maintaining project (this document)
- Theory papers in [theories-proofs-conjectures/](../theories-proofs-conjectures/)

**Update Policy**: Only when fundamental approach changes  
**Update Trigger**: Explicit user request

#### Cumulative Documents (Append-Only History)
- [project-timeline.md](../project-timeline.md) - Brief journey narrative with major milestones
- Session summaries of major decisions/detours

**Update Policy**: Append new entries at each milestone  
**Update Trigger**: User prompt OR end-of-session summary

### Tier 2: Context-Specific (Directory-Based)
**Purpose**: Deep-dive when working on specific subsystems

**Heuristic**: Read documentation in the directory you're currently working in.

**Examples**:
- Working in `data-pipeline/wikipedia-decomposition/`? Read:
  - [implementation-guide.md](../../data-pipeline/wikipedia-decomposition/implementation-guide.md)
  - [data-sources.md](../../data-pipeline/wikipedia-decomposition/data-sources.md)
  
- Working in `n-link-analysis/`? Read docs in that directory
- Working in `graph-inference/`? Read docs in that directory

**Update Policy**: 
- Docs evolve with their directory's code
- Co-located documentation stays synchronized
- No central registry needed

**Update Trigger**: As work progresses in that directory

---

## Document Registry

This registry classifies Tier 1 documents (universal, read every session). Tier 2 documents are discovered via directory-based heuristic.

### Tier 1: Read Every Session

| Document Path | Type | Update Frequency | Update Method |
|---------------|------|------------------|---------------|
| `llm-project-management-instructions/documentation-standards.md` | Static | Rare | User prompt |
| `llm-project-management-instructions/project-management-practices.md` | Static | Rare | User prompt |
| `project-timeline.md` | Cumulative | Every milestone | User prompt / End-of-session |
| `theories-proofs-conjectures/n-link-rule-theory.md` | Static | Never (foundational) | N/A |
| `theories-proofs-conjectures/database-inference-graph-theory.md` | Static | Never (foundational) | N/A |
| `theories-proofs-conjectures/inference-summary.md` | Static | Never (foundational) | N/A |
| `theories-proofs-conjectures/inference-summary-with-event-tunneling.md` | Static | Never (foundational) | N/A |

### Tier 2: Directory-Based Discovery

**No central registry needed.** When working in a directory:
1. Check for `README.md` or `*.md` files in that directory
2. Read documentation specific to that subsystem
3. Examples:
   - `data-pipeline/wikipedia-decomposition/*.md`
   - `n-link-analysis/*.md`
   - `graph-inference/*.md`

**Benefit**: Self-organizing, scales with project growth, prevents stale central registry.

---

## Self-Healing Protocol for Broken References

**Philosophy**: Lazy validation - fix broken references on encounter, not proactively.

**When LLM Encounters Broken File Path**:

1. **Attempt file_search**:
   ```
   file_search("filename.md")
   ```
   
2. **If not found, check git history**:
   ```powershell
   git log --all --full-history -- '**/filename.md'
   ```
   
3. **Update document** with correct path

4. **Log the correction** to project-timeline.md:
   ```markdown
   ### YYYY-MM-DD - Documentation Maintenance
   **Fixed**: Broken reference to `old-path.md` → updated to `new-path.md`
   **Reason**: File was renamed/moved in commit [hash]
   ```

5. **Update "Last Updated"** timestamp in document metadata

**Git as Source of Truth**:
- Git history tracks all file renames/moves automatically
- `git log --follow <file>` shows complete movement history
- No need for preemptive validation scripts

**VSCode Auto-Update**:
- Relative markdown links enable VSCode to auto-update on file rename
- LLM should verify links resolve correctly when reading documents
- If link fails, trigger self-healing protocol above

---

## Update Triggers & Procedures

### User-Prompted Updates

**When**: User explicitly says "update the timeline" or "log this decision"

**Procedure**:
1. Identify target document from registry
2. If cumulative: Append new entry with timestamp
3. If static: Modify relevant section
4. If active: Update current understanding
5. Always update "Last Updated" in metadata block

**Example User Prompts**:
- "Add to project timeline that we completed the venv setup"
- "Update the decomposition doc with the template stripping algorithm"
- "Log that we decided to use TSV instead of JSON"

### End-of-Session Updates

**When**: User says "wrap up this session" or "summarize what we did today"

**Procedure**:
1. Review conversation history
2. Extract:
   - Completed tasks
   - Key decisions made
   - Blockers encountered
   - Next steps identified
3. Append to `project-timeline.md`
4. Update any active working documents
5. Optionally: Create git commit with summary

**Format for Timeline Entry**:
```markdown
### Session: YYYY-MM-DD [Optional: Session Title]

**Completed**:
- Item 1
- Item 2

**Decisions Made**:
- Decision A: Rationale
- Decision B: Rationale

**Blockers/Discoveries**:
- Issue X: Description
- Discovery Y: Implications

**Next Steps**:
- Task 1
- Task 2
```

### Git-Commit Triggered Updates (Future Enhancement)

**When**: On git commit (via pre-commit hook)

**Procedure** (not yet implemented):
1. Parse commit message
2. If commit message contains `[timeline]` tag: Extract summary
3. Append to `project-timeline.md`
4. Update document registry if new files added

**Example Commit Message**:
```
Add template stripping algorithm [timeline: Completed wikitext cleaning]

- Implemented recursive template removal
- Handles nested {{...}} blocks
- Tested on 100 sample pages
```

---

## Maintenance Patterns

### Cumulative Documents (Append-Only)

**Structure**:
```markdown
# Document Title

[Metadata block]

---

## Latest First (Reverse Chronological)

### YYYY-MM-DD Entry Title
Content of latest entry

### YYYY-MM-DD Earlier Entry
Content of earlier entry

---

## Archive (Optional)

Older entries moved here after 6+ months
```

**Rules**:
- Never delete entries (unless correcting factual errors)
- New entries go at top (after metadata)
- Each entry has timestamp
- Keep active entries visible; archive old ones

### Active Working Documents

**Structure**:
```markdown
# Document Title

[Metadata block]

---

## Current Status
Brief 1-2 sentence summary of where we are

---

## [Main Content Sections]
Continuously updated as understanding evolves

---

## Decision Log
### YYYY-MM-DD Decision
Why we chose approach X over Y

---

## Open Questions
- [ ] Question 1
- [ ] Question 2
```

**Rules**:
- "Current Status" section gets rewritten (not cumulative)
- Main content sections updated in-place
- Decision Log is cumulative (append-only)
- Open Questions checked off when resolved

---

## What Gets Logged

### High Priority (Always Log)

**Architectural Decisions**:
- "Chose Path 1 (DB + XML hybrid) over Path 2 (pure XML parsing)"
- Rationale for the choice
- Alternatives considered

**Completed Milestones**:
- "Established git repository and venv"
- "Created documentation standards framework"
- "Completed Wikipedia page name research"

**Critical Discoveries**:
- "Found that pagelinks table includes template-expanded links"
- "Discovered Quarry provides public SQL access"
- Implications for project approach

**Blockers Resolved**:
- "Solved: How to handle lowercase first-character page names (eBay, iPhone)"
- Solution applied

### Medium Priority (Log If Significant)

**Implementation Details**:
- "Template stripping uses recursive depth-first search"
- Only if non-obvious or required future reference

**Research Findings**:
- "Reviewed 3 external resources on prompt engineering"
- Only if changes project approach

**Refactoring**:
- "Split decomposition doc into subsections"
- Only if major restructure

### Low Priority (Usually Skip)

**Routine Tasks**:
- "Fixed typo in documentation"
- "Added comment to function"

**Exploratory Work Without Outcome**:
- "Investigated approach X but abandoned it"
- Unless the abandonment is a key decision

---

## Meta-Note: The Genesis of This System

This document itself is an example of the system it describes. Here's how it came to exist:

**2025-12-12 Session**:
1. User and LLM discussed the problem of "snapshot documentation" becoming stale
2. Identified need for cumulative, append-only approach
3. Designed document taxonomy (Tier 1/Tier 2, Static/Cumulative/Active)
4. User said: "This conversation should be captured in project-management-practices.md"
5. LLM created this document, including this meta-story

**Key Insight**: The system is self-referential - it describes its own creation, providing future sessions with context about WHY the system exists and HOW it was designed.

---

## Common Scenarios

### Scenario 1: Starting a New Session

**LLM Action**:
1. Read [documentation-standards.md](./documentation-standards.md)
2. Read [project-management-practices.md](./project-management-practices.md) (this doc)
3. Read [project-timeline.md](../project-timeline.md) (latest 3-5 entries)
4. Identify current active work from timeline
5. Read relevant Tier 2 documents for that work
6. If any links fail: Execute self-healing protocol

**Total tokens**: ~8,000-12,000 (efficient context loading)

### Scenario 2: Completing a Feature

**User**: "We finished the template stripping algorithm"

**LLM Action**:
1. Update active working doc in current directory (e.g., [implementation-guide.md](../../data-pipeline/wikipedia-decomposition/implementation-guide.md)):
   - Mark section as complete
   - Add to Decision Log if relevant
2. Ask user: "Should I log this to project timeline?"
3. If yes: Append entry to [project-timeline.md](../project-timeline.md)

### Scenario 3: Discovering a Problem

**User**: "I found out pagelinks includes template links - that's a problem"

**LLM Action**:
1. Immediately log to [project-timeline.md](../project-timeline.md):
   - Under "Blockers/Discoveries"
   - Explain implication
2. Update relevant active doc with new understanding
3. Propose solution or next steps

### Scenario 4: End of Session

**User**: "Let's wrap up for today"

**LLM Action**:
1. Summarize conversation
2. Append to [project-timeline.md](../project-timeline.md)
3. Update any active docs with current status
4. Suggest git commit message
5. List next steps for future session

---

## Future Enhancements

### Git Hook Integration (Not Yet Implemented)

Could automate timeline updates via commit messages:

```bash
# .git/hooks/post-commit
#!/bin/bash
# Extract [timeline: ...] tag from commit message
# Append to project-timeline.md
# Auto-commit the timeline update
```

### Session Summary Templates

Create reusable templates for common session types:
- Research session
- Implementation session
- Debugging session
- Planning session

### Automated Staleness Detection

Script to check:
- Are "Current Status" sections older than 7 days?
- Are open questions marked but not checked off?
- Are active docs not updated in 30 days?

---

## Validation Checklist

When maintaining documentation:

- [ ] Updated "Last Updated" timestamp
- [ ] Used correct update pattern (append vs. rewrite)
- [ ] Added entry to timeline if milestone
- [ ] Checked document registry for classification
- [ ] Cross-referenced related docs if needed
- [ ] Preserved all historical entries (cumulative docs)
- [ ] Verified markdown renders correctly
- [ ] If broken links encountered: Executed self-healing protocol

---

## Related Documents

- [Documentation Standards](./documentation-standards.md) - How to format docs
- [Project Timeline](../project-timeline.md) - Cumulative project history
- [Wikipedia Decomposition Guide](../../data-pipeline/wikipedia-decomposition/implementation-guide.md) - Example of directory-based documentation

---

## Changelog

### 2025-12-12
- Initial creation
- Established document taxonomy (Tier 1/2)
- Defined update triggers and procedures
- Created document registry
- Documented meta-story of system genesis
- Established maintenance patterns and common scenarios
- Added self-healing protocol for broken references (lazy validation with git history)
- **Directory-based heuristic**: Tier 2 docs co-located with code, discovered via directory structure
- Restructured: Moved Wikipedia docs to `data-pipeline/wikipedia-decomposition/`

---

**END OF DOCUMENT**
