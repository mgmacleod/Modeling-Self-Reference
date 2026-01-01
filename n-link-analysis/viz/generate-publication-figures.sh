#!/bin/bash
# Quick generation of publication-quality basin visualization figures
# Run from repository root

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"

cd "$REPO_ROOT"

echo "=== Generating Publication Figures for N=5 Basins ==="
echo ""

# Ensure virtual environment is activated
if [[ -z "$VIRTUAL_ENV" ]]; then
    if [[ -f ".venv/bin/activate" ]]; then
        echo "Activating virtual environment..."
        source .venv/bin/activate
    fi
fi

# Check dependencies
if ! python -c "import kaleido" 2>/dev/null; then
    echo "Error: kaleido not installed"
    echo "Install with: pip install kaleido"
    exit 1
fi

# Set 1: Individual high-resolution basins (1920x1200, presentation size)
echo "[1/5] Rendering individual basins (1920x1200, Viridis)..."
python n-link-analysis/viz/batch-render-basin-images.py \
    --n 5 \
    --all-cycles \
    --width 1920 \
    --height 1200 \
    --colorscale Viridis \
    --opacity 0.85 \
    --max-plot-points 120000

echo ""

# Set 2: Comparison grid (3600x2400, standard)
echo "[2/5] Rendering comparison grid (3600x2400)..."
python n-link-analysis/viz/batch-render-basin-images.py \
    --n 5 \
    --comparison-grid \
    --width 3600 \
    --height 2400

echo ""

# Set 3: Key basins with alternative colorscale (publication variants)
echo "[3/5] Rendering key basins with Plasma colorscale..."
python n-link-analysis/viz/batch-render-basin-images.py \
    --n 5 \
    --cycles Massachusetts Thermosetting Sea_salt \
    --width 2400 \
    --height 1600 \
    --colorscale Plasma \
    --opacity 0.9 \
    --max-plot-points 150000

echo ""

# Set 4: Ultra high-res Massachusetts (flagship visualization)
echo "[4/5] Rendering ultra high-res Massachusetts basin (3200x2400)..."
python n-link-analysis/viz/batch-render-basin-images.py \
    --n 5 \
    --cycles Massachusetts \
    --width 3200 \
    --height 2400 \
    --colorscale Viridis \
    --opacity 0.85 \
    --max-plot-points 200000

echo ""

# Set 5: Thermosetting polymer (deepest basin, special interest)
echo "[5/5] Rendering ultra high-res Thermosetting polymer basin (3200x2400)..."
python n-link-analysis/viz/batch-render-basin-images.py \
    --n 5 \
    --cycles Thermosetting \
    --width 3200 \
    --height 2400 \
    --colorscale Inferno \
    --opacity 0.9 \
    --max-plot-points 100000

echo ""
echo "=== Generation Complete ==="
echo ""
echo "Output directory: n-link-analysis/report/assets/"
echo ""
echo "Generated files:"
ls -lh n-link-analysis/report/assets/basin_3d_n=5_*.png 2>/dev/null | wc -l | xargs echo "  - Individual basins:"
ls -lh n-link-analysis/report/assets/basin_comparison_grid_n=5.png 2>/dev/null | wc -l | xargs echo "  - Comparison grids:"
echo ""
echo "Total size:"
du -sh n-link-analysis/report/assets/ | awk '{print "  " $1}'
echo ""
echo "✓ All figures ready for publication"
