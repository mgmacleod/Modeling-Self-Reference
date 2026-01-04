#!/bin/bash
# Download and prepare data from HuggingFace for local analysis
#
# This script encapsulates the one-time data preparation steps:
#   1. Download data from HuggingFace (if not cached)
#   2. Create symlinks from data/wikipedia/processed/ to HF cache
#   3. Generate basin visualization images (PNG)
#   4. Regenerate gallery HTML
#
# Prerequisites:
#   - Virtual environment activated (source .venv/bin/activate)
#   - Python dependencies installed (pip install -r requirements.txt)
#
# Usage:
#   ./prepare-data.sh [OPTIONS]
#
# Options:
#   --skip-download     Skip HuggingFace download (use existing cache)
#   --skip-symlinks     Skip symlink creation
#   --skip-images       Skip basin image generation
#   --skip-gallery      Skip gallery regeneration
#   --force-symlinks    Overwrite existing symlinks
#   --validate-only     Only validate data, don't prepare anything
#   --dry-run           Show what would be done without executing
#   --help              Show this help message
#
# Examples:
#   ./prepare-data.sh                    # Full preparation
#   ./prepare-data.sh --skip-images      # Skip slow image generation
#   ./prepare-data.sh --validate-only    # Just check data exists

set -e

# Get script directory and repo root
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"

# Default configuration
SKIP_DOWNLOAD=false
SKIP_SYMLINKS=false
SKIP_IMAGES=false
SKIP_GALLERY=false
FORCE_SYMLINKS=false
VALIDATE_ONLY=false
DRY_RUN=false

# HuggingFace configuration
HF_CACHE_DIR="$HOME/.cache/wikipedia-nlink-basins/mgmacleod_wikidata1"
DATA_DIR="$REPO_ROOT/data/wikipedia/processed"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Parse command line arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        --skip-download)
            SKIP_DOWNLOAD=true
            shift
            ;;
        --skip-symlinks)
            SKIP_SYMLINKS=true
            shift
            ;;
        --skip-images)
            SKIP_IMAGES=true
            shift
            ;;
        --skip-gallery)
            SKIP_GALLERY=true
            shift
            ;;
        --force-symlinks)
            FORCE_SYMLINKS=true
            shift
            ;;
        --validate-only)
            VALIDATE_ONLY=true
            shift
            ;;
        --dry-run)
            DRY_RUN=true
            shift
            ;;
        --help)
            head -35 "$0" | tail -30
            exit 0
            ;;
        *)
            echo -e "${RED}Unknown option: $1${NC}"
            exit 1
            ;;
    esac
done

# Helper functions
log_step() {
    echo -e "\n${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo -e "${BLUE}▶ $1${NC}"
    echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
}

log_success() {
    echo -e "${GREEN}✓ $1${NC}"
}

log_warning() {
    echo -e "${YELLOW}⚠ $1${NC}"
}

log_error() {
    echo -e "${RED}✗ $1${NC}"
}

log_info() {
    echo -e "  $1"
}

