# Documentation System - Future Enhancements

**Document Type**: TODO List  
**Target Audience**: LLMs + Developers  
**Purpose**: Track planned improvements to the documentation system  
**Last Updated**: 2025-12-12  
**Dependencies**: [project-management-practices.md](../llm-facing-documentation/llm-project-management-instructions/project-management-practices.md)  
**Status**: Active

---

## High Priority

### Git Hook Automation
- [ ] Implement post-commit hook to auto-append to session-logs
- [ ] Parse commit messages for `[log: ...]` tag
- [ ] Determine which directory's session-log.md to update (based on changed files)
- [ ] Handle commits that touch multiple subsystems
- [ ] Test on Windows (PowerShell) and Unix (bash)

**Rationale**: Reduce manual documentation burden, make git commits the primary documentation input

**Open Questions**:
- What if a commit touches multiple directories? Append to multiple session-logs?
- Should Tier 1 timeline also auto-update from git commits with `[timeline: ...]` tag?
- How to handle merge commits vs feature commits?

---

### CLI Tool for Documentation Validation
- [ ] Build `doc-check` script to validate documentation structure
- [ ] Check all markdown links resolve correctly
- [ ] Verify metadata blocks present in all docs
- [ ] Detect stale "Last Updated" timestamps (>30 days with recent code changes)
- [ ] Flag missing standard files (session-log.md, future.md in Tier 2 directories)

**Rationale**: Proactive health checks without manual validation overhead

---

### Session Summary Generator
- [ ] Experiment with LLM-generated session summaries
- [ ] Tool to analyze git diff + commit messages → generate session-log entry
- [ ] Compare auto-generated vs manual summaries for quality
- [ ] Determine if this saves time or creates noise

**Rationale**: Further reduce documentation burden if quality is acceptable

---

## Medium Priority

### Documentation Health Dashboard
- [ ] Script to generate metrics:
  - Total docs, by tier
  - Average "Last Updated" age
  - Broken link count
  - Session-log entry count per directory
- [ ] Visualize doc coverage: which directories lack session-logs?

**Rationale**: Visibility into documentation quality over time

---

### Session Templates
- [ ] Create templates for common session types:
  - Research session (discoveries, external resources)
  - Implementation session (progress, blockers)
  - Debugging session (tried X, failed, did Y instead)
  - Planning session (design alternatives, decision rationale)
- [ ] Test if templates improve consistency

**Rationale**: Lower barrier to documentation, ensure key info captured

---

### "New Project Setup" Script
- [ ] After "living in" this system for 2-4 weeks, canonicalize it
- [ ] Create CLI: `new-project --with-doc-system`
- [ ] Auto-generate Tier 1 structure + templates
- [ ] Include pre-commit hook templates

**Rationale**: Reuse this system for future projects

---

## Low Priority (Experiment First)

### Automated Staleness Detection
- [ ] Script to check:
  - "Current Status" sections older than 7 days?
  - Open questions marked but never checked off?
  - Active docs not updated in 30+ days despite code changes?
- [ ] Generate report: "These docs may be stale"

**Rationale**: Helpful but not critical - system designed to avoid staleness naturally

---

### Cross-Reference Graph
- [ ] Parse all markdown links across docs
- [ ] Build graph of doc dependencies
- [ ] Detect orphaned docs (no inbound links)
- [ ] Find circular dependencies

**Rationale**: Interesting visualization, unclear if actionable

---

### LLM Context Optimizer
- [ ] Tool to analyze which docs are most frequently read together
- [ ] Suggest consolidation or splitting based on access patterns
- [ ] Measure token efficiency over time

**Rationale**: Optimize for real usage patterns, not theoretical

---

## Research Questions

### Does This System Scale?
- [ ] After 6 months, measure:
  - Average session startup token count (target: <20k)
  - Time to find relevant context (target: <2 minutes)
  - Documentation maintenance burden (target: <10% of dev time)
- [ ] Identify pain points that emerged from "living in" the system

---

### Do We Need Tier 4?
- [ ] After building 2-3 complex subsystems, evaluate:
  - Did we naturally create deeper nesting?
  - Was it necessary or could code comments suffice?
  - Does Tier 3 ever become unwieldy?

**Current hypothesis**: Tier 3 is sufficient, deeper = use code comments

---

### Git Commit Message Quality
- [ ] Analyze commit message quality after 1 month
- [ ] Are messages detailed enough for auto-documentation?
- [ ] Do we need commit message templates?

---

## Rejected Ideas (And Why)

### Central Document Index
**Rejected**: Defeats the purpose of directory-based discovery. Would go stale.

### Automated Doc Generation from Code
**Rejected**: Code comments already serve this purpose. Duplication without value.

### Notion/Confluence Integration
**Rejected**: Want docs in git, version-controlled, searchable with grep. Markdown is sufficient.

### Real-Time Doc Sync
**Rejected**: Cumulative append-only pattern already handles this. No need for live collaboration features.

---

## Completed (Moved from Future to Archive)

(When items from above are completed, move them here with completion date)

---

**Last Review**: 2025-12-12

**Next Review**: After 2-4 weeks of using the system

---

**END OF DOCUMENT**
