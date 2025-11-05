"""
Pytest configuration and shared fixtures for KeePassXC Web Manager tests.
"""

import asyncio
import os
import tempfile
from pathlib import Path
from typing import AsyncGenerator, Generator
from unittest.mock import MagicMock

import pytest
from fastapi.testclient import TestClient
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

# =============================================================================
# Pytest configuration
# =============================================================================

@pytest.fixture(scope="session")
def event_loop() -> Generator[asyncio.AbstractEventLoop, None, None]:
    """
    Create an event loop for the test session.
    """
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


# =============================================================================
# Environment and configuration fixtures
# =============================================================================

@pytest.fixture(scope="session", autouse=True)
def setup_test_environment() -> None:
    """
    Setup test environment variables.
    """
    os.environ["TESTING"] = "true"
    os.environ["ENVIRONMENT"] = "test"
    os.environ["DEBUG"] = "false"
    os.environ["SECRET_KEY"] = "test-secret-key-for-testing-only-not-secure"
    os.environ["DATABASE_URL"] = "sqlite+aiosqlite:///:memory:"
    os.environ["CACHE_BACKEND"] = "memory"
    os.environ["ALLOW_SENSITIVE_DATA_IN_DB"] = "false"


@pytest.fixture
def temp_dir() -> Generator[Path, None, None]:
    """
    Create a temporary directory for test files.
    """
    with tempfile.TemporaryDirectory() as tmp_dir:
        yield Path(tmp_dir)


@pytest.fixture
def test_kdbx_path(temp_dir: Path) -> Path:
    """
    Create a test KeePassXC database path.
    Note: This is just a path, not an actual database.
    """
    db_path = temp_dir / "test_database.kdbx"
    return db_path


@pytest.fixture
def test_key_path(temp_dir: Path) -> Path:
    """
    Create a test key file path.
    """
    key_path = temp_dir / "test_keyfile.key"
    return key_path


# =============================================================================
# Database fixtures
# =============================================================================

@pytest.fixture
async def async_db_engine():
    """
    Create an async database engine for testing (in-memory SQLite).
    """
    engine = create_async_engine(
        "sqlite+aiosqlite:///:memory:",
        echo=False,
        future=True,
    )

    # Import models and create tables
    # from app.infrastructure.database.models import Base
    # async with engine.begin() as conn:
    #     await conn.run_sync(Base.metadata.create_all)

    yield engine

    await engine.dispose()


@pytest.fixture
async def async_db_session(async_db_engine) -> AsyncGenerator[AsyncSession, None]:
    """
    Create an async database session for testing.
    """
    async_session = sessionmaker(
        async_db_engine,
        class_=AsyncSession,
        expire_on_commit=False,
    )

    async with async_session() as session:
        yield session
        await session.rollback()


# =============================================================================
# Cache fixtures
# =============================================================================

@pytest.fixture
def mock_redis_cache():
    """
    Mock Redis cache for testing.
    """
    mock = MagicMock()
    mock.get = MagicMock(return_value=None)
    mock.set = MagicMock(return_value=True)
    mock.delete = MagicMock(return_value=True)
    mock.clear = MagicMock(return_value=True)
    return mock


@pytest.fixture
def memory_cache():
    """
    Create a simple in-memory cache for testing.
    """
    from app.infrastructure.cache.memory_cache import MemoryCache
    cache = MemoryCache()
    yield cache
    cache.clear()


# =============================================================================
# Security fixtures
# =============================================================================

@pytest.fixture
def mock_security_manager():
    """
    Mock security manager for testing.
    """
    from app.infrastructure.security.sessions import SecurityManager
    manager = SecurityManager(
        secret_key="test-secret-key",
        session_timeout=1800
    )
    return manager


@pytest.fixture
def test_password() -> str:
    """
    Test password for KeePassXC database.
    """
    return "test_password_123"


