"""
Global error handlers for FastAPI.

Converts application exceptions into appropriate HTTP responses.
"""

import logging
from datetime import datetime

from fastapi import Request, status
from fastapi.responses import JSONResponse

from app.core.exceptions import (
    CacheException,
    ConfigurationException,
    DatabaseAuthenticationError,
    DatabaseInvalidError,
    DatabaseLockedError,
    DatabaseNotFoundError,
    EntryAlreadyExistsError,
    EntryInvalidDataError,
    EntryNotFoundError,
    InvalidTokenError,
    KeePassWebManagerException,
    KeePassXCCommandError,
    KeePassXCNotAvailableError,
    KeePassXCParsingError,
    KeePassXCTimeoutError,
    RateLimitExceededError,
    SecurityException,
    SensitiveDataError,
    SessionExpiredError,
    ValidationException,
)

logger = logging.getLogger(__name__)


def create_error_response(
    error_type: str,
    message: str,
    status_code: int,
    details: dict = None,
) -> JSONResponse:
    """
    Create standardized error response.

    Args:
        error_type: Error type identifier
        message: Human-readable error message
        status_code: HTTP status code
        details: Additional error details

    Returns:
        JSONResponse with error data
    """
    return JSONResponse(
        status_code=status_code,
        content={
            "error": error_type,
            "message": message,
            "details": details or {},
            "timestamp": datetime.utcnow().isoformat(),
        },
    )


async def keepassxc_not_available_handler(
    request: Request,
    exc: KeePassXCNotAvailableError,
) -> JSONResponse:
    """Handle KeePassXC CLI not available errors."""
    logger.error(f"KeePassXC CLI not available: {str(exc)}")

    return create_error_response(
        error_type="keepassxc_not_available",
        message="KeePassXC CLI is not available. Please ensure keepassxc-cli is installed.",
        status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
        details={"reason": str(exc)},
    )


async def keepassxc_command_error_handler(
    request: Request,
    exc: KeePassXCCommandError,
) -> JSONResponse:
    """Handle KeePassXC command execution errors."""
    logger.error(f"KeePassXC command failed: {str(exc)}")

    return create_error_response(
        error_type="keepassxc_command_error",
        message="KeePassXC command execution failed",
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        details={"reason": str(exc), "context": exc.details},
    )


async def keepassxc_timeout_handler(
    request: Request,
    exc: KeePassXCTimeoutError,
) -> JSONResponse:
    """Handle KeePassXC command timeout errors."""
    logger.error(f"KeePassXC command timed out: {str(exc)}")

    return create_error_response(
        error_type="keepassxc_timeout",
        message="KeePassXC command timed out. The operation took too long.",
        status_code=status.HTTP_504_GATEWAY_TIMEOUT,
        details={"reason": str(exc)},
    )


async def keepassxc_parsing_error_handler(
    request: Request,
    exc: KeePassXCParsingError,
) -> JSONResponse:
    """Handle KeePassXC output parsing errors."""
    logger.error(f"KeePassXC output parsing failed: {str(exc)}")

    return create_error_response(
        error_type="keepassxc_parsing_error",
        message="Failed to parse KeePassXC output",
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        details={"reason": str(exc)},
    )


async def database_not_found_handler(
    request: Request,
    exc: DatabaseNotFoundError,
) -> JSONResponse:
    """Handle database not found errors."""
    logger.warning(f"Database not found: {str(exc)}")

    return create_error_response(
        error_type="database_not_found",
        message="Database file not found",
        status_code=status.HTTP_404_NOT_FOUND,
        details={"reason": str(exc)},
    )


async def database_authentication_handler(
    request: Request,
    exc: DatabaseAuthenticationError,
) -> JSONResponse:
    """Handle database authentication errors."""
    logger.warning(f"Database authentication failed: {str(exc)}")

    return create_error_response(
        error_type="database_authentication_failed",
        message="Invalid password or keyfile. Authentication failed.",
        status_code=status.HTTP_401_UNAUTHORIZED,
        details={"reason": "Invalid credentials"},
    )


