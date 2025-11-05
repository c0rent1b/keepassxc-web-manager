"""
Integration tests for authentication API endpoints.

Tests:
- POST /api/v1/auth/login
- POST /api/v1/auth/logout
- POST /api/v1/auth/refresh
- GET /api/v1/auth/session
"""

import pytest
from httpx import AsyncClient


class TestAuthenticationAPI:
    """Integration tests for authentication endpoints."""

    @pytest.mark.asyncio
    async def test_health_check(self, client: AsyncClient):
        """Test health check endpoint."""
        response = await client.get("/health")

        assert response.status_code == 200
        data = response.json()

        assert "status" in data
        assert "version" in data
        assert "keepassxc_available" in data
        assert "cache_healthy" in data

    @pytest.mark.asyncio
    async def test_ping(self, client: AsyncClient):
        """Test ping endpoint."""
        response = await client.get("/ping")

        assert response.status_code == 200
        data = response.json()

        assert data == {"ping": "pong"}

    @pytest.mark.asyncio
    async def test_login_with_invalid_database_path(self, client: AsyncClient):
        """Test login with non-existent database."""
        response = await client.post(
            "/api/v1/auth/login",
            json={
                "database_path": "/nonexistent/path/database.kdbx",
                "password": "test_password",
            },
        )

        assert response.status_code == 404
        data = response.json()

        assert data["error"] == "database_not_found"
        assert "message" in data
        assert "timestamp" in data

    @pytest.mark.asyncio
    async def test_login_with_invalid_extension(self, client: AsyncClient):
        """Test login with invalid database extension."""
        response = await client.post(
            "/api/v1/auth/login",
            json={
                "database_path": "/path/to/database.txt",
                "password": "test_password",
            },
        )

        assert response.status_code == 422  # Validation error
        data = response.json()

        # Pydantic validation error format
        assert "detail" in data

    @pytest.mark.asyncio
    async def test_login_without_password(self, client: AsyncClient):
        """Test login without password."""
        response = await client.post(
            "/api/v1/auth/login",
            json={
                "database_path": "/path/to/database.kdbx",
            },
        )

        assert response.status_code == 422  # Validation error

    @pytest.mark.asyncio
    @pytest.mark.skipif(
        True,  # Skip by default (requires real database)
        reason="Requires real KeePassXC database",
    )
    async def test_login_success(
        self,
        client: AsyncClient,
        test_database_path,
        test_database_password: str,
    ):
        """Test successful login."""
        response = await client.post(
            "/api/v1/auth/login",
            json={
                "database_path": str(test_database_path),
                "password": test_database_password,
            },
        )

        assert response.status_code == 200
        data = response.json()

        # Check response structure
        assert "token" in data
        assert "session_id" in data
        assert "expires_in" in data
        assert "database_path" in data

        # Validate token format (JWT)
        assert isinstance(data["token"], str)
        assert len(data["token"]) > 0
        assert data["token"].count(".") == 2  # JWT format: header.payload.signature

        # Validate session ID
        assert isinstance(data["session_id"], str)
        assert len(data["session_id"]) > 0

        # Validate expiration
        assert isinstance(data["expires_in"], int)
        assert data["expires_in"] > 0

        # Validate database path
        assert data["database_path"] == str(test_database_path)

    @pytest.mark.asyncio
    async def test_logout_without_authentication(self, client: AsyncClient):
        """Test logout without authentication."""
        response = await client.post("/api/v1/auth/logout")

        assert response.status_code == 401
        data = response.json()

        assert data["error"] in ["authentication_failed", "invalid_token"]
        assert "message" in data

    @pytest.mark.asyncio
    @pytest.mark.skipif(
        True,  # Skip by default
        reason="Requires real KeePassXC database",
    )
    async def test_logout_success(
        self,
        authenticated_client: tuple[AsyncClient, str, dict],
    ):
        """Test successful logout."""
        client, token, session_info = authenticated_client

        response = await client.post("/api/v1/auth/logout")

        assert response.status_code == 200
        data = response.json()

        assert "message" in data
        assert "success" in data["message"].lower()

        # Verify token is invalidated
        response2 = await client.get("/api/v1/databases/info")
        assert response2.status_code == 401

    @pytest.mark.asyncio
    async def test_refresh_token_without_authentication(self, client: AsyncClient):
        """Test token refresh without authentication."""
        response = await client.post("/api/v1/auth/refresh")

        assert response.status_code == 401

    @pytest.mark.asyncio
    @pytest.mark.skipif(
        True,  # Skip by default
        reason="Requires real KeePassXC database",
    )
    async def test_refresh_token_success(
        self,
        authenticated_client: tuple[AsyncClient, str, dict],
    ):
        """Test successful token refresh."""
        client, old_token, session_info = authenticated_client

        response = await client.post("/api/v1/auth/refresh")

        assert response.status_code == 200
        data = response.json()

        # Check response structure
        assert "token" in data
        assert "expires_in" in data

        # Validate new token
        new_token = data["token"]
        assert isinstance(new_token, str)
        assert len(new_token) > 0
        assert new_token != old_token  # Should be different

        # Verify new token works
        client.headers["Authorization"] = f"Bearer {new_token}"
        response2 = await client.get("/api/v1/databases/info")
        assert response2.status_code == 200

    @pytest.mark.asyncio
    async def test_get_session_info_without_authentication(self, client: AsyncClient):
        """Test getting session info without authentication."""
        response = await client.get("/api/v1/auth/session")

        assert response.status_code == 401

    @pytest.mark.asyncio
    @pytest.mark.skipif(
        True,  # Skip by default
        reason="Requires real KeePassXC database",
    )
    async def test_get_session_info_success(
        self,
        authenticated_client: tuple[AsyncClient, str, dict],
    ):
        """Test getting session info."""
        client, token, session_info = authenticated_client

        response = await client.get("/api/v1/auth/session")

        assert response.status_code == 200
        data = response.json()

        # Should NOT contain sensitive data
        from tests.integration.conftest import assert_no_sensitive_data_in_response

        assert_no_sensitive_data_in_response(data)

        # Should contain session metadata
        assert "session_id" in data or "database_path" in data

    @pytest.mark.asyncio
    async def test_login_with_wrong_password(
        self,
        client: AsyncClient,
        test_database_path,
    ):
        """Test login with incorrect password."""
        # Skip if no database
        if not test_database_path.exists():
            pytest.skip("Test database not available")

        response = await client.post(
            "/api/v1/auth/login",
            json={
                "database_path": str(test_database_path),
                "password": "wrong_password_123",
            },
        )

        assert response.status_code == 401
        data = response.json()

        assert data["error"] == "database_authentication_failed"
        assert "message" in data
        assert "password" in data["message"].lower() or "authentication" in data["message"].lower()

    @pytest.mark.asyncio
    async def test_invalid_token_format(self, client: AsyncClient):
        """Test request with invalid token format."""
        # Set invalid token
        client.headers["Authorization"] = "Bearer invalid-token-format"

        response = await client.get("/api/v1/databases/info")

        assert response.status_code == 401
        data = response.json()

        assert "error" in data
        assert data["error"] in ["invalid_token", "session_expired"]

    @pytest.mark.asyncio
    async def test_missing_bearer_prefix(self, client: AsyncClient):
        """Test request without Bearer prefix in Authorization header."""
        # Set token without Bearer prefix
        client.headers["Authorization"] = "some-token"

        response = await client.get("/api/v1/databases/info")

        assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_malformed_authorization_header(self, client: AsyncClient):
        """Test request with malformed Authorization header."""
        # Set malformed header
        client.headers["Authorization"] = "BearerWithoutSpace"

        response = await client.get("/api/v1/databases/info")

        assert response.status_code == 401
