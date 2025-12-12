# Documentation Writing Guide

**Document Type**: Reference guide  
**Target Audience**: LLMs creating new documentation  
**Purpose**: Detailed examples, patterns, and research-backed principles for writing effective LLM-facing documentation  
**Last Updated**: 2025-12-12  
**Dependencies**: [documentation-standards.md](../llm-facing-documentation/llm-project-management-instructions/documentation-standards.md), [implementation.md](./implementation.md)  
**Status**: Active

---

## When to Read This Document

**Primary Use Cases**:
- Creating a new documentation file for the first time
- Unsure how to structure a specific section
- Need examples of specific patterns (tables, XML, definition lists)
- Researching best practices for prompt engineering

**Bootstrap Path**: 
1. First read [documentation-standards.md](../llm-facing-documentation/llm-project-management-instructions/documentation-standards.md) for core rules
2. Then read this document for detailed implementation guidance
3. Use templates directly from this file (copy-paste ready)

---

## Research Foundation

### Prompt Engineering & Best Practices

**OpenAI Prompt Engineering Guide**  
https://platform.openai.com/docs/guides/prompt-engineering

Key takeaways for documentation:
- Use clear hierarchical structure (Markdown headers, XML tags)
- Separate Identity/Instructions/Examples/Context into distinct sections
- Position reusable context at the beginning (prompt caching optimization)
- Use few-shot examples for pattern establishment
- Explicit instructions outperform implicit assumptions
- Developer messages > User messages in priority hierarchy

**Anthropic Research on AI Safety & Interpretability**  
https://www.anthropic.com/research

Key findings relevant to documentation:
- Models exhibit limited introspection capabilities → Provide explicit reasoning frameworks
- Alignment through constitutional principles → Establish clear rules
- Circuit tracing reveals shared conceptual spaces → Use consistent terminology
- Models benefit from explicit reasoning frameworks → Document decision logic

**Principled Instructions Paper (arXiv:2312.16171)**  
https://arxiv.org/abs/2312.16171

26 core principles for LLM prompting validated across LLaMA, GPT-3.5/4:
1. Be specific and detailed in requirements
2. Break complex tasks into sequential steps
3. Use positive framing ("do this" not "don't do that")
4. Include examples of desired outputs
5. Specify output format explicitly
6. Use delimiters to mark distinct sections
7. Provide context at the beginning
8. Use repeated phrases for emphasis on key concepts
9. Combine Chain-of-Thought with few-shot prompting
10. Use output primers (start generation with desired format)
11. Add detailed context within the prompt
12. Use examples to demonstrate reasoning process
13. Assign roles to establish perspective
14. Specify style, tone, or length constraints
15. Incorporate "reason step-by-step" instructions
16. Use affirmative directives ("do") over negative ones ("don't")
17. Clarify the intended audience
18. Break complex prompts into smaller sub-tasks
19. Use leading words to guide output format
20. Repeat key instructions at critical points
21. Use separators to distinguish sections
22. Include both positive and negative examples
23. Test prompts iteratively and refine
24. Specify desired length or level of detail explicitly
25. Combine multiple strategies for complex tasks
26. Prioritize clarity over brevity

---

## Content Formatting Patterns (Detailed Examples)

### Lists for Discrete Items

**Purpose**: Enumerate distinct elements without implicit ordering

**Good Example**:
```markdown
**Supported Python Versions**:
- Python 3.9
- Python 3.10
- Python 3.11
- Python 3.12
- Python 3.13
```

**Bad Example** (implicit ordering suggests priority):
```markdown
Python versions:
- Python 3.13 (works great!)
- Python 3.9 (older but fine)
```

**When to Use**:
- Configuration options
- Feature lists
- Dependencies
- Tool inventory

---

### Numbered Lists for Sequences

**Purpose**: Steps, procedures, ranked priorities where order matters

**Good Example** (Procedure):
```markdown
**Git Self-Healing Protocol**:
1. Attempt `file_search("filename.md")`
2. If not found, check `git log --all --full-history -- '**/filename.md'`
3. Update document with correct path
4. Log correction to project-timeline.md
5. Update "Last Updated" timestamp
```

