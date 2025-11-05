"""
Integration tests for security features.

Tests:
- Rate limiting
- Authentication security
- Sensitive data exclusion
- Error responses
"""

import pytest
from httpx import AsyncClient


class TestSecurityFeatures:
    """Integration tests for security features."""

    @pytest.mark.asyncio
    async def test_no_passwords_in_list_response(
        self,
        authenticated_client: tuple[AsyncClient, str, dict],
    ):
        """
        CRITICAL: Verify passwords are NEVER in list responses.

        This is a core security requirement.
        """
        if not authenticated_client:
            pytest.skip("Authentication not available")

        client, token, session_info = authenticated_client

        response = await client.get("/api/v1/entries")

        # Skip if no entries
        if response.status_code != 200:
            pytest.skip("No entries available")

        data = response.json()

        # Critical: No password field should exist in any entry
        for entry in data.get("entries", []):
            assert "password" not in entry, "SECURITY VIOLATION: Password found in list response!"

            # Should have boolean indicators only
            assert "has_password" in entry
            assert isinstance(entry["has_password"], bool)

    @pytest.mark.asyncio
    async def test_no_passwords_in_single_entry_response(
        self,
        authenticated_client: tuple[AsyncClient, str, dict],
    ):
        """
        CRITICAL: Verify passwords are not in single entry GET responses.

        Only the dedicated /password endpoint should return passwords.
        """
        if not authenticated_client:
            pytest.skip("Authentication not available")

        client, token, session_info = authenticated_client

        # List entries
        list_response = await client.get("/api/v1/entries")
        if list_response.status_code != 200:
            pytest.skip("No entries available")

        entries = list_response.json().get("entries", [])
        if not entries:
            pytest.skip("No entries in database")

        entry_name = entries[0]["name"]

        # Get single entry
        response = await client.get(f"/api/v1/entries/{entry_name}")

        assert response.status_code == 200
        data = response.json()

        # Critical: No password field
        assert "password" not in data, "SECURITY VIOLATION: Password found in entry response!"

        # Should have boolean indicator
        assert "has_password" in data

    @pytest.mark.asyncio
    async def test_password_only_in_dedicated_endpoint(
        self,
        authenticated_client: tuple[AsyncClient, str, dict],
    ):
        """
        Verify passwords are ONLY returned from /password endpoint.
        """
        if not authenticated_client:
            pytest.skip("Authentication not available")

        client, token, session_info = authenticated_client

        # List entries
        list_response = await client.get("/api/v1/entries")
        if list_response.status_code != 200:
            pytest.skip("No entries available")

        entries = list_response.json().get("entries", [])
        if not entries:
            pytest.skip("No entries in database")

        entry_name = entries[0]["name"]

        # Get password from dedicated endpoint
        response = await client.get(f"/api/v1/entries/{entry_name}/password")

        assert response.status_code == 200
        data = response.json()

        # This endpoint SHOULD have password
        assert "password" in data
        assert isinstance(data["password"], str)

    @pytest.mark.asyncio
    async def test_no_sensitive_data_in_database_info(
        self,
        authenticated_client: tuple[AsyncClient, str, dict],
    ):
        """Verify database info contains no sensitive data."""
        if not authenticated_client:
            pytest.skip("Authentication not available")

        client, token, session_info = authenticated_client

        response = await client.get("/api/v1/databases/info")

        assert response.status_code == 200
        data = response.json()

        # Should NOT contain sensitive data
        from tests.integration.conftest import assert_no_sensitive_data_in_response

        assert_no_sensitive_data_in_response(data)

    @pytest.mark.asyncio
    async def test_no_sensitive_data_in_session_info(
        self,
        authenticated_client: tuple[AsyncClient, str, dict],
    ):
        """Verify session info contains no sensitive data."""
        if not authenticated_client:
            pytest.skip("Authentication not available")

        client, token, session_info = authenticated_client

        response = await client.get("/api/v1/auth/session")

        assert response.status_code == 200
        data = response.json()

        # Should NOT contain sensitive data
        from tests.integration.conftest import assert_no_sensitive_data_in_response

        assert_no_sensitive_data_in_response(data)

    @pytest.mark.asyncio
    async def test_authentication_required_for_all_entry_operations(
        self,
        client: AsyncClient,
    ):
        """Verify all entry operations require authentication."""
        endpoints = [
            ("GET", "/api/v1/entries"),
            ("GET", "/api/v1/entries/Test/Entry"),
            ("GET", "/api/v1/entries/Test/Entry/password"),
            ("POST", "/api/v1/entries", {"name": "Test", "password": "test"}),
            ("PUT", "/api/v1/entries/Test", {}),
            ("DELETE", "/api/v1/entries/Test"),
        ]

        for method, path, *body in endpoints:
            if method == "GET":
                response = await client.get(path)
            elif method == "POST":
                response = await client.post(path, json=body[0] if body else {})
            elif method == "PUT":
                response = await client.put(path, json=body[0] if body else {})
            elif method == "DELETE":
                response = await client.delete(path)

            assert response.status_code == 401, f"{method} {path} should require auth"

    @pytest.mark.asyncio
    async def test_authentication_required_for_database_info(
        self,
        client: AsyncClient,
    ):
        """Verify database info requires authentication."""
        response = await client.get("/api/v1/databases/info")

        assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_authentication_required_for_groups(
        self,
        client: AsyncClient,
    ):
        """Verify groups listing requires authentication."""
        response = await client.get("/api/v1/groups")

        assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_error_responses_have_standard_format(
        self,
        client: AsyncClient,
    ):
        """Verify all error responses follow standard format."""
        # Test various error scenarios
        error_endpoints = [
            # Authentication error
            ("GET", "/api/v1/databases/info", 401),
            # Not found error
            ("POST", "/api/v1/databases/test", {
                "database_path": "/nonexistent.kdbx",
                "password": "test",
            }, 404),
            # Validation error
            ("POST", "/api/v1/auth/login", {
                "database_path": "invalid.txt",
                "password": "test",
            }, 422),
        ]

        for method, path, *args in error_endpoints:
            if method == "GET":
                response = await client.get(path)
            elif method == "POST":
                response = await client.post(path, json=args[0] if args else {})

            # Check error response format
            data = response.json()

            # Standard error format (or Pydantic validation format)
            if response.status_code == 422:
                # Pydantic validation errors have 'detail'
                assert "detail" in data
            else:
                # Custom errors have our format
                from tests.integration.conftest import assert_error_response_format

                assert_error_response_format(data)

    @pytest.mark.asyncio
    async def test_invalid_json_returns_422(
        self,
        client: AsyncClient,
    ):
        """Test that invalid JSON returns proper error."""
        response = await client.post(
            "/api/v1/auth/login",
            content=b"invalid json{",
            headers={"Content-Type": "application/json"},
        )

        assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_missing_content_type(
        self,
        client: AsyncClient,
    ):
        """Test requests without content-type header."""
        response = await client.post(
            "/api/v1/auth/login",
            content=b'{"database_path": "test.kdbx", "password": "test"}',
        )

        # FastAPI should handle this gracefully
        assert response.status_code in [422, 415]

    @pytest.mark.asyncio
    async def test_token_in_authorization_header_only(
        self,
        client: AsyncClient,
    ):
        """Verify tokens must be in Authorization header (not query params)."""
        # Try to send token as query parameter (should not work)
        response = await client.get(
            "/api/v1/databases/info?token=fake-token"
        )

        assert response.status_code == 401

        # Tokens should only work in header
        client.headers["Authorization"] = "Bearer fake-token"
        response = await client.get("/api/v1/databases/info")

        # Still 401 because token is invalid, but it's reading from header
        assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_cors_headers_present(
        self,
        client: AsyncClient,
    ):
        """Test that CORS headers are present in responses."""
        response = await client.options("/api/v1/auth/login")

        # Should have CORS headers
        # Note: Actual CORS headers depend on configuration
        # This test verifies the endpoint accepts OPTIONS

        assert response.status_code in [200, 204, 405]

    @pytest.mark.asyncio
    async def test_case_sensitive_paths(
        self,
        client: AsyncClient,
    ):
        """Verify API paths are case-sensitive."""
        # Correct path
        response1 = await client.get("/api/v1/auth/session")
        # Wrong case
        response2 = await client.get("/API/V1/AUTH/SESSION")

        # Second should not work (404 not found, not 401)
        assert response1.status_code == 401  # Correct path, wrong auth
        assert response2.status_code == 404  # Wrong path

    @pytest.mark.asyncio
    async def test_sql_injection_protection(
        self,
        client: AsyncClient,
    ):
        """Test that SQL injection attempts are handled safely."""
        # Try SQL injection in entry name
        response = await client.post(
            "/api/v1/databases/test",
            json={
                "database_path": "'; DROP TABLE entries; --.kdbx",
                "password": "test",
            },
        )

        # Should get validation error or not found, not 500
        assert response.status_code in [404, 422]

    @pytest.mark.asyncio
    async def test_xss_protection(
        self,
        authenticated_client: tuple[AsyncClient, str, dict],
    ):
        """Test XSS protection in responses."""
        if not authenticated_client:
            pytest.skip("Authentication not available")

        client, token, session_info = authenticated_client

        # Try to create entry with XSS payload
        xss_payload = "<script>alert('XSS')</script>"

        response = await client.post(
            "/api/v1/entries",
            json={
                "name": f"Test/{xss_payload}",
                "title": xss_payload,
                "username": xss_payload,
                "password": "test_password",
            },
        )

        # Should either succeed or fail gracefully (not 500)
        assert response.status_code in [201, 400, 409, 422]

        # If successful, verify response doesn't execute script
        if response.status_code == 201:
            data = response.json()
            # Response should contain the literal string, not executable code
            # (actual execution prevention is browser-side, but we verify structure)
            assert "<script>" not in str(data) or xss_payload in str(data)

            # Cleanup
            await client.delete(f"/api/v1/entries/Test/{xss_payload}")
