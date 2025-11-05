#!/bin/bash

# =============================================================================
# KeePassXC Web Manager - Start Script
# =============================================================================
# Usage:
#   ./scripts/start.sh [environment]
#
# Arguments:
#   environment: development (default), production, staging
#
# Examples:
#   ./scripts/start.sh                    # Start in development mode
#   ./scripts/start.sh production         # Start in production mode
#
# =============================================================================

set -e  # Exit on error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Default configuration
ENVIRONMENT="${1:-development}"
PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

# =============================================================================
# Functions
# =============================================================================

log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

check_requirements() {
    log_info "Checking requirements..."

    # Check Python version
    if ! command -v python3 &> /dev/null; then
        log_error "Python 3 is not installed"
        exit 1
    fi

    PYTHON_VERSION=$(python3 --version | cut -d' ' -f2)
    log_success "Python $PYTHON_VERSION found"

    # Check Poetry
    if ! command -v poetry &> /dev/null; then
        log_error "Poetry is not installed"
        log_info "Install with: curl -sSL https://install.python-poetry.org | python3 -"
        exit 1
    fi
    log_success "Poetry found"

    # Check KeePassXC CLI
    if ! command -v keepassxc-cli &> /dev/null; then
        log_warning "keepassxc-cli not found in PATH"
        log_info "Install KeePassXC: https://keepassxc.org/download"
    else
        KEEPASSXC_VERSION=$(keepassxc-cli --version 2>&1 | head -n1)
        log_success "KeePassXC CLI found: $KEEPASSXC_VERSION"
    fi

    # Check .env file
    if [ ! -f "$PROJECT_ROOT/.env" ]; then
        log_warning ".env file not found"
        log_info "Creating .env from .env.example..."
        cp "$PROJECT_ROOT/.env.example" "$PROJECT_ROOT/.env"
        log_success ".env file created - Please configure it before running"
        exit 0
    fi
}

start_services() {
    log_info "Starting services..."

    # Start Redis if using Docker Compose (optional)
    if [ -f "$PROJECT_ROOT/docker-compose.yml" ]; then
        # Check if docker or docker compose is available
        if command -v docker &> /dev/null; then
            log_info "Starting Redis with Docker Compose..."
            cd "$PROJECT_ROOT"

            # Try Docker Compose V2 (docker compose) first, then V1 (docker-compose)
            if docker compose version &> /dev/null; then
                docker compose up -d redis
                log_success "Redis started (Docker Compose V2)"
            elif command -v docker-compose &> /dev/null; then
                docker-compose up -d redis
                log_success "Redis started (Docker Compose V1)"
            else
                log_warning "Docker Compose not available - will use memory cache"
                log_info "Application will work without Redis (memory cache fallback)"
            fi
        else
            log_warning "Docker not available - will use memory cache"
            log_info "Application will work without Redis (memory cache fallback)"
        fi
    else
        log_warning "docker-compose.yml not found - will use memory cache"
    fi
}

start_development() {
    log_info "Starting in DEVELOPMENT mode..."

    cd "$PROJECT_ROOT"

    # Install dependencies
    log_info "Installing dependencies with Poetry..."
    poetry install

    # Start Tailwind CSS watcher in background
    if [ -f "$PROJECT_ROOT/package.json" ]; then
        log_info "Starting Tailwind CSS watcher..."
        npm install 2>/dev/null || true
        npm run dev &
        TAILWIND_PID=$!
        log_success "Tailwind CSS watcher started (PID: $TAILWIND_PID)"
    fi

    # Start FastAPI with uvicorn (hot reload)
    log_info "Starting FastAPI server with hot reload..."
    cd "$PROJECT_ROOT/backend"

    poetry run uvicorn app.main:app \
        --reload \
        --host 127.0.0.1 \
        --port 8000 \
        --log-level info

    # Cleanup on exit
    if [ -n "$TAILWIND_PID" ]; then
        kill $TAILWIND_PID 2>/dev/null || true
    fi
}

start_production() {
    log_info "Starting in PRODUCTION mode..."

    cd "$PROJECT_ROOT"

    # Install dependencies (no dev dependencies)
    log_info "Installing production dependencies..."
    poetry install --no-dev

    # Build Tailwind CSS (minified)
    if [ -f "$PROJECT_ROOT/package.json" ]; then
        log_info "Building Tailwind CSS..."
        npm install --production
        npm run build:css
        log_success "Tailwind CSS built"
    fi

    # Start FastAPI with uvicorn (production settings)
    log_info "Starting FastAPI server (production)..."
    cd "$PROJECT_ROOT/backend"

    poetry run uvicorn app.main:app \
        --host 0.0.0.0 \
        --port 8000 \
        --workers 4 \
        --log-level warning \
        --no-access-log
}

# =============================================================================
# Main execution
# =============================================================================

echo ""
echo "╔═══════════════════════════════════════════════════════════╗"
echo "║       KeePassXC Web Manager - Start Script               ║"
echo "╚═══════════════════════════════════════════════════════════╝"
echo ""

log_info "Environment: $ENVIRONMENT"
log_info "Project root: $PROJECT_ROOT"
echo ""

# Check requirements
check_requirements

# Start services
start_services

echo ""

# Start based on environment
case "$ENVIRONMENT" in
    development|dev)
        start_development
        ;;
    production|prod)
        start_production
        ;;
    staging)
        log_info "Staging mode not yet implemented, using production settings..."
        start_production
        ;;
    *)
        log_error "Unknown environment: $ENVIRONMENT"
        log_info "Valid environments: development, production, staging"
        exit 1
        ;;
esac
