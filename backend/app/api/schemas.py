"""
Pydantic schemas for API requests and responses.

All schemas are designed to:
- Never include sensitive data (passwords, tokens) in responses
- Validate input data strictly
- Provide clear documentation
"""

from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, Field, field_validator


# =============================================================================
# Authentication Schemas
# =============================================================================


class LoginRequest(BaseModel):
    """Login request with database credentials."""

    database_path: str = Field(
        ...,
        description="Path to KeePassXC database file (.kdbx)",
        examples=["/path/to/database.kdbx"],
    )

    password: str = Field(
        ...,
        description="Master password for the database",
        min_length=1,
    )

    keyfile: Optional[str] = Field(
        None,
        description="Optional path to key file",
        examples=["/path/to/keyfile.key"],
    )

    @field_validator("database_path")
    @classmethod
    def validate_database_path(cls, v: str) -> str:
        """Validate database path has .kdbx extension."""
        if not v.endswith(".kdbx"):
            raise ValueError("Database path must end with .kdbx")
        return v


class LoginResponse(BaseModel):
    """Login response with session token."""

    token: str = Field(
        ...,
        description="JWT session token",
    )

    session_id: str = Field(
        ...,
        description="Session ID",
    )

    expires_in: int = Field(
        ...,
        description="Token expiration in seconds",
    )

    database_path: str = Field(
        ...,
        description="Path to authenticated database",
    )


class RefreshTokenResponse(BaseModel):
    """Refresh token response."""

    token: str = Field(
        ...,
        description="New JWT session token",
    )

    expires_in: int = Field(
        ...,
        description="Token expiration in seconds",
    )


class LogoutResponse(BaseModel):
    """Logout response."""

    message: str = Field(
        default="Logged out successfully",
        description="Success message",
    )


# =============================================================================
# Database Schemas
# =============================================================================


class DatabaseInfo(BaseModel):
    """Database metadata (NO sensitive data)."""

    path: str = Field(
        ...,
        description="Database file path",
    )

    name: Optional[str] = Field(
        None,
        description="Database name",
    )

    filename: str = Field(
        ...,
        description="Database filename",
    )

    file_size: int = Field(
        default=0,
        description="File size in bytes",
    )

    file_size_mb: float = Field(
        ...,
        description="File size in megabytes",
    )

    entry_count: int = Field(
        default=0,
        description="Number of entries in database",
    )

    has_keyfile: bool = Field(
        default=False,
        description="Whether database uses a keyfile",
    )

    is_locked: bool = Field(
        default=True,
        description="Whether database is currently locked",
    )


class DatabaseTestRequest(BaseModel):
    """Test database connection request."""

    database_path: str = Field(
        ...,
        description="Path to database file",
    )

    password: str = Field(
        ...,
        description="Master password",
    )

    keyfile: Optional[str] = Field(
        None,
        description="Optional keyfile path",
    )


class DatabaseTestResponse(BaseModel):
    """Test connection response."""

    success: bool = Field(
        ...,
        description="Whether connection test succeeded",
    )

    message: str = Field(
        ...,
        description="Result message",
    )

    database_info: Optional[DatabaseInfo] = Field(
        None,
        description="Database info if connection succeeded",
    )


# =============================================================================
# Entry Schemas
# =============================================================================


class EntryBase(BaseModel):
    """Base entry schema (shared fields)."""

    name: str = Field(
        ...,
        description="Entry name/path",
        min_length=1,
    )

    title: str = Field(
        ...,
        description="Entry title",
        min_length=1,
    )

    username: str = Field(
        default="",
        description="Username",
    )

    url: str = Field(
        default="",
        description="URL",
    )

    notes: str = Field(
        default="",
        description="Notes",
    )

    tags: list[str] = Field(
        default_factory=list,
        description="Tags",
    )


class EntryCreate(EntryBase):
    """Create entry request (includes password)."""

    password: str = Field(
        ...,
        description="Entry password",
        min_length=1,
    )


class EntryUpdate(BaseModel):
    """Update entry request (all fields optional)."""

    title: Optional[str] = Field(
        None,
        description="New title",
    )

    username: Optional[str] = Field(
        None,
        description="New username",
    )

    password: Optional[str] = Field(
        None,
        description="New password",
    )

    url: Optional[str] = Field(
        None,
        description="New URL",
    )

    notes: Optional[str] = Field(
        None,
        description="New notes",
    )


