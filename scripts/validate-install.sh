#!/bin/bash

# =============================================================================
# KeePassXC Web Manager - Installation Validation Script (Fixed)
# =============================================================================

set -e

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# Counters
TOTAL_CHECKS=0
PASSED_CHECKS=0
FAILED_CHECKS=0
WARNING_CHECKS=0

# =============================================================================
# Functions
# =============================================================================

log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[✓]${NC} $1"
    ((PASSED_CHECKS++))
}

log_warning() {
    echo -e "${YELLOW}[!]${NC} $1"
    ((WARNING_CHECKS++))
}

log_error() {
    echo -e "${RED}[✗]${NC} $1"
    ((FAILED_CHECKS++))
}

check_command() {
    local cmd=$1
    local name=$2

    ((TOTAL_CHECKS++))

    if which "$cmd" > /dev/null 2>&1; then
        log_success "$name found"
        return 0
    else
        log_error "$name not found"
        return 1
    fi
}

check_file() {
    local file=$1
    local name=$2

    ((TOTAL_CHECKS++))

    if [ -f "$file" ]; then
        log_success "$name exists"
        return 0
    else
        log_error "$name missing: $file"
        return 1
    fi
}

check_directory() {
    local dir=$1
    local name=$2

    ((TOTAL_CHECKS++))

    if [ -d "$dir" ]; then
        log_success "$name exists"
        return 0
    else
        log_error "$name missing: $dir"
        return 1
    fi
}

# =============================================================================
# Main Validation
# =============================================================================

echo ""
echo "╔═══════════════════════════════════════════════════════════╗"
echo "║   KeePassXC Web Manager - Installation Validation        ║"
echo "╚═══════════════════════════════════════════════════════════╝"
echo ""

# -----------------------------------------------------------------------------
# 1. Check Prerequisites
# -----------------------------------------------------------------------------

log_info "Checking prerequisites..."
echo ""

check_command "python3" "Python 3"
check_command "poetry" "Poetry"
check_command "keepassxc-cli" "KeePassXC CLI"
check_command "docker" "Docker"

echo ""

# Check Python version
((TOTAL_CHECKS++))
PYTHON_VERSION=$(python3 --version 2>&1 | grep -oP '[\d.]+' || echo "unknown")
if python3 -c 'import sys; exit(0 if sys.version_info >= (3, 12) else 1)' 2>/dev/null; then
    log_success "Python version $PYTHON_VERSION is >= 3.12"
else
    log_error "Python version $PYTHON_VERSION is < 3.12"
fi

# Check Poetry version
((TOTAL_CHECKS++))
POETRY_VERSION=$(poetry --version 2>&1 | grep -oP '[\d.]+' || echo "unknown")
log_success "Poetry version: $POETRY_VERSION"

# Check KeePassXC version
((TOTAL_CHECKS++))
if which keepassxc-cli > /dev/null 2>&1; then
    KEEPASSXC_VERSION=$(keepassxc-cli --version 2>&1 | head -1 || echo "unknown")
    log_success "KeePassXC CLI version: $KEEPASSXC_VERSION"
else
    log_warning "KeePassXC CLI not found"
fi

# -----------------------------------------------------------------------------
# 2. Check Project Structure
# -----------------------------------------------------------------------------

echo ""
log_info "Checking project structure..."
echo ""

check_file "pyproject.toml" "Poetry config"
check_file "package.json" "Node.js config"
check_file "tailwind.config.js" "Tailwind config"
check_file "docker-compose.yml" "Docker Compose config"
check_file ".env.example" "Environment template"
check_file ".gitignore" "Git ignore file"
check_file "README.md" "README"

echo ""

check_directory "backend/app" "Backend application"
check_directory "backend/tests" "Backend tests"
check_directory "frontend/src" "Frontend source"
check_directory "scripts" "Utility scripts"

# -----------------------------------------------------------------------------
# 3. Check Configuration
# -----------------------------------------------------------------------------

echo ""
log_info "Checking configuration..."
echo ""

# Check pyproject.toml for package-mode
((TOTAL_CHECKS++))
if grep -q "package-mode = false" pyproject.toml 2>/dev/null; then
    log_success "Poetry package-mode correctly set to false"
else
    log_error "Poetry package-mode not set (should be 'false')"
fi

# Check if .env exists
((TOTAL_CHECKS++))
if [ -f ".env" ]; then
    log_success ".env file exists"
else
    log_warning ".env file not found (copy from .env.example)"
fi

# -----------------------------------------------------------------------------
# 4. Check Docker
# -----------------------------------------------------------------------------

echo ""
log_info "Checking Docker..."
echo ""

# Check if Docker daemon is running
((TOTAL_CHECKS++))
if docker info > /dev/null 2>&1; then
    log_success "Docker daemon is running"

    # Check if Redis container exists
    ((TOTAL_CHECKS++))
    if docker compose ps 2>/dev/null | grep -q "redis"; then
        log_success "Redis container exists"

        # Check if Redis is running
        ((TOTAL_CHECKS++))
        if docker compose ps 2>/dev/null | grep "redis" | grep -q "Up"; then
            log_success "Redis container is running"

            # Test Redis connection
            ((TOTAL_CHECKS++))
            if docker compose exec -T redis redis-cli ping 2>&1 | grep -q "PONG"; then
                log_success "Redis connection working"
            else
                log_warning "Redis connection test failed"
            fi
        else
            log_warning "Redis container not running (run: docker compose up -d redis)"
        fi
    else
        log_warning "Redis container not created (run: docker compose up -d redis)"
    fi
