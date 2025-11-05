"""
KeePassXC repository implementation.

This module implements the IKeePassXCRepository interface using
the CLI wrapper to interact with KeePassXC databases.
"""

import logging
from pathlib import Path
from typing import Optional

from app.core.domain.database import Database
from app.core.domain.entry import Entry
from app.core.domain.group import Group
from app.core.interfaces.repository import IKeePassXCRepository
from app.infrastructure.keepassxc.cli_wrapper import KeePassXCCLIWrapper

logger = logging.getLogger(__name__)


class KeePassXCRepository(IKeePassXCRepository):
    """
    Repository implementation for KeePassXC operations.

    This adapter (in hexagonal architecture) implements the IKeePassXCRepository
    port using the keepassxc-cli wrapper.

    Security notes:
    - Passwords are never logged
    - All CLI operations are isolated via subprocess
    - Sensitive data only exists in memory during operation
    """

    def __init__(
        self,
        cli_path: str = "keepassxc-cli",
        default_timeout: int = 30,
    ):
        """
        Initialize repository.

        Args:
            cli_path: Path to keepassxc-cli executable
            default_timeout: Default timeout for operations in seconds
        """
        self.cli = KeePassXCCLIWrapper(cli_path, default_timeout)
        logger.info("KeePassXC repository initialized")

    async def check_cli_available(self) -> bool:
        """
        Check if keepassxc-cli is available on the system.

        Returns:
            True if keepassxc-cli is available, False otherwise
        """
        logger.debug("Checking keepassxc-cli availability")
        is_available = await self.cli.check_cli_available()

        if is_available:
            logger.info("keepassxc-cli is available")
        else:
            logger.warning("keepassxc-cli is NOT available")

        return is_available

    async def test_connection(
        self,
        database_path: str,
        password: str,
        keyfile: Optional[str] = None,
    ) -> bool:
        """
        Test connection to a KeePassXC database.

        Args:
            database_path: Path to the .kdbx file
            password: Master password
            keyfile: Optional key file path

        Returns:
            True if connection successful, False otherwise
        """
        logger.info(f"Testing connection to database: {database_path}")

        try:
            result = await self.cli.test_connection(
                database_path=database_path,
                password=password,
                keyfile=keyfile,
            )

            logger.info(f"Connection test {'succeeded' if result else 'failed'}")
            return result

        except Exception as e:
            logger.error(f"Connection test failed: {str(e)}")
            raise

    async def get_database_info(
        self,
        database_path: str,
        password: str,
        keyfile: Optional[str] = None,
    ) -> Database:
        """
        Get information about a database.

        Args:
            database_path: Path to the .kdbx file
            password: Master password
            keyfile: Optional key file path

        Returns:
            Database entity with metadata

        Raises:
            DatabaseNotFoundError: If database file doesn't exist
            DatabaseAuthenticationError: If password is incorrect
        """
        logger.info(f"Getting database info for: {database_path}")

        try:
            # Get basic info via CLI
            db_info = await self.cli.get_database_info(
                database_path=database_path,
                password=password,
                keyfile=keyfile,
            )

            # Enrich with file system info
            db_path = Path(database_path).resolve()
            if db_path.exists():
                db_info.file_size = db_path.stat().st_size

            logger.info(
                f"Database info retrieved: {db_info.name or 'unnamed'}, "
                f"{db_info.entry_count} entries"
            )

            return db_info

        except Exception as e:
            logger.error(f"Failed to get database info: {str(e)}")
            raise

    async def list_entries(
        self,
        database_path: str,
        password: str,
        keyfile: Optional[str] = None,
        include_recycle_bin: bool = False,
    ) -> list[str]:
        """
        List all entry names in the database.

        Args:
            database_path: Path to the .kdbx file
            password: Master password
            keyfile: Optional key file path
            include_recycle_bin: Include entries from recycle bin

        Returns:
            List of entry names (full paths)

        Raises:
            DatabaseAuthenticationError: If password is incorrect
            KeePassXCCommandError: If command fails
        """
        logger.info(f"Listing entries in: {database_path}")

        try:
            entries = await self.cli.list_entries(
                database_path=database_path,
                password=password,
                keyfile=keyfile,
                include_recycle_bin=include_recycle_bin,
            )

            logger.info(f"Found {len(entries)} entries")
            return entries

        except Exception as e:
            logger.error(f"Failed to list entries: {str(e)}")
            raise

    async def get_entry(
        self,
        database_path: str,
        password: str,
        entry_name: str,
        keyfile: Optional[str] = None,
    ) -> Entry:
        """
        Get a specific entry with all its details.

        Args:
            database_path: Path to the .kdbx file
            password: Master password
            entry_name: Name or path of the entry
            keyfile: Optional key file path

        Returns:
            Entry entity with all details

        Raises:
            EntryNotFoundError: If entry doesn't exist
            DatabaseAuthenticationError: If password is incorrect
        """
        logger.info(f"Getting entry: {entry_name} from {database_path}")

        try:
            entry = await self.cli.get_entry(
                database_path=database_path,
                password=password,
                entry_name=entry_name,
                keyfile=keyfile,
            )

            logger.info(f"Entry retrieved: {entry.title}")
            return entry

        except Exception as e:
            logger.error(f"Failed to get entry: {str(e)}")
            raise

    async def create_entry(
        self,
        database_path: str,
        password: str,
        entry_data: dict[str, str],
        keyfile: Optional[str] = None,
    ) -> bool:
        """
        Create a new entry in the database.

        Args:
            database_path: Path to the .kdbx file
            password: Master password
            entry_data: Dictionary with entry data (title, username, password, url, notes)
            keyfile: Optional key file path

        Returns:
            True if created successfully

        Raises:
            EntryAlreadyExistsError: If entry already exists
            DatabaseAuthenticationError: If password is incorrect
        """
        entry_path = entry_data.get("title", "Untitled")
        logger.info(f"Creating entry: {entry_path} in {database_path}")

        try:
            result = await self.cli.create_entry(
                database_path=database_path,
                password=password,
                entry_path=entry_path,
                username=entry_data.get("username", ""),
                entry_password=entry_data.get("password", ""),
                url=entry_data.get("url"),
                notes=entry_data.get("notes"),
                keyfile=keyfile,
            )

            if result:
                logger.info(f"Entry created successfully: {entry_path}")
            else:
                logger.warning(f"Entry creation may have failed: {entry_path}")

            return result

        except Exception as e:
            logger.error(f"Failed to create entry: {str(e)}")
            raise

    async def update_entry(
        self,
        database_path: str,
        password: str,
        entry_name: str,
        new_data: dict[str, str],
        keyfile: Optional[str] = None,
    ) -> bool:
        """
        Update an existing entry.

        Args:
            database_path: Path to the .kdbx file
            password: Master password
            entry_name: Name of the entry to update
            new_data: Dictionary with updated data
            keyfile: Optional key file path

        Returns:
            True if updated successfully

        Raises:
            EntryNotFoundError: If entry doesn't exist
            DatabaseAuthenticationError: If password is incorrect
        """
        logger.info(f"Updating entry: {entry_name} in {database_path}")

        try:
            result = await self.cli.update_entry(
                database_path=database_path,
                password=password,
                entry_name=entry_name,
                username=new_data.get("username"),
                entry_password=new_data.get("password"),
                url=new_data.get("url"),
                keyfile=keyfile,
            )

            if result:
                logger.info(f"Entry updated successfully: {entry_name}")
            else:
                logger.warning(f"Entry update may have failed: {entry_name}")

            return result

        except Exception as e:
            logger.error(f"Failed to update entry: {str(e)}")
            raise

    async def delete_entry(
        self,
        database_path: str,
        password: str,
        entry_name: str,
        keyfile: Optional[str] = None,
    ) -> bool:
        """
        Delete an entry from the database.

        Args:
            database_path: Path to the .kdbx file
            password: Master password
            entry_name: Name of the entry to delete
            keyfile: Optional key file path

        Returns:
            True if deleted successfully

        Raises:
            EntryNotFoundError: If entry doesn't exist
            DatabaseAuthenticationError: If password is incorrect
        """
        logger.info(f"Deleting entry: {entry_name} from {database_path}")

        try:
            result = await self.cli.delete_entry(
                database_path=database_path,
                password=password,
                entry_name=entry_name,
                keyfile=keyfile,
            )

            if result:
                logger.info(f"Entry deleted successfully: {entry_name}")
            else:
                logger.warning(f"Entry deletion may have failed: {entry_name}")

            return result

        except Exception as e:
            logger.error(f"Failed to delete entry: {str(e)}")
            raise

    async def search_entries(
        self,
        database_path: str,
        password: str,
        search_term: str,
        keyfile: Optional[str] = None,
    ) -> list[str]:
        """
        Search for entries matching a search term.

        Args:
            database_path: Path to the .kdbx file
            password: Master password
            search_term: Term to search for
            keyfile: Optional key file path

        Returns:
            List of matching entry names

        Raises:
            DatabaseAuthenticationError: If password is incorrect
        """
        logger.info(f"Searching entries for: {search_term} in {database_path}")

        try:
            results = await self.cli.search_entries(
                database_path=database_path,
                password=password,
                search_term=search_term,
                keyfile=keyfile,
            )

            logger.info(f"Search found {len(results)} results")
            return results

        except Exception as e:
            logger.error(f"Search failed: {str(e)}")
            raise

    async def list_groups(
        self,
        database_path: str,
        password: str,
        keyfile: Optional[str] = None,
    ) -> list[Group]:
        """
        List all groups in the database.

        Args:
            database_path: Path to the .kdbx file
            password: Master password
            keyfile: Optional key file path

        Returns:
            List of Group entities

        Raises:
            DatabaseAuthenticationError: If password is incorrect
        """
        logger.info(f"Listing groups in: {database_path}")

        try:
            # Get entries list (which includes group paths)
            entries = await self.cli.list_entries(
                database_path=database_path,
                password=password,
                keyfile=keyfile,
                include_recycle_bin=False,
            )

            # Extract unique groups from entry paths
            groups_dict: dict[str, Group] = {}

            for entry_path in entries:
                if "/" in entry_path:
                    # Extract group path
                    parts = entry_path.split("/")
                    for i in range(len(parts) - 1):  # Exclude entry name
                        group_path = "/".join(parts[: i + 1])
                        if group_path not in groups_dict:
                            group_name = parts[i]
                            parent = "/".join(parts[:i]) if i > 0 else None

                            groups_dict[group_path] = Group(
                                name=group_name,
                                path=group_path,
                                parent=parent,
                            )

            groups = list(groups_dict.values())
            logger.info(f"Found {len(groups)} groups")

            return groups

        except Exception as e:
            logger.error(f"Failed to list groups: {str(e)}")
            raise

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
            include_symbols: Include special symbols
            include_numbers: Include numbers
            include_uppercase: Include uppercase letters
            include_lowercase: Include lowercase letters

        Returns:
            Generated password
        """
        logger.debug(f"Generating password of length {length}")

        try:
            password = await self.cli.generate_password(
                length=length,
                include_symbols=include_symbols,
                include_numbers=include_numbers,
                include_uppercase=include_uppercase,
                include_lowercase=include_lowercase,
            )

            logger.debug("Password generated successfully")
            return password

        except Exception as e:
            logger.error(f"Failed to generate password: {str(e)}")
            raise
