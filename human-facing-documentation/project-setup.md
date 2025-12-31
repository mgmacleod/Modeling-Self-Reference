# Self Reference Modeling Project Setup

**Document Type**: Setup Guide  
**Target Audience**: New human collaborators/researchers  
**Purpose**: Complete environment configuration for reproducible work on this project  
**Last Updated**: 2025-12-30  
**Status**: Active

---

## Overview

This project applies formal graph theory to self-referential systems (Wikipedia, databases, code, documentation). The project structure itself is designed using these principles - documentation as a self-referential graph navigable via multi-rule tunneling.

---

## Prerequisites

- **VS Code** with GitHub Copilot extension
- **Python 3.13+** (for data pipeline work)
- **Git** for version control
- Basic understanding of graph theory (helpful but not required)

---

## Initial Setup

### Quick Start (Automated)

**For LLM-assisted setup**: Open [initialization.md](../initialization.md) in GitHub Copilot Chat and say "execute these initialization steps"

The LLM will:
1. Create virtual environment
2. Activate environment
3. Install dependencies from requirements.txt
4. Verify installation
5. Guide you to next steps

**Result**: Fully configured Python environment ready for work

---

### Manual Setup (Step-by-Step)

See [initialization.md](../initialization.md) for detailed platform-specific commands.

**Summary**:
1. Create virtual environment: `python -m venv .venv`
2. Activate environment: `.venv\Scripts\Activate.ps1` (Windows) or `source .venv/bin/activate` (macOS/Linux)
3. Install dependencies: `pip install -r requirements.txt`

**Core dependencies**:
- mwparserfromhell (Wikipedia parsing)
- mwxml (MediaWiki XML processing)
- requests (HTTP client)

---

### 3. VS Code Configuration

**Workspace file included**: Open `self-reference-modeling.code-workspace`

The workspace automatically configures:
- Python interpreter path (`.venv/Scripts/python.exe` or `.venv/bin/python`)
- System prompts for LLM navigation (`.vscode/settings.json`)
- Recommended extensions (Python, Pylance, Jupyter, Markdown)
- File exclusions and formatting rules

**No manual configuration needed** - workspace settings are committed to repository

---

## Understanding the Project Structure

### Documentation Hierarchy

```
llm-facing-documentation/           # LLM-optimized docs (machine-first)
├── README.md                       # Quick start for LLMs
├── project-timeline.md             # Cumulative history (append-only)
├── contracts/                       # Theory ↔ experiment ↔ evidence bindings (explicit contracts)
│   ├── README.md
│   └── contract-registry.md
├── llm-project-management-instructions/
│   ├── documentation-standards.md  # How to write docs
│   └── project-management-practices.md  # How to maintain project
└── theories-proofs-conjectures/    # Mathematical foundations
    ├── INDEX.md                    # Load this for theory overview
    ├── unified-inference-theory.md # Primary theory document
    └── deprecated/                 # Historical theory versions

human-facing-documentation/         # Human-optimized docs (you are here)
├── system-prompts.md               # VS Code configuration
├── context-management-guide.md     # How LLM context works
└── project-setup.md                # This file

data-pipeline/                      # Data extraction/processing
meta-maintenance/                   # Documentation system details
```

### Key Concept: Tier System

Documentation is organized in 3 tiers by loading frequency:

- **Tier 1** (~12k tokens): Load every session (universal orientation)
- **Tier 2** (~20k tokens): Load when working in specific directory
- **Tier 3** (unlimited): Load only when debugging specific issues

See `llm-facing-documentation/llm-project-management-instructions/project-management-practices.md` for details.

---

## First Session Workflow

### 1. Bootstrap the LLM

In GitHub Copilot chat:

1. **Paperclip attach**: `llm-facing-documentation/` folder
2. **Let LLM read**: 
   - "Please read llm-facing-documentation/README.md"
   - "Please read the latest 3-5 entries from project-timeline.md"
3. **Orient**: "What is the current focus of this project?"

