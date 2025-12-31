# Wikipedia Link Graph Decomposition - Implementation Guide

**Document Type**: Technical Specification  
**Target Audience**: LLMs + Developers  
**Purpose**: Complete extraction pipeline from Wikipedia XML to clean N-Link dataset  
**Last Updated**: 2025-12-29  
**Dependencies**: [data-sources.md](./data-sources.md)  
**Status**: Complete - All extraction scripts implemented and run

---

## Quick Start: Running the Pipeline

If you're starting from scratch with a fresh Wikipedia dump, run scripts in this order:

### Prerequisites

```bash
# From repository root
python -m venv .venv
.venv/Scripts/activate  # Windows
pip install pyarrow duckdb pandas
```

### Step 1: Download Data

Download from https://dumps.wikimedia.org/enwiki/YYYYMMDD/ to `data/wikipedia/raw/`:
- `enwiki-YYYYMMDD-pages-articles-multistream*.xml.bz2` (all 69 parts)
- `enwiki-YYYYMMDD-page.sql.gz`
- `enwiki-YYYYMMDD-redirect.sql.gz`
- `enwiki-YYYYMMDD-page_props.sql.gz`

### Step 2: Run Extraction Scripts

```bash
cd data-pipeline/wikipedia-decomposition/scripts

# 1. Parse SQL dumps → page metadata (pages, redirects, disambig)
python parse-sql-to-parquet.py          # ~2 min, outputs 3 parquet files

# 2. Extract prose-only links from XML (strips templates/tables/refs)
python parse-xml-prose-links.py         # ~53 min, outputs links_prose.parquet

# 3. Resolve link titles → page IDs with order preserved
python build-nlink-sequences-v3.py      # ~5 min, outputs nlink_sequences.parquet
```

### Step 3: Verify Output

```bash
python quick-stats.py                   # Run verification queries
```

### Output Summary

| File | Rows | Size | Purpose |
|------|------|------|---------|
| `pages.parquet` | 64.7M | 985 MB | Page metadata |
| `redirects.parquet` | 15.0M | 189 MB | Redirect mappings |
| `disambig_pages.parquet` | 376K | 1.8 MB | Disambiguation IDs |
| `links_prose.parquet` | 214.2M | 1.67 GB | Prose-only links with positions |
| `nlink_sequences.parquet` | 18.0M | 686 MB | **N-Link sequences** (final output) |

**Total**: ~3.5 GB processed data

---

## Overview

Complete extraction from enwiki XML dumps with full metadata preservation. This decomposition approach parses the massive XML **once**, extracts **everything** with proper tags, and lets downstream tools filter what they need.

**Philosophy**: Expensive parsing operation done once; cheap storage preserved forever; flexible downstream analysis.

---

## Data Directory Structure

All data stored in `data/wikipedia/` (gitignored, see `.gitkeep` for documentation).

```
data/wikipedia/
├── raw/                           # Downloaded dumps (~100GB uncompressed)
│   ├── enwiki-20251220-pages-articles-multistream*.xml  # 69 XML files
│   ├── enwiki-20251220-page.sql.gz
│   ├── enwiki-20251220-redirect.sql.gz
│   └── enwiki-20251220-page_props.sql.gz
│
└── processed/                     # Extracted data (~3.5GB total)
    ├── pages.parquet              # 64.7M rows, 985 MB - all pages
    ├── redirects.parquet          # 15.0M rows, 189 MB - redirect mappings
    ├── disambig_pages.parquet     # 376K rows, 1.8 MB - disambiguation IDs
    ├── links_prose.parquet        # 214.2M rows, 1.67 GB - prose links w/ position
    └── nlink_sequences.parquet    # 18.0M rows, 686 MB - N-Link sequences (FINAL)
```

**Legacy Files** (from earlier pipeline, not needed for N-Link):
- `links.parquet` - Raw links without position (353M rows, 2.84 GB)
- `links_resolved.parquet` - Resolved edges without order (237M rows, 1.39 GB)

