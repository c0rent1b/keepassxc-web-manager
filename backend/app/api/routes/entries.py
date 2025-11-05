"""
Entry endpoints.

Handles CRUD operations for password entries.
"""

import logging
from typing import Optional

from fastapi import APIRouter, Query, status

from app.api.dependencies import (
    CurrentSessionDep,
    DecryptedPasswordDep,
    RepositoryDep,
)
from app.api.schemas import (
    EntryCreate,
    EntryList,
    EntryPasswordResponse,
    EntryResponse,
    EntryUpdate,
)

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get(
    "",
    response_model=EntryList,
    status_code=status.HTTP_200_OK,
    summary="List entries",
    description="List all entries in the database (passwords NOT included)",
)
async def list_entries(
    session: CurrentSessionDep,
    password: DecryptedPasswordDep,
    repository: RepositoryDep,
    search: Optional[str] = Query(None, description="Search term (optional)"),
) -> EntryList:
    """
    List all entries.

    Returns list of entries WITHOUT passwords for security.
    Use GET /entries/{entry_name}/password to retrieve a specific password.

    Args:
        session: Current session
        password: Decrypted password
        repository: KeePassXC repository
        search: Optional search term

    Returns:
        EntryList with entries (NO passwords)
    """
    logger.info(f"Listing entries for: {session.database_path}")

    if search:
        # Search entries
        logger.info(f"Searching entries: {search}")
        entry_names = await repository.search_entries(
            database_path=session.database_path,
            password=password,
            search_term=search,
            keyfile=session.keyfile,
        )
    else:
        # List all entries
        entry_names = await repository.list_entries(
            database_path=session.database_path,
            password=password,
            keyfile=session.keyfile,
        )

    # Get details for each entry (without password)
    entries = []
    for entry_name in entry_names:
        try:
            entry = await repository.get_entry(
                database_path=session.database_path,
                password=password,
                entry_name=entry_name,
                keyfile=session.keyfile,
            )

            # Convert to safe response (NO password)
            entry_data = entry.to_safe_dict()

            entries.append(
                EntryResponse(
                    name=entry.name,
                    title=entry.title,
                    username=entry.username,
                    url=entry.url,
                    notes=entry.notes,
                    tags=entry.tags,
                    uuid=entry.uuid,
                    group=entry.group,
                    has_password=entry.has_password,
                    password_length=entry.password_length,
                    created_at=entry.created_at,
                    modified_at=entry.modified_at,
                )
            )

        except Exception as e:
            logger.warning(f"Failed to get entry details: {entry_name} - {str(e)}")
            continue

    logger.info(f"Returned {len(entries)} entries")

    return EntryList(
        entries=entries,
        total=len(entries),
    )


@router.get(
    "/{entry_name:path}",
    response_model=EntryResponse,
    status_code=status.HTTP_200_OK,
    summary="Get entry",
    description="Get entry details (password NOT included, use /password endpoint)",
)
async def get_entry(
    entry_name: str,
    session: CurrentSessionDep,
    password: DecryptedPasswordDep,
    repository: RepositoryDep,
) -> EntryResponse:
    """
    Get entry details.

    Returns entry WITHOUT password for security.
    Use GET /entries/{entry_name}/password to retrieve the password.

    Args:
        entry_name: Entry name/path
        session: Current session
        password: Decrypted password
        repository: KeePassXC repository

    Returns:
        EntryResponse (NO password)

    Raises:
        EntryNotFoundError: If entry doesn't exist
    """
    logger.info(f"Getting entry: {entry_name}")

    entry = await repository.get_entry(
        database_path=session.database_path,
        password=password,
        entry_name=entry_name,
        keyfile=session.keyfile,
    )

    logger.info(f"Entry retrieved: {entry.title}")

    return EntryResponse(
        name=entry.name,
        title=entry.title,
        username=entry.username,
        url=entry.url,
        notes=entry.notes,
        tags=entry.tags,
        uuid=entry.uuid,
        group=entry.group,
        has_password=entry.has_password,
        password_length=entry.password_length,
        created_at=entry.created_at,
        modified_at=entry.modified_at,
    )


@router.get(
    "/{entry_name:path}/password",
    response_model=EntryPasswordResponse,
    status_code=status.HTTP_200_OK,
    summary="Get entry password",
    description="Get password for a specific entry (SENSITIVE - use with caution)",
)
async def get_entry_password(
    entry_name: str,
    session: CurrentSessionDep,
    password: DecryptedPasswordDep,
    repository: RepositoryDep,
) -> EntryPasswordResponse:
    """
    Get entry password.

    This endpoint returns the ACTUAL password.
    Use ONLY when explicitly requested by user.

    Args:
        entry_name: Entry name/path
        session: Current session
        password: Decrypted password
        repository: KeePassXC repository

    Returns:
        EntryPasswordResponse with password

    Raises:
        EntryNotFoundError: If entry doesn't exist
    """
    logger.info(f"Password requested for entry: {entry_name}")

    entry = await repository.get_entry(
        database_path=session.database_path,
        password=password,
        entry_name=entry_name,
        keyfile=session.keyfile,
    )

    logger.info(f"Password retrieved for entry: {entry.title}")

    return EntryPasswordResponse(password=entry.password)


