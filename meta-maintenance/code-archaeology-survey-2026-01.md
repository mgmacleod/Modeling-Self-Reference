# Code Archaeology Survey - January 2026

**Document Type**: Reference
**Target Audience**: LLMs + Developers
**Purpose**: Inventory of scripts, conformance assessment, and cleanup recommendations
**Last Updated**: 2026-01-03
**Dependencies**: [../llm-facing-documentation/llm-project-management-instructions/documentation-standards.md](../llm-facing-documentation/llm-project-management-instructions/documentation-standards.md)
**Status**: Active

---

## Executive Summary

The codebase has **~130 Python scripts** and **~10 bash scripts** spread across several directories. While there's good documentation for core analysis scripts, about **40% of scripts in n-link-analysis are undocumented** in `scripts-reference.md`. Several organizational patterns need attention.

---

## Script Location Inventory

| Directory | Python | Bash | Notes |
|-----------|--------|------|-------|
| `n-link-analysis/scripts/` | 42 | 2 | Main analysis scripts |
| `n-link-analysis/scripts/tunneling/` | 16 | 0 | Tunneling pipeline (well-documented) |
| `n-link-analysis/scripts/_core/` | 6 | 0 | Shared engine modules |
| `n-link-analysis/scripts/temporal/` | 1 | 0 | Single fetch script |
| `n-link-analysis/scripts/semantic/` | 1 | 0 | Single fetch script |
| `n-link-analysis/viz/` | 10 | 2 | Visualization dashboards |
| `n-link-analysis/viz/tunneling/` | 4 | 0 | Tunneling viz tools |
| `n-link-analysis/viz/shared/` | 4 | 0 | Shared components |
| `data-pipeline/wikipedia-decomposition/scripts/` | 9 | 4 | Pipeline scripts (well-documented) |
| `data-pipeline/.../deprecated/` | 2 | 0 | Properly deprecated |
| `nlink_api/` | 27 | 0 | API package (well-structured) |
| `tools/` | 1 | 0 | git_stats.py |
| `docker/` | 0 | 1 | entrypoint.sh |

---

## Conformance Issues

### 1. Naming Convention Violations

**Standard**: Kebab-case for scripts (`my-script.py`), snake_case for modules

**Violations**:
- `tools/git_stats.py` → should be `git-stats.py` (it's a CLI script, not a module)

**Acceptable Exceptions** (importable modules):
- `n-link-analysis/scripts/data_loader.py`
- `n-link-analysis/scripts/_core/*.py`
- `n-link-analysis/viz/api_client.py`

### 2. Undocumented Scripts

**27 scripts in `n-link-analysis/scripts/`** exist but are not in `scripts-reference.md`:

| Category | Scripts | Recommendation |
|----------|---------|----------------|
| **Exploratory/WIP** | `analyze-basin-entry-breadth.py`, `analyze-depth-distributions.py`, `analyze-halt-probability.py`, `analyze-phase-transition-n3-n10.py`, `explore-depth-structure-large-scale.py`, `interactive-depth-explorer.py`, `interactive-depth-explorer-enhanced.py` | Document or deprecate |
| **Infrastructure/utility** | `upload-to-huggingface.py`, `validate-hf-dataset.py`, `validate-data-dependencies.py`, `organize-consolidated-data.py` | Document in scripts-reference.md |
| **Batch runners** | `batch-render-basin-pointclouds.py`, `batch-render-tributary-trees.py`, `run-analysis-harness.py`, `run-single-cycle-analysis.py` | Document as orchestration scripts |
| **Analysis scripts** | `compare-across-n.py`, `compare-cycle-evolution.py`, `correlate-edit-basin-stability.py`, `analyze-cycle-link-profiles.py`, `analyze-path-characteristics.py`, `analyze-universal-cycles.py`, `answer-wh-cycle-attachment.py` | Document or assess if still needed |
| **Compute scripts** | `compute-hyperstructure-coverage.py`, `compute-hyperstructure-size.py` | Document |
| **Rendering** | `render-reports-to-html.py`, `visualize-mechanism-comparison.py` | Document |

### 3. Orphaned Subdirectories

| Directory | Contents | Issue |
|-----------|----------|-------|
| `n-link-analysis/scripts/temporal/` | `fetch-edit-history.py` | Single script in isolated subdir |
| `n-link-analysis/scripts/semantic/` | `fetch-page-categories.py` | Single script in isolated subdir |

These were likely created for specific investigations but have only one script each.

### 4. Archive/Backup Files

Location: `n-link-analysis/viz/_archive/`

| File | Size | Status |
|------|------|--------|
| `dash-cross-n-comparison.py.bak` | 19KB | Old version |
| `dash-multiplex-explorer.py.bak` | 27KB | Old version |
| `path-tracer-tool.py.bak` | 24KB | Old version |
| `tunneling-dashboard.py.bak` | 26KB | Old version |

These are from the visualization consolidation effort (documented in `VIZ-CONSOLIDATION-PLAN.md`).

### 5. Documentation Gaps

| Directory | Has implementation.md | Has scripts reference | Issue |
|-----------|----------------------|----------------------|-------|
| `n-link-analysis/` | Yes | Yes (partial) | 27 undocumented scripts |
| `n-link-analysis/viz/` | Yes (README.md) | No | No script reference doc |
| `n-link-analysis/scripts/tunneling/` | Yes (README.md) | Yes | Good |
| `data-pipeline/` | No | N/A | Only has INDEX.md |
| `tools/` | Yes (README.md) | N/A | Good |

---

## Cleanup Recommendations

### Priority 1: Documentation Updates (Low effort, high value)

1. **Update `scripts-reference.md`** to document the 27 undocumented scripts, or explicitly mark placeholder/WIP scripts as such
2. **Create `viz/scripts-reference.md`** documenting visualization scripts
3. **Update `data-pipeline/INDEX.md`** to note it's no longer "Planning" phase (status says "Planning" but it's complete)

