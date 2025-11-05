"""
FastAPI dependency injection.

Provides dependencies for routes including:
- Settings
- Services (repository, cache, security)
- Authentication
- Rate limiting
"""

import logging
from typing import Annotated, Optional

from fastapi import Depends, Header, HTTPException, Request, status

from app.core.config import Settings, get_settings
from app.core.domain.session import Session
from app.core.exceptions import (
    InvalidTokenError,
    RateLimitExceededError,
    SessionExpiredError,
)
from app.core.interfaces.cache import ICacheService
from app.core.interfaces.repository import IKeePassXCRepository
from app.infrastructure.cache.memory_cache import MemoryCache
from app.infrastructure.cache.redis_cache import RedisCache
from app.infrastructure.keepassxc.repository import KeePassXCRepository
from app.infrastructure.security.session_manager import SessionManager

logger = logging.getLogger(__name__)


# =============================================================================
# Settings Dependency
# =============================================================================


async def get_settings_dependency() -> Settings:
    """
    Get application settings.

    Returns:
        Settings instance
    """
    return get_settings()


# =============================================================================
# Service Dependencies
# =============================================================================


async def get_repository(
    settings: Annotated[Settings, Depends(get_settings_dependency)],
) -> IKeePassXCRepository:
    """
    Get KeePassXC repository.

    Args:
        settings: Application settings

    Returns:
        KeePassXC repository instance
    """
    return KeePassXCRepository(
        cli_path=settings.KEEPASSXC_CLI_PATH,
        default_timeout=settings.KEEPASSXC_COMMAND_TIMEOUT,
    )


async def get_cache_service(
    settings: Annotated[Settings, Depends(get_settings_dependency)],
) -> ICacheService:
    """
    Get cache service (Redis or Memory).

    Args:
        settings: Application settings

    Returns:
        Cache service instance
    """
    if settings.CACHE_BACKEND == "redis":
        return RedisCache(
            redis_url=settings.REDIS_URL,
            default_ttl=settings.CACHE_DEFAULT_TTL,
            key_prefix=settings.CACHE_KEY_PREFIX,
            use_fallback=True,
        )
    else:
        return MemoryCache(
            default_ttl=settings.CACHE_DEFAULT_TTL,
        )


async def get_session_manager(
    settings: Annotated[Settings, Depends(get_settings_dependency)],
) -> SessionManager:
    """
    Get session manager.

    Args:
        settings: Application settings

    Returns:
        Session manager instance
    """
    return SessionManager(
        secret_key=settings.SECRET_KEY,
        session_timeout=settings.SESSION_TIMEOUT,
        max_password_age=settings.MAX_PASSWORD_AGE,
    )


# =============================================================================
# Authentication Dependencies
# =============================================================================


async def get_token_from_header(
    authorization: Annotated[Optional[str], Header()] = None,
) -> str:
    """
    Extract JWT token from Authorization header.

    Args:
        authorization: Authorization header value

    Returns:
        JWT token

    Raises:
        HTTPException: If header missing or invalid format
    """
    if not authorization:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing authorization header",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Expected format: "Bearer <token>"
    parts = authorization.split()

    if len(parts) != 2 or parts[0].lower() != "bearer":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authorization header format (expected: Bearer <token>)",
            headers={"WWW-Authenticate": "Bearer"},
        )

    return parts[1]


async def get_current_session(
    token: Annotated[str, Depends(get_token_from_header)],
    session_manager: Annotated[SessionManager, Depends(get_session_manager)],
) -> Session:
    """
    Get current session from token.

    Args:
        token: JWT token
        session_manager: Session manager instance

    Returns:
        Active session

    Raises:
        HTTPException: If token invalid or session expired
    """
    try:
        session = await session_manager.get_session(token)

        if not session:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid or expired session",
                headers={"WWW-Authenticate": "Bearer"},
            )

        logger.debug(f"Session authenticated: {session.session_id[:8]}...")

        return session

    except SessionExpiredError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Session has expired",
            headers={"WWW-Authenticate": "Bearer"},
        ) from e

    except InvalidTokenError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token",
            headers={"WWW-Authenticate": "Bearer"},
        ) from e

    except Exception as e:
        logger.error(f"Authentication failed: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Authentication failed",
        ) from e


