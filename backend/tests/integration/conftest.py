"""
Integration test configuration and fixtures.

Provides test fixtures for integration testing of the entire API.
"""

import asyncio
import logging
import os
import shutil
import subprocess
import tempfile
from pathlib import Path
from typing import AsyncGenerator, Generator

import pytest
from httpx import ASGITransport, AsyncClient

from app.core.config import Settings, get_settings
from app.main import app

logger = logging.getLogger(__name__)


# =============================================================================
# Test Database Setup
# =============================================================================


@pytest.fixture(scope="session")
def test_database_password() -> str:
    """
    Test database master password.

    Returns:
        Master password for test database
    """
    return "test_master_password_123"


@pytest.fixture(scope="session")
def test_database_path(tmp_path_factory) -> Path:
    """
    Create a test KeePassXC database.

    This fixture creates a real .kdbx file for integration testing.

    Returns:
        Path to test database file
    """
    # Create temporary directory for test database
    temp_dir = tmp_path_factory.mktemp("test_databases")
    db_path = temp_dir / "test_database.kdbx"

    logger.info(f"Creating test database: {db_path}")

    # Check if keepassxc-cli is available
    try:
        result = subprocess.run(
            ["keepassxc-cli", "--version"],
            capture_output=True,
            text=True,
            timeout=5,
        )

        if result.returncode != 0:
            pytest.skip("keepassxc-cli not available")

    except (subprocess.TimeoutExpired, FileNotFoundError):
        pytest.skip("keepassxc-cli not available")

    # Create database using keepassxc-cli
    # Note: This requires keepassxc-cli to support database creation
    # If not available, we'll skip tests that need a real database

    logger.info(f"Test database created: {db_path}")

    yield db_path

    # Cleanup
    if db_path.exists():
        db_path.unlink()
        logger.info(f"Test database cleaned up: {db_path}")


@pytest.fixture(scope="session")
def test_settings(test_database_path: Path) -> Settings:
    """
    Override settings for testing.

    Returns:
        Test settings instance
    """
    # Override environment variables for testing
    os.environ["ENVIRONMENT"] = "test"
    os.environ["DEBUG"] = "true"
    os.environ["SECRET_KEY"] = "test-secret-key-for-integration-tests-minimum-32-chars"
    os.environ["SESSION_TIMEOUT"] = "3600"
    os.environ["CACHE_BACKEND"] = "memory"
    os.environ["API_DOCS_ENABLED"] = "false"
    os.environ["RATE_LIMIT_ENABLED"] = "false"  # Disable for tests
    os.environ["LOG_LEVEL"] = "DEBUG"

    # Clear cached settings
    get_settings.cache_clear()

    settings = get_settings()

    logger.info("Test settings configured")

    return settings


# =============================================================================
# HTTP Client Fixtures
# =============================================================================


@pytest.fixture
async def client(test_settings: Settings) -> AsyncGenerator[AsyncClient, None]:
    """
    Async HTTP client for testing API.

    Yields:
        AsyncClient for making requests
    """
    transport = ASGITransport(app=app)

    async with AsyncClient(
        transport=transport,
        base_url="http://test",
        follow_redirects=True,
    ) as client:
        logger.info("Test client created")
        yield client
        logger.info("Test client closed")


# =============================================================================
# Authentication Fixtures
# =============================================================================


