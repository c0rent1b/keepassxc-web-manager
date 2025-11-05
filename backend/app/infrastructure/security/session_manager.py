"""
Session manager for KeePassXC Web Manager.

Manages active sessions with encrypted credentials, using JWT for tokens
and Fernet for password encryption.
"""

import logging
import uuid
from datetime import datetime, timedelta
from typing import Optional

from app.core.domain.session import Session
from app.core.exceptions import SecurityException, SessionExpiredError
from app.infrastructure.security.encryption import FernetEncryptionService
from app.infrastructure.security.jwt_manager import JWTManager

logger = logging.getLogger(__name__)


class SessionManager:
    """
    Session manager combining JWT and encrypted credentials.

    This class:
    - Creates sessions with JWT tokens
    - Stores encrypted passwords in memory
    - Validates and retrieves sessions
    - Handles session expiration and cleanup

    Security notes:
    - Passwords are Fernet-encrypted in memory, NEVER plain text
    - Sessions are stored in memory only (cleared on restart)
    - Automatic cleanup of expired sessions
    - JWT tokens are stateless (signed, not stored)
    """

    def __init__(
        self,
        secret_key: str,
        session_timeout: int = 1800,
        max_password_age: int = 3600,
    ):
        """
        Initialize session manager.

        Args:
            secret_key: Secret key for encryption and JWT signing
            session_timeout: Session timeout in seconds (default 30min)
            max_password_age: Maximum age for encrypted passwords (default 1h)

        Raises:
            ValueError: If secret key is invalid
        """
        if len(secret_key) < 32:
            raise ValueError("Secret key must be at least 32 characters")

        self.session_timeout = session_timeout
        self.max_password_age = max_password_age

        # Initialize security services
        self.encryption = FernetEncryptionService(secret_key)
        self.jwt = JWTManager(secret_key, session_timeout)

        # In-memory session store
        self._sessions: dict[str, Session] = {}

        logger.info(
            f"Session manager initialized "
            f"(timeout: {session_timeout}s, max_password_age: {max_password_age}s)"
        )

    async def create_session(
        self,
        database_path: str,
        password: str,
        keyfile: Optional[str] = None,
        metadata: Optional[dict] = None,
    ) -> dict[str, str]:
        """
        Create a new session.

        Args:
            database_path: Path to KeePassXC database
            password: Master password (will be encrypted)
            keyfile: Optional keyfile path
            metadata: Optional metadata (e.g., IP, user agent)

        Returns:
            Dictionary with 'token' (JWT) and 'session_id'

        Raises:
            SecurityException: If session creation fails
        """
        try:
            # Generate unique session ID
            session_id = str(uuid.uuid4())

            # Encrypt password
            encrypted_password = self.encryption.encrypt_password(password)

            # Calculate expiration
            now = datetime.utcnow()
            expires_at = now + timedelta(seconds=self.session_timeout)

            # Create session entity
            session = Session(
                session_id=session_id,
                database_path=database_path,
                encrypted_password=encrypted_password,
                keyfile=keyfile,
                created_at=now,
                expires_at=expires_at,
                last_accessed=now,
            )

            # Store session in memory
            self._sessions[session_id] = session

            # Create JWT token
            token = self.jwt.create_token(
                subject=session_id,
                claims={
                    "database_path": database_path,
                    "has_keyfile": keyfile is not None,
                },
                expiration=self.session_timeout,
            )

            logger.info(
                f"Session created: {session_id[:8]}... "
                f"(database: {database_path})"
            )

            return {
                "token": token,
                "session_id": session_id,
            }

        except Exception as e:
            logger.error(f"Failed to create session: {str(e)}")
            raise SecurityException(f"Failed to create session: {str(e)}") from e

    async def get_session(self, token: str) -> Optional[Session]:
        """
        Get session from token.

        Args:
            token: JWT token

        Returns:
            Session object or None if invalid/expired

        Raises:
            SessionExpiredError: If session is expired
        """
        try:
            # Decode JWT token
            payload = self.jwt.decode_token(token, verify_expiration=True)
            session_id = payload.get("sub")

            if not session_id:
                logger.warning("Token missing session ID")
                return None

            # Retrieve session from memory
            session = self._sessions.get(session_id)

            if not session:
                logger.warning(f"Session not found: {session_id[:8]}...")
                return None

            # Check if session is expired
            if session.is_expired:
                logger.warning(f"Session expired: {session_id[:8]}...")
                # Clean up expired session
                del self._sessions[session_id]
                raise SessionExpiredError("Session has expired")

            # Update last accessed time
            session.last_accessed = datetime.utcnow()

            logger.debug(f"Session retrieved: {session_id[:8]}...")

            return session

        except SessionExpiredError:
            raise
        except Exception as e:
            logger.error(f"Failed to get session: {str(e)}")
            return None

    async def get_decrypted_password(self, token: str) -> Optional[str]:
        """
        Get decrypted password for a session.

        Args:
            token: JWT token

        Returns:
            Decrypted password or None if session invalid

        Raises:
            SecurityException: If decryption fails
            SessionExpiredError: If session is expired
        """
        session = await self.get_session(token)

        if not session:
            return None

        try:
            # Decrypt password with max age check
            password = self.encryption.decrypt_password(
                session.encrypted_password,
                max_age=self.max_password_age,
            )

            logger.debug(f"Password decrypted for session: {session.session_id[:8]}...")

            return password

        except Exception as e:
            logger.error(f"Failed to decrypt password: {str(e)}")
            raise SecurityException(f"Failed to decrypt password: {str(e)}") from e

    async def refresh_session(self, token: str) -> Optional[str]:
        """
        Refresh a session (extend expiration).

        Args:
            token: Current JWT token

        Returns:
            New JWT token or None if session invalid

        Raises:
            SessionExpiredError: If session is expired
        """
        try:
            # Get current session
            session = await self.get_session(token)

            if not session:
                return None

            # Update session expiration
            session.expires_at = datetime.utcnow() + timedelta(
                seconds=self.session_timeout
            )
            session.last_accessed = datetime.utcnow()

            # Create new JWT token
            new_token = self.jwt.refresh_token(token, expiration=self.session_timeout)

            logger.info(f"Session refreshed: {session.session_id[:8]}...")

            return new_token

        except SessionExpiredError:
            raise
        except Exception as e:
            logger.error(f"Failed to refresh session: {str(e)}")
            return None

    async def invalidate_session(self, token: str) -> bool:
        """
        Invalidate a session (logout).

        Args:
            token: JWT token

        Returns:
            True if invalidated successfully, False otherwise
        """
        try:
            # Get session ID from token
            payload = self.jwt.decode_token(token, verify_expiration=False)
            session_id = payload.get("sub")

            if not session_id:
                return False

            # Remove session from memory
            if session_id in self._sessions:
                del self._sessions[session_id]
                logger.info(f"Session invalidated: {session_id[:8]}...")
                return True

            return False

        except Exception as e:
            logger.error(f"Failed to invalidate session: {str(e)}")
            return False

    async def cleanup_expired_sessions(self) -> int:
        """
        Remove all expired sessions from memory.

        Returns:
            Number of sessions cleaned up
        """
        now = datetime.utcnow()
        expired_sessions = []

        # Find expired sessions
        for session_id, session in self._sessions.items():
            if session.expires_at < now:
                expired_sessions.append(session_id)

        # Remove expired sessions
        for session_id in expired_sessions:
            del self._sessions[session_id]

        if expired_sessions:
            logger.info(f"Cleaned up {len(expired_sessions)} expired sessions")

        return len(expired_sessions)

    def get_active_session_count(self) -> int:
        """
        Get number of active sessions.

        Returns:
            Active session count
        """
        # Filter out expired sessions
        now = datetime.utcnow()
        active_count = sum(
            1 for session in self._sessions.values() if session.expires_at > now
        )

        return active_count

    def get_session_info(self, token: str) -> Optional[dict]:
        """
        Get safe session information (no sensitive data).

        Args:
            token: JWT token

        Returns:
            Dictionary with safe session info or None
        """
        try:
            payload = self.jwt.decode_token(token, verify_expiration=False)
            session_id = payload.get("sub")

            if not session_id or session_id not in self._sessions:
                return None

            session = self._sessions[session_id]

            return {
                "session_id": session_id[:8] + "...",  # Truncated
                "database_path": session.database_path,
                "has_keyfile": session.keyfile is not None,
                "created_at": session.created_at.isoformat(),
                "expires_at": session.expires_at.isoformat(),
                "is_expired": session.is_expired,
                "remaining_time": session.remaining_time_seconds,
            }

        except Exception:
            return None

    async def clear_all_sessions(self) -> int:
        """
        Clear all sessions (emergency logout).

        Returns:
            Number of sessions cleared
        """
        count = len(self._sessions)
        self._sessions.clear()

        logger.warning(f"All sessions cleared: {count} sessions removed")

        return count