@pytest.fixture
def test_jwt_token(mock_security_manager, test_kdbx_path: Path, test_password: str) -> str:
    """
    Generate a test JWT token.
    """
    session_data = mock_security_manager.create_session(
        database_path=str(test_kdbx_path),
        password=test_password,
    )
    return session_data["token"]


# =============================================================================
# KeePassXC CLI fixtures
# =============================================================================

@pytest.fixture
def mock_keepassxc_cli():
    """
    Mock KeePassXC CLI wrapper for testing.
    """
    mock = MagicMock()
    mock.check_cli_available = MagicMock(return_value=True)
    mock.test_connection = MagicMock(return_value=True)
    mock.list_entries = MagicMock(return_value=["entry1", "entry2"])
    mock.get_entry_details = MagicMock(return_value={
        "title": "test_entry",
        "username": "test_user",
        "password": "test_pass",
        "url": "https://example.com",
        "notes": "Test notes"
    })
    return mock


# =============================================================================
# FastAPI application fixtures
# =============================================================================

@pytest.fixture
def app():
    """
    Create FastAPI application instance for testing.
    """
    # This will be implemented in Phase 2 when we have the main app
    # from app.main import create_app
    # app = create_app()
    # return app
    pass


@pytest.fixture
def client(app):
    """
    Create synchronous test client.
    """
    if app:
        return TestClient(app)
    return None


@pytest.fixture
async def async_client(app) -> AsyncGenerator[AsyncClient, None]:
    """
    Create asynchronous test client.
    """
    if app:
        async with AsyncClient(app=app, base_url="http://test") as client:
            yield client
    else:
        yield None


# =============================================================================
# Test data fixtures
# =============================================================================

@pytest.fixture
def sample_entry_data() -> dict:
    """
    Sample entry data for testing.
    """
    return {
        "title": "Test Entry",
        "username": "test_user@example.com",
        "password": "SecureP@ssw0rd123",
        "url": "https://example.com",
        "notes": "This is a test note"
    }


@pytest.fixture
def sample_entries_list() -> list:
    """
    Sample list of entries for testing.
    """
    return [
        "Work/GitHub",
        "Work/GitLab",
        "Personal/Email",
        "Personal/Social/Facebook",
        "Banking/MainBank"
    ]


@pytest.fixture
def sample_entry_details() -> dict:
    """
    Sample detailed entry for testing.
    """
    return {
        "name": "GitHub",
        "title": "GitHub",
        "username": "user@example.com",
        "password": "github_password_123",
        "url": "https://github.com",
        "notes": "Work GitHub account",
        "uuid": "1234567890abcdef",
        "tags": ["work", "dev"],
        "group": "Work",
        "created": "2024-01-01 12:00:00",
        "modified": "2024-01-15 14:30:00"
    }


# =============================================================================
# Markers for organizing tests
# =============================================================================

def pytest_configure(config):
    """
    Register custom markers.
    """
    config.addinivalue_line("markers", "unit: Unit tests")
    config.addinivalue_line("markers", "integration: Integration tests")
    config.addinivalue_line("markers", "e2e: End-to-end tests")
    config.addinivalue_line("markers", "security: Security tests")
    config.addinivalue_line("markers", "slow: Slow tests")


# =============================================================================
# Test utilities
# =============================================================================

@pytest.fixture
def assert_no_sensitive_data():
    """
    Utility fixture to assert no sensitive data in a dict.
    """
    def _assert(data: dict) -> None:
        """
        Check that data doesn't contain sensitive fields.
        """
        forbidden_keys = [
            "password",
            "passwd",
            "pwd",
            "secret",
            "token",
            "api_key",
            "private_key",
            "master_password"
        ]

        for key in data.keys():
            assert not any(
                forbidden in key.lower() for forbidden in forbidden_keys
            ), f"Sensitive data field '{key}' found in data!"

    return _assert


# =============================================================================
# Cleanup
# =============================================================================

@pytest.fixture(autouse=True)
def cleanup_after_test():
    """
    Cleanup after each test.
    """
    yield
    # Add any cleanup logic here
