"""
Authentication endpoints.

Handles login, logout, and session management.
"""

import logging

from fastapi import APIRouter, status

from app.api.dependencies import (
    ClientInfoDep,
    CurrentSessionDep,
    RateLimitDep,
    RepositoryDep,
    SessionManagerDep,
    SettingsDep,
    TokenDep,
)
from app.api.schemas import (
    LoginRequest,
    LoginResponse,
    LogoutResponse,
    RefreshTokenResponse,
)

logger = logging.getLogger(__name__)

router = APIRouter()


@router.post(
    "/login",
    response_model=LoginResponse,
    status_code=status.HTTP_200_OK,
    summary="Login",
    description="Authenticate with KeePassXC database and create session",
    dependencies=[RateLimitDep],
)
async def login(
    request: LoginRequest,
    repository: RepositoryDep,
    session_manager: SessionManagerDep,
    settings: SettingsDep,
    client_info: ClientInfoDep,
) -> LoginResponse:
    """
    Login with database credentials.

    This endpoint:
    1. Tests connection to the KeePassXC database
    2. Creates an encrypted session
    3. Returns a JWT token

    Security:
    - Password is encrypted with Fernet in memory
    - JWT token is stateless and signed
    - Rate limited to prevent brute force

    Args:
        request: Login credentials
        repository: KeePassXC repository
        session_manager: Session manager
        settings: Application settings
        client_info: Client information

    Returns:
        LoginResponse with JWT token

    Raises:
        DatabaseNotFoundError: If database file doesn't exist
        DatabaseAuthenticationError: If credentials are invalid
    """
    logger.info(
        f"Login attempt for database: {request.database_path} "
        f"from {client_info['ip_address']}"
    )

    # Test connection first
    await repository.test_connection(
        database_path=request.database_path,
        password=request.password,
        keyfile=request.keyfile,
    )

    logger.info(f"Database authentication successful: {request.database_path}")

    # Create session
    session_data = await session_manager.create_session(
        database_path=request.database_path,
        password=request.password,
        keyfile=request.keyfile,
        metadata=client_info,
    )

    logger.info(
        f"Session created: {session_data['session_id'][:8]}... "
        f"for {client_info['ip_address']}"
    )

    return LoginResponse(
        token=session_data["token"],
        session_id=session_data["session_id"],
        expires_in=settings.SESSION_TIMEOUT,
        database_path=request.database_path,
    )


@router.post(
    "/logout",
    response_model=LogoutResponse,
    status_code=status.HTTP_200_OK,
    summary="Logout",
    description="Invalidate current session",
)
async def logout(
    token: TokenDep,
    session_manager: SessionManagerDep,
    session: CurrentSessionDep,
) -> LogoutResponse:
    """
    Logout and invalidate session.

    This endpoint:
    1. Validates the current session
    2. Removes it from memory
    3. Invalidates the JWT token

    Args:
        token: JWT token
        session_manager: Session manager
        session: Current session (validates authentication)

    Returns:
        LogoutResponse with success message
    """
    logger.info(f"Logout requested for session: {session.session_id[:8]}...")

    # Invalidate session
    success = await session_manager.invalidate_session(token)

    if success:
        logger.info(f"Session invalidated: {session.session_id[:8]}...")
        return LogoutResponse(message="Logged out successfully")
    else:
        logger.warning(f"Failed to invalidate session: {session.session_id[:8]}...")
        return LogoutResponse(message="Logout completed (session may have already expired)")


@router.post(
    "/refresh",
    response_model=RefreshTokenResponse,
    status_code=status.HTTP_200_OK,
    summary="Refresh token",
    description="Refresh JWT token to extend session",
)
async def refresh_token(
    token: TokenDep,
    session_manager: SessionManagerDep,
    settings: SettingsDep,
    session: CurrentSessionDep,
) -> RefreshTokenResponse:
    """
    Refresh JWT token.

    This endpoint:
    1. Validates the current token
    2. Creates a new token with extended expiration
    3. Updates session expiration time

    Note: The old token is immediately invalidated.

    Args:
        token: Current JWT token
        session_manager: Session manager
        settings: Application settings
        session: Current session (validates authentication)

    Returns:
        RefreshTokenResponse with new token

    Raises:
        SessionExpiredError: If session has expired
    """
    logger.info(f"Token refresh requested for session: {session.session_id[:8]}...")

    # Refresh session
    new_token = await session_manager.refresh_session(token)

    if not new_token:
        logger.error(f"Failed to refresh session: {session.session_id[:8]}...")
        raise ValueError("Failed to refresh session")

    logger.info(f"Token refreshed for session: {session.session_id[:8]}...")

    return RefreshTokenResponse(
        token=new_token,
        expires_in=settings.SESSION_TIMEOUT,
    )


@router.get(
    "/session",
    summary="Get session info",
    description="Get information about current session (safe, no sensitive data)",
)
async def get_session_info(
    token: TokenDep,
    session_manager: SessionManagerDep,
    session: CurrentSessionDep,
) -> dict:
    """
    Get session information.

    Returns safe session information without sensitive data.

    Args:
        token: JWT token
        session_manager: Session manager
        session: Current session

    Returns:
        Dictionary with safe session info
    """
    session_info = session_manager.get_session_info(token)

    return session_info or {
        "error": "Session information not available"
    }
