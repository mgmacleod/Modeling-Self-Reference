# Hugging Face Upload Manifest

**Purpose**: Checklist and file manifest for uploading the Wikipedia N-Link Basins dataset to Hugging Face.

---

## Upload Configurations

### Option A: Minimal (Recommended) — 115 MB

The multiplex analysis results only. Sufficient for most research use cases.

```
wikipedia-nlink-basins/
├── README.md                    # DATASET_CARD.md content
└── data/
    └── multiplex/
        ├── multiplex_basin_assignments.parquet   # 11.7 MB
        ├── tunnel_nodes.parquet                   # 9.7 MB
        ├── multiplex_edges.parquet                # 87 MB
        ├── tunnel_frequency_ranking.tsv           # 972 KB
        ├── tunnel_classification.tsv              # 1.6 MB
        ├── tunnel_mechanisms.tsv                  # 1.8 MB
        ├── basin_flows.tsv                        # 1 KB
        ├── basin_stability_scores.tsv             # 1 KB
        ├── cycle_identity_map.tsv                 # 1 KB
        └── semantic_model_wikipedia.json          # 43 KB
```

**Pros**: Small, focused, contains all key findings
**Cons**: Cannot reproduce from scratch (no source links)

---

### Option B: Full Reproducibility — 1.8 GB

Includes source link sequences for complete reproducibility.

```
wikipedia-nlink-basins/
├── README.md
└── data/
    ├── source/
    │   ├── nlink_sequences.parquet               # 687 MB ⭐
    │   └── pages.parquet                         # 940 MB ⭐
    └── multiplex/
        └── [same as Option A]
```

**Pros**: Full reproducibility, can compute any N
**Cons**: Large download, redundant if user already has Wikipedia

---

### Option C: Research Complete — 2.0 GB

Includes per-N analysis files for studying individual N values.

```
wikipedia-nlink-basins/
├── README.md
└── data/
    ├── source/
    │   └── [same as Option B]
    ├── multiplex/
    │   └── [same as Option A]
    └── analysis/
        ├── branches_n=3_*.parquet                # Per-cycle basins at N=3
        ├── branches_n=4_*.parquet
        ├── branches_n=5_*.parquet                # Most important
        ├── branches_n=6_*.parquet
        ├── branches_n=7_*.parquet
        ├── branches_n=8_*.parquet
        ├── branches_n=9_*.parquet
        ├── branches_n=10_*.parquet
        └── basin_pointcloud_*.parquet            # 3D geometry data
```

---

## File-by-File Manifest

### Core Files (Must Include)

| File | Size | Rows | Priority | Notes |
|------|------|------|----------|-------|
| `multiplex_basin_assignments.parquet` | 11.7 MB | 2.1M | **Required** | Core finding data |
| `tunnel_nodes.parquet` | 9.7 MB | 2.0M | **Required** | Tunnel node classification |
| `DATASET_CARD.md` → `README.md` | 5 KB | - | **Required** | HF dataset card |

### Recommended Additions

| File | Size | Rows | Priority | Notes |
|------|------|------|----------|-------|
| `multiplex_edges.parquet` | 87 MB | 9.7M | High | Graph structure |
| `tunnel_frequency_ranking.tsv` | 972 KB | 9K | High | Ranked tunnel nodes |
| `semantic_model_wikipedia.json` | 43 KB | - | Medium | Extracted semantic model |
| `basin_flows.tsv` | 1 KB | 16 | Medium | Cross-basin transitions |

### Source Data (For Reproducibility)

| File | Size | Rows | Priority | Notes |
|------|------|------|----------|-------|
| `nlink_sequences.parquet` | 687 MB | 18M | Optional | Enables any-N computation |
| `pages.parquet` | 940 MB | 65M | Optional | Page ID → title mapping |

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

- [ ] All parquet files readable: `python -c "import pandas; pandas.read_parquet('file.parquet')"`
- [ ] Row counts match documentation
- [ ] No PII or sensitive data (Wikipedia is public)
- [ ] Schema matches documentation

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
| Minimal (Option A) | 115 MB | Research on tunneling/basins |
| Full (Option B) | 1.8 GB | Complete reproducibility |
| Research (Option C) | 2.0 GB | Per-N detailed analysis |

**Recommendation**: Start with Option A. Add source data as separate config if requested.

---

**Last Updated**: 2026-01-01
