"""
Async wrapper for keepassxc-cli.

This module provides async execution of keepassxc-cli commands
using asyncio subprocess for non-blocking operations.
"""

import asyncio
import logging
from pathlib import Path
from typing import Optional

from app.core.exceptions import (
    KeePassXCCommandError,
    KeePassXCNotAvailableError,
    KeePassXCTimeoutError,
)
from app.infrastructure.keepassxc.command_builder import KeePassXCCommandBuilder
from app.infrastructure.keepassxc.output_parser import KeePassXCOutputParser

logger = logging.getLogger(__name__)


class KeePassXCCLIWrapper:
    """
    Async wrapper for keepassxc-cli operations.

    This class handles:
    - Async command execution via subprocess
    - Password passing via stdin (never as CLI argument)
    - Timeout handling
    - Error detection and parsing
    - Output parsing into structured data

    Security notes:
    - Passwords are NEVER passed as command-line arguments
    - All sensitive data goes through stdin
    - Command execution is isolated via subprocess
    """

    def __init__(
        self,
        cli_path: str = "keepassxc-cli",
        default_timeout: int = 30,
    ):
        """
        Initialize CLI wrapper.

        Args:
            cli_path: Path to keepassxc-cli executable
            default_timeout: Default timeout for commands in seconds
        """
        self.cli_path = cli_path
        self.default_timeout = default_timeout
        self.command_builder = KeePassXCCommandBuilder(cli_path)
        self.parser = KeePassXCOutputParser()

    async def check_cli_available(self) -> bool:
        """
        Check if keepassxc-cli is available on the system.

        Returns:
            True if available, False otherwise
        """
        try:
            cmd = self.command_builder.build_version_command()
            stdout, stderr, returncode = await self._execute_command(
                cmd, stdin_data=None, timeout=5
            )

            if returncode == 0:
                version = self.parser.parse_version(stdout)
                logger.info(f"keepassxc-cli version {version} detected")
                return True

            return False

        except Exception as e:
            logger.error(f"keepassxc-cli not available: {str(e)}")
            return False

    async def get_version(self) -> str:
        """
        Get keepassxc-cli version.

        Returns:
            Version string

        Raises:
            KeePassXCNotAvailableError: If CLI not available
        """
        try:
            cmd = self.command_builder.build_version_command()
            stdout, stderr, returncode = await self._execute_command(
                cmd, stdin_data=None, timeout=5
            )

            if returncode != 0:
                raise KeePassXCNotAvailableError("keepassxc-cli returned error")

            return self.parser.parse_version(stdout)

        except KeePassXCNotAvailableError:
            raise
        except Exception as e:
            raise KeePassXCNotAvailableError(
                f"Failed to get version: {str(e)}"
            ) from e

    async def test_connection(
        self,
        database_path: str,
        password: str,
        keyfile: Optional[str] = None,
        timeout: Optional[int] = None,
    ) -> bool:
        """
        Test connection to a KeePassXC database.

        Args:
            database_path: Path to .kdbx file
            password: Master password
            keyfile: Optional keyfile path
            timeout: Command timeout in seconds

        Returns:
            True if connection successful

        Raises:
            DatabaseNotFoundError: If database doesn't exist
            DatabaseAuthenticationError: If password is incorrect
            KeePassXCCommandError: For other errors
        """
        # Validate paths
        db_path = self.command_builder.validate_database_path(database_path)
        if not db_path.exists():
            from app.core.exceptions import DatabaseNotFoundError

            raise DatabaseNotFoundError(f"Database not found: {database_path}")

        # Build command
        cmd, stdin_template = self.command_builder.build_test_connection_command(
            str(db_path), keyfile
        )

        # Replace password placeholder
        stdin_data = stdin_template.replace("{password}", password)

        # Execute
        stdout, stderr, returncode = await self._execute_command(
            cmd, stdin_data, timeout or self.default_timeout
        )

        # Check for errors (will raise exception if failed)
        self.parser.check_for_errors(stdout, stderr, returncode)

        return True

    async def get_database_info(
        self,
        database_path: str,
        password: str,
        keyfile: Optional[str] = None,
        timeout: Optional[int] = None,
    ):
        """
        Get database information.

        Args:
            database_path: Path to .kdbx file
            password: Master password
            keyfile: Optional keyfile path
            timeout: Command timeout in seconds

        Returns:
            Database entity

        Raises:
            DatabaseNotFoundError: If database doesn't exist
            DatabaseAuthenticationError: If password is incorrect
        """
        # Validate path
        db_path = self.command_builder.validate_database_path(database_path)

        # Build command (uses same command as test_connection)
        cmd, stdin_template = self.command_builder.build_test_connection_command(
            str(db_path), keyfile
        )

        stdin_data = stdin_template.replace("{password}", password)

        # Execute
        stdout, stderr, returncode = await self._execute_command(
            cmd, stdin_data, timeout or self.default_timeout
        )

        # Check for errors
        self.parser.check_for_errors(stdout, stderr, returncode)

        # Parse database info
        return self.parser.parse_database_info(stdout, str(db_path))

    async def list_entries(
        self,
        database_path: str,
        password: str,
        keyfile: Optional[str] = None,
        include_recycle_bin: bool = False,
        timeout: Optional[int] = None,
    ) -> list[str]:
        """
        List all entries in database.

        Args:
            database_path: Path to .kdbx file
            password: Master password
            keyfile: Optional keyfile path
            include_recycle_bin: Include recycle bin entries
            timeout: Command timeout in seconds

        Returns:
            List of entry paths
        """
        db_path = self.command_builder.validate_database_path(database_path)

        cmd, stdin_template = self.command_builder.build_list_entries_command(
            str(db_path), keyfile, include_recycle_bin
        )

        stdin_data = stdin_template.replace("{password}", password)

        stdout, stderr, returncode = await self._execute_command(
            cmd, stdin_data, timeout or self.default_timeout
        )

        self.parser.check_for_errors(stdout, stderr, returncode)

        return self.parser.parse_entry_list(stdout)

    async def get_entry(
        self,
        database_path: str,
        password: str,
        entry_name: str,
        keyfile: Optional[str] = None,
        timeout: Optional[int] = None,
    ):
        """
        Get entry details.

        Args:
            database_path: Path to .kdbx file
            password: Master password
            entry_name: Entry name/path
            keyfile: Optional keyfile path
            timeout: Command timeout in seconds

        Returns:
            Entry entity

        Raises:
            EntryNotFoundError: If entry doesn't exist
        """
        db_path = self.command_builder.validate_database_path(database_path)

        cmd, stdin_template = self.command_builder.build_show_entry_command(
            str(db_path), entry_name, keyfile, show_password=True
        )

        stdin_data = stdin_template.replace("{password}", password)

        stdout, stderr, returncode = await self._execute_command(
            cmd, stdin_data, timeout or self.default_timeout
        )

        self.parser.check_for_errors(stdout, stderr, returncode)

        return self.parser.parse_entry_details(stdout, entry_name)

    async def create_entry(
        self,
        database_path: str,
        password: str,
        entry_path: str,
        username: str,
        entry_password: str,
        url: Optional[str] = None,
        notes: Optional[str] = None,
        keyfile: Optional[str] = None,
        timeout: Optional[int] = None,
    ) -> bool:
        """
        Create a new entry.

        Args:
            database_path: Path to .kdbx file
            password: Master password
            entry_path: Full path for new entry
            username: Username for entry
            entry_password: Password for entry
            url: Optional URL
            notes: Optional notes
            keyfile: Optional keyfile path
            timeout: Command timeout in seconds

        Returns:
            True if created successfully

        Raises:
            EntryAlreadyExistsError: If entry already exists
        """
        db_path = self.command_builder.validate_database_path(database_path)

        cmd, stdin_template = self.command_builder.build_add_entry_command(
            str(db_path), entry_path, username, entry_password, url, notes, keyfile
        )

        stdin_data = stdin_template.replace("{password}", password)

        stdout, stderr, returncode = await self._execute_command(
            cmd, stdin_data, timeout or self.default_timeout
        )

        self.parser.check_for_errors(stdout, stderr, returncode)

        return self.parser.is_success_message(stdout + stderr)

    async def update_entry(
        self,
        database_path: str,
        password: str,
        entry_name: str,
        username: Optional[str] = None,
        entry_password: Optional[str] = None,
        url: Optional[str] = None,
        keyfile: Optional[str] = None,
        timeout: Optional[int] = None,
    ) -> bool:
        """
        Update an existing entry.

        Args:
            database_path: Path to .kdbx file
            password: Master password
            entry_name: Entry name/path to update
            username: New username (if updating)
            entry_password: New password (if updating)
            url: New URL (if updating)
            keyfile: Optional keyfile path
            timeout: Command timeout in seconds

        Returns:
            True if updated successfully
        """
        db_path = self.command_builder.validate_database_path(database_path)

        cmd, stdin_template = self.command_builder.build_edit_entry_command(
            str(db_path), entry_name, username, entry_password, url, keyfile
        )

        stdin_data = stdin_template.replace("{password}", password)

        stdout, stderr, returncode = await self._execute_command(
            cmd, stdin_data, timeout or self.default_timeout
        )

        self.parser.check_for_errors(stdout, stderr, returncode)

        return self.parser.is_success_message(stdout + stderr)

    async def delete_entry(
        self,
        database_path: str,
        password: str,
        entry_name: str,
        keyfile: Optional[str] = None,
        timeout: Optional[int] = None,
    ) -> bool:
        """
        Delete an entry.

        Args:
            database_path: Path to .kdbx file
            password: Master password
            entry_name: Entry name/path to delete
            keyfile: Optional keyfile path
            timeout: Command timeout in seconds

        Returns:
            True if deleted successfully
        """
        db_path = self.command_builder.validate_database_path(database_path)

        cmd, stdin_template = self.command_builder.build_remove_entry_command(
            str(db_path), entry_name, keyfile
        )

        stdin_data = stdin_template.replace("{password}", password)

        stdout, stderr, returncode = await self._execute_command(
            cmd, stdin_data, timeout or self.default_timeout
        )

        self.parser.check_for_errors(stdout, stderr, returncode)

        return self.parser.is_success_message(stdout + stderr)

    async def search_entries(
        self,
        database_path: str,
        password: str,
        search_term: str,
        keyfile: Optional[str] = None,
        timeout: Optional[int] = None,
    ) -> list[str]:
        """
        Search for entries.

        Args:
            database_path: Path to .kdbx file
            password: Master password
            search_term: Search term
            keyfile: Optional keyfile path
            timeout: Command timeout in seconds

        Returns:
            List of matching entry paths
        """
        db_path = self.command_builder.validate_database_path(database_path)

        cmd, stdin_template = self.command_builder.build_search_command(
            str(db_path), search_term, keyfile
        )

        stdin_data = stdin_template.replace("{password}", password)

        stdout, stderr, returncode = await self._execute_command(
            cmd, stdin_data, timeout or self.default_timeout
        )

        self.parser.check_for_errors(stdout, stderr, returncode)

        return self.parser.parse_search_results(stdout)

    async def generate_password(
        self,
        length: int = 16,
        include_symbols: bool = True,
        include_numbers: bool = True,
        include_uppercase: bool = True,
        include_lowercase: bool = True,
    ) -> str:
        """
        Generate a secure password.

        Args:
            length: Password length
            include_symbols: Include symbols
            include_numbers: Include numbers
            include_uppercase: Include uppercase
            include_lowercase: Include lowercase

        Returns:
            Generated password
        """
        cmd = self.command_builder.build_generate_password_command(
            length, include_symbols, include_numbers, include_uppercase, include_lowercase
        )

        stdout, stderr, returncode = await self._execute_command(
            cmd, stdin_data=None, timeout=5
        )

        self.parser.check_for_errors(stdout, stderr, returncode)

        return self.parser.parse_generated_password(stdout)

    async def _execute_command(
        self,
        cmd: list[str],
        stdin_data: Optional[str],
        timeout: int,
    ) -> tuple[str, str, int]:
        """
        Execute a command asynchronously.

        Args:
            cmd: Command as list of strings
            stdin_data: Data to pass via stdin (or None)
            timeout: Timeout in seconds

        Returns:
            Tuple of (stdout, stderr, returncode)

        Raises:
            KeePassXCTimeoutError: If command times out
            KeePassXCCommandError: For execution errors
        """
        try:
            logger.debug(f"Executing command: {cmd[0]} {cmd[1]}")

            # Create subprocess
            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdin=asyncio.subprocess.PIPE if stdin_data else None,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )

            # Communicate with timeout
            try:
                stdout_bytes, stderr_bytes = await asyncio.wait_for(
                    process.communicate(
                        input=stdin_data.encode() if stdin_data else None
                    ),
                    timeout=timeout,
                )
            except asyncio.TimeoutError:
                # Kill process on timeout
                try:
                    process.kill()
                    await process.wait()
                except Exception:
                    pass

                raise KeePassXCTimeoutError(
                    f"Command timed out after {timeout} seconds"
                )

            stdout = stdout_bytes.decode("utf-8", errors="replace")
            stderr = stderr_bytes.decode("utf-8", errors="replace")
            returncode = process.returncode

            logger.debug(
                f"Command completed with returncode {returncode}, "
                f"stdout length: {len(stdout)}, stderr length: {len(stderr)}"
            )

            return stdout, stderr, returncode

        except KeePassXCTimeoutError:
            raise
        except Exception as e:
            logger.error(f"Command execution failed: {str(e)}")
            raise KeePassXCCommandError(
                f"Failed to execute command: {str(e)}"
            ) from e
