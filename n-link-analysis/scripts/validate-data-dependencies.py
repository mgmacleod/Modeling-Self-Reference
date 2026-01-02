#!/usr/bin/env python3
"""Validate data dependencies for N-Link analysis scripts.

Supports both local data and HuggingFace dataset sources.

Checks:
1. Required files exist
2. Parquet schemas match expectations
3. Basic data integrity (row counts, null checks, type validation)
4. Cross-file consistency (page_id references)

Usage:
    # Validate local data (default)
    python validate-data-dependencies.py

    # Validate HuggingFace dataset
    python validate-data-dependencies.py --data-source huggingface

    # Override HuggingFace repo
    python validate-data-dependencies.py --data-source huggingface --hf-repo mgmacleod/wikidata1

Exit codes:
  0 = All checks passed
  1 = Validation errors found
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

import duckdb
import pyarrow.parquet as pq

from data_loader import (
    DataLoader,
    add_data_source_args,
    get_data_loader_from_args,
)


REPO_ROOT = Path(__file__).resolve().parents[2]

# Required files with expected schemas
REQUIRED_FILES = {
    "nlink_sequences": {
        "columns": {"page_id": "int64", "link_sequence": "list<item: int64>"},
        "description": "N-link sequences (primary input)",
    },
    "pages": {
        "columns": {"page_id": "int64", "title": "string", "namespace": "int64", "is_redirect": "bool"},
        "description": "Page metadata (for title resolution)",
    },
}

# Multiplex files (optional, but validated if present)
MULTIPLEX_FILES = {
    "multiplex_basin_assignments": {
        "columns": {"page_id": "int64", "N": "int8", "canonical_cycle_id": "string", "depth": "int32"},
        "description": "Basin membership per page per N",
    },
    "tunnel_nodes": {
        "columns": {"page_id": "int64", "is_tunnel_node": "bool", "n_distinct_basins": "int8"},
        "description": "Pages that switch basins across N",
    },
}


def check_file_exists(file_path: Path, loader: DataLoader) -> bool:
    """Check if file exists and is readable."""
    if not file_path.exists():
        print(f"  MISSING: {file_path}")
        return False
    if not file_path.is_file():
        print(f"  NOT A FILE: {file_path}")
        return False
    size_mb = file_path.stat().st_size / (1024 ** 2)
    print(f"  Found: {file_path.name} ({size_mb:.1f} MB)")
    return True


def check_schema(file_path: Path, expected_columns: dict[str, str]) -> bool:
    """Validate Parquet schema matches expectations."""
    try:
        schema = pq.read_schema(file_path)
        actual_columns = {field.name: str(field.type) for field in schema}

        missing = set(expected_columns.keys()) - set(actual_columns.keys())
        extra = set(actual_columns.keys()) - set(expected_columns.keys())

        if missing:
            print(f"    Missing columns: {missing}")
            return False
        if extra:
            print(f"    Extra columns (ok): {extra}")

        # Check types (flexible matching for complex types and integer widths)
        type_mismatches = []
        INTEGER_TYPES = {"int8", "int16", "int32", "int64"}
        for col, expected_type in expected_columns.items():
            actual_type = actual_columns.get(col, "")
            # Normalize type strings for comparison
            if expected_type.startswith("list<"):
                # For list types, just check it's a list
                if not actual_type.startswith("list<"):
                    type_mismatches.append(f"{col}: expected {expected_type}, got {actual_type}")
            elif expected_type in INTEGER_TYPES and actual_type in INTEGER_TYPES:
                # Allow any integer type (int8/16/32/64 are compatible)
                if actual_type != expected_type:
                    print(f"    Column '{col}': {actual_type} (compatible with expected {expected_type})")
            elif expected_type != actual_type:
                type_mismatches.append(f"{col}: expected {expected_type}, got {actual_type}")

        if type_mismatches:
            print(f"    Type mismatches:")
            for mismatch in type_mismatches:
                print(f"      - {mismatch}")
            return False

        print(f"    Schema valid: {len(actual_columns)} columns")
        return True

    except Exception as e:
        print(f"    Schema read error: {e}")
        return False


def check_data_integrity(file_path: Path, file_info: dict) -> bool:
    """Run basic data integrity checks using DuckDB."""
    try:
        con = duckdb.connect()
        table_name = file_path.stem

        # Get row count
        row_count = con.execute(
            f"SELECT COUNT(*) FROM read_parquet('{file_path.as_posix()}')"
        ).fetchone()[0]
        print(f"    Row count: {row_count:,}")

        if row_count == 0:
            print(f"    WARNING: Empty table")
            return False

        # Check for NULLs in critical columns
        columns = file_info.get("columns", {})
        for col in columns.keys():
            null_count = con.execute(
                f"SELECT COUNT(*) FROM read_parquet('{file_path.as_posix()}') WHERE {col} IS NULL"
            ).fetchone()[0]
            if null_count > 0:
                print(f"    Column '{col}' has {null_count:,} NULL values ({100*null_count/row_count:.2f}%)")

        # File-specific checks
        if table_name == "nlink_sequences":
            # Check page_id uniqueness
            unique_count = con.execute(
                f"SELECT COUNT(DISTINCT page_id) FROM read_parquet('{file_path.as_posix()}')"
            ).fetchone()[0]
            if unique_count != row_count:
                print(f"    Duplicate page_ids: {row_count - unique_count:,} duplicates")
                return False
            print(f"    All page_ids unique")

            # Check link_sequence stats
            stats = con.execute(
                f"""
                SELECT
                    MIN(len(link_sequence)) AS min_len,
                    MAX(len(link_sequence)) AS max_len,
                    CAST(AVG(len(link_sequence)) AS INTEGER) AS avg_len,
                    APPROX_QUANTILE(len(link_sequence), 0.5) AS median_len
                FROM read_parquet('{file_path.as_posix()}')
                """
            ).fetchone()
            print(f"    Link sequence lengths: min={stats[0]}, max={stats[1]}, avg={stats[2]}, median={stats[3]}")

        elif table_name == "pages":
            # Check page_id uniqueness
            unique_count = con.execute(
                f"SELECT COUNT(DISTINCT page_id) FROM read_parquet('{file_path.as_posix()}')"
            ).fetchone()[0]
            if unique_count != row_count:
                print(f"    Duplicate page_ids: {row_count - unique_count:,} duplicates")
                return False
            print(f"    All page_ids unique")

            # Check namespace distribution
            ns_dist = con.execute(
                f"""
                SELECT namespace, COUNT(*) AS count
                FROM read_parquet('{file_path.as_posix()}')
                GROUP BY namespace
                ORDER BY count DESC
                LIMIT 5
                """
            ).fetchall()
            print(f"    Top namespaces: {', '.join(f'ns={ns}({cnt:,})' for ns, cnt in ns_dist)}")

        elif table_name == "multiplex_basin_assignments":
            # Check N values are in expected range
            n_values = con.execute(
                f"SELECT DISTINCT N FROM read_parquet('{file_path.as_posix()}') ORDER BY N"
            ).fetchall()
            n_list = [n[0] for n in n_values]
            print(f"    N values: {n_list}")

        elif table_name == "tunnel_nodes":
            # Check tunnel node count
            tunnel_count = con.execute(
                f"SELECT COUNT(*) FROM read_parquet('{file_path.as_posix()}') WHERE is_tunnel_node = true"
            ).fetchone()[0]
            tunnel_pct = 100 * tunnel_count / row_count
            print(f"    Tunnel nodes: {tunnel_count:,} ({tunnel_pct:.2f}%)")

        con.close()
        return True

    except Exception as e:
        print(f"    Integrity check error: {e}")
        return False


def check_cross_file_consistency(loader: DataLoader) -> bool:
    """Check consistency between nlink_sequences and pages."""
    print("\n## Cross-File Consistency Checks")

    paths = loader.paths
    nlink_path = paths.nlink_sequences
    pages_path = paths.pages

    if not (nlink_path.exists() and pages_path.exists()):
        print("  Skipping (required files not present)")
        return True

    try:
        con = duckdb.connect()

        # Check if all page_ids in nlink_sequences exist in pages
        missing = con.execute(
            f"""
            SELECT COUNT(DISTINCT n.page_id) AS missing_count
            FROM read_parquet('{nlink_path.as_posix()}') n
            LEFT JOIN read_parquet('{pages_path.as_posix()}') p
              ON n.page_id = p.page_id
            WHERE p.page_id IS NULL
            """
        ).fetchone()[0]

        total_nlink = con.execute(
            f"SELECT COUNT(*) FROM read_parquet('{nlink_path.as_posix()}')"
        ).fetchone()[0]

        if missing > 0:
            missing_pct = 100 * missing / total_nlink
            if missing_pct > 1.0:
                # Only error if >1% missing
                print(f"  {missing:,} page_ids in nlink_sequences missing from pages ({missing_pct:.2f}%)")
                return False
            else:
                # Small number of missing is ok (edge cases, data pipeline race conditions)
                print(f"  {missing:,} page_ids in nlink_sequences missing from pages ({missing_pct:.4f}%) - minor, likely edge cases")
        else:
            print(f"  All nlink_sequences page_ids exist in pages")

        # Check coverage: what fraction of pages have sequences?
        coverage = con.execute(
            f"""
            SELECT
                (SELECT COUNT(*) FROM read_parquet('{nlink_path.as_posix()}')) AS with_sequences,
                (SELECT COUNT(*) FROM read_parquet('{pages_path.as_posix()}')) AS total_pages
            """
        ).fetchone()

        coverage_pct = 100 * coverage[0] / coverage[1]
        print(f"  Coverage: {coverage[0]:,} / {coverage[1]:,} pages have sequences ({coverage_pct:.1f}%)")

        con.close()
        return True

    except Exception as e:
        print(f"  Consistency check error: {e}")
        return False


def main() -> int:
    parser = argparse.ArgumentParser(
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    add_data_source_args(parser)
    args = parser.parse_args()

    # Get the data loader
    loader = get_data_loader_from_args(args)

    print("=" * 80)
    print("N-Link Analysis Data Dependency Validation")
    print("=" * 80)
    print(f"\nData source: {loader.source_name}")

    all_passed = True

    # Get paths (this may trigger HF download)
    try:
        paths = loader.paths
    except Exception as e:
        print(f"\nFailed to access data source: {e}")
        return 1

    # Check required files
    print("\n## Required Files")
    for file_key, info in REQUIRED_FILES.items():
        file_path = getattr(paths, file_key, None)
        if file_path is None:
            print(f"\n### {file_key}")
            print(f"  Path not configured for this data source")
            all_passed = False
            continue

        print(f"\n### {file_key}")
        print(f"Description: {info['description']}")

        if not check_file_exists(file_path, loader):
            all_passed = False
            continue

        if not check_schema(file_path, info["columns"]):
            all_passed = False
            continue

        if not check_data_integrity(file_path, info):
            all_passed = False

    # Check multiplex files (optional)
    print("\n## Multiplex Files (Optional)")
    for file_key, info in MULTIPLEX_FILES.items():
        file_path = getattr(paths, file_key, None)
        if file_path is None or not file_path.exists():
            print(f"  {file_key}: Not present (optional)")
            continue

        print(f"\n### {file_key}")
        print(f"Description: {info['description']}")

        if not check_file_exists(file_path, loader):
            continue

        if not check_schema(file_path, info["columns"]):
            continue

        check_data_integrity(file_path, info)

    # Cross-file checks
    if not check_cross_file_consistency(loader):
        all_passed = False

    # Check analysis output directory
    print("\n## Analysis Output Directory")
    analysis_dir = loader.get_analysis_output_dir()
    if not analysis_dir.exists():
        print(f"  {analysis_dir} does not exist (will be created on first run)")
    else:
        print(f"  {analysis_dir} exists")
        # List existing files
        existing = list(analysis_dir.glob("*"))
        if existing:
            print(f"    Contains {len(existing)} existing artifacts")
            for f in sorted(existing)[:5]:
                print(f"      - {f.name}")
            if len(existing) > 5:
                print(f"      ... and {len(existing) - 5} more")

    # Summary
    print("\n" + "=" * 80)
    if all_passed:
        print("ALL CHECKS PASSED - Ready to run analysis scripts")
        print("=" * 80)
        print("\nRecommended next steps:")
        if "huggingface" in loader.source_name.lower():
            print("  1. Run a sanity sample:")
            print("     python n-link-analysis/scripts/sample-nlink-traces.py --data-source huggingface --n 5 --num 100")
            print("  2. Trace a single path:")
            print("     python n-link-analysis/scripts/trace-nlink-path.py --data-source huggingface --n 5")
        else:
            print("  1. Run a sanity sample:")
            print("     python n-link-analysis/scripts/sample-nlink-traces.py --n 5 --num 100")
            print("  2. Trace a single path:")
            print("     python n-link-analysis/scripts/trace-nlink-path.py --n 5")
        print("  3. See scripts-reference.md for full documentation")
        return 0
    else:
        print("VALIDATION FAILED - Fix errors above before running analysis")
        print("=" * 80)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
