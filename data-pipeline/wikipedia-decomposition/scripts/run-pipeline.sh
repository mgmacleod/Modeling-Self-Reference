#!/usr/bin/env bash
# Wikipedia Data Pipeline Runner
# Runs the complete extraction pipeline from downloaded dumps to N-Link sequences

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
DATA_DIR="$(cd "$SCRIPT_DIR/../../../data/wikipedia" && pwd)"
RAW_DIR="$DATA_DIR/raw"
PROCESSED_DIR="$DATA_DIR/processed"

# Color output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
BOLD='\033[1m'
NC='\033[0m' # No Color

# Configuration
SKIP_SQL="${SKIP_SQL:-false}"
SKIP_XML="${SKIP_XML:-false}"
SKIP_NLINK="${SKIP_NLINK:-false}"

echo -e "${CYAN}${BOLD}Wikipedia Data Extraction Pipeline${NC}"
echo -e "${CYAN}===================================${NC}"
echo ""

# Check Python environment
if ! command -v python &> /dev/null && ! command -v python3 &> /dev/null; then
    echo -e "${RED}Error: Python not found. Please install Python 3.8+${NC}"
    exit 1
fi

PYTHON_CMD="python"
if ! command -v python &> /dev/null; then
    PYTHON_CMD="python3"
fi

echo -e "${CYAN}Using Python: $($PYTHON_CMD --version)${NC}"
echo -e "${CYAN}Data directory: $DATA_DIR${NC}"
echo ""

# Check for required files
echo -e "${YELLOW}Checking prerequisites...${NC}"

# Count compressed SQL files
SQL_GZ_COUNT=$(find "$RAW_DIR" -name "*.sql.gz" 2>/dev/null | wc -l)
# Count decompressed SQL files
SQL_COUNT=$(find "$RAW_DIR" -name "*.sql" -not -name "*.sql.gz" 2>/dev/null | wc -l)

# Count compressed XML files
XML_BZ2_COUNT=$(find "$RAW_DIR" -name "enwiki-*-pages-articles-multistream*.xml*.bz2" 2>/dev/null | wc -l)
# Count decompressed XML files
XML_COUNT=$(find "$RAW_DIR" -name "enwiki-*-pages-articles-multistream*.xml" -not -name "*.bz2" 2>/dev/null | wc -l)

echo -e "  Compressed SQL: $SQL_GZ_COUNT/3 files"
echo -e "  Decompressed SQL: $SQL_COUNT/3 files"
echo -e "  Compressed XML: $XML_BZ2_COUNT/70 files"
echo -e "  Decompressed XML: $XML_COUNT/70 files"
echo ""

# Check if we need to download
if [[ $SQL_GZ_COUNT -lt 3 ]]; then
    echo -e "${RED}Missing SQL dumps! Run: ./download-sql.sh${NC}"
    exit 1
fi

if [[ $XML_BZ2_COUNT -lt 69 ]]; then
    echo -e "${RED}Missing XML dumps! Run: ./download-multistream.sh${NC}"
    exit 1
fi

# Check if we need to decompress
NEED_DECOMPRESS=false
if [[ $SQL_COUNT -lt 3 ]] || [[ $XML_COUNT -lt 70 ]]; then
    NEED_DECOMPRESS=true
    echo -e "${YELLOW}Compressed files need decompression${NC}"
    echo -e "${YELLOW}Run: ./decompress-all.sh (takes ~15-30 minutes)${NC}"
    echo ""
    read -p "Decompress now? (Y/n) " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Nn]$ ]]; then
        echo -e "${RED}Aborted. Decompress files first.${NC}"
        exit 1
    fi

    # Run decompression
    "$SCRIPT_DIR/decompress-all.sh"
    if [[ $? -ne 0 ]]; then
        echo -e "${RED}Decompression failed!${NC}"
        exit 1
    fi
fi

echo -e "${GREEN}✓ Prerequisites OK${NC}"
echo ""

# Create processed directory
mkdir -p "$PROCESSED_DIR"

# Step 1: Parse SQL dumps to Parquet
if [[ "$SKIP_SQL" != "true" ]]; then
    if [[ -f "$PROCESSED_DIR/pages.parquet" ]] && \
       [[ -f "$PROCESSED_DIR/redirects.parquet" ]] && \
       [[ -f "$PROCESSED_DIR/disambig_pages.parquet" ]]; then
        echo -e "${GREEN}✓ SQL parsing already complete (output files exist)${NC}"
    else
        echo -e "${CYAN}${BOLD}Step 1: Parsing SQL dumps → Parquet${NC}"
        echo -e "${CYAN}======================================${NC}"
        cd "$SCRIPT_DIR"
        $PYTHON_CMD parse-sql-to-parquet.py
        if [[ $? -ne 0 ]]; then
            echo -e "${RED}SQL parsing failed!${NC}"
            exit 1
        fi
        echo -e "${GREEN}✓ SQL parsing complete${NC}"
        echo ""
    fi
