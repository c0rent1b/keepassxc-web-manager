"""
Unit tests for KeePassXC command builder.

Tests the command construction logic without executing actual commands.
"""

import pytest

from app.infrastructure.keepassxc.command_builder import KeePassXCCommandBuilder


class TestKeePassXCCommandBuilder:
    """Tests for KeePassXCCommandBuilder class."""

    def setup_method(self):
        """Set up test fixtures."""
        self.builder = KeePassXCCommandBuilder()

    def test_build_version_command(self):
        """Test version command construction."""
        cmd = self.builder.build_version_command()

        assert cmd == ["keepassxc-cli", "--version"]

    def test_build_test_connection_command_without_keyfile(self):
        """Test connection command without keyfile."""
        cmd, stdin = self.builder.build_test_connection_command(
            database_path="/path/to/db.kdbx",
            keyfile=None,
        )

        assert cmd == ["keepassxc-cli", "db-info", "/path/to/db.kdbx"]
        assert stdin == "{password}\n"

    def test_build_test_connection_command_with_keyfile(self):
        """Test connection command with keyfile."""
        cmd, stdin = self.builder.build_test_connection_command(
            database_path="/path/to/db.kdbx",
            keyfile="/path/to/key.key",
        )

        assert cmd == [
            "keepassxc-cli",
            "db-info",
            "--key-file",
            "/path/to/key.key",
            "/path/to/db.kdbx",
        ]
        assert stdin == "{password}\n"

    def test_build_list_entries_command_basic(self):
        """Test list entries command without recycle bin."""
        cmd, stdin = self.builder.build_list_entries_command(
            database_path="/path/to/db.kdbx",
            keyfile=None,
            include_recycle_bin=False,
        )

        assert cmd == ["keepassxc-cli", "ls", "/path/to/db.kdbx", "/"]
        assert stdin == "{password}\n"

    def test_build_list_entries_command_with_recycle_bin(self):
        """Test list entries command with recycle bin."""
        cmd, stdin = self.builder.build_list_entries_command(
            database_path="/path/to/db.kdbx",
            keyfile=None,
            include_recycle_bin=True,
        )

        assert cmd == [
            "keepassxc-cli",
            "ls",
            "--recursive",
            "/path/to/db.kdbx",
            "/",
        ]
        assert stdin == "{password}\n"

    def test_build_show_entry_command(self):
        """Test show entry command."""
        cmd, stdin = self.builder.build_show_entry_command(
            database_path="/path/to/db.kdbx",
            entry_name="Work/GitHub",
            keyfile=None,
            show_password=True,
        )

        assert cmd == [
            "keepassxc-cli",
            "show",
            "--show-protected",
            "/path/to/db.kdbx",
            "Work/GitHub",
        ]
        assert stdin == "{password}\n"

    def test_build_add_entry_command(self):
        """Test add entry command."""
        cmd, stdin = self.builder.build_add_entry_command(
            database_path="/path/to/db.kdbx",
            entry_path="Work/GitHub",
            username="user@example.com",
            entry_password="entry_pass_123",
            url="https://github.com",
            notes="Test notes",
            keyfile=None,
        )

        assert "keepassxc-cli" in cmd
        assert "add" in cmd
        assert "--username" in cmd
        assert "user@example.com" in cmd
        assert "--url" in cmd
        assert "https://github.com" in cmd
        assert "/path/to/db.kdbx" in cmd
        assert "Work/GitHub" in cmd

        # Password should be in stdin, not command
        assert "entry_pass_123" not in cmd
        assert "entry_pass_123" in stdin

    def test_build_edit_entry_command(self):
        """Test edit entry command."""
        cmd, stdin = self.builder.build_edit_entry_command(
            database_path="/path/to/db.kdbx",
            entry_name="Work/GitHub",
            username="new_user@example.com",
            entry_password="new_pass_123",
            url="https://github.com/new",
            keyfile=None,
        )

        assert "keepassxc-cli" in cmd
        assert "edit" in cmd
        assert "--username" in cmd
        assert "new_user@example.com" in cmd
        assert "/path/to/db.kdbx" in cmd
        assert "Work/GitHub" in cmd

        # New password should be in stdin
        assert "new_pass_123" in stdin

    def test_build_remove_entry_command(self):
        """Test remove entry command."""
        cmd, stdin = self.builder.build_remove_entry_command(
            database_path="/path/to/db.kdbx",
            entry_name="Work/GitHub",
            keyfile=None,
        )

        assert cmd == [
            "keepassxc-cli",
            "rm",
            "/path/to/db.kdbx",
            "Work/GitHub",
        ]
        assert stdin == "{password}\n"

    def test_build_search_command(self):
        """Test search command."""
        cmd, stdin = self.builder.build_search_command(
            database_path="/path/to/db.kdbx",
            search_term="github",
            keyfile=None,
        )

        assert cmd == [
            "keepassxc-cli",
            "search",
            "/path/to/db.kdbx",
            "github",
        ]
        assert stdin == "{password}\n"

    def test_build_generate_password_command(self):
        """Test generate password command."""
        cmd = self.builder.build_generate_password_command(
            length=20,
            include_symbols=True,
            include_numbers=True,
            include_uppercase=True,
            include_lowercase=True,
        )

        assert "keepassxc-cli" in cmd
        assert "generate" in cmd
        assert "--length" in cmd
        assert "20" in cmd

    def test_validate_database_path_valid(self, tmp_path):
        """Test database path validation with valid path."""
        db_path = tmp_path / "test.kdbx"
        db_path.touch()

        result = self.builder.validate_database_path(str(db_path))

        assert result.suffix == ".kdbx"
        assert result.exists()

    def test_validate_database_path_invalid_extension(self, tmp_path):
        """Test database path validation with invalid extension."""
        db_path = tmp_path / "test.txt"

        with pytest.raises(ValueError, match="Invalid database extension"):
            self.builder.validate_database_path(str(db_path))

    def test_validate_database_path_traversal_attempt(self):
        """Test database path validation prevents path traversal."""
        with pytest.raises(ValueError, match="Path traversal detected"):
            self.builder.validate_database_path("../../../etc/passwd.kdbx")

    def test_validate_keyfile_path_valid(self, tmp_path):
        """Test keyfile path validation with valid path."""
        key_path = tmp_path / "test.key"
        key_path.touch()

        result = self.builder.validate_keyfile_path(str(key_path))

        assert result.exists()

    def test_validate_keyfile_path_traversal_attempt(self):
        """Test keyfile path validation prevents path traversal."""
        with pytest.raises(ValueError, match="Path traversal detected"):
            self.builder.validate_keyfile_path("../../../etc/passwd")

    def test_escape_argument(self):
        """Test argument escaping for shell safety."""
        # Test simple string
        result = self.builder.escape_argument("simple")
        assert "simple" in result

        # Test string with spaces
        result = self.builder.escape_argument("string with spaces")
        assert "string with spaces" in result or "string\\ with\\ spaces" in result

        # Test string with special characters
        result = self.builder.escape_argument("string$with;special")
        # Should be escaped safely
        assert "$" not in result or "\\" in result

    def test_custom_cli_path(self):
        """Test builder with custom CLI path."""
        builder = KeePassXCCommandBuilder(cli_path="/custom/path/keepassxc-cli")

        cmd = builder.build_version_command()

        assert cmd[0] == "/custom/path/keepassxc-cli"
