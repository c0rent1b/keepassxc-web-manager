"""
Domain entity for KeePassXC Entry.

This module defines the Entry entity which represents a password entry
in a KeePassXC database.
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional
from uuid import UUID


@dataclass
class Entry:
    """
    Represents a password entry in a KeePassXC database.

    This is a domain entity that encapsulates all the data and behavior
    related to a password entry.

    Attributes:
        name: Full path name of the entry (e.g., "Work/GitHub")
        title: Display title of the entry
        username: Username associated with this entry
        password: Password (should always be handled securely)
        url: URL associated with this entry
        notes: Additional notes for this entry
        uuid: Unique identifier for this entry
        group: Group/folder this entry belongs to
        tags: List of tags for organization
        created: Creation timestamp
        modified: Last modification timestamp
        expires: Expiration timestamp (if set)
        custom_attributes: Custom key-value attributes
    """

    # Required fields
    name: str
    title: str

    # Optional fields with defaults
    username: str = ""
    password: str = ""
    url: str = ""
    notes: str = ""
    uuid: Optional[UUID] = None
    group: str = ""
    tags: list[str] = field(default_factory=list)

    # Timestamps
    created: Optional[datetime] = None
    modified: Optional[datetime] = None
    expires: Optional[datetime] = None

    # Custom attributes (for KeePassXC custom fields)
    custom_attributes: dict[str, str] = field(default_factory=dict)

    # Metadata
    is_in_group: bool = False
    has_password: bool = True

    def __post_init__(self) -> None:
        """Validate and normalize entry data after initialization."""
        # Extract group from name if present
        if "/" in self.name and not self.group:
            parts = self.name.split("/")
            self.group = "/".join(parts[:-1])
            self.is_in_group = True

        # Determine if entry has a password
        self.has_password = bool(self.password)

    @property
    def display_name(self) -> str:
        """Get the display name (title without group path)."""
        if "/" in self.name:
            return self.name.split("/")[-1]
        return self.title

    @property
    def full_path(self) -> str:
        """Get the full path including group."""
        return self.name

    @property
    def has_notes(self) -> bool:
        """Check if entry has notes."""
        return bool(self.notes)

    @property
    def has_url(self) -> bool:
        """Check if entry has a URL."""
        return bool(self.url)

    @property
    def has_username(self) -> bool:
        """Check if entry has a username."""
        return bool(self.username)

    @property
    def has_custom_attributes(self) -> bool:
        """Check if entry has custom attributes."""
        return bool(self.custom_attributes)

    @property
    def is_expired(self) -> bool:
        """Check if entry has expired."""
        if self.expires is None:
            return False
        return datetime.now() > self.expires

    @property
    def age_days(self) -> Optional[int]:
        """Get the age of the entry in days."""
        if self.created is None:
            return None
        return (datetime.now() - self.created).days

    def to_dict(self) -> dict[str, any]:
        """
        Convert entry to dictionary (safe for JSON serialization).

        WARNING: This DOES include the password. Only use this for
        secure contexts. For API responses, use to_safe_dict().

        Returns:
            Dictionary representation of the entry
        """
        return {
            "name": self.name,
            "title": self.title,
            "username": self.username,
            "password": self.password,  # WARNING: Contains password!
            "url": self.url,
            "notes": self.notes,
            "uuid": str(self.uuid) if self.uuid else None,
            "group": self.group,
            "tags": self.tags,
            "created": self.created.isoformat() if self.created else None,
            "modified": self.modified.isoformat() if self.modified else None,
            "expires": self.expires.isoformat() if self.expires else None,
            "custom_attributes": self.custom_attributes,
            "is_in_group": self.is_in_group,
            "has_password": self.has_password,
        }

    def to_safe_dict(self) -> dict[str, any]:
        """
        Convert entry to safe dictionary WITHOUT sensitive data.

        This is safe for API responses and logging. The password is
        never included, only a boolean indicating its presence.

        Returns:
            Safe dictionary representation (no password)
        """
        return {
            "name": self.name,
            "title": self.title,
            "username": self.username,
            "url": self.url,
            "notes": self.notes,
            "uuid": str(self.uuid) if self.uuid else None,
            "group": self.group,
            "tags": self.tags,
            "created": self.created.isoformat() if self.created else None,
            "modified": self.modified.isoformat() if self.modified else None,
            "expires": self.expires.isoformat() if self.expires else None,
            "custom_attributes": self.custom_attributes,
            "is_in_group": self.is_in_group,
            "has_password": self.has_password,  # Boolean, not the actual password
            "has_notes": self.has_notes,
            "has_url": self.has_url,
            "has_username": self.has_username,
            "has_custom_attributes": self.has_custom_attributes,
            "is_expired": self.is_expired,
            "age_days": self.age_days,
        }

    @classmethod
    def from_dict(cls, data: dict[str, any]) -> "Entry":
        """
        Create Entry from dictionary.

        Args:
            data: Dictionary containing entry data

        Returns:
            Entry instance
        """
        # Parse timestamps if present
        created = None
        if data.get("created"):
            created = datetime.fromisoformat(data["created"])

        modified = None
        if data.get("modified"):
            modified = datetime.fromisoformat(data["modified"])

        expires = None
        if data.get("expires"):
            expires = datetime.fromisoformat(data["expires"])

        # Parse UUID if present
        uuid_val = None
        if data.get("uuid"):
            uuid_val = UUID(data["uuid"])

        return cls(
            name=data["name"],
            title=data.get("title", data["name"]),
            username=data.get("username", ""),
            password=data.get("password", ""),
            url=data.get("url", ""),
            notes=data.get("notes", ""),
            uuid=uuid_val,
            group=data.get("group", ""),
            tags=data.get("tags", []),
            created=created,
            modified=modified,
            expires=expires,
            custom_attributes=data.get("custom_attributes", {}),
            is_in_group=data.get("is_in_group", False),
            has_password=data.get("has_password", True),
        )

    def __repr__(self) -> str:
        """String representation for debugging."""
        return f"Entry(name='{self.name}', group='{self.group}', has_password={self.has_password})"
