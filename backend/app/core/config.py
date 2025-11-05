"""
Application configuration using Pydantic Settings.

Manages all configuration from environment variables with validation
and type safety.
"""

import logging
from functools import lru_cache
from pathlib import Path
from typing import Any, Literal, Optional

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

logger = logging.getLogger(__name__)


class Settings(BaseSettings):
    """
    Application settings loaded from environment variables.

    Configuration priority:
    1. Environment variables
    2. .env file
    3. Default values

    Security:
    - SECRET_KEY must be 32+ characters in production
    - ALLOW_SENSITIVE_DATA_IN_DB must ALWAYS be False
    """

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # =========================================================================
    # Application
    # =========================================================================

    APP_NAME: str = Field(
        default="KeePassXC Web Manager",
        description="Application name",
    )

    APP_VERSION: str = Field(
        default="2.0.0-alpha",
        description="Application version",
    )

    APP_DESCRIPTION: str = Field(
        default="Modern web interface for KeePassXC database management",
        description="Application description",
    )

    ENVIRONMENT: Literal["development", "production", "test"] = Field(
        default="development",
        description="Runtime environment",
    )

    DEBUG: bool = Field(
        default=False,
        description="Enable debug mode (verbose logging, auto-reload)",
    )

    LOG_LEVEL: Literal["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"] = Field(
        default="INFO",
        description="Logging level",
    )

    # =========================================================================
    # Security - CRITICAL
    # =========================================================================

    SECRET_KEY: str = Field(
        default="CHANGE-ME-IN-PRODUCTION-USE-RANDOM-32-CHARS-MINIMUM",
        description="Secret key for encryption and JWT signing (32+ chars required)",
        min_length=32,
    )

    SESSION_TIMEOUT: int = Field(
        default=1800,
        description="Session timeout in seconds (30 minutes default)",
        ge=300,  # Minimum 5 minutes
        le=86400,  # Maximum 24 hours
    )

    MAX_PASSWORD_AGE: int = Field(
        default=3600,
        description="Maximum age for encrypted passwords in seconds (1 hour default)",
        ge=300,
        le=86400,
    )

    ALLOW_SENSITIVE_DATA_IN_DB: bool = Field(
        default=False,
        description="MUST BE FALSE - prevents sensitive data in SQLite",
    )

    CORS_ORIGINS: list[str] = Field(
        default=["http://localhost:3000", "http://localhost:8000"],
        description="Allowed CORS origins",
    )

    CORS_ALLOW_CREDENTIALS: bool = Field(
        default=True,
        description="Allow credentials in CORS requests",
    )

    # =========================================================================
    # KeePassXC
    # =========================================================================

    KEEPASSXC_CLI_PATH: str = Field(
        default="keepassxc-cli",
        description="Path to keepassxc-cli executable",
    )

    KEEPASSXC_COMMAND_TIMEOUT: int = Field(
        default=30,
        description="Default timeout for keepassxc-cli commands in seconds",
        ge=5,
        le=300,
    )

    KEEPASSXC_DATABASES_PATH: Optional[str] = Field(
        default=None,
        description="Default directory for KeePassXC databases (optional)",
    )

    # =========================================================================
    # Database (SQLite for metadata ONLY)
    # =========================================================================

    DATABASE_URL: str = Field(
        default="sqlite+aiosqlite:///./data/keepass_metadata.db",
        description="SQLite database URL for metadata storage",
    )

    DATABASE_ECHO: bool = Field(
        default=False,
        description="Echo SQL queries (for debugging)",
    )

    # =========================================================================
    # Cache (Redis with fallback)
    # =========================================================================

    CACHE_BACKEND: Literal["redis", "memory"] = Field(
        default="redis",
        description="Cache backend to use",
    )

    REDIS_URL: str = Field(
        default="redis://localhost:6379/0",
        description="Redis connection URL",
    )

    CACHE_DEFAULT_TTL: int = Field(
        default=300,
        description="Default cache TTL in seconds (5 minutes)",
        ge=10,
        le=86400,
    )

    CACHE_KEY_PREFIX: str = Field(
        default="kpxc:",
        description="Prefix for all cache keys",
    )

    # =========================================================================
    # API
    # =========================================================================

    API_V1_PREFIX: str = Field(
        default="/api/v1",
        description="API v1 prefix",
    )

    API_TITLE: str = Field(
        default="KeePassXC Web Manager API",
        description="API documentation title",
    )

    API_DOCS_ENABLED: bool = Field(
        default=True,
        description="Enable API documentation (Swagger/ReDoc)",
    )

    MAX_REQUEST_SIZE: int = Field(
        default=1048576,  # 1 MB
        description="Maximum request body size in bytes",
    )

    # =========================================================================
    # Rate Limiting
    # =========================================================================

    RATE_LIMIT_ENABLED: bool = Field(
        default=True,
        description="Enable rate limiting",
    )

    RATE_LIMIT_LOGIN: int = Field(
        default=5,
        description="Max login attempts per window",
        ge=1,
    )

    RATE_LIMIT_API: int = Field(
        default=100,
        description="Max API calls per window",
        ge=10,
    )

    RATE_LIMIT_WINDOW: int = Field(
        default=60,
        description="Rate limit window in seconds",
        ge=10,
    )

    # =========================================================================
    # Frontend
    # =========================================================================

    FRONTEND_DIR: str = Field(
        default="frontend/public",
        description="Frontend static files directory",
    )

    FRONTEND_TEMPLATES_DIR: str = Field(
        default="frontend/templates",
        description="Frontend templates directory",
    )

    # =========================================================================
    # Validators
    # =========================================================================

    @field_validator("ALLOW_SENSITIVE_DATA_IN_DB")
    @classmethod
    def validate_no_sensitive_data(cls, v: bool) -> bool:
        """CRITICAL: Ensure sensitive data is never allowed in database."""
        if v is True:
            raise ValueError(
                "ALLOW_SENSITIVE_DATA_IN_DB must be False - "
                "Storing sensitive data in SQLite is FORBIDDEN"
            )
        return v

    @field_validator("SECRET_KEY")
    @classmethod
    def validate_secret_key(cls, v: str) -> str:
        """Validate secret key strength."""
        if len(v) < 32:
            raise ValueError("SECRET_KEY must be at least 32 characters")

        # Warn if using default in production
        if "CHANGE-ME" in v:
            logger.warning(
                "Using default SECRET_KEY - CHANGE THIS IN PRODUCTION!"
            )

        return v

    @field_validator("DATABASE_URL")
    @classmethod
    def validate_database_url(cls, v: str) -> str:
        """Validate database URL is SQLite."""
        if not v.startswith("sqlite"):
            raise ValueError(
                "Only SQLite databases are supported for metadata storage"
            )
        return v

    @field_validator("KEEPASSXC_DATABASES_PATH")
    @classmethod
    def validate_databases_path(cls, v: Optional[str]) -> Optional[str]:
        """Validate databases path exists if provided."""
        if v is not None:
            path = Path(v)
            if not path.exists():
                logger.warning(
                    f"KEEPASSXC_DATABASES_PATH does not exist: {v}"
                )
        return v

    # =========================================================================
    # Computed Properties
    # =========================================================================

    @property
    def is_production(self) -> bool:
        """Check if running in production."""
        return self.ENVIRONMENT == "production"

    @property
    def is_development(self) -> bool:
        """Check if running in development."""
        return self.ENVIRONMENT == "development"

    @property
    def is_test(self) -> bool:
        """Check if running in test mode."""
        return self.ENVIRONMENT == "test"

    @property
    def docs_url(self) -> Optional[str]:
        """Get API docs URL (None if disabled)."""
        return "/docs" if self.API_DOCS_ENABLED else None

    @property
    def redoc_url(self) -> Optional[str]:
        """Get ReDoc URL (None if disabled)."""
        return "/redoc" if self.API_DOCS_ENABLED else None

    @property
    def openapi_url(self) -> Optional[str]:
        """Get OpenAPI schema URL (None if docs disabled)."""
        return f"{self.API_V1_PREFIX}/openapi.json" if self.API_DOCS_ENABLED else None

    # =========================================================================
    # Methods
    # =========================================================================

    def get_database_path(self) -> Path:
        """
        Get database file path.

        Returns:
            Path to SQLite database file
        """
        # Extract path from URL (sqlite+aiosqlite:///./path/to/db.db)
        db_path = self.DATABASE_URL.split("///")[-1]
        return Path(db_path)

    def ensure_directories(self) -> None:
        """
        Ensure all required directories exist.

        Creates:
        - Database directory
        - Frontend directories
        - Databases path (if configured)
        """
        # Database directory
        db_path = self.get_database_path()
        db_path.parent.mkdir(parents=True, exist_ok=True)
        logger.info(f"Database directory: {db_path.parent}")

        # Frontend directories
        frontend_dir = Path(self.FRONTEND_DIR)
        frontend_dir.mkdir(parents=True, exist_ok=True)
        logger.info(f"Frontend directory: {frontend_dir}")

        templates_dir = Path(self.FRONTEND_TEMPLATES_DIR)
        templates_dir.mkdir(parents=True, exist_ok=True)
        logger.info(f"Templates directory: {templates_dir}")

        # Databases path (if configured)
        if self.KEEPASSXC_DATABASES_PATH:
            databases_path = Path(self.KEEPASSXC_DATABASES_PATH)
            databases_path.mkdir(parents=True, exist_ok=True)
            logger.info(f"Databases path: {databases_path}")

    def configure_logging(self) -> None:
        """Configure logging based on settings."""
        log_level = getattr(logging, self.LOG_LEVEL)

        # Configure root logger
        logging.basicConfig(
            level=log_level,
            format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        )

        # Set specific loggers
        logging.getLogger("uvicorn").setLevel(log_level)
        logging.getLogger("fastapi").setLevel(log_level)

        # Reduce noise from external libraries in production
        if self.is_production:
            logging.getLogger("asyncio").setLevel(logging.WARNING)
            logging.getLogger("urllib3").setLevel(logging.WARNING)

        logger.info(f"Logging configured: {self.LOG_LEVEL}")

    def model_dump_safe(self) -> dict[str, Any]:
        """
        Dump settings safely (hides SECRET_KEY).

        Returns:
            Dictionary with settings (SECRET_KEY redacted)
        """
        data = self.model_dump()

        # Redact sensitive data
        if "SECRET_KEY" in data:
            data["SECRET_KEY"] = "*" * 8

        return data


@lru_cache
def get_settings() -> Settings:
    """
    Get cached settings instance.

    Returns:
        Settings singleton

    Note:
        Uses lru_cache for singleton pattern - settings are loaded once
    """
    settings = Settings()

    # Configure logging
    settings.configure_logging()

    # Ensure directories
    settings.ensure_directories()

    # Log configuration (safe)
    logger.info(f"Settings loaded: Environment={settings.ENVIRONMENT}")
    logger.debug(f"Configuration: {settings.model_dump_safe()}")

    return settings
