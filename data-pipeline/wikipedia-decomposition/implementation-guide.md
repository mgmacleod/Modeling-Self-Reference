# Wikipedia Link Graph Decomposition - Implementation Guide

**Document Type**: Technical Specification  
**Target Audience**: LLMs + Developers  
**Purpose**: Complete extraction pipeline from Wikipedia XML to clean N-Link dataset  
**Last Updated**: 2025-12-12  
**Dependencies**: [data-sources.md](./data-sources.md)  
**Status**: Design Complete - Implementation Pending

---

## Overview

Complete extraction from enwiki XML dumps with full metadata preservation. This decomposition approach parses the massive XML **once**, extracts **everything** with proper tags, and lets downstream tools filter what they need.

**Philosophy**: Expensive parsing operation done once; cheap storage preserved forever; flexible downstream analysis.

---

## Output Files Structure

```
wikipedia_decomposition/
├── metadata/
│   ├── pages.tsv              # All pages with flags
│   ├── redirects.tsv          # page_id → target_title
│   ├── disambiguations.tsv    # page_id list
│   └── decomposition_log.json # Extraction metadata
│
├── links/
│   ├── links_ordered.tsv      # page_id → [link_id:pos, ...]
│   ├── links_unmatched.tsv    # page_id → [raw_text:pos, ...]
│   └── links_stats.tsv        # page_id → link_count, match_rate
│
├── content/
│   ├── wikitext_raw/          # Optional: page_id.txt (original)
│   ├── wikitext_clean/        # Optional: page_id.txt (templates stripped)
│   └── templates_extracted/   # Optional: page_id_templates.json
│
└── quarry_source/
    ├── page_table.tsv         # Downloaded from Quarry
    ├── page_props.tsv         # Downloaded from Quarry
    └── redirect_table.tsv     # Downloaded from Quarry
```

---

## Core File Specifications

### `pages.tsv`

Complete metadata for all extracted pages.

**Format**: Tab-separated values, UTF-8 encoded

**Columns**:
```tsv
page_id	page_title	namespace	is_redirect	is_disambiguation	is_stub	byte_size	link_count	extraction_status
```

**Example**:
```tsv
page_id	page_title	namespace	is_redirect	is_disambiguation	is_stub	byte_size	link_count	extraction_status
12	Anarchism	0	false	false	false	82456	342	success
89342	Snow	0	false	false	false	45123	187	success
175623	SNOW	0	false	true	false	1205	23	success
892	EBay	0	false	false	false	34567	156	success
```

**Field Descriptions**:
- `page_id`: Integer, primary key from Wikipedia `page` table
- `page_title`: String, canonical page title (exact case, underscores preserved)
- `namespace`: Integer, 0 = main article namespace
- `is_redirect`: Boolean, true if redirect page
- `is_disambiguation`: Boolean, true if disambiguation page
- `is_stub`: Boolean, true if stub article
- `byte_size`: Integer, size of raw wikitext in bytes
- `link_count`: Integer, number of internal links found
- `extraction_status`: Enum: `success`, `partial`, `failed`, `skipped`

---

### `links_ordered.tsv`

Ordered link sequences for each page, preserving document order from prose.

**Format**: Tab-separated values, UTF-8 encoded

**Columns**:
```tsv
page_id	link_sequence
```

**Link Sequence Format**: `target_page_id:byte_position,target_page_id:byte_position,...`

**Example**:
```tsv
page_id	link_sequence
12	8091:145,9382:567,12890:892,8091:1234,23456:1890
89342	175623:234,8091:456,23456:789,8091:1023
175623	89342:120,89342:450,89342:680
```

**Properties**:
- Sorted by byte position (ascending)
- Multiple links to same target preserved with different positions
- Position = byte offset in **cleaned** wikitext (post-template-stripping)
- Allows duplicate target_ids to track multiple mentions

---

### `links_unmatched.tsv`

Failed link matches for debugging and redlink analysis.

**Format**: Tab-separated values, UTF-8 encoded

**Columns**:
```tsv
page_id	unmatched_links
```

**Unmatched Links Format**: JSON array of objects `[{"text": "...", "pos": 123}, ...]`

**Example**:
```tsv
page_id	unmatched_links
12	[{"text":"some obscure thing","pos":456},{"text":"Red link","pos":789}]
89342	[{"text":"Future article","pos":234}]
```

**Use Cases**:
- Identify redlinks (links to non-existent pages)
- Debug parsing edge cases
- Track temporal changes (pages created after decomposition)
- Find malformed wikitext

