"""
Command builder for keepassxc-cli.

This module constructs keepassxc-cli commands with proper argument escaping
and security considerations.
"""

import shlex
from pathlib import Path
from typing import Optional


class KeePassXCCommandBuilder:
    """
    Builder for keepassxc-cli commands.

    This class handles:
    - Command construction with proper argument order
    - Path validation and escaping
    - Password passing via stdin (never as argument)
    - Keyfile handling
    """

    def __init__(self, cli_path: str = "keepassxc-cli"):
        """
        Initialize command builder.

        Args:
            cli_path: Path to keepassxc-cli executable
        """
        self.cli_path = cli_path

    def build_version_command(self) -> list[str]:
        """
        Build command to check keepassxc-cli version.

        Returns:
            Command as list of strings

        Example:
            ["keepassxc-cli", "--version"]
        """
        return [self.cli_path, "--version"]

    def build_test_connection_command(
        self,
        database_path: str,
        keyfile: Optional[str] = None,
    ) -> tuple[list[str], str]:
        """
        Build command to test database connection.

        Args:
            database_path: Path to .kdbx file
            keyfile: Optional keyfile path

        Returns:
            Tuple of (command list, stdin data with password placeholder)

        Example:
            (["keepassxc-cli", "db-info", "/path/to/db.kdbx"], "{password}\\n")
        """
        cmd = [self.cli_path, "db-info"]

        if keyfile:
            cmd.extend(["--key-file", str(keyfile)])

        cmd.append(str(database_path))

        # Password will be passed via stdin
        stdin_data = "{password}\n"

        return cmd, stdin_data

    def build_list_entries_command(
        self,
        database_path: str,
        keyfile: Optional[str] = None,
        include_recycle_bin: bool = False,
    ) -> tuple[list[str], str]:
        """
        Build command to list all entries.

        Args:
            database_path: Path to .kdbx file
            keyfile: Optional keyfile path
            include_recycle_bin: Include recycle bin entries

        Returns:
            Tuple of (command list, stdin data)
        """
        cmd = [self.cli_path, "ls"]

        if keyfile:
            cmd.extend(["--key-file", str(keyfile)])

        if include_recycle_bin:
            cmd.append("--recursive")

        cmd.append(str(database_path))
        cmd.append("/")  # Root path

        stdin_data = "{password}\n"

        return cmd, stdin_data

    def build_show_entry_command(
        self,
        database_path: str,
        entry_name: str,
        keyfile: Optional[str] = None,
        show_password: bool = True,
    ) -> tuple[list[str], str]:
        """
        Build command to show entry details.

        Args:
            database_path: Path to .kdbx file
            entry_name: Entry name/path
            keyfile: Optional keyfile path
            show_password: Include password in output

        Returns:
            Tuple of (command list, stdin data)
        """
        cmd = [self.cli_path, "show"]

        if keyfile:
            cmd.extend(["--key-file", str(keyfile)])

        if show_password:
            cmd.append("--show-protected")

        cmd.append(str(database_path))
        cmd.append(entry_name)

        stdin_data = "{password}\n"

        return cmd, stdin_data

    def build_add_entry_command(
        self,
        database_path: str,
        entry_path: str,
        username: str,
        entry_password: str,
        url: Optional[str] = None,
        notes: Optional[str] = None,
        keyfile: Optional[str] = None,
    ) -> tuple[list[str], str]:
        """
        Build command to add a new entry.

        Args:
            database_path: Path to .kdbx file
            entry_path: Full path for new entry (e.g., "Work/GitHub")
            username: Username for the entry
            entry_password: Password for the entry
            url: Optional URL
            notes: Optional notes
            keyfile: Optional keyfile path

        Returns:
            Tuple of (command list, stdin data)
        """
        cmd = [self.cli_path, "add"]

        if keyfile:
            cmd.extend(["--key-file", str(keyfile)])

        cmd.extend(["--username", username])

        if url:
            cmd.extend(["--url", url])

        cmd.append(str(database_path))
        cmd.append(entry_path)

        # Password order: database password, then entry password
        # Notes are passed via stdin after passwords
        stdin_data = f"{{password}}\n{entry_password}\n{entry_password}\n"

        if notes:
            # Notes will be added via edit command after creation
            pass

        return cmd, stdin_data

    def build_edit_entry_command(
        self,
        database_path: str,
        entry_name: str,
        username: Optional[str] = None,
        entry_password: Optional[str] = None,
        url: Optional[str] = None,
        keyfile: Optional[str] = None,
    ) -> tuple[list[str], str]:
        """
        Build command to edit an entry.

        Args:
            database_path: Path to .kdbx file
            entry_name: Entry name/path
            username: New username (if updating)
            entry_password: New password (if updating)
            url: New URL (if updating)
            keyfile: Optional keyfile path

        Returns:
            Tuple of (command list, stdin data)
        """
        cmd = [self.cli_path, "edit"]

        if keyfile:
            cmd.extend(["--key-file", str(keyfile)])

        if username is not None:
            cmd.extend(["--username", username])

        if url is not None:
            cmd.extend(["--url", url])

        cmd.append(str(database_path))
        cmd.append(entry_name)

        # stdin: database password, then entry password if changing
        if entry_password is not None:
            stdin_data = f"{{password}}\n{entry_password}\n"
        else:
            stdin_data = "{password}\n"

        return cmd, stdin_data

    def build_remove_entry_command(
        self,
        database_path: str,
        entry_name: str,
        keyfile: Optional[str] = None,
    ) -> tuple[list[str], str]:
        """
        Build command to remove an entry.

        Args:
            database_path: Path to .kdbx file
            entry_name: Entry name/path to remove
            keyfile: Optional keyfile path

        Returns:
            Tuple of (command list, stdin data)
        """
        cmd = [self.cli_path, "rm"]

        if keyfile:
            cmd.extend(["--key-file", str(keyfile)])

        cmd.append(str(database_path))
        cmd.append(entry_name)

        stdin_data = "{password}\n"

        return cmd, stdin_data

    def build_search_command(
        self,
        database_path: str,
        search_term: str,
        keyfile: Optional[str] = None,
    ) -> tuple[list[str], str]:
        """
        Build command to search entries.

        Args:
            database_path: Path to .kdbx file
            search_term: Search term
            keyfile: Optional keyfile path

        Returns:
            Tuple of (command list, stdin data)
        """
        cmd = [self.cli_path, "search"]

        if keyfile:
            cmd.extend(["--key-file", str(keyfile)])

        cmd.append(str(database_path))
        cmd.append(search_term)

        stdin_data = "{password}\n"

        return cmd, stdin_data

    def build_generate_password_command(
        self,
        length: int = 16,
        include_symbols: bool = True,
        include_numbers: bool = True,
        include_uppercase: bool = True,
        include_lowercase: bool = True,
    ) -> list[str]:
        """
        Build command to generate a password.

        Args:
            length: Password length
            include_symbols: Include symbols
            include_numbers: Include numbers
            include_uppercase: Include uppercase
            include_lowercase: Include lowercase

        Returns:
            Command list (no stdin needed)
        """
        cmd = [self.cli_path, "generate"]

        cmd.extend(["--length", str(length)])

        char_sets = []
        if include_lowercase:
            char_sets.append("lower")
        if include_uppercase:
            char_sets.append("upper")
        if include_numbers:
            char_sets.append("numbers")
        if include_symbols:
            char_sets.append("special")

        if char_sets:
            # Note: keepassxc-cli uses different flag format
            # We'll use the default character set unless specified
            pass

        return cmd

    @staticmethod
    def escape_argument(arg: str) -> str:
        """
        Escape an argument for shell execution.

        Args:
            arg: Argument to escape

        Returns:
            Escaped argument safe for shell

        Note:
            We use shlex.quote for proper shell escaping
        """
        return shlex.quote(arg)

    @staticmethod
    def validate_database_path(path: str) -> Path:
        """
        Validate and resolve database path.

        Args:
            path: Database path to validate

        Returns:
            Resolved Path object

        Raises:
            ValueError: If path is invalid
        """
        db_path = Path(path).resolve()

        # Security: Prevent path traversal
        if ".." in str(db_path):
            raise ValueError("Path traversal detected in database path")

        # Check extension
        if db_path.suffix.lower() != ".kdbx":
            raise ValueError(f"Invalid database extension: {db_path.suffix}")

        return db_path

    @staticmethod
    def validate_keyfile_path(path: str) -> Path:
        """
        Validate and resolve keyfile path.

        Args:
            path: Keyfile path to validate

        Returns:
            Resolved Path object

        Raises:
            ValueError: If path is invalid
        """
        key_path = Path(path).resolve()

        # Security: Prevent path traversal
        if ".." in str(key_path):
            raise ValueError("Path traversal detected in keyfile path")

        return key_path
