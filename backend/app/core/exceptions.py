"""
Custom exceptions for KeePassXC Web Manager.

This module defines all custom exceptions used throughout the application.
They provide clear error messages and help with error handling.
"""

from typing import Any, Optional


# =============================================================================
# Base Exception
# =============================================================================

class KeePassWebManagerException(Exception):
    """Base exception for all KeePassXC Web Manager exceptions."""

    def __init__(self, message: str, details: Optional[dict[str, Any]] = None) -> None:
        """
        Initialize the exception.

        Args:
            message: Human-readable error message
            details: Additional context about the error
        """
        self.message = message
        self.details = details or {}
        super().__init__(self.message)


# =============================================================================
# KeePassXC CLI Exceptions
# =============================================================================

class KeePassXCException(KeePassWebManagerException):
    """Base exception for KeePassXC CLI related errors."""


class KeePassXCNotAvailableError(KeePassXCException):
    """Raised when keepassxc-cli is not available on the system."""

    def __init__(self) -> None:
        super().__init__(
            "keepassxc-cli is not available. Please install KeePassXC.",
            {"suggestion": "Install KeePassXC from https://keepassxc.org/"}
        )


class KeePassXCCommandError(KeePassXCException):
    """Raised when a keepassxc-cli command fails."""

    def __init__(self, command: str, return_code: int, stderr: str) -> None:
        super().__init__(
            f"KeePassXC CLI command failed: {command}",
            {
                "command": command,
                "return_code": return_code,
                "stderr": stderr
            }
        )


class KeePassXCTimeoutError(KeePassXCException):
    """Raised when a keepassxc-cli command times out."""

    def __init__(self, command: str, timeout: int) -> None:
        super().__init__(
            f"KeePassXC CLI command timed out after {timeout}s: {command}",
            {"command": command, "timeout": timeout}
        )


class KeePassXCParsingError(KeePassXCException):
    """Raised when unable to parse keepassxc-cli output."""

    def __init__(self, output: str, expected_format: str) -> None:
        super().__init__(
            "Failed to parse KeePassXC CLI output",
            {"output": output[:200], "expected_format": expected_format}
        )


# =============================================================================
# Database Exceptions
# =============================================================================

class DatabaseException(KeePassWebManagerException):
    """Base exception for database related errors."""


class DatabaseNotFoundError(DatabaseException):
    """Raised when a KeePassXC database file is not found."""

    def __init__(self, database_path: str) -> None:
        super().__init__(
            f"Database file not found: {database_path}",
            {"database_path": database_path}
        )


class DatabaseInvalidError(DatabaseException):
    """Raised when a database file is invalid or corrupted."""

    def __init__(self, database_path: str, reason: str) -> None:
        super().__init__(
            f"Invalid database file: {database_path}",
            {"database_path": database_path, "reason": reason}
        )


class DatabaseAuthenticationError(DatabaseException):
    """Raised when authentication to a database fails."""

    def __init__(self, database_path: str) -> None:
        super().__init__(
            "Authentication failed. Invalid password or key file.",
            {"database_path": database_path}
        )


class DatabaseLockedError(DatabaseException):
    """Raised when trying to access a locked database."""

    def __init__(self, database_path: str) -> None:
        super().__init__(
            f"Database is locked: {database_path}",
            {"database_path": database_path}
        )


# =============================================================================
# Entry Exceptions
# =============================================================================

class EntryException(KeePassWebManagerException):
    """Base exception for entry related errors."""


class EntryNotFoundError(EntryException):
    """Raised when an entry is not found in the database."""

    def __init__(self, entry_name: str) -> None:
        super().__init__(
            f"Entry not found: {entry_name}",
            {"entry_name": entry_name}
        )


class EntryAlreadyExistsError(EntryException):
    """Raised when trying to create an entry that already exists."""

    def __init__(self, entry_name: str) -> None:
        super().__init__(
            f"Entry already exists: {entry_name}",
            {"entry_name": entry_name}
        )


class EntryInvalidDataError(EntryException):
    """Raised when entry data is invalid."""

    def __init__(self, field: str, reason: str) -> None:
        super().__init__(
            f"Invalid entry data for field '{field}': {reason}",
            {"field": field, "reason": reason}
        )


# =============================================================================
# Security Exceptions
# =============================================================================

