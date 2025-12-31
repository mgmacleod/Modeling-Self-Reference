#!/usr/bin/env python3
"""
Resolve Wikipedia link titles to page IDs.

This script takes the raw links (from_id, to_title) and resolves them to
(from_id, to_id) edges by:
1. Joining to_title with pages.title to get target page IDs
2. Following redirects to get the final target page ID
3. Excluding links to non-existent pages and disambiguation pages

Input:
  - links.parquet: (from_id, to_title) - raw extracted links
  - pages.parquet: (id, title, namespace, is_redirect) - all pages
  - redirects.parquet: (from_id, to_title) - redirect mappings
  - disambig_pages.parquet: (page_id,) - disambiguation page IDs

Output:
  - links_resolved.parquet: (from_id, to_id) - resolved edge list
"""

import time
from pathlib import Path
import duckdb

# Paths
PROCESSED_DIR = Path("data/wikipedia/processed")
LINKS_PATH = PROCESSED_DIR / "links.parquet"
PAGES_PATH = PROCESSED_DIR / "pages.parquet"
REDIRECTS_PATH = PROCESSED_DIR / "redirects.parquet"
DISAMBIG_PATH = PROCESSED_DIR / "disambig_pages.parquet"
OUTPUT_PATH = PROCESSED_DIR / "links_resolved.parquet"

def main():
    start = time.time()
    
    print("Connecting to DuckDB...")
    con = duckdb.connect()
    
    # Enable parallel processing
    con.execute("SET threads TO 8")
    
    print("Loading data...")
    
    # Create views for our parquet files
    con.execute(f"CREATE VIEW links AS SELECT * FROM read_parquet('{LINKS_PATH}')")
    con.execute(f"CREATE VIEW pages AS SELECT * FROM read_parquet('{PAGES_PATH}')")
    con.execute(f"CREATE VIEW redirects AS SELECT * FROM read_parquet('{REDIRECTS_PATH}')")
    con.execute(f"CREATE VIEW disambig AS SELECT * FROM read_parquet('{DISAMBIG_PATH}')")
    
    # Get counts for progress reporting
    link_count = con.execute("SELECT COUNT(*) FROM links").fetchone()[0]
    print(f"  Links to resolve: {link_count:,}")
    
    page_count = con.execute("SELECT COUNT(*) FROM pages WHERE namespace = 0").fetchone()[0]
    print(f"  NS0 pages: {page_count:,}")
    
    redirect_count = con.execute("SELECT COUNT(*) FROM redirects").fetchone()[0]
    print(f"  Redirects: {redirect_count:,}")
    
    disambig_count = con.execute("SELECT COUNT(*) FROM disambig").fetchone()[0]
    print(f"  Disambiguation pages: {disambig_count:,}")
    
    print("\nBuilding title->id lookup for NS0 content pages...")
    # Create a lookup table: title -> page_id for non-redirect NS0 pages
    con.execute("""
        CREATE TABLE page_lookup AS
        SELECT title, page_id
        FROM pages
        WHERE namespace = 0 AND is_redirect = false
    """)
    
    lookup_count = con.execute("SELECT COUNT(*) FROM page_lookup").fetchone()[0]
    print(f"  Content pages in lookup: {lookup_count:,}")
    
    print("\nBuilding redirect resolution table...")
    # Create redirect chain resolution (redirect_title -> final_page_id)
    # We need to follow redirect chains: A -> B -> C means A should resolve to C
    # Most redirects are single-hop, but some have chains
    
    # First, get redirect source titles and their target titles
    con.execute("""
        CREATE TABLE redirect_lookup AS
        SELECT 
            p.title as from_title,
            r.to_title
        FROM redirects r
        JOIN pages p ON r.from_id = p.page_id
        WHERE p.namespace = 0 AND r.to_namespace = 0
    """)
    
    # Now resolve redirect targets to final page IDs
    # Handle up to 3 redirect hops (should cover 99.9% of cases)
    con.execute("""
        CREATE TABLE redirect_resolved AS
        WITH RECURSIVE resolve AS (
            -- Base case: redirect target is a content page
            SELECT 
                rl.from_title,
                pl.page_id as to_id,
                1 as depth
            FROM redirect_lookup rl
            JOIN page_lookup pl ON rl.to_title = pl.title
            
            UNION ALL
            
            -- Recursive case: follow redirect chain
            SELECT 
                rl.from_title,
                r.to_id,
                r.depth + 1
            FROM redirect_lookup rl
            JOIN resolve r ON rl.to_title = r.from_title
            WHERE r.depth < 5  -- Max 5 hops to prevent infinite loops
        )
        SELECT from_title, to_id
        FROM resolve
        WHERE depth = (SELECT MAX(depth) FROM resolve r2 WHERE r2.from_title = resolve.from_title)
    """)
    
    redirect_resolved_count = con.execute("SELECT COUNT(*) FROM redirect_resolved").fetchone()[0]
    print(f"  Resolved redirects: {redirect_resolved_count:,}")
    
    print("\nResolving links...")
    # Now resolve all links:
    # 1. Try direct match to content page
    # 2. If not found, try redirect resolution
    # 3. Exclude disambiguation pages
    
    query = """
        COPY (
            SELECT DISTINCT
                l.from_id,
                COALESCE(pl.page_id, rr.to_id) as to_id
            FROM links l
            LEFT JOIN page_lookup pl ON l.to_title = pl.title
            LEFT JOIN redirect_resolved rr ON l.to_title = rr.from_title
            WHERE COALESCE(pl.page_id, rr.to_id) IS NOT NULL
              AND COALESCE(pl.page_id, rr.to_id) NOT IN (SELECT page_id FROM disambig)
              AND l.from_id != COALESCE(pl.page_id, rr.to_id)  -- No self-links
        ) TO '{}' (FORMAT PARQUET, COMPRESSION ZSTD)
    """.format(OUTPUT_PATH)
    
    con.execute(query)
    
    elapsed = time.time() - start
    print(f"\nCompleted in {elapsed:.1f}s")
    
    # Get output stats
    result = con.execute(f"SELECT COUNT(*) FROM read_parquet('{OUTPUT_PATH}')").fetchone()[0]
    print(f"Wrote {OUTPUT_PATH} with {result:,} edges")
    
    # File size
    size_mb = OUTPUT_PATH.stat().st_size / (1024 * 1024)
    print(f"File size: {size_mb:.1f} MB")
    
    # Sample output
    print("\nSample edges:")
    sample = con.execute(f"SELECT * FROM read_parquet('{OUTPUT_PATH}') LIMIT 10").fetchall()
    for row in sample:
        print(f"  {row[0]} -> {row[1]}")
    
    con.close()

if __name__ == "__main__":
    main()
