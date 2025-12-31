"""Quick stats on the parsed parquet files."""
import duckdb

duckdb.sql("CREATE TABLE pages AS SELECT * FROM read_parquet('data/wikipedia/processed/pages.parquet')")
duckdb.sql("CREATE TABLE redirects AS SELECT * FROM read_parquet('data/wikipedia/processed/redirects.parquet')")
duckdb.sql("CREATE TABLE disambig AS SELECT * FROM read_parquet('data/wikipedia/processed/disambig_pages.parquet')")

print("=== Namespace Distribution (top 10) ===")
print(duckdb.sql("""
    SELECT namespace, COUNT(*) as count 
    FROM pages 
    GROUP BY namespace 
    ORDER BY count DESC 
    LIMIT 10
"""))

print("\n=== Article Pages (namespace=0) ===")
print(duckdb.sql("""
    SELECT 
        COUNT(*) as total,
        SUM(CASE WHEN is_redirect THEN 1 ELSE 0 END) as redirects,
        SUM(CASE WHEN NOT is_redirect THEN 1 ELSE 0 END) as content_pages
    FROM pages WHERE namespace = 0
"""))

print("\n=== Sample Content Pages ===")
print(duckdb.sql("""
    SELECT page_id, title
    FROM pages 
    WHERE namespace = 0 AND NOT is_redirect
    LIMIT 10
"""))
