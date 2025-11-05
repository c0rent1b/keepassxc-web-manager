"""
Cache service interface.

This interface defines the contract for caching operations.
Implementations can use Redis, memory, or other backends.
"""

from abc import ABC, abstractmethod
from typing import Any, Optional


class ICacheService(ABC):
    """
    Interface for cache operations.

    This is a port (in hexagonal architecture) that defines caching operations.
    Actual implementations (Redis, Memory) are in the infrastructure layer.
    """

    @abstractmethod
    async def get(self, key: str) -> Optional[Any]:
        """
        Get a value from cache.

        Args:
            key: Cache key

        Returns:
            Cached value or None if not found/expired
        """
        pass

    @abstractmethod
    async def set(
        self,
        key: str,
        value: Any,
        ttl: Optional[int] = None,
    ) -> bool:
        """
        Set a value in cache.

        Args:
            key: Cache key
            value: Value to cache (must be JSON-serializable)
            ttl: Time to live in seconds (None = default TTL)

        Returns:
            True if successful

        Raises:
            SensitiveDataError: If attempting to cache sensitive data
        """
        pass

    @abstractmethod
    async def delete(self, key: str) -> bool:
        """
        Delete a value from cache.

        Args:
            key: Cache key to delete

        Returns:
            True if deleted, False if key didn't exist
        """
        pass

    @abstractmethod
    async def clear(self) -> bool:
        """
        Clear all cache entries.

        Returns:
            True if successful

        Warning:
            This clears ALL cache entries, use with caution.
        """
        pass

    @abstractmethod
    async def exists(self, key: str) -> bool:
        """
        Check if a key exists in cache.

        Args:
            key: Cache key to check

        Returns:
            True if key exists and hasn't expired
        """
        pass

    @abstractmethod
    async def get_ttl(self, key: str) -> Optional[int]:
        """
        Get remaining TTL for a key.

        Args:
            key: Cache key

        Returns:
            Remaining seconds until expiration, or None if key doesn't exist
        """
        pass

    @abstractmethod
    async def increment(self, key: str, amount: int = 1) -> int:
        """
        Increment a numeric value in cache.

        Useful for rate limiting and counters.

        Args:
            key: Cache key
            amount: Amount to increment by

        Returns:
            New value after increment

        Raises:
            ValueError: If value is not numeric
        """
        pass

    @abstractmethod
    async def get_many(self, keys: list[str]) -> dict[str, Any]:
        """
        Get multiple values from cache at once.

        Args:
            keys: List of cache keys

        Returns:
            Dictionary mapping keys to values (missing keys are omitted)
        """
        pass

    @abstractmethod
    async def set_many(
        self,
        items: dict[str, Any],
        ttl: Optional[int] = None,
    ) -> bool:
        """
        Set multiple values in cache at once.

        Args:
            items: Dictionary mapping keys to values
            ttl: Time to live in seconds (None = default TTL)

        Returns:
            True if successful

        Raises:
            SensitiveDataError: If attempting to cache sensitive data
        """
        pass

    @abstractmethod
    async def delete_pattern(self, pattern: str) -> int:
        """
        Delete all keys matching a pattern.

        Args:
            pattern: Pattern to match (e.g., "user:*", "session:123:*")

        Returns:
            Number of keys deleted

        Warning:
            This can be expensive for large caches. Use specific keys when possible.
        """
        pass

    @abstractmethod
    async def health_check(self) -> bool:
        """
        Check if cache backend is healthy and accessible.

        Returns:
            True if cache is healthy, False otherwise
        """
        pass
