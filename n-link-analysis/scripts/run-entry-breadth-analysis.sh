#!/bin/bash
# Run entry breadth analysis on cross-N data (N=3,4,5,6,7)
#
# This script tests the entry breadth hypothesis:
#   Entry_Breadth(N=5) / Entry_Breadth(N=4) ≈ 8-10×
#
# Usage:
#   bash run-entry-breadth-analysis.sh [TAG]

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
ANALYSIS_SCRIPT="$SCRIPT_DIR/analyze-basin-entry-breadth.py"
CYCLES_FILE="$REPO_ROOT/n-link-analysis/test-cycles.tsv"

TAG="${1:-cross_n_2025_12_31}"

echo "================================================================"
echo "Entry Breadth Analysis - Cross-N Study"
echo "================================================================"
echo "Cycles file: $CYCLES_FILE"
echo "Tag: $TAG"
echo "N range: 3-7"
echo ""

# Check prerequisites
if [ ! -f "$ANALYSIS_SCRIPT" ]; then
    echo "ERROR: Analysis script not found: $ANALYSIS_SCRIPT"
    exit 1
fi

if [ ! -f "$CYCLES_FILE" ]; then
    echo "ERROR: Cycles file not found: $CYCLES_FILE"
    exit 1
fi

# Activate virtual environment if it exists
if [ -f "$REPO_ROOT/.venv/bin/activate" ]; then
    echo "Activating virtual environment..."
    source "$REPO_ROOT/.venv/bin/activate"
fi

# Run analysis
echo "Running entry breadth analysis..."
echo ""

python3 "$ANALYSIS_SCRIPT" \
    --n-range 3 7 \
    --cycles-file "$CYCLES_FILE" \
    --tag "$TAG" \
    --namespace 0

echo ""
echo "================================================================"
echo "Analysis complete!"
echo "================================================================"
echo ""
echo "Output files (in data/wikipedia/processed/analysis/):"
echo "  - entry_breadth_n={3,4,5,6,7}_${TAG}.tsv"
echo "  - entry_breadth_summary_${TAG}.tsv"
echo "  - entry_breadth_correlation_${TAG}.tsv"
echo ""