---

### `redirects.tsv`

Redirect mappings extracted from pages.

**Format**: Tab-separated values, UTF-8 encoded

**Columns**:
```tsv
page_id	page_title	redirect_target_title
```

**Example**:
```tsv
page_id	page_title	redirect_target_title
456789	USA	United_States
234567	Colour	Color
891234	GWB	George_W._Bush
```

---

### `disambiguations.tsv`

List of disambiguation pages for separate analysis.

**Format**: Tab-separated values, UTF-8 encoded

**Columns**:
```tsv
page_id	page_title	disambiguation_links_count
```

**Example**:
```tsv
page_id	page_title	disambiguation_links_count
175623	SNOW	3
234891	Mercury_(disambiguation)	12
```

---

### `decomposition_log.json`

Complete provenance and statistics for the extraction.

**Example**:
```json
{
  "extraction_date": "2025-12-12T10:30:00Z",
  "xml_source": "enwiki-20251201-pages-articles-multistream.xml.bz2",
  "xml_sha256": "abc123...",
  "xml_url": "https://dumps.wikimedia.org/enwiki/20251201/",
  "quarry_query_date": "2025-12-10",
  "page_table_count": 6847301,
  
  "extraction_config": {
    "strip_templates": true,
    "strip_refs": true,
    "strip_comments": true,
    "strip_tables": false,
    "strip_galleries": true,
    "link_pattern": "\\[\\[([^|\\]]+)(?:\\|[^\\]]+)?\\]\\]",
    "template_pattern": "\\{\\{[^}]+\\}\\}",
    "normalization_rules": [
      "Exact match priority",
      "First-char capitalization fallback",
      "Underscore to space conversion",
      "Case-insensitive final fallback"
    ]
  },
  
  "statistics": {
    "pages_processed": 6847301,
    "pages_successful": 6842156,
    "pages_partial": 3012,
    "pages_failed": 5145,
    "pages_skipped": 0,
    
    "links_matched": 245891023,
    "links_unmatched": 2341567,
    "match_rate": 0.991,
    
    "redirects_found": 892345,
    "disambiguations_found": 234567,
    "stubs_found": 1234567,
    
    "avg_links_per_page": 35.9,
    "median_links_per_page": 23,
    "max_links_single_page": 2341,
    
    "processing_time_seconds": 28934,
    "pages_per_second": 236.5
  },
  
  "version_info": {
    "schema_version": "1.0.0",
    "extractor_version": "1.0.0",
    "python_version": "3.11.5"
  },
  
  "recomposition_instructions": "See decomposition README for filtering strategies"
}
```

---

## Extraction Pipeline

### Step 1: Download Quarry Tables

```sql
-- 1. Main page table (all articles)
SELECT page_id, page_title, page_namespace, page_is_redirect, page_len
FROM page
WHERE page_namespace = 0;
-- Save as: quarry_source/page_table.tsv

-- 2. Page properties (for disambiguation detection)
SELECT pp_page, pp_propname
FROM page_props
WHERE pp_propname IN ('disambiguation', 'stub');
-- Save as: quarry_source/page_props.tsv

-- 3. Redirect targets
SELECT rd_from, rd_title
FROM redirect
WHERE rd_namespace = 0;
-- Save as: quarry_source/redirect_table.tsv
```

### Step 2: Build Lookup Structures

```python
# Load page table
page_lookup = {}  # {title: page_id}
page_lookup_lower = {}  # {title.lower(): [page_ids]} for fallback
page_metadata = {}  # {page_id: {title, is_redirect, ...}}

for row in load_tsv('quarry_source/page_table.tsv'):
    page_id = int(row['page_id'])
    title = row['page_title']
    
    page_lookup[title] = page_id
    page_lookup_lower.setdefault(title.lower(), []).append(page_id)
    page_metadata[page_id] = row

# Load disambiguation flags
disambig_set = set()
stub_set = set()
for row in load_tsv('quarry_source/page_props.tsv'):
    if row['pp_propname'] == 'disambiguation':
        disambig_set.add(int(row['pp_page']))
    elif row['pp_propname'] == 'stub':
        stub_set.add(int(row['pp_page']))
```

### Step 3: Template Stripper