else
    log_error "Docker daemon not running (run: sudo systemctl start docker)"
fi

# -----------------------------------------------------------------------------
# 5. Check Poetry Dependencies
# -----------------------------------------------------------------------------

echo ""
log_info "Checking Poetry dependencies..."
echo ""

((TOTAL_CHECKS++))
if [ -f "poetry.lock" ]; then
    log_success "poetry.lock file exists"

    # Check if FastAPI is installed
    ((TOTAL_CHECKS++))
    if poetry run python -c "import fastapi" 2>/dev/null; then
        log_success "FastAPI is installed"
    else
        log_error "FastAPI not installed (run: poetry install)"
    fi

    # Check if Redis is installed
    ((TOTAL_CHECKS++))
    if poetry run python -c "import redis" 2>/dev/null; then
        log_success "Redis Python client is installed"
    else
        log_error "Redis not installed (run: poetry install)"
    fi

    # Check if Pytest is installed
    ((TOTAL_CHECKS++))
    if poetry run python -c "import pytest" 2>/dev/null; then
        log_success "Pytest is installed"
    else
        log_error "Pytest not installed (run: poetry install)"
    fi
else
    log_warning "poetry.lock not found (run: poetry install)"
fi

# -----------------------------------------------------------------------------
# 6. Check Scripts
# -----------------------------------------------------------------------------

echo ""
log_info "Checking script permissions..."
echo ""

((TOTAL_CHECKS++))
if [ -x "scripts/start.sh" ]; then
    log_success "start.sh is executable"
else
    log_warning "start.sh not executable (run: chmod +x scripts/start.sh)"
fi

((TOTAL_CHECKS++))
if [ -x "scripts/test.sh" ]; then
    log_success "test.sh is executable"
else
    log_warning "test.sh not executable (run: chmod +x scripts/test.sh)"
fi

((TOTAL_CHECKS++))
if [ -x "scripts/lint.sh" ]; then
    log_success "lint.sh is executable"
else
    log_warning "lint.sh not executable (run: chmod +x scripts/lint.sh)"
fi

# -----------------------------------------------------------------------------
# 7. Check Node.js (optional)
# -----------------------------------------------------------------------------

echo ""
log_info "Checking Node.js setup..."
echo ""

((TOTAL_CHECKS++))
if which npm > /dev/null 2>&1; then
    NPM_VERSION=$(npm --version 2>&1 || echo "unknown")
    log_success "npm found: $NPM_VERSION"

    ((TOTAL_CHECKS++))
    if [ -d "node_modules" ]; then
        log_success "node_modules directory exists"

        # Check if Tailwind is installed
        ((TOTAL_CHECKS++))
        if [ -d "node_modules/tailwindcss" ]; then
            log_success "Tailwind CSS is installed"
        else
            log_warning "Tailwind CSS not installed (run: npm install)"
        fi
    else
        log_warning "node_modules not found (run: npm install)"
    fi
else
    log_warning "npm not found (Tailwind CSS build will not work)"
fi

# -----------------------------------------------------------------------------
# Summary
# -----------------------------------------------------------------------------

echo ""
echo "═══════════════════════════════════════════════════════════"
echo "                      VALIDATION SUMMARY"
echo "═══════════════════════════════════════════════════════════"
echo ""

echo "Total checks:    $TOTAL_CHECKS"
echo -e "${GREEN}Passed:          $PASSED_CHECKS${NC}"
echo -e "${YELLOW}Warnings:        $WARNING_CHECKS${NC}"
echo -e "${RED}Failed:          $FAILED_CHECKS${NC}"

echo ""

if [ $FAILED_CHECKS -eq 0 ]; then
    if [ $WARNING_CHECKS -eq 0 ]; then
        echo -e "${GREEN}✅ Perfect! All checks passed.${NC}"
        echo ""
        echo "You can now start the application:"
        echo "  ./scripts/start.sh development"
        exit 0
    else
        echo -e "${YELLOW}⚠️  Installation mostly complete, but with warnings.${NC}"
        echo ""
        echo "Review warnings above and fix if needed."
        echo "You can try starting the application:"
        echo "  ./scripts/start.sh development"
        exit 0
    fi
else
    echo -e "${RED}❌ Some checks failed. Please fix the errors above.${NC}"
    echo ""
    echo "Common fixes:"
    echo "  - Install missing dependencies: poetry install"
    echo "  - Start Docker: sudo systemctl start docker"
    echo "  - Start Redis: docker compose up -d redis"
    echo "  - Make scripts executable: chmod +x scripts/*.sh"
    echo ""
    echo "See TROUBLESHOOTING.md for detailed help."
    exit 1
fi
