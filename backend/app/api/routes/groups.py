"""
Group endpoints.

Handles group/folder operations.
"""

import logging

from fastapi import APIRouter, status

from app.api.dependencies import (
    CurrentSessionDep,
    DecryptedPasswordDep,
    RepositoryDep,
)
from app.api.schemas import GroupList, GroupResponse

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get(
    "",
    response_model=GroupList,
    status_code=status.HTTP_200_OK,
    summary="List groups",
    description="List all groups/folders in the database",
)
async def list_groups(
    session: CurrentSessionDep,
    password: DecryptedPasswordDep,
    repository: RepositoryDep,
) -> GroupList:
    """
    List all groups.

    Groups are folders/categories that organize entries.

    Args:
        session: Current session
        password: Decrypted password
        repository: KeePassXC repository

    Returns:
        GroupList with all groups
    """
    logger.info(f"Listing groups for: {session.database_path}")

    groups = await repository.list_groups(
        database_path=session.database_path,
        password=password,
        keyfile=session.keyfile,
    )

    logger.info(f"Found {len(groups)} groups")

    group_responses = [
        GroupResponse(
            name=group.name,
            path=group.path,
            parent=group.parent,
            entry_count=group.entry_count,
            subgroups=group.subgroups,
            depth=group.depth,
            is_root=group.is_root,
        )
        for group in groups
    ]

    return GroupList(
        groups=group_responses,
        total=len(group_responses),
    )
