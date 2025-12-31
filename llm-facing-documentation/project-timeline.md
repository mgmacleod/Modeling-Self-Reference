# Project Timeline

**Document Type**: Cumulative history  
**Target Audience**: LLMs  
**Purpose**: Chronological record of project evolution, decisions, and discoveries  
**Last Updated**: 2025-12-30  
**Status**: Active (append-only)

---

## How to Use This Document

**For LLMs**: Read the latest 3-5 entries to understand current project state. Scroll to relevant dates when investigating specific decisions.

**Update Policy**: Append new entries at top (reverse chronological order). Never delete entries.

---

## Timeline Entries

### Session: 2025-12-30 - Contracts Layer for Theory↔Experiment↔Evidence + Empirical N-Link Analysis

**Completed**:
- Built N-link empirical analysis scripts (trace, sampling, preimages, basin mapping) and documented investigation streams under `n-link-analysis/empirical-investigations/`.
- Introduced a dedicated contracts layer under `llm-facing-documentation/contracts/`:
  - Contract registry binds canonical theory ↔ experiments ↔ evidence without rewriting theory.
  - Added external artifact tracking (`EXT-*`) and a citation/integration contract for `sqsd.html` (Ryan Querin).
- Updated onboarding + session protocols to reflect the contracts layer and empirical workflow bootstrap.

**Decisions Made**:
| Decision | Rationale |
|----------|-----------|
| Canonical theory docs are additive/append-only for routine evolution | Avoid stealth edits; preserve lineage |
| Major theory rewrites use deprecation, not silent modification | Namespace hygiene + historical integrity |
| Evidence/status updates live in contracts + investigation streams | Keeps theory stable while enabling fast empirics |

**Discoveries**:
- Under fixed-$N$ traversal, Wikipedia exhibits strong cycle dominance at $N=5$ with a heavy-tailed basin size distribution (documented in investigation stream).

**Validation**:
- Empirical workflows are reproducible via the documented scripts and investigation runbooks.

**Architecture Impact**:
- Documentation system now includes an explicit cross-cutting contract registry (exception to “no central registry” for directory-local discovery).

**Next Steps**:
- Run Phase 1 across multiple $N$ values and promote results into additional investigation docs + updated contract statuses.

---

### Session: 2025-12-29 - N-Link Sequence Pipeline Complete

**Completed**:
- Prose-only link extraction (`parse-xml-prose-links.py`)
  - Strips templates, tables, refs, comments from wikitext
  - Output: `links_prose.parquet` (214.2M prose links with position, 1.67 GB)
  - Processing: 53 minutes over 69 XML files

- N-Link sequence builder (`build-nlink-sequences-v3.py`)
  - Vectorized Pandas approach (1000x faster than iterrows, DuckDB-compatible)
  - Resolves titles → page IDs while preserving order
  - Output: `nlink_sequences.parquet` (17.97M pages, 206.3M ordered links, 686 MB)
  - Processing: ~5 minutes for full resolution + sort + groupby

- Deprecated slower/failed implementations
  - Moved to `scripts/deprecated/` with explanations
  - `build-nlink-sequences.py`: DuckDB OOM on list() aggregation
  - `build-nlink-sequences-v2.py`: Too slow with Pandas iterrows()

- Updated documentation with Quick Start
  - INDEX.md: Added run order, output summary, script categorization
  - implementation-guide.md: Added prerequisites, step-by-step execution, file specs

**Impact**:
- **Data pipeline complete**: All extraction work finished. Future sessions do analysis only (reads parquet)
- **N-Link ready**: Can now compute f_N(page_id) = link_sequence[N-1] for basin partition experiments
- **Pattern documented**: Vectorized approach + streaming for large datasets

**Key Discovery**:
- Vectorized Pandas on 200M+ rows beats row-by-row iteration and DuckDB aggregation by orders of magnitude

---

### Session: 2025-12-15 (Evening) - Tier System Clarification & INDEX Standardization

**Completed**:
- Clarified tier system as context depth (functional), not directory nesting (structural)
  - Tier 0: .vscode/settings.json (system prompts, experimental apparatus)
  - Tier 1: Universal (every session)
  - Tier 2: Contextual (working in functional area)
  - Tier 3: Reference (deep-dive, as-needed)

