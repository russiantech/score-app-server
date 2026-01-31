# redis_service.py
# ========================================================================
# Professional Redis Service - Clean, scalable, reload-safe
# ========================================================================
import json
import logging
from typing import Optional, Any
from urllib.parse import urlparse
from redis import Redis
from redis.connection import ConnectionPool
from redis.exceptions import RedisError

logger = logging.getLogger(__name__)


class RedisService:
    """Professional Redis service with connection pooling and error handling"""

    def __init__(self, connection_string: Optional[str] = None):
        self.client: Optional[Redis] = None
        self.pool: Optional[ConnectionPool] = None
        if connection_string:
            self._initialize_connection(connection_string)

    def _initialize_connection(self, connection_string: str):
        """Parse connection string and create connection pool"""
        try:
            parsed = urlparse(connection_string)
            host = parsed.hostname or 'localhost'
            port = parsed.port or 6379
            db = int(parsed.path.lstrip('/')) if parsed.path else 0
            password = parsed.password
            username = parsed.username

            self.pool = ConnectionPool(
                host=host,
                port=port,
                db=db,
                password=password,
                username=username,
                max_connections=50,
                decode_responses=True,
                socket_timeout=5,
                socket_connect_timeout=5,
                socket_keepalive=True,
                retry_on_timeout=True,
                health_check_interval=30
            )

            self.client = Redis(connection_pool=self.pool)
            self.client.ping()
            logger.info(f"Redis connected successfully to {host}:{port}/{db}")
        except Exception as e:
            logger.error(f"Failed to initialize Redis: {e}")
            raise

    def get_client(self) -> Redis:
        if not self.client:
            raise RuntimeError("Redis client not initialized")
        return self.client

    def set(self, key: str, value: Any, expiry: Optional[int] = None) -> bool:
        try:
            if isinstance(value, (dict, list)):
                value = json.dumps(value)
            if expiry:
                return bool(self.client.setex(key, expiry, value))
            return bool(self.client.set(key, value))
        except RedisError as e:
            logger.error(f"Redis SET error for key {key}: {e}")
            return False

    def get(self, key: str, as_json: bool = True) -> Optional[Any]:
        try:
            value = self.client.get(key)
            if value and as_json:
                try:
                    return json.loads(value)
                except json.JSONDecodeError:
                    return value
            return value
        except RedisError as e:
            logger.error(f"Redis GET error for key {key}: {e}")
            return None

    def delete(self, key: str) -> bool:
        try:
            return bool(self.client.delete(key))
        except RedisError as e:
            logger.error(f"Redis DELETE error for key {key}: {e}")
            return False

    def exists(self, key: str) -> bool:
        try:
            return bool(self.client.exists(key))
        except RedisError as e:
            logger.error(f"Redis EXISTS error for key {key}: {e}")
            return False

    def increment_rate_limit(
        self, key: str, window: int = 60, limit: int = 50
    ) -> tuple[int, bool]:
        """Increment rate limit counter with TTL"""
        try:
            pipe = self.client.pipeline()
            pipe.incr(key)
            pipe.expire(key, window)
            current_count, _ = pipe.execute()
            return current_count, current_count <= limit
        except RedisError as e:
            logger.error(f"Redis rate limit error for key {key}: {e}")
            return 0, True

    def close(self):
        """Close Redis connection pool"""
        if self.pool:
            self.pool.disconnect()
            logger.info("Redis connection closed")