**Good Example** (Ranking):
```markdown
**Priority Order for Token Budget**:
1. Metadata & Purpose (front-load context)
2. Core Definitions (establish vocabulary)
3. Algorithmic Logic (procedures, decision trees)
4. Examples (illustrative cases)
5. Edge Cases (corner conditions)
```

**Bad Example** (No dependency between items):
```markdown
Setup steps:
1. Install Python
2. Configure git
3. Create venv
```
*Note: These could be done in any order, so bullet list is better*

---

### Definition Lists for Term Clarification

**Purpose**: Establish vocabulary, clarify project-specific meanings

**Good Example**:
```markdown
**N-Link Rule**: A deterministic graph traversal algorithm that selects the Nth outgoing link at each vertex, where N is fixed for the entire traversal.

**HALT Condition**: The traversal terminates when reaching a vertex with fewer than N outgoing links.

**CYCLE Condition**: The traversal enters an infinite loop when revisiting a previously-visited vertex.
```

**When to Use**:
- Glossary sections
- Term introductions
- Disambiguating overloaded terms
- Project-specific vocabulary

**Pattern**:
```markdown
**Term Name**: Single-sentence definition, optionally followed by clarifying details or constraints.
```

---

### Code Blocks with Language Tags

**Purpose**: Executable examples, schemas, configurations

**Good Example** (Python with docstring):
```python
def normalize_link_text(raw_text: str, page_lookup: dict) -> Optional[int]:
    """
    Normalize wikitext link and match to page_id.
    
    Args:
        raw_text: Link text from [[...]] pattern (may be lowercase, underscored)
        page_lookup: Dict mapping canonical page_title -> page_id
        
    Returns:
        page_id if match found, None if unmatched
        
    Algorithm:
        1. Strip whitespace
        2. Replace underscores with spaces
        3. Try exact match
        4. Fallback: capitalize first char and retry
        5. Fallback: case-insensitive search
    """
    # Edge case: Some pages like "eBay" have forced lowercase first char
    clean_text = raw_text.strip().replace('_', ' ')
    
    if clean_text in page_lookup:
        return page_lookup[clean_text]
    
    capitalized = clean_text[0].upper() + clean_text[1:]
    if capitalized in page_lookup:
        return page_lookup[capitalized]
    
    return None
```

**Good Example** (Configuration):
```json
{
  "python.analysis.typeCheckingMode": "strict",
  "editor.formatOnSave": true,
  "python.linting.pylintEnabled": true
}
```

**Good Example** (Shell command with explanation):
```powershell
# Download latest Wikipedia page table (enwiki database)
# --limit 1000 for testing, remove for full dataset
python -m quarry.download --database enwiki --table page --limit 1000
```

**When to Use**:
- Executable code snippets
- Configuration files
- Command-line examples
- Data schemas
- API request/response examples

---

### Tables for Comparative Data

**Purpose**: Compare 3+ dimensions across multiple items

**Good Example** (Feature comparison):
```markdown
| Approach | Data Source | Link Quality | Setup Complexity | Processing Time |
|----------|-------------|--------------|------------------|-----------------|
| Quarry pagelinks | SQL table | Contaminated (templates) | Low | Minutes |
| XML dump parsing | Wikitext source | Clean (prose only) | High | Hours |
| **Hybrid** (chosen) | Quarry + XML | Clean | Medium | Hours |
```

**Good Example** (Document types):
```markdown
| Document Type | Target Length | Max Length | Update Frequency |
|---------------|---------------|------------|------------------|
| Meta-documentation | 2000-4000 tokens | 8000 tokens | Rare |
| Theory paper | 3000-6000 tokens | 12000 tokens | Never |
| Implementation guide | 1000-3000 tokens | 6000 tokens | Per feature |
| API reference | 500-1500 tokens | 4000 tokens | Per API change |
```

