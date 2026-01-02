# Hugging Face Upload Manifest

**Purpose**: Checklist and file manifest for uploading the Wikipedia N-Link Basins dataset to Hugging Face.

---

## Upload Configurations

### Option A: Minimal — 125 MB

The multiplex analysis results only. Sufficient for exploring findings but cannot regenerate figures.

```
wikipedia-nlink-basins/
├── README.md                    # DATASET_CARD.md content
└── data/
    └── multiplex/
        ├── multiplex_basin_assignments.parquet   # 11.2 MB
        ├── tunnel_nodes.parquet                  # 10.3 MB
        ├── multiplex_edges.parquet               # 86.3 MB
        ├── tunnel_frequency_ranking.tsv          # 4.7 MB
        ├── tunnel_classification.tsv             # 7.5 MB
        ├── tunnel_mechanisms.tsv                 # 1.8 MB
        ├── tunnel_nodes_summary.tsv              # 3.2 MB
        ├── basin_flows.tsv                       # 4 KB
        ├── basin_stability_scores.tsv            # 1 KB
        ├── cycle_identity_map.tsv                # 1 KB
        └── semantic_model_wikipedia.json         # 43 KB
```

**Pros**: Small, focused, contains all key findings
**Cons**: Cannot regenerate reports, figures, or visualizations

---

### Option B: Full Reproducibility (Recommended) — 1.8 GB

Everything needed to regenerate all reports, figures, and visualizations.

```
wikipedia-nlink-basins/
├── README.md
└── data/
    ├── source/
    │   ├── nlink_sequences.parquet               # 686 MB (link sequences for any N)
    │   └── pages.parquet                         # 939 MB (page ID → title mapping)
    ├── multiplex/
    │   └── [all files from Option A]             # 125 MB
    └── analysis/
        ├── branches_n={3-10}_*_assignments.parquet  # 20 MB (per-N basin assignments)
        └── basin_pointcloud_n=5_*.parquet           # 16 MB (3D geometry data)
```

**Pros**: Full reproducibility - regenerate any report, figure, or visualization
**Cons**: Large download (1.8 GB)

---

### Option C: Research Complete — 1.85 GB

Includes all TSV analysis artifacts for detailed per-N study.

```
wikipedia-nlink-basins/
├── README.md
└── data/
    ├── source/
    │   └── [same as Option B]
    ├── multiplex/
    │   └── [same as Option A]
    └── analysis/
        ├── branches_n={3-10}_*_assignments.parquet  # Per-cycle basins
        ├── basin_pointcloud_*.parquet               # 3D geometry data
        ├── branches_*_branches_all.tsv              # Branch statistics
        ├── basin_n=*_*_layers.tsv                   # Layer breakdowns
        └── branch_trunkiness_*.tsv                  # Trunkiness metrics
```

---

## File-by-File Manifest

### Core Files (Must Include)

| File | Size | Rows | Priority | Notes |
|------|------|------|----------|-------|
| `multiplex_basin_assignments.parquet` | 11.2 MB | 2,134,621 | **Required** | Core finding data |
| `tunnel_nodes.parquet` | 10.3 MB | 2,079,289 | **Required** | Tunnel node classification |
| `DATASET_CARD.md` → `README.md` | 5 KB | - | **Required** | HF dataset card |

### Recommended Additions

| File | Size | Rows | Priority | Notes |
|------|------|------|----------|-------|
| `multiplex_edges.parquet` | 86.3 MB | 9,693,473 | High | Graph structure |
| `tunnel_frequency_ranking.tsv` | 4.7 MB | 41,732 | High | Ranked tunnel nodes |
| `semantic_model_wikipedia.json` | 43 KB | - | Medium | Extracted semantic model |
| `basin_flows.tsv` | 4 KB | 58 | Medium | Cross-basin transitions |

### Source Data (For Reproducibility)

| File | Size | Rows | Priority | Notes |
|------|------|------|----------|-------|
| `nlink_sequences.parquet` | 686 MB | 17,972,018 | Optional | Enables any-N computation |
| `pages.parquet` | 939 MB | 64,703,361 | Optional | Page ID → title mapping |

### Analysis Artifacts (Optional)

| Pattern | Total Size | Files | Priority | Notes |
|---------|------------|-------|----------|-------|
| `branches_n=5_*_assignments.parquet` | ~15 MB | 9 | Low | N=5 individual basins |
| `branches_n={3,4,6,7}_*.parquet` | ~5 MB | 12 | Low | Other N values |
| `branches_n={8,9,10}_*.parquet` | ~1 MB | 18 | Low | Extended range |
| `basin_pointcloud_*.parquet` | ~15 MB | 9 | Low | 3D visualization data |

---

## Pre-Upload Checklist

### Data Validation

- [x] All parquet files readable: `python -c "import pandas; pandas.read_parquet('file.parquet')"` ✓ Validated 2026-01-02
- [x] Row counts match documentation ✓ Validated 2026-01-02
- [x] No PII or sensitive data (Wikipedia is public) ✓ Validated 2026-01-02
- [x] Schema matches documentation ✓ Updated 2026-01-02

### Documentation

- [ ] DATASET_CARD.md follows HF template
- [ ] License specified (CC BY-SA 4.0)
- [ ] Citation format provided
- [ ] Usage examples tested

### Technical

- [ ] Total size under HF limits (50 GB for free tier)
- [ ] File names follow conventions (no spaces, lowercase)
- [ ] Parquet compression optimal

---

## Upload Commands

### Using huggingface_hub CLI

```bash
# Install
pip install huggingface_hub

# Login
huggingface-cli login

# Create dataset repo
huggingface-cli repo create wikipedia-nlink-basins --type dataset

# Upload Option A (minimal)
cd data/wikipedia/processed
huggingface-cli upload your-username/wikipedia-nlink-basins multiplex/ data/multiplex/

# Upload DATASET_CARD as README
cp ../../DATASET_CARD.md README.md
huggingface-cli upload your-username/wikipedia-nlink-basins README.md
```

### Using Python

```python
from huggingface_hub import HfApi, upload_folder

api = HfApi()

# Create repo
api.create_repo("wikipedia-nlink-basins", repo_type="dataset")

# Upload folder
upload_folder(
    folder_path="data/wikipedia/processed/multiplex",
    repo_id="your-username/wikipedia-nlink-basins",
    repo_type="dataset",
    path_in_repo="data/multiplex"
)
```

---

## Post-Upload Verification

1. **Dataset loads correctly**:
   ```python
   from datasets import load_dataset
   ds = load_dataset("your-username/wikipedia-nlink-basins")
   print(ds)
   ```

2. **Preview works** on HF website

3. **Size matches** expected

4. **Tags appear** in HF search

---

## Size Summary

| Configuration | Size | Use Case |
|---------------|------|----------|
| Minimal (Option A) | 125 MB | Explore findings only |
| Full Reproducibility (Option B) | 1.8 GB | Regenerate all reports/figures |
| Research Complete (Option C) | 1.85 GB | Per-N detailed analysis |

**Recommendation**: Use Option B for full reproducibility of all reports, figures, and visualizations.

---

**Last Updated**: 2026-01-02
