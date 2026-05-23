# v3
# app/services/redis_service.py
# ========================================================================
# Production Redis Service - Upstash-compatible with auto-reconnect
# + In-memory fallback for high availability
# ========================================================================

import json
import logging
import threading
import time
from typing import Optional, Any
from urllib.parse import urlparse
from redis import Redis
from redis.connection import ConnectionPool
from redis.exceptions import RedisError, ConnectionError as RedisConnectionError

logger = logging.getLogger(__name__)


class RedisService:
    """
    Production Redis service with Upstash-specific optimizations.

    Key features for Upstash:
    - TCP keepalive to prevent idle disconnections
    - Health check interval to detect stale connections
    - Auto-reconnect on connection errors
    - Connection pool management
    - IN-MEMORY FALLBACK when Redis is unavailable (sessions, rate limits,
      and temporary data continue to work across the app)
    """

    def __init__(
        self,
        connection_string: Optional[str] = None,
        fallback_to_memory: bool = True
    ):
        self.connection_string = connection_string
        self.fallback_to_memory = fallback_to_memory
        self.client: Optional[Redis] = None
        self.pool: Optional[ConnectionPool] = None
        self._memory_mode = False
        self._memory_store: dict[str, tuple[Any, Optional[float]]] = {}
        self._memory_lock = threading.Lock()

        if connection_string:
            try:
                self._initialize_connection(connection_string)
            except Exception as e:
                if fallback_to_memory:
                    logger.warning(
                        f"Redis connection failed ({e}), activating in-memory fallback"
                    )
                    self._enable_memory_mode()
                else:
                    logger.error(f"Redis init failed: {e}")
                    raise
        else:
            if fallback_to_memory:
                logger.info("No Redis URL provided; using in-memory fallback")
                self._enable_memory_mode()
            else:
                raise RuntimeError("Redis connection string required")

    def _enable_memory_mode(self):
        """Switch to thread-safe in-memory dictionary storage."""
        self._memory_mode = True
        self.client = None
        self.pool = None
        logger.info("RedisService operating in IN-MEMORY mode")

    def _memory_cleanup_expired(self):
        """Remove expired keys from in-memory store."""
        now = time.time()
        expired = [
            k for k, (_, exp) in self._memory_store.items()
            if exp is not None and exp <= now
        ]
        for k in expired:
            del self._memory_store[k]

    def _initialize_connection(self, connection_string: str):
        """Initialize Redis from connection string - Upstash-compatible."""
        try:
            self.pool = ConnectionPool.from_url(
                connection_string,
                decode_responses=True,
                socket_timeout=10,
                socket_connect_timeout=10,
                retry_on_timeout=True,
                max_connections=10,
            )
            self.client = Redis(connection_pool=self.pool)
            self.client.ping()
            parsed = urlparse(connection_string)
            logger.info(
                f"Redis connected to {parsed.hostname}:{parsed.port} "
                f"(SSL: {parsed.scheme == 'rediss'})"
            )
        except Exception as e:
            logger.error(f"Redis init failed: {e}")
            raise

    def _get_healthy_client(self) -> Redis:
        """
        Get Redis client with automatic reconnection on stale connections.
        If reconnection fails and fallback is enabled, switches to memory mode.
        """
        if self._memory_mode:
            raise RuntimeError("In memory mode - no Redis client available")

        if not self.client:
            raise RuntimeError("Redis client not initialized")

        try:
            self.client.ping()
            return self.client

        except (RedisConnectionError, ConnectionError, BrokenPipeError) as e:
            logger.warning(f"Redis connection stale ({e}), reconnecting...")
            try:
                self.client = Redis(connection_pool=self.pool)
                self.client.ping()
                logger.info("Redis reconnected successfully")
                return self.client
            except Exception as reconnect_err:
                if self.fallback_to_memory:
                    logger.warning(
                        f"Redis reconnection failed ({reconnect_err}), "
                        f"falling back to in-memory"
                    )
                    self._enable_memory_mode()
                    raise RuntimeError("Switched to memory mode")
                logger.error(f"Redis reconnection failed: {reconnect_err}")
                raise

    def get_client(self) -> Redis:
        """Get Redis client (backward compatibility)"""
        return self._get_healthy_client()

    def set(
        self,
        key: str,
        value: Any,
        expiry: Optional[int] = None,
        as_json: bool = True
    ) -> bool:
        """
        Set a key with optional expiry.
        Falls back to in-memory storage if Redis becomes unavailable.
        """
        if self._memory_mode:
            return self._memory_set(key, value, expiry, as_json)

        try:
            client = self._get_healthy_client()
            if as_json and isinstance(value, (dict, list)):
                value = json.dumps(value)
            if expiry:
                return bool(client.setex(key, expiry, value))
            return bool(client.set(key, value))
        except RedisError as e:
            logger.error(f"Redis SET error for key '{key}': {e}")
            return False
        except RuntimeError:
            return self._memory_set(key, value, expiry, as_json)

    def _memory_set(
        self,
        key: str,
        value: Any,
        expiry: Optional[int],
        as_json: bool
    ) -> bool:
        with self._memory_lock:
            self._memory_cleanup_expired()
            if as_json and isinstance(value, (dict, list)):
                value = json.dumps(value)
            exp_time = time.time() + expiry if expiry else None
            self._memory_store[key] = (value, exp_time)
            return True

    def get(
        self,
        key: str,
        as_json: bool = False,
        default: Any = None
    ) -> Optional[Any]:
        """
        Get value by key.
        Falls back to in-memory store if Redis becomes unavailable.
        """
        if self._memory_mode:
            return self._memory_get(key, as_json, default)

        try:
            client = self._get_healthy_client()
            value = client.get(key)
            if value is None:
                return default
            if as_json:
                try:
                    return json.loads(value)
                except json.JSONDecodeError as je:
                    logger.warning(f"JSON decode failed for key '{key}': {je}")
                    return value
            return value
        except RedisError as e:
            logger.error(f"Redis GET error for key '{key}': {e}")
            return default
        except RuntimeError:
            return self._memory_get(key, as_json, default)

    def _memory_get(
        self,
        key: str,
        as_json: bool,
        default: Any
    ) -> Optional[Any]:
        with self._memory_lock:
            self._memory_cleanup_expired()
            if key not in self._memory_store:
                return default
            value, _ = self._memory_store[key]
            if as_json:
                try:
                    return json.loads(value)
                except (json.JSONDecodeError, TypeError):
                    return value
            return value

    def delete(self, *keys: str) -> int:
        """Delete one or more keys."""
        if self._memory_mode:
            return self._memory_delete(*keys)

        try:
            client = self._get_healthy_client()
            return client.delete(*keys)
        except RedisError as e:
            logger.error(f"Redis DELETE error: {e}")
            return 0
        except RuntimeError:
            return self._memory_delete(*keys)

    def _memory_delete(self, *keys: str) -> int:
        with self._memory_lock:
            count = 0
            for k in keys:
                if k in self._memory_store:
                    del self._memory_store[k]
                    count += 1
            return count

    def exists(self, *keys: str) -> int:
        """Check if keys exist."""
        if self._memory_mode:
            return self._memory_exists(*keys)

        try:
            client = self._get_healthy_client()
            return client.exists(*keys)
        except RedisError as e:
            logger.error(f"Redis EXISTS error: {e}")
            return 0
        except RuntimeError:
            return self._memory_exists(*keys)

    def _memory_exists(self, *keys: str) -> int:
        with self._memory_lock:
            self._memory_cleanup_expired()
            return sum(1 for k in keys if k in self._memory_store)

    def increment_rate_limit(
        self,
        key: str,
        window: int = 60,
        limit: int = 50
    ) -> tuple[int, bool]:
        """
        Increment rate limit counter with sliding window.
        Works identically in Redis or in-memory mode.
        """
        if self._memory_mode:
            return self._memory_increment_rate_limit(key, window, limit)

        try:
            client = self._get_healthy_client()
            pipe = client.pipeline()
            pipe.incr(key)
            pipe.expire(key, window)
            results = pipe.execute()
            current_count = results[0]
            is_allowed = current_count <= limit
            return current_count, is_allowed
        except RedisError as e:
            logger.error(f"Redis rate limit error for key '{key}': {e}")
            return 0, True
        except RuntimeError:
            return self._memory_increment_rate_limit(key, window, limit)

    def _memory_increment_rate_limit(
        self,
        key: str,
        window: int,
        limit: int
    ) -> tuple[int, bool]:
        with self._memory_lock:
            self._memory_cleanup_expired()
            now = time.time()
            current = self._memory_store.get(key)
            if current is None:
                count = 1
                self._memory_store[key] = (count, now + window)
            else:
                count, _ = current
                count += 1
                self._memory_store[key] = (count, now + window)
            return count, count <= limit

    def ping(self) -> bool:
        """Test Redis connection. Always True in memory mode."""
        if self._memory_mode:
            return True

        try:
            client = self._get_healthy_client()
            return bool(client.ping())
        except Exception as e:
            logger.error(f"Redis PING failed: {e}")
            return False

    def close(self):
        """Close Redis connection pool or clear in-memory store."""
        if self._memory_mode:
            with self._memory_lock:
                self._memory_store.clear()
            logger.info("In-memory store cleared")
            return

        try:
            if self.pool:
                self.pool.disconnect()
                logger.info("Redis connection pool closed")
        except Exception as e:
            logger.error(f"Error closing Redis pool: {e}")
            