### Priority 2: Consolidation (Medium effort)

1. **Merge temporal/ and semantic/ into scripts/**:
   - Move `fetch-edit-history.py` → `n-link-analysis/scripts/` (rename to `fetch-temporal-edit-history.py` if needed)
   - Move `fetch-page-categories.py` → `n-link-analysis/scripts/` (rename to `fetch-semantic-categories.py` if needed)
   - Delete empty subdirectories

2. **Rename `tools/git_stats.py`** → `tools/git-stats.py` (kebab-case for CLI scripts)

### Priority 3: Archive Management (Low effort)

1. **Keep `viz/_archive/`** as-is - the consolidation plan is active and .bak files provide fallback
2. **After consolidation completes**: Delete _archive/ or move to git-only history

### Priority 4: Future Consideration

1. **Assess exploratory scripts** (`analyze-*.py`, `explore-*.py`, `interactive-*.py`):
   - If used regularly → document
   - If one-off exploration → consider deprecating to `scripts/deprecated/`
   - If still WIP → add TODO comments

---

## Project Standards Compliance Summary

| Aspect | Status | Notes |
|--------|--------|-------|
| Kebab-case scripts | 98% | One violation: `git_stats.py` |
| Snake_case modules | 100% | All importable modules correct |
| Documentation headers | Variable | Main docs excellent, some scripts lack docstrings |
| Deprecated directory | Good | `data-pipeline/.../deprecated/` properly used |
| INDEX.md pattern | Good | Used where appropriate |
| implementation.md | Partial | Missing for data-pipeline root |

---

## Action Items Checklist

### Quick Wins
- [ ] Rename `tools/git_stats.py` → `tools/git-stats.py`
- [ ] Update `data-pipeline/INDEX.md` status from "Planning" to "Complete"

### Documentation Sprint
- [ ] Audit and document the 27 undocumented scripts in `scripts-reference.md`
- [ ] Create `n-link-analysis/viz/scripts-reference.md`

### Structural Cleanup
- [ ] Consolidate `temporal/` and `semantic/` orphan directories
- [ ] Assess whether exploratory scripts should be deprecated

### Post-Consolidation
- [ ] Delete `viz/_archive/` after consolidation effort completes

---

## Changelog

### 2026-01-03
- Initial survey conducted
- Identified 27 undocumented scripts
- Documented naming violations and orphaned directories
- Created prioritized cleanup recommendations

---

**END OF DOCUMENT**
