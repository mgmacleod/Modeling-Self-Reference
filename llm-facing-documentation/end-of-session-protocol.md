# End-of-Session Protocol

**Tier**: 1  
**Purpose**: Systematic procedure for closing work sessions and maintaining documentation consistency  
**Last Updated**: 2025-12-30  
**Status**: Active

---

## When to Execute This Protocol

User says any of:
- "Execute end-of-session protocol"
- "Wrap up session"
- "Summarize session"
- "End of session"
- "Close session"

---

## Step 1: Session Summary

**Extract from conversation**:
- What was accomplished (completed work)
- What decisions were made (with rationale)
- What discoveries were made (non-obvious findings)
- What blockers were encountered (and resolution status)
- What architectural changes occurred (system-level impacts)

**Format**: Concise bullet points, not prose.

---

## Step 2: Meta-Update Check (Conditional)

**Did you modify any of these files this session?**
- `llm-facing-documentation/llm-project-management-instructions/documentation-standards.md`
- `llm-facing-documentation/llm-project-management-instructions/project-management-practices.md`
- `llm-facing-documentation/README.md`
- `llm-facing-documentation/end-of-session-protocol.md` (this file)
- `llm-facing-documentation/contracts/contract-registry.md`
- `llm-facing-documentation/contracts/README.md`

**If YES → Load meta-maintenance context**:

1. **Request these files** (if not already in context):
   - `meta-maintenance/implementation.md`
   - `llm-facing-documentation/llm-project-management-instructions/project-management-practices.md`
   - `llm-facing-documentation/llm-project-management-instructions/documentation-standards.md`

2. **Check consistency**:
   - Do your changes contradict documented system architecture?
   - Do they extend patterns that need to be documented?
   - Are new procedures captured in implementation.md?

3. **Update meta-maintenance** (if needed):
   - Add to `meta-maintenance/session-log.md` (append to top)
   - Update `meta-maintenance/implementation.md` (if architecture changed)
   - Update `meta-maintenance/future.md` (if TODOs completed or added)

**If NO → Skip to Step 3**

---

## Step 2.5: Contracts Check (Conditional)

**Did this session produce or change any empirical evidence, or create a new investigation stream?**

Examples:
- New/updated `n-link-analysis/empirical-investigations/*.md`
- New analysis outputs under `data/**/analysis/` or `**/processed/analysis/`
- A theory claim was evaluated, supported, refuted, or marked inconclusive
- An external artifact (third-party) was cited as part of a theory/evidence chain

**If YES**:
- Update `llm-facing-documentation/contracts/contract-registry.md`:
   - add a new `*-C-*` entry, or update status of an existing one
   - ensure experiments + evidence links are recorded
   - if applicable, ensure external artifact is tracked under an `EXT-*` entry with author attribution and permission/license status

**If NO**: proceed to Step 3

---

## Step 3: Dependency Check

**For each file you modified**:

1. **Check metadata Dependencies field**
   - Example: `**Dependencies**: [implementation.md](../../meta-maintenance/implementation.md)`

2. **Read listed dependencies**
   - Verify your changes don't create inconsistency
   - Update dependencies if they reference your modified file

3. **Follow dependency chain**
   - If dependency has dependencies, check those too
   - Maximum depth: 2 levels (prevents infinite loops)

---

## Step 4: Project Timeline Update

**Request file** (if not in context):
- `llm-facing-documentation/project-timeline.md`

**Determine priority level**:

| Priority | When to Log | Example |
|----------|-------------|---------|
| **High** | Always log | Architectural decisions, completed milestones, critical discoveries, blockers resolved |
| **Medium** | Log if significant | Non-obvious implementation details, research findings that changed approach, major refactoring |
| **Low** | Usually skip | Routine tasks (typo fixes, minor edits), exploratory work without outcome |

**If High or Medium → Append new entry**:

```markdown
### Session: YYYY-MM-DD - [Brief Title]

**Completed**:
- Bullet list of what was accomplished
- Include file names and key changes

**Decisions Made**:
- Decision: Rationale
- Use table format if multiple decisions

**Discoveries**:
- Non-obvious findings
- Things that surprised you or weren't intuitive

**Validation**:
- How you verified changes work
- Tests run, checks performed

**Architecture Impact**:
- Changes to system structure or patterns
- New capabilities or constraints

**Next Steps**:
- Logical continuation of work
- Open questions or blockers

---
```