- Corrected tier classifications across all documents
  - Theory documents reclassified as Tier 2 (load all when working on theory)
  - data-sources.md files reclassified as Tier 3 (historical reproducibility)
  - end-of-session-protocol.md reclassified as Tier 2 (triggered by system prompt)

- Updated meta-maintenance/implementation.md
  - Added Tier 0 definition (system prompts outside hierarchy)
  - Clarified functional vs structural tier semantics
  - Updated tier descriptions with "context depth" principle

- Standardized all INDEX.md files with relay node pattern
  - meta-maintenance/: Core (implementation.md, session-log.md) vs Reference (writing-guide.md, data-sources.md, future.md)
  - theories-proofs-conjectures/: All Tier 2 (load all when working on theory)
  - llm-project-management-instructions/: All Tier 1 (always loaded)
  - data-pipeline/wikipedia-decomposition/: Core (implementation-guide.md) vs Reference (data-sources.md)
  - human-facing-documentation/: Marked "Not for LLM loading"

- Added initialization.md for automated environment setup
  - LLM-executable setup steps (venv, dependencies)
  - Platform-specific commands (Windows/macOS/Linux)
  - Updated project-setup.md with Quick Start reference

- Configured workspace-specific system prompts
  - Created .vscode/settings.json (end-of-session protocol trigger)
  - Version-controlled as experimental apparatus
  - Updated system-prompts.md to document workspace approach

**Decisions Made**:

| Decision | Rationale | Impact |
|----------|-----------|--------|
| Tiers measure context depth, not directory nesting | Previous ambiguity conflated structural with functional tiers | Clear guidance for which files to load in any context |
| INDEX files as relay nodes | "First time here? Load core files. Need more? References available" | Simple directory entry pattern, no complex dependency mappings |
| Theory documents all Tier 2 | Formalized = lightweight tokens, load all for complete context | ~25k tokens when working on theory (manageable) |
| data-sources.md as Tier 3 | Historical reproducibility, not routine loading | Reduces unnecessary context pollution |
| Workspace-specific settings | System prompts only active in this project | Zero manual switching, version-controlled configuration |

**Discoveries**:
- Previous session encoded ambiguity: directories ≠ tiers (structural ≠ functional)
- Directory structure encodes semantics: WITH implementation.md = workspace (Tier 2), WITHOUT = library (Tier 3)
- Tier structure naturally handles dependency cascading (no explicit "to edit X load Y" needed)
- System prompts are Tier 0 (outside hierarchy but critical for reproducibility)

**Validation**:
- All INDEX files follow relay node pattern ✓
- Tier classifications consistent across all documents ✓
- implementation.md correctly specifies functional tier system ✓
- Meta-maintenance updated to reflect architectural changes ✓

**Architecture Impact**:
- Tier system now correctly specified and consistently applied
- INDEX files provide clear directory entry guidance
- System maintains self-referential consistency (meta-docs follow own patterns)
- Workspace configuration version-controlled (reproducible experimental apparatus)

**Git Commits**:
- 709fc95: Added initialization.md and updated project-setup.md
- e343e8e: Added .vscode/settings.json to repository
- 15ed3d0: Tier clarification and INDEX standardization

**Next Steps**:
- Test tier system with fresh session (verify bootstrap → directory navigation)
- Begin Wikipedia pipeline implementation using documented patterns
- Monitor token budgets in practice (validate tier estimates)

---

### Session: 2025-12-15 (Afternoon) - End-of-Session Protocol & Per-Directory INDEX Pattern

**Completed**:
- Created `llm-facing-documentation/end-of-session-protocol.md` (~3k tokens)
  - 7-step systematic procedure for closing work sessions
  - Conditional meta-loading trigger (only when system docs modified)
  - Three scenario walkthroughs (implementation, documentation, research)
  - Token budget estimates per scenario type
  - Error recovery guidance for missed steps

- Updated `human-facing-documentation/system-prompts.md`
  - Added end-of-session protocol trigger configuration
  - Updated validation steps to match 7-step protocol
  - Added protocol description and reference link