class SecurityException(KeePassWebManagerException):
    """Base exception for security related errors."""


class AuthenticationError(SecurityException):
    """Raised when authentication fails."""

    def __init__(self, reason: str = "Invalid credentials") -> None:
        super().__init__(reason)


class AuthorizationError(SecurityException):
    """Raised when user is not authorized for an action."""

    def __init__(self, action: str) -> None:
        super().__init__(
            f"Not authorized to perform action: {action}",
            {"action": action}
        )


class SessionExpiredError(SecurityException):
    """Raised when a session has expired."""

    def __init__(self, session_id: str) -> None:
        super().__init__(
            "Session has expired. Please log in again.",
            {"session_id": session_id[:8] + "..."}  # Don't expose full session ID
        )


class SessionNotFoundError(SecurityException):
    """Raised when a session is not found."""

    def __init__(self) -> None:
        super().__init__("Session not found. Please log in.")


class InvalidTokenError(SecurityException):
    """Raised when a JWT token is invalid."""

    def __init__(self, reason: str = "Invalid token") -> None:
        super().__init__(f"Invalid authentication token: {reason}")


class RateLimitExceededError(SecurityException):
    """Raised when rate limit is exceeded."""

    def __init__(self, limit: int, window: int) -> None:
        super().__init__(
            f"Rate limit exceeded: {limit} requests per {window} seconds",
            {"limit": limit, "window": window}
        )


class SensitiveDataError(SecurityException):
    """
    Raised when attempting to store sensitive data where it's not allowed.

    This is a CRITICAL security exception that prevents sensitive data
    (passwords, secrets, tokens) from being stored in SQLite or logs.
    """

    def __init__(self, field_name: str, location: str = "database") -> None:
        super().__init__(
            f"FORBIDDEN: Attempt to store sensitive data '{field_name}' in {location}",
            {
                "field_name": field_name,
                "location": location,
                "severity": "CRITICAL"
            }
        )


# =============================================================================
# Validation Exceptions
# =============================================================================

class ValidationException(KeePassWebManagerException):
    """Base exception for validation errors."""


class InvalidPathError(ValidationException):
    """Raised when a file path is invalid or unsafe."""

    def __init__(self, path: str, reason: str) -> None:
        super().__init__(
            f"Invalid or unsafe path: {path}",
            {"path": path, "reason": reason}
        )


class InvalidInputError(ValidationException):
    """Raised when user input is invalid."""

    def __init__(self, field: str, value: Any, reason: str) -> None:
        # Don't expose the actual value if it might be sensitive
        safe_value = "***" if any(
            sensitive in field.lower()
            for sensitive in ["password", "secret", "token", "key"]
        ) else str(value)[:50]

        super().__init__(
            f"Invalid input for field '{field}': {reason}",
            {"field": field, "value": safe_value, "reason": reason}
        )


# =============================================================================
# Cache Exceptions
# =============================================================================

class CacheException(KeePassWebManagerException):
    """Base exception for cache related errors."""


class CacheConnectionError(CacheException):
    """Raised when unable to connect to cache backend (Redis)."""

    def __init__(self, backend: str, reason: str) -> None:
        super().__init__(
            f"Failed to connect to cache backend ({backend}): {reason}",
            {"backend": backend, "reason": reason}
        )


class CacheKeyError(CacheException):
    """Raised when a cache key operation fails."""

    def __init__(self, key: str, operation: str) -> None:
        super().__init__(
            f"Cache {operation} failed for key: {key}",
            {"key": key, "operation": operation}
        )


# =============================================================================
# Configuration Exceptions
# =============================================================================

class ConfigurationException(KeePassWebManagerException):
    """Base exception for configuration errors."""


class MissingConfigurationError(ConfigurationException):
    """Raised when required configuration is missing."""

    def __init__(self, config_key: str) -> None:
        super().__init__(
            f"Missing required configuration: {config_key}",
            {"config_key": config_key}
        )


class InvalidConfigurationError(ConfigurationException):
    """Raised when configuration value is invalid."""

    def __init__(self, config_key: str, value: Any, reason: str) -> None:
        super().__init__(
            f"Invalid configuration for '{config_key}': {reason}",
            {"config_key": config_key, "value": str(value), "reason": reason}
        )
