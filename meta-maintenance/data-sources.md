# External Documentation Resources

**Document Type**: Reference  
**Target Audience**: LLMs researching best practices  
**Purpose**: Curated external resources for LLM prompt engineering, documentation strategies, and Wikipedia technical details  
**Last Updated**: 2025-12-12  
**Status**: Active

---

## LLM Prompt Engineering & Best Practices

### OpenAI Prompt Engineering Guide

**URL**: https://platform.openai.com/docs/guides/prompt-engineering

**Discovered**: 2025-12-12 (documentation system design)

**Key Takeaways**:
- Use clear hierarchical structure (Markdown headers, XML tags)
- Separate Identity/Instructions/Examples/Context into distinct sections
- Position reusable context at the beginning for prompt caching optimization
- Use few-shot examples to establish patterns
- Explicit instructions outperform implicit assumptions
- Developer messages have higher priority than user messages

**Application to This Project**:
- Informed metadata block design (explicit identity)
- Influenced document structure patterns (hierarchy, delimiters)
- Guided token budget optimization strategy (front-load critical content)

---

### Anthropic Research on AI Safety & Interpretability

**URL**: https://www.anthropic.com/research

**Discovered**: 2025-12-12 (documentation system design)

**Key Findings**:
- Models exhibit limited introspection capabilities
- Alignment achieved through constitutional principles
- Circuit tracing reveals shared conceptual reasoning spaces
- Models benefit from explicit reasoning frameworks

**Application to This Project**:
- Established explicit rules over implicit conventions
- Created "golden rules" as constitutional principles for docs
- Designed self-healing protocol with explicit decision logic
- Emphasized semantic consistency (one term per concept)

---

### Principled Instructions Paper (arXiv:2312.16171)

**Full Citation**: 
```
PRINCIPLED INSTRUCTIONS ARE ALL YOU NEED FOR QUESTIONING LLAMA-1/2, GPT-3.5/4
Sondos Mahmoud Bsharat, Aidar Myrzakhan, Zhiqiang Shen
arXiv:2312.16171v3 [cs.CL] 23 May 2024
```

**URL**: https://arxiv.org/abs/2312.16171

**Discovered**: 2025-12-12 (documentation system design)

**Content**: 26 empirically-validated principles for LLM prompting, tested across multiple model families

**Key Principles (Relevant to Documentation)**:
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

**Application to This Project**:
- Influenced "Golden Rules" in documentation-standards.md
- Validated approach to examples-first documentation
- Guided template design (output primers)
- Informed section delimiter strategy (XML, headers, tables)

**Full List**: See [writing-guide.md](./writing-guide.md#research-foundation) for complete 26 principles

---

## Wikipedia & MediaWiki Technical Resources

### Wikipedia Technical Restrictions Page

**URL**: https://en.wikipedia.org/wiki/Wikipedia:Technical_restrictions

**Discovered**: 2025-12-10 (Wikipedia page name research)

**Content**: Canonical rules for page name normalization, forbidden characters, case sensitivity

**Key Rules**:
- First character auto-capitalized (except special pages like "eBay", "iPhone")
- Underscores `_` equivalent to spaces
- Certain characters forbidden: `# < > [ ] | { }`
- Special namespace prefixes: `Wikipedia:`, `User:`, etc.

**Application to This Project**:
- Link normalization algorithm in wikipedia-decomposition pipeline
- Page lookup dictionary design
- Edge case handling for lowercase-first pages

---

### MediaWiki Database Layout

**URL**: https://www.mediawiki.org/wiki/Manual:Database_layout

**Discovered**: 2025-12-10 (pagelinks investigation)

**Content**: Complete schema for Wikipedia database tables

**Key Tables**:
- `page`: Core page registry (page_id, page_title, page_namespace)
- `pagelinks`: Outgoing links from each page
- `categorylinks`: Page-to-category memberships
- `redirect`: Page redirect mappings

**Application to This Project**:
- Informed hybrid extraction strategy (Quarry + XML)
- Clarified pagelinks contamination issue (includes template-expanded links)

---

### Quarry: Public SQL Access to Wikipedia Database

**URL**: https://quarry.wmflabs.org/

**Discovered**: 2025-12-10 (data source research)

**Content**: Web-based SQL query interface for Wikipedia replicas

**Capabilities**:
- Query `page`, `pagelinks`, `categorylinks` tables
- Export results as CSV/TSV
- Historical snapshots available
- Rate-limited but free

**Application to This Project**:
- Primary source for page table (page_id → page_title mapping)
- Alternative to full database download
- Used for quick prototyping and validation queries

**Example Query**:
```sql
SELECT page_id, page_title, page_namespace
FROM page
WHERE page_namespace = 0  -- Main namespace (articles)
LIMIT 1000;
```

---

### Wikipedia XML Dumps

**URL**: https://dumps.wikimedia.org/enwiki/

**Discovered**: 2025-12-10 (pagelinks contamination research)

**Content**: Complete XML dumps of Wikipedia content (pages, revisions, history)

**Key Files**:
- `pages-articles.xml.bz2`: Current article content (~25GB compressed)
- `pages-meta-history.xml.bz2`: Full revision history (~several TB)

**Application to This Project**:
- Primary source for clean link extraction (prose-only links)
- XML parsing required to strip templates before link extraction
- Complements Quarry page table data

---

### MediaWiki API Documentation

**URL**: https://www.mediawiki.org/wiki/API:Main_page

**Discovered**: 2025-12-10 (alternative extraction approaches)

**Content**: RESTful API for programmatic Wikipedia access

**Relevant Endpoints**:
- `action=parse`: Parse wikitext to HTML
- `action=query&prop=links`: Get outgoing links from page
- `action=query&prop=pageprops`: Get page metadata

**Application to This Project**:
- Considered but rejected for bulk extraction (rate limits)
- Useful for single-page validation
- Alternative to XML parsing for small-scale experiments

---

## VSCode & Extension Development

*(No external resources yet - placeholder for future additions)*

---

## Python Development Resources

*(No external resources yet - placeholder for future additions)*

---

## Graph Theory & Algorithms

*(No external resources yet - placeholder for future additions)*

---

## Related Documents

- [writing-guide.md](./writing-guide.md) - Detailed implementation of principles from these sources
- [documentation-standards.md](../llm-facing-documentation/llm-project-management-instructions/documentation-standards.md) - Core rules derived from these sources
- [data-pipeline/wikipedia-decomposition/data-sources.md](../data-pipeline/wikipedia-decomposition/data-sources.md) - Wikipedia-specific technical details

---

## Maintenance Protocol

**Adding New Resources**:
1. Add entry to appropriate section
2. Include: URL, discovery date, key takeaways, application to project
3. Update "Last Updated" metadata
4. Cross-reference to documents that apply the resource

**Deprecating Resources**:
- Mark as `[DEPRECATED YYYY-MM-DD]` but keep for history
- Add reason and replacement resource if applicable

---

## Changelog

### 2025-12-12
- Initial creation
- Extracted external resources from documentation-standards.md
- Organized into categories: LLM best practices, Wikipedia/MediaWiki, future sections
- Added application notes connecting resources to project decisions

---

**END OF DOCUMENT**