**Update metadata timestamp**:
```markdown
**Last Updated**: YYYY-MM-DD
```

---

## Step 5: Directory-Specific Documentation

**If you worked in a specific directory**:

**Check for directory documentation**:
- Does `<directory>/session-log.md` exist?
- Does `<directory>/implementation.md` exist?

**If session-log.md exists → Append entry**:
```markdown
### YYYY-MM-DD - [Brief Title]
[What you tried, what worked, what didn't]
Commit: [git hash if committed]
```

**If implementation.md exists and architecture changed**:
- Update relevant sections
- Add note about what changed and why
- Update "Last Updated" timestamp

**If you created new files → Update future.md** (if it exists):
- Mark completed tasks as done
- Add new tasks if discovered

---

## Step 6: Git Status Check

**Run git status**:
```powershell
git status
```

**Review changes**:
- Are all files you expect to change listed?
- Any unexpected changes?
- Files that should be committed?

**Prompt user**:
"Git status shows changes to [list files]. Ready to commit or need more review?"

---

## Step 7: Final Checklist

Before ending session, verify:

- [ ] Project timeline updated (if High/Medium priority work)
- [ ] Meta-maintenance updated (if you modified system docs)
- [ ] Dependencies checked (for all modified files)
- [ ] Directory session-log updated (if working in specific directory)
- [ ] Git status reviewed
- [ ] User aware of any uncommitted changes

---

## Common Scenarios

### Scenario: Simple Implementation Work
**Example**: Added function to data pipeline

**Steps needed**:
- Step 1: Session summary ✓
- Step 2: Meta-update check (NO) → Skip
- Step 3: Dependency check ✓
- Step 4: Timeline update (probably Medium priority) ✓
- Step 5: Update directory session-log.md ✓
- Step 6: Git status ✓
- Step 7: Checklist ✓

### Scenario: Documentation System Changes
**Example**: Added deprecation policy

**Steps needed**:
- Step 1: Session summary ✓
- Step 2: Meta-update check (YES) → **Load meta-maintenance** ✓
- Step 3: Dependency check ✓
- Step 4: Timeline update (HIGH priority) ✓
- Step 5: Update meta-maintenance/session-log.md ✓
- Step 6: Git status ✓
- Step 7: Checklist ✓

### Scenario: Exploratory Research
**Example**: Reading Wikipedia API docs, no code changes

**Steps needed**:
- Step 1: Session summary ✓
- Step 2: Meta-update check (NO) → Skip
- Step 3: Dependency check (no files modified) → Skip
- Step 4: Timeline update (LOW priority, skip) → Skip
- Step 5: Directory update (maybe add to data-sources.md) ✓
- Step 6: Git status (no changes expected) ✓
- Step 7: Checklist ✓

---

## Error Recovery

**If you realize you missed a step**:
1. Note it in timeline entry: "**Note**: Discovered missing update during next session"
2. Execute missed step immediately
3. Don't try to retroactively edit history - append corrections

**If dependency chain is too complex**:
1. Document the complexity in timeline
2. Flag for future automation: "Dependency chain: A → B → C → D (needs tooling)"
3. Update at least direct dependencies (depth 1)

---

## Token Budget Considerations

**Estimated token costs**:
- Normal session: ~2-3k tokens (timeline update, directory log)
- Meta session: ~8-12k tokens (add meta-maintenance context)
- Complex session: ~5-8k tokens (multiple directory updates)

**Optimization**:
- Request only files you need to update
- Don't re-read files already in context
- Use git status to identify changed files (avoids guessing)

---

## Notes for System Prompt Integration

This protocol should be triggered by VS Code system prompt when user says end-of-session keywords.

**System prompt should**:
1. Trigger this protocol
2. Request this file if not in context
3. Request project-management-practices.md and documentation-standards.md if not in context
4. Follow steps sequentially

**Do NOT**:
- Try to guess what files need updating
- Skip dependency checks
- Assume meta-maintenance doesn't need updating

---