else
    echo -e "${YELLOW}Skipping SQL parsing (SKIP_SQL=true)${NC}"
fi

# Step 2: Extract prose links from XML
if [[ "$SKIP_XML" != "true" ]]; then
    if [[ -f "$PROCESSED_DIR/links_prose.parquet" ]]; then
        echo -e "${GREEN}✓ XML link extraction already complete (output file exists)${NC}"
    else
        echo -e "${CYAN}${BOLD}Step 2: Extracting prose links from XML${NC}"
        echo -e "${CYAN}========================================${NC}"
        echo -e "${YELLOW}This step takes ~53 minutes for 69 XML files${NC}"
        cd "$SCRIPT_DIR"
        $PYTHON_CMD parse-xml-prose-links.py
        if [[ $? -ne 0 ]]; then
            echo -e "${RED}XML parsing failed!${NC}"
            exit 1
        fi
        echo -e "${GREEN}✓ XML link extraction complete${NC}"
        echo ""
    fi
else
    echo -e "${YELLOW}Skipping XML parsing (SKIP_XML=true)${NC}"
fi

# Step 3: Build N-Link sequences
if [[ "$SKIP_NLINK" != "true" ]]; then
    if [[ -f "$PROCESSED_DIR/nlink_sequences.parquet" ]]; then
        echo -e "${GREEN}✓ N-Link sequences already built (output file exists)${NC}"
    else
        echo -e "${CYAN}${BOLD}Step 3: Building N-Link sequences${NC}"
        echo -e "${CYAN}==================================${NC}"
        echo -e "${YELLOW}This step takes ~5 minutes${NC}"
        cd "$SCRIPT_DIR"
        $PYTHON_CMD build-nlink-sequences-v3.py
        if [[ $? -ne 0 ]]; then
            echo -e "${RED}N-Link sequence building failed!${NC}"
            exit 1
        fi
        echo -e "${GREEN}✓ N-Link sequences complete${NC}"
        echo ""
    fi
else
    echo -e "${YELLOW}Skipping N-Link building (SKIP_NLINK=true)${NC}"
fi

# Final verification
echo -e "${CYAN}${BOLD}Pipeline Summary${NC}"
echo -e "${CYAN}================${NC}"

if [[ -f "$PROCESSED_DIR/pages.parquet" ]]; then
    PAGES_SIZE=$(du -h "$PROCESSED_DIR/pages.parquet" | cut -f1)
    echo -e "${GREEN}✓${NC} pages.parquet ($PAGES_SIZE)"
else
    echo -e "${RED}✗${NC} pages.parquet (missing)"
fi

if [[ -f "$PROCESSED_DIR/redirects.parquet" ]]; then
    REDIRECTS_SIZE=$(du -h "$PROCESSED_DIR/redirects.parquet" | cut -f1)
    echo -e "${GREEN}✓${NC} redirects.parquet ($REDIRECTS_SIZE)"
else
    echo -e "${RED}✗${NC} redirects.parquet (missing)"
fi

if [[ -f "$PROCESSED_DIR/disambig_pages.parquet" ]]; then
    DISAMBIG_SIZE=$(du -h "$PROCESSED_DIR/disambig_pages.parquet" | cut -f1)
    echo -e "${GREEN}✓${NC} disambig_pages.parquet ($DISAMBIG_SIZE)"
else
    echo -e "${RED}✗${NC} disambig_pages.parquet (missing)"
fi

if [[ -f "$PROCESSED_DIR/links_prose.parquet" ]]; then
    LINKS_SIZE=$(du -h "$PROCESSED_DIR/links_prose.parquet" | cut -f1)
    echo -e "${GREEN}✓${NC} links_prose.parquet ($LINKS_SIZE)"
else
    echo -e "${RED}✗${NC} links_prose.parquet (missing)"
fi

if [[ -f "$PROCESSED_DIR/nlink_sequences.parquet" ]]; then
    NLINK_SIZE=$(du -h "$PROCESSED_DIR/nlink_sequences.parquet" | cut -f1)
    echo -e "${GREEN}✓${NC} nlink_sequences.parquet ($NLINK_SIZE) ${BOLD}← FINAL OUTPUT${NC}"
else
    echo -e "${RED}✗${NC} nlink_sequences.parquet (missing)"
fi

echo ""
TOTAL_SIZE=$(du -sh "$PROCESSED_DIR" | cut -f1)
echo -e "${CYAN}Total processed data: $TOTAL_SIZE${NC}"
echo ""

# Check if final output exists
if [[ -f "$PROCESSED_DIR/nlink_sequences.parquet" ]]; then
    echo -e "${GREEN}${BOLD}✓ PIPELINE COMPLETE!${NC}"
    echo ""
    echo -e "${CYAN}Next steps:${NC}"
    echo "  1. Verify data with: python quick-stats.py"
    echo "  2. Run N-Link analysis (see n-link-analysis/ directory)"
    echo ""
else
    echo -e "${RED}Pipeline incomplete - missing final output file${NC}"
    exit 1
fi
