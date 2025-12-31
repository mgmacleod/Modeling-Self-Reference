#!/usr/bin/env python3
"""
Resolve prose link titles to page IDs, preserving order for N-Link traversal.

Vectorized version using Pandas operations instead of slow iteration.

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
import pandas as pd

# Paths
PROCESSED_DIR = Path("data/wikipedia/processed")
LINKS_PROSE_PATH = PROCESSED_DIR / "links_prose.parquet"
PAGES_PATH = PROCESSED_DIR / "pages.parquet"
REDIRECTS_PATH = PROCESSED_DIR / "redirects.parquet"
DISAMBIG_PATH = PROCESSED_DIR / "disambig_pages.parquet"
OUTPUT_PATH = PROCESSED_DIR / "nlink_sequences.parquet"


def main():
    start = time.time()
    
    print("=== N-Link Sequence Builder (Vectorized) ===")
    print("Resolving prose links to ordered page ID sequences")
    print()
    
    print("Connecting to DuckDB...")
    con = duckdb.connect()
    con.execute("SET threads TO 4")
    con.execute("SET memory_limit = '16GB'")
    
    # Load lookup data as DataFrames for merge operations
    print("Loading lookup tables...")
    
    # Content page lookup (title → page_id)
    print("  Loading content pages...")
    pages_df = con.execute(f"""
        SELECT title, page_id 
        FROM read_parquet('{PAGES_PATH}')
        WHERE namespace = 0 AND is_redirect = false
    """).df()
    pages_df = pages_df.rename(columns={'title': 'to_title', 'page_id': 'to_id'})
    print(f"  Content pages: {len(pages_df):,}")
    
    # Redirect lookup (title → target_page_id)
    print("  Loading redirects...")
    redirect_df = con.execute(f"""
        SELECT p.title as to_title, pl.page_id as to_id
        FROM read_parquet('{REDIRECTS_PATH}') r
        JOIN read_parquet('{PAGES_PATH}') p ON r.from_id = p.page_id
        JOIN read_parquet('{PAGES_PATH}') pl ON r.to_title = pl.title AND pl.namespace = 0 AND pl.is_redirect = false
        WHERE p.namespace = 0 AND r.to_namespace = 0
    """).df()
    print(f"  Redirects: {len(redirect_df):,}")
    
    # Combine into single lookup (pages take priority over redirects for same title)
    print("  Building combined lookup...")
    lookup_df = pd.concat([pages_df, redirect_df], ignore_index=True).drop_duplicates(subset='to_title', keep='first')
    lookup_df = lookup_df.set_index('to_title')['to_id']  # Series for fast lookup
    print(f"  Combined lookup entries: {len(lookup_df):,}")
    
    # Disambiguation pages to exclude
    print("  Loading disambiguation pages...")
    disambig_df = con.execute(f"SELECT page_id FROM read_parquet('{DISAMBIG_PATH}')").df()
    disambig_set = set(disambig_df['page_id'].values)
    print(f"  Disambiguation pages: {len(disambig_set):,}")
    
    con.close()
    
    print()
    print("Processing links in batches...")
    
    # Read links parquet in batches and build sequences
    parquet_file = pq.ParquetFile(str(LINKS_PROSE_PATH))
    
    # Will accumulate all resolved links, then group
    all_resolved = []
    
    total_links = 0
    resolved_links = 0
    batch_num = 0
    
    for batch in parquet_file.iter_batches(batch_size=10_000_000):
        batch_num += 1
        batch_start = time.time()
        
        # Convert to DataFrame
        df = batch.to_pandas()
        batch_size = len(df)
        total_links += batch_size
        
        # Vectorized lookup: merge with lookup table
        df['to_id'] = df['to_title'].map(lookup_df)
        
        # Filter: remove unresolved, disambig, self-links
        df = df.dropna(subset=['to_id'])
        df['to_id'] = df['to_id'].astype('int64')
        df = df[~df['to_id'].isin(disambig_set)]
        df = df[df['from_id'] != df['to_id']]
        
        resolved_in_batch = len(df)
        resolved_links += resolved_in_batch
        
        # Keep only needed columns
        df = df[['from_id', 'link_position', 'to_id']]
        all_resolved.append(df)
        
        batch_elapsed = time.time() - batch_start
        print(f"  Batch {batch_num}: {batch_size:,} → {resolved_in_batch:,} resolved ({batch_elapsed:.1f}s)")
    
    print()
    print(f"Concatenating {len(all_resolved)} batches...")
    resolved_df = pd.concat(all_resolved, ignore_index=True)
    del all_resolved
    
    print(f"Total resolved: {len(resolved_df):,} links")
    
    print()
    print("Sorting by (from_id, link_position)...")
    resolved_df = resolved_df.sort_values(['from_id', 'link_position'])
    
    print("Grouping into sequences...")
    # Group by from_id and collect to_id as list
    sequences = resolved_df.groupby('from_id')['to_id'].apply(list).reset_index()
    sequences.columns = ['page_id', 'link_sequence']
    
    del resolved_df
    
    print(f"Created {len(sequences):,} page sequences")
    
    print()
    print("Converting to Arrow and writing parquet...")
    
    # Convert to Arrow table with list column
    page_ids = sequences['page_id'].values
    link_seqs = sequences['link_sequence'].tolist()
    
    table = pa.table({
        'page_id': pa.array(page_ids, type=pa.int64()),
        'link_sequence': pa.array(link_seqs, type=pa.list_(pa.int64())),
    })
    
    pq.write_table(table, OUTPUT_PATH, compression='zstd', compression_level=3)
    
    elapsed = time.time() - start
    size_mb = OUTPUT_PATH.stat().st_size / (1024 * 1024)
    
    print()
    print("=== Output Summary ===")
    print(f"File: {OUTPUT_PATH}")
    print(f"Size: {size_mb:.1f} MB")
    print(f"Pages with links: {len(sequences):,}")
    print(f"Total resolved links: {resolved_links:,}")
    print(f"Time: {elapsed:.1f}s")
    print()
    print("Schema: (page_id: int64, link_sequence: list<int64>)")
    print("Usage: f_N(page_id) = link_sequence[N-1]  # N is 1-indexed")
    
    # Sample output
    print()
    print("Sample sequences (first 5 with 5+ links):")
    count = 0
    for _, row in sequences.iterrows():
        if len(row['link_sequence']) >= 5:
            seq = row['link_sequence']
            print(f"  Page {row['page_id']}: {seq[:5]}... ({len(seq)} total)")
            count += 1
            if count >= 5:
                break


if __name__ == "__main__":
    main()
