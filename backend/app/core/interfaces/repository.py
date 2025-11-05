"""
Repository interfaces for KeePassXC operations.

These interfaces define the contracts for interacting with KeePassXC databases.
The actual implementation is in the infrastructure layer.
"""

from abc import ABC, abstractmethod
from typing import Optional

from app.core.domain.database import Database
from app.core.domain.entry import Entry
from app.core.domain.group import Group


class IKeePassXCRepository(ABC):
    """
    Interface for KeePassXC database operations.

    This is a port (in hexagonal architecture) that defines what operations
    can be performed on a KeePassXC database. The actual implementation
    uses keepassxc-cli in the infrastructure layer.
    """

    @abstractmethod
    async def check_cli_available(self) -> bool:
        """
        Check if keepassxc-cli is available on the system.

        Returns:
            True if keepassxc-cli is available, False otherwise
        """
        pass

    @abstractmethod
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
        pass

    @abstractmethod
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
        pass

    @abstractmethod
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
        pass

    @abstractmethod
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
        pass

    @abstractmethod
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
        pass

    @abstractmethod
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
        pass

    @abstractmethod
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
        pass

    @abstractmethod
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
        pass

    @abstractmethod
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
        pass

    @abstractmethod
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
        pass