```python
def strip_templates(wikitext):
    """Remove {{...}} blocks recursively, handling nested templates."""
    result = wikitext
    max_iterations = 100  # Prevent infinite loops
    
    for _ in range(max_iterations):
        changed = False
        depth = 0
        start = None
        
        i = 0
        while i < len(result):
            if i < len(result) - 1 and result[i:i+2] == '{{':
                if depth == 0:
                    start = i
                depth += 1
                i += 2
            elif i < len(result) - 1 and result[i:i+2] == '}}':
                depth -= 1
                if depth == 0 and start is not None:
                    result = result[:start] + result[i+2:]
                    changed = True
                    break
                i += 2
            else:
                i += 1
        
        if not changed:
            break
    
    return result

def strip_refs(wikitext):
    """Remove <ref>...</ref> blocks."""
    import re
    return re.sub(r'<ref[^>]*>.*?</ref>', '', wikitext, flags=re.DOTALL)

def strip_comments(wikitext):
    """Remove <!-- ... --> comments."""
    import re
    return re.sub(r'<!--.*?-->', '', wikitext, flags=re.DOTALL)
```

### Step 4: Link Extractor

```python
import re

def extract_links_with_positions(wikitext):
    """Extract [[link]] patterns with byte positions."""
    pattern = r'\[\[([^|\]]+)(?:\|[^\]]+)?\]\]'
    links = []
    
    for match in re.finditer(pattern, wikitext):
        link_text = match.group(1).strip()
        position = match.start()
        links.append((link_text, position))
    
    return links
```

### Step 5: Link Normalizer & Matcher

```python
def normalize_and_match(link_text, page_lookup, page_lookup_lower):
    """
    Normalize link text and match against page table.
    Returns: page_id (int) or None
    """
    # Step 1: Normalize
    normalized = link_text.replace('_', ' ').strip()
    
    # Step 2: Try exact match
    if normalized in page_lookup:
        return page_lookup[normalized]
    
    # Step 3: Try first-char capitalization
    if normalized:
        capitalized = normalized[0].upper() + normalized[1:]
        if capitalized in page_lookup:
            return page_lookup[capitalized]
    
    # Step 4: Case-insensitive fallback
    lower = normalized.lower()
    if lower in page_lookup_lower:
        candidates = page_lookup_lower[lower]
        if len(candidates) == 1:
            return candidates[0]
        # Multiple matches - ambiguous, log for review
        return None
    
    return None
```

### Step 6: Main Processing Loop

```python
from xml.etree import ElementTree as ET
import bz2

def process_xml_dump(xml_path, page_lookup, page_lookup_lower, output_dir):
    """Stream process XML dump."""
    
    pages_output = open(f'{output_dir}/metadata/pages.tsv', 'w', encoding='utf-8')
    links_output = open(f'{output_dir}/links/links_ordered.tsv', 'w', encoding='utf-8')
    unmatched_output = open(f'{output_dir}/links/links_unmatched.tsv', 'w', encoding='utf-8')
    
    # Write headers
    pages_output.write('page_id\tpage_title\tnamespace\tis_redirect\tis_disambiguation\tis_stub\tbyte_size\tlink_count\textraction_status\n')
    links_output.write('page_id\tlink_sequence\n')
    unmatched_output.write('page_id\tunmatched_links\n')
    
    stats = {'processed': 0, 'matched': 0, 'unmatched': 0}
    
    # Stream XML (pseudo-code - actual implementation uses iterparse)
    for page in stream_xml(xml_path):
        page_id = page['id']
        title = page['title']
        wikitext = page['text']
        
        # Clean wikitext
        clean = strip_comments(wikitext)
        clean = strip_templates(clean)
        clean = strip_refs(clean)
        
        # Extract links
        raw_links = extract_links_with_positions(clean)
        
        matched_links = []
        unmatched_links = []
        
        for link_text, pos in raw_links:
            matched_id = normalize_and_match(link_text, page_lookup, page_lookup_lower)
            if matched_id:
                matched_links.append(f'{matched_id}:{pos}')
                stats['matched'] += 1
            else:
                unmatched_links.append({'text': link_text, 'pos': pos})
                stats['unmatched'] += 1
        
        # Write outputs
        pages_output.write(f'{page_id}\t{title}\t...\n')
        links_output.write(f'{page_id}\t{",".join(matched_links)}\n')
        
        if unmatched_links:
            import json
            unmatched_output.write(f'{page_id}\t{json.dumps(unmatched_links)}\n')
        
        stats['processed'] += 1
        
        if stats['processed'] % 10000 == 0:
            print(f"Processed {stats['processed']} pages...")
    
    return stats
```

