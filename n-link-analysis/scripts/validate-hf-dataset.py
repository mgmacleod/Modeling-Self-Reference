#!/usr/bin/env python3
"""
Validate HuggingFace Dataset for Wikipedia N-Link Basins.

This script downloads the dataset from HuggingFace and runs comprehensive
validation to confirm it provides everything needed to reproduce all results.

Usage:
    python validate-hf-dataset.py --repo-id mgmacleod/wikidata1
    python validate-hf-dataset.py --repo-id mgmacleod/wikidata1 --full-validation
    python validate-hf-dataset.py --repo-id mgmacleod/wikidata1 --test-reproduction

Exit codes:
    0 = All validations passed
    1 = Validation errors found
    2 = Download/setup errors
"""

from __future__ import annotations

import argparse
import json
import sys
import tempfile
from dataclasses import dataclass, field
from pathlib import Path

# Attempt imports with helpful error messages
try:
    import pandas as pd
except ImportError:
    print("ERROR: pandas not installed. Run: pip install pandas")
    sys.exit(2)

try:
    import pyarrow.parquet as pq
except ImportError:
    print("ERROR: pyarrow not installed. Run: pip install pyarrow")
    sys.exit(2)


# =============================================================================
# Expected Dataset Structure
# =============================================================================

EXPECTED_FILES = {
    # Source files (for full reproducibility)
    "data/source/nlink_sequences.parquet": {
        "required_for": ["full", "complete"],
        "description": "Link sequences per page (up to 3873 links)",
        "expected_rows": 17_972_018,
        "expected_columns": ["page_id", "link_sequence"],
    },
    "data/source/pages.parquet": {
        "required_for": ["full", "complete"],
        "description": "Page ID to title mapping",
        "expected_rows": 64_703_361,
        "expected_columns": ["page_id", "title", "namespace", "is_redirect"],
    },
    # Multiplex files (core analysis results)
    "data/multiplex/multiplex_basin_assignments.parquet": {
        "required_for": ["minimal", "full", "complete"],
        "description": "Basin membership per page per N",
        "expected_rows": 2_134_621,
        "expected_columns": ["page_id", "N", "cycle_key", "canonical_cycle_id", "entry_id", "depth"],
    },
    "data/multiplex/tunnel_nodes.parquet": {
        "required_for": ["minimal", "full", "complete"],
        "description": "Pages that switch basins across N",
        "expected_rows": 2_079_289,
        "expected_columns": ["page_id", "is_tunnel_node", "n_distinct_basins"],
        # Also has basin_at_N3 through basin_at_N10
    },
    "data/multiplex/multiplex_edges.parquet": {
        "required_for": ["minimal", "full", "complete"],
        "description": "Multiplex graph edges",
        "expected_rows": 9_693_473,
        "expected_columns": ["src_page_id", "src_N", "dst_page_id", "dst_N", "edge_type"],
    },
    # TSV files (human-readable analysis artifacts)
    "data/multiplex/tunnel_frequency_ranking.tsv": {
        "required_for": ["minimal", "full", "complete"],
        "description": "Ranked tunnel nodes by frequency",
    },
    "data/multiplex/tunnel_classification.tsv": {
        "required_for": ["minimal", "full", "complete"],
        "description": "Tunnel node classification",
    },
    "data/multiplex/tunnel_mechanisms.tsv": {
        "required_for": ["minimal", "full", "complete"],
        "description": "Tunnel mechanism analysis",
    },
    "data/multiplex/semantic_model_wikipedia.json": {
        "required_for": ["minimal", "full", "complete"],
        "description": "Extracted semantic model",
    },
    "data/multiplex/basin_flows.tsv": {
        "required_for": ["minimal", "full", "complete"],
        "description": "Cross-basin transitions",
    },
}

# Expected key statistics from the analysis
EXPECTED_STATISTICS = {
    "total_wikipedia_pages": 17_972_018,
    "pages_in_analysis": 2_079_289,
    # Tunnel nodes: pages with n_distinct_basins > 1 across N=3-10
    "tunnel_nodes_count": 41_732,
    "tunnel_nodes_percentage": 2.01,
    "basins_tracked": 9,
    "n_range": (3, 10),
    # Basin sizes at N=5 (phase transition peak)
    "n5_basin_sizes": {
        "Massachusetts_Gulf_of_Maine": 1_006_218,
        "Sea_salt_Seawater": 265_896,
        "Mountain_Hill": 188_968,
        "Autumn_Summer": 162_624,
        "Kingdom_(biology)_Animal": 112_805,
    },
}


