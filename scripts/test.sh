#!/bin/bash

# =============================================================================
# KeePassXC Web Manager - Test Script
# =============================================================================
# Usage:
#   ./scripts/test.sh [options]
#
# Options:
#   --all           Run all tests (default)
#   --unit          Run only unit tests
#   --integration   Run only integration tests
#   --e2e           Run only end-to-end tests
#   --security      Run only security tests
#   --coverage      Run tests with coverage report
#   --watch         Watch mode (re-run on changes)
#   --verbose       Verbose output
#   --fast          Skip slow tests
#
# Examples:
#   ./scripts/test.sh                    # Run all tests
#   ./scripts/test.sh --unit             # Run unit tests only
#   ./scripts/test.sh --coverage         # Run with coverage
#   ./scripts/test.sh --unit --fast      # Run fast unit tests
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
TEST_DIR="$PROJECT_ROOT/backend/tests"
PYTEST_ARGS=""

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

show_help() {
    cat << EOF
KeePassXC Web Manager - Test Script

Usage: $0 [options]

Options:
    --all           Run all tests (default)
    --unit          Run only unit tests
    --integration   Run only integration tests
    --e2e           Run only end-to-end tests
    --security      Run only security tests
    --coverage      Generate coverage report
    --watch         Watch mode (re-run on changes)
    --verbose       Verbose output
    --fast          Skip slow tests
    --help          Show this help message

Examples:
    $0                          # Run all tests
    $0 --unit                   # Run unit tests only
    $0 --coverage               # Run with coverage
    $0 --unit --fast            # Run fast unit tests only
EOF
}

# =============================================================================
# Parse arguments
# =============================================================================

TEST_TYPE="all"
RUN_COVERAGE=false
WATCH_MODE=false
VERBOSE=false
FAST_MODE=false

while [[ $# -gt 0 ]]; do
    case $1 in
        --all)
            TEST_TYPE="all"
            shift
            ;;
        --unit)
            TEST_TYPE="unit"
            shift
            ;;
        --integration)
            TEST_TYPE="integration"
            shift
            ;;
        --e2e)
            TEST_TYPE="e2e"
            shift
            ;;
        --security)
            TEST_TYPE="security"
            shift
            ;;
        --coverage)
            RUN_COVERAGE=true
            shift
            ;;
        --watch)
            WATCH_MODE=true
            shift
            ;;
        --verbose)
            VERBOSE=true
            shift
            ;;
        --fast)
            FAST_MODE=true
            shift
            ;;
        --help)
            show_help
            exit 0
            ;;
        *)
            log_error "Unknown option: $1"
            show_help
            exit 1
            ;;
    esac
done

# =============================================================================
# Build pytest arguments
# =============================================================================

# Base arguments
PYTEST_ARGS="--strict-markers"

# Verbose mode
if [ "$VERBOSE" = true ]; then
    PYTEST_ARGS="$PYTEST_ARGS -vv"
else
    PYTEST_ARGS="$PYTEST_ARGS -v"
fi

# Fast mode (skip slow tests)
if [ "$FAST_MODE" = true ]; then
    PYTEST_ARGS="$PYTEST_ARGS -m 'not slow'"
    log_info "Fast mode: Skipping slow tests"
fi

# Test selection
case "$TEST_TYPE" in
    unit)
        PYTEST_ARGS="$PYTEST_ARGS -m unit"
        log_info "Running UNIT tests"
        ;;
    integration)
        PYTEST_ARGS="$PYTEST_ARGS -m integration"
        log_info "Running INTEGRATION tests"
        ;;
    e2e)
        PYTEST_ARGS="$PYTEST_ARGS -m e2e"
        log_info "Running END-TO-END tests"
        ;;
    security)
        PYTEST_ARGS="$PYTEST_ARGS -m security"
        log_info "Running SECURITY tests"
        ;;
    all)
        log_info "Running ALL tests"
        ;;
esac

# Coverage
if [ "$RUN_COVERAGE" = true ]; then
    PYTEST_ARGS="$PYTEST_ARGS --cov=backend/app --cov-report=term-missing --cov-report=html"
    log_info "Coverage reporting enabled"
fi

# Watch mode
if [ "$WATCH_MODE" = true ]; then
    PYTEST_ARGS="$PYTEST_ARGS -f"
    log_info "Watch mode enabled"
fi

# =============================================================================
# Run tests
# =============================================================================

echo ""
echo "╔═══════════════════════════════════════════════════════════╗"
echo "║       KeePassXC Web Manager - Test Runner                ║"
echo "╚═══════════════════════════════════════════════════════════╝"
echo ""

log_info "Project root: $PROJECT_ROOT"
log_info "Test directory: $TEST_DIR"
echo ""

# Check if tests directory exists
if [ ! -d "$TEST_DIR" ]; then
    log_error "Test directory not found: $TEST_DIR"
    exit 1
fi

# Check Poetry
if ! command -v poetry &> /dev/null; then
    log_error "Poetry is not installed"
    exit 1
fi

# Run tests
cd "$PROJECT_ROOT"

log_info "Running pytest with args: $PYTEST_ARGS"
echo ""

if poetry run pytest $PYTEST_ARGS "$TEST_DIR"; then
    echo ""
    log_success "All tests passed! ✅"

    # Show coverage report location if generated
    if [ "$RUN_COVERAGE" = true ]; then
        echo ""
        log_info "Coverage HTML report: file://$PROJECT_ROOT/coverage_html/index.html"
    fi

    exit 0
else
    echo ""
    log_error "Tests failed! ❌"
    exit 1
fi