---

## Recomposition Strategies

### N-Link Analysis (Strict - Prose Only)

```python
import pandas as pd

# Load decomposition
pages = pd.read_csv('metadata/pages.tsv', sep='\t')
links = pd.read_csv('links/links_ordered.tsv', sep='\t')

# Filter: main namespace, not redirects, not disambiguation
valid_pages = pages[
    (pages['namespace'] == 0) & 
    (~pages['is_redirect']) & 
    (~pages['is_disambiguation'])
]

# Build N-Link graph
n_link_graph = {}
for _, row in valid_pages.iterrows():
    page_id = row['page_id']
    link_seq = links[links['page_id'] == page_id]['link_sequence'].values[0]
    
    # Parse link sequence
    link_ids = [int(x.split(':')[0]) for x in link_seq.split(',') if x]
    n_link_graph[page_id] = link_ids

# Now run N-Link traversal
def n_link_traverse(start_page, n, graph):
    current = start_page
    visited = set()
    path = [current]
    
    while current not in visited:
        visited.add(current)
        if current not in graph or len(graph[current]) < n:
            return path, 'HALT'
        
        next_page = graph[current][n-1]  # nth link (0-indexed)
        path.append(next_page)
        current = next_page
    
    return path, 'CYCLE'
```

### Redirect Resolution Layer

```python
# Load redirects
redirects = pd.read_csv('metadata/redirects.tsv', sep='\t')
redirect_map = dict(zip(redirects['page_id'], redirects['redirect_target_title']))

# Apply resolution to link sequences
def resolve_redirects(link_ids, redirect_map, page_lookup):
    """Resolve redirect chains in link sequences."""
    resolved = []
    for link_id in link_ids:
        current = link_id
        seen = set()
        
        # Follow redirect chain
        while current in redirect_map and current not in seen:
            seen.add(current)
            target_title = redirect_map[current]
            current = page_lookup.get(target_title, current)
        
        resolved.append(current)
    
    return resolved
```

### Disambiguation Research

```python
# Load disambiguation pages
disambig_pages = pages[pages['is_disambiguation']]

# Analyze patterns
for _, page in disambig_pages.iterrows():
    page_id = page['page_id']
    title = page['page_title']
    
    # Get links from disambiguation page
    link_seq = links[links['page_id'] == page_id]['link_sequence'].values[0]
    link_ids = [int(x.split(':')[0]) for x in link_seq.split(',') if x]
    
    # These are the ambiguous targets
    print(f"'{title}' disambiguates to: {link_ids}")
```

---

## File Format Specifications

### TSV Encoding Standards

- **Character Encoding**: UTF-8 (no BOM)
- **Delimiter**: Tab character (`\t`, 0x09)
- **Line Terminator**: Unix LF (`\n`, 0x0A)
- **Header Row**: First line contains column names
- **Quoting**: Fields quoted only if they contain tabs, newlines, or quotes
- **Escaping**: Quotes escaped as `""` (double-quote)
- **Null Values**: Empty string for missing values
- **Boolean Values**: Lowercase `true` / `false`

### Size Estimates

Based on enwiki (English Wikipedia) as of December 2025:

| File | Compressed | Uncompressed |
|------|------------|--------------|
| pages.tsv | ~80MB | ~500MB |
| links_ordered.tsv | ~1.2GB | ~8GB |
| links_unmatched.tsv | ~30MB | ~200MB |
| redirects.tsv | ~15MB | ~80MB |
| disambiguations.tsv | ~5MB | ~25MB |
| **Total** | **~1.4GB** | **~9GB** |

Storage recommendation: Keep both compressed and uncompressed versions.

---

## Versioning & Updates

### Version Naming Convention

```
wikipedia_decomposition_YYYYMMDD_vX/
```

Example: `wikipedia_decomposition_20251201_v1/`

### When to Re-extract

- **Monthly**: Wikipedia dump updates monthly
- **Config Changes**: Different template stripping settings
- **Schema Updates**: New fields added to decomposition

### Incremental Updates

For small updates (new pages added since last dump):
1. Keep base decomposition
2. Extract delta pages only
3. Merge with append strategy

---

## Quality Assurance

### Validation Checks