**Storage Format**: Parquet (columnar, compressed, portable) + DuckDB for queries.

**Rationale**: Parquet enables efficient columnar access and compression. DuckDB provides SQL queries without server overhead. Both are industry-standard for analytical workloads.

---

## Core File Specifications

### `pages.parquet`

Complete metadata for all pages from the `page` SQL dump.

**Format**: Apache Parquet (ZSTD compressed)

**Schema** (actual):
```
page_id: int64 (primary key)
namespace: int32 (0 = main article)
title: string (canonical, underscores replaced with spaces)
is_redirect: bool
```

**Statistics**:
- Total rows: 64,709,137
- File size: 984.6 MB
- NS0 (main) pages: 18,803,531
- NS0 content articles (non-redirect): 7,109,811

**Example** (as DataFrame):
```
   page_id  namespace                 title  is_redirect
0       10          0   AccessibleComputing         True
1       12          0             Anarchism        False
2       13          0    AfghanistanHistory         True
3       14          0  AfghanistanGeography         True
```

**Field Descriptions**:
- `page_id`: Primary key from Wikipedia `page` table
- `namespace`: 0 = main article, 1 = talk, 14 = category, etc.
- `title`: Page title with underscores converted to spaces
- `is_redirect`: True if page is a redirect

---

### `links.parquet`

Raw extracted wikilinks from XML article content (before title resolution).

**Format**: Apache Parquet (ZSTD compressed)

**Schema** (actual):
```
from_id: int64    # Source page ID
to_title: string  # Target page title (as written in [[...]])
```

**Statistics**:
- Total rows: 353,449,165
- File size: 2.84 GB
- Extraction time: 31 minutes (69 XML files)

**Example** (as DataFrame):
```
   from_id                                    to_title
0       10                      Computer_accessibility
1       12                        Political_philosophy
2       12                          Political_movement
3       12                                   Authority
```

**Properties**:
- One row per link occurrence (duplicates preserved)
- `to_title` is raw link target before `|` or `#`
- Links extracted with regex: `\[\[([^\[\]|#]+)`
- Includes links to redirects, non-existent pages, etc.

---

### `links_resolved.parquet`

Resolved link graph with page IDs for both source and target.

**Format**: Apache Parquet (ZSTD compressed)

**Schema** (actual):
```
from_id: int64  # Source page ID
to_id: int64    # Target page ID (resolved)
```

**Statistics**:
- Total rows: 237,645,648
- File size: 1.39 GB
- Resolution time: 17.6 seconds

**Example** (as DataFrame):
```
   from_id     to_id
0  4205775  69991491
1  4205840    459132
2  4205756       698
3  4205840  23785316
```

**Resolution Process**:
1. Join `to_title` with `pages.title` for direct matches
2. Follow redirects via `redirect_lookup` table
3. Exclude: disambiguation pages, self-links, non-existent targets
4. Deduplicate edges (same from→to only appears once)

**Filtering Applied**:
- ✅ Links to content pages (NS0, non-redirect)
- ✅ Redirects resolved to final target
- ❌ Links to non-existent pages (redlinks)
- ❌ Links to disambiguation pages
- ❌ Self-links (from_id = to_id)

**Note**: This file does NOT preserve link order. For N-Link experiments, use `nlink_sequences.parquet`.

---

### `links_prose.parquet`

Prose-only wikilinks with position preserved (templates, tables, refs stripped).

**Format**: Apache Parquet (ZSTD compressed)

**Schema**:
```
from_id: int64        # Source page ID
link_position: int32  # Character position in cleaned prose
to_title: string      # Target page title (before resolution)
```

**Statistics**:
- Total rows: 214,239,496
- File size: 1.67 GB
- Extraction time: 53 minutes

**Pre-processing Applied**:
- ✅ Templates stripped (`{{...}}`)
- ✅ Tables stripped (`{|...|}`)
- ✅ References stripped (`<ref>...</ref>`)
- ✅ Comments stripped (`<!--...-->`)
- ✅ Galleries, nowiki, math, code tags stripped