async def database_locked_handler(
    request: Request,
    exc: DatabaseLockedError,
) -> JSONResponse:
    """Handle database locked errors."""
    logger.warning(f"Database locked: {str(exc)}")

    return create_error_response(
        error_type="database_locked",
        message="Database is locked by another process",
        status_code=status.HTTP_423_LOCKED,
        details={"reason": str(exc)},
    )


async def database_invalid_handler(
    request: Request,
    exc: DatabaseInvalidError,
) -> JSONResponse:
    """Handle invalid database errors."""
    logger.error(f"Invalid database: {str(exc)}")

    return create_error_response(
        error_type="database_invalid",
        message="Database file is invalid or corrupted",
        status_code=status.HTTP_400_BAD_REQUEST,
        details={"reason": str(exc)},
    )


async def entry_not_found_handler(
    request: Request,
    exc: EntryNotFoundError,
) -> JSONResponse:
    """Handle entry not found errors."""
    logger.warning(f"Entry not found: {str(exc)}")

    return create_error_response(
        error_type="entry_not_found",
        message="Entry not found in database",
        status_code=status.HTTP_404_NOT_FOUND,
        details={"reason": str(exc)},
    )


async def entry_already_exists_handler(
    request: Request,
    exc: EntryAlreadyExistsError,
) -> JSONResponse:
    """Handle entry already exists errors."""
    logger.warning(f"Entry already exists: {str(exc)}")

    return create_error_response(
        error_type="entry_already_exists",
        message="An entry with this name already exists",
        status_code=status.HTTP_409_CONFLICT,
        details={"reason": str(exc)},
    )


async def entry_invalid_data_handler(
    request: Request,
    exc: EntryInvalidDataError,
) -> JSONResponse:
    """Handle invalid entry data errors."""
    logger.warning(f"Invalid entry data: {str(exc)}")

    return create_error_response(
        error_type="entry_invalid_data",
        message="Invalid entry data provided",
        status_code=status.HTTP_400_BAD_REQUEST,
        details={"reason": str(exc)},
    )


async def session_expired_handler(
    request: Request,
    exc: SessionExpiredError,
) -> JSONResponse:
    """Handle session expired errors."""
    logger.info(f"Session expired: {str(exc)}")

    return create_error_response(
        error_type="session_expired",
        message="Your session has expired. Please log in again.",
        status_code=status.HTTP_401_UNAUTHORIZED,
        details={"reason": "Session expired"},
    )


async def invalid_token_handler(
    request: Request,
    exc: InvalidTokenError,
) -> JSONResponse:
    """Handle invalid token errors."""
    logger.warning(f"Invalid token: {str(exc)}")

    return create_error_response(
        error_type="invalid_token",
        message="Invalid or malformed authentication token",
        status_code=status.HTTP_401_UNAUTHORIZED,
        details={"reason": str(exc)},
    )


async def rate_limit_exceeded_handler(
    request: Request,
    exc: RateLimitExceededError,
) -> JSONResponse:
    """Handle rate limit exceeded errors."""
    logger.warning(f"Rate limit exceeded: {str(exc)}")

    return create_error_response(
        error_type="rate_limit_exceeded",
        message="Too many requests. Please try again later.",
        status_code=status.HTTP_429_TOO_MANY_REQUESTS,
        details={"reason": str(exc)},
    )


async def sensitive_data_error_handler(
    request: Request,
    exc: SensitiveDataError,
) -> JSONResponse:
    """
    Handle sensitive data errors.

    This is CRITICAL - it means someone tried to store passwords/secrets
    where they shouldn't be.
    """
    logger.critical(f"CRITICAL SECURITY ERROR - Sensitive data: {str(exc)}")

    return create_error_response(
        error_type="sensitive_data_forbidden",
        message="Operation blocked: Attempted to store sensitive data in forbidden location",
        status_code=status.HTTP_403_FORBIDDEN,
        details={"severity": "CRITICAL"},
    )


