"""
Integration tests for database API endpoints.

Tests:
- POST /api/v1/databases/test
- GET /api/v1/databases/info
"""

import pytest
from httpx import AsyncClient


class TestDatabasesAPI:
    """Integration tests for database endpoints."""

    @pytest.mark.asyncio
    async def test_test_database_without_auth(self, client: AsyncClient):
        """Test that /databases/test doesn't require authentication."""
        # This endpoint should work without authentication
        # (it's for testing credentials before login)
        response = await client.post(
            "/api/v1/databases/test",
            json={
                "database_path": "/nonexistent/database.kdbx",
                "password": "test_password",
            },
        )

        # Should get 404 (database not found) not 401 (unauthorized)
        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_test_database_invalid_path(self, client: AsyncClient):
        """Test database test with invalid path."""
        response = await client.post(
            "/api/v1/databases/test",
            json={
                "database_path": "/nonexistent/database.kdbx",
                "password": "test_password",
            },
        )

        assert response.status_code == 404
        data = response.json()

        assert data["error"] == "database_not_found"
        assert "message" in data

    @pytest.mark.asyncio
    async def test_test_database_invalid_extension(self, client: AsyncClient):
        """Test database test with invalid extension."""
        response = await client.post(
            "/api/v1/databases/test",
            json={
                "database_path": "/path/to/database.txt",
                "password": "test_password",
            },
        )

        assert response.status_code == 422  # Validation error

    @pytest.mark.asyncio
    async def test_test_database_missing_password(self, client: AsyncClient):
        """Test database test without password."""
        response = await client.post(
            "/api/v1/databases/test",
            json={
                "database_path": "/path/to/database.kdbx",
            },
        )

        assert response.status_code == 422  # Validation error

    @pytest.mark.asyncio
    @pytest.mark.skipif(
        True,  # Skip by default
        reason="Requires real KeePassXC database",
    )
    async def test_test_database_success(
        self,
        client: AsyncClient,
        test_database_path,
        test_database_password: str,
    ):
        """Test successful database test."""
        response = await client.post(
            "/api/v1/databases/test",
            json={
                "database_path": str(test_database_path),
                "password": test_database_password,
            },
        )

        assert response.status_code == 200
        data = response.json()

        # Check response structure
        assert "success" in data
        assert "message" in data
        assert data["success"] is True

        # Check database info
        assert "database_info" in data
        db_info = data["database_info"]

        assert "path" in db_info
        assert "filename" in db_info
        assert "file_size" in db_info
        assert "file_size_mb" in db_info
        assert "entry_count" in db_info
        assert "is_locked" in db_info

        # Validate types
        assert isinstance(db_info["path"], str)
        assert isinstance(db_info["file_size"], int)
        assert isinstance(db_info["file_size_mb"], float)
        assert isinstance(db_info["entry_count"], int)
        assert isinstance(db_info["is_locked"], bool)

        # Database should not be locked after successful test
        assert db_info["is_locked"] is False

        # Should NOT contain sensitive data
        from tests.integration.conftest import assert_no_sensitive_data_in_response

        assert_no_sensitive_data_in_response(data)

    @pytest.mark.asyncio
    async def test_test_database_wrong_password(
        self,
        client: AsyncClient,
        test_database_path,
    ):
        """Test database test with wrong password."""
        if not test_database_path.exists():
            pytest.skip("Test database not available")

        response = await client.post(
            "/api/v1/databases/test",
            json={
                "database_path": str(test_database_path),
                "password": "wrong_password",
            },
        )

        assert response.status_code == 401
        data = response.json()

        assert data["error"] == "database_authentication_failed"

    @pytest.mark.asyncio
    async def test_get_database_info_without_auth(self, client: AsyncClient):
        """Test getting database info without authentication."""
        response = await client.get("/api/v1/databases/info")

        assert response.status_code == 401

    @pytest.mark.asyncio
    @pytest.mark.skipif(
        True,  # Skip by default
        reason="Requires real KeePassXC database",
    )
    async def test_get_database_info_success(
        self,
        authenticated_client: tuple[AsyncClient, str, dict],
    ):
        """Test getting current database info."""
        client, token, session_info = authenticated_client

        response = await client.get("/api/v1/databases/info")

        assert response.status_code == 200
        data = response.json()

        # Check response structure
        assert "path" in data
        assert "filename" in data
        assert "file_size" in data
        assert "file_size_mb" in data
        assert "entry_count" in data
        assert "has_keyfile" in data
        assert "is_locked" in data

        # Validate types
        assert isinstance(data["path"], str)
        assert isinstance(data["filename"], str)
        assert isinstance(data["file_size"], int)
        assert isinstance(data["file_size_mb"], float)
        assert isinstance(data["entry_count"], int)
        assert isinstance(data["has_keyfile"], bool)
        assert isinstance(data["is_locked"], bool)

        # Database should not be locked
        assert data["is_locked"] is False

        # Should NOT contain sensitive data
        from tests.integration.conftest import assert_no_sensitive_data_in_response

        assert_no_sensitive_data_in_response(data)

    @pytest.mark.asyncio
    async def test_database_info_with_invalid_token(self, client: AsyncClient):
        """Test database info with invalid token."""
        client.headers["Authorization"] = "Bearer invalid-token"

        response = await client.get("/api/v1/databases/info")

        assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_database_info_with_expired_token(self, client: AsyncClient):
        """Test database info with expired token."""
        # Use a token that's definitely expired (old format)
        expired_token = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiIxMjM0NTY3ODkwIiwiZXhwIjoxNTE2MjM5MDIyfQ.SflKxwRJSMeKKF2QT4fwpMeJf36POk6yJV_adQssw5c"
        client.headers["Authorization"] = f"Bearer {expired_token}"

        response = await client.get("/api/v1/databases/info")

        assert response.status_code == 401
        data = response.json()

        # Should indicate token/session expired
        assert data["error"] in ["invalid_token", "session_expired"]