- Created per-directory INDEX.md files (5 total)
  - `meta-maintenance/INDEX.md` (5 files, ~34k tokens)
  - `llm-project-management-instructions/INDEX.md` (2 files, ~11k tokens)
  - `human-facing-documentation/INDEX.md` (4 files, ~16k tokens)
  - `data-pipeline/INDEX.md` (subdirectory manifest)
  - `data-pipeline/wikipedia-decomposition/INDEX.md` (2 files, ~8k tokens)
  
- Updated `meta-maintenance/implementation.md` with new architectural patterns
  - Per-directory INDEX.md specification (minimal manifest format)
  - Document deprecation policy (theory → deprecated/, code → git)
  - System prompts as experimental apparatus section
  - End-of-session protocol overview with token budgets
  - Updated Tier 1 structure diagram

- Updated `meta-maintenance/session-log.md` with Dec 15 comprehensive entry
  - 7 major work areas (theory cleanup, deprecation, tier classification, human docs, protocol, INDEX, meta-updates)
  - Key discoveries (system prompts, context displacement, self-referential application)
  - Decision table with rationale and impact
  - Before/after architecture comparison

**Decisions Made**:

| Decision | Rationale | Impact |
|----------|-----------|--------|
| **End-of-session protocol created** | Circular dependency: changing llm-docs requires updating meta-maintenance | Closes meta-documentation loop systematically |
| **Conditional meta-loading** | Loading meta-maintenance every session wastes ~30k tokens | Only load when system docs modified (~8-12k conditional cost) |
| **Per-directory INDEX.md** | Quick directory overview without loading all files | -300 tokens per directory scan |
| **System prompts as apparatus** | Recognition that prompts define inference rules, not just config | Establishes reproducibility requirement for all collaborators |

**Discoveries**:
- **Meta-documentation loop closed**: Protocol ensures system docs trigger meta-maintenance updates
- **Self-referential consistency**: Meta-maintenance now follows its own documented principles
- **Token optimization validated**: All phases completed within budget estimates
- **Phased implementation success**: Breaking into 5 phases prevented cognitive overload

**Validation**:
- End-of-session protocol comprehensive (covers all edge cases) ✓
- System prompts updated with correct trigger keywords ✓
- All 5 INDEX.md files created with 200-300 token targets ✓
- Meta-maintenance files updated with Dec 15 architectural changes ✓
- Timeline entry created (this entry) ✓

**Architecture Impact**:
- **End-of-session protocol establishes feedback loop**: Documentation system now maintains itself systematically
- **INDEX.md pattern universalized**: Every directory gets minimal manifest
- **System prompts formalized**: Recognized as experimental apparatus requiring version control
- **Meta-maintenance updated**: Now reflects complete current architecture (deprecation, INDEX, protocol, tiers)

**Git Commits**:
- Morning commit (7701353): Theory cleanup, human docs, deprecation policy
- Pending commit: End-of-session protocol, INDEX files, meta-maintenance updates

**Next Steps**:
- Commit protocol and INDEX.md work
- Test end-of-session protocol in next session
- Verify system prompt trigger configuration works
- Apply protocol when closing this session

---

### Session: 2025-12-15 (Morning) - Theory Documentation Cleanup & Deprecation Policy

**Completed**:
- Created `theories-proofs-conjectures/deprecated/` subdirectory
  - Moved superseded inference summary files out of active namespace
  - Preserved historical documents with updated links to merged version
  
- Created `theories-proofs-conjectures/INDEX.md` (~500 tokens)
  - Clear listing of 3 active theory documents vs. deprecated documents
  - Explicit "never load deprecated/" instruction
  - Token budget guidance (~15-20k for all theory)
  
- Created `theories-proofs-conjectures/unified-inference-theory.md` (~4-5k tokens)
  - Merged inference-summary.md and inference-summary-with-event-tunneling.md
  - Comprehensive integration: N-Link theory, database inference, tunneling, event-coupled inference
  - Proper metadata blocks following documentation standards
  
- Standardized theory document metadata
  - Replaced HTML comments in n-link-rule-theory.md and database-inference-graph-theory.md
  - Added proper metadata blocks with theory-appropriate fields
  
- Created `llm-facing-documentation/README.md` (~700 tokens)
  - 3-sentence project summary for new sessions
  - Bootstrap instructions with tier system
  - Theory overview pointing to unified document

