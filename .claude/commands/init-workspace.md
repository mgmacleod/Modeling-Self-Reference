---
description: Initialize project environment from fresh clone (one-time setup)
allowed-tools: Bash(*), Read
---

# Project Initialization

Execute the one-time setup procedure for this project from a fresh clone.

## Setup Instructions

Follow the procedure documented in @initialization.md

## Current Environment

Platform: !`uname -s 2>/dev/null || echo "Windows"`
Python version: !`python --version 2>/dev/null || python3 --version 2>/dev/null || echo "Python not found"`
Virtual environment status: !`[ -d .venv ] && echo "Virtual environment exists" || echo "Virtual environment not found"`

## Setup Steps

1. **Create Virtual Environment**
   - Linux/macOS: `python3 -m venv .venv`
   - Windows: `python -m venv .venv`

2. **Activate Virtual Environment**
   - Linux/macOS: `source .venv/bin/activate`
   - Windows: `.venv\Scripts\Activate.ps1`

3. **Upgrade pip**
   - `python -m pip install --upgrade pip`

4. **Install Dependencies**
   - `pip install -r requirements.txt`

5. **Verify Installation**
   - `python --version` (should be 3.8+)
   - `pip list` (should show: pandas, plotly, kaleido, huggingface_hub)

6. **Open VS Code Workspace (Optional)**
   - `code self-reference-modeling.code-workspace`

7. **Download Data from HuggingFace**
   - `python n-link-analysis/scripts/data_loader.py --data-source huggingface --validate`
   - Downloads ~3.2 GB to `~/.cache/wikipedia-nlink-basins/`

8. **Create Data Symlinks**
   - `cd data/wikipedia/processed/`
   - `ln -sf ~/.cache/wikipedia-nlink-basins/mgmacleod_wikidata1/data/source/nlink_sequences.parquet .`
   - `ln -sf ~/.cache/wikipedia-nlink-basins/mgmacleod_wikidata1/data/source/pages.parquet .`
   - `ln -sf ~/.cache/wikipedia-nlink-basins/mgmacleod_wikidata1/data/multiplex .`
   - `ln -sf ~/.cache/wikipedia-nlink-basins/mgmacleod_wikidata1/data/analysis .`
   - `cd ../../..`

9. **Generate Basin Visualizations**
   - `python n-link-analysis/viz/batch-render-basin-images.py --n 5 --all-cycles`

10. **Regenerate Gallery**
    - `python n-link-analysis/viz/create-visualization-gallery.py`

## After Setup

Once initialization is complete, bootstrap your LLM session:
1. Read [llm-facing-documentation/README.md](llm-facing-documentation/README.md)
2. Read latest 3-5 entries of [llm-facing-documentation/project-timeline.md](llm-facing-documentation/project-timeline.md)
3. Ask user what to work on

---

Please execute the initialization procedure now, adapting commands for the detected platform.
