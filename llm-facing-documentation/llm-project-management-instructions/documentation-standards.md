# LLM-Facing Documentation Standards

**Document Type**: Meta-documentation framework  
**Target Audience**: Large Language Models (AI assistants)  
**Purpose**: Establish standards for creating, maintaining, and interpreting documentation within this project  
**Last Updated**: 2025-12-12

---

## Core Principle

This project uses **LLM-first documentation** - optimized for machine parsing and reasoning rather than human narrative reading. Documentation should be structured, explicit, and context-efficient.

---

## Key Resources

### Prompt Engineering & Best Practices

**OpenAI Prompt Engineering Guide**  
https://platform.openai.com/docs/guides/prompt-engineering

Key takeaways:
- Use clear hierarchical structure (Markdown headers, XML tags)
- Separate Identity/Instructions/Examples/Context into distinct sections
- Position reusable context at the beginning (prompt caching optimization)
- Use few-shot examples for pattern establishment
- Explicit instructions outperform implicit assumptions
- Developer messages > User messages in priority hierarchy

**Anthropic Research on AI Safety & Interpretability**  
https://www.anthropic.com/research

Key findings:
- Models exhibit limited introspection capabilities
- Alignment can be achieved through constitutional principles
- Circuit tracing reveals shared conceptual reasoning spaces
- Models benefit from explicit reasoning frameworks

**Principled Instructions Paper (arXiv:2312.16171)**  
https://arxiv.org/abs/2312.16171

26 core principles for LLM prompting validated across LLaMA, GPT-3.5/4:
- Be specific and detailed in requirements
- Break complex tasks into sequential steps
- Use positive framing ("do this" not "don't do that")
- Include examples of desired outputs
- Specify output format explicitly
- Use delimiters to mark distinct sections

---

## Documentation Architecture for LLMs

### 1. Document Metadata Block

Every LLM-facing document MUST begin with a metadata block:

```markdown
# [Document Title]

**Document Type**: [meta-documentation | theory | implementation | reference | procedure]
**Target Audience**: [LLMs | humans | both]
**Purpose**: [One-sentence description]
**Last Updated**: YYYY-MM-DD
**Dependencies**: [Links to prerequisite documents]
**Status**: [draft | active | deprecated]
```

**Rationale**: Provides immediate context for document classification and relevance assessment.

### 2. Structural Hierarchy

Use **strict Markdown hierarchy** for logical relationships:

```markdown
# Top-level concept (H1)
## Major section (H2)
### Subsection (H3)
#### Detail level (H4)
```

**Rules**:
- Never skip heading levels (H1 → H3 invalid)
- Use H1 only once per document (title)
- Each section should be self-contained and referenceable
- Keep heading text concise (<10 words)

### 3. Content Formatting Patterns

#### Lists for Discrete Items

```markdown
**Purpose**: Enumerate distinct elements without implicit ordering

- Item one
- Item two
- Item three
```

#### Numbered Lists for Sequences

```markdown
**Purpose**: Steps, procedures, ranked priorities

1. First action
2. Second action (depends on 1)
3. Third action (depends on 2)
```

#### Definition Lists for Term Clarification

```markdown
**Term**: Precise definition or explanation

**Another Term**: Its specific meaning in this context
```

#### Code Blocks with Language Tags

```markdown
**Purpose**: Executable examples, schemas, configurations

```python
def example_function():
    """Docstring explains purpose."""
    return "value"
```
```

#### Tables for Comparative Data

```markdown
| Column A | Column B | Column C |
|----------|----------|----------|
| Value 1  | Value 2  | Value 3  |
```

Use when comparing 3+ dimensions across multiple items.

### 4. XML Delimiters for Complex Content

Use XML-style tags when content needs **strict boundaries** or **metadata**:

```xml
<concept id="n-link-theory" category="graph-theory">
  <definition>
    A deterministic traversal rule on finite directed graphs...
  </definition>
  
  <properties>
    <property name="termination">Guaranteed</property>
    <property name="outcome">HALT or CYCLE</property>
  </properties>
</concept>
```

**When to use**:
- Nested conceptual structures
- Content with multiple attributes
- Cross-referenced sections
- Examples with metadata

### 5. Explicit Relationship Markers

Use explicit markers for logical relationships:

```markdown
**PREREQUISITE**: Must understand [Document A] before this section

**IMPLIES**: This fact leads to [Consequence B]

**CONTRADICTS**: Conflicts with assumption in [Section X]

**ALTERNATIVE**: Another approach is described in [Document Y]

**DEPRECATED**: Replaced by [New Approach Z]
```

---

## Context Window Optimization

### Token Budget Awareness

LLMs have finite context windows. Optimize for token efficiency:

**Priority Order** (most to least important):
1. **Metadata & Purpose** (front-load context)
2. **Core Definitions** (establish vocabulary)
3. **Algorithmic Logic** (procedures, decision trees)
4. **Examples** (illustrative cases)
5. **Edge Cases** (corner conditions)
6. **Historical Context** (why decisions were made)

### Document Length Guidelines

| Document Type | Target Length | Max Length |
|---------------|---------------|------------|
| Meta-documentation | 2000-4000 tokens | 8000 tokens |
| Theory paper | 3000-6000 tokens | 12000 tokens |
| Implementation guide | 1000-3000 tokens | 6000 tokens |
| API reference | 500-1500 tokens | 4000 tokens |
| Procedure | 200-800 tokens | 2000 tokens |

**Exceed max length?** → Split into multiple documents with clear navigation.

### Redundancy Strategy

**AVOID**: Repeating information across documents  
**INSTEAD**: Use explicit cross-references

```markdown
For the complete N-Link algorithm, see [n-link-rule-theory.md#algorithm]

Instead of: "The N-Link algorithm works by selecting the Nth link..."
```

### Caching-Friendly Structure

Place **static, reusable content** at document start:

1. Definitions (rarely change)
2. Core principles (stable)
3. Data schemas (version-controlled)
4. Examples (illustrative)

Place **volatile content** at document end:

1. Status updates
2. Open questions
3. Temporary notes
4. TODOs

---

## Semantic Precision

### Vocabulary Control

**CRITICAL**: Maintain a project glossary (`glossary.md`) with canonical terms.

**Rules**:
- Use **exact** glossary terms (case-sensitive)
- Link first usage of glossary terms: `[N-Link](#n-link-definition)`
- Never use synonyms interchangeably
- Define abbreviations on first use

**Example**:
```markdown
**Correct**: "The pagelinks table contains outlinks."
**Incorrect**: "The pagelinks table has links going out."
```

### Ambiguity Elimination

**AVOID vague language**:
- "might", "could", "possibly" → State probability or conditions
- "some", "several", "many" → Provide numbers or ranges
- "recently", "soon", "later" → Provide dates or versions
- "simple", "complex", "large" → Quantify

**Example**:
```markdown
**Vague**: "The XML dump is large and might take a while to process."

**Precise**: "The enwiki XML dump is ~25GB compressed. Processing takes 4-8 hours on an 8-core system with 16GB RAM."
```

### Imperative vs. Declarative

**Procedures (steps to execute)**: Use imperative mood
```markdown
1. Download the page table from Quarry
2. Build the lookup dictionary
3. Stream the XML dump
```

**Facts (state of reality)**: Use declarative mood
```markdown
The page table contains three columns: page_id, page_title, page_namespace.
```

---

## Self-Referential Documentation Maintenance

### Update Protocols

When modifying documentation, an LLM MUST:

1. **Check Dependencies**: Search for references to modified content
2. **Update Cross-References**: Ensure links remain valid
3. **Increment Version**: Update "Last Updated" timestamp
4. **Log Changes**: Append to document changelog (if present)
5. **Validate Format**: Confirm Markdown renders correctly

### Change Documentation Pattern

Add a changelog section at document end:

```markdown
---

## Changelog

### 2025-12-12
- Added section on XML delimiters
- Clarified token budget guidelines
- Fixed broken link to external-docs.md

### 2025-12-10
- Initial document creation
- Established metadata format
```

### Deprecation Protocol

When information becomes outdated:

**DON'T**: Delete immediately  
**DO**: Mark deprecated with replacement

```markdown
## ~~Old Approach~~ [DEPRECATED 2025-12-12]

This section described using the pagelinks table directly for N-Link traversal.

**REASON FOR DEPRECATION**: pagelinks includes template-expanded links, causing contamination.

**REPLACEMENT**: See [wikipedia-link-graph-decomposition.md#extraction-pipeline]
```

---

## Query Patterns for LLMs

### Efficient Information Retrieval

When an LLM needs information from this codebase:

**STEP 1**: Check `llm-facing-documentation/` directory structure  
**STEP 2**: Read document metadata blocks  
**STEP 3**: Use grep/search for specific terms  
**STEP 4**: Read full relevant sections

**DON'T**: Read entire files sequentially without purpose

### Semantic Search Recommendations

When using semantic search tools:

**GOOD QUERIES**:
- "How to normalize Wikipedia page titles for lookup"
- "Algorithm for stripping templates from wikitext"
- "Definition of N-Link HALT condition"

**BAD QUERIES**:
- "Wikipedia" (too broad)
- "code" (non-specific)
- "how does it work" (ambiguous referent)

### Context Assembly Strategy

When solving a complex task:

1. **Identify subtasks**: Break into discrete components
2. **Find relevant docs**: Use file search + grep
3. **Extract key facts**: Read only necessary sections
4. **Synthesize**: Combine information with explicit citations
5. **Verify**: Cross-check for contradictions

---

## Code Documentation Integration

### Docstring Standards (Python)

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
        
    References:
        See external-docs.md#page-name-normalization for Wikipedia rules
    """
    pass
```

**Key elements**:
- One-sentence summary
- Args/Returns with types
- Algorithm steps (if non-trivial)
- Cross-references to documentation

### Inline Comments (Sparingly)

```python
# Edge case: Some pages like "eBay" have forced lowercase first char
if raw_text in page_lookup:
    return page_lookup[raw_text]
```

Use inline comments ONLY for:
- Edge cases not obvious from code
- Workarounds for external API quirks
- Performance optimizations that look strange

**AVOID**:
```python
# Loop through items
for item in items:
    # Process item
    process(item)
```

---

## Testing Documentation Effectiveness

### Validation Checklist

When creating/updating documentation, verify:

- [ ] Metadata block present and complete
- [ ] All links resolve correctly
- [ ] Code examples are syntactically valid
- [ ] Markdown renders without errors
- [ ] No ambiguous pronouns ("it", "this", "that" without clear antecedent)
- [ ] Technical terms defined or linked to glossary
- [ ] Examples demonstrate edge cases
- [ ] Cross-references use absolute paths

### Readability Metrics for LLMs

**GOOD INDICATORS**:
- Information density: 1 key fact per paragraph
- Consistent terminology: Same term for same concept
- Explicit structure: Headers reveal content without reading body
- Minimal forward references: Definitions before usage

**WARNING SIGNS**:
- Narrative flow: "As we mentioned earlier..." (use links instead)
- Implicit knowledge: "Obviously..." (state explicitly)
- Tangled dependencies: Must read 5+ docs to understand one section

---

## Directory Structure Conventions

### LLM-Facing Documentation Organization

```
llm-facing-documentation/
├── llm-project-management-instructions/  ← Meta-docs about the project
│   ├── documentation-standards.md  ← This file
│   ├── development-workflow.md
│   └── testing-protocols.md
├── theories-proofs-conjectures/  ← Mathematical/conceptual foundations
│   ├── n-link-rule-theory.md
│   └── database-inference-graph-theory.md
├── external-docs/  ← Curated external resources
│   └── external-docs.md
├── implementation-guides/  ← How-to guides for specific tasks
└── api-references/  ← Function/class documentation
```

### Naming Conventions

**Files**: `kebab-case-descriptive-name.md`  
**Directories**: `kebab-case-plural-nouns/`  
**Avoid**: Spaces, underscores, CamelCase in file paths

---

## Communication with Human Users

### When Writing for Humans

If a human asks a question, provide:

1. **Direct answer first** (concise)
2. **Explanation second** (if needed)
3. **Code/examples third** (if applicable)
4. **References last** (links to docs)

### When Updating Documentation

**ALWAYS** inform humans:
- What changed
- Why it changed
- What they need to review (if anything)

**NEVER** make silent updates to critical documentation without user awareness.

---

## Summary: Golden Rules for LLM-Facing Docs

1. **Structure over prose**: Use hierarchy, not narrative flow
2. **Explicit over implicit**: State assumptions, don't assume shared context
3. **Precise over fluent**: Accuracy beats readability
4. **Cross-reference over duplication**: Link, don't repeat
5. **Token-efficient**: Front-load critical information
6. **Self-maintaining**: Include update protocols in every doc type
7. **Semantic consistency**: One term per concept, defined once
8. **Executable examples**: Show, don't just tell
9. **Metadata always**: Every document declares its purpose
10. **Version-aware**: Timestamp all changes

---

## Meta-Note: Using This Document

**For LLMs**: This is your reference manual. When uncertain how to structure documentation, consult this file. When maintaining docs, follow the protocols in "Self-Referential Documentation Maintenance" section.

**For Humans**: This document prioritizes machine parsing over human reading comfort. For human-facing documentation needs, create separate files in a `human-docs/` directory.

---

## Changelog

### 2025-12-12
- Initial creation of documentation standards
- Established metadata format, structural hierarchy, content patterns
- Defined context window optimization strategies
- Set protocols for self-referential maintenance
- Created validation checklist and golden rules

---

## Related Documents

- [Project workspace structure](../../README.md) - Overview of entire project
- [Wikipedia decomposition strategy](../wikipedia-link-graph-decomposition.md) - Major implementation guide
- [N-Link theory](../theories-proofs-conjectures/n-link-rule-theory.md) - Foundational concept
- [External resources](../external-docs/external-docs.md) - Curated third-party documentation

---

**END OF DOCUMENT**