**Decisions Made**:
- **Deprecation Policy Established**: Theory documents get explicit deprecation
  - Rationale: Major theory evolutions create substantial divergence from original
  - Pattern: Create deprecated/ subdirectory, move old versions, update links
  - Add INDEX.md to directories with deprecated content
  - Code and project documentation rely on git version history (not deprecated/)
  
- **Namespace Hygiene**: Active vs. deprecated content separation
  - Rationale: Prevents accidental loading of superseded documents
  - Achievement: Reduced theory context pollution by ~8-10k tokens
  - New sessions load only current theory via INDEX.md guidance

**Discoveries**:
- **Documentation System Self-Application**: System properly documents its own maintenance patterns
  - Theory documents needed same rigor as implementation documents
  - Metadata standardization applies across all document types
  - Deprecation is a documented, repeatable process

**Validation**:
- All deprecated documents updated with new paths and deprecation notices
- INDEX.md provides clear active/deprecated distinction
- README.md provides fast onboarding (<1 min read for project summary)
- Cross-references verified in unified-inference-theory.md

**Architecture Impact**:
- Theory directory now self-documenting via INDEX.md
- Clear separation: active theory (3 files) vs. historical archive (deprecated/)
- Deprecation policy formalized in project-management-practices.md
- Pattern established for future theory evolutions
- **Theory documents classified as Tier 2** (resolved open question from 2025-12-12)

**Next Steps**:
- Begin Wikipedia extraction implementation using documented theory foundation
- Consider applying INDEX.md pattern to other directories as they grow
- Monitor theory context load in practice (target: 15-20k tokens)

---

### Session: 2025-12-12 (Evening) - Tier 1 Documentation Token Budget Optimization

**Completed**:
- Created `meta-maintenance/writing-guide.md` (~2,324 tokens)
  - Extracted detailed examples from documentation-standards.md
  - Complete formatting patterns with good/bad examples
  - Research foundation (OpenAI, Anthropic, arXiv paper - all 26 principles)
  - Copy-paste ready templates (metadata blocks, docstrings, procedures)
  
- Created `meta-maintenance/data-sources.md` (~690 tokens)
  - External research links with annotations
  - Wikipedia/MediaWiki technical resources
  - Discovery dates and application notes
  
- Compressed `documentation-standards.md` (20k+ → ~960 tokens)
  - Reduced to core 10 Golden Rules + quick-reference tables
  - Added bootstrap instructions for new LLM sessions
  - All detailed content moved to writing-guide.md with pointers
  
- Compressed `project-management-practices.md` (8-10k → ~960 tokens)
  - Tier system quick reference table
  - "How to start new session" bootstrap instructions
  - "Creating new directory" copy-paste template
  - Removed redundant content (implementation.md covers architecture)

**Decisions Made**:
- **Token Budget Strategy**: Aggressive compression with just-in-time loading
  - Rationale: Tier 1 should be <12k tokens total; was ~30k (2.5x over budget)
  - Achieved: ~2,370 tokens (80% savings, 5x under budget)
  
- **Restructure Approach**: Extract to Tier 2, not delete
  - Rationale: Preserve granular content for when creating new documentation
  - Pattern: Brief + pointer in Tier 1 → Details in Tier 2
  
- **Bootstrap Path**: Explicit navigation instructions in Tier 1
  - Rationale: Blank-slate LLM must be able to navigate from cold start
  - Implementation: Step-by-step "Starting a New Session" section

**Discoveries**:
- **Recursive Realization**: Documentation system's own docs violated its principles
  - Original Tier 1 docs written before architecture finalized
  - System needed to "self-heal" by applying its own rules to itself
  
- **Just-In-Time Loading Pattern**: Tier 2 details loaded only when needed
  - Don't load writing-guide.md every session
  - Load it only when creating new documentation
  - Matches human behavior: Check style guide when writing, not when reading

**Validation**:
- Tier 1 token count: 2,370 / 12,000 budget ✓
- Bootstrap path tested mentally: Clear Tier 1 → Tier 2 navigation
- Cross-references validated (documentation-standards.md ↔ writing-guide.md)
- Self-referential integrity maintained (system documents itself correctly)

**Architecture Impact**:
- Tier 1 now truly universal: Core rules + templates only
- Tier 2 now contains granular implementation: Detailed examples + research
- System achieves stated goal: "Just enough context to bootstrap"

