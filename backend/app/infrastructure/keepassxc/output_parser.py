"""
Output parser for keepassxc-cli responses.

This module parses stdout/stderr from keepassxc-cli commands
and converts them into structured data or domain entities.
"""

import re
from datetime import datetime
from typing import Optional
from uuid import UUID

from app.core.domain.database import Database
from app.core.domain.entry import Entry
from app.core.domain.group import Group
from app.core.exceptions import (
    DatabaseAuthenticationError,
    DatabaseNotFoundError,
    EntryNotFoundError,
    KeePassXCCommandError,
    KeePassXCParsingError,
)


class KeePassXCOutputParser:
    """
    Parser for keepassxc-cli output.

    This class handles:
    - Success/failure detection
    - Error message parsing
    - Structured data extraction
    - Domain entity creation
    """

    # Error patterns from keepassxc-cli
    ERROR_PATTERNS = {
        "auth": re.compile(
            r"(invalid password|wrong password|incorrect password|failed to open database)",
            re.IGNORECASE,
        ),
        "not_found": re.compile(
            r"(not found|does not exist|no such|could not find)", re.IGNORECASE
        ),
        "locked": re.compile(r"(database is locked|lock file)", re.IGNORECASE),
        "timeout": re.compile(r"(timeout|timed out)", re.IGNORECASE),
    }

    @staticmethod
    def check_for_errors(stdout: str, stderr: str, returncode: int) -> None:
        """
        Check command output for errors and raise appropriate exceptions.

        Args:
            stdout: Standard output from command
            stderr: Standard error from command
            returncode: Process return code

        Raises:
            DatabaseAuthenticationError: If authentication failed
            DatabaseNotFoundError: If database not found
            EntryNotFoundError: If entry not found
            KeePassXCCommandError: For other command errors
        """
        if returncode == 0:
            return  # Success

        error_text = stderr + stdout

        # Check for authentication errors
        if KeePassXCOutputParser.ERROR_PATTERNS["auth"].search(error_text):
            raise DatabaseAuthenticationError(
                "Invalid password or authentication failed"
            )

        # Check for not found errors
        if KeePassXCOutputParser.ERROR_PATTERNS["not_found"].search(error_text):
            if "database" in error_text.lower():
                raise DatabaseNotFoundError("Database file not found")
            else:
                raise EntryNotFoundError("Entry not found in database")

        # Check for locked database
        if KeePassXCOutputParser.ERROR_PATTERNS["locked"].search(error_text):
            raise KeePassXCCommandError(
                "Database is locked by another process",
                {"error_type": "locked"},
            )

        # Check for timeout
        if KeePassXCOutputParser.ERROR_PATTERNS["timeout"].search(error_text):
            raise KeePassXCCommandError(
                "Command timed out", {"error_type": "timeout"}
            )

        # Generic error
        raise KeePassXCCommandError(
            f"Command failed with code {returncode}: {error_text[:200]}"
        )

    @staticmethod
    def parse_version(output: str) -> str:
        """
        Parse version from --version output.

        Args:
            output: Output from keepassxc-cli --version

        Returns:
            Version string (e.g., "2.7.10")

        Example output:
            keepassxc-cli 2.7.10
        """
        match = re.search(r"keepassxc-cli\s+([\d.]+)", output, re.IGNORECASE)
        if match:
            return match.group(1)

        raise KeePassXCParsingError(
            f"Could not parse version from output: {output[:100]}"
        )

    @staticmethod
    def parse_database_info(output: str, database_path: str) -> Database:
        """
        Parse database info from db-info command.

        Args:
            output: Output from db-info command
            database_path: Path to the database

        Returns:
            Database entity

        Example output:
            UUID: {12345678-1234-5678-1234-567812345678}
            Name: MyDatabase
            Description: My personal passwords
            Cipher: AES 256-bit
            KDF: Argon2d
            ...
        """
        try:
            # Extract name
            name_match = re.search(r"Name:\s*(.+)", output)
            name = name_match.group(1).strip() if name_match else None

            # Extract description (optional)
            desc_match = re.search(r"Description:\s*(.+)", output)
            description = desc_match.group(1).strip() if desc_match else None

            # Count entries (if available)
            entry_count_match = re.search(r"Number of entries:\s*(\d+)", output)
            entry_count = (
                int(entry_count_match.group(1)) if entry_count_match else 0
            )

            return Database(
                path=database_path,
                name=name,
                entry_count=entry_count,
                is_locked=False,  # If we got here, it's unlocked
            )

        except Exception as e:
            raise KeePassXCParsingError(
                f"Failed to parse database info: {str(e)}"
            ) from e

    @staticmethod
    def parse_entry_list(output: str) -> list[str]:
        """
        Parse entry list from ls command.

        Args:
            output: Output from ls command

        Returns:
            List of entry paths

        Example output:
            Work/GitHub
            Work/GitLab
            Personal/Email
            Banking/MainBank
        """
        if not output.strip():
            return []

        entries = []
        for line in output.strip().split("\n"):
            line = line.strip()
            # Skip empty lines and group markers
            if line and not line.endswith("/"):
                entries.append(line)

        return entries

    @staticmethod
    def parse_entry_details(output: str, entry_name: str) -> Entry:
        """
        Parse entry details from show command.

        Args:
            output: Output from show command
            entry_name: Name of the entry

        Returns:
            Entry entity

        Example output:
            Title: GitHub
            UserName: user@example.com
            Password: ********
            URL: https://github.com
            Notes: Work account
            UUID: {12345678-1234-5678-1234-567812345678}
            Tags: work, dev
            Created: 2024-01-01 12:00:00
            Modified: 2024-01-15 14:30:00
        """
        try:
            # Extract title
            title_match = re.search(r"Title:\s*(.+)", output)
            title = title_match.group(1).strip() if title_match else entry_name

            # Extract username
            username_match = re.search(r"UserName:\s*(.+)", output)
            username = username_match.group(1).strip() if username_match else ""

            # Extract password
            password_match = re.search(r"Password:\s*(.+)", output)
            password = password_match.group(1).strip() if password_match else ""

            # Extract URL
            url_match = re.search(r"URL:\s*(.+)", output)
            url = url_match.group(1).strip() if url_match else ""

            # Extract notes
            notes_match = re.search(r"Notes:\s*(.+?)(?=\n[A-Z]|$)", output, re.DOTALL)
            notes = notes_match.group(1).strip() if notes_match else ""

            # Extract UUID
            uuid_match = re.search(
                r"UUID:\s*\{?([0-9a-f-]+)\}?", output, re.IGNORECASE
            )
            entry_uuid = None
            if uuid_match:
                try:
                    entry_uuid = UUID(uuid_match.group(1))
                except ValueError:
                    pass

            # Extract tags
            tags_match = re.search(r"Tags:\s*(.+)", output)
            tags = []
            if tags_match:
                tags = [
                    tag.strip()
                    for tag in tags_match.group(1).split(",")
                    if tag.strip()
                ]

            # Extract dates
            created_match = re.search(r"Created:\s*(.+)", output)
            created_at = None
            if created_match:
                try:
                    created_at = datetime.fromisoformat(
                        created_match.group(1).strip()
                    )
                except (ValueError, AttributeError):
                    pass

            modified_match = re.search(r"Modified:\s*(.+)", output)
            modified_at = None
            if modified_match:
                try:
                    modified_at = datetime.fromisoformat(
                        modified_match.group(1).strip()
                    )
                except (ValueError, AttributeError):
                    pass

            # Extract group from entry path
            group = ""
            if "/" in entry_name:
                group = "/".join(entry_name.split("/")[:-1])

            return Entry(
                name=entry_name,
                title=title,
                username=username,
                password=password,
                url=url,
                notes=notes,
                uuid=entry_uuid,
                group=group,
                tags=tags,
                created_at=created_at,
                modified_at=modified_at,
            )

        except Exception as e:
            raise KeePassXCParsingError(
                f"Failed to parse entry details: {str(e)}"
            ) from e

    @staticmethod
    def parse_search_results(output: str) -> list[str]:
        """
        Parse search results from search command.

        Args:
            output: Output from search command

        Returns:
            List of matching entry paths

        Example output:
            Work/GitHub
            Personal/GitHub-Personal
        """
        # Same format as ls output
        return KeePassXCOutputParser.parse_entry_list(output)

    @staticmethod
    def parse_groups(output: str) -> list[Group]:
        """
        Parse groups from ls command output.

        Args:
            output: Output from ls command with groups

        Returns:
            List of Group entities

        Example output:
            Work/
            Personal/
            Banking/
        """
        groups = []

        for line in output.strip().split("\n"):
            line = line.strip()
            # Groups end with /
            if line.endswith("/"):
                group_path = line.rstrip("/")
                group_name = group_path.split("/")[-1]
                parent = (
                    "/".join(group_path.split("/")[:-1])
                    if "/" in group_path
                    else None
                )

                groups.append(
                    Group(
                        name=group_name,
                        path=group_path,
                        parent=parent,
                    )
                )

        return groups

    @staticmethod
    def parse_generated_password(output: str) -> str:
        """
        Parse generated password from generate command.

        Args:
            output: Output from generate command

        Returns:
            Generated password

        Example output:
            X9$mK2!pL5@nQ8#w
        """
        # keepassxc-cli generate outputs just the password
        password = output.strip()

        if not password:
            raise KeePassXCParsingError("Empty password generated")

        return password

    @staticmethod
    def is_success_message(output: str) -> bool:
        """
        Check if output indicates success.

        Args:
            output: Command output

        Returns:
            True if operation was successful
        """
        success_keywords = [
            "successfully",
            "success",
            "added",
            "updated",
            "removed",
            "deleted",
        ]

        output_lower = output.lower()
        return any(keyword in output_lower for keyword in success_keywords)
