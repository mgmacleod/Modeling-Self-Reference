"""
Parse Wikipedia SQL dumps to Parquet files.

Extracts:
- pages.parquet: page_id, title, namespace, is_redirect
- redirects.parquet: from_id, to_title  
- disambig_pages.parquet: page_id (pages with disambiguation property)

The SQL dumps use MariaDB format with multi-row INSERT statements.
Values are comma-separated tuples within each INSERT.
"""

import re
import pyarrow as pa
import pyarrow.parquet as pq
from pathlib import Path
from typing import Iterator
import time

# Paths
RAW_DIR = Path("data/wikipedia/raw")
PROCESSED_DIR = Path("data/wikipedia/processed")


def parse_sql_values(line: str) -> Iterator[tuple]:
    """
    Parse VALUES from a SQL INSERT statement.
    
    Format: INSERT INTO `table` VALUES (v1,v2,...),(v1,v2,...),...;
    
    Values can be:
    - Numbers: 123, 0.456
    - Strings: 'text' (with escaped quotes \')
    - NULL
    """
    # Find the VALUES part
    match = re.search(r'VALUES\s*', line, re.IGNORECASE)
    if not match:
        return
    
    start = match.end()
    data = line[start:]
    
    # State machine to parse tuples
    i = 0
    n = len(data)
    
    while i < n:
        # Skip whitespace
        while i < n and data[i] in ' \t\n':
            i += 1
        
        if i >= n or data[i] != '(':
            break
        
        # Parse tuple
        i += 1  # skip '('
        values = []
        
        while i < n:
            # Skip whitespace
            while i < n and data[i] in ' \t':
                i += 1
            
            if i >= n:
                break
            
            if data[i] == ')':
                i += 1
                break
            
            if data[i] == ',':
                i += 1
                continue
            
            # Parse value
            if data[i] == "'":
                # String value
                i += 1
                val_chars = []
                while i < n:
                    if data[i] == '\\' and i + 1 < n:
                        # Escaped character
                        val_chars.append(data[i + 1])
                        i += 2
                    elif data[i] == "'":
                        i += 1
                        break
                    else:
                        val_chars.append(data[i])
                        i += 1
                values.append(''.join(val_chars))
            elif data[i:i+4].upper() == 'NULL':
                values.append(None)
                i += 4
            else:
                # Number or other value
                val_chars = []
                while i < n and data[i] not in ',)':
                    val_chars.append(data[i])
                    i += 1
                val_str = ''.join(val_chars).strip()
                # Try to parse as number
                try:
                    if '.' in val_str:
                        values.append(float(val_str))
                    else:
                        values.append(int(val_str))
                except ValueError:
                    values.append(val_str)
        
        yield tuple(values)
        
        # Skip comma between tuples
        while i < n and data[i] in ' \t\n,':
            i += 1


def parse_page_sql() -> None:
    """
    Parse page.sql to pages.parquet.
    
    Schema: page_id, page_namespace, page_title, page_is_redirect, ...
    We keep: page_id, title, namespace, is_redirect
    """
    print("Parsing page.sql...")
    sql_file = RAW_DIR / "enwiki-20251220-page.sql"
    
    page_ids = []
    titles = []
    namespaces = []
    is_redirects = []
    
    row_count = 0
    start = time.time()
    
    with open(sql_file, 'r', encoding='utf-8', errors='replace') as f:
        for line in f:
            if not line.startswith('INSERT INTO'):
                continue
            
            for values in parse_sql_values(line):
                if len(values) >= 4:
                    page_id, namespace, title, is_redirect = values[:4]
                    page_ids.append(page_id)
                    namespaces.append(namespace)
                    # Title is stored as binary, decode from bytes-like string
                    titles.append(str(title) if title else '')
                    is_redirects.append(bool(is_redirect))
                    
                    row_count += 1
                    if row_count % 1_000_000 == 0:
                        elapsed = time.time() - start
                        print(f"  {row_count:,} rows ({elapsed:.1f}s)")
    
    elapsed = time.time() - start
    print(f"  Total: {row_count:,} rows in {elapsed:.1f}s")
    
    # Create Arrow table
    print("  Writing parquet...")
    table = pa.table({
        'page_id': pa.array(page_ids, type=pa.int32()),
        'namespace': pa.array(namespaces, type=pa.int16()),
        'title': pa.array(titles, type=pa.string()),
        'is_redirect': pa.array(is_redirects, type=pa.bool_()),
    })
    
    out_path = PROCESSED_DIR / "pages.parquet"
    pq.write_table(table, out_path, compression='zstd')
    print(f"  Wrote {out_path} ({out_path.stat().st_size / 1e6:.1f} MB)")