async def security_exception_handler(
    request: Request,
    exc: SecurityException,
) -> JSONResponse:
    """Handle generic security exceptions."""
    logger.error(f"Security error: {str(exc)}")

    return create_error_response(
        error_type="security_error",
        message="A security error occurred",
        status_code=status.HTTP_403_FORBIDDEN,
        details={"reason": str(exc)},
    )


async def validation_exception_handler(
    request: Request,
    exc: ValidationException,
) -> JSONResponse:
    """Handle validation errors."""
    logger.warning(f"Validation error: {str(exc)}")

    return create_error_response(
        error_type="validation_error",
        message="Validation failed",
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        details={"reason": str(exc), "context": exc.details},
    )


async def cache_exception_handler(
    request: Request,
    exc: CacheException,
) -> JSONResponse:
    """Handle cache errors."""
    logger.error(f"Cache error: {str(exc)}")

    # Don't expose cache errors to users - treat as internal error
    return create_error_response(
        error_type="internal_error",
        message="An internal error occurred",
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
    )


async def configuration_exception_handler(
    request: Request,
    exc: ConfigurationException,
) -> JSONResponse:
    """Handle configuration errors."""
    logger.critical(f"Configuration error: {str(exc)}")

    return create_error_response(
        error_type="configuration_error",
        message="Server configuration error. Please contact administrator.",
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
    )


async def generic_keepass_exception_handler(
    request: Request,
    exc: KeePassWebManagerException,
) -> JSONResponse:
    """Handle generic KeePass Web Manager exceptions."""
    logger.error(f"Application error: {str(exc)}")

    return create_error_response(
        error_type="application_error",
        message=str(exc),
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        details=exc.details,
    )


async def unhandled_exception_handler(
    request: Request,
    exc: Exception,
) -> JSONResponse:
    """Handle unhandled exceptions."""
    logger.exception(f"Unhandled exception: {str(exc)}")

    # Don't expose internal error details in production
    return create_error_response(
        error_type="internal_error",
        message="An unexpected error occurred",
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
    )


# Map exceptions to handlers
EXCEPTION_HANDLERS = {
    # KeePassXC errors
    KeePassXCNotAvailableError: keepassxc_not_available_handler,
    KeePassXCCommandError: keepassxc_command_error_handler,
    KeePassXCTimeoutError: keepassxc_timeout_handler,
    KeePassXCParsingError: keepassxc_parsing_error_handler,
    # Database errors
    DatabaseNotFoundError: database_not_found_handler,
    DatabaseAuthenticationError: database_authentication_handler,
    DatabaseLockedError: database_locked_handler,
    DatabaseInvalidError: database_invalid_handler,
    # Entry errors
    EntryNotFoundError: entry_not_found_handler,
    EntryAlreadyExistsError: entry_already_exists_handler,
    EntryInvalidDataError: entry_invalid_data_handler,
    # Security errors
    SessionExpiredError: session_expired_handler,
    InvalidTokenError: invalid_token_handler,
    RateLimitExceededError: rate_limit_exceeded_handler,
    SensitiveDataError: sensitive_data_error_handler,
    SecurityException: security_exception_handler,
    # Validation errors
    ValidationException: validation_exception_handler,
    # Infrastructure errors
    CacheException: cache_exception_handler,
    ConfigurationException: configuration_exception_handler,
    # Generic application error
    KeePassWebManagerException: generic_keepass_exception_handler,
    # Catch-all
    Exception: unhandled_exception_handler,
}


def register_exception_handlers(app) -> None:
    """
    Register all exception handlers with FastAPI app.

    Args:
        app: FastAPI application instance
    """
    for exc_class, handler in EXCEPTION_HANDLERS.items():
        app.add_exception_handler(exc_class, handler)

    logger.info(f"Registered {len(EXCEPTION_HANDLERS)} exception handlers")
