# Wikipedia Decomposition Pipeline Index

**Purpose**: Design documents and scripts for Wikipedia parsing and link graph extraction  
**Last Updated**: 2025-12-29

---

## Quick Start

**New users**: Run scripts in order:
1. `parse-sql-to-parquet.py` - Parse SQL dumps (~2 min)
2. `parse-xml-prose-links.py` - Extract prose links (~53 min)
3. `build-nlink-sequences-v3.py` - Build N-Link sequences (~5 min)

See [implementation-guide.md](implementation-guide.md) for full details.

---

## Core Files (Load when entering directory)

| File | Tier | Purpose | Tokens |
|------|------|---------|--------|
| [implementation-guide.md](implementation-guide.md) | 2 | Pipeline architecture and design | ~5k |

**Load these when**: Working on Wikipedia data extraction pipeline

---

## Reference Files (Available as-needed)

| File | Tier | Purpose | Tokens |
|------|------|---------|--------|
| [data-sources.md](data-sources.md) | 3 | Wikipedia/MediaWiki technical resources | ~3k |

**Load these when**: Adding new data sources or citing Wikipedia technical details (historical reproducibility)

---

## Scripts

### Active Scripts (Run Order)

| # | Script | Purpose | Time | Output |
|---|--------|---------|------|--------|
| 1 | [parse-sql-to-parquet.py](scripts/parse-sql-to-parquet.py) | Parse SQL dumps → pages, redirects, disambig | ~2 min | 3 parquet files |
| 2 | [parse-xml-prose-links.py](scripts/parse-xml-prose-links.py) | Extract prose-only links w/ position | ~53 min | `links_prose.parquet` |
| 3 | [build-nlink-sequences-v3.py](scripts/build-nlink-sequences-v3.py) | Resolve & build ordered sequences | ~5 min | `nlink_sequences.parquet` |

### Utility Scripts

| Script | Purpose |
|--------|---------|
| [quick-stats.py](scripts/quick-stats.py) | DuckDB queries for data verification |
| [decompress-all.py](scripts/decompress-all.py) | Helper for .bz2 decompression |
| [download-multistream.ps1](scripts/download-multistream.ps1) | PowerShell download helper |

### Legacy Scripts (Not needed for N-Link)

| Script | Purpose | Status |
|--------|---------|--------|
| [parse-xml-links.py](scripts/parse-xml-links.py) | Extract ALL links (no filtering) | Superseded |
| [resolve-links.py](scripts/resolve-links.py) | Resolve links (no order preservation) | Superseded |

### Deprecated Scripts

See [scripts/deprecated/](scripts/deprecated/) for earlier versions that failed or were too slow.

---

## Output Files

All in `data/wikipedia/processed/` (gitignored):

### Primary N-Link Output

| File | Rows | Size | Description |
|------|------|------|-------------|
| `nlink_sequences.parquet` | 18.0M | 686 MB | **⭐ N-Link sequences: f_N(page) = sequence[N-1]** |

### Supporting Data

| File | Rows | Size | Description |
|------|------|------|-------------|
| `pages.parquet` | 64.7M | 985 MB | All pages with namespace, redirect flag |
| `redirects.parquet` | 15.0M | 189 MB | Redirect mappings (from_id → to_title) |
| `disambig_pages.parquet` | 376K | 1.8 MB | Disambiguation page IDs |
| `links_prose.parquet` | 214.2M | 1.67 GB | Prose links with position (intermediate) |

### Legacy Files (Graph Analysis Only)

| File | Rows | Size | Description |
|------|------|------|-------------|
| `links.parquet` | 353.4M | 2.84 GB | Raw links - no order, includes templates |
| `links_resolved.parquet` | 237.6M | 1.39 GB | Resolved edges - no order |

---

## Status

- **Phase**: Complete
- **Implementation**: All N-Link extraction scripts complete
- **Dump Date**: 2025-12-20
- **Dependencies**: Python 3.13, pyarrow 22.0.0, duckdb 1.4.3, pandas

---

## Usage

**First time in wikipedia-decomposition/**: Load implementation-guide.md for complete pipeline context

**Re-running extraction**: Follow scripts 1→2→3 in Active Scripts table above

**Querying data**: Use DuckDB on parquet files directly:
```python
import duckdb
duckdb.sql("SELECT * FROM 'data/wikipedia/processed/nlink_sequences.parquet' LIMIT 5")
```

---
