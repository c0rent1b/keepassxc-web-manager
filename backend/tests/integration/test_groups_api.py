"""
Integration tests for group API endpoints.

Tests:
- GET /api/v1/groups (list all)
"""

import pytest
from httpx import AsyncClient


class TestGroupsAPI:
    """Integration tests for group endpoints."""

    @pytest.mark.asyncio
    async def test_list_groups_without_auth(self, client: AsyncClient):
        """Test listing groups without authentication."""
        response = await client.get("/api/v1/groups")

        assert response.status_code == 401

    @pytest.mark.asyncio
    @pytest.mark.skipif(
        True,  # Skip by default
        reason="Requires real KeePassXC database",
    )
    async def test_list_groups_success(
        self,
        authenticated_client: tuple[AsyncClient, str, dict],
    ):
        """Test listing all groups."""
        client, token, session_info = authenticated_client

        response = await client.get("/api/v1/groups")

        assert response.status_code == 200
        data = response.json()

        # Check response structure
        assert "groups" in data
        assert "total" in data

        # Validate types
        assert isinstance(data["groups"], list)
        assert isinstance(data["total"], int)
        assert data["total"] == len(data["groups"])

        # If there are groups, validate structure
        if data["groups"]:
            group = data["groups"][0]

            # Required fields
            assert "name" in group
            assert "path" in group
            assert "entry_count" in group
            assert "subgroups" in group
            assert "depth" in group
            assert "is_root" in group

            # Validate types
            assert isinstance(group["name"], str)
            assert isinstance(group["path"], str)
            assert isinstance(group["entry_count"], int)
            assert isinstance(group["subgroups"], list)
            assert isinstance(group["depth"], int)
            assert isinstance(group["is_root"], bool)

            # Validate depth
            assert group["depth"] >= 0

        # Should NOT contain sensitive data
        from tests.integration.conftest import assert_no_sensitive_data_in_response

        assert_no_sensitive_data_in_response(data)

    @pytest.mark.asyncio
    @pytest.mark.skipif(
        True,  # Skip by default
        reason="Requires real KeePassXC database",
    )
    async def test_groups_hierarchy(
        self,
        authenticated_client: tuple[AsyncClient, str, dict],
    ):
        """Test that groups have correct hierarchy."""
        client, token, session_info = authenticated_client

        response = await client.get("/api/v1/groups")
        assert response.status_code == 200

        data = response.json()
        groups = data["groups"]

        if not groups:
            pytest.skip("No groups in test database")

        # Validate hierarchy consistency
        for group in groups:
            # If group has parent, parent must exist
            if group.get("parent"):
                parent_paths = [g["path"] for g in groups]
                assert group["parent"] in parent_paths, f"Parent '{group['parent']}' not found"

            # Root groups have depth 0
            if group["is_root"]:
                assert group["depth"] == 0

            # Non-root groups should have depth > 0
            if not group["is_root"]:
                assert group["depth"] > 0

    @pytest.mark.asyncio
    async def test_groups_with_invalid_token(self, client: AsyncClient):
        """Test groups list with invalid token."""
        client.headers["Authorization"] = "Bearer invalid-token"

        response = await client.get("/api/v1/groups")

        assert response.status_code == 401
