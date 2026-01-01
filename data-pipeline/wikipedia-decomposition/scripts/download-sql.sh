#!/usr/bin/env bash
# Wikipedia SQL Dumps Download Script (Linux/macOS)
# Downloads SQL dumps needed for Wikipedia link graph extraction

set -uo pipefail

# Configuration
BASE_URL="https://dumps.wikimedia.org/enwiki/20251220/"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
DEST_DIR="$(cd "$SCRIPT_DIR/../../../data/wikipedia/raw" && pwd)"
MAX_RETRIES=3
RETRY_DELAY=5

# SQL files needed for the pipeline
FILES=(
    "enwiki-20251220-page.sql.gz"
    "enwiki-20251220-redirect.sql.gz"
    "enwiki-20251220-page_props.sql.gz"
)

# File size estimates (for reference)
declare -A SIZES=(
    ["enwiki-20251220-page.sql.gz"]="~2.5GB"
    ["enwiki-20251220-redirect.sql.gz"]="~150MB"
    ["enwiki-20251220-page_props.sql.gz"]="~250MB"
)

# Color output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# Check for required tools
if ! command -v wget &> /dev/null && ! command -v curl &> /dev/null; then
    echo -e "${RED}Error: Neither wget nor curl found. Please install one.${NC}"
    exit 1
fi

# Prefer wget if available
if command -v wget &> /dev/null; then
    DOWNLOADER="wget"
else
    DOWNLOADER="curl"
fi

# Create destination directory if it doesn't exist
mkdir -p "$DEST_DIR"

# Filter to files that don't exist yet
TO_DOWNLOAD=()
for file in "${FILES[@]}"; do
    if [[ ! -f "$DEST_DIR/$file" ]]; then
        TO_DOWNLOAD+=("$file")
    fi
done

if [[ ${#TO_DOWNLOAD[@]} -eq 0 ]]; then
    echo -e "${GREEN}All SQL files already downloaded!${NC}"
    exit 0
fi

echo -e "${CYAN}Wikipedia SQL Dumps Download${NC}"
echo -e "${CYAN}============================${NC}"
echo -e "${CYAN}Destination: $DEST_DIR${NC}"
echo -e "${CYAN}Using: $DOWNLOADER${NC}"
echo -e "${CYAN}Files to download: ${#TO_DOWNLOAD[@]}/${#FILES[@]}${NC}"
echo ""

for file in "${TO_DOWNLOAD[@]}"; do
    echo -e "${YELLOW}Downloading: $file (estimated size: ${SIZES[$file]})${NC}"
done
echo ""

COMPLETED=0
FAILED=0
START_TIME=$(date +%s)

# Download files sequentially (they're large, no parallelism needed)
for file in "${TO_DOWNLOAD[@]}"; do
    url="$BASE_URL$file"
    dest="$DEST_DIR/$file.tmp"

    echo -e "${YELLOW}Starting download: $file${NC}"

    retry=0
    success=false

    while [[ $retry -lt $MAX_RETRIES ]] && [[ "$success" == "false" ]]; do
        if [[ $retry -gt 0 ]]; then
            sleep $((RETRY_DELAY * retry))  # Exponential backoff
            echo -e "${YELLOW}  Retry $retry/$MAX_RETRIES for $file...${NC}"
        fi

        if [[ "$DOWNLOADER" == "wget" ]]; then
            # Use wget with progress bar and resume support
            wget --continue --show-progress --progress=bar:force -O "$dest" "$url"
        else
            # Use curl with progress bar and resume support
            curl -fL -C - --progress-bar -o "$dest" "$url"
        fi
        exit_code=$?

        # Check if download succeeded and file is not empty
        if [[ $exit_code -eq 0 ]] && [[ -s "$dest" ]]; then
            success=true
            mv "$dest" "${dest%.tmp}"
            ((COMPLETED++))
            echo -e "${GREEN}  ✓ Done: $file${NC}"
            echo ""
        else
            rm -f "$dest"
            ((retry++))
            if [[ $retry -lt $MAX_RETRIES ]]; then
                echo -e "${RED}  Failed, retrying...${NC}"
            fi
        fi
    done

    if [[ "$success" == "false" ]]; then
        ((FAILED++))
        echo -e "${RED}  ✗ FAIL: $file (max retries exceeded)${NC}"
        echo ""
    fi
done

# Final summary
END_TIME=$(date +%s)
ELAPSED=$((END_TIME - START_TIME))
HOURS=$((ELAPSED / 3600))
MINUTES=$(( (ELAPSED % 3600) / 60 ))
SECONDS=$((ELAPSED % 60))

echo "====================================="
printf "COMPLETE in %02d:%02d:%02d\n" $HOURS $MINUTES $SECONDS
echo "  Success: $COMPLETED"
echo "  Failed: $FAILED"
echo "====================================="

if [[ $FAILED -gt 0 ]]; then
    echo -e "${RED}Some downloads failed. Re-run script to retry.${NC}"
    exit 1
fi

echo -e "${GREEN}All SQL dumps downloaded successfully!${NC}"
echo ""
echo -e "${CYAN}Next steps:${NC}"
echo "  1. Run: cd ../scripts"
echo "  2. Run: python parse-sql-to-parquet.py"
echo "  3. Run: python parse-xml-prose-links.py"
echo "  4. Run: python build-nlink-sequences-v3.py"
