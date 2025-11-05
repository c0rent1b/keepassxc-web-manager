# 🔐 KeePassXC Web Manager v2.0

> Modern web interface to manage KeePassXC databases with Alpine.js + Tailwind CSS

[![Python](https://img.shields.io/badge/Python-3.12+-blue.svg)](https://www.python.org/downloads/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.110+-green.svg)](https://fastapi.tiangolo.com/)
[![License](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Code style: Ruff](https://img.shields.io/badge/code%20style-ruff-000000.svg)](https://github.com/astral-sh/ruff)

---

## 📋 Table of Contents

- [Overview](#overview)
- [Features](#features)
- [Architecture](#architecture)
- [Prerequisites](#prerequisites)
- [Installation](#installation)
- [Configuration](#configuration)
- [Usage](#usage)
- [Development](#development)
- [Testing](#testing)
- [Security](#security)
- [Project Structure](#project-structure)
- [Contributing](#contributing)
- [License](#license)

---

## 🎯 Overview

KeePassXC Web Manager is a **modern web interface** for managing KeePassXC password databases. Built with **FastAPI** backend and **Alpine.js + Tailwind CSS** frontend, it provides a secure, fast, and beautiful interface for your passwords.

### Why v2.0?

This is a complete rewrite from v1.0 with:
- ✅ **Support for KeePassXC 2.7.10** (latest features)
- ✅ **Notes support** (missing in v1.0)
- ✅ **Tags management**
- ✅ **Advanced search** (CLI `search` command)
- ✅ **Clean Architecture** (maintainable, testable)
- ✅ **SQLite for audit logs** (non-sensitive metadata only)
- ✅ **Redis caching** (performance)
- ✅ **Modern UI** (Alpine.js + Tailwind)
- ✅ **Comprehensive tests** (80%+ coverage)

---

## ✨ Features

### Core Functionality

- 🔑 **Password Management**
  - Create, read, update, delete entries
  - Support for notes (new in 2.7.0!)
  - Password generation with customizable rules
  - Copy passwords to clipboard (secure)
  - Reveal passwords with confirmation

- 🏷️ **Organization**
  - Groups/folders navigation
  - Tags support (filter and search)
  - Favorites and recent entries
  - Multi-database management

- 🔍 **Search**
  - Advanced search using KeePassXC CLI `search`
  - Filter by title, username, URL, notes, tags
  - Search within groups
  - Regex support (optional)

- 📊 **Security Analysis**
  - Password strength scoring
  - Weak password detection
  - Duplicate password detection
  - Password age tracking
  - Security dashboard

- 📥 **Export**
  - HTML export (new in 2.7.10)
  - JSON export (for backup)
  - CSV export (for migration)
  - CLI templates (network devices)

### Technical Features

- 🔒 **Security**
  - JWT authentication
  - Session management with timeout
  - Fernet encryption for passwords in memory
  - Rate limiting
  - Audit logging (who did what, when)
  - **ZERO sensitive data in SQLite** (strict validation)

- ⚡ **Performance**
  - Redis caching with intelligent invalidation
  - Async/await throughout
  - Pagination for large databases
  - Lazy loading

- 🎨 **User Experience**
  - Modern, responsive design
  - Dark/light mode
  - Real-time updates
  - Loading states and animations
  - Keyboard shortcuts
  - Mobile-friendly

---

## 🏗️ Architecture

**Clean Architecture (Hexagonal)** with clear separation of concerns:

```
┌─────────────────────────────────────┐
│   Presentation Layer (API, UI)     │
├─────────────────────────────────────┤
│   Application Layer (Services)     │
├─────────────────────────────────────┤
│   Domain Layer (Entities)          │
├─────────────────────────────────────┤
│   Infrastructure (KeePassXC, DB)   │
└─────────────────────────────────────┘
```

**Tech Stack:**

| Layer | Technology |
|-------|-----------|
| **Frontend** | Alpine.js 3.x + Tailwind CSS 3.x |
| **Backend** | FastAPI 0.110+ + Pydantic v2 |
| **Cache** | Redis 7+ (with memory fallback) |
| **Database** | SQLite (metadata only - no passwords!) |
| **Testing** | Pytest 8.x (80%+ coverage) |
| **Linting** | Ruff + MyPy |
| **Security** | JWT + Fernet + Rate limiting |

See [ARCHITECTURE.md](ARCHITECTURE.md) for detailed architecture documentation.

---

## 📦 Prerequisites

### Required

- **Python 3.12+** ([Download](https://www.python.org/downloads/))
- **KeePassXC 2.7.10+** with CLI ([Download](https://keepassxc.org/download/))
- **Poetry** for dependency management ([Install](https://python-poetry.org/docs/#installation))

### Optional

- **Docker** for Redis (recommended) ([Install](https://docs.docker.com/get-docker/))
- **Node.js** for Tailwind CSS compilation ([Install](https://nodejs.org/))

### Verification

```bash
# Check Python version
python3 --version  # Should be 3.12+

# Check KeePassXC CLI
keepassxc-cli --version  # Should be 2.7.10+

# Check Poetry
poetry --version

# Check Docker (optional)
docker --version
```

---

## 🚀 Installation

### 1. Clone the repository

```bash
git clone https://github.com/c0rent1b/keepassxc-web-manager.git
cd keepassxc-web-manager
```

### 2. Install Poetry

```bash
# Install Poetry if not already installed
curl -sSL https://install.python-poetry.org | python3 -
```

### 3. Install dependencies

```bash
# Install Python dependencies
poetry install

# Install Node.js dependencies (for Tailwind CSS)
npm install
```

### 4. Setup environment

```bash
# Copy example environment file
cp .env.example .env

# Edit .env and configure your settings
nano .env  # or vim, code, etc.
```

**Important:** Change the `SECRET_KEY` in `.env` to a strong random value:

```bash
# Generate a secure secret key
openssl rand -hex 32
```

### 5. Start Redis

```bash
# Option A: Using Docker Compose (recommended)
docker-compose up -d redis

# Option B: Install Redis locally
# Ubuntu/Debian:
sudo apt-get install redis-server
sudo systemctl start redis

# macOS:
brew install redis
brew services start redis
```

### 6. Build frontend

```bash
# Build Tailwind CSS
npm run build:css
```

### 7. Start the application

```bash
# Development mode (with hot reload)
./scripts/start.sh development

# Or manually:
poetry run uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

### 8. Access the application

Open your browser and go to:
```
http://localhost:8000
```

---

## ⚙️ Configuration

### Environment Variables

Key configuration variables in `.env`:

```bash
# Security (REQUIRED - change in production!)
SECRET_KEY="your-super-secret-key-min-32-chars"

# Server
HOST="127.0.0.1"
PORT=8000
ENVIRONMENT="development"  # development, production

# Database (SQLite for metadata)
DATABASE_URL="sqlite+aiosqlite:///./data/keepass_metadata.db"

# Cache (Redis)
CACHE_BACKEND="redis"  # or "memory"
REDIS_URL="redis://localhost:6379/0"

# Session
SESSION_TIMEOUT=1800  # 30 minutes

# Rate Limiting
RATE_LIMIT_PER_MINUTE=60
RATE_LIMIT_LOGIN_ATTEMPTS=5
```

See `.env.example` for all available options.

### Security Checklist (Production)

- [ ] Change `SECRET_KEY` to a strong random value
- [ ] Set `DEBUG=false`
- [ ] Set `ENVIRONMENT=production`
- [ ] Configure proper `ALLOWED_ORIGINS`
- [ ] Enable HTTPS/TLS
- [ ] Setup Redis password
- [ ] Configure log rotation
- [ ] Enable monitoring (Sentry, metrics)
- [ ] Review rate limiting settings

---

## 📖 Usage

### Quick Start

1. **Login**
   - Go to `http://localhost:8000`
   - Enter path to your `.kdbx` file
   - Enter master password
   - Optionally provide key file

2. **Manage Entries**
   - View all entries in the dashboard
   - Click "New Entry" to create
   - Click on entry to view details
   - Use search bar for quick lookup

3. **Advanced Features**
   - Add tags to organize entries
   - Use advanced search with filters
   - Generate secure passwords
   - Export data in various formats
   - View security analysis

### CLI Usage

```bash
# Start in development mode
./scripts/start.sh development

# Start in production mode
./scripts/start.sh production

# Run tests
./scripts/test.sh --all

# Run specific test types
./scripts/test.sh --unit
./scripts/test.sh --integration
./scripts/test.sh --security

# Run with coverage
./scripts/test.sh --coverage

# Lint code
./scripts/lint.sh --check  # Check only
./scripts/lint.sh --fix    # Fix issues
```

---

## 🛠️ Development

### Setup Development Environment

```bash
# Install all dependencies including dev tools
poetry install

# Install pre-commit hooks
poetry run pre-commit install

# Start Tailwind CSS watcher
npm run dev
```

### Development Workflow

1. **Create a branch**
   ```bash
   git checkout -b feature/my-feature
   ```

2. **Make changes**
   - Code in `backend/app/` or `frontend/`
   - Write tests in `backend/tests/`

3. **Test changes**
   ```bash
   # Run tests
   ./scripts/test.sh --unit

   # Check linting
   ./scripts/lint.sh --check

   # Run pre-commit hooks manually
   poetry run pre-commit run --all-files
   ```

4. **Commit and push**
   ```bash
   git add .
   git commit -m "Add my feature"
   git push origin feature/my-feature
   ```

### Code Quality

**Linting:**
```bash
# Check code quality
./scripts/lint.sh --check

# Auto-fix issues
./scripts/lint.sh --fix

# Individual tools
poetry run ruff check backend/app
poetry run mypy backend/app
```

**Testing:**
```bash
# All tests
./scripts/test.sh --all

# Specific types
./scripts/test.sh --unit        # Unit tests
./scripts/test.sh --integration # Integration tests
./scripts/test.sh --e2e         # End-to-end tests
./scripts/test.sh --security    # Security tests

# With coverage
./scripts/test.sh --coverage
```

**Pre-commit hooks:**

Pre-commit hooks run automatically on `git commit`:
- Trailing whitespace removal
- File size checks
- Secret detection
- Ruff (linting + formatting)
- MyPy (type checking)
- Bandit (security scanning)

---

## 🧪 Testing

### Test Structure

```
backend/tests/
├── unit/               # Unit tests (80%+ coverage target)
│   ├── core/
│   │   └── services/
│   └── infrastructure/
├── integration/        # Integration tests
├── e2e/                # End-to-end tests
└── security/           # Security tests
```

### Running Tests

```bash
# All tests
poetry run pytest

# Specific marker
poetry run pytest -m unit
poetry run pytest -m integration
poetry run pytest -m security

# With coverage
poetry run pytest --cov=backend/app --cov-report=html

# Watch mode
poetry run pytest -f

# Fast mode (skip slow tests)
poetry run pytest -m "not slow"
```

### Writing Tests

Tests use pytest with async support:

```python
import pytest

@pytest.mark.unit
async def test_my_feature(async_client):
    """Test my awesome feature."""
    response = await async_client.get("/api/v1/entries")
    assert response.status_code == 200
```

See `backend/tests/conftest.py` for available fixtures.

---

## 🔒 Security

### Security Principles

1. **NEVER store sensitive data in SQLite**
   - ❌ No passwords, secrets, tokens
   - ✅ Only non-sensitive metadata (audit logs, stats)
   - All sensitive data stays in encrypted `.kdbx` files

2. **Defense in depth**
   - JWT authentication
   - Session timeouts
   - Rate limiting
   - Input validation
   - Audit logging

3. **Least privilege**
   - Minimal permissions
   - No unnecessary file access
   - Sandboxed execution

### Security Features

- **Authentication:** JWT tokens with expiration
- **Encryption:** Fernet (AES) for passwords in memory
- **Sessions:** Automatic timeout and cleanup
- **Rate Limiting:** Protection against brute force
- **Audit Logging:** Who did what, when (stored in SQLite)
- **Input Validation:** Pydantic schemas + sanitization
- **Secret Detection:** Pre-commit hooks scan for secrets

### Reporting Security Issues

Please report security vulnerabilities to: [your.email@example.com]

Do NOT create public GitHub issues for security vulnerabilities.

---

## 📁 Project Structure

```
keepassxc-web-manager/
├── backend/
│   ├── app/
│   │   ├── api/                   # API endpoints
│   │   ├── core/                  # Business logic
│   │   ├── infrastructure/        # External services
│   │   └── schemas/               # Data validation
│   └── tests/                     # All tests
├── frontend/
│   ├── src/                       # Source files
│   │   ├── js/                    # Alpine.js code
│   │   └── css/                   # Tailwind CSS
│   ├── templates/                 # Jinja2 templates
│   └── public/                    # Static files
├── docs/                          # Documentation
├── scripts/                       # Utility scripts
├── docker/                        # Docker files
├── .env.example                   # Environment template
├── pyproject.toml                 # Poetry config
├── docker-compose.yml             # Docker Compose
└── README.md                      # This file
```

See [ARCHITECTURE.md](ARCHITECTURE.md) for detailed structure.

---

## 📚 Documentation

- [ARCHITECTURE.md](ARCHITECTURE.md) - Complete architecture documentation
- [DECISIONS.md](DECISIONS.md) - Architectural decision records (ADR)
- [KICKOFF.md](KICKOFF.md) - Project kickoff and planning
- [API Documentation](http://localhost:8000/docs) - Interactive OpenAPI docs (when running)

---

## 🤝 Contributing

Contributions are welcome! Please follow these guidelines:

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Make your changes
4. Write or update tests
5. Run tests and linting
6. Commit your changes (`git commit -m 'Add amazing feature'`)
7. Push to the branch (`git push origin feature/amazing-feature`)
8. Open a Pull Request

### Code Standards

- Follow PEP 8 (enforced by Ruff)
- Write type hints (checked by MyPy)
- Add docstrings to functions
- Write tests for new features
- Keep coverage above 80%

---

## 📋 Roadmap

### Current Version: 2.0.0-alpha

### Upcoming Features

- [ ] TOTP/2FA code display
- [ ] File attachments support
- [ ] Entry history visualization
- [ ] Have I Been Pwned integration
- [ ] PWA support (offline mode)
- [ ] Multi-language support (i18n)
- [ ] Import from other password managers
- [ ] Automated database backups

See [ARCHITECTURE.md](ARCHITECTURE.md) for the complete development plan.

---

## 🐛 Troubleshooting

### Common Issues

**1. "keepassxc-cli not found"**
```bash
# Install KeePassXC
# Ubuntu/Debian:
sudo apt-get install keepassxc

# macOS:
brew install keepassxc

# Verify installation
keepassxc-cli --version
```

**2. "Redis connection failed"**
```bash
# Start Redis with Docker
docker-compose up -d redis

# Or use memory cache (in .env):
CACHE_BACKEND=memory
```

**3. "Poetry not found"**
```bash
# Install Poetry
curl -sSL https://install.python-poetry.org | python3 -

# Add to PATH (add to ~/.bashrc or ~/.zshrc)
export PATH="$HOME/.local/bin:$PATH"
```

**4. "Tests failing"**
```bash
# Ensure Redis is running for integration tests
docker-compose up -d redis

# Or run only unit tests
./scripts/test.sh --unit
```

---

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

---

## 🙏 Acknowledgments

- [KeePassXC](https://keepassxc.org/) - Excellent password manager
- [FastAPI](https://fastapi.tiangolo.com/) - Modern web framework
- [Alpine.js](https://alpinejs.dev/) - Lightweight JavaScript framework
- [Tailwind CSS](https://tailwindcss.com/) - Utility-first CSS framework

---

## 📞 Support

- **Issues:** [GitHub Issues](https://github.com/c0rent1b/keepassxc-web-manager/issues)
- **Discussions:** [GitHub Discussions](https://github.com/c0rent1b/keepassxc-web-manager/discussions)
- **Documentation:** [docs/](docs/)

---

**Made with ❤️ for secure password management**

---

## 🚀 Quick Commands Reference

| Command | Description |
|---------|-------------|
| `./scripts/start.sh development` | Start dev server |
| `./scripts/start.sh production` | Start prod server |
| `./scripts/test.sh --all` | Run all tests |
| `./scripts/test.sh --coverage` | Run with coverage |
| `./scripts/lint.sh --fix` | Lint and fix code |
| `poetry install` | Install dependencies |
| `npm run dev` | Watch Tailwind CSS |
| `docker-compose up -d` | Start all services |
| `poetry shell` | Activate virtual env |

---

**Version:** 2.0.0-alpha
**Last Updated:** 2025-11-05
**Status:** Development (Phase 0 complete)
