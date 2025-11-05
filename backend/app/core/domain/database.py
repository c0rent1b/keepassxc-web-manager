"""
Domain entity for KeePassXC Database.

This module defines the Database entity which represents a KeePassXC
database file (.kdbx).
"""

from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Optional


@dataclass
class Database:
    """
    Represents a KeePassXC database file.

    This entity contains metadata about a database file, but NOT
    the actual passwords (which remain encrypted in the .kdbx file).

    Attributes:
        path: Absolute path to the .kdbx file
        keyfile: Optional path to key file
        name: Display name of the database
        file_size: Size of the database file in bytes
        last_modified: When the file was last modified
        entry_count: Total number of entries
        group_count: Total number of groups
        is_locked: Whether the database is currently locked
    """

    path: str
    keyfile: Optional[str] = None
    name: Optional[str] = None
    file_size: int = 0
    last_modified: Optional[datetime] = None
    entry_count: int = 0
    group_count: int = 0
    is_locked: bool = True

    def __post_init__(self) -> None:
        """Extract database name from path if not provided."""
        if self.name is None:
            self.name = Path(self.path).stem  # Filename without extension

    @property
    def filename(self) -> str:
        """Get the database filename."""
        return Path(self.path).name

    @property
    def directory(self) -> str:
        """Get the directory containing the database."""
        return str(Path(self.path).parent)

    @property
    def has_keyfile(self) -> bool:
        """Check if database uses a key file."""
        return self.keyfile is not None

    @property
    def file_size_mb(self) -> float:
        """Get file size in megabytes."""
        return self.file_size / (1024 * 1024)

    @property
    def is_empty(self) -> bool:
        """Check if database has no entries."""
        return self.entry_count == 0

    def to_dict(self) -> dict[str, any]:
        """
        Convert database to dictionary.

        NOTE: This is SAFE - contains no sensitive data (passwords, keys).
        """
        return {
            "path": self.path,
            "keyfile": self.keyfile,
            "name": self.name,
            "filename": self.filename,
            "directory": self.directory,
            "file_size": self.file_size,
            "file_size_mb": round(self.file_size_mb, 2),
            "last_modified": (
                self.last_modified.isoformat() if self.last_modified else None
            ),
            "entry_count": self.entry_count,
            "group_count": self.group_count,
            "is_locked": self.is_locked,
            "has_keyfile": self.has_keyfile,
            "is_empty": self.is_empty,
        }

    @classmethod
    def from_dict(cls, data: dict[str, any]) -> "Database":
        """Create Database from dictionary."""
        last_modified = None
        if data.get("last_modified"):
            last_modified = datetime.fromisoformat(data["last_modified"])

        return cls(
            path=data["path"],
            keyfile=data.get("keyfile"),
            name=data.get("name"),
            file_size=data.get("file_size", 0),
            last_modified=last_modified,
            entry_count=data.get("entry_count", 0),
            group_count=data.get("group_count", 0),
            is_locked=data.get("is_locked", True),
        )

    def __repr__(self) -> str:
        """String representation for debugging."""
        return (
            f"Database(name='{self.name}', "
            f"entries={self.entry_count}, "
            f"locked={self.is_locked})"
        )
