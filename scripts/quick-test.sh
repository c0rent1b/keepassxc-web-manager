#!/bin/bash

# =============================================================================
# KeePassXC Web Manager - Quick Test Script
# =============================================================================
# This script performs quick health checks on the backend API
#
# Usage:
#   ./scripts/quick-test.sh
#
# Prerequisites:
#   - Backend must be running on http://localhost:8000
#   - curl must be installed
#
# =============================================================================

set -e  # Exit on error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
API_BASE_URL="${API_BASE_URL:-http://localhost:8000}"
TIMEOUT=5

# =============================================================================
# Functions
# =============================================================================

log_info() {
    echo -e "${BLUE}ℹ${NC} $1"
}

log_success() {
    echo -e "${GREEN}✓${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}⚠${NC} $1"
}

log_error() {
    echo -e "${RED}✗${NC} $1"
}

# Test if server is running
check_server() {
    if ! curl -s --max-time "$TIMEOUT" "$API_BASE_URL/ping" > /dev/null 2>&1; then
        log_error "Backend is not running or not accessible at $API_BASE_URL"
        log_info "Start the backend with: ./scripts/start.sh"
        exit 1
    fi
}

# Test endpoint
test_endpoint() {
    local name="$1"
    local endpoint="$2"
    local expected_status="${3:-200}"

    echo -n "🔍 Test $name... "

    RESPONSE=$(curl -s -w "\n%{http_code}" --max-time "$TIMEOUT" "$API_BASE_URL$endpoint" 2>&1)
    HTTP_CODE=$(echo "$RESPONSE" | tail -n1)
    BODY=$(echo "$RESPONSE" | head -n-1)

    if [ "$HTTP_CODE" -eq "$expected_status" ]; then
        log_success "$name works (HTTP $HTTP_CODE)"
        return 0
    else
        log_error "$name failed (HTTP $HTTP_CODE, expected $expected_status)"
        return 1
    fi
}

# =============================================================================
# Main execution
# =============================================================================

echo ""
echo "╔═══════════════════════════════════════════════════════════╗"
echo "║       KeePassXC Web Manager - Quick Test                 ║"
echo "╚═══════════════════════════════════════════════════════════╝"
echo ""

log_info "Testing backend at: $API_BASE_URL"
echo ""

# Check if server is running
check_server

# Run tests
TESTS_PASSED=0
TESTS_FAILED=0

# Test 1: Ping endpoint
if test_endpoint "Ping" "/ping" 200; then
    ((TESTS_PASSED++))
else
    ((TESTS_FAILED++))
fi

# Test 2: Health endpoint
if test_endpoint "Health Check" "/health" 200; then
    ((TESTS_PASSED++))
else
    ((TESTS_FAILED++))
fi

# Test 3: API docs
if test_endpoint "API Docs" "/docs" 200; then
    ((TESTS_PASSED++))
else
    ((TESTS_FAILED++))
fi

# Test 4: OpenAPI spec
if test_endpoint "OpenAPI Spec" "/openapi.json" 200; then
    ((TESTS_PASSED++))
else
    ((TESTS_FAILED++))
fi

# Test 5: Frontend - Login page
if test_endpoint "Login Page" "/" 200; then
    ((TESTS_PASSED++))
else
    ((TESTS_FAILED++))
fi

# Test 6: Frontend - Dashboard page
if test_endpoint "Dashboard Page" "/dashboard.html" 200; then
    ((TESTS_PASSED++))
else
    ((TESTS_FAILED++))
fi

# Test 7: Frontend - CSS
if test_endpoint "Tailwind CSS" "/css/tailwind.min.css" 200; then
    ((TESTS_PASSED++))
else
    ((TESTS_FAILED++))
fi

# Summary
echo ""
echo "═══════════════════════════════════════════════════════════"
echo "Summary: $TESTS_PASSED passed, $TESTS_FAILED failed"
echo "═══════════════════════════════════════════════════════════"
echo ""

if [ "$TESTS_FAILED" -eq 0 ]; then
    log_success "All tests passed! Backend is healthy."
    echo ""
    log_info "Next steps:"
    echo "  1. Open http://localhost:8000/ in your browser"
    echo "  2. Test login with your KeePassXC database"
    echo "  3. Explore the dashboard"
    echo ""
    log_info "API Documentation: http://localhost:8000/docs"
    exit 0
else
    log_warning "Some tests failed. Check the backend logs."
    echo ""
    log_info "Troubleshooting:"
    echo "  - Ensure backend is running: ./scripts/start.sh"
    echo "  - Check backend logs for errors"
    echo "  - Verify Tailwind CSS is built: cd frontend && npm run build:css"
    exit 1
fi