**When to Use**:
- Comparing multiple alternatives
- Specification tables (parameters, return values)
- Decision matrices
- Status dashboards

**When NOT to Use**:
- Two-item comparison (use prose or bullet list)
- Single-dimension data (use list)
- Deeply nested structures (use XML or JSON)

---

### XML Delimiters for Complex Content

**Purpose**: Strict boundaries, nested structures, content with metadata

**Good Example** (Conceptual structure):
```xml
<concept id="n-link-theory" category="graph-theory">
  <definition>
    A deterministic traversal rule on finite directed graphs that selects
    the Nth outgoing link at each vertex.
  </definition>
  
  <properties>
    <property name="termination">Guaranteed (finite graphs)</property>
    <property name="outcome">Binary: HALT or CYCLE</property>
    <property name="determinism">Given same N and graph, outcome identical</property>
  </properties>
  
  <applications>
    <application domain="web-graphs">Link analysis and connectivity studies</application>
    <application domain="knowledge-graphs">Inference path traversal</application>
  </applications>
</concept>
```

**Good Example** (Multi-attribute examples):
```xml
<example id="wikipedia-template-contamination" severity="critical">
  <discovery-date>2025-12-12</discovery-date>
  
  <problem>
    The pagelinks table includes links expanded from templates like
    {{Infobox}} and {{Navbox}}, which are not prose links clicked by readers.
  </problem>
  
  <evidence>
    SELECT COUNT(*) FROM pagelinks WHERE pl_from = 12345;
    -- Returns 847 links
    
    Manual inspection of [[Page_Title]] shows only ~50 prose links in article body.
  </evidence>
  
  <solution>
    Parse XML dump directly, strip templates before link extraction.
    See: data-pipeline/wikipedia-decomposition/implementation.md
  </solution>
  
  <impact>High - Invalidates N-Link analysis using pagelinks table</impact>
</example>
```

**When to Use**:
- Nested conceptual hierarchies
- Examples with multiple attributes (date, severity, category)
- Cross-referenced sections needing unique IDs
- Content requiring semantic markup beyond Markdown

**Pattern Template**:
```xml
<[element-type] id="unique-identifier" [optional-attributes]>
  <[child-element]>Content</[child-element]>
  <[another-child]>More content</[another-child]>
</[element-type]>
```

---

## Explicit Relationship Markers

### Standard Markers

**PREREQUISITE**: Must understand referenced content before this section
```markdown
**PREREQUISITE**: Must read [n-link-rule-theory.md](../theories-proofs-conjectures/n-link-rule-theory.md) before implementing graph traversal.
```

**IMPLIES**: Logical consequence
```markdown
**IMPLIES**: If pagelinks contains template links, then N-Link analysis using this table will be contaminated.
```

**CONTRADICTS**: Conflicts with previous assumption
```markdown
**CONTRADICTS**: Earlier assumption that pagelinks = prose links. Actually pagelinks = prose + template-expanded links.
```

**ALTERNATIVE**: Different approach to same problem
```markdown
**ALTERNATIVE**: Instead of XML parsing, could use Wikipedia API with prop=links parameter. See [data-sources.md](./data-sources.md#api-approach) for trade-offs.
```

**DEPRECATED**: Replaced by newer approach
```markdown
**DEPRECATED** (2025-12-12): Direct pagelinks table usage for N-Link traversal.

**REASON**: pagelinks includes template-expanded links, causing contamination.

**REPLACEMENT**: XML parsing pipeline. See [implementation.md](../../data-pipeline/wikipedia-decomposition/implementation.md).
```

**SEE ALSO**: Related but not required
```markdown
**SEE ALSO**: For Wikipedia page name normalization rules, see [data-sources.md](./data-sources.md#page-name-normalization).
```

---

## Semantic Precision Techniques

### Ambiguity Elimination

**AVOID vague language**:

