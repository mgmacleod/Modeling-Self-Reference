#!/usr/bin/env python3
"""
Upload Wikipedia N-Link Basins dataset to Hugging Face.

Usage:
    python upload-to-huggingface.py --repo-id YOUR_USERNAME/wikipedia-nlink-basins
    python upload-to-huggingface.py --repo-id YOUR_USERNAME/wikipedia-nlink-basins --dry-run
    python upload-to-huggingface.py --repo-id YOUR_USERNAME/wikipedia-nlink-basins --config minimal

Requires HF_TOKEN in .env file or environment variable.
"""

import argparse
import os
import shutil
import sys
from pathlib import Path

# Paths
PROJECT_ROOT = Path(__file__).parent.parent.parent


def load_env():
    """Load environment variables from .env file."""
    env_file = PROJECT_ROOT / ".env"
    if env_file.exists():
        with open(env_file) as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#") and "=" in line:
                    key, value = line.split("=", 1)
                    os.environ.setdefault(key.strip(), value.strip())


load_env()
DATA_ROOT = PROJECT_ROOT / "data" / "wikipedia" / "processed"
REPORT_DIR = Path(__file__).parent.parent / "report"
STAGING_DIR = PROJECT_ROOT / "data" / "huggingface-staging"


def get_file_manifest(config: str) -> dict[str, list[tuple[Path, str]]]:
    """Get files to upload based on configuration."""

    manifest = {
        "source": [],
        "multiplex": [],
        "analysis": [],
    }

    # Multiplex files (all configs)
    multiplex_files = [
        "multiplex_basin_assignments.parquet",
        "tunnel_nodes.parquet",
        "multiplex_edges.parquet",
        "tunnel_frequency_ranking.tsv",
        "tunnel_classification.tsv",
        "tunnel_mechanisms.tsv",
        "tunnel_nodes_summary.tsv",
        "basin_flows.tsv",
        "basin_stability_scores.tsv",
        "cycle_identity_map.tsv",
        "semantic_model_wikipedia.json",
        "basin_intersection_summary.tsv",
        "basin_intersection_by_cycle.tsv",
        "tunneling_traces.tsv",
        "tunneling_validation_metrics.tsv",
        "tunnel_mechanism_summary.tsv",
        "tunnel_top_100.tsv",
        "multiplex_cross_n_paths.tsv",
        "multiplex_layer_connectivity.tsv",
        "multiplex_reachability_summary.tsv",
    ]

    for fname in multiplex_files:
        fpath = DATA_ROOT / "multiplex" / fname
        if fpath.exists():
            manifest["multiplex"].append((fpath, f"data/multiplex/{fname}"))

    if config in ("full", "complete"):
        # Source files
        manifest["source"].append(
            (DATA_ROOT / "nlink_sequences.parquet", "data/source/nlink_sequences.parquet")
        )
        manifest["source"].append(
            (DATA_ROOT / "pages.parquet", "data/source/pages.parquet")
        )

        # Analysis files - parquet only for 'full', all for 'complete'
        analysis_dir = DATA_ROOT / "analysis"

        # Per-N basin assignments
        for f in analysis_dir.glob("branches_n=*_*_assignments.parquet"):
            manifest["analysis"].append((f, f"data/analysis/{f.name}"))

        # 3D pointcloud data
        for f in analysis_dir.glob("basin_pointcloud_*.parquet"):
            manifest["analysis"].append((f, f"data/analysis/{f.name}"))

        if config == "complete":
            # Include TSV analysis artifacts
            for f in analysis_dir.glob("branches_*_branches_all.tsv"):
                manifest["analysis"].append((f, f"data/analysis/{f.name}"))
            for f in analysis_dir.glob("basin_n=*_*_layers.tsv"):
                manifest["analysis"].append((f, f"data/analysis/{f.name}"))
            for f in analysis_dir.glob("branch_trunkiness_*.tsv"):
                manifest["analysis"].append((f, f"data/analysis/{f.name}"))

    return manifest


def calculate_total_size(manifest: dict) -> int:
    """Calculate total size in bytes."""
    total = 0
    for category, files in manifest.items():
        for src, _ in files:
            if src.exists():
                total += src.stat().st_size
    return total