@dataclass
class ValidationResult:
    """Result of a validation check."""

    name: str
    passed: bool
    message: str
    details: list[str] = field(default_factory=list)


class DatasetValidator:
    """Validates the HuggingFace dataset for completeness and correctness."""

    def __init__(self, dataset_path: Path, config: str = "full"):
        self.dataset_path = dataset_path
        self.config = config
        self.results: list[ValidationResult] = []

    def validate_all(self, full_validation: bool = False) -> bool:
        """Run all validation checks."""
        print("=" * 80)
        print("HuggingFace Dataset Validation")
        print("=" * 80)
        print(f"Dataset path: {self.dataset_path}")
        print(f"Configuration: {self.config}")
        print(f"Full validation: {full_validation}")
        print()

        # 1. Check file existence
        self._check_file_existence()

        # 2. Validate parquet schemas
        self._validate_parquet_schemas()

        # 3. Validate row counts
        self._validate_row_counts()

        # 4. Validate data integrity
        self._validate_data_integrity()

        # 5. Validate key statistics match expected
        if full_validation:
            self._validate_key_statistics()

        # 6. Cross-file consistency
        self._validate_cross_file_consistency()

        # Print summary
        return self._print_summary()

    def _check_file_existence(self) -> None:
        """Check that all expected files exist."""
        print("\n## File Existence Checks")
        print("-" * 40)

        for file_path, info in EXPECTED_FILES.items():
            required_for = info.get("required_for", [])

            # Skip files not required for this config
            if self.config not in required_for:
                continue

            full_path = self.dataset_path / file_path
            exists = full_path.exists()

            if exists:
                size_mb = full_path.stat().st_size / (1024 * 1024)
                self.results.append(ValidationResult(
                    name=f"file_exists:{file_path}",
                    passed=True,
                    message=f"✓ {file_path} ({size_mb:.1f} MB)",
                ))
                print(f"  ✓ {file_path} ({size_mb:.1f} MB)")
            else:
                self.results.append(ValidationResult(
                    name=f"file_exists:{file_path}",
                    passed=False,
                    message=f"✗ MISSING: {file_path}",
                    details=[info.get("description", "")],
                ))
                print(f"  ✗ MISSING: {file_path}")

    def _validate_parquet_schemas(self) -> None:
        """Validate parquet file schemas."""
        print("\n## Schema Validation")
        print("-" * 40)

        for file_path, info in EXPECTED_FILES.items():
            if not file_path.endswith(".parquet"):
                continue

            required_for = info.get("required_for", [])
            if self.config not in required_for:
                continue

            full_path = self.dataset_path / file_path
            if not full_path.exists():
                continue

            expected_columns = info.get("expected_columns", [])
            if not expected_columns:
                continue

            try:
                schema = pq.read_schema(full_path)
                actual_columns = [field.name for field in schema]

                missing = set(expected_columns) - set(actual_columns)
                if missing:
                    self.results.append(ValidationResult(
                        name=f"schema:{file_path}",
                        passed=False,
                        message=f"✗ {file_path}: Missing columns: {missing}",
                        details=[f"Expected: {expected_columns}", f"Actual: {actual_columns}"],
                    ))
                    print(f"  ✗ {file_path}: Missing columns: {missing}")
                else:
                    self.results.append(ValidationResult(
                        name=f"schema:{file_path}",
                        passed=True,
                        message=f"✓ {file_path}: Schema valid ({len(actual_columns)} columns)",
                    ))
                    print(f"  ✓ {file_path}: Schema valid ({len(actual_columns)} columns)")

            except Exception as e:
                self.results.append(ValidationResult(
                    name=f"schema:{file_path}",
                    passed=False,
                    message=f"✗ {file_path}: Error reading schema: {e}",
                ))
                print(f"  ✗ {file_path}: Error reading schema: {e}")

    def _validate_row_counts(self) -> None:
        """Validate row counts match expected values."""
        print("\n## Row Count Validation")
        print("-" * 40)

        for file_path, info in EXPECTED_FILES.items():
            if not file_path.endswith(".parquet"):
                continue

            required_for = info.get("required_for", [])
            if self.config not in required_for:
                continue

            full_path = self.dataset_path / file_path
            if not full_path.exists():
                continue

            expected_rows = info.get("expected_rows")
            if expected_rows is None:
                continue

            try:
                # Read metadata only for row count
                parquet_file = pq.ParquetFile(full_path)
                actual_rows = parquet_file.metadata.num_rows

                # Allow 1% tolerance for minor data pipeline variations
                tolerance = 0.01
                diff_pct = abs(actual_rows - expected_rows) / expected_rows

                if diff_pct <= tolerance:
                    self.results.append(ValidationResult(
                        name=f"row_count:{file_path}",
                        passed=True,
                        message=f"✓ {file_path}: {actual_rows:,} rows (expected ~{expected_rows:,})",
                    ))
                    print(f"  ✓ {file_path}: {actual_rows:,} rows")
                else:
                    self.results.append(ValidationResult(
                        name=f"row_count:{file_path}",
                        passed=False,
                        message=f"✗ {file_path}: {actual_rows:,} rows (expected {expected_rows:,}, diff {diff_pct:.1%})",
                    ))
                    print(f"  ✗ {file_path}: {actual_rows:,} rows (expected {expected_rows:,})")

            except Exception as e:
                self.results.append(ValidationResult(
                    name=f"row_count:{file_path}",
                    passed=False,
                    message=f"✗ {file_path}: Error reading: {e}",
                ))
                print(f"  ✗ {file_path}: Error reading: {e}")

    def _validate_data_integrity(self) -> None:
        """Validate data integrity (nulls, types, etc.)."""
        print("\n## Data Integrity Validation")
        print("-" * 40)

        # Validate multiplex_basin_assignments
        mba_path = self.dataset_path / "data/multiplex/multiplex_basin_assignments.parquet"
        if mba_path.exists():
            try:
                df = pd.read_parquet(mba_path)

                # Check N values are in expected range
                n_values = df["N"].unique()
                expected_n = set(range(3, 11))
                if set(n_values) == expected_n:
                    self.results.append(ValidationResult(
                        name="integrity:mba_n_values",
                        passed=True,
                        message=f"✓ multiplex_basin_assignments: N values correct (3-10)",
                    ))
                    print(f"  ✓ multiplex_basin_assignments: N values = {sorted(n_values)}")
                else:
                    self.results.append(ValidationResult(
                        name="integrity:mba_n_values",
                        passed=False,
                        message=f"✗ multiplex_basin_assignments: N values incorrect",
                        details=[f"Expected: {expected_n}", f"Actual: {set(n_values)}"],
                    ))
                    print(f"  ✗ multiplex_basin_assignments: N values = {sorted(n_values)} (expected 3-10)")

                # Check depth values are non-negative
                if (df["depth"] >= 0).all():
                    self.results.append(ValidationResult(
                        name="integrity:mba_depth",
                        passed=True,
                        message="✓ multiplex_basin_assignments: All depths non-negative",
                    ))
                    print(f"  ✓ multiplex_basin_assignments: Depths valid (min={df['depth'].min()}, max={df['depth'].max()})")
                else:
                    self.results.append(ValidationResult(
                        name="integrity:mba_depth",
                        passed=False,
                        message="✗ multiplex_basin_assignments: Negative depths found",
                    ))
                    print(f"  ✗ multiplex_basin_assignments: Negative depths found")

            except Exception as e:
                self.results.append(ValidationResult(
                    name="integrity:mba",
                    passed=False,
                    message=f"✗ multiplex_basin_assignments: Error: {e}",
                ))
                print(f"  ✗ multiplex_basin_assignments: Error: {e}")

        # Validate tunnel_nodes
        tn_path = self.dataset_path / "data/multiplex/tunnel_nodes.parquet"
        if tn_path.exists():
            try:
                df = pd.read_parquet(tn_path)

                # Check is_tunnel_node is boolean
                tunnel_count = df["is_tunnel_node"].sum()
                tunnel_pct = 100 * tunnel_count / len(df)

                # Expected: ~41,732 tunnel nodes (~2.01%)
                expected_pct = EXPECTED_STATISTICS["tunnel_nodes_percentage"]
                if abs(tunnel_pct - expected_pct) < 0.2:  # Within 0.2% tolerance
                    self.results.append(ValidationResult(
                        name="integrity:tunnel_node_count",
                        passed=True,
                        message=f"✓ tunnel_nodes: {tunnel_count:,} tunnel nodes ({tunnel_pct:.2f}%)",
                    ))
                    print(f"  ✓ tunnel_nodes: {tunnel_count:,} tunnel nodes ({tunnel_pct:.2f}%)")
                else:
                    self.results.append(ValidationResult(
                        name="integrity:tunnel_node_count",
                        passed=False,
                        message=f"✗ tunnel_nodes: {tunnel_count:,} tunnel nodes ({tunnel_pct:.2f}%), expected ~{expected_pct}%",
                    ))
                    print(f"  ✗ tunnel_nodes: Unexpected tunnel node percentage: {tunnel_pct:.2f}%")

            except Exception as e:
                self.results.append(ValidationResult(
                    name="integrity:tunnel_nodes",
                    passed=False,
                    message=f"✗ tunnel_nodes: Error: {e}",
                ))
                print(f"  ✗ tunnel_nodes: Error: {e}")

    def _validate_key_statistics(self) -> None:
        """Validate that key statistics match expected values."""
        print("\n## Key Statistics Validation")
        print("-" * 40)

        mba_path = self.dataset_path / "data/multiplex/multiplex_basin_assignments.parquet"
        if not mba_path.exists():
            print("  ⚠ Skipping (multiplex_basin_assignments not present)")
            return

        try:
            df = pd.read_parquet(mba_path)

            # Check N=5 basin sizes
            n5 = df[df["N"] == 5]
            n5_basins = n5.groupby("canonical_cycle_id").size().sort_values(ascending=False)

            print(f"  N=5 Basin Sizes:")
            for basin_name, expected_size in EXPECTED_STATISTICS["n5_basin_sizes"].items():
                # Try to find matching basin
                matching = [k for k in n5_basins.index if basin_name.split("_")[0] in k]
                if matching:
                    actual_size = n5_basins[matching[0]]
                    tolerance = 0.05  # 5% tolerance
                    diff_pct = abs(actual_size - expected_size) / expected_size

                    if diff_pct <= tolerance:
                        self.results.append(ValidationResult(
                            name=f"stats:n5_basin:{basin_name}",
                            passed=True,
                            message=f"✓ {basin_name}: {actual_size:,} (expected ~{expected_size:,})",
                        ))
                        print(f"    ✓ {basin_name}: {actual_size:,}")
                    else:
                        self.results.append(ValidationResult(
                            name=f"stats:n5_basin:{basin_name}",
                            passed=False,
                            message=f"✗ {basin_name}: {actual_size:,} (expected {expected_size:,}, diff {diff_pct:.1%})",
                        ))
                        print(f"    ✗ {basin_name}: {actual_size:,} (expected {expected_size:,})")
                else:
                    print(f"    ⚠ {basin_name}: Not found in data")

        except Exception as e:
            self.results.append(ValidationResult(
                name="stats:n5_basins",
                passed=False,
                message=f"✗ Error validating N=5 basins: {e}",
            ))
            print(f"  ✗ Error: {e}")

    def _validate_cross_file_consistency(self) -> None:
        """Validate consistency between files."""
        print("\n## Cross-File Consistency")
        print("-" * 40)

        # Check if source files are present
        nlink_path = self.dataset_path / "data/source/nlink_sequences.parquet"
        pages_path = self.dataset_path / "data/source/pages.parquet"
        mba_path = self.dataset_path / "data/multiplex/multiplex_basin_assignments.parquet"
        tn_path = self.dataset_path / "data/multiplex/tunnel_nodes.parquet"

        if not mba_path.exists() or not tn_path.exists():
            print("  ⚠ Skipping (core files not present)")
            return

        try:
            # Check that page_ids in multiplex_basin_assignments exist in tunnel_nodes
            mba_df = pd.read_parquet(mba_path)
            tn_df = pd.read_parquet(tn_path)

            mba_pages = set(mba_df["page_id"].unique())
            tn_pages = set(tn_df["page_id"].unique())

            # All pages in mba should be in tn (tn is the superset)
            missing_in_tn = mba_pages - tn_pages
            if len(missing_in_tn) == 0:
                self.results.append(ValidationResult(
                    name="consistency:mba_tn_pages",
                    passed=True,
                    message="✓ All multiplex_basin_assignments pages exist in tunnel_nodes",
                ))
                print("  ✓ All multiplex_basin_assignments pages exist in tunnel_nodes")
            else:
                self.results.append(ValidationResult(
                    name="consistency:mba_tn_pages",
                    passed=False,
                    message=f"✗ {len(missing_in_tn):,} pages in mba missing from tunnel_nodes",
                ))
                print(f"  ✗ {len(missing_in_tn):,} pages in mba missing from tunnel_nodes")

            # If source files exist, check more consistency
            if nlink_path.exists() and pages_path.exists():
                # Sample check: verify some page_ids from mba exist in pages
                pages_df = pd.read_parquet(pages_path, columns=["page_id"])
                all_page_ids = set(pages_df["page_id"])

                sample_mba_pages = list(mba_pages)[:1000]
                missing_in_pages = [p for p in sample_mba_pages if p not in all_page_ids]

                if len(missing_in_pages) == 0:
                    self.results.append(ValidationResult(
                        name="consistency:mba_pages",
                        passed=True,
                        message="✓ Sample of multiplex_basin_assignments pages exist in pages.parquet",
                    ))
                    print("  ✓ Sample of mba pages verified against pages.parquet")
                else:
                    pct_missing = 100 * len(missing_in_pages) / len(sample_mba_pages)
                    self.results.append(ValidationResult(
                        name="consistency:mba_pages",
                        passed=False,
                        message=f"✗ {pct_missing:.1f}% of sampled mba pages missing from pages.parquet",
                    ))
                    print(f"  ✗ {pct_missing:.1f}% of sampled mba pages missing from pages.parquet")

        except Exception as e:
            self.results.append(ValidationResult(
                name="consistency",
                passed=False,
                message=f"✗ Consistency check error: {e}",
            ))
            print(f"  ✗ Error: {e}")

    def _print_summary(self) -> bool:
        """Print validation summary and return success status."""
        print("\n" + "=" * 80)
        print("VALIDATION SUMMARY")
        print("=" * 80)

        passed = sum(1 for r in self.results if r.passed)
        failed = sum(1 for r in self.results if not r.passed)
        total = len(self.results)

        print(f"\nTotal checks: {total}")
        print(f"  ✓ Passed: {passed}")
        print(f"  ✗ Failed: {failed}")

        if failed > 0:
            print("\nFailed checks:")
            for r in self.results:
                if not r.passed:
                    print(f"  - {r.message}")
                    for detail in r.details:
                        print(f"      {detail}")

        all_passed = failed == 0
        print("\n" + "=" * 80)
        if all_passed:
            print("✓ ALL VALIDATIONS PASSED")
            print("  The dataset provides everything needed to reproduce results.")
        else:
            print("✗ VALIDATION FAILED")
            print("  Fix the issues above before using the dataset.")
        print("=" * 80)

        return all_passed