| Vague | Precise | Why Better |
|-------|---------|------------|
| "might", "could", "possibly" | "occurs when X condition" OR "estimated 60% probability" | Eliminates uncertainty |
| "some", "several", "many" | "3-5 items" OR ">50% of cases" | Quantifies |
| "recently", "soon", "later" | "2025-12-10" OR "version 2.0" OR "after pagelinks extraction" | Anchors in time |
| "simple", "complex", "large" | "3 steps" OR "O(n²) complexity" OR "25GB compressed" | Measurable |
| "it", "this", "that" | Repeat noun OR use [concept-name] | Eliminates ambiguity |

**Examples**:

**Vague**:
```markdown
The XML dump is large and might take a while to process. It has many pages.
```

**Precise**:
```markdown
The enwiki XML dump is ~25GB compressed, containing ~6.8M pages. Processing takes 4-8 hours on an 8-core system with 16GB RAM.
```

---

**Vague**:
```markdown
Some pages have special characters that could cause problems.
```

**Precise**:
```markdown
~2% of Wikipedia pages contain Unicode characters outside ASCII range (e.g., [[Björk]], [[François Mitterrand]]). The link normalization function handles UTF-8 encoding correctly, but ensure page_lookup dictionary keys are UTF-8 strings.
```

---

### Vocabulary Control Patterns

**Establish canonical terms early**:
```markdown
## Terminology

This project uses the following canonical terms:

**N-Link Rule**: NOT "N-link algorithm", "nth link traversal", "link-following rule"  
**pagelinks table**: NOT "page_links", "page-links", "link table"  
**wikitext**: NOT "wiki text", "wiki-text", "MediaWiki markup"  
**HALT condition**: NOT "halt state", "termination", "dead-end"  
**CYCLE condition**: NOT "loop", "infinite traversal", "cycle detection"

Use these terms consistently throughout all documentation and code.
```

**Link on first usage**:
```markdown
The [N-Link Rule](#n-link-rule-definition) determines traversal behavior...
```

**Create glossary for large projects**:
```markdown
See [glossary.md](./glossary.md) for complete term definitions.
```

---

## Document Length & Token Budget

### Estimation Technique

**Rule of Thumb**: 
- 1 token ≈ 4 characters (English text)
- 1 token ≈ 0.75 words (average)
- 1000 tokens ≈ 750 words ≈ 3000 characters

**Quick Check**:
```python
# Python token estimation
import tiktoken

encoder = tiktoken.get_encoding("cl100k_base")  # GPT-4 encoding
with open("document.md", "r", encoding="utf-8") as f:
    text = f.read()
    tokens = encoder.encode(text)
    print(f"Token count: {len(tokens)}")
```

### Splitting Strategy When Over Budget

**OPTION 1: Hierarchical Split**
```
Original: comprehensive-guide.md (15k tokens)

Split into:
- guide-overview.md (2k tokens) - High-level concepts, links to details
- guide-setup.md (4k tokens) - Installation and configuration
- guide-usage.md (5k tokens) - Common workflows
- guide-advanced.md (4k tokens) - Edge cases and optimizations
```

**OPTION 2: Tier-Based Split**
```
Original: implementation.md (20k tokens)

Split into:
- Tier 1: implementation.md (3k tokens) - WHAT + templates
- Tier 2: implementation-details.md (10k tokens) - HOW + examples
- Tier 3: implementation-research.md (7k tokens) - WHY + alternatives
```

**OPTION 3: Extract Examples**
```
Original: api-docs.md (12k tokens, includes 30 examples)

Split into:
- api-docs.md (4k tokens) - API signatures, brief descriptions
- api-examples.md (8k tokens) - Complete working examples with explanations
```

---

## Testing Documentation Effectiveness

### Self-Test Questions

After writing documentation, ask:

**Clarity**:
- [ ] Can a blank-slate LLM understand this without external context?
- [ ] Are all technical terms defined or linked?
- [ ] Are there any ambiguous pronouns ("it", "this") without clear antecedent?

**Completeness**:
- [ ] Does the document deliver on its stated purpose (from metadata)?
- [ ] Are all code examples syntactically valid and runnable?
- [ ] Are error cases and edge cases documented?