**Why Prose-Only?**: Templates/tables contain reused components (navboxes, infoboxes) that create artificial "gravity wells" in N-Link traversal. Prose links reflect actual editorial intent.

---

### `nlink_sequences.parquet` ⭐

**THE FINAL OUTPUT FOR N-LINK THEORY**

Ordered link sequences for each page, enabling `f_N(page)` function.

**Format**: Apache Parquet (ZSTD compressed)

**Schema**:
```
page_id: int64              # Source page ID
link_sequence: list<int64>  # Ordered array of target page IDs
```

**Statistics**:
- Total rows: 17,972,018
- Total resolved links: 206,322,770
- File size: 686 MB
- Build time: ~5 minutes

**Usage**:
```python
# N-Link function: f_N(page_id) = link_sequence[N-1]
# Example: f_1(page_id) = first link, f_2(page_id) = second link, etc.

import pyarrow.parquet as pq
table = pq.read_table('nlink_sequences.parquet')

# Get sequence for specific page
page_row = table.filter(table['page_id'] == 12).to_pandas().iloc[0]
sequence = page_row['link_sequence']
print(f"f_1(12) = {sequence[0]}")  # First link from page 12
print(f"f_5(12) = {sequence[4]}")  # Fifth link from page 12
```

**Sample Data**:
```
Page 12: [23040, 99232, 170653, 6512, 1182927, ...] (599 total)
Page 303: [18618239, 816925, 401342, 30395, 48830, ...] (758 total)
```

**Resolution Applied**:
- ✅ Redirects resolved to final target
- ❌ Disambiguation pages excluded
- ❌ Self-links excluded
- ❌ Unresolvable titles excluded

---

### `redirects.parquet`

Redirect mappings from SQL dump.

**Format**: Apache Parquet (ZSTD compressed)

**Schema** (actual):
```
from_id: int64       # Redirect page's ID
to_namespace: int32  # Target namespace
to_title: string     # Target page title
```

**Statistics**:
- Total rows: 15,024,669
- File size: 189.3 MB
- NS0 redirects: 11,693,720