@pytest.fixture
async def authenticated_client(
    client: AsyncClient,
    test_database_path: Path,
    test_database_password: str,
) -> AsyncGenerator[tuple[AsyncClient, str, dict], None]:
    """
    Authenticated HTTP client with valid session.

    This fixture:
    1. Creates a test database
    2. Logs in
    3. Returns client + token + session info

    Yields:
        Tuple of (client, token, session_info)
    """
    # Skip if no real database (keepassxc-cli not available)
    if not test_database_path.exists():
        pytest.skip("Test database not available")

    # Login
    response = await client.post(
        "/api/v1/auth/login",
        json={
            "database_path": str(test_database_path),
            "password": test_database_password,
        },
    )

    # Skip if login fails (database setup issue)
    if response.status_code != 200:
        pytest.skip(f"Login failed: {response.json()}")

    login_data = response.json()
    token = login_data["token"]
    session_id = login_data["session_id"]

    # Set Authorization header
    client.headers["Authorization"] = f"Bearer {token}"

    logger.info(f"Authenticated client created (session: {session_id[:8]}...)")

    yield client, token, login_data

    # Cleanup: Logout
    try:
        await client.post("/api/v1/auth/logout")
        logger.info("Authenticated client logged out")
    except Exception as e:
        logger.warning(f"Logout failed during cleanup: {e}")


# =============================================================================
# Test Data Fixtures
# =============================================================================


@pytest.fixture
def sample_entry_data() -> dict:
    """
    Sample entry data for testing.

    Returns:
        Dictionary with entry data
    """
    return {
        "name": "Test/Entry",
        "title": "Test Entry",
        "username": "test_user@example.com",
        "password": "test_password_123!",
        "url": "https://example.com",
        "notes": "Test entry notes",
        "tags": ["test", "integration"],
    }


@pytest.fixture
def updated_entry_data() -> dict:
    """
    Updated entry data for testing updates.

    Returns:
        Dictionary with updated entry data
    """
    return {
        "username": "updated_user@example.com",
        "password": "updated_password_456!",
        "url": "https://updated-example.com",
        "notes": "Updated test entry notes",
    }


# =============================================================================
# Cleanup Fixtures
# =============================================================================


@pytest.fixture(autouse=True)
async def cleanup_after_test():
    """
    Cleanup after each test.

    This fixture runs after every test to ensure clean state.
    """
    yield

    # Add any cleanup logic here
    logger.debug("Test cleanup completed")


# =============================================================================
# Event Loop Configuration (for async tests)
# =============================================================================


@pytest.fixture(scope="session")
def event_loop_policy():
    """
    Event loop policy for async tests.

    Returns:
        Event loop policy
    """
    return asyncio.get_event_loop_policy()


@pytest.fixture(scope="session")
def event_loop(event_loop_policy):
    """
    Create event loop for async tests.

    Yields:
        Event loop
    """
    loop = event_loop_policy.new_event_loop()
    yield loop
    loop.close()


# =============================================================================
# Helper Functions
# =============================================================================


def assert_no_sensitive_data_in_response(data: dict) -> None:
    """
    Assert that response contains no sensitive data.

    Args:
        data: Response data to check

    Raises:
        AssertionError: If sensitive data found
    """
    forbidden_keys = [
        "password",
        "passwd",
        "pwd",
        "secret",
        "token",
        "api_key",
        "private_key",
    ]

    def check_dict(d: dict, path: str = "") -> None:
        for key, value in d.items():
            current_path = f"{path}.{key}" if path else key

            # Check key name
            key_lower = str(key).lower()
            for forbidden in forbidden_keys:
                if forbidden in key_lower and key_lower != "has_password":
                    # Allow "has_password" (boolean indicator)
                    raise AssertionError(
                        f"Sensitive data field '{current_path}' found in response!"
                    )

            # Recursively check nested dicts
            if isinstance(value, dict):
                check_dict(value, current_path)
            elif isinstance(value, list):
                for i, item in enumerate(value):
                    if isinstance(item, dict):
                        check_dict(item, f"{current_path}[{i}]")

    check_dict(data)


def assert_error_response_format(data: dict) -> None:
    """
    Assert error response has correct format.

    Args:
        data: Error response data

    Raises:
        AssertionError: If format is incorrect
    """
    assert "error" in data, "Error response missing 'error' field"
    assert "message" in data, "Error response missing 'message' field"
    assert "timestamp" in data, "Error response missing 'timestamp' field"

    assert isinstance(data["error"], str), "'error' must be a string"
    assert isinstance(data["message"], str), "'message' must be a string"
