"""
Redis-based caching service for high-performance data access.
Provides 10-100x performance improvement by caching frequently accessed data.
"""
import logging
import json
import pickle
from typing import Any, Optional, List, Dict
import redis
from functools import wraps
import hashlib

logger = logging.getLogger(__name__)


class CacheService:
    """
    Redis-based caching service with automatic serialization.
    Supports TTL, batch operations, and cache invalidation patterns.
    """

    def __init__(
        self,
        host: str = "localhost",
        port: int = 6379,
        db: int = 0,
        password: Optional[str] = None,
        default_ttl: int = 3600,
        max_connections: int = 10,
        enabled: bool = True
    ):
        """
        Initialize cache service.

        Args:
            host: Redis host
            port: Redis port
            db: Redis database number
            password: Redis password (if required)
            default_ttl: Default TTL in seconds
            max_connections: Maximum connection pool size
            enabled: Whether caching is enabled
        """
        self.enabled = enabled
        self.default_ttl = default_ttl
        self._client = None
        self._connection_pool = None

        if self.enabled:
            try:
                # Create connection pool
                self._connection_pool = redis.ConnectionPool(
                    host=host,
                    port=port,
                    db=db,
                    password=password,
                    max_connections=max_connections,
                    decode_responses=False  # We'll handle encoding ourselves
                )

                # Create Redis client
                self._client = redis.Redis(connection_pool=self._connection_pool)

                # Test connection
                self._client.ping()
                logger.info(f"Redis cache connected: {host}:{port}/{db}")

            except redis.ConnectionError as e:
                logger.warning(f"Redis connection failed: {e}. Caching disabled.")
                self.enabled = False
            except Exception as e:
                logger.error(f"Failed to initialize Redis cache: {e}")
                self.enabled = False
        else:
            logger.info("Caching is disabled")

    def get(self, key: str, deserialize: bool = True) -> Optional[Any]:
        """
        Get a value from cache.

        Args:
            key: Cache key
            deserialize: Whether to deserialize the value

        Returns:
            Cached value or None if not found
        """
        if not self.enabled:
            return None

        try:
            value = self._client.get(key)
            if value is None:
                return None

            if deserialize:
                return self._deserialize(value)
            return value

        except Exception as e:
            logger.error(f"Cache get failed for key '{key}': {e}")
            return None

    def set(
        self,
        key: str,
        value: Any,
        ttl: Optional[int] = None,
        serialize: bool = True
    ) -> bool:
        """
        Set a value in cache.

        Args:
            key: Cache key
            value: Value to cache
            ttl: Time-to-live in seconds (uses default if not provided)
            serialize: Whether to serialize the value

        Returns:
            True if successful, False otherwise
        """
        if not self.enabled:
            return False

        try:
            if serialize:
                value = self._serialize(value)

            ttl = ttl or self.default_ttl
            self._client.setex(key, ttl, value)
            return True

        except Exception as e:
            logger.error(f"Cache set failed for key '{key}': {e}")
            return False

    def delete(self, key: str) -> bool:
        """
        Delete a key from cache.

        Args:
            key: Cache key

        Returns:
            True if deleted, False otherwise
        """
        if not self.enabled:
            return False

        try:
            self._client.delete(key)
            return True
        except Exception as e:
            logger.error(f"Cache delete failed for key '{key}': {e}")
            return False

    def delete_pattern(self, pattern: str) -> int:
        """
        Delete all keys matching a pattern.

        Args:
            pattern: Key pattern (e.g., "user:*")

        Returns:
            Number of keys deleted
        """
        if not self.enabled:
            return 0

        try:
            keys = self._client.keys(pattern)
            if keys:
                return self._client.delete(*keys)
            return 0
        except Exception as e:
            logger.error(f"Cache delete pattern failed for '{pattern}': {e}")
            return 0

    def exists(self, key: str) -> bool:
        """
        Check if a key exists in cache.

        Args:
            key: Cache key

        Returns:
            True if exists, False otherwise
        """
        if not self.enabled:
            return False

        try:
            return bool(self._client.exists(key))
        except Exception as e:
            logger.error(f"Cache exists check failed for key '{key}': {e}")
            return False

    def get_many(self, keys: List[str], deserialize: bool = True) -> Dict[str, Any]:
        """
        Get multiple values from cache.

        Args:
            keys: List of cache keys
            deserialize: Whether to deserialize values

        Returns:
            Dictionary of key-value pairs
        """
        if not self.enabled or not keys:
            return {}

        try:
            values = self._client.mget(keys)
            result = {}

            for key, value in zip(keys, values):
                if value is not None:
                    if deserialize:
                        result[key] = self._deserialize(value)
                    else:
                        result[key] = value

            return result

        except Exception as e:
            logger.error(f"Cache get_many failed: {e}")
            return {}

    def set_many(
        self,
        mapping: Dict[str, Any],
        ttl: Optional[int] = None,
        serialize: bool = True
    ) -> bool:
        """
        Set multiple values in cache.

        Args:
            mapping: Dictionary of key-value pairs
            ttl: Time-to-live in seconds
            serialize: Whether to serialize values

        Returns:
            True if successful, False otherwise
        """
        if not self.enabled or not mapping:
            return False

        try:
            pipe = self._client.pipeline()
            ttl = ttl or self.default_ttl

            for key, value in mapping.items():
                if serialize:
                    value = self._serialize(value)
                pipe.setex(key, ttl, value)

            pipe.execute()
            return True

        except Exception as e:
            logger.error(f"Cache set_many failed: {e}")
            return False

    def increment(self, key: str, amount: int = 1) -> Optional[int]:
        """
        Increment a numeric value.

        Args:
            key: Cache key
            amount: Amount to increment

        Returns:
            New value or None if failed
        """
        if not self.enabled:
            return None

        try:
            return self._client.incrby(key, amount)
        except Exception as e:
            logger.error(f"Cache increment failed for key '{key}': {e}")
            return None

    def clear_all(self) -> bool:
        """
        Clear all keys in the current database.
        Use with caution!

        Returns:
            True if successful, False otherwise
        """
        if not self.enabled:
            return False

        try:
            self._client.flushdb()
            logger.warning("All cache cleared")
            return True
        except Exception as e:
            logger.error(f"Cache clear_all failed: {e}")
            return False

    def get_stats(self) -> Dict[str, Any]:
        """
        Get cache statistics.

        Returns:
            Dictionary with cache stats
        """
        if not self.enabled:
            return {"enabled": False}

        try:
            info = self._client.info()
            return {
                "enabled": True,
                "used_memory": info.get("used_memory_human"),
                "connected_clients": info.get("connected_clients"),
                "total_commands_processed": info.get("total_commands_processed"),
                "keyspace_hits": info.get("keyspace_hits"),
                "keyspace_misses": info.get("keyspace_misses"),
                "uptime_in_seconds": info.get("uptime_in_seconds")
            }
        except Exception as e:
            logger.error(f"Failed to get cache stats: {e}")
            return {"enabled": True, "error": str(e)}

    def _serialize(self, value: Any) -> bytes:
        """Serialize a Python object to bytes."""
        try:
            # Try JSON first (faster and more readable)
            return json.dumps(value).encode('utf-8')
        except (TypeError, ValueError):
            # Fall back to pickle for complex objects
            return pickle.dumps(value)

    def _deserialize(self, value: bytes) -> Any:
        """Deserialize bytes to a Python object."""
        try:
            # Try JSON first
            return json.loads(value.decode('utf-8'))
        except (json.JSONDecodeError, UnicodeDecodeError):
            # Fall back to pickle
            return pickle.loads(value)


