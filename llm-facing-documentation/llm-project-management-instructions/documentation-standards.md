# LLM-Facing Documentation Standards

**Document Type**: Meta-documentation framework  
**Target Audience**: Large Language Models (AI assistants)  
**Purpose**: Core rules for creating, maintaining, and interpreting documentation within this project  
**Last Updated**: 2025-12-12  
**Status**: Active

---

## Core Principle

This project uses **LLM-first documentation** - optimized for machine parsing and reasoning rather than human narrative reading. Documentation should be structured, explicit, and context-efficient.

**For detailed implementation guidance**: See [../../meta-maintenance/writing-guide.md](../../meta-maintenance/writing-guide.md)  
**For external research references**: See [../../meta-maintenance/data-sources.md](../../meta-maintenance/data-sources.md)

---

## Document Metadata Template

Every LLM-facing document MUST begin with this metadata block (copy-paste ready):

```markdown
# [Document Title]

**Document Type**: [meta-documentation | theory | implementation | reference | procedure]
**Target Audience**: [LLMs | humans | both]
**Purpose**: [One-sentence description]
**Last Updated**: YYYY-MM-DD
**Dependencies**: [[linked-doc.md](path/to/doc.md)] (optional)
**Status**: [draft | active | deprecated]
```

**Rationale**: Provides immediate context for document classification and relevance assessment.

---

## Structural Hierarchy

Use **strict Markdown hierarchy** for logical relationships:

```markdown
# Top-level concept (H1) - use once per document
## Major section (H2)
### Subsection (H3)
#### Detail level (H4)
```

**Rules**:
- Never skip heading levels (H1 → H3 invalid)
- Each section should be self-contained and referenceable
- Keep heading text concise (<10 words)

---

## Content Formatting Patterns (Quick Reference)

