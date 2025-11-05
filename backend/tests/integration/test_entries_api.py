"""
Integration tests for entry API endpoints.

Tests:
- GET /api/v1/entries (list all)
- GET /api/v1/entries?search=term (search)
- GET /api/v1/entries/{entry_name} (get one)
- GET /api/v1/entries/{entry_name}/password (get password)
- POST /api/v1/entries (create)
- PUT /api/v1/entries/{entry_name} (update)
- DELETE /api/v1/entries/{entry_name} (delete)
"""

import pytest
from httpx import AsyncClient


class TestEntriesAPI:
    """Integration tests for entry endpoints."""

    @pytest.mark.asyncio
    async def test_list_entries_without_auth(self, client: AsyncClient):
        """Test listing entries without authentication."""
        response = await client.get("/api/v1/entries")

        assert response.status_code == 401

    @pytest.mark.asyncio
    @pytest.mark.skipif(
        True,  # Skip by default
        reason="Requires real KeePassXC database",
    )
    async def test_list_entries_success(
        self,
        authenticated_client: tuple[AsyncClient, str, dict],
    ):
        """Test listing all entries."""
        client, token, session_info = authenticated_client

        response = await client.get("/api/v1/entries")

        assert response.status_code == 200
        data = response.json()

        # Check response structure
        assert "entries" in data
        assert "total" in data

        # Validate types
        assert isinstance(data["entries"], list)
        assert isinstance(data["total"], int)
        assert data["total"] == len(data["entries"])

        # If there are entries, validate structure
        if data["entries"]:
            entry = data["entries"][0]

            # Required fields
            assert "name" in entry
            assert "title" in entry
            assert "username" in entry
            assert "has_password" in entry  # Boolean, not actual password
            assert "password_length" in entry  # Length, not actual password

            # Should NOT have actual password
            assert "password" not in entry

            # Validate types
            assert isinstance(entry["has_password"], bool)
            assert isinstance(entry["password_length"], int)

        # Should NOT contain sensitive data in any entry
        from tests.integration.conftest import assert_no_sensitive_data_in_response

        assert_no_sensitive_data_in_response(data)

    @pytest.mark.asyncio
    @pytest.mark.skipif(
        True,  # Skip by default
        reason="Requires real KeePassXC database",
    )
    async def test_search_entries(
        self,
        authenticated_client: tuple[AsyncClient, str, dict],
    ):
        """Test searching entries."""
        client, token, session_info = authenticated_client

        response = await client.get("/api/v1/entries?search=test")

        assert response.status_code == 200
        data = response.json()

        assert "entries" in data
        assert "total" in data

        # Search results should NOT contain passwords
        from tests.integration.conftest import assert_no_sensitive_data_in_response

        assert_no_sensitive_data_in_response(data)

    @pytest.mark.asyncio
    async def test_get_entry_without_auth(self, client: AsyncClient):
        """Test getting entry without authentication."""
        response = await client.get("/api/v1/entries/Test/Entry")

        assert response.status_code == 401

    @pytest.mark.asyncio
    @pytest.mark.skipif(
        True,  # Skip by default
        reason="Requires real KeePassXC database with entries",
    )
    async def test_get_entry_success(
        self,
        authenticated_client: tuple[AsyncClient, str, dict],
    ):
        """Test getting a specific entry."""
        client, token, session_info = authenticated_client

        # First, list entries to get an entry name
        list_response = await client.get("/api/v1/entries")
        assert list_response.status_code == 200

        entries = list_response.json()["entries"]
        if not entries:
            pytest.skip("No entries in test database")

        entry_name = entries[0]["name"]

        # Get specific entry
        response = await client.get(f"/api/v1/entries/{entry_name}")

        assert response.status_code == 200
        data = response.json()

        # Check structure
        assert "name" in data
        assert "title" in data
        assert "username" in data
        assert "has_password" in data

        # Should NOT have actual password
        assert "password" not in data

        # Validate boolean
        assert isinstance(data["has_password"], bool)

        # Should NOT contain sensitive data
        from tests.integration.conftest import assert_no_sensitive_data_in_response

        assert_no_sensitive_data_in_response(data)

    @pytest.mark.asyncio
    @pytest.mark.skipif(
        True,  # Skip by default
        reason="Requires real KeePassXC database",
    )
    async def test_get_entry_not_found(
        self,
        authenticated_client: tuple[AsyncClient, str, dict],
    ):
        """Test getting non-existent entry."""
        client, token, session_info = authenticated_client

        response = await client.get("/api/v1/entries/Nonexistent/Entry")

        assert response.status_code == 404
        data = response.json()

        assert data["error"] == "entry_not_found"

    @pytest.mark.asyncio
    async def test_get_entry_password_without_auth(self, client: AsyncClient):
        """Test getting entry password without authentication."""
        response = await client.get("/api/v1/entries/Test/Entry/password")

        assert response.status_code == 401

    @pytest.mark.asyncio
    @pytest.mark.skipif(
        True,  # Skip by default
        reason="Requires real KeePassXC database with entries",
    )
    async def test_get_entry_password_success(
        self,
        authenticated_client: tuple[AsyncClient, str, dict],
    ):
        """Test getting entry password (explicit request)."""
        client, token, session_info = authenticated_client

        # First, list entries
        list_response = await client.get("/api/v1/entries")
        entries = list_response.json()["entries"]
        if not entries:
            pytest.skip("No entries in test database")

        entry_name = entries[0]["name"]

        # Get password explicitly
        response = await client.get(f"/api/v1/entries/{entry_name}/password")

        assert response.status_code == 200
        data = response.json()

        # Should have password field
        assert "password" in data
        assert isinstance(data["password"], str)

    @pytest.mark.asyncio
    async def test_create_entry_without_auth(
        self,
        client: AsyncClient,
        sample_entry_data: dict,
    ):
        """Test creating entry without authentication."""
        response = await client.post(
            "/api/v1/entries",
            json=sample_entry_data,
        )

        assert response.status_code == 401

    @pytest.mark.asyncio
    @pytest.mark.skipif(
        True,  # Skip by default
        reason="Requires real KeePassXC database",
    )
    async def test_create_entry_success(
        self,
        authenticated_client: tuple[AsyncClient, str, dict],
        sample_entry_data: dict,
    ):
        """Test creating a new entry."""
        client, token, session_info = authenticated_client

        response = await client.post(
            "/api/v1/entries",
            json=sample_entry_data,
        )

        assert response.status_code == 201
        data = response.json()

        # Check structure
        assert "name" in data
        assert "title" in data
        assert "username" in data
        assert "has_password" in data

        # Should NOT contain actual password in response
        assert "password" not in data

        # Verify entry was created
        get_response = await client.get(f"/api/v1/entries/{sample_entry_data['name']}")
        assert get_response.status_code == 200

        # Cleanup: Delete test entry
        await client.delete(f"/api/v1/entries/{sample_entry_data['name']}")

    @pytest.mark.asyncio
    @pytest.mark.skipif(
        True,  # Skip by default
        reason="Requires real KeePassXC database",
    )
    async def test_create_entry_already_exists(
        self,
        authenticated_client: tuple[AsyncClient, str, dict],
        sample_entry_data: dict,
    ):
        """Test creating entry that already exists."""
        client, token, session_info = authenticated_client

        # Create first time
        response1 = await client.post(
            "/api/v1/entries",
            json=sample_entry_data,
        )
        assert response1.status_code == 201

        # Try to create again
        response2 = await client.post(
            "/api/v1/entries",
            json=sample_entry_data,
        )

        assert response2.status_code == 409  # Conflict
        data = response2.json()
        assert data["error"] == "entry_already_exists"

        # Cleanup
        await client.delete(f"/api/v1/entries/{sample_entry_data['name']}")

    @pytest.mark.asyncio
    async def test_create_entry_missing_fields(
        self,
        authenticated_client: tuple[AsyncClient, str, dict],
    ):
        """Test creating entry with missing required fields."""
        if not authenticated_client:
            pytest.skip("Authentication not available")

        client, token, session_info = authenticated_client

        # Missing password
        response = await client.post(
            "/api/v1/entries",
            json={
                "name": "Test/Entry",
                "title": "Test Entry",
                "username": "test_user",
                # Missing password
            },
        )

        assert response.status_code == 422  # Validation error

    @pytest.mark.asyncio
    async def test_update_entry_without_auth(
        self,
        client: AsyncClient,
        updated_entry_data: dict,
    ):
        """Test updating entry without authentication."""
        response = await client.put(
            "/api/v1/entries/Test/Entry",
            json=updated_entry_data,
        )

        assert response.status_code == 401

    @pytest.mark.asyncio
    @pytest.mark.skipif(
        True,  # Skip by default
        reason="Requires real KeePassXC database",
    )
    async def test_update_entry_success(
        self,
        authenticated_client: tuple[AsyncClient, str, dict],
        sample_entry_data: dict,
        updated_entry_data: dict,
    ):
        """Test updating an entry."""
        client, token, session_info = authenticated_client

        # Create entry first
        create_response = await client.post(
            "/api/v1/entries",
            json=sample_entry_data,
        )
        assert create_response.status_code == 201

        # Update entry
        response = await client.put(
            f"/api/v1/entries/{sample_entry_data['name']}",
            json=updated_entry_data,
        )

        assert response.status_code == 200
        data = response.json()

        # Check updated fields
        assert data["username"] == updated_entry_data["username"]
        assert data["url"] == updated_entry_data["url"]

        # Should NOT contain password in response
        assert "password" not in data

        # Cleanup
        await client.delete(f"/api/v1/entries/{sample_entry_data['name']}")

    @pytest.mark.asyncio
    @pytest.mark.skipif(
        True,  # Skip by default
        reason="Requires real KeePassXC database",
    )
    async def test_update_entry_not_found(
        self,
        authenticated_client: tuple[AsyncClient, str, dict],
        updated_entry_data: dict,
    ):
        """Test updating non-existent entry."""
        client, token, session_info = authenticated_client

        response = await client.put(
            "/api/v1/entries/Nonexistent/Entry",
            json=updated_entry_data,
        )

        assert response.status_code == 404
        data = response.json()
        assert data["error"] == "entry_not_found"

    @pytest.mark.asyncio
    async def test_delete_entry_without_auth(self, client: AsyncClient):
        """Test deleting entry without authentication."""
        response = await client.delete("/api/v1/entries/Test/Entry")

        assert response.status_code == 401

    @pytest.mark.asyncio
    @pytest.mark.skipif(
        True,  # Skip by default
        reason="Requires real KeePassXC database",
    )
    async def test_delete_entry_success(
        self,
        authenticated_client: tuple[AsyncClient, str, dict],
        sample_entry_data: dict,
    ):
        """Test deleting an entry."""
        client, token, session_info = authenticated_client

        # Create entry first
        create_response = await client.post(
            "/api/v1/entries",
            json=sample_entry_data,
        )
        assert create_response.status_code == 201

        # Delete entry
        response = await client.delete(f"/api/v1/entries/{sample_entry_data['name']}")

        assert response.status_code == 204  # No Content

        # Verify entry is deleted
        get_response = await client.get(f"/api/v1/entries/{sample_entry_data['name']}")
        assert get_response.status_code == 404

    @pytest.mark.asyncio
    @pytest.mark.skipif(
        True,  # Skip by default
        reason="Requires real KeePassXC database",
    )
    async def test_delete_entry_not_found(
        self,
        authenticated_client: tuple[AsyncClient, str, dict],
    ):
        """Test deleting non-existent entry."""
        client, token, session_info = authenticated_client

        response = await client.delete("/api/v1/entries/Nonexistent/Entry")

        assert response.status_code == 404
        data = response.json()
        assert data["error"] == "entry_not_found"

    @pytest.mark.asyncio
    @pytest.mark.skipif(
        True,  # Skip by default
        reason="Requires real KeePassXC database",
    )
    async def test_entry_crud_flow(
        self,
        authenticated_client: tuple[AsyncClient, str, dict],
        sample_entry_data: dict,
        updated_entry_data: dict,
    ):
        """Test complete CRUD flow for an entry."""
        client, token, session_info = authenticated_client

        # 1. Create
        create_response = await client.post(
            "/api/v1/entries",
            json=sample_entry_data,
        )
        assert create_response.status_code == 201
        assert "password" not in create_response.json()

        # 2. Read
        read_response = await client.get(f"/api/v1/entries/{sample_entry_data['name']}")
        assert read_response.status_code == 200
        assert "password" not in read_response.json()
        assert read_response.json()["has_password"] is True

        # 3. Read password (explicit)
        password_response = await client.get(
            f"/api/v1/entries/{sample_entry_data['name']}/password"
        )
        assert password_response.status_code == 200
        assert password_response.json()["password"] == sample_entry_data["password"]

        # 4. Update
        update_response = await client.put(
            f"/api/v1/entries/{sample_entry_data['name']}",
            json=updated_entry_data,
        )
        assert update_response.status_code == 200
        assert "password" not in update_response.json()

        # 5. Verify update
        verify_response = await client.get(f"/api/v1/entries/{sample_entry_data['name']}")
        assert verify_response.json()["username"] == updated_entry_data["username"]

        # 6. Delete
        delete_response = await client.delete(f"/api/v1/entries/{sample_entry_data['name']}")
        assert delete_response.status_code == 204

        # 7. Verify deletion
        verify_deleted = await client.get(f"/api/v1/entries/{sample_entry_data['name']}")
        assert verify_deleted.status_code == 404