@router.post(
    "",
    response_model=EntryResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create entry",
    description="Create a new password entry",
)
async def create_entry(
    request: EntryCreate,
    session: CurrentSessionDep,
    password: DecryptedPasswordDep,
    repository: RepositoryDep,
) -> EntryResponse:
    """
    Create a new entry.

    Args:
        request: Entry creation data
        session: Current session
        password: Decrypted password
        repository: KeePassXC repository

    Returns:
        EntryResponse for created entry (NO password)

    Raises:
        EntryAlreadyExistsError: If entry already exists
    """
    logger.info(f"Creating entry: {request.name}")

    # Create entry
    success = await repository.create_entry(
        database_path=session.database_path,
        password=password,
        entry_data={
            "title": request.name,
            "username": request.username,
            "password": request.password,
            "url": request.url,
            "notes": request.notes,
        },
        keyfile=session.keyfile,
    )

    if not success:
        raise ValueError("Failed to create entry")

    logger.info(f"Entry created: {request.name}")

    # Get created entry (to return full details)
    entry = await repository.get_entry(
        database_path=session.database_path,
        password=password,
        entry_name=request.name,
        keyfile=session.keyfile,
    )

    return EntryResponse(
        name=entry.name,
        title=entry.title,
        username=entry.username,
        url=entry.url,
        notes=entry.notes,
        tags=entry.tags,
        uuid=entry.uuid,
        group=entry.group,
        has_password=entry.has_password,
        password_length=entry.password_length,
        created_at=entry.created_at,
        modified_at=entry.modified_at,
    )


@router.put(
    "/{entry_name:path}",
    response_model=EntryResponse,
    status_code=status.HTTP_200_OK,
    summary="Update entry",
    description="Update an existing entry",
)
async def update_entry(
    entry_name: str,
    request: EntryUpdate,
    session: CurrentSessionDep,
    password: DecryptedPasswordDep,
    repository: RepositoryDep,
) -> EntryResponse:
    """
    Update an entry.

    Only provided fields will be updated.

    Args:
        entry_name: Entry name/path to update
        request: Update data
        session: Current session
        password: Decrypted password
        repository: KeePassXC repository

    Returns:
        EntryResponse with updated entry (NO password)

    Raises:
        EntryNotFoundError: If entry doesn't exist
    """
    logger.info(f"Updating entry: {entry_name}")

    # Build update data (only include provided fields)
    update_data = {}
    if request.username is not None:
        update_data["username"] = request.username
    if request.password is not None:
        update_data["password"] = request.password
    if request.url is not None:
        update_data["url"] = request.url

    # Update entry
    success = await repository.update_entry(
        database_path=session.database_path,
        password=password,
        entry_name=entry_name,
        new_data=update_data,
        keyfile=session.keyfile,
    )

    if not success:
        raise ValueError("Failed to update entry")

    logger.info(f"Entry updated: {entry_name}")

    # Get updated entry
    entry = await repository.get_entry(
        database_path=session.database_path,
        password=password,
        entry_name=entry_name,
        keyfile=session.keyfile,
    )

    return EntryResponse(
        name=entry.name,
        title=entry.title,
        username=entry.username,
        url=entry.url,
        notes=entry.notes,
        tags=entry.tags,
        uuid=entry.uuid,
        group=entry.group,
        has_password=entry.has_password,
        password_length=entry.password_length,
        created_at=entry.created_at,
        modified_at=entry.modified_at,
    )


@router.delete(
    "/{entry_name:path}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete entry",
    description="Delete a password entry",
)
async def delete_entry(
    entry_name: str,
    session: CurrentSessionDep,
    password: DecryptedPasswordDep,
    repository: RepositoryDep,
) -> None:
    """
    Delete an entry.

    Args:
        entry_name: Entry name/path to delete
        session: Current session
        password: Decrypted password
        repository: KeePassXC repository

    Raises:
        EntryNotFoundError: If entry doesn't exist
    """
    logger.info(f"Deleting entry: {entry_name}")

    success = await repository.delete_entry(
        database_path=session.database_path,
        password=password,
        entry_name=entry_name,
        keyfile=session.keyfile,
    )

    if not success:
        raise ValueError("Failed to delete entry")

    logger.info(f"Entry deleted: {entry_name}")
