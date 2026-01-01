#!/usr/bin/env bash
# Decompress Wikipedia dumps (.gz and .bz2 files)

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Color output
CYAN='\033[0;36m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

# Check Python
PYTHON_CMD="python"
if ! command -v python &> /dev/null; then
    PYTHON_CMD="python3"
fi

echo -e "${CYAN}Wikipedia Dump Decompression${NC}"
echo -e "${CYAN}===========================${NC}"
echo ""
echo -e "${YELLOW}This will decompress ~70 files to ~100GB${NC}"
echo -e "${YELLOW}Estimated time: 15-30 minutes (4 parallel workers)${NC}"
echo ""

cd "$SCRIPT_DIR"
$PYTHON_CMD decompress-all.py

echo ""
echo -e "${GREEN}Decompression complete!${NC}"