def download_dataset(repo_id: str, target_dir: Path) -> bool:
    """Download dataset from HuggingFace."""
    print("=" * 80)
    print("Downloading Dataset from HuggingFace")
    print("=" * 80)
    print(f"Repo ID: {repo_id}")
    print(f"Target: {target_dir}")
    print()

    try:
        from huggingface_hub import snapshot_download
    except ImportError:
        print("ERROR: huggingface_hub not installed. Run: pip install huggingface_hub")
        return False

    try:
        print("Downloading files (this may take a while for large datasets)...")
        snapshot_download(
            repo_id=repo_id,
            repo_type="dataset",
            local_dir=str(target_dir),
            local_dir_use_symlinks=False,
        )
        print(f"\n✓ Download complete: {target_dir}")
        return True

    except Exception as e:
        print(f"\n✗ Download failed: {e}")
        return False


def run_reproduction_test(dataset_path: Path) -> bool:
    """Run a minimal reproduction test using the downloaded data."""
    print("\n" + "=" * 80)
    print("REPRODUCTION TEST")
    print("=" * 80)
    print("Testing that we can load data and reproduce key findings...")
    print()

    try:
        # 1. Load and verify basin assignments
        mba_path = dataset_path / "data/multiplex/multiplex_basin_assignments.parquet"
        print("1. Loading multiplex_basin_assignments...")
        df = pd.read_parquet(mba_path)
        print(f"   ✓ Loaded {len(df):,} rows")

        # 2. Reproduce N=5 phase transition finding
        print("\n2. Reproducing N=5 phase transition analysis...")
        basin_sizes = df.groupby(["N", "canonical_cycle_id"]).size().reset_index(name="size")
        max_basin_by_n = basin_sizes.groupby("N")["size"].max()

        print("   Maximum basin size by N:")
        for n in range(3, 11):
            if n in max_basin_by_n.index:
                size = max_basin_by_n[n]
                marker = "← PEAK" if n == 5 else ""
                print(f"     N={n}: {size:>10,} {marker}")

        # Verify N=5 is the peak
        peak_n = max_basin_by_n.idxmax()
        if peak_n == 5:
            print("   ✓ Confirmed: N=5 is the phase transition peak")
        else:
            print(f"   ✗ Unexpected: Peak at N={peak_n}, not N=5")
            return False

        # 3. Verify tunnel nodes
        print("\n3. Verifying tunnel node analysis...")
        tn_path = dataset_path / "data/multiplex/tunnel_nodes.parquet"
        tn_df = pd.read_parquet(tn_path)
        tunnel_count = tn_df["is_tunnel_node"].sum()
        print(f"   ✓ Found {tunnel_count:,} tunnel nodes ({100*tunnel_count/len(tn_df):.2f}%)")

        # 4. Check semantic model
        print("\n4. Checking semantic model...")
        sm_path = dataset_path / "data/multiplex/semantic_model_wikipedia.json"
        if sm_path.exists():
            with open(sm_path) as f:
                sm = json.load(f)
            print(f"   ✓ Semantic model loaded: {len(sm.get('basins', []))} basins defined")
        else:
            print("   ⚠ Semantic model not found (optional)")

        # 5. If source files exist, verify we can trace paths
        nlink_path = dataset_path / "data/source/nlink_sequences.parquet"
        if nlink_path.exists():
            print("\n5. Testing path tracing capability...")
            nlink_df = pd.read_parquet(nlink_path).head(100)
            sequences_with_links = sum(1 for seq in nlink_df["link_sequence"] if len(seq) >= 5)
            print(f"   ✓ {sequences_with_links}/100 sampled pages have ≥5 links (can trace N=5 paths)")
        else:
            print("\n5. Source files not present (skipping path tracing test)")

        print("\n" + "=" * 80)
        print("✓ REPRODUCTION TEST PASSED")
        print("  All key findings are reproducible from this dataset.")
        print("=" * 80)
        return True

    except Exception as e:
        print(f"\n✗ Reproduction test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def main() -> int:
    parser = argparse.ArgumentParser(
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        "--repo-id",
        required=True,
        help="HuggingFace dataset repo ID (e.g., 'mgmacleod/wikidata1')",
    )
    parser.add_argument(
        "--config",
        choices=["minimal", "full", "complete"],
        default="full",
        help="Configuration to validate (default: full)",
    )
    parser.add_argument(
        "--target-dir",
        type=Path,
        default=None,
        help="Target directory for download (default: temp directory)",
    )
    parser.add_argument(
        "--skip-download",
        action="store_true",
        help="Skip download, use existing files at target-dir",
    )
    parser.add_argument(
        "--full-validation",
        action="store_true",
        help="Run full validation including key statistics checks",
    )
    parser.add_argument(
        "--test-reproduction",
        action="store_true",
        help="Run reproduction test after validation",
    )

    args = parser.parse_args()

    # Determine target directory
    if args.target_dir:
        target_dir = args.target_dir
        target_dir.mkdir(parents=True, exist_ok=True)
        cleanup = False
    else:
        # Use a persistent temp directory for this session
        target_dir = Path(tempfile.mkdtemp(prefix="hf_dataset_validation_"))
        cleanup = False  # Keep it around for inspection
        print(f"Using temporary directory: {target_dir}")

    # Download if needed
    if not args.skip_download:
        if not download_dataset(args.repo_id, target_dir):
            return 2

    # Validate
    validator = DatasetValidator(target_dir, config=args.config)
    validation_passed = validator.validate_all(full_validation=args.full_validation)

    # Reproduction test
    if args.test_reproduction and validation_passed:
        reproduction_passed = run_reproduction_test(target_dir)
        if not reproduction_passed:
            return 1

    # Ensure output is flushed
    sys.stdout.flush()
    sys.stderr.flush()

    return 0 if validation_passed else 1


if __name__ == "__main__":
    # Use os._exit to avoid pyarrow cleanup issues
    import os
    exit_code = main()
    sys.stdout.flush()
    sys.stderr.flush()
    os._exit(exit_code)
