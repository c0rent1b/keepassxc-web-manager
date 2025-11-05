"""
Security service interface.

This interface defines the contract for security operations including
session management, encryption, password generation, and validation.
"""

from abc import ABC, abstractmethod
from typing import Optional

from app.core.domain.session import Session


class ISecurityService(ABC):
    """
    Interface for security operations.

    This is a port (in hexagonal architecture) that defines security operations.
    Actual implementation is in the infrastructure layer.
    """

    # =========================================================================
    # Session Management
    # =========================================================================

    @abstractmethod
    async def create_session(
        self,
        database_path: str,
        password: str,
        keyfile: Optional[str] = None,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
    ) -> dict[str, str]:
        """
        Create a new session with encrypted credentials.

        Args:
            database_path: Path to the .kdbx file
            password: Master password (will be encrypted)
            keyfile: Optional key file path
            ip_address: Client IP address for audit
            user_agent: Client user agent for audit

        Returns:
            Dictionary with 'token' (JWT) and 'session_id'

        Raises:
            SecurityException: If session creation fails
        """
        pass

    @abstractmethod
    async def validate_token(self, token: str) -> Optional[Session]:
        """
        Validate a JWT token and return the session.

        Args:
            token: JWT token to validate

        Returns:
            Session object if valid, None if invalid/expired

        Raises:
            InvalidTokenError: If token is malformed
            SessionExpiredError: If session has expired
        """
        pass

    @abstractmethod
    async def refresh_session(self, session_id: str) -> bool:
        """
        Refresh a session's expiration time.

        Args:
            session_id: Session ID to refresh

        Returns:
            True if refreshed successfully

        Raises:
            SessionExpiredError: If session no longer exists
        """
        pass

    @abstractmethod
    async def invalidate_session(self, session_id: str) -> bool:
        """
        Invalidate a session (logout).

        Args:
            session_id: Session ID to invalidate

        Returns:
            True if invalidated successfully
        """
        pass

    @abstractmethod
    async def get_session(self, session_id: str) -> Optional[Session]:
        """
        Get a session by ID.

        Args:
            session_id: Session ID

        Returns:
            Session object if found and valid, None otherwise
        """
        pass

    @abstractmethod
    async def cleanup_expired_sessions(self) -> int:
        """
        Remove all expired sessions.

        Returns:
            Number of sessions cleaned up
        """
        pass

    # =========================================================================
    # Encryption/Decryption
    # =========================================================================

    @abstractmethod
    def encrypt_password(self, password: str) -> str:
        """
        Encrypt a password using Fernet.

        Args:
            password: Plain text password

        Returns:
            Fernet-encrypted password (base64 encoded)

        Note:
            Synchronous because Fernet operations are CPU-bound and fast
        """
        pass

    @abstractmethod
    def decrypt_password(self, encrypted_password: str) -> str:
        """
        Decrypt a password using Fernet.

        Args:
            encrypted_password: Fernet-encrypted password

        Returns:
            Plain text password

        Raises:
            SecurityException: If decryption fails

        Note:
            Synchronous because Fernet operations are CPU-bound and fast
        """
        pass

    @abstractmethod
    def encrypt_data(self, data: str) -> str:
        """
        Encrypt arbitrary data using Fernet.

        Args:
            data: Plain text data

        Returns:
            Fernet-encrypted data (base64 encoded)
        """
        pass

    @abstractmethod
    def decrypt_data(self, encrypted_data: str) -> str:
        """
        Decrypt arbitrary data using Fernet.

        Args:
            encrypted_data: Fernet-encrypted data

        Returns:
            Plain text data

        Raises:
            SecurityException: If decryption fails
        """
        pass

    # =========================================================================
    # Password Generation
    # =========================================================================

    @abstractmethod
    def generate_password(
        self,
        length: int = 16,
        include_symbols: bool = True,
        include_numbers: bool = True,
        include_uppercase: bool = True,
        include_lowercase: bool = True,
        exclude_ambiguous: bool = False,
    ) -> str:
        """
        Generate a secure random password.

        Args:
            length: Password length (minimum 8)
            include_symbols: Include special symbols (!@#$%^&*)
            include_numbers: Include numbers (0-9)
            include_uppercase: Include uppercase letters (A-Z)
            include_lowercase: Include lowercase letters (a-z)
            exclude_ambiguous: Exclude ambiguous characters (0/O, 1/l/I)

        Returns:
            Generated password

        Raises:
            ValueError: If invalid parameters (e.g., length < 8, no character types)
        """
        pass

    @abstractmethod
    def calculate_password_strength(self, password: str) -> dict[str, any]:
        """
        Calculate password strength score.

        Args:
            password: Password to analyze

        Returns:
            Dictionary with:
            - score: int (0-100)
            - level: str (weak/fair/good/excellent)
            - feedback: list[str] (improvement suggestions)
            - estimated_crack_time: str (human-readable)
        """
        pass

    # =========================================================================
    # Validation and Sanitization
    # =========================================================================

    @abstractmethod
    async def validate_file_path(
        self,
        file_path: str,
        must_exist: bool = False,
        allowed_extensions: Optional[list[str]] = None,
    ) -> dict[str, any]:
        """
        Validate a file path for security issues.

        Args:
            file_path: File path to validate
            must_exist: If True, path must exist
            allowed_extensions: If provided, path must have one of these extensions

        Returns:
            Dictionary with:
            - valid: bool
            - absolute_path: str (resolved path)
            - exists: bool
            - is_file: bool
            - errors: list[str] (validation errors)

        Raises:
            ValueError: If path is invalid or dangerous (path traversal, etc.)
        """
        pass

    @abstractmethod
    def sanitize_input(
        self,
        input_str: str,
        max_length: Optional[int] = None,
        allow_special_chars: bool = True,
    ) -> str:
        """
        Sanitize user input.

        Args:
            input_str: Input string to sanitize
            max_length: Maximum allowed length (None = no limit)
            allow_special_chars: Allow special characters

        Returns:
            Sanitized string

        Raises:
            ValueError: If input is invalid after sanitization
        """
        pass

    @abstractmethod
    async def validate_database_credentials(
        self,
        database_path: str,
        password: str,
        keyfile: Optional[str] = None,
    ) -> bool:
        """
        Validate database credentials without creating a session.

        Args:
            database_path: Path to the .kdbx file
            password: Master password
            keyfile: Optional key file path

        Returns:
            True if credentials are valid

        Raises:
            DatabaseNotFoundError: If database doesn't exist
            DatabaseAuthenticationError: If credentials are invalid
        """
        pass

    # =========================================================================
    # Rate Limiting
    # =========================================================================

    @abstractmethod
    async def check_rate_limit(
        self,
        identifier: str,
        action: str,
        max_attempts: int = 5,
        window_seconds: int = 60,
    ) -> dict[str, any]:
        """
        Check if action is allowed under rate limit.

        Args:
            identifier: Unique identifier (IP address, user ID, etc.)
            action: Action name (e.g., "login", "api_call")
            max_attempts: Maximum attempts allowed in window
            window_seconds: Time window in seconds

        Returns:
            Dictionary with:
            - allowed: bool (if action is allowed)
            - remaining: int (attempts remaining)
            - reset_at: datetime (when limit resets)

        Raises:
            RateLimitExceededError: If limit is exceeded
        """
        pass

    @abstractmethod
    async def record_action(
        self,
        identifier: str,
        action: str,
    ) -> None:
        """
        Record an action for rate limiting.

        Args:
            identifier: Unique identifier
            action: Action name
        """
        pass

    @abstractmethod
    async def reset_rate_limit(
        self,
        identifier: str,
        action: str,
    ) -> bool:
        """
        Reset rate limit for an identifier/action.

        Args:
            identifier: Unique identifier
            action: Action name

        Returns:
            True if reset successfully
        """
        pass

    # =========================================================================
    # Audit Logging
    # =========================================================================

    @abstractmethod
    async def log_security_event(
        self,
        event_type: str,
        severity: str,
        message: str,
        details: Optional[dict[str, any]] = None,
        session_id: Optional[str] = None,
        ip_address: Optional[str] = None,
    ) -> None:
        """
        Log a security event for audit.

        Args:
            event_type: Type of event (login, logout, access_denied, etc.)
            severity: Event severity (info, warning, error, critical)
            message: Human-readable message
            details: Additional details (will be stored in metadata DB)
            session_id: Associated session ID if applicable
            ip_address: Client IP address if applicable

        Note:
            NEVER log sensitive data (passwords, tokens, etc.)
        """
        pass

    @abstractmethod
    async def get_security_events(
        self,
        session_id: Optional[str] = None,
        event_type: Optional[str] = None,
        severity: Optional[str] = None,
        limit: int = 100,
        offset: int = 0,
    ) -> list[dict[str, any]]:
        """
        Get security events from audit log.

        Args:
            session_id: Filter by session ID
            event_type: Filter by event type
            severity: Filter by severity
            limit: Maximum number of results
            offset: Offset for pagination

        Returns:
            List of security events (non-sensitive data only)
        """
        pass