# Check Python environment
check_python() {
    log_step "Checking Python Environment"

    if ! command -v python &> /dev/null && ! command -v python3 &> /dev/null; then
        log_error "Python not found in PATH"
        exit 1
    fi

    # Prefer python3 if available
    if command -v python3 &> /dev/null; then
        PYTHON=python3
    else
        PYTHON=python
    fi

    local version=$($PYTHON --version 2>&1)
    log_success "Python: $version"

    # Check if we're in a virtual environment
    if [[ -z "$VIRTUAL_ENV" ]]; then
        log_warning "Not in a virtual environment"
        log_info "Consider: source $REPO_ROOT/.venv/bin/activate"
    else
        log_success "Virtual environment: $VIRTUAL_ENV"
    fi

    # Check required packages
    local missing=()
    for pkg in huggingface_hub pandas pyarrow plotly kaleido; do
        if ! $PYTHON -c "import $pkg" 2>/dev/null; then
            missing+=("$pkg")
        fi
    done

    if [ ${#missing[@]} -gt 0 ]; then
        log_error "Missing packages: ${missing[*]}"
        log_info "Run: pip install -r requirements.txt"
        exit 1
    fi

    log_success "Required packages installed"
}

# Download data from HuggingFace
download_data() {
    if $SKIP_DOWNLOAD; then
        log_warning "Skipping HuggingFace download (--skip-download)"
        return 0
    fi

    log_step "Downloading Data from HuggingFace"

    if $DRY_RUN; then
        echo -e "${YELLOW}[DRY-RUN]${NC} Would run: $PYTHON $REPO_ROOT/n-link-analysis/scripts/data_loader.py --data-source huggingface --validate"
        return 0
    fi

    if $PYTHON "$REPO_ROOT/n-link-analysis/scripts/data_loader.py" --data-source huggingface --validate; then
        log_success "Data downloaded and validated"
    else
        log_error "Data download failed"
        exit 1
    fi
}

# Create symlinks to HuggingFace cache
create_symlinks() {
    if $SKIP_SYMLINKS; then
        log_warning "Skipping symlink creation (--skip-symlinks)"
        return 0
    fi

    log_step "Creating Data Symlinks"

    # Ensure data directory exists
    mkdir -p "$DATA_DIR"

    # Define symlinks to create
    declare -A SYMLINKS=(
        ["nlink_sequences.parquet"]="$HF_CACHE_DIR/data/source/nlink_sequences.parquet"
        ["pages.parquet"]="$HF_CACHE_DIR/data/source/pages.parquet"
        ["multiplex"]="$HF_CACHE_DIR/data/multiplex"
        ["analysis"]="$HF_CACHE_DIR/data/analysis"
    )

    local created=0
    local skipped=0
    local failed=0

    for name in "${!SYMLINKS[@]}"; do
        local target="${SYMLINKS[$name]}"
        local link="$DATA_DIR/$name"

        if $DRY_RUN; then
            echo -e "${YELLOW}[DRY-RUN]${NC} Would create: $link -> $target"
            continue
        fi

        # Check if target exists
        if [ ! -e "$target" ]; then
            log_warning "Target not found: $target"
            ((failed++)) || true
            continue
        fi

        # Handle existing symlink or file
        if [ -L "$link" ]; then
            if $FORCE_SYMLINKS; then
                rm "$link"
                log_info "Removed existing symlink: $name"
            else
                log_info "Exists: $name"
                ((skipped++)) || true
                continue
            fi
        elif [ -e "$link" ]; then
            log_warning "Regular file exists (not symlink): $link"
            ((skipped++)) || true
            continue
        fi

        # Create symlink
        if ln -sf "$target" "$link"; then
            log_info "Created: $name -> $target"
            ((created++)) || true
        else
            log_warning "Failed to create symlink: $name"
            ((failed++)) || true
        fi
    done

    if $DRY_RUN; then
        log_success "Symlinks: would create ${#SYMLINKS[@]} symlinks"
    else
        log_success "Symlinks: $created created, $skipped skipped, $failed failed"
    fi
}

# Generate basin visualization images
generate_images() {
    if $SKIP_IMAGES; then
        log_warning "Skipping basin image generation (--skip-images)"
        return 0
    fi

    log_step "Generating Basin Visualization Images"

    local viz_script="$REPO_ROOT/n-link-analysis/viz/batch-render-basin-images.py"

    if $DRY_RUN; then
        echo -e "${YELLOW}[DRY-RUN]${NC} Would run: $PYTHON $viz_script --n 5 --all-cycles"
        return 0
    fi

    if $PYTHON "$viz_script" --n 5 --all-cycles; then
        log_success "Basin images generated"
    else
        log_warning "Basin image generation failed - continuing anyway"
    fi
}

# Regenerate gallery HTML
generate_gallery() {
    if $SKIP_GALLERY; then
        log_warning "Skipping gallery regeneration (--skip-gallery)"
        return 0
    fi

    log_step "Regenerating Gallery HTML"

    local gallery_script="$REPO_ROOT/n-link-analysis/viz/create-visualization-gallery.py"

    if $DRY_RUN; then
        echo -e "${YELLOW}[DRY-RUN]${NC} Would run: $PYTHON $gallery_script"
        return 0
    fi

    if $PYTHON "$gallery_script"; then
        log_success "Gallery HTML generated"
    else
        log_warning "Gallery generation failed - continuing anyway"
    fi
}

# Validate data setup
validate_data() {
    log_step "Validating Data Setup"

    local errors=0

    # Check symlinks
    for name in nlink_sequences.parquet pages.parquet multiplex analysis; do
        local path="$DATA_DIR/$name"
        if [ -L "$path" ]; then
            if [ -e "$path" ]; then
                log_success "Symlink valid: $name"
            else
                log_error "Broken symlink: $name"
                ((errors++)) || true
            fi
        elif [ -e "$path" ]; then
            log_success "File exists: $name"
        else
            log_error "Missing: $name"
            ((errors++)) || true
        fi
    done

    # Check basin images
    local assets_dir="$REPO_ROOT/n-link-analysis/report/assets"
    local png_count=$(ls -1 "$assets_dir"/basin_3d_n=5_cycle=*.png 2>/dev/null | wc -l)

    if [ "$png_count" -ge 9 ]; then
        log_success "Basin images: $png_count PNGs found"
    else
        log_warning "Basin images: only $png_count PNGs (expected 9)"
    fi

    # Check gallery
    if [ -f "$assets_dir/gallery.html" ]; then
        log_success "Gallery HTML exists"
    else
        log_warning "Gallery HTML missing"
    fi

    # Run data_loader validation
    if $PYTHON "$REPO_ROOT/n-link-analysis/scripts/data_loader.py" --validate 2>&1 | grep -q "All checks passed"; then
        log_success "Data loader validation passed"
    else
        log_error "Data loader validation failed"
        ((errors++)) || true
    fi

    if [ $errors -eq 0 ]; then
        log_success "All validation checks passed"
        return 0
    else
        log_error "$errors validation errors found"
        return 1
    fi
}

# Print summary
print_summary() {
    log_step "Data Preparation Complete"

    if $DRY_RUN; then
        log_warning "This was a dry run - no changes were made"
        return 0
    fi

    echo ""
    echo "Data is ready for analysis!"
    echo ""
    echo "Next steps:"
    echo "  - View gallery: xdg-open $REPO_ROOT/n-link-analysis/report/assets/gallery.html"
    echo "  - Start API:    cd $REPO_ROOT && uvicorn nlink_api.main:app --port 28000"
    echo "  - Generate reports: $SCRIPT_DIR/generate-all-reports.sh"
    echo ""
}

# Main execution
main() {
    echo -e "${BLUE}"
    echo "╔══════════════════════════════════════════════════════════════════╗"
    echo "║           N-Link Data Preparation Pipeline                       ║"
    echo "╚══════════════════════════════════════════════════════════════════╝"
    echo -e "${NC}"

    echo "Configuration:"
    echo "  Repo Root:     $REPO_ROOT"
    echo "  Data Dir:      $DATA_DIR"
    echo "  HF Cache:      $HF_CACHE_DIR"
    echo "  Dry Run:       $DRY_RUN"
    echo "  Validate Only: $VALIDATE_ONLY"

    if $DRY_RUN; then
        echo ""
        log_warning "DRY RUN MODE - No changes will be made"
    fi

    check_python

    if $VALIDATE_ONLY; then
        validate_data
        exit $?
    fi

    download_data
    create_symlinks
    generate_images
    generate_gallery
    validate_data
    print_summary
}

main "$@"