**Efficiency**:
- [ ] Can key information be found via grep/search without reading entire doc?
- [ ] Are examples copy-paste ready?
- [ ] Is information density high (1 key fact per paragraph)?

**Maintainability**:
- [ ] Will this document become stale? If yes, is update protocol clear?
- [ ] Are all cross-references using absolute paths?
- [ ] Is the changelog present (for cumulative docs)?

### Readability Metrics

**GOOD INDICATORS**:
- Headers reveal content without reading body
- Consistent terminology throughout
- Minimal forward references (definitions before usage)
- Information density: 1-2 key facts per paragraph

**WARNING SIGNS**:
- Narrative flow: "As we mentioned earlier..." → Use explicit links
- Implicit knowledge: "Obviously..." → State explicitly
- Tangled dependencies: Must read 5+ docs to understand one section → Refactor
- Repeated information across multiple docs → Consolidate or cross-reference

---

## Metadata Block Template

Copy-paste this template for new documents:

```markdown
# [Document Title]

**Document Type**: [meta-documentation | theory | implementation | reference | procedure]  
**Target Audience**: [LLMs | humans | both]  
**Purpose**: [One-sentence description of what this document accomplishes]  
**Last Updated**: YYYY-MM-DD  
**Dependencies**: [[linked-doc.md](path/to/linked-doc.md)] (optional)  
**Status**: [draft | active | deprecated]

---

[Document content begins here]
```

**Field Definitions**:

**Document Type**:
- `meta-documentation`: Describes the documentation system itself
- `theory`: Mathematical proofs, conceptual foundations
- `implementation`: How to build something
- `reference`: API docs, lookup tables, specifications
- `procedure`: Step-by-step instructions for a specific task

