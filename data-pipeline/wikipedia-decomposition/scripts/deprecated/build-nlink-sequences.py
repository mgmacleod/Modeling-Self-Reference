#!/usr/bin/env python3
"""
Resolve prose link titles to page IDs, preserving order for N-Link traversal.

Takes links_prose.parquet (from_id, link_position, to_title) and produces
nlink_sequences.parquet (page_id, link_sequence) where link_sequence is
an ordered array of resolved page IDs.

This is the final output for N-Link theory experiments:
  f_N(page_id) = link_sequence[N-1]  (0-indexed array, N is 1-indexed)

Resolution process:
1. Direct match: to_title → content page
2. Redirect resolution: to_title → redirect → final target
3. Filter: exclude disambiguation pages, self-links, unresolvable links
4. Preserve: link order within each page (critical for N-Link)
"""

import time
from pathlib import Path
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
    con.execute("SET threads TO 8")
    # Enable disk spilling for large aggregations
    con.execute("SET temp_directory = 'data/wikipedia/processed/tmp'")
    con.execute("SET memory_limit = '20GB'")
    con.execute("SET preserve_insertion_order = false")
    
    # Create views
    print("Loading data...")
    con.execute(f"CREATE VIEW links AS SELECT * FROM read_parquet('{LINKS_PROSE_PATH}')")
    con.execute(f"CREATE VIEW pages AS SELECT * FROM read_parquet('{PAGES_PATH}')")
    con.execute(f"CREATE VIEW redirects AS SELECT * FROM read_parquet('{REDIRECTS_PATH}')")
    con.execute(f"CREATE VIEW disambig AS SELECT * FROM read_parquet('{DISAMBIG_PATH}')")
    
    # Stats
    link_result = con.execute("SELECT COUNT(*) FROM links").fetchone()
    link_count = link_result[0] if link_result else 0
    page_result = con.execute("SELECT COUNT(*) FROM pages WHERE namespace = 0 AND is_redirect = false").fetchone()
    page_count = page_result[0] if page_result else 0
    print(f"  Prose links to resolve: {link_count:,}")
    print(f"  Content pages: {page_count:,}")
    
    print()
    print("Building lookup tables...")
    
    # Content page lookup (title → page_id)
    con.execute("""
        CREATE TABLE page_lookup AS
        SELECT title, page_id
        FROM pages
        WHERE namespace = 0 AND is_redirect = false
    """)
    lookup_result = con.execute("SELECT COUNT(*) FROM page_lookup").fetchone()
    lookup_count = lookup_result[0] if lookup_result else 0
    print(f"  Content page lookup: {lookup_count:,} entries")
    
    # Redirect resolution (redirect_title → final_page_id)
    # First get redirect source titles
    con.execute("""
        CREATE TABLE redirect_sources AS
        SELECT p.title as from_title, r.to_title
        FROM redirects r
        JOIN pages p ON r.from_id = p.page_id
        WHERE p.namespace = 0 AND r.to_namespace = 0
    """)
    
    # Resolve redirects to final target page IDs
    con.execute("""
        CREATE TABLE redirect_lookup AS
        SELECT rs.from_title, pl.page_id as to_id
        FROM redirect_sources rs
        JOIN page_lookup pl ON rs.to_title = pl.title
    """)
    redirect_result = con.execute("SELECT COUNT(*) FROM redirect_lookup").fetchone()
    redirect_count = redirect_result[0] if redirect_result else 0
    print(f"  Redirect lookup: {redirect_count:,} entries")
    
    print()
    print("Resolving links (preserving order)...")
    
    # Resolve each link while preserving position
    # COALESCE: try direct match first, then redirect
    con.execute("""
        CREATE TABLE resolved_links AS
        SELECT 
            l.from_id,
            l.link_position,
            COALESCE(pl.page_id, rl.to_id) as to_id
        FROM links l
        LEFT JOIN page_lookup pl ON l.to_title = pl.title
        LEFT JOIN redirect_lookup rl ON l.to_title = rl.from_title
        WHERE COALESCE(pl.page_id, rl.to_id) IS NOT NULL
          AND COALESCE(pl.page_id, rl.to_id) NOT IN (SELECT page_id FROM disambig)
          AND l.from_id != COALESCE(pl.page_id, rl.to_id)
    """)
    
    resolved_result = con.execute("SELECT COUNT(*) FROM resolved_links").fetchone()
    resolved_count = resolved_result[0] if resolved_result else 0
    print(f"  Resolved links: {resolved_count:,}")
    
    print()
    print("Building ordered sequences...")
    
    # Aggregate into ordered arrays per page
    # ORDER BY link_position ensures correct N-Link ordering
    query = f"""
        COPY (
            SELECT 
                from_id as page_id,
                list(to_id ORDER BY link_position) as link_sequence
            FROM resolved_links
            GROUP BY from_id
        ) TO '{OUTPUT_PATH}' (FORMAT PARQUET, COMPRESSION ZSTD)
    """
    con.execute(query)
    
    elapsed = time.time() - start
    print(f"Completed in {elapsed:.1f}s")
    
    # Output stats
    result = con.execute(f"""
        SELECT 
            COUNT(*) as pages,
            SUM(len(link_sequence)) as total_links,
            AVG(len(link_sequence)) as avg_links,
            MAX(len(link_sequence)) as max_links
        FROM read_parquet('{OUTPUT_PATH}')
    """).fetchone()
    
    if result:
        pages, total_links, avg_links, max_links = result
    else:
        pages, total_links, avg_links, max_links = 0, 0, 0.0, 0
    size_mb = OUTPUT_PATH.stat().st_size / (1024 * 1024)
    
    print()
    print("=== Output Summary ===")
    print(f"File: {OUTPUT_PATH}")
    print(f"Size: {size_mb:.1f} MB")
    print(f"Pages with links: {pages:,}")
    print(f"Total links: {int(total_links):,}")
    print(f"Avg links per page: {avg_links:.1f}")
    print(f"Max links on single page: {int(max_links):,}")
    print()
    print("Schema: (page_id: int64, link_sequence: list<int64>)")
    print("Usage: f_N(page_id) = link_sequence[N-1]  # N is 1-indexed")
    
    # Sample output
    print()
    print("Sample sequences:")
    sample = con.execute(f"""
        SELECT page_id, link_sequence[:5] as first_5_links, len(link_sequence) as total
        FROM read_parquet('{OUTPUT_PATH}')
        WHERE len(link_sequence) >= 5
        LIMIT 5
    """).fetchall()
    
    for page_id, first_5, total in sample:
        print(f"  Page {page_id}: {list(first_5)}... ({total} total)")
    
    con.close()


if __name__ == "__main__":
    main()