def cache_key(*args, **kwargs) -> str:
    """
    Generate a cache key from arguments.

    Args:
        *args: Positional arguments
        **kwargs: Keyword arguments

    Returns:
        Cache key string
    """
    # Create a string representation of arguments
    key_parts = [str(arg) for arg in args]
    key_parts.extend(f"{k}={v}" for k, v in sorted(kwargs.items()))
    key_string = ":".join(key_parts)

    # Hash for consistent key length
    return hashlib.md5(key_string.encode()).hexdigest()


def cached(ttl: Optional[int] = None, key_prefix: str = ""):
    """
    Decorator for caching function results.

    Args:
        ttl: Cache TTL in seconds
        key_prefix: Prefix for cache key

    Example:
        @cached(ttl=3600, key_prefix="user")
        def get_user(user_id):
            return fetch_user_from_db(user_id)
    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            cache = get_cache_service()
            if not cache.enabled:
                return func(*args, **kwargs)

            # Generate cache key
            func_name = f"{func.__module__}.{func.__name__}"
            key = f"{key_prefix}:{func_name}:{cache_key(*args, **kwargs)}"

            # Try to get from cache
            result = cache.get(key)
            if result is not None:
                logger.debug(f"Cache hit: {key}")
                return result

            # Execute function and cache result
            logger.debug(f"Cache miss: {key}")
            result = func(*args, **kwargs)
            cache.set(key, result, ttl=ttl)
            return result

        return wrapper
    return decorator


# Global instance cache
_cache_service_instance = None


def get_cache_service() -> CacheService:
    """
    Get a cached Redis service instance.
    Singleton pattern to maintain single connection pool.
    """
    global _cache_service_instance

    if _cache_service_instance is None:
        from ..config.settings import get_settings

        settings = get_settings()
        redis_config = settings.get_redis_config()

        _cache_service_instance = CacheService(
            host=redis_config["host"],
            port=redis_config["port"],
            db=redis_config["db"],
            password=redis_config["password"],
            default_ttl=redis_config["cache_ttl"],
            max_connections=redis_config["max_connections"],
            enabled=redis_config["enabled"]
        )

    return _cache_service_instance


def reset_cache_service():
    """Reset the global cache service instance."""
    global _cache_service_instance
    _cache_service_instance = None
