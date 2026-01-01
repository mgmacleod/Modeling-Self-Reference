#!/usr/bin/env bash
# Wikipedia Multistream Download Script (Linux/macOS)
# Downloads all multistream XML files with parallel downloads using wget

set -uo pipefail  # Removed -e to allow wait to handle failed downloads

# Configuration
MAX_PARALLEL="${1:-4}"  # Reduced default to 4 to avoid rate limiting
MAX_RETRIES=3
RETRY_DELAY=5
BASE_URL="https://dumps.wikimedia.org/enwiki/20251220/"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
DEST_DIR="$(cd "$SCRIPT_DIR/../../../data/wikipedia/raw" && pwd)"

# All 69 multistream files + index
FILES=(
    "enwiki-20251220-pages-articles-multistream1.xml-p1p41242.bz2"
    "enwiki-20251220-pages-articles-multistream2.xml-p41243p151573.bz2"
    "enwiki-20251220-pages-articles-multistream3.xml-p151574p311329.bz2"
    "enwiki-20251220-pages-articles-multistream4.xml-p311330p558391.bz2"
    "enwiki-20251220-pages-articles-multistream5.xml-p558392p958045.bz2"
    "enwiki-20251220-pages-articles-multistream6.xml-p958046p1483661.bz2"
    "enwiki-20251220-pages-articles-multistream7.xml-p1483662p2134111.bz2"
    "enwiki-20251220-pages-articles-multistream8.xml-p2134112p2936260.bz2"
    "enwiki-20251220-pages-articles-multistream9.xml-p2936261p4045402.bz2"
    "enwiki-20251220-pages-articles-multistream10.xml-p4045403p5399366.bz2"
    "enwiki-20251220-pages-articles-multistream11.xml-p5399367p6899366.bz2"
    "enwiki-20251220-pages-articles-multistream11.xml-p6899367p7054859.bz2"
    "enwiki-20251220-pages-articles-multistream12.xml-p7054860p8554859.bz2"
    "enwiki-20251220-pages-articles-multistream12.xml-p8554860p9172788.bz2"
    "enwiki-20251220-pages-articles-multistream13.xml-p9172789p10672788.bz2"
    "enwiki-20251220-pages-articles-multistream13.xml-p10672789p11659682.bz2"
    "enwiki-20251220-pages-articles-multistream14.xml-p11659683p13159682.bz2"
    "enwiki-20251220-pages-articles-multistream14.xml-p13159683p14324602.bz2"
    "enwiki-20251220-pages-articles-multistream15.xml-p14324603p15824602.bz2"
    "enwiki-20251220-pages-articles-multistream15.xml-p15824603p17324602.bz2"
    "enwiki-20251220-pages-articles-multistream15.xml-p17324603p17460152.bz2"
    "enwiki-20251220-pages-articles-multistream16.xml-p17460153p18960152.bz2"
    "enwiki-20251220-pages-articles-multistream16.xml-p18960153p20460152.bz2"
    "enwiki-20251220-pages-articles-multistream16.xml-p20460153p20570392.bz2"
    "enwiki-20251220-pages-articles-multistream17.xml-p20570393p22070392.bz2"
    "enwiki-20251220-pages-articles-multistream17.xml-p22070393p23570392.bz2"
    "enwiki-20251220-pages-articles-multistream17.xml-p23570393p23716197.bz2"
    "enwiki-20251220-pages-articles-multistream18.xml-p23716198p25216197.bz2"
    "enwiki-20251220-pages-articles-multistream18.xml-p25216198p26716197.bz2"
    "enwiki-20251220-pages-articles-multistream18.xml-p26716198p27121850.bz2"
    "enwiki-20251220-pages-articles-multistream19.xml-p27121851p28621850.bz2"
    "enwiki-20251220-pages-articles-multistream19.xml-p28621851p30121850.bz2"
    "enwiki-20251220-pages-articles-multistream19.xml-p30121851p31308442.bz2"
    "enwiki-20251220-pages-articles-multistream20.xml-p31308443p32808442.bz2"
    "enwiki-20251220-pages-articles-multistream20.xml-p32808443p34308442.bz2"
    "enwiki-20251220-pages-articles-multistream20.xml-p34308443p35522432.bz2"
    "enwiki-20251220-pages-articles-multistream21.xml-p35522433p37022432.bz2"
    "enwiki-20251220-pages-articles-multistream21.xml-p37022433p38522432.bz2"
    "enwiki-20251220-pages-articles-multistream21.xml-p38522433p39996245.bz2"
    "enwiki-20251220-pages-articles-multistream22.xml-p39996246p41496245.bz2"
    "enwiki-20251220-pages-articles-multistream22.xml-p41496246p42996245.bz2"
    "enwiki-20251220-pages-articles-multistream22.xml-p42996246p44496245.bz2"
    "enwiki-20251220-pages-articles-multistream22.xml-p44496246p44788941.bz2"
    "enwiki-20251220-pages-articles-multistream23.xml-p44788942p46288941.bz2"
    "enwiki-20251220-pages-articles-multistream23.xml-p46288942p47788941.bz2"
    "enwiki-20251220-pages-articles-multistream23.xml-p47788942p49288941.bz2"
    "enwiki-20251220-pages-articles-multistream23.xml-p49288942p50564553.bz2"
    "enwiki-20251220-pages-articles-multistream24.xml-p50564554p52064553.bz2"
    "enwiki-20251220-pages-articles-multistream24.xml-p52064554p53564553.bz2"
    "enwiki-20251220-pages-articles-multistream24.xml-p53564554p55064553.bz2"
    "enwiki-20251220-pages-articles-multistream24.xml-p55064554p56564553.bz2"
    "enwiki-20251220-pages-articles-multistream24.xml-p56564554p57025655.bz2"
    "enwiki-20251220-pages-articles-multistream25.xml-p57025656p58525655.bz2"
    "enwiki-20251220-pages-articles-multistream25.xml-p58525656p60025655.bz2"
    "enwiki-20251220-pages-articles-multistream25.xml-p60025656p61525655.bz2"
    "enwiki-20251220-pages-articles-multistream25.xml-p61525656p62585850.bz2"
    "enwiki-20251220-pages-articles-multistream26.xml-p62585851p63975909.bz2"
    "enwiki-20251220-pages-articles-multistream27.xml-p63975910p65475909.bz2"
    "enwiki-20251220-pages-articles-multistream27.xml-p65475910p66975909.bz2"
    "enwiki-20251220-pages-articles-multistream27.xml-p66975910p68475909.bz2"
    "enwiki-20251220-pages-articles-multistream27.xml-p68475910p69975909.bz2"
    "enwiki-20251220-pages-articles-multistream27.xml-p69975910p71475909.bz2"
    "enwiki-20251220-pages-articles-multistream27.xml-p71475910p72975909.bz2"
    "enwiki-20251220-pages-articles-multistream27.xml-p72975910p74475909.bz2"
    "enwiki-20251220-pages-articles-multistream27.xml-p74475910p75975909.bz2"
    "enwiki-20251220-pages-articles-multistream27.xml-p75975910p77475909.bz2"
    "enwiki-20251220-pages-articles-multistream27.xml-p77475910p78975909.bz2"
    "enwiki-20251220-pages-articles-multistream27.xml-p78975910p80475909.bz2"
    "enwiki-20251220-pages-articles-multistream27.xml-p80475910p81895635.bz2"
    "enwiki-20251220-pages-articles-multistream-index.txt.bz2"
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

# Prefer wget if available (better for batch downloads)
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
    echo -e "${GREEN}All files already downloaded!${NC}"
    exit 0
fi

echo -e "${CYAN}Downloading ${#TO_DOWNLOAD[@]} files with $MAX_PARALLEL parallel connections...${NC}"
echo -e "${CYAN}Destination: $DEST_DIR${NC}"
echo -e "${CYAN}Using: $DOWNLOADER${NC}"
echo -e "${CYAN}Max retries per file: $MAX_RETRIES${NC}"
echo ""

COMPLETED=0
FAILED=0
START_TIME=$(date +%s)

# Process files in batches
for ((i=0; i<${#TO_DOWNLOAD[@]}; i+=MAX_PARALLEL)); do
    BATCH=("${TO_DOWNLOAD[@]:i:MAX_PARALLEL}")
    BATCH_NUM=$(( i / MAX_PARALLEL + 1 ))
    TOTAL_BATCHES=$(( (${#TO_DOWNLOAD[@]} + MAX_PARALLEL - 1) / MAX_PARALLEL ))

    echo -e "${YELLOW}Batch $BATCH_NUM/$TOTAL_BATCHES - Starting ${#BATCH[@]} downloads...${NC}"

    # Start downloads in parallel
    PIDS=()
    FILENAMES=()
    for file in "${BATCH[@]}"; do
        url="$BASE_URL$file"
        dest="$DEST_DIR/$file.tmp"  # Download to .tmp first

        (
            retry=0
            success=false

            while [[ $retry -lt $MAX_RETRIES ]] && [[ "$success" == "false" ]]; do
                if [[ $retry -gt 0 ]]; then
                    sleep $((RETRY_DELAY * retry))  # Exponential backoff
                    echo "  Retry $retry/$MAX_RETRIES for $file..." >&2
                fi

                if [[ "$DOWNLOADER" == "wget" ]]; then
                    # Use wget with progress bar and built-in retries
                    wget --show-progress --progress=bar:force --waitretry=3 --random-wait -O "$dest" "$url" 2>&1
                else
                    curl -fL --progress-bar --retry 2 --retry-delay 3 -o "$dest" "$url" 2>&1
                fi
                exit_code=$?

                # Check if download succeeded and file is not empty
                if [[ $exit_code -eq 0 ]] && [[ -s "$dest" ]]; then
                    success=true
                    mv "$dest" "${dest%.tmp}"
                    exit 0
                else
                    rm -f "$dest"
                    ((retry++))
                fi
            done

            exit 1
        ) &
        PIDS+=($!)
        FILENAMES+=("$file")
        echo "  Started: $file (PID ${PIDS[-1]})"
    done

    echo "  Waiting for ${#PIDS[@]} downloads to complete..."

    # Wait for all downloads in this batch and check exit codes
    for idx in "${!PIDS[@]}"; do
        pid=${PIDS[$idx]}
        file=${FILENAMES[$idx]}
        echo "  Waiting for PID $pid ($file)..."
        if wait "$pid"; then
            ((COMPLETED++))
            echo -e "  ${GREEN}Done: $file${NC}"
        else
            ((FAILED++))
            echo -e "  ${RED}FAIL: $file${NC}"
        fi
    done

    # Progress update
    TOTAL_PROCESSED=$((COMPLETED + FAILED))
    PCT=$(( TOTAL_PROCESSED * 100 / ${#TO_DOWNLOAD[@]} ))
    REMAINING=$(( ${#TO_DOWNLOAD[@]} - TOTAL_PROCESSED ))
    echo -e "  ${CYAN}[$PCT%] $COMPLETED done, $FAILED failed, $REMAINING remaining${NC}"
    echo ""

    # Delay between batches to avoid rate limiting (longer if there were failures)
    if [[ $i -lt $((${#TO_DOWNLOAD[@]} - MAX_PARALLEL)) ]]; then
        if [[ $FAILED -gt 0 ]]; then
            echo -e "${YELLOW}Pausing 10 seconds due to failures (rate limiting)...${NC}"
            sleep 10
        else
            sleep 3
        fi
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