def parse_redirect_sql() -> None:
    """
    Parse redirect.sql to redirects.parquet.
    
    Schema: rd_from, rd_namespace, rd_title, rd_interwiki, rd_fragment
    We keep: from_id (rd_from), to_title (rd_title)
    """
    print("Parsing redirect.sql...")
    sql_file = RAW_DIR / "enwiki-20251220-redirect.sql"
    
    from_ids = []
    to_titles = []
    to_namespaces = []
    
    row_count = 0
    start = time.time()
    
    with open(sql_file, 'r', encoding='utf-8', errors='replace') as f:
        for line in f:
            if not line.startswith('INSERT INTO'):
                continue
            
            for values in parse_sql_values(line):
                if len(values) >= 3:
                    from_id, namespace, to_title = values[:3]
                    from_ids.append(from_id)
                    to_namespaces.append(namespace)
                    to_titles.append(str(to_title) if to_title else '')
                    
                    row_count += 1
                    if row_count % 1_000_000 == 0:
                        elapsed = time.time() - start
                        print(f"  {row_count:,} rows ({elapsed:.1f}s)")
    
    elapsed = time.time() - start
    print(f"  Total: {row_count:,} rows in {elapsed:.1f}s")
    
    # Create Arrow table
    print("  Writing parquet...")
    table = pa.table({
        'from_id': pa.array(from_ids, type=pa.int32()),
        'to_namespace': pa.array(to_namespaces, type=pa.int16()),
        'to_title': pa.array(to_titles, type=pa.string()),
    })
    
    out_path = PROCESSED_DIR / "redirects.parquet"
    pq.write_table(table, out_path, compression='zstd')
    print(f"  Wrote {out_path} ({out_path.stat().st_size / 1e6:.1f} MB)")


def parse_page_props_sql() -> None:
    """
    Parse page_props.sql to extract disambiguation pages.
    
    Schema: pp_page, pp_propname, pp_value, pp_sortkey
    We want pages where pp_propname = 'disambiguation'
    """
    print("Parsing page_props.sql for disambiguation pages...")
    sql_file = RAW_DIR / "enwiki-20251220-page_props.sql"
    
    disambig_page_ids = []
    
    row_count = 0
    start = time.time()
    
    with open(sql_file, 'r', encoding='utf-8', errors='replace') as f:
        for line in f:
            if not line.startswith('INSERT INTO'):
                continue
            
            for values in parse_sql_values(line):
                row_count += 1
                if len(values) >= 2:
                    page_id, propname = values[:2]
                    if propname == 'disambiguation':
                        disambig_page_ids.append(page_id)
                
                if row_count % 5_000_000 == 0:
                    elapsed = time.time() - start
                    print(f"  {row_count:,} rows scanned ({elapsed:.1f}s)")
    
    elapsed = time.time() - start
    print(f"  Scanned {row_count:,} rows in {elapsed:.1f}s")
    print(f"  Found {len(disambig_page_ids):,} disambiguation pages")
    
    # Create Arrow table
    print("  Writing parquet...")
    table = pa.table({
        'page_id': pa.array(disambig_page_ids, type=pa.int32()),
    })
    
    out_path = PROCESSED_DIR / "disambig_pages.parquet"
    pq.write_table(table, out_path, compression='zstd')
    print(f"  Wrote {out_path} ({out_path.stat().st_size / 1e6:.1f} MB)")


def main():
    PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
    
    total_start = time.time()
    
    parse_page_sql()
    print()
    
    parse_redirect_sql()
    print()
    
    parse_page_props_sql()
    
    total_elapsed = time.time() - total_start
    print(f"\nAll done! Total time: {total_elapsed:.1f}s")


if __name__ == "__main__":
    main()
