#!/bin/bash

# =============================================================================
# KeePassXC Web Manager - Linting Script
# =============================================================================
# Usage:
#   ./scripts/lint.sh [options]
#
# Options:
#   --fix       Auto-fix issues where possible
#   --check     Check only (no fixes)
#   --all       Run all linters (default)
#   --ruff      Run only Ruff
#   --mypy      Run only MyPy
#
# =============================================================================

set -e

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# Configuration
PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
BACKEND_DIR="$PROJECT_ROOT/backend"

# =============================================================================
# Functions
# =============================================================================

log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

run_ruff() {
    local mode=$1
    log_info "Running Ruff..."

    cd "$PROJECT_ROOT"

    if [ "$mode" = "fix" ]; then
        poetry run ruff check backend/app --fix
        poetry run ruff format backend/app
        log_success "Ruff: Fixed and formatted"
    else
        poetry run ruff check backend/app
        poetry run ruff format backend/app --check
        log_success "Ruff: All checks passed"
    fi
}

run_mypy() {
    log_info "Running MyPy (type checking)..."

    cd "$PROJECT_ROOT"

    poetry run mypy backend/app
    log_success "MyPy: Type checking passed"
}

# =============================================================================
# Parse arguments
# =============================================================================

MODE="check"
TARGET="all"

while [[ $# -gt 0 ]]; do
    case $1 in
        --fix)
            MODE="fix"
            shift
            ;;
        --check)
            MODE="check"
            shift
            ;;
        --all)
            TARGET="all"
            shift
            ;;
        --ruff)
            TARGET="ruff"
            shift
            ;;
        --mypy)
            TARGET="mypy"
            shift
            ;;
        *)
            log_error "Unknown option: $1"
            exit 1
            ;;
    esac
done

# =============================================================================
# Main execution
# =============================================================================

echo ""
echo "╔═══════════════════════════════════════════════════════════╗"
echo "║       KeePassXC Web Manager - Linting                    ║"
echo "╚═══════════════════════════════════════════════════════════╝"
echo ""

log_info "Mode: $MODE"
log_info "Target: $TARGET"
echo ""

FAILED=false

# Run linters based on target
if [ "$TARGET" = "all" ] || [ "$TARGET" = "ruff" ]; then
    if ! run_ruff "$MODE"; then
        FAILED=true
    fi
    echo ""
fi

if [ "$TARGET" = "all" ] || [ "$TARGET" = "mypy" ]; then
    if ! run_mypy; then
        FAILED=true
    fi
    echo ""
fi

# Final result
if [ "$FAILED" = true ]; then
    log_error "Linting failed! ❌"
    exit 1
else
    log_success "All linting checks passed! ✅"
    exit 0
fi
