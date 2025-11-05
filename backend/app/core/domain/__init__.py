"""
Domain entities for KeePassXC Web Manager.

This module contains the core domain models that represent business concepts:
- Entry: Password entry in a database
- Group: Folder/group organization
- Database: KeePassXC database metadata
- Session: Active user session with encrypted credentials
"""

from app.core.domain.database import Database
from app.core.domain.entry import Entry
from app.core.domain.group import Group
from app.core.domain.session import Session

__all__ = [
    "Database",
    "Entry",
    "Group",
    "Session",
]
