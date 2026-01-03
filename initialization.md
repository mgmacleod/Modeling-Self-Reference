# Project Initialization (One-Time Setup)

**Document Type**: Bootstrap instructions  
**Target Audience**: LLMs (executing setup)  
**Purpose**: Get project environment running from fresh clone  
**Usage**: Run once after cloning repository, never again  
**Last Updated**: 2026-01-02

---

## Prerequisites Check

Before running these commands, verify:
- Python 3.8+ installed and in PATH
- Git installed (you cloned the repo, so ✓)
- VS Code installed (recommended, not required)

---

## Setup Procedure

### Step 1: Create Virtual Environment

```powershell
# Windows
python -m venv .venv
```

```bash
# macOS/Linux
python3 -m venv .venv
```

**Expected result**: `.venv/` directory created in project root

---

### Step 2: Activate Virtual Environment

```powershell
# Windows
.venv\Scripts\Activate.ps1
```

```bash
# macOS/Linux
source .venv/bin/activate
```

**Expected result**: Prompt shows `(.venv)` prefix

**Note**: If Windows PowerShell execution policy blocks activation:
```powershell
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```

---

### Step 3: Upgrade pip

```powershell
python -m pip install --upgrade pip
```

**Expected result**: Latest pip version installed

---

### Step 4: Install Dependencies

```powershell
pip install -r requirements.txt
```

**Expected result**: All packages from requirements.txt installed

**Current dependencies** (as of 2025-12-15):
**Current dependencies**: See `requirements.txt` (source of truth).

Key packages used by the empirical Wikipedia N-link analysis include:
- duckdb
- pyarrow
- numpy
- pandas

---

### Step 5: Verify Installation

```powershell
# Check Python environment
python --version

# Check installed packages
pip list
```

**Expected result**: 
- Python 3.8+
- All dependencies listed

---

### Step 6: Open in VS Code (Optional)

```powershell
code self-reference-modeling.code-workspace
```

**Expected result**: 
- Workspace opens with correct settings
- Python interpreter auto-detected at `.venv/Scripts/python.exe` (Windows) or `.venv/bin/python` (macOS/Linux)
- System prompts loaded from `.vscode/settings.json`

---

## Step 7: Download Data from HuggingFace

The analysis data is hosted on HuggingFace and cached locally. Run the data loader to download:

```bash
# Download the dataset (~3.2 GB)
python n-link-analysis/scripts/data_loader.py --data-source huggingface --validate
```

**Expected result**:
- Download completes to `~/.cache/wikipedia-nlink-basins/mgmacleod_wikidata1/`
- Validation passes: "All checks passed!"

**Files downloaded**:
- `data/source/nlink_sequences.parquet` - Wikipedia N-link sequences
- `data/source/pages.parquet` - Page ID to title mapping
- `data/multiplex/` - Pre-computed cross-N analysis results
- `data/analysis/` - Basin pointcloud data for visualizations

---

## Step 8: Create Data Symlinks

Create symlinks from the local data directory to the HuggingFace cache:

```bash
# Create symlinks for data access
cd data/wikipedia/processed/
ln -sf ~/.cache/wikipedia-nlink-basins/mgmacleod_wikidata1/data/source/nlink_sequences.parquet .
ln -sf ~/.cache/wikipedia-nlink-basins/mgmacleod_wikidata1/data/source/pages.parquet .
ln -sf ~/.cache/wikipedia-nlink-basins/mgmacleod_wikidata1/data/multiplex .
ln -sf ~/.cache/wikipedia-nlink-basins/mgmacleod_wikidata1/data/analysis .
cd ../../..
```

**Expected result**:
- Symlinks created in `data/wikipedia/processed/`
- `ls -la data/wikipedia/processed/` shows symlinks pointing to cache

**Verify**:
```bash
python n-link-analysis/scripts/data_loader.py --validate
```

---

## Step 9: Generate Basin Visualizations

Generate the 3D basin visualization PNG images for the gallery:

```bash
# Generate all N=5 basin images (~30 seconds)
python n-link-analysis/viz/batch-render-basin-images.py --n 5 --all-cycles
```

**Expected result**:
- 9 PNG files created in `n-link-analysis/report/assets/`
- Console shows "Successfully rendered 9/9 basins"

**Note**: Kaleido 0.2.1 deprecation warnings are expected but harmless.

---

## Step 10: Regenerate Gallery

Update the HTML gallery to include the newly generated basin images:

```bash
python n-link-analysis/viz/create-visualization-gallery.py
```

**Expected result**:
- `n-link-analysis/report/assets/gallery.html` regenerated
- Console shows path to open in browser

**View the gallery**:
```bash
# Open in browser (Linux)
xdg-open n-link-analysis/report/assets/gallery.html

# Or manually navigate to:
# file:///path/to/repo/n-link-analysis/report/assets/gallery.html
```

---

## Validation Checklist

After setup, verify:

- [ ] Virtual environment created (`.venv/` directory exists)
- [ ] Virtual environment activated (prompt shows `(.venv)`)
- [ ] Dependencies installed (`pip list` shows pandas, plotly, kaleido, huggingface_hub)
- [ ] VS Code workspace opens (if using VS Code)
- [ ] Python interpreter configured (check VS Code status bar)
- [ ] HuggingFace data downloaded (~3.2 GB in `~/.cache/wikipedia-nlink-basins/`)
- [ ] Data symlinks created (`data/wikipedia/processed/` has symlinks)
- [ ] Basin images generated (9 PNGs in `n-link-analysis/report/assets/`)
- [ ] Gallery accessible (open gallery.html in browser)

---

## Next Steps

**For LLMs**: After completing initialization, read bootstrap documentation:
1. [llm-facing-documentation/README.md](llm-facing-documentation/README.md) - Project overview and navigation
2. [llm-facing-documentation/project-timeline.md](llm-facing-documentation/project-timeline.md) - Recent 3-5 entries
3. Ask user what to work on

**For humans**: See [human-facing-documentation/project-setup.md](human-facing-documentation/project-setup.md) for complete setup guide with context.

---

## Troubleshooting

**Issue**: `python` not found
- **Solution**: Try `python3` or verify Python installation in PATH

**Issue**: Virtual environment won't activate (Windows)
- **Solution**: Run PowerShell as Administrator, set execution policy (see Step 2)

**Issue**: pip install fails with permission error
- **Solution**: Ensure virtual environment is activated (`.venv` prefix in prompt)

**Issue**: VS Code doesn't detect Python interpreter
- **Solution**: Open command palette (Ctrl+Shift+P), search "Python: Select Interpreter", choose `.venv/Scripts/python.exe`

---

## Platform-Specific Notes

**Windows**:
- Virtual environment: `.venv\Scripts\`
- Python executable: `.venv\Scripts\python.exe`
- Activation: `.venv\Scripts\Activate.ps1`

**macOS/Linux**:
- Virtual environment: `.venv/bin/`
- Python executable: `.venv/bin/python`
- Activation: `source .venv/bin/activate`

---

**After initialization, this document is not needed for regular work.**