**Git Commit**: `2811316` - "Optimize Tier 1 documentation token budget"

**Next Steps**:
- Test bootstrap path with actual new session (verify Tier 1 sufficient)
- Begin Wikipedia extraction implementation with new documentation patterns

---

### Session: 2025-12-12 - Project Initialization & Documentation Framework

**Completed**:
- Initialized git repository at `c:\Coding\Self Reference Modeling`
- Created `.gitignore` excluding Python artifacts and large Wikipedia data files
- Set up Python virtual environment (3.13.9)
- Installed core dependencies: pandas, numpy, lxml, regex, pytest, black, jupyter
- Created VSCode workspace configuration with Python/Jupyter support
- Created `documentation-standards.md` - Comprehensive LLM-facing documentation guidelines
- Created `project-management-practices.md` - Document taxonomy and maintenance procedures
- Created `project-timeline.md` - This cumulative timeline document

**Decisions Made**:
- **Documentation Philosophy**: LLM-first approach prioritizing structure over prose
  - Rationale: Optimize for machine parsing and token efficiency
  - Alternative considered: Human-readable narrative style (rejected - wrong audience)
  
- **Documentation Maintenance**: Cumulative append-only timeline instead of snapshot status
  - Rationale: Prevents stale "current status" statements that future sessions misinterpret
  - Alternative considered: Rewriting status sections (rejected - loses historical context)
  
- **Document Taxonomy**: Two-tier system (Read Every Session vs. Context-Specific)
  - Rationale: Efficient context loading - load ~8-12k tokens of essential context, then deep-dive as needed
  - Alternative considered: Flat structure with all docs equal priority (rejected - token waste)

- **Wikipedia Data Pipeline**: Path 1 (DB + XML hybrid) over pure XML parsing
  - Rationale: Database provides ground truth for page names; XML provides link ordering
  - Alternative considered: Pure XML parsing with manual canonicalization (rejected - too error-prone)

**Discoveries**:
- **Critical**: Wikipedia's `pagelinks` table contains template-expanded links
  - Implication: Cannot use pagelinks directly for N-Link analysis - would include template-injected "gravity wells"
  - Solution: Parse raw wikitext from XML dumps, strip templates before extracting links
  
- Quarry (https://quarry.wmcloud.org/) provides free SQL access to Wikipedia database
  - Implication: Can download complete page table for canonical name lookup
  
- Wikipedia has special lowercase-first-char pages (eBay, iPhone, pH)
  - Implication: Cannot assume first-char capitalization; must check exact match first
  
- Disambiguation pages are in regular `page` table but flagged in `page_props`
  - Implication: Can query and exclude from N-Link traversal; valuable to catalog separately

**Research Completed**:
- Reviewed Wikipedia naming convention documentation (technical restrictions, page names, MediaWiki manual)
- Investigated database schema: `page`, `pagelinks`, `templatelinks`, `redirect`, `linktarget` tables
- Analyzed template vs. prose link distinction problem
- Researched prompt engineering best practices (OpenAI, Anthropic, arXiv:2312.16171)

**Documentation Created**:
- `external-docs.md` - Wikipedia naming rules, Quarry info, database schema resources
- `wikipedia-link-graph-decomposition.md` - Complete extraction pipeline design
  - TSV-based output format to avoid JSON escaping issues
  - Decomposition approach: parse once, preserve everything, filter downstream
  - Recomposition strategies for different N-Link configurations

**Next Steps**:
- Create functional project directories (src/, data/, tests/)
- Implement Quarry query scripts to download page table
- Begin Wikipedia XML multistream parser implementation
- Develop template stripping algorithm (recursive `{{...}}` removal)
- Build link extraction with normalization and matching logic

**Session Context**:
This was the foundational session establishing project infrastructure and documentation framework. Heavy emphasis on designing maintainable, self-referential documentation system for future LLM sessions. Key breakthrough: understanding that pagelinks table contamination requires full wikitext parsing approach.

---

## Archive

*(Entries older than 6 months will be moved here)*

---

## Changelog

### 2025-12-12 (Second Update)
- Added evening session entry: Tier 1 documentation token budget optimization

### 2025-12-12
- Created project timeline document
- Added first session entry documenting initialization and framework design

---

**END OF DOCUMENT**