**For detailed examples and templates**: See [../../meta-maintenance/writing-guide.md#content-formatting-patterns](../../meta-maintenance/writing-guide.md#content-formatting-patterns)

| Pattern | When to Use | Example |
|---------|-------------|---------|
| **Bullet lists** | Discrete items, no ordering | `- Item one\n- Item two` |
| **Numbered lists** | Steps, procedures, sequences | `1. First\n2. Second` |
| **Definition lists** | Vocabulary, terms | `**Term**: Definition` |
| **Code blocks** | Executable examples | ` ```python\ndef func(): pass\n``` ` |
| **Tables** | Compare 3+ dimensions | See below |
| **XML tags** | Nested structures, metadata | `<concept id="...">...</concept>` |

**Tables** - Use when comparing multiple items across multiple dimensions:
```markdown
| Column A | Column B | Column C |
|----------|----------|----------|
| Value 1  | Value 2  | Value 3  |
```

**XML Delimiters** - Use for complex nested content with metadata:
```xml
<concept id="unique-id" category="type">
  <definition>Content here</definition>
  <properties>
    <property name="key">value</property>
  </properties>
</concept>
```

---

## Explicit Relationship Markers

Use these markers to show logical relationships between sections:

```markdown
**PREREQUISITE**: Must read [doc.md](path/to/doc.md) before this section

**IMPLIES**: This fact leads to [consequence]

**CONTRADICTS**: Conflicts with assumption in [section]

**ALTERNATIVE**: Another approach in [doc.md](path/to/doc.md)

**DEPRECATED** (YYYY-MM-DD): Replaced by [new-doc.md](path/to/new-doc.md)
```

---

## Token Budget & Document Length

| Document Type | Target Length | Max Length |
|---------------|---------------|------------|
| Meta-documentation | 2000-4000 tokens | 8000 tokens |
| Theory paper | 3000-6000 tokens | 12000 tokens |
| Implementation guide | 1000-3000 tokens | 6000 tokens |
| API reference | 500-1500 tokens | 4000 tokens |
| Procedure | 200-800 tokens | 2000 tokens |

**Exceed max length?** → Split into multiple documents with clear navigation.

**Token Estimation**: ~1 token = 0.75 words = 4 characters (English text)

**Priority Order** (front-load critical content):
1. Metadata & Purpose
2. Core Definitions
3. Algorithmic Logic
4. Examples
5. Edge Cases
6. Historical Context

---

## Semantic Precision Rules

**Vocabulary Control**:
- Use **exact** canonical terms consistently (case-sensitive)
- Link first usage: `[Term](#term-definition)`
- Never use synonyms interchangeably
- Define abbreviations on first use

**Eliminate Ambiguity**:

| Vague | Precise |
|-------|---------|
| "might", "could", "possibly" | State probability or conditions |
| "some", "several", "many" | Provide numbers or ranges |
| "recently", "soon", "later" | Provide dates or versions |
| "simple", "complex", "large" | Quantify with metrics |
| "it", "this", "that" (without antecedent) | Repeat noun or use [concept-name] |

**Example**:
- **Vague**: "The XML dump is large and might take a while to process."
- **Precise**: "The enwiki XML dump is ~25GB compressed. Processing takes 4-8 hours on an 8-core system with 16GB RAM."

---

## Code Documentation Standards

**Python Docstring Template** (copy-paste ready):
```python
def function_name(param1: Type1, param2: Type2) -> ReturnType:
    """
    One-sentence summary of function purpose.
    
    Args:
        param1: Description of first parameter
        param2: Description of second parameter
        
    Returns:
        Description of return value
        
    Algorithm:
        1. Step one
        2. Step two
        
    References:
        See [doc.md](path/to/doc.md#section) for details
    """
    pass
```

**Inline Comments** - Use ONLY for:
- Edge cases not obvious from code
- Workarounds for external API quirks
- Performance optimizations that look strange

**For complete templates and examples**: See [../../meta-maintenance/writing-guide.md#code-documentation-integration](../../meta-maintenance/writing-guide.md#code-documentation-integration)

---

## Update & Maintenance Protocols

When modifying documentation, an LLM MUST:

1. **Check Dependencies**: Search for references to modified content
2. **Update Cross-References**: Ensure links remain valid
3. **Increment Version**: Update "Last Updated" timestamp
4. **Log Changes**: Append to document changelog (if present)
5. **Validate Format**: Confirm Markdown renders correctly

**Changelog Pattern** (add to document end):
```markdown
---

## Changelog

### YYYY-MM-DD
- Added section on X
- Fixed broken link to Y
- Clarified Z guidelines

### YYYY-MM-DD
- Initial document creation
```

**Deprecation Protocol**:
- Mark section with `## ~~Old Approach~~ [DEPRECATED YYYY-MM-DD]`
- State reason for deprecation
- Link to replacement: `**REPLACEMENT**: See [new-doc.md](path/to/doc.md)`

**For complete maintenance procedures**: See [project-management-practices.md](./project-management-practices.md)

---

## Validation Checklist

When creating/updating documentation:

- [ ] Metadata block present and complete
- [ ] All links resolve correctly
- [ ] Code examples are syntactically valid
- [ ] Markdown renders without errors
- [ ] No ambiguous pronouns without clear antecedent
- [ ] Technical terms defined or linked
- [ ] Cross-references use absolute paths or workspace-relative paths

---

## Directory Structure & Naming

**Files**: `kebab-case-descriptive-name.md`  
**Directories**: `kebab-case-plural-nouns/`  
**Avoid**: Spaces, underscores, CamelCase in file paths

**Standard Structure**:
```
llm-facing-documentation/       ← Tier 1: Read every session
├── llm-project-management-instructions/
│   ├── documentation-standards.md  ← This file
│   └── project-management-practices.md
├── theories-proofs-conjectures/
└── project-timeline.md

meta-maintenance/               ← Tier 2: Documentation system details
├── implementation.md
├── writing-guide.md
├── data-sources.md
├── session-log.md
└── future.md

data-pipeline/                  ← Tier 2: Directory-based discovery
├── wikipedia-decomposition/
│   ├── implementation.md
│   └── data-sources.md
└── ...other-pipelines/
```

---

## Golden Rules for LLM-Facing Documentation

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

## Bootstrap Instructions for New LLMs

**Starting a new session?**

1. Read [project-timeline.md](../project-timeline.md) - Recent project history
2. Read [project-management-practices.md](./project-management-practices.md) - Maintenance patterns
3. Read this document - Documentation standards
4. Navigate to directory you're working in
5. Read directory-specific documentation (Tier 2)

**Creating new documentation?**

1. Copy metadata template from this document (top section)
2. Consult [../../meta-maintenance/writing-guide.md](../../meta-maintenance/writing-guide.md) for detailed patterns
3. Follow golden rules above
4. Validate using checklist before committing

**Need detailed examples or research references?**

- See [../../meta-maintenance/writing-guide.md](../../meta-maintenance/writing-guide.md) - Complete guide with examples
- See [../../meta-maintenance/data-sources.md](../../meta-maintenance/data-sources.md) - External research links
- See [../../meta-maintenance/implementation.md](../../meta-maintenance/implementation.md) - Documentation system architecture

---

## Related Documents

- [project-management-practices.md](./project-management-practices.md) - How to maintain project documentation
- [../../meta-maintenance/writing-guide.md](../../meta-maintenance/writing-guide.md) - Detailed examples and templates
- [../../meta-maintenance/data-sources.md](../../meta-maintenance/data-sources.md) - External research references
- [../../meta-maintenance/implementation.md](../../meta-maintenance/implementation.md) - Documentation system architecture
- [../project-timeline.md](../project-timeline.md) - Project history and milestones

---

## Changelog

### 2025-12-12 (Second Update)
- **Token budget optimization**: Compressed from 20k+ tokens to ~3k tokens
- Extracted detailed examples to [../../meta-maintenance/writing-guide.md](../../meta-maintenance/writing-guide.md)
- Extracted external research to [../../meta-maintenance/data-sources.md](../../meta-maintenance/data-sources.md)
- Added bootstrap instructions for new LLM sessions
- Converted detailed patterns to quick-reference tables with pointers
- Added copy-paste ready templates (metadata, docstring)

### 2025-12-12 (Initial)
- Initial creation of documentation standards
- Established metadata format, structural hierarchy, content patterns
- Defined context window optimization strategies
- Set protocols for self-referential maintenance
- Created validation checklist and golden rules

---

**END OF DOCUMENT**
