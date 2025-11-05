"""
Redis cache implementation.

Provides Redis-based caching with automatic fallback to memory cache
if Redis is unavailable.
"""

import json
import logging
from typing import Any, Optional

from redis import asyncio as aioredis

from app.core.exceptions import CacheException, SensitiveDataError
from app.core.interfaces.cache import ICacheService
from app.infrastructure.cache.memory_cache import MemoryCache

logger = logging.getLogger(__name__)


class RedisCache(ICacheService):
    """
    Redis cache implementation with fallback.

    Features:
    - Async Redis operations
    - JSON serialization
    - Automatic fallback to memory cache
    - Connection pooling
    - Health checking

    Security:
    - Validates that no sensitive data is cached
    - Encrypted connections supported (configure via URL)
    """

    def __init__(
        self,
        redis_url: str = "redis://localhost:6379/0",
        default_ttl: int = 300,
        key_prefix: str = "kpxc:",
        use_fallback: bool = True,
    ):
        """
        Initialize Redis cache.

        Args:
            redis_url: Redis connection URL
            default_ttl: Default TTL in seconds (5 minutes)
            key_prefix: Prefix for all cache keys
            use_fallback: Use memory cache as fallback if Redis unavailable
        """
        self.redis_url = redis_url
        self.default_ttl = default_ttl
        self.key_prefix = key_prefix
        self.use_fallback = use_fallback

        # Redis client (initialized on first use)
        self._redis: Optional[aioredis.Redis] = None
        self._connected = False

        # Fallback cache
        self._fallback_cache = MemoryCache(default_ttl=default_ttl) if use_fallback else None

        logger.info(
            f"Redis cache initialized (URL: {redis_url}, "
            f"fallback: {use_fallback})"
        )

    async def _get_redis(self) -> aioredis.Redis:
        """
        Get Redis client, initializing if needed.

        Returns:
            Redis client

        Raises:
            CacheException: If Redis unavailable and no fallback
        """
        if self._redis is None:
            try:
                self._redis = await aioredis.from_url(
                    self.redis_url,
                    encoding="utf-8",
                    decode_responses=True,
                )

                # Test connection
                await self._redis.ping()
                self._connected = True

                logger.info("Redis connection established")

            except Exception as e:
                logger.error(f"Redis connection failed: {str(e)}")
                self._connected = False

                if not self.use_fallback:
                    raise CacheException(f"Redis unavailable: {str(e)}") from e

        return self._redis

    def _make_key(self, key: str) -> str:
        """
        Add prefix to cache key.

        Args:
            key: Original key

        Returns:
            Prefixed key
        """
        return f"{self.key_prefix}{key}"

    async def get(self, key: str) -> Optional[Any]:
        """
        Get a value from cache.

        Args:
            key: Cache key

        Returns:
            Cached value or None if not found/expired
        """
        try:
            redis = await self._get_redis()

            if not self._connected:
                # Use fallback
                if self._fallback_cache:
                    return await self._fallback_cache.get(key)
                return None

            full_key = self._make_key(key)
            value_str = await redis.get(full_key)

            if value_str is None:
                logger.debug(f"Cache miss: {key}")
                return None

            # Deserialize JSON
            value = json.loads(value_str)

            logger.debug(f"Cache hit: {key}")
            return value

        except Exception as e:
            logger.error(f"Redis get failed: {str(e)}")

            # Fallback to memory cache
            if self._fallback_cache:
                return await self._fallback_cache.get(key)

            return None

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
        # Security check
        self._validate_not_sensitive(key, value)

        try:
            redis = await self._get_redis()

            if not self._connected:
                # Use fallback
                if self._fallback_cache:
                    return await self._fallback_cache.set(key, value, ttl)
                return False

            full_key = self._make_key(key)
            ttl_seconds = ttl if ttl is not None else self.default_ttl

            # Serialize to JSON
            value_str = json.dumps(value)

            # Set with TTL
            if ttl_seconds > 0:
                await redis.setex(full_key, ttl_seconds, value_str)
            else:
                await redis.set(full_key, value_str)

            logger.debug(f"Cache set: {key} (TTL: {ttl_seconds}s)")

            return True

        except Exception as e:
            logger.error(f"Redis set failed: {str(e)}")

            # Fallback to memory cache
            if self._fallback_cache:
                return await self._fallback_cache.set(key, value, ttl)

            return False

    async def delete(self, key: str) -> bool:
        """
        Delete a value from cache.

        Args:
            key: Cache key to delete

        Returns:
            True if deleted, False if key didn't exist
        """
        try:
            redis = await self._get_redis()

            if not self._connected:
                if self._fallback_cache:
                    return await self._fallback_cache.delete(key)
                return False

            full_key = self._make_key(key)
            deleted = await redis.delete(full_key)

            logger.debug(f"Cache deleted: {key}")

            return deleted > 0

        except Exception as e:
            logger.error(f"Redis delete failed: {str(e)}")

            if self._fallback_cache:
                return await self._fallback_cache.delete(key)

            return False

    async def clear(self) -> bool:
        """
        Clear all cache entries with our prefix.

        Returns:
            True if successful
        """
        try:
            redis = await self._get_redis()

            if not self._connected:
                if self._fallback_cache:
                    return await self._fallback_cache.clear()
                return False

            # Find all keys with prefix
            pattern = f"{self.key_prefix}*"
            keys = []
            async for key in redis.scan_iter(match=pattern):
                keys.append(key)

            if keys:
                await redis.delete(*keys)
                logger.info(f"Cache cleared: {len(keys)} items removed")

            return True

        except Exception as e:
            logger.error(f"Redis clear failed: {str(e)}")

            if self._fallback_cache:
                return await self._fallback_cache.clear()

            return False

    async def exists(self, key: str) -> bool:
        """
        Check if a key exists in cache.

        Args:
            key: Cache key to check

        Returns:
            True if key exists
        """
        try:
            redis = await self._get_redis()

            if not self._connected:
                if self._fallback_cache:
                    return await self._fallback_cache.exists(key)
                return False

            full_key = self._make_key(key)
            exists = await redis.exists(full_key)

            return exists > 0

        except Exception as e:
            logger.error(f"Redis exists failed: {str(e)}")

            if self._fallback_cache:
                return await self._fallback_cache.exists(key)

            return False

    async def get_ttl(self, key: str) -> Optional[int]:
        """
        Get remaining TTL for a key.

        Args:
            key: Cache key

        Returns:
            Remaining seconds until expiration, or None if key doesn't exist
        """
        try:
            redis = await self._get_redis()

            if not self._connected:
                if self._fallback_cache:
                    return await self._fallback_cache.get_ttl(key)
                return None

            full_key = self._make_key(key)
            ttl = await redis.ttl(full_key)

            if ttl < 0:  # -1 = no expiry, -2 = key doesn't exist
                return None

            return ttl

        except Exception as e:
            logger.error(f"Redis get_ttl failed: {str(e)}")

            if self._fallback_cache:
                return await self._fallback_cache.get_ttl(key)

            return None

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
        try:
            redis = await self._get_redis()

            if not self._connected:
                if self._fallback_cache:
                    return await self._fallback_cache.increment(key, amount)
                return amount

            full_key = self._make_key(key)
            new_value = await redis.incrby(full_key, amount)

            # Set TTL if this is a new key
            ttl = await redis.ttl(full_key)
            if ttl < 0:
                await redis.expire(full_key, self.default_ttl)

            logger.debug(f"Cache incremented: {key} = {new_value}")

            return new_value

        except Exception as e:
            logger.error(f"Redis increment failed: {str(e)}")

            if self._fallback_cache:
                return await self._fallback_cache.increment(key, amount)

            raise ValueError(f"Increment failed: {str(e)}")

    async def get_many(self, keys: list[str]) -> dict[str, Any]:
        """
        Get multiple values from cache at once.

        Args:
            keys: List of cache keys

        Returns:
            Dictionary mapping keys to values (missing keys are omitted)
        """
        try:
            redis = await self._get_redis()

            if not self._connected:
                if self._fallback_cache:
                    return await self._fallback_cache.get_many(keys)
                return {}

            full_keys = [self._make_key(key) for key in keys]
            values = await redis.mget(full_keys)

            result = {}
            for key, value_str in zip(keys, values):
                if value_str is not None:
                    result[key] = json.loads(value_str)

            logger.debug(f"Cache get_many: {len(result)}/{len(keys)} keys found")

            return result

        except Exception as e:
            logger.error(f"Redis get_many failed: {str(e)}")

            if self._fallback_cache:
                return await self._fallback_cache.get_many(keys)

            return {}

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
        # Validate all items first
        for key, value in items.items():
            self._validate_not_sensitive(key, value)

        try:
            redis = await self._get_redis()

            if not self._connected:
                if self._fallback_cache:
                    return await self._fallback_cache.set_many(items, ttl)
                return False

            # Set all items
            for key, value in items.items():
                await self.set(key, value, ttl)

            logger.debug(f"Cache set_many: {len(items)} items")

            return True

        except Exception as e:
            logger.error(f"Redis set_many failed: {str(e)}")

            if self._fallback_cache:
                return await self._fallback_cache.set_many(items, ttl)

            return False

    async def delete_pattern(self, pattern: str) -> int:
        """
        Delete all keys matching a pattern.

        Args:
            pattern: Pattern to match (e.g., "user:*", "session:123:*")

        Returns:
            Number of keys deleted
        """
        try:
            redis = await self._get_redis()

            if not self._connected:
                if self._fallback_cache:
                    return await self._fallback_cache.delete_pattern(pattern)
                return 0

            # Add prefix to pattern
            full_pattern = self._make_key(pattern)

            # Find matching keys
            keys = []
            async for key in redis.scan_iter(match=full_pattern):
                keys.append(key)

            # Delete matching keys
            if keys:
                deleted = await redis.delete(*keys)
                logger.info(f"Cache delete_pattern: {deleted} keys deleted")
                return deleted

            return 0

        except Exception as e:
            logger.error(f"Redis delete_pattern failed: {str(e)}")

            if self._fallback_cache:
                return await self._fallback_cache.delete_pattern(pattern)

            return 0

    async def health_check(self) -> bool:
        """
        Check if Redis is healthy and accessible.

        Returns:
            True if Redis is healthy, False otherwise
        """
        try:
            redis = await self._get_redis()

            if not self._connected:
                return False

            # Ping Redis
            await redis.ping()

            return True

        except Exception as e:
            logger.error(f"Redis health check failed: {str(e)}")
            return False

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
        # Reuse validation from memory cache
        MemoryCache._validate_not_sensitive(key, value)