### 2. Work Session

- Keep relevant files open (but not too many - see context-management-guide.md)
- Follow documentation standards for any new docs
- Let LLM suggest updates to timeline for major milestones

### 3. End Session

"Execute end-of-session protocol"

LLM will (if system prompts configured):
1. Load management documentation
2. Update project-timeline.md with session summary
3. Note any architectural decisions or discoveries

---

## Working with Theory Documents

### To understand the mathematical foundations:

1. Read `llm-facing-documentation/theories-proofs-conjectures/INDEX.md`
2. Start with `unified-inference-theory.md` (comprehensive overview)
3. Dive into specific theory docs as needed:
   - `n-link-rule-theory.md` - Foundational theorems
   - `database-inference-graph-theory.md` - Database applications

### Important:
- **Never load** files in `deprecated/` subdirectories
- They're preserved for history but superseded by current versions
- INDEX.md in each directory guides you to active documents

**Contract layer (recommended)**:
- When linking theory claims to experiments and evidence (especially empirical investigations), record the linkage in:
   - `llm-facing-documentation/contracts/contract-registry.md`
- This is designed to avoid “stealth edits” to theory documents by keeping status/linkage updates in an explicit, additive registry.

---

## Working on Implementation

### Data Pipeline Work

```powershell
cd data-pipeline/wikipedia-decomposition/
```

1. Read `implementation.md` in that directory (Tier 2 context)
2. Check `data-sources.md` for external resources
3. Work on code, following documented patterns

### Creating New Directories

When starting a new subsystem:
1. Create directory with descriptive name
2. Add `implementation.md` (required)
3. Optional: `data-sources.md`, `session-log.md`, `future.md`
4. Log creation to project-timeline.md

Template in `project-management-practices.md`.

---

## Git Workflow

### Standard Practice

```powershell
# Make changes
git add .
git commit -m "Descriptive message"
git push
```

### What to Commit

**Always commit**:
- Code changes
- Documentation updates
- Configuration changes

**Usually commit**:
- Project timeline updates (cumulative)
- New theory documents

**Rarely commit**:
- Large data files (use .gitignore)
- Temporary debugging artifacts

### Commit Messages

Follow conventional commits:
```
feat: Add Wikipedia extraction pipeline
fix: Correct basin partition algorithm
docs: Update theory document with event tunneling
chore: Optimize Tier 1 documentation token budget
```

---

## Troubleshooting

### "LLM doesn't remember early session instructions"
→ See context-management-guide.md. This is expected behavior.
→ Use system prompts for persistent instructions.

### "Documentation seems contradictory"
→ Check if you're reading deprecated documents.
→ Always start with INDEX.md in each directory.

### "Not sure which documents to load"
→ Follow the tier system in project-management-practices.md.
→ Tier 1 always, Tier 2 for active directory, Tier 3 rarely.

### "LLM behavior differs from colleague's"
→ Verify identical system prompts configuration.
→ Check active files in editor (affects context).

---

## Getting Help

1. **Check documentation first**: 
   - LLM-facing: `llm-facing-documentation/README.md`
   - Human-facing: This directory

2. **Ask the LLM**: 
   - "What does the project timeline say about [topic]?"
   - "How should I document [thing] according to standards?"

3. **Review meta-cognitive-insights.md**: Explains the theoretical foundations of how this project is structured

---

## Next Steps After Setup

1. Read `meta-cognitive-insights.md` to understand the self-referential nature of this project
2. Review latest project-timeline.md entries to understand current focus
3. Choose a work area (theory, data pipeline, documentation)
4. Start a session with proper LLM bootstrap

---

## Contributing

When adding features or documentation:
1. Follow documentation-standards.md (for writing style)
2. Update project-timeline.md (for significant milestones)
3. Consider deprecation policy (in project-management-practices.md)
4. Test that LLM can navigate your additions

The goal: Documentation that supports efficient multi-rule tunneling by LLM inference engines.

---