**Example** (as DataFrame):
```
   from_id  to_namespace                       to_title
0       10             0         Computer_accessibility
1       13             0         History_of_Afghanistan
2       14             0       Geography_of_Afghanistan
```
page_title: string          # Redirect page's title
target_title: string        # Target page title (as stored in redirect table)
target_page_id: int64       # Resolved target page_id (nullable if target doesn't exist)
```

**Note**: `target_page_id` is resolved by joining with `pages.parquet`. If target doesn't exist (broken redirect), field is null.

---

**Note on Disambiguation Pages**: Disambiguation status is stored as `is_disambiguation` boolean in `pages.parquet`. No separate file needed - query with: `SELECT * FROM pages WHERE is_disambiguation = true`

---

### `extraction_log.json`

Complete provenance and statistics for the extraction.

**Example**:
```json
{
  "extraction_date": "2025-12-29T10:30:00Z",
  "dump_date": "20251201",
  
  "sources": {
    "xml_dump": {
      "file": "enwiki-20251201-pages-articles-multistream.xml.bz2",
      "sha256": "abc123...",
      "url": "https://dumps.wikimedia.org/enwiki/20251201/"
    },
    "page_sql": {
      "file": "enwiki-20251201-page.sql.gz",
      "sha256": "def456..."
    },
    "redirect_sql": {
      "file": "enwiki-20251201-redirect.sql.gz",
      "sha256": "ghi789..."
    },
    "page_props_sql": {
      "file": "enwiki-20251201-page_props.sql.gz",
      "sha256": "jkl012..."
    }
  },
  
  "extraction_config": {
    "strip_templates": true,
    "strip_refs": true,
    "strip_comments": true,
    "strip_tables": false,
    "strip_galleries": true,
    "link_pattern": "\\[\\[([^|\\]]+)(?:\\|[^\\]]+)?\\]\\]"
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

### Step 1: Download SQL Dumps

Download from https://dumps.wikimedia.org/enwiki/YYYYMMDD/ to `data/wikipedia/raw/`:

| File | Size | Contents |
|------|------|----------|
| `enwiki-YYYYMMDD-pages-articles-multistream.xml.bz2` | ~22GB | Article content (wikitext) |
| `enwiki-YYYYMMDD-page.sql.gz` | ~600MB | Page table (id, title, namespace, redirect flag) |
| `enwiki-YYYYMMDD-redirect.sql.gz` | ~50MB | Redirect mappings |
| `enwiki-YYYYMMDD-page_props.sql.gz` | ~100MB | Page properties (disambiguation, stub flags) |

**Critical**: All files must be from the **same dump date** to ensure consistency.

**SQL Dump Format**: MySQL INSERT statements. Example:
```sql
INSERT INTO `page` VALUES (10,0,'AccessibleComputing','',0,1,0,0.33167112649574004,'20230903080914','20230903080914',1002250816,94,'wikitext',NULL),...
```

We need to parse these INSERT statements to extract the data.

### Step 2: Parse SQL Dumps into Parquet

```python
import re
import pyarrow as pa
import pyarrow.parquet as pq
import gzip

def parse_sql_dump(sql_path: str, table_name: str) -> pa.Table:
    """
    Parse MySQL INSERT statements from a .sql.gz file.
    Returns a PyArrow Table.
    """
    # Pattern matches: INSERT INTO `table` VALUES (...),(...),(...);
    insert_pattern = re.compile(
        rf"INSERT INTO `{table_name}` VALUES \((.+?)\);",
        re.DOTALL
    )
    
    rows = []
    with gzip.open(sql_path, 'rt', encoding='utf-8', errors='replace') as f:
        for line in f:
            if line.startswith('INSERT INTO'):
                # Parse value tuples
                # ... parsing logic ...
                pass
    
    return pa.Table.from_pydict(rows)
```

### Step 3: Build Lookup Structures

```python
import pyarrow.parquet as pq

# Load parsed page table from Parquet
pages_df = pq.read_table('data/wikipedia/processed/pages.parquet').to_pandas()

# Build lookup structures
page_lookup = {}       # {title: page_id} for exact match
page_lookup_lower = {} # {title.lower(): [page_ids]} for fallback

for _, row in pages_df.iterrows():
    page_id = row['page_id']
    title = row['page_title']
    
    page_lookup[title] = page_id
    page_lookup_lower.setdefault(title.lower(), []).append(page_id)

# Disambiguation and stub flags already in pages_df
# Access via: pages_df[pages_df['is_disambiguation'] == True]
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
import bz2
from xml.etree import ElementTree as ET
import pyarrow as pa
import pyarrow.parquet as pq

def process_xml_dump(xml_path: str, page_lookup: dict, output_dir: str):
    """Stream process XML dump, output to Parquet."""
    
    # Accumulators (flush periodically for memory management)
    pages_data = {'page_id': [], 'page_title': [], 'namespace': [], 
                  'is_redirect': [], 'is_disambiguation': [], 'is_stub': [],
                  'byte_size': [], 'link_count': [], 'extraction_status': []}
    links_data = {'page_id': [], 'link_sequence': [], 'positions': []}
    unmatched_data = {'page_id': [], 'link_text': [], 'position': []}
    
    stats = {'processed': 0, 'matched': 0, 'unmatched': 0}
    
    # Stream XML using iterparse (memory efficient)
    for page in stream_xml(xml_path):
        page_id = page['id']
        wikitext = page['text']
        
        # Clean wikitext (strip templates, refs, comments)
        clean = strip_templates(strip_refs(strip_comments(wikitext)))
        
        # Extract and match links
        raw_links = extract_links_with_positions(clean)
        matched_ids, matched_pos, unmatched = [], [], []
        
        for link_text, pos in raw_links:
            matched_id = normalize_and_match(link_text, page_lookup)
            if matched_id:
                matched_ids.append(matched_id)
                matched_pos.append(pos)
                stats['matched'] += 1
            else:
                unmatched.append((link_text, pos))
                stats['unmatched'] += 1
        
        # Append to accumulators
        links_data['page_id'].append(page_id)
        links_data['link_sequence'].append(matched_ids)
        links_data['positions'].append(matched_pos)
        
        for text, pos in unmatched:
            unmatched_data['page_id'].append(page_id)
            unmatched_data['link_text'].append(text)
            unmatched_data['position'].append(pos)
        
        stats['processed'] += 1
        if stats['processed'] % 100000 == 0:
            print(f"Processed {stats['processed']} pages...")
    
    # Write final Parquet files
    pq.write_table(pa.Table.from_pydict(links_data), 
                   f'{output_dir}/links.parquet')
    pq.write_table(pa.Table.from_pydict(unmatched_data), 
                   f'{output_dir}/unmatched_links.parquet')
    
    return stats
```
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
import pyarrow.parquet as pq
import duckdb

# Load pages and links from Parquet
pages_df = pq.read_table('data/wikipedia/processed/pages.parquet').to_pandas()
links_df = pq.read_table('data/wikipedia/processed/links.parquet').to_pandas()

# Filter: main namespace, not redirects, not disambiguation
valid_pages = pages_df[
    (pages_df['namespace'] == 0) & 
    (~pages_df['is_redirect']) & 
    (~pages_df['is_disambiguation'])
]

# Build N-Link graph (dict for O(1) lookup during traversal)
n_link_graph = dict(zip(links_df['page_id'], links_df['link_sequence']))

# N-Link traversal
def n_link_traverse(start_page: int, n: int, graph: dict) -> tuple[list, str]:
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
import pyarrow.parquet as pq

# Load redirects
redirects_df = pq.read_table('data/wikipedia/processed/redirects.parquet').to_pandas()
redirect_map = dict(zip(redirects_df['page_id'], redirects_df['target_page_id']))

def resolve_redirects(link_ids: list[int], redirect_map: dict) -> list[int]:
    """Resolve redirect chains in link sequences."""
    resolved = []
    for link_id in link_ids:
        current = link_id
        seen = set()
        
        # Follow redirect chain (max 10 hops to prevent infinite loops)
        while current in redirect_map and current not in seen and len(seen) < 10:
            seen.add(current)
            target = redirect_map[current]
            if target is not None:
                current = target
            else:
                break  # Broken redirect
        
        resolved.append(current)
    
    return resolved
```

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
import duckdb

# Load disambiguation pages and their links
result = duckdb.sql("""
    SELECT p.page_id, p.page_title, l.link_sequence
    FROM 'data/wikipedia/processed/pages.parquet' p
    JOIN 'data/wikipedia/processed/links.parquet' l ON p.page_id = l.page_id
    WHERE p.is_disambiguation = true
    LIMIT 100
""").fetchall()

for page_id, title, link_ids in result:
    print(f"'{title}' disambiguates to: {link_ids}")
```

---

## File Format Specifications

### Parquet Format Standards

- **Compression**: Snappy (default) or ZSTD for smaller files
- **Row Group Size**: ~128MB (default)
- **Data Types**: Use native Arrow types (int64, string, list, bool)
- **Null Handling**: Native Parquet null support

### DuckDB Integration

All Parquet files can be queried directly with DuckDB without loading into memory:

```python
import duckdb

# Query Parquet files directly
result = duckdb.sql("""
    SELECT page_title, link_count 
    FROM 'data/wikipedia/processed/pages.parquet'
    WHERE is_redirect = false AND link_count > 100
    ORDER BY link_count DESC
    LIMIT 10
""")
```

### Size Estimates

Based on enwiki-20251220 (English Wikipedia December 2025):

**Raw Downloads** (to `data/wikipedia/raw/`):

| File | Size |
|------|------|
| XML dump (69 multistream files) | ~100GB uncompressed |
| page.sql.gz | ~2.5GB |
| redirect.sql.gz | ~150MB |
| page_props.sql.gz | ~250MB |

**Processed Output** (to `data/wikipedia/processed/`):

| File | Rows | Size |
|------|------|------|
| pages.parquet | 64.7M | 985 MB |
| redirects.parquet | 15.0M | 189 MB |
| disambig_pages.parquet | 376K | 1.8 MB |
| links.parquet | 353.4M | 2.84 GB |
| links_resolved.parquet | 237.6M | 1.39 GB |
| **Total** | | **~5.4 GB** |

**Processing Times**:
- SQL parsing: ~15 minutes
- XML link extraction: ~31 minutes (69 files)
- Link resolution: ~18 seconds
- **Total pipeline**: ~47 minutes

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
import duckdb

# 1. Link count consistency
result = duckdb.sql("""
    SELECT p.page_id, p.link_count, len(l.link_sequence) as actual_count
    FROM 'data/wikipedia/processed/pages.parquet' p
    JOIN 'data/wikipedia/processed/links.parquet' l ON p.page_id = l.page_id
    WHERE p.link_count != len(l.link_sequence)
""").fetchall()
assert len(result) == 0, f"Link count mismatches: {len(result)}"

# 2. No self-loops in links
result = duckdb.sql("""
    SELECT page_id
    FROM 'data/wikipedia/processed/links.parquet'
    WHERE list_contains(link_sequence, page_id)
""").fetchall()
assert len(result) == 0, f"Self-loops detected: {len(result)}"

# 3. All link targets exist (sample check)
result = duckdb.sql("""
    WITH all_targets AS (
        SELECT DISTINCT unnest(link_sequence) as target_id
        FROM 'data/wikipedia/processed/links.parquet'
    )
    SELECT target_id FROM all_targets
    WHERE target_id NOT IN (SELECT page_id FROM 'data/wikipedia/processed/pages.parquet')
    LIMIT 100
""").fetchall()
print(f"Dangling links (sample): {len(result)}")
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
From `unmatched_links.parquet`, identify most-linked non-existent pages (future article candidates).

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

All from https://dumps.wikimedia.org/enwiki/YYYYMMDD/:

1. **Wikipedia XML Dump**: `enwiki-YYYYMMDD-pages-articles-multistream.xml.bz2` (~22GB)
2. **Page SQL Dump**: `enwiki-YYYYMMDD-page.sql.gz` (~600MB)
3. **Redirect SQL Dump**: `enwiki-YYYYMMDD-redirect.sql.gz` (~50MB)
4. **Page Props SQL Dump**: `enwiki-YYYYMMDD-page_props.sql.gz` (~100MB)

**No external account required** - all files publicly downloadable.

### Software Requirements

- Python 3.10+
- Libraries: `pyarrow`, `duckdb`, `lxml`, `regex`
- Disk Space: 30GB+ free (raw downloads + processed output)
- RAM: 8GB minimum, 16GB+ recommended

---

## Troubleshooting

### Issue: Low Match Rate

**Symptoms**: <90% links matched

**Causes**:
- SQL dumps from different date than XML dump
- Template stripping too aggressive (removing valid links)
- Case normalization failures

**Solutions**:
- Ensure all dump files from **same date**
- Review `unmatched_links.parquet` for patterns
- Add logging to normalization function

### Issue: Memory Exhaustion

**Symptoms**: Process killed by OS

**Causes**:
- Loading entire XML into memory
- Accumulating data without flushing to Parquet

**Solutions**:
- Use streaming XML parser (iterparse)
- Flush to Parquet in batches (every 100k pages)
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
- Wikipedia Dumps: https://dumps.wikimedia.org/
- Wikipedia Database Documentation: https://www.mediawiki.org/wiki/Manual:Database_layout

---

**END OF DOCUMENT**
