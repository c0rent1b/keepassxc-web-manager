"""
Domain entity for User Session.

This module defines the Session entity which represents an active
user session with a KeePassXC database.
"""

from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Optional


@dataclass
class Session:
    """
    Represents an active user session.

    A session is created when a user successfully authenticates to a
    KeePassXC database. The session stores the encrypted database password
    and metadata about the session.

    SECURITY NOTE: The password is stored encrypted (Fernet) in memory only.
    It is NEVER persisted to disk or database.

    Attributes:
        session_id: Unique session identifier
        database_path: Path to the connected database
        keyfile: Optional path to key file
        encrypted_password: Database password (Fernet encrypted)
        created_at: When the session was created
        last_activity: Last time the session was used
        expires_at: When the session expires
        ip_address: Client IP address (for security logging)
        user_agent: Client user agent (for security logging)
    """

    session_id: str
    database_path: str
    encrypted_password: str
    created_at: datetime
    last_activity: datetime
    expires_at: datetime
    keyfile: Optional[str] = None
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None

    @classmethod
    def create(
        cls,
        session_id: str,
        database_path: str,
        encrypted_password: str,
        timeout_seconds: int = 1800,
        keyfile: Optional[str] = None,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
    ) -> "Session":
        """
        Create a new session.

        Args:
            session_id: Unique session identifier
            database_path: Path to the database
            encrypted_password: Encrypted database password
            timeout_seconds: Session timeout in seconds (default: 30 min)
            keyfile: Optional key file path
            ip_address: Client IP address
            user_agent: Client user agent

        Returns:
            New Session instance
        """
        now = datetime.utcnow()
        return cls(
            session_id=session_id,
            database_path=database_path,
            encrypted_password=encrypted_password,
            keyfile=keyfile,
            created_at=now,
            last_activity=now,
            expires_at=now + timedelta(seconds=timeout_seconds),
            ip_address=ip_address,
            user_agent=user_agent,
        )

    @property
    def is_expired(self) -> bool:
        """Check if session has expired."""
        return datetime.utcnow() > self.expires_at

    @property
    def is_active(self) -> bool:
        """Check if session is still active (not expired)."""
        return not self.is_expired

    @property
    def remaining_time_seconds(self) -> int:
        """Get remaining time until expiration in seconds."""
        if self.is_expired:
            return 0
        delta = self.expires_at - datetime.utcnow()
        return int(delta.total_seconds())

    @property
    def age_seconds(self) -> int:
        """Get session age in seconds."""
        delta = datetime.utcnow() - self.created_at
        return int(delta.total_seconds())

    @property
    def idle_time_seconds(self) -> int:
        """Get idle time (time since last activity) in seconds."""
        delta = datetime.utcnow() - self.last_activity
        return int(delta.total_seconds())

    def refresh(self, timeout_seconds: int = 1800) -> None:
        """
        Refresh session (extend expiration and update last activity).

        Args:
            timeout_seconds: New timeout in seconds
        """
        now = datetime.utcnow()
        self.last_activity = now
        self.expires_at = now + timedelta(seconds=timeout_seconds)

    def to_dict(self) -> dict[str, any]:
        """
        Convert session to dictionary (SAFE - no decrypted password).

        The encrypted_password is intentionally excluded from the dict
        to prevent accidental exposure in logs or API responses.
        """
        return {
            "session_id": self.session_id[:8] + "...",  # Truncated for security
            "database_path": self.database_path,
            "has_keyfile": self.keyfile is not None,
            "created_at": self.created_at.isoformat(),
            "last_activity": self.last_activity.isoformat(),
            "expires_at": self.expires_at.isoformat(),
            "is_expired": self.is_expired,
            "is_active": self.is_active,
            "remaining_time_seconds": self.remaining_time_seconds,
            "age_seconds": self.age_seconds,
            "idle_time_seconds": self.idle_time_seconds,
            "ip_address": self.ip_address,
        }

    def __repr__(self) -> str:
        """String representation for debugging (without sensitive data)."""
        return (
            f"Session(id='{self.session_id[:8]}...', "
            f"database='{self.database_path}', "
            f"active={self.is_active})"
        )