**Target Audience**:
- `LLMs`: Optimized for machine parsing (this project's default)
- `humans`: Narrative style for human reading
- `both`: Hybrid format

**Purpose**: Answer "Why would someone read this document?" in one sentence.

**Dependencies**: Link to documents that should be read first. Optional but helpful.

**Status**:
- `draft`: Work in progress, may have gaps
- `active`: Complete and current
- `deprecated`: Replaced by newer document, kept for history

---

## Changelog Pattern

For documents that evolve over time, add a changelog section at the end:

```markdown
---

## Changelog

### YYYY-MM-DD
- Added section on XML delimiters
- Clarified token budget guidelines
- Fixed broken link to external-docs.md

### YYYY-MM-DD
- Initial document creation
- Established metadata format
```

**Rules**:
- Reverse chronological (newest first)
- Brief bullet points
- Focus on structural changes, not typo fixes
- Include date in YYYY-MM-DD format

---

## Code Documentation Integration

### Python Docstring Template

```python
def function_name(param1: Type1, param2: Type2) -> ReturnType:
    """
    One-sentence summary of what the function does.
    
    Longer explanation if needed. Describe the algorithm, edge cases,
    or any non-obvious behavior.
    
    Args:
        param1: Description of first parameter
        param2: Description of second parameter
        
    Returns:
        Description of return value, including None cases
        
    Raises:
        ExceptionType: When this exception occurs
        
    Algorithm:
        1. Step one
        2. Step two
        3. Step three
        
    Example:
        >>> result = function_name("input", 42)
        >>> print(result)
        'output'
        
    References:
        See [doc-name.md](path/to/doc.md#section) for context
    """
    pass
```

**When to Include Each Section**:
- `Args`: Always (unless no parameters)
- `Returns`: Always (unless void/None)
- `Raises`: If function can raise exceptions
- `Algorithm`: If logic is non-trivial
- `Example`: For public API functions
- `References`: If implementation follows spec in docs

---

### Inline Comment Guidelines

**GOOD - Explains non-obvious edge case**:
```python
# Edge case: Wikipedia pages like "eBay" and "iPhone" have lowercase first char
# MediaWiki's page table stores these exactly as written
if raw_text in page_lookup:
    return page_lookup[raw_text]
```

**GOOD - Explains performance optimization**:
```python
# Pre-compile regex once (1000x faster than compiling per iteration)
LINK_PATTERN = re.compile(r'\[\[([^|\]]+)(?:\|[^\]]+)?\]\]')
```

**BAD - Restates what code obviously does**:
```python
# Loop through items
for item in items:
    # Process item
    process(item)
```

**Rule**: Only comment if the "why" is not obvious from reading the code itself.

---

## Examples Library

### Example 1: Procedure Document

```markdown
# Git Self-Healing Protocol

**Document Type**: Procedure  
**Target Audience**: LLMs  
**Purpose**: Fix broken file references using git history as source of truth  
**Last Updated**: 2025-12-12  
**Status**: Active

---

## When to Use

Execute this procedure when:
- A markdown link returns "file not found"
- A referenced document path is invalid
- Cross-reference fails to resolve

---

## Steps

### 1. Attempt Workspace Search

```
file_search("filename.md")
```

**Expected**: List of matching files with full paths

**If found**: Proceed to step 4

**If not found**: Proceed to step 2

### 2. Check Git History

```powershell
git log --all --full-history -- '**/filename.md'
```

**Expected**: Commit history showing file renames/moves

**Extract**: Latest known path from most recent commit

### 3. Update Document

Replace broken reference:
```markdown
OLD: [doc](old-path/filename.md)
NEW: [doc](new-path/filename.md)
```

### 4. Log Correction

Append to project-timeline.md:
```markdown
### YYYY-MM-DD - Documentation Maintenance
**Fixed**: Broken reference to `old-path/filename.md` → `new-path/filename.md`
**Reason**: File moved in commit [hash]
```

### 5. Update Metadata

In the corrected document, update:
```markdown
**Last Updated**: YYYY-MM-DD
```

---

## Validation

Verify fix by:
- [ ] Following updated link successfully
- [ ] Confirming file_search returns correct path
- [ ] Checking no other references to old path exist (grep search)

---

## Related Documents

- [project-management-practices.md](../llm-facing-documentation/llm-project-management-instructions/project-management-practices.md) - Context for when to use this protocol
```

---

### Example 2: Theory Document

```markdown
# Inference Tunneling Through Event Graphs

**Document Type**: Theory  
**Target Audience**: LLMs  
**Purpose**: Prove that N-Link traversals can tunnel through intermediate events to connect distant database entities  
**Last Updated**: 2025-12-10  
**Dependencies**: [n-link-rule-theory.md](./n-link-rule-theory.md)  
**Status**: Active

---

## Core Theorem

**Theorem**: For any database D represented as a bipartite graph (entities ↔ events), an N-Link traversal that reaches entity E via path P implicitly contains all intermediate events along P.

**Implication**: N-Link results encode provenance - not just "these entities are related" but "these entities are related via this specific event chain."

---

## Formal Definition

### Graph Structure

```
G = (V, E) where:
  V = Entities ∪ Events
  E ⊆ (Entities × Events) ∪ (Events × Entities)
```

**Constraints**:
- Entities only link to Events
- Events only link to Entities
- No Entity→Entity or Event→Event edges

### Traversal Path

```
P = [v₀, v₁, v₂, ..., vₖ] where:
  v₀ ∈ Entities (start)
  vₖ ∈ Entities (end)
  vᵢ ∈ Events for odd i
  vᵢ ∈ Entities for even i
```

---

## Proof

[Proof content here...]

---

## Example: Wikipedia Person-Article-Person Chain

[Example content here...]
```

---

## Related Documents

- [documentation-standards.md](../llm-facing-documentation/llm-project-management-instructions/documentation-standards.md) - Core rules (Tier 1)
- [implementation.md](./implementation.md) - Documentation system architecture (Tier 2)
- [data-sources.md](./data-sources.md) - External research links

---

## Changelog

### 2025-12-12
- Initial creation
- Extracted from documentation-standards.md as part of token budget optimization
- Reorganized content: research → patterns → examples → templates
- Added detailed examples for all formatting patterns
- Created copy-paste templates for metadata blocks and docstrings

---

**END OF DOCUMENT**
