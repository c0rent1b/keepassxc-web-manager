"""
Domain entity for KeePassXC Group.

This module defines the Group entity which represents a folder/group
in a KeePassXC database.
"""

from dataclasses import dataclass, field
from typing import Optional


@dataclass
class Group:
    """
    Represents a group/folder in a KeePassXC database.

    Groups are used to organize entries hierarchically.

    Attributes:
        name: Name of the group
        path: Full path of the group (e.g., "Work/Projects")
        parent: Parent group path
        entry_count: Number of entries in this group
        subgroups: List of subgroup names
    """

    name: str
    path: str
    parent: Optional[str] = None
    entry_count: int = 0
    subgroups: list[str] = field(default_factory=list)

    def __post_init__(self) -> None:
        """Extract parent from path if not provided."""
        if self.parent is None and "/" in self.path:
            parts = self.path.split("/")
            self.parent = "/".join(parts[:-1])

    @property
    def is_root(self) -> bool:
        """Check if this is a root group (no parent)."""
        return self.parent is None or self.parent == ""

    @property
    def depth(self) -> int:
        """Get the depth level of this group (0 for root)."""
        if self.is_root:
            return 0
        return self.path.count("/") + 1

    @property
    def has_subgroups(self) -> bool:
        """Check if this group has subgroups."""
        return bool(self.subgroups)

    def to_dict(self) -> dict[str, any]:
        """Convert group to dictionary."""
        return {
            "name": self.name,
            "path": self.path,
            "parent": self.parent,
            "entry_count": self.entry_count,
            "subgroups": self.subgroups,
            "is_root": self.is_root,
            "depth": self.depth,
            "has_subgroups": self.has_subgroups,
        }

    @classmethod
    def from_dict(cls, data: dict[str, any]) -> "Group":
        """Create Group from dictionary."""
        return cls(
            name=data["name"],
            path=data["path"],
            parent=data.get("parent"),
            entry_count=data.get("entry_count", 0),
            subgroups=data.get("subgroups", []),
        )

    def __repr__(self) -> str:
        """String representation for debugging."""
        return f"Group(path='{self.path}', entries={self.entry_count})"