```python
# 1. Link count consistency
pages_df = pd.read_csv('metadata/pages.tsv', sep='\t')
links_df = pd.read_csv('links/links_ordered.tsv', sep='\t')

for _, page in pages_df.iterrows():
    declared_count = page['link_count']
    link_seq = links_df[links_df['page_id'] == page['page_id']]['link_sequence'].values[0]
    actual_count = len(link_seq.split(',')) if link_seq else 0
    
    assert declared_count == actual_count, f"Mismatch for page {page['page_id']}"

# 2. No self-loops in links
for _, row in links_df.iterrows():
    page_id = row['page_id']
    link_ids = [int(x.split(':')[0]) for x in row['link_sequence'].split(',') if x]
    assert page_id not in link_ids, f"Self-loop detected: {page_id}"

# 3. All link targets exist
all_page_ids = set(pages_df['page_id'])
for _, row in links_df.iterrows():
    link_ids = [int(x.split(':')[0]) for x in row['link_sequence'].split(',') if x]
    for link_id in link_ids:
        assert link_id in all_page_ids, f"Dangling link: {link_id}"
```

### Match Rate Targets

- **Good**: >95% of links matched
- **Acceptable**: 90-95% matched
- **Investigate**: <90% matched (likely parsing issues)

---

## Use Cases

### 1. N-Link Basin Mapping
Filter to prose-only links, run N-Link traversal, compute basin partitions.

### 2. Link Graph Analysis
Compute PageRank, betweenness centrality, community detection on full graph.

### 3. Disambiguation Studies
Analyze ambiguous terms, common naming conflicts, semantic overlap.

### 4. Temporal Studies
Compare decompositions across monthly dumps to track Wikipedia growth.

### 5. Redirect Chain Analysis
Identify long redirect chains, circular redirects, orphaned redirects.

### 6. Redlink Mining
From `links_unmatched.tsv`, identify most-linked non-existent pages (future article candidates).

---

## Performance Optimization

### Memory-Efficient Processing

- **Stream XML**: Use `xml.etree.ElementTree.iterparse()` to avoid loading entire dump
- **Chunked Output**: Write to disk incrementally, don't accumulate in memory
- **Page Table Index**: Use hash maps for O(1) lookups

### Parallelization

- **Multi-process**: Split XML dump by page_id ranges, process in parallel
- **Caution**: Ensure consistent ordering in output files

### Disk I/O

- **SSD Recommended**: Random access to XML index file benefits from SSD
- **Compression**: Use `gzip` or `zstd` for intermediate files

---

## Dependencies

### Required Data Sources

1. **Wikipedia XML Dump**: `enwiki-YYYYMMDD-pages-articles-multistream.xml.bz2`
2. **XML Index File**: `enwiki-YYYYMMDD-pages-articles-multistream-index.txt.bz2`
3. **Quarry Access**: https://quarry.wmcloud.org/ (free Wikimedia account required)

### Software Requirements

- Python 3.10+
- Libraries: `pandas`, `lxml`, `regex`
- Disk Space: 50GB+ free (for extraction + output)
- RAM: 16GB+ recommended

---

## Troubleshooting

### Issue: Low Match Rate

**Symptoms**: <90% links matched

**Causes**:
- Quarry page table out of sync with XML dump dates
- Template stripping too aggressive (removing valid links)
- Case normalization failures

**Solutions**:
- Ensure Quarry query date ≤ XML dump date
- Review `links_unmatched.tsv` for patterns
- Add logging to normalization function

### Issue: Memory Exhaustion

**Symptoms**: Process killed by OS

**Causes**:
- Loading entire XML into memory
- Accumulating links list without flushing

**Solutions**:
- Use streaming XML parser
- Write outputs incrementally
- Process in page_id chunks

### Issue: Missing Disambiguation Flags

**Symptoms**: Disambiguation pages not filtered

**Causes**:
- `page_props` table query incomplete
- Some disambig pages lack database flag

**Solutions**:
- Also check title suffix `_(disambiguation)`
- Query `categorylinks` table for `All_disambiguation_pages`

---

## License & Attribution

This decomposition methodology is released under CC-BY-SA 4.0, compatible with Wikipedia's content license.

**Attribution**: When publishing research using this decomposition, cite:
- Wikipedia data source: Wikimedia Foundation dumps
- Decomposition methodology: [Your project]

---

## Contact & Support

For issues with this decomposition schema, consult:
- MediaWiki API Documentation: https://www.mediawiki.org/
- Quarry Support: https://quarry.wmcloud.org/
- Wikipedia Database Documentation: https://www.mediawiki.org/wiki/Manual:Database_layout

---

**END OF DOCUMENT**