async def get_decrypted_password(
    token: Annotated[str, Depends(get_token_from_header)],
    session_manager: Annotated[SessionManager, Depends(get_session_manager)],
) -> str:
    """
    Get decrypted password from current session.

    Args:
        token: JWT token
        session_manager: Session manager instance

    Returns:
        Decrypted master password

    Raises:
        HTTPException: If token invalid or password decryption fails
    """
    try:
        password = await session_manager.get_decrypted_password(token)

        if not password:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Failed to decrypt password",
            )

        return password

    except Exception as e:
        logger.error(f"Password decryption failed: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Failed to decrypt password",
        ) from e


# =============================================================================
# Rate Limiting Dependencies
# =============================================================================


async def check_rate_limit(
    request: Request,
    cache: Annotated[ICacheService, Depends(get_cache_service)],
    settings: Annotated[Settings, Depends(get_settings_dependency)],
) -> None:
    """
    Check rate limit for current request.

    Args:
        request: FastAPI request
        cache: Cache service
        settings: Application settings

    Raises:
        HTTPException: If rate limit exceeded
    """
    if not settings.RATE_LIMIT_ENABLED:
        return

    # Get client identifier (IP address)
    client_ip = request.client.host if request.client else "unknown"

    # Get endpoint path
    endpoint = request.url.path

    # Determine rate limit based on endpoint
    if "/auth/login" in endpoint:
        max_attempts = settings.RATE_LIMIT_LOGIN
    else:
        max_attempts = settings.RATE_LIMIT_API

    # Create rate limit key
    rate_limit_key = f"rate_limit:{client_ip}:{endpoint}"

    try:
        # Get current count
        current_count = await cache.get(rate_limit_key) or 0

        if isinstance(current_count, int) and current_count >= max_attempts:
            logger.warning(
                f"Rate limit exceeded: {client_ip} on {endpoint} "
                f"({current_count}/{max_attempts})"
            )

            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail=f"Rate limit exceeded. Try again in {settings.RATE_LIMIT_WINDOW} seconds",
                headers={"Retry-After": str(settings.RATE_LIMIT_WINDOW)},
            )

        # Increment counter
        await cache.increment(rate_limit_key, 1)

        # Set TTL if this is the first request
        if current_count == 0:
            await cache.set(
                rate_limit_key,
                1,
                ttl=settings.RATE_LIMIT_WINDOW,
            )

    except HTTPException:
        raise
    except RateLimitExceededError as e:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail=str(e),
        ) from e
    except Exception as e:
        # Don't block requests if rate limiting fails
        logger.error(f"Rate limiting check failed: {str(e)}")


# =============================================================================
# Optional Authentication (for public endpoints)
# =============================================================================


async def get_optional_session(
    authorization: Annotated[Optional[str], Header()] = None,
    session_manager: Annotated[SessionManager, Depends(get_session_manager)] = None,
) -> Optional[Session]:
    """
    Get session if token provided, otherwise None.

    Useful for endpoints that can work with or without authentication.

    Args:
        authorization: Authorization header (optional)
        session_manager: Session manager instance

    Returns:
        Session if authenticated, None otherwise
    """
    if not authorization:
        return None

    try:
        # Extract token
        parts = authorization.split()
        if len(parts) != 2 or parts[0].lower() != "bearer":
            return None

        token = parts[1]

        # Get session
        session = await session_manager.get_session(token)
        return session

    except Exception:
        # Silently fail for optional authentication
        return None


# =============================================================================
# Request Context Dependencies
# =============================================================================


async def get_client_info(request: Request) -> dict[str, str]:
    """
    Get client information from request.

    Args:
        request: FastAPI request

    Returns:
        Dictionary with client info (IP, user agent)
    """
    return {
        "ip_address": request.client.host if request.client else "unknown",
        "user_agent": request.headers.get("user-agent", "unknown"),
    }


# =============================================================================
# Type Aliases for Easier Usage
# =============================================================================

# Common dependencies
SettingsDep = Annotated[Settings, Depends(get_settings_dependency)]
RepositoryDep = Annotated[IKeePassXCRepository, Depends(get_repository)]
CacheDep = Annotated[ICacheService, Depends(get_cache_service)]
SessionManagerDep = Annotated[SessionManager, Depends(get_session_manager)]

# Authentication dependencies
TokenDep = Annotated[str, Depends(get_token_from_header)]
CurrentSessionDep = Annotated[Session, Depends(get_current_session)]
DecryptedPasswordDep = Annotated[str, Depends(get_decrypted_password)]

# Optional authentication
OptionalSessionDep = Annotated[Optional[Session], Depends(get_optional_session)]

# Rate limiting
RateLimitDep = Annotated[None, Depends(check_rate_limit)]

# Client info
ClientInfoDep = Annotated[dict[str, str], Depends(get_client_info)]
