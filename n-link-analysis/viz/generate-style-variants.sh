#!/bin/bash
# Generate multiple style variants of key basins for presentations/publications
# Run from repository root

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"

cd "$REPO_ROOT"

# Parse arguments
CYCLES="Massachusetts Thermosetting"  # Default: most interesting basins
WIDTH=2400
HEIGHT=1600

while [[ $# -gt 0 ]]; do
    case $1 in
        --cycles)
            CYCLES="$2"
            shift 2
            ;;
        --width)
            WIDTH="$2"
            shift 2
            ;;
        --height)
            HEIGHT="$2"
            shift 2
            ;;
        --help)
            echo "Usage: $0 [--cycles 'Basin1 Basin2'] [--width 2400] [--height 1600]"
            echo ""
            echo "Generates style variants for specified basins:"
            echo "  - Standard (Viridis, 0.85 opacity)"
            echo "  - High contrast (Plasma, 0.95 opacity)"
            echo "  - Warm tones (Inferno, 0.90 opacity)"
            echo "  - Cool tones (Cividis, 0.85 opacity)"
            echo "  - Monochrome (Greys, 0.80 opacity)"
            echo ""
            echo "Examples:"
            echo "  $0  # Default: Massachusetts and Thermosetting"
            echo "  $0 --cycles 'Massachusetts Sea_salt Kingdom'"
            echo "  $0 --cycles Massachusetts --width 3200 --height 2400"
            exit 0
            ;;
        *)
            echo "Unknown option: $1"
            exit 1
            ;;
    esac
done

# Ensure virtual environment is activated
if [[ -z "$VIRTUAL_ENV" ]]; then
    if [[ -f ".venv/bin/activate" ]]; then
        source .venv/bin/activate
    fi
fi

echo "=== Generating Style Variants ==="
echo "Cycles: $CYCLES"
echo "Resolution: ${WIDTH}x${HEIGHT}"
echo ""

# Create variants subdirectory
VARIANTS_DIR="n-link-analysis/report/assets/variants"
mkdir -p "$VARIANTS_DIR"

# Style 1: Standard (Viridis)
echo "[1/5] Generating Standard (Viridis)..."
python n-link-analysis/viz/batch-render-basin-images.py \
    --n 5 \
    --cycles $CYCLES \
    --width $WIDTH \
    --height $HEIGHT \
    --colorscale Viridis \
    --opacity 0.85 \
    --output-dir "$VARIANTS_DIR"

# Rename to include variant suffix
for file in "$VARIANTS_DIR"/basin_3d_n=5_cycle=*.png; do
    if [[ -f "$file" ]] && [[ ! "$file" =~ _standard\.png$ ]]; then
        base="${file%.png}"
        mv "$file" "${base}_standard.png"
    fi
done

echo ""

# Style 2: High Contrast (Plasma)
echo "[2/5] Generating High Contrast (Plasma)..."
python n-link-analysis/viz/batch-render-basin-images.py \
    --n 5 \
    --cycles $CYCLES \
    --width $WIDTH \
    --height $HEIGHT \
    --colorscale Plasma \
    --opacity 0.95 \
    --output-dir "$VARIANTS_DIR"

for file in "$VARIANTS_DIR"/basin_3d_n=5_cycle=*.png; do
    if [[ -f "$file" ]] && [[ ! "$file" =~ _.*\.png$ ]] || [[ "$file" =~ _standard\.png$ ]]; then
        continue
    fi
    base="${file%.png}"
    mv "$file" "${base}_plasma.png" 2>/dev/null || true
done

echo ""

# Style 3: Warm Tones (Inferno)
echo "[3/5] Generating Warm Tones (Inferno)..."
python n-link-analysis/viz/batch-render-basin-images.py \
    --n 5 \
    --cycles $CYCLES \
    --width $WIDTH \
    --height $HEIGHT \
    --colorscale Inferno \
    --opacity 0.90 \
    --output-dir "$VARIANTS_DIR"

for file in "$VARIANTS_DIR"/basin_3d_n=5_cycle=*.png; do
    if [[ -f "$file" ]] && [[ ! "$file" =~ _.*\.png$ ]]; then
        base="${file%.png}"
        mv "$file" "${base}_inferno.png"
    fi
done

echo ""

# Style 4: Cool Tones (Cividis - colorblind safe)
echo "[4/5] Generating Cool Tones (Cividis)..."
python n-link-analysis/viz/batch-render-basin-images.py \
    --n 5 \
    --cycles $CYCLES \
    --width $WIDTH \
    --height $HEIGHT \
    --colorscale Cividis \
    --opacity 0.85 \
    --output-dir "$VARIANTS_DIR"

for file in "$VARIANTS_DIR"/basin_3d_n=5_cycle=*.png; do
    if [[ -f "$file" ]] && [[ ! "$file" =~ _.*\.png$ ]]; then
        base="${file%.png}"
        mv "$file" "${base}_cividis.png"
    fi
done

echo ""

# Style 5: Monochrome (Greys - publication safe)
echo "[5/5] Generating Monochrome (Greys)..."
python n-link-analysis/viz/batch-render-basin-images.py \
    --n 5 \
    --cycles $CYCLES \
    --width $WIDTH \
    --height $HEIGHT \
    --colorscale Greys \
    --opacity 0.80 \
    --output-dir "$VARIANTS_DIR"

for file in "$VARIANTS_DIR"/basin_3d_n=5_cycle=*.png; do
    if [[ -f "$file" ]] && [[ ! "$file" =~ _.*\.png$ ]]; then
        base="${file%.png}"
        mv "$file" "${base}_monochrome.png"
    fi
done

echo ""
echo "=== Generation Complete ==="
echo ""
echo "Output directory: $VARIANTS_DIR/"
echo ""
echo "Generated variants:"
ls -1 "$VARIANTS_DIR"/*.png 2>/dev/null | wc -l | xargs echo "  Total files:"
echo ""
echo "Variants per basin:"
echo "  - *_standard.png     (Viridis, 0.85 opacity)"
echo "  - *_plasma.png       (Plasma, 0.95 opacity - high contrast)"
echo "  - *_inferno.png      (Inferno, 0.90 opacity - warm tones)"
echo "  - *_cividis.png      (Cividis, 0.85 opacity - colorblind safe)"
echo "  - *_monochrome.png   (Greys, 0.80 opacity - B&W publications)"
echo ""

# Summary table
echo "File sizes:"
du -sh "$VARIANTS_DIR" | awk '{print "  Total: " $1}'
echo ""

echo "✓ Style variants ready"
