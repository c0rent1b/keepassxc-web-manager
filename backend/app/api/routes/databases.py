"""
Database endpoints.

Handles database operations (test, info, etc.).
"""

import logging

from fastapi import APIRouter, status

from app.api.dependencies import (
    CurrentSessionDep,
    DecryptedPasswordDep,
    RepositoryDep,
)
from app.api.schemas import DatabaseInfo, DatabaseTestRequest, DatabaseTestResponse

logger = logging.getLogger(__name__)

router = APIRouter()


@router.post(
    "/test",
    response_model=DatabaseTestResponse,
    status_code=status.HTTP_200_OK,
    summary="Test database connection",
    description="Test connection to a KeePassXC database without creating a session",
)
async def test_database(
    request: DatabaseTestRequest,
    repository: RepositoryDep,
) -> DatabaseTestResponse:
    """
    Test database connection.

    This endpoint tests if:
    - Database file exists
    - Password/keyfile are correct
    - Database can be opened

    Does NOT create a session.

    Args:
        request: Test request with credentials
        repository: KeePassXC repository

    Returns:
        DatabaseTestResponse with result

    Raises:
        DatabaseNotFoundError: If database doesn't exist
        DatabaseAuthenticationError: If credentials invalid
    """
    logger.info(f"Testing database connection: {request.database_path}")

    try:
        # Test connection
        success = await repository.test_connection(
            database_path=request.database_path,
            password=request.password,
            keyfile=request.keyfile,
        )

        if success:
            # Get database info
            db_info = await repository.get_database_info(
                database_path=request.database_path,
                password=request.password,
                keyfile=request.keyfile,
            )

            logger.info(f"Database test successful: {request.database_path}")

            return DatabaseTestResponse(
                success=True,
                message="Database connection successful",
                database_info=DatabaseInfo(
                    path=db_info.path,
                    name=db_info.name,
                    filename=db_info.filename,
                    file_size=db_info.file_size,
                    file_size_mb=db_info.file_size_mb,
                    entry_count=db_info.entry_count,
                    has_keyfile=request.keyfile is not None,
                    is_locked=False,
                ),
            )
        else:
            return DatabaseTestResponse(
                success=False,
                message="Database connection failed",
                database_info=None,
            )

    except Exception as e:
        logger.error(f"Database test failed: {str(e)}")
        raise


@router.get(
    "/info",
    response_model=DatabaseInfo,
    status_code=status.HTTP_200_OK,
    summary="Get current database info",
    description="Get information about currently opened database",
)
async def get_database_info(
    session: CurrentSessionDep,
    password: DecryptedPasswordDep,
    repository: RepositoryDep,
) -> DatabaseInfo:
    """
    Get current database information.

    Requires active session.

    Args:
        session: Current session
        password: Decrypted password from session
        repository: KeePassXC repository

    Returns:
        DatabaseInfo with metadata

    Raises:
        DatabaseAuthenticationError: If session invalid
    """
    logger.info(f"Getting database info: {session.database_path}")

    # Get database info
    db_info = await repository.get_database_info(
        database_path=session.database_path,
        password=password,
        keyfile=session.keyfile,
    )

    logger.info(
        f"Database info retrieved: {db_info.name or 'unnamed'} "
        f"({db_info.entry_count} entries)"
    )

    return DatabaseInfo(
        path=db_info.path,
        name=db_info.name,
        filename=db_info.filename,
        file_size=db_info.file_size,
        file_size_mb=db_info.file_size_mb,
        entry_count=db_info.entry_count,
        has_keyfile=session.keyfile is not None,
        is_locked=False,
    )
