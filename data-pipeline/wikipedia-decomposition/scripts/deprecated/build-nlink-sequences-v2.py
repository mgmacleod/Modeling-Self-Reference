#!/usr/bin/env python3
"""
Resolve prose link titles to page IDs, preserving order for N-Link traversal.

Memory-efficient version that processes in chunks.

Takes links_prose.parquet (from_id, link_position, to_title) and produces
nlink_sequences.parquet (page_id, link_sequence) where link_sequence is
an ordered array of resolved page IDs.

This is the final output for N-Link theory experiments:
  f_N(page_id) = link_sequence[N-1]  (0-indexed array, N is 1-indexed)
"""

import time
from pathlib import Path
import pyarrow as pa
import pyarrow.parquet as pq
import duckdb

# Paths
PROCESSED_DIR = Path("data/wikipedia/processed")
LINKS_PROSE_PATH = PROCESSED_DIR / "links_prose.parquet"
PAGES_PATH = PROCESSED_DIR / "pages.parquet"
REDIRECTS_PATH = PROCESSED_DIR / "redirects.parquet"
DISAMBIG_PATH = PROCESSED_DIR / "disambig_pages.parquet"
OUTPUT_PATH = PROCESSED_DIR / "nlink_sequences.parquet"


def main():
    start = time.time()
    
    print("=== N-Link Sequence Builder ===")
    print("Resolving prose links to ordered page ID sequences")
    print()
    
    print("Connecting to DuckDB...")
    con = duckdb.connect()
    con.execute("SET threads TO 4")
    con.execute("SET memory_limit = '16GB'")
    
    # Load lookup data into memory (small enough)
    print("Loading lookup tables...")
    
    # Content page lookup (title → page_id)
    page_lookup = {}
    pages = con.execute(f"""
        SELECT title, page_id 
        FROM read_parquet('{PAGES_PATH}')
        WHERE namespace = 0 AND is_redirect = false
    """).fetchall()
    for title, page_id in pages:
        page_lookup[title] = page_id
    print(f"  Content pages: {len(page_lookup):,}")
    
    # Redirect lookup (title → target_page_id)
    redirect_lookup = {}
    redirects = con.execute(f"""
        SELECT p.title, pl.page_id
        FROM read_parquet('{REDIRECTS_PATH}') r
        JOIN read_parquet('{PAGES_PATH}') p ON r.from_id = p.page_id
        JOIN read_parquet('{PAGES_PATH}') pl ON r.to_title = pl.title AND pl.namespace = 0 AND pl.is_redirect = false
        WHERE p.namespace = 0 AND r.to_namespace = 0
    """).fetchall()
    for from_title, to_id in redirects:
        redirect_lookup[from_title] = to_id
    print(f"  Redirects: {len(redirect_lookup):,}")
    
    # Disambiguation pages to exclude
    disambig_ids = set()
    disambig = con.execute(f"SELECT page_id FROM read_parquet('{DISAMBIG_PATH}')").fetchall()
    for (page_id,) in disambig:
        disambig_ids.add(page_id)
    print(f"  Disambiguation pages: {len(disambig_ids):,}")
    
    con.close()
    
    print()
    print("Processing links in streaming mode...")
    
    # Read links parquet in batches and build sequences
    parquet_file = pq.ParquetFile(str(LINKS_PROSE_PATH))
    
    # Dictionary to accumulate sequences: page_id -> [(position, to_id), ...]
    sequences = {}
    
    total_links = 0
    resolved_links = 0
    batch_num = 0
    
    for batch in parquet_file.iter_batches(batch_size=10_000_000):
        batch_num += 1
        df = batch.to_pandas()
        
        for _, row in df.iterrows():
            from_id = int(row['from_id'])
            position = int(row['link_position'])
            to_title = row['to_title']
            
            total_links += 1
            
            # Resolve title to page_id
            to_id = page_lookup.get(to_title) or redirect_lookup.get(to_title)
            
            if to_id is None:
                continue
            if to_id in disambig_ids:
                continue
            if to_id == from_id:
                continue
            
            resolved_links += 1
            
            if from_id not in sequences:
                sequences[from_id] = []
            sequences[from_id].append((position, to_id))
        
        print(f"  Batch {batch_num}: {total_links:,} processed, {resolved_links:,} resolved, {len(sequences):,} pages")
    
    print()
    print(f"Total: {resolved_links:,} resolved links from {len(sequences):,} pages")
    
    # Sort each sequence by position and extract just the page_ids
    print("Sorting sequences by position...")
    page_ids = []
    link_sequences = []
    
    for page_id, pos_list in sequences.items():
        pos_list.sort(key=lambda x: x[0])  # Sort by position
        link_seq = [to_id for pos, to_id in pos_list]
        page_ids.append(page_id)
        link_sequences.append(link_seq)
    
    # Free memory
    del sequences
    
    print(f"Writing {len(page_ids):,} sequences to parquet...")
    
    # Create Arrow table with list column
    table = pa.table({
        'page_id': pa.array(page_ids, type=pa.int64()),
        'link_sequence': pa.array(link_sequences, type=pa.list_(pa.int64())),
    })
    
    pq.write_table(table, OUTPUT_PATH, compression='zstd', compression_level=3)
    
    elapsed = time.time() - start
    size_mb = OUTPUT_PATH.stat().st_size / (1024 * 1024)
    
    print()
    print("=== Output Summary ===")
    print(f"File: {OUTPUT_PATH}")
    print(f"Size: {size_mb:.1f} MB")
    print(f"Pages with links: {len(page_ids):,}")
    print(f"Total resolved links: {resolved_links:,}")
    print(f"Time: {elapsed:.1f}s")
    print()
    print("Schema: (page_id: int64, link_sequence: list<int64>)")
    print("Usage: f_N(page_id) = link_sequence[N-1]  # N is 1-indexed")
    
    # Sample output
    print()
    print("Sample sequences (first 5 with 5+ links):")
    count = 0
    for i, (pid, seq) in enumerate(zip(page_ids, link_sequences)):
        if len(seq) >= 5:
            print(f"  Page {pid}: {seq[:5]}... ({len(seq)} total)")
            count += 1
            if count >= 5:
                break


if __name__ == "__main__":
    main()
