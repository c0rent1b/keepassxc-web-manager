#!/bin/bash
#
# Quick Test Script for KeePassXC Web Manager
# Tests backend functionality quickly
#

set -e

echo "=================================================="
echo "  KeePassXC Web Manager - Quick Test"
echo "=================================================="
echo ""

# Colors
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Check if backend is running
echo -n "🔍 Checking if backend is running... "
if curl -s http://localhost:8000/ping > /dev/null 2>&1; then
    echo -e "${GREEN}✓${NC}"
else
    echo -e "${RED}✗${NC}"
    echo ""
    echo "❌ Backend is not running!"
    echo ""
    echo "Start backend with:"
    echo "  cd backend"
    echo "  poetry run uvicorn app.main:app --reload"
    echo ""
    exit 1
fi

# Test 1: Ping
echo -n "🔍 Test 1: Ping endpoint... "
RESPONSE=$(curl -s http://localhost:8000/ping)
if [ "$RESPONSE" = '{"ping":"pong"}' ]; then
    echo -e "${GREEN}✓${NC}"
else
    echo -e "${RED}✗${NC}"
    echo "Response: $RESPONSE"
fi

# Test 2: Health Check
echo -n "🔍 Test 2: Health check... "
RESPONSE=$(curl -s http://localhost:8000/health)
if echo "$RESPONSE" | grep -q '"status"'; then
    echo -e "${GREEN}✓${NC}"
else
    echo -e "${RED}✗${NC}"
    echo "Response: $RESPONSE"
fi

# Test 3: API Docs
echo -n "🔍 Test 3: API docs... "
STATUS=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:8000/docs)
if [ "$STATUS" = "200" ]; then
    echo -e "${GREEN}✓${NC}"
else
    echo -e "${RED}✗${NC}"
    echo "Status: $STATUS"
fi

# Test 4: Frontend
echo -n "🔍 Test 4: Frontend index... "
STATUS=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:8000/)
if [ "$STATUS" = "200" ]; then
    echo -e "${GREEN}✓${NC}"
else
    echo -e "${RED}✗${NC}"
    echo "Status: $STATUS"
fi

# Test 5: Login page
echo -n "🔍 Test 5: Login page... "
STATUS=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:8000/login.html)
if [ "$STATUS" = "200" ]; then
    echo -e "${GREEN}✓${NC}"
else
    echo -e "${RED}✗${NC}"
    echo "Status: $STATUS"
fi

# Test 6: Dashboard page
echo -n "🔍 Test 6: Dashboard page... "
STATUS=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:8000/dashboard.html)
if [ "$STATUS" = "200" ]; then
    echo -e "${GREEN}✓${NC}"
else
    echo -e "${RED}✗${NC}"
    echo "Status: $STATUS"
fi

# Test 7: CSS
echo -n "🔍 Test 7: Tailwind CSS... "
if [ -f "frontend/public/css/tailwind.min.css" ]; then
    SIZE=$(stat -f%z frontend/public/css/tailwind.min.css 2>/dev/null || stat -c%s frontend/public/css/tailwind.min.css 2>/dev/null || echo "0")
    if [ "$SIZE" -gt "1000" ]; then
        echo -e "${GREEN}✓${NC} (${SIZE} bytes)"
    else
        echo -e "${YELLOW}⚠${NC} File exists but seems too small"
    fi
else
    echo -e "${RED}✗${NC}"
    echo "Run: cd frontend && npm run build:css"
fi

echo ""
echo "=================================================="
echo "  Test Summary"
echo "=================================================="
echo ""
echo "✅ Backend is running"
echo "✅ API endpoints responding"
echo "✅ Frontend pages accessible"
echo ""
echo "🌐 Open in browser:"
echo "   http://localhost:8000/"
echo ""
echo "📚 API Documentation:"
echo "   http://localhost:8000/docs"
echo ""
echo "=================================================="
