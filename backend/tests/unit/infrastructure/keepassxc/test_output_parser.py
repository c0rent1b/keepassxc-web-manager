"""
Unit tests for KeePassXC output parser.

Tests the parsing logic for various CLI outputs and error scenarios.
"""

import pytest

from app.core.exceptions import (
    DatabaseAuthenticationError,
    DatabaseNotFoundError,
    EntryNotFoundError,
    KeePassXCCommandError,
    KeePassXCParsingError,
)
from app.infrastructure.keepassxc.output_parser import KeePassXCOutputParser


class TestKeePassXCOutputParser:
    """Tests for KeePassXCOutputParser class."""

    def setup_method(self):
        """Set up test fixtures."""
        self.parser = KeePassXCOutputParser()

    # =========================================================================
    # Error Detection Tests
    # =========================================================================

    def test_check_for_errors_success(self):
        """Test error check with successful command."""
        # Should not raise
        self.parser.check_for_errors(
            stdout="Success output",
            stderr="",
            returncode=0,
        )

    def test_check_for_errors_authentication_failure(self):
        """Test error check detects authentication errors."""
        with pytest.raises(DatabaseAuthenticationError):
            self.parser.check_for_errors(
                stdout="",
                stderr="Error: Invalid password",
                returncode=1,
            )

    def test_check_for_errors_database_not_found(self):
        """Test error check detects database not found."""
        with pytest.raises(DatabaseNotFoundError):
            self.parser.check_for_errors(
                stdout="",
                stderr="Error: Database file not found",
                returncode=1,
            )

    def test_check_for_errors_entry_not_found(self):
        """Test error check detects entry not found."""
        with pytest.raises(EntryNotFoundError):
            self.parser.check_for_errors(
                stdout="",
                stderr="Error: Entry not found in database",
                returncode=1,
            )

    def test_check_for_errors_database_locked(self):
        """Test error check detects locked database."""
        with pytest.raises(KeePassXCCommandError, match="locked"):
            self.parser.check_for_errors(
                stdout="",
                stderr="Error: Database is locked by another process",
                returncode=1,
            )

    def test_check_for_errors_timeout(self):
        """Test error check detects timeout."""
        with pytest.raises(KeePassXCCommandError, match="timeout"):
            self.parser.check_for_errors(
                stdout="",
                stderr="Error: Command timed out",
                returncode=1,
            )

    def test_check_for_errors_generic_error(self):
        """Test error check handles generic errors."""
        with pytest.raises(KeePassXCCommandError):
            self.parser.check_for_errors(
                stdout="",
                stderr="Some unknown error occurred",
                returncode=1,
            )

    # =========================================================================
    # Version Parsing Tests
    # =========================================================================

    def test_parse_version_standard_format(self):
        """Test parsing standard version output."""
        output = "keepassxc-cli 2.7.10"
        version = self.parser.parse_version(output)

        assert version == "2.7.10"

    def test_parse_version_with_extra_info(self):
        """Test parsing version with extra information."""
        output = "keepassxc-cli 2.7.10\nSome additional info"
        version = self.parser.parse_version(output)

        assert version == "2.7.10"

    def test_parse_version_invalid_format(self):
        """Test parsing invalid version output."""
        with pytest.raises(KeePassXCParsingError):
            self.parser.parse_version("Invalid output")

    # =========================================================================
    # Database Info Parsing Tests
    # =========================================================================

    def test_parse_database_info_complete(self):
        """Test parsing complete database info."""
        output = """UUID: {12345678-1234-5678-1234-567812345678}
Name: MyDatabase
Description: My personal passwords
Cipher: AES 256-bit
KDF: Argon2d
Number of entries: 42"""

        db = self.parser.parse_database_info(output, "/path/to/db.kdbx")

        assert db.name == "MyDatabase"
        assert db.entry_count == 42
        assert db.path == "/path/to/db.kdbx"
        assert db.is_locked is False

    def test_parse_database_info_minimal(self):
        """Test parsing minimal database info."""
        output = "UUID: {12345678-1234-5678-1234-567812345678}"

        db = self.parser.parse_database_info(output, "/path/to/db.kdbx")

        assert db.path == "/path/to/db.kdbx"
        assert db.entry_count == 0
        assert db.is_locked is False

    # =========================================================================
    # Entry List Parsing Tests
    # =========================================================================

    def test_parse_entry_list_multiple_entries(self):
        """Test parsing list of entries."""
        output = """Work/GitHub
Work/GitLab
Personal/Email
Banking/MainBank"""

        entries = self.parser.parse_entry_list(output)

        assert len(entries) == 4
        assert "Work/GitHub" in entries
        assert "Personal/Email" in entries

    def test_parse_entry_list_empty(self):
        """Test parsing empty entry list."""
        entries = self.parser.parse_entry_list("")

        assert entries == []

    def test_parse_entry_list_with_groups(self):
        """Test parsing entry list filters out group markers."""
        output = """Work/
Work/GitHub
Personal/
Personal/Email"""

        entries = self.parser.parse_entry_list(output)

        # Should only include entries, not group markers
        assert "Work/GitHub" in entries
        assert "Personal/Email" in entries
        assert "Work/" not in entries
        assert "Personal/" not in entries

    # =========================================================================
    # Entry Details Parsing Tests
    # =========================================================================

    def test_parse_entry_details_complete(self):
        """Test parsing complete entry details."""
        output = """Title: GitHub
UserName: user@example.com
Password: my_secure_password_123
URL: https://github.com
Notes: Work account
UUID: {12345678-1234-5678-1234-567812345678}
Tags: work, dev
Created: 2024-01-01T12:00:00
Modified: 2024-01-15T14:30:00"""

        entry = self.parser.parse_entry_details(output, "Work/GitHub")

        assert entry.title == "GitHub"
        assert entry.username == "user@example.com"
        assert entry.password == "my_secure_password_123"
        assert entry.url == "https://github.com"
        assert entry.notes == "Work account"
        assert entry.tags == ["work", "dev"]
        assert entry.group == "Work"

    def test_parse_entry_details_minimal(self):
        """Test parsing minimal entry details."""
        output = """Title: MinimalEntry
UserName: user
Password: pass"""

        entry = self.parser.parse_entry_details(output, "MinimalEntry")

        assert entry.title == "MinimalEntry"
        assert entry.username == "user"
        assert entry.password == "pass"
        assert entry.url == ""
        assert entry.notes == ""

    def test_parse_entry_details_multiline_notes(self):
        """Test parsing entry with multiline notes."""
        output = """Title: TestEntry
UserName: user
Password: pass
Notes: Line 1
Line 2
Line 3
UUID: {12345678-1234-5678-1234-567812345678}"""

        entry = self.parser.parse_entry_details(output, "TestEntry")

        # Notes should capture multiple lines
        assert "Line 1" in entry.notes

    # =========================================================================
    # Search Results Parsing Tests
    # =========================================================================

    def test_parse_search_results(self):
        """Test parsing search results."""
        output = """Work/GitHub
Personal/GitHub-Personal"""

        results = self.parser.parse_search_results(output)

        assert len(results) == 2
        assert "Work/GitHub" in results
        assert "Personal/GitHub-Personal" in results

    def test_parse_search_results_no_matches(self):
        """Test parsing empty search results."""
        results = self.parser.parse_search_results("")

        assert results == []

    # =========================================================================
    # Groups Parsing Tests
    # =========================================================================

    def test_parse_groups(self):
        """Test parsing groups from output."""
        output = """Work/
Personal/
Banking/
Work/Development/"""

        groups = self.parser.parse_groups(output)

        assert len(groups) == 4
        group_names = [g.name for g in groups]
        assert "Work" in group_names
        assert "Personal" in group_names
        assert "Banking" in group_names
        assert "Development" in group_names

    def test_parse_groups_with_hierarchy(self):
        """Test parsing hierarchical groups."""
        output = """Work/
Work/Development/
Work/Development/Projects/"""

        groups = self.parser.parse_groups(output)

        # Check hierarchy
        dev_group = next(g for g in groups if g.name == "Development")
        assert dev_group.parent == "Work"

        projects_group = next(g for g in groups if g.name == "Projects")
        assert projects_group.parent == "Work/Development"

    # =========================================================================
    # Password Generation Parsing Tests
    # =========================================================================

    def test_parse_generated_password(self):
        """Test parsing generated password."""
        output = "X9$mK2!pL5@nQ8#w\n"

        password = self.parser.parse_generated_password(output)

        assert password == "X9$mK2!pL5@nQ8#w"
        assert len(password) > 0

    def test_parse_generated_password_empty(self):
        """Test parsing empty password raises error."""
        with pytest.raises(KeePassXCParsingError, match="Empty password"):
            self.parser.parse_generated_password("")

    # =========================================================================
    # Success Message Tests
    # =========================================================================

    def test_is_success_message_positive(self):
        """Test detecting success messages."""
        assert self.parser.is_success_message("Entry added successfully")
        assert self.parser.is_success_message("Updated entry: Work/GitHub")
        assert self.parser.is_success_message("Entry removed")

    def test_is_success_message_negative(self):
        """Test non-success messages."""
        assert not self.parser.is_success_message("Error occurred")
        assert not self.parser.is_success_message("Failed to add entry")