def stage_files(manifest: dict, staging_dir: Path) -> None:
    """Copy files to staging directory with correct structure."""
    if staging_dir.exists():
        shutil.rmtree(staging_dir)
    staging_dir.mkdir(parents=True)

    for category, files in manifest.items():
        for src, dst_rel in files:
            dst = staging_dir / dst_rel
            dst.parent.mkdir(parents=True, exist_ok=True)
            print(f"  Copying {src.name} -> {dst_rel}")
            shutil.copy2(src, dst)

    # Copy README
    readme_src = REPORT_DIR / "DATASET_CARD.md"
    readme_dst = staging_dir / "README.md"
    print(f"  Copying DATASET_CARD.md -> README.md")
    shutil.copy2(readme_src, readme_dst)


def upload_to_hf(staging_dir: Path, repo_id: str, dry_run: bool = False) -> None:
    """Upload staged files to Hugging Face."""
    if dry_run:
        print(f"\n[DRY RUN] Would upload to: {repo_id}")
        print(f"[DRY RUN] Files in staging directory:")
        total_size = 0
        for f in sorted(staging_dir.rglob("*")):
            if f.is_file():
                size_mb = f.stat().st_size / (1024 * 1024)
                total_size += size_mb
                print(f"  {f.relative_to(staging_dir)} ({size_mb:.2f} MB)")
        print(f"\n[DRY RUN] Total: {total_size:.2f} MB ({total_size/1024:.2f} GB)")
        print(f"\nTo upload for real, run without --dry-run")
        return

    try:
        from huggingface_hub import HfApi, create_repo
    except ImportError:
        print("ERROR: huggingface_hub not installed. Run: pip install huggingface_hub")
        sys.exit(1)

    api = HfApi()

    # Create repo if it doesn't exist
    print(f"\nCreating/verifying repo: {repo_id}")
    try:
        create_repo(repo_id, repo_type="dataset", exist_ok=True)
    except Exception as e:
        print(f"Note: {e}")

    # Upload
    print(f"\nUploading to {repo_id}...")
    api.upload_folder(
        folder_path=str(staging_dir),
        repo_id=repo_id,
        repo_type="dataset",
        commit_message="Upload Wikipedia N-Link Basins dataset (Full Reproducibility config)",
    )

    print(f"\n✓ Upload complete!")
    print(f"  View at: https://huggingface.co/datasets/{repo_id}")


def main():
    parser = argparse.ArgumentParser(
        description="Upload Wikipedia N-Link Basins dataset to Hugging Face"
    )
    parser.add_argument(
        "--repo-id",
        required=True,
        help="Hugging Face repo ID (e.g., 'username/wikipedia-nlink-basins')"
    )
    parser.add_argument(
        "--config",
        choices=["minimal", "full", "complete"],
        default="full",
        help="Upload configuration: minimal (125MB), full (1.8GB, recommended), complete (1.85GB)"
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show what would be uploaded without actually uploading"
    )
    parser.add_argument(
        "--skip-staging",
        action="store_true",
        help="Skip staging step (use existing staging directory)"
    )

    args = parser.parse_args()

    print("=" * 60)
    print("Wikipedia N-Link Basins - Hugging Face Upload")
    print("=" * 60)
    print(f"Config: {args.config}")
    print(f"Repo: {args.repo_id}")
    print(f"Dry run: {args.dry_run}")

    # Build manifest
    print("\nBuilding file manifest...")
    manifest = get_file_manifest(args.config)

    total_files = sum(len(files) for files in manifest.values())
    total_size = calculate_total_size(manifest)

    print(f"\nFiles to upload:")
    for category, files in manifest.items():
        if files:
            cat_size = sum(f[0].stat().st_size for f in files if f[0].exists())
            print(f"  {category}/: {len(files)} files ({cat_size / (1024*1024):.1f} MB)")

    print(f"\nTotal: {total_files} files ({total_size / (1024*1024*1024):.2f} GB)")

    # Stage files
    if not args.skip_staging:
        print(f"\nStaging files to {STAGING_DIR}...")
        stage_files(manifest, STAGING_DIR)
        print("✓ Staging complete")

    # Upload
    upload_to_hf(STAGING_DIR, args.repo_id, args.dry_run)


if __name__ == "__main__":
    main()
