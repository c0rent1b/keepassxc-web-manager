"""
In-memory cache implementation.

Provides a simple in-memory cache as fallback when Redis is unavailable.
Uses Python dictionaries with TTL tracking.
"""

import asyncio
import logging
import time
from typing import Any, Optional

from app.core.exceptions import SensitiveDataError
from app.core.interfaces.cache import ICacheService

logger = logging.getLogger(__name__)


class MemoryCache(ICacheService):
    """
    In-memory cache implementation.

    Features:
    - TTL (Time To Live) support
    - Automatic expiration
    - Thread-safe operations
    - Pattern matching for bulk deletes

    Limitations:
    - Data is lost on restart
    - No persistence
    - Limited by available memory
    - Not shared across processes

    Security:
    - Validates that no sensitive data is cached
    """

    def __init__(self, default_ttl: int = 300, max_size: int = 10000):
        """
        Initialize memory cache.

        Args:
            default_ttl: Default TTL in seconds (5 minutes)
            max_size: Maximum number of cached items
        """
        self.default_ttl = default_ttl
        self.max_size = max_size

        # Cache storage: key -> (value, expiration_time)
        self._cache: dict[str, tuple[Any, float]] = {}

        # Lock for thread safety
        self._lock = asyncio.Lock()

        logger.info(
            f"Memory cache initialized (default_ttl: {default_ttl}s, max_size: {max_size})"
        )

    async def get(self, key: str) -> Optional[Any]:
        """
        Get a value from cache.

        Args:
            key: Cache key

        Returns:
            Cached value or None if not found/expired
        """
        async with self._lock:
            if key not in self._cache:
                logger.debug(f"Cache miss: {key}")
                return None

            value, expiration = self._cache[key]

            # Check if expired
            if expiration > 0 and time.time() > expiration:
                logger.debug(f"Cache expired: {key}")
                del self._cache[key]
                return None

            logger.debug(f"Cache hit: {key}")
            return value

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
            value: Value to cache
            ttl: Time to live in seconds (None = default TTL)

        Returns:
            True if successful

        Raises:
            SensitiveDataError: If attempting to cache sensitive data
        """
        # Security check: prevent sensitive data
        self._validate_not_sensitive(key, value)

        async with self._lock:
            # Check max size
            if len(self._cache) >= self.max_size and key not in self._cache:
                # Evict oldest entries (simple FIFO)
                logger.warning(
                    f"Cache full ({self.max_size} items), evicting oldest entry"
                )
                oldest_key = next(iter(self._cache))
                del self._cache[oldest_key]

            # Calculate expiration
            ttl_seconds = ttl if ttl is not None else self.default_ttl
            expiration = time.time() + ttl_seconds if ttl_seconds > 0 else 0

            # Store value
            self._cache[key] = (value, expiration)

            logger.debug(f"Cache set: {key} (TTL: {ttl_seconds}s)")

            return True

    async def delete(self, key: str) -> bool:
        """
        Delete a value from cache.

        Args:
            key: Cache key to delete

        Returns:
            True if deleted, False if key didn't exist
        """
        async with self._lock:
            if key in self._cache:
                del self._cache[key]
                logger.debug(f"Cache deleted: {key}")
                return True

            return False

    async def clear(self) -> bool:
        """
        Clear all cache entries.

        Returns:
            True if successful
        """
        async with self._lock:
            count = len(self._cache)
            self._cache.clear()
            logger.info(f"Cache cleared: {count} items removed")
            return True

    async def exists(self, key: str) -> bool:
        """
        Check if a key exists in cache.

        Args:
            key: Cache key to check

        Returns:
            True if key exists and hasn't expired
        """
        value = await self.get(key)
        return value is not None

    async def get_ttl(self, key: str) -> Optional[int]:
        """
        Get remaining TTL for a key.

        Args:
            key: Cache key

        Returns:
            Remaining seconds until expiration, or None if key doesn't exist
        """
        async with self._lock:
            if key not in self._cache:
                return None

            value, expiration = self._cache[key]

            if expiration == 0:  # No expiration
                return -1

            remaining = int(expiration - time.time())

            if remaining <= 0:
                # Already expired, remove it
                del self._cache[key]
                return None

            return remaining

    async def increment(self, key: str, amount: int = 1) -> int:
        """
        Increment a numeric value in cache.

        Args:
            key: Cache key
            amount: Amount to increment by

        Returns:
            New value after increment

        Raises:
            ValueError: If value is not numeric
        """
        async with self._lock:
            current_value = 0

            if key in self._cache:
                value, expiration = self._cache[key]

                # Check expiration
                if expiration > 0 and time.time() > expiration:
                    del self._cache[key]
                else:
                    if not isinstance(value, (int, float)):
                        raise ValueError(f"Value for key '{key}' is not numeric")
                    current_value = value

            # Increment
            new_value = current_value + amount

            # Store with default TTL
            expiration = time.time() + self.default_ttl
            self._cache[key] = (new_value, expiration)

            logger.debug(f"Cache incremented: {key} = {new_value}")

            return new_value

    async def get_many(self, keys: list[str]) -> dict[str, Any]:
        """
        Get multiple values from cache at once.

        Args:
            keys: List of cache keys

        Returns:
            Dictionary mapping keys to values (missing keys are omitted)
        """
        result = {}

        for key in keys:
            value = await self.get(key)
            if value is not None:
                result[key] = value

        logger.debug(f"Cache get_many: {len(result)}/{len(keys)} keys found")

        return result

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
        for key, value in items.items():
            await self.set(key, value, ttl)

        logger.debug(f"Cache set_many: {len(items)} items")

        return True

    async def delete_pattern(self, pattern: str) -> int:
        """
        Delete all keys matching a pattern.

        Args:
            pattern: Pattern to match (supports * wildcard)

        Returns:
            Number of keys deleted
        """
        import fnmatch

        async with self._lock:
            matching_keys = [
                key for key in self._cache.keys() if fnmatch.fnmatch(key, pattern)
            ]

            for key in matching_keys:
                del self._cache[key]

            logger.info(f"Cache delete_pattern: {len(matching_keys)} keys deleted")

            return len(matching_keys)

    async def health_check(self) -> bool:
        """
        Check if cache is healthy.

        Returns:
            Always True for memory cache
        """
        return True

    def get_stats(self) -> dict[str, Any]:
        """
        Get cache statistics.

        Returns:
            Dictionary with cache stats
        """
        total_items = len(self._cache)
        expired_items = 0
        now = time.time()

        for value, expiration in self._cache.values():
            if expiration > 0 and now > expiration:
                expired_items += 1

        return {
            "total_items": total_items,
            "active_items": total_items - expired_items,
            "expired_items": expired_items,
            "max_size": self.max_size,
            "utilization": round((total_items / self.max_size) * 100, 2),
        }

    async def cleanup_expired(self) -> int:
        """
        Remove expired entries from cache.

        Returns:
            Number of entries removed
        """
        async with self._lock:
            now = time.time()
            expired_keys = []

            for key, (value, expiration) in self._cache.items():
                if expiration > 0 and now > expiration:
                    expired_keys.append(key)

            for key in expired_keys:
                del self._cache[key]

            if expired_keys:
                logger.info(f"Cache cleanup: {len(expired_keys)} expired items removed")

            return len(expired_keys)

    @staticmethod
    def _validate_not_sensitive(key: str, value: Any) -> None:
        """
        Validate that data being cached is not sensitive.

        Args:
            key: Cache key
            value: Value to cache

        Raises:
            SensitiveDataError: If sensitive data detected
        """
        # Check key for sensitive keywords
        sensitive_keywords = [
            "password",
            "passwd",
            "pwd",
            "secret",
            "token",
            "key",
            "private",
            "credential",
            "masterpassword",
        ]

        key_lower = key.lower()
        for keyword in sensitive_keywords:
            if keyword in key_lower:
                raise SensitiveDataError(
                    field_name=key,
                    location="cache",
                )

        # Check if value is a dict with sensitive keys
        if isinstance(value, dict):
            for dict_key in value.keys():
                dict_key_lower = str(dict_key).lower()
                for keyword in sensitive_keywords:
                    if keyword in dict_key_lower:
                        raise SensitiveDataError(
                            field_name=dict_key,
                            location="cache",
                        )