class EntryResponse(EntryBase):
    """
    Entry response (SAFE - NO password).

    This schema is used for API responses and NEVER includes the password.
    """

    uuid: Optional[UUID] = Field(
        None,
        description="Entry UUID",
    )

    group: str = Field(
        default="",
        description="Group/folder path",
    )

    has_password: bool = Field(
        ...,
        description="Whether entry has a password (boolean only, not the password itself)",
    )

    password_length: int = Field(
        default=0,
        description="Length of password (for UI indicators)",
    )

    created_at: Optional[datetime] = Field(
        None,
        description="Creation timestamp",
    )

    modified_at: Optional[datetime] = Field(
        None,
        description="Last modification timestamp",
    )

    model_config = {
        "json_schema_extra": {
            "example": {
                "name": "Work/GitHub",
                "title": "GitHub",
                "username": "user@example.com",
                "url": "https://github.com",
                "notes": "Work account",
                "tags": ["work", "dev"],
                "uuid": "12345678-1234-5678-1234-567812345678",
                "group": "Work",
                "has_password": True,
                "password_length": 16,
            }
        }
    }


class EntryPasswordResponse(BaseModel):
    """
    Entry password response.

    ONLY used for explicit "get password" requests.
    NEVER included in list/search responses.
    """

    password: str = Field(
        ...,
        description="Entry password (SENSITIVE - use with caution)",
    )


class EntryList(BaseModel):
    """List of entries."""

    entries: list[EntryResponse] = Field(
        ...,
        description="List of entries (NO passwords)",
    )

    total: int = Field(
        ...,
        description="Total number of entries",
    )


# =============================================================================
# Group Schemas
# =============================================================================


class GroupResponse(BaseModel):
    """Group/folder response."""

    name: str = Field(
        ...,
        description="Group name",
    )

    path: str = Field(
        ...,
        description="Full group path",
    )

    parent: Optional[str] = Field(
        None,
        description="Parent group path",
    )

    entry_count: int = Field(
        default=0,
        description="Number of entries in group",
    )

    subgroups: list[str] = Field(
        default_factory=list,
        description="List of subgroup paths",
    )

    depth: int = Field(
        ...,
        description="Depth in hierarchy (0 = root)",
    )

    is_root: bool = Field(
        ...,
        description="Whether this is a root group",
    )


class GroupList(BaseModel):
    """List of groups."""

    groups: list[GroupResponse] = Field(
        ...,
        description="List of groups",
    )

    total: int = Field(
        ...,
        description="Total number of groups",
    )


# =============================================================================
# Password Generator Schemas
# =============================================================================


class PasswordGenerateRequest(BaseModel):
    """Password generation request."""

    length: int = Field(
        default=16,
        description="Password length",
        ge=8,
        le=128,
    )

    include_symbols: bool = Field(
        default=True,
        description="Include special symbols (!@#$%^&*)",
    )

    include_numbers: bool = Field(
        default=True,
        description="Include numbers (0-9)",
    )

    include_uppercase: bool = Field(
        default=True,
        description="Include uppercase letters (A-Z)",
    )

    include_lowercase: bool = Field(
        default=True,
        description="Include lowercase letters (a-z)",
    )

    exclude_ambiguous: bool = Field(
        default=False,
        description="Exclude ambiguous characters (0/O, 1/l/I)",
    )


class PasswordGenerateResponse(BaseModel):
    """Password generation response."""

    password: str = Field(
        ...,
        description="Generated password",
    )

    length: int = Field(
        ...,
        description="Password length",
    )

    strength: dict = Field(
        ...,
        description="Password strength analysis",
    )


# =============================================================================
# Error Schemas
# =============================================================================


class ErrorResponse(BaseModel):
    """Standard error response."""

    error: str = Field(
        ...,
        description="Error type",
    )

    message: str = Field(
        ...,
        description="Error message",
    )

    details: Optional[dict] = Field(
        None,
        description="Additional error details",
    )

    timestamp: datetime = Field(
        default_factory=datetime.utcnow,
        description="Error timestamp",
    )


# =============================================================================
# Health Check Schemas
# =============================================================================


class HealthCheckResponse(BaseModel):
    """Health check response."""

    status: str = Field(
        ...,
        description="Service status (healthy/unhealthy)",
    )

    version: str = Field(
        ...,
        description="Application version",
    )

    keepassxc_available: bool = Field(
        ...,
        description="Whether keepassxc-cli is available",
    )

    cache_healthy: bool = Field(
        ...,
        description="Whether cache is healthy",
    )

    timestamp: datetime = Field(
        default_factory=datetime.utcnow,
        description="Check timestamp",
    )
