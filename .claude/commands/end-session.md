---
description: Execute end-of-session protocol to wrap up and document work session
argument-hint: [optional-session-notes]
allowed-tools: Read, Edit, Bash(git *)
---

# End-of-Session Protocol

Execute the systematic end-of-session protocol for this project.

## Instructions

Follow the 7-step procedure documented in [llm-facing-documentation/end-of-session-protocol.md](llm-facing-documentation/end-of-session-protocol.md):

1. **Session Summary**: Extract what was accomplished, decisions made, discoveries, and blockers
2. **Meta-Update Check**: If system docs were modified, load and update meta-maintenance context
3. **Dependency Check**: Verify consistency with dependent documents
4. **Project Timeline Update**: Append entry to project-timeline.md (if High/Medium priority)
5. **Directory-Specific Documentation**: Update session-log.md or implementation.md as needed
6. **Git Status Check**: Review uncommitted changes
7. **Final Checklist**: Validate all steps completed

## Additional Session Notes

$ARGUMENTS

## Current Git Status

!`git status --short`

## Recent Commits

!`git log --oneline -3`

---

Please execute the end-of-session protocol now, following all 7 steps systematically.
