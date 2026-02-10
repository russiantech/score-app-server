# # redis_service.py
# # ========================================================================
# # Professional Redis Service - Clean, scalable, reload-safe
# # ========================================================================
# import json
# import logging
# from typing import Optional, Any
# from urllib.parse import urlparse
# from redis import Redis
# from redis.connection import ConnectionPool
# from redis.exceptions import RedisError

# logger = logging.getLogger(__name__)


# class RedisService:
#     """Professional Redis service with connection pooling and error handling"""

#     def __init__(self, connection_string: Optional[str] = None):
#         self.client: Optional[Redis] = None
#         self.pool: Optional[ConnectionPool] = None
#         if connection_string:
#             self._initialize_connection(connection_string)

#     def _initialize_connection(self, connection_string: str):
#         """Parse connection string and create connection pool"""
#         try:
#             parsed = urlparse(connection_string)
#             host = parsed.hostname or 'localhost'
#             port = parsed.port or 6379
#             db = int(parsed.path.lstrip('/')) if parsed.path else 0
#             password = parsed.password
#             username = parsed.username

#             self.pool = ConnectionPool(
#                 host=host,
#                 port=port,
#                 db=db,
#                 password=password,
#                 username=username,
#                 max_connections=50,
#                 decode_responses=True,
#                 socket_timeout=5,
#                 socket_connect_timeout=5,
#                 socket_keepalive=True,
#                 retry_on_timeout=True,
#                 health_check_interval=30
#             )

#             self.client = Redis(connection_pool=self.pool)
#             self.client.ping()
#             logger.info(f"Redis connected successfully to {host}:{port}/{db}")
#         except Exception as e:
#             logger.error(f"Failed to initialize Redis: {e}")
#             raise

#     def get_client(self) -> Redis:
#         if not self.client:
#             raise RuntimeError("Redis client not initialized")
#         return self.client

#     def set(self, key: str, value: Any, expiry: Optional[int] = None) -> bool:
#         try:
#             if isinstance(value, (dict, list)):
#                 value = json.dumps(value)
#             if expiry:
#                 return bool(self.client.setex(key, expiry, value))
#             return bool(self.client.set(key, value))
#         except RedisError as e:
#             logger.error(f"Redis SET error for key {key}: {e}")
#             return False

#     def get(self, key: str, as_json: bool = True) -> Optional[Any]:
#         try:
#             value = self.client.get(key)
#             if value and as_json:
#                 try:
#                     return json.loads(value)
#                 except json.JSONDecodeError:
#                     return value
#             return value
#         except RedisError as e:
#             logger.error(f"Redis GET error for key {key}: {e}")
#             return None

#     def delete(self, key: str) -> bool:
#         try:
#             return bool(self.client.delete(key))
#         except RedisError as e:
#             logger.error(f"Redis DELETE error for key {key}: {e}")
#             return False

#     def exists(self, key: str) -> bool:
#         try:
#             return bool(self.client.exists(key))
#         except RedisError as e:
#             logger.error(f"Redis EXISTS error for key {key}: {e}")
#             return False

#     def increment_rate_limit(
#         self, key: str, window: int = 60, limit: int = 50
#     ) -> tuple[int, bool]:
#         """Increment rate limit counter with TTL"""
#         try:
#             pipe = self.client.pipeline()
#             pipe.incr(key)
#             pipe.expire(key, window)
#             current_count, _ = pipe.execute()
#             return current_count, current_count <= limit
#         except RedisError as e:
#             logger.error(f"Redis rate limit error for key {key}: {e}")
#             return 0, True

#     def close(self):
#         """Close Redis connection pool"""
#         if self.pool:
#             self.pool.disconnect()
#             logger.info("Redis connection closed")


# # v2
# # app/services/redis_service.py
# # ========================================================================
# # Production Redis Service - Upstash-compatible with auto-reconnect
# # ========================================================================
# import json
# import logging
# from typing import Optional, Any
# from urllib.parse import urlparse
# from redis import Redis
# from redis.connection import ConnectionPool
# from redis.exceptions import RedisError, ConnectionError as RedisConnectionError

# logger = logging.getLogger(__name__)


# class RedisService:
#     """
#     Production Redis service with Upstash-specific optimizations.
    
#     Key features for Upstash:
#     - TCP keepalive to prevent idle disconnections
#     - Health check interval to detect stale connections
#     - Auto-reconnect on connection errors
#     - Connection pool management
#     """

#     def __init__(self, connection_string: Optional[str] = None):
#         self.connection_string = connection_string
#         self.client: Optional[Redis] = None
#         self.pool: Optional[ConnectionPool] = None
        
#         if connection_string:
#             self._initialize_connection(connection_string)

#     def _initialize_connection(self, connection_string: str):
#         """Parse connection string and create Upstash-compatible connection pool"""
#         try:
#             parsed = urlparse(connection_string)
#             host = parsed.hostname or 'localhost'
#             port = parsed.port or 6379
#             db = int(parsed.path.lstrip('/')) if parsed.path else 0
#             password = parsed.password
#             username = parsed.username
            
#             # Determine if SSL
#             use_ssl = parsed.scheme == 'rediss'

#             # CRITICAL: Upstash-specific connection pool settings
#             self.pool = ConnectionPool(
#                 host=host,
#                 port=port,
#                 db=db,
#                 password=password,
#                 username=username,
                
#                 # Connection pool size (conservative for shared hosting)
#                 max_connections=10,
                
#                 # Decoding
#                 decode_responses=True,
                
#                 # Timeouts (CRITICAL for Upstash)
#                 socket_timeout=5,          # 5s read/write timeout
#                 socket_connect_timeout=5,  # 5s to establish connection
                
#                 # TCP Keepalive (CRITICAL - prevents Upstash from closing idle connections)
#                 socket_keepalive=True,
#                 socket_keepalive_options={
#                     1: 30,   # TCP_KEEPIDLE: start keepalive after 30s idle
#                     2: 10,   # TCP_KEEPINTVL: send keepalive probe every 10s
#                     3: 3,    # TCP_KEEPCNT: close after 3 failed probes
#                 },
                
#                 # Auto-retry on failures
#                 retry_on_timeout=True,
#                 retry_on_error=[RedisConnectionError],
                
#                 # Health checks (CRITICAL - detects stale connections)
#                 health_check_interval=30,  # Check connection health every 30s
                
#                 # SSL settings
#                 connection_class=None,  # Let redis-py auto-detect
#                 ssl=use_ssl,
#                 ssl_cert_reqs='required' if use_ssl else None,
#             )

#             self.client = Redis(connection_pool=self.pool)
            
#             # Verify connection
#             self.client.ping()
#             logger.info(f"✅ Redis connected to {host}:{port}/{db} (SSL: {use_ssl})")
            
#         except Exception as e:
#             logger.error(f"❌ Failed to initialize Redis: {e}")
#             raise

#     def _get_healthy_client(self) -> Redis:
#         """
#         Get Redis client with automatic reconnection on stale connections.
#         This is the KEY to fixing "Connection closed by server" errors.
#         """
#         if not self.client:
#             raise RuntimeError("Redis client not initialized")
        
#         try:
#             # Quick ping to check if connection is alive
#             self.client.ping()
#             return self.client
        
#         except (RedisConnectionError, ConnectionError, BrokenPipeError) as e:
#             logger.warning(f"Redis connection stale ({e}), reconnecting...")
            
#             # Recreate client from pool (pool will handle creating new connection)
#             try:
#                 self.client = Redis(connection_pool=self.pool)
#                 self.client.ping()
#                 logger.info("✅ Redis reconnected successfully")
#                 return self.client
            
#             except Exception as reconnect_err:
#                 logger.error(f"❌ Redis reconnection failed: {reconnect_err}")
#                 raise

#     def get_client(self) -> Redis:
#         """Get Redis client (backward compatibility)"""
#         return self._get_healthy_client()

#     def set(
#         self, 
#         key: str, 
#         value: Any, 
#         expiry: Optional[int] = None,
#         as_json: bool = True
#     ) -> bool:
#         """
#         Set a key with optional expiry.
        
#         Args:
#             key: Redis key
#             value: Value to store
#             expiry: TTL in seconds
#             as_json: Auto-serialize dicts/lists to JSON
        
#         Returns:
#             True if successful
#         """
#         try:
#             client = self._get_healthy_client()
            
#             # Auto-serialize complex types
#             if as_json and isinstance(value, (dict, list)):
#                 value = json.dumps(value)
            
#             if expiry:
#                 return bool(client.setex(key, expiry, value))
#             return bool(client.set(key, value))
        
#         except RedisError as e:
#             logger.error(f"Redis SET error for key '{key}': {e}")
#             return False

#     def get(
#         self, 
#         key: str, 
#         as_json: bool = False,
#         default: Any = None
#     ) -> Optional[Any]:
#         """
#         Get value by key.
        
#         Args:
#             key: Redis key
#             as_json: Auto-deserialize JSON
#             default: Default value if key doesn't exist
        
#         Returns:
#             Value or default
#         """
#         try:
#             client = self._get_healthy_client()
#             value = client.get(key)
            
#             if value is None:
#                 return default
            
#             if as_json:
#                 try:
#                     return json.loads(value)
#                 except json.JSONDecodeError as je:
#                     logger.warning(f"JSON decode failed for key '{key}': {je}")
#                     return value
            
#             return value
        
#         except RedisError as e:
#             logger.error(f"Redis GET error for key '{key}': {e}")
#             return default

#     def delete(self, *keys: str) -> int:
#         """
#         Delete one or more keys.
        
#         Args:
#             *keys: Keys to delete
        
#         Returns:
#             Number of keys deleted
#         """
#         try:
#             client = self._get_healthy_client()
#             return client.delete(*keys)
        
#         except RedisError as e:
#             logger.error(f"Redis DELETE error: {e}")
#             return 0

#     def exists(self, *keys: str) -> int:
#         """
#         Check if keys exist.
        
#         Args:
#             *keys: Keys to check
        
#         Returns:
#             Number of keys that exist
#         """
#         try:
#             client = self._get_healthy_client()
#             return client.exists(*keys)
        
#         except RedisError as e:
#             logger.error(f"Redis EXISTS error: {e}")
#             return 0

#     def increment_rate_limit(
#         self, 
#         key: str, 
#         window: int = 60, 
#         limit: int = 50
#     ) -> tuple[int, bool]:
#         """
#         Increment rate limit counter with sliding window.
        
#         Args:
#             key: Rate limit key (e.g., "signup:192.168.1.1")
#             window: Time window in seconds
#             limit: Max requests in window
        
#         Returns:
#             (current_count, is_allowed)
#         """
#         try:
#             client = self._get_healthy_client()
            
#             pipe = client.pipeline()
#             pipe.incr(key)
#             pipe.expire(key, window)
#             results = pipe.execute()
            
#             current_count = results[0]
#             is_allowed = current_count <= limit
            
#             return current_count, is_allowed
        
#         except RedisError as e:
#             logger.error(f"Redis rate limit error for key '{key}': {e}")
#             # Fail open - allow request on Redis errors (prevents blocking users)
#             return 0, True

#     def ping(self) -> bool:
#         """Test Redis connection"""
#         try:
#             client = self._get_healthy_client()
#             return bool(client.ping())
        
#         except Exception as e:
#             logger.error(f"Redis PING failed: {e}")
#             return False

#     def close(self):
#         """Close Redis connection pool"""
#         try:
#             if self.pool:
#                 self.pool.disconnect()
#                 logger.info("✅ Redis connection pool closed")
        
#         except Exception as e:
#             logger.error(f"Error closing Redis pool: {e}")




# v3
# app/services/redis_service.py
# ========================================================================
# Production Redis Service - Upstash-compatible with auto-reconnect
# ========================================================================
import json
import logging
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
    """

    def __init__(self, connection_string: Optional[str] = None):
        self.connection_string = connection_string
        self.client: Optional[Redis] = None
        self.pool: Optional[ConnectionPool] = None
        
        if connection_string:
            self._initialize_connection(connection_string)

    def _initialize_connection(self, connection_string: str):
        """Parse connection string and create Upstash-compatible connection pool"""
        try:
            parsed = urlparse(connection_string)
            host = parsed.hostname or 'localhost'
            port = parsed.port or 6379
            db = int(parsed.path.lstrip('/')) if parsed.path else 0
            password = parsed.password
            username = parsed.username
            
            # Determine if SSL
            use_ssl = parsed.scheme == 'rediss'

            # CRITICAL: Upstash-specific connection pool settings
            self.pool = ConnectionPool(
                host=host,
                port=port,
                db=db,
                password=password,
                username=username,
                
                # Connection pool size (conservative for shared hosting)
                max_connections=10,
                
                # Decoding
                decode_responses=True,
                
                # Timeouts (CRITICAL for Upstash)
                socket_timeout=5,          # 5s read/write timeout
                socket_connect_timeout=5,  # 5s to establish connection
                
                # TCP Keepalive (CRITICAL - prevents Upstash from closing idle connections)
                socket_keepalive=True,
                socket_keepalive_options={
                    1: 30,   # TCP_KEEPIDLE: start keepalive after 30s idle
                    2: 10,   # TCP_KEEPINTVL: send keepalive probe every 10s
                    3: 3,    # TCP_KEEPCNT: close after 3 failed probes
                },
                
                # Auto-retry on failures
                retry_on_timeout=True,
                retry_on_error=[RedisConnectionError],
                
                # Health checks (CRITICAL - detects stale connections)
                health_check_interval=30,  # Check connection health every 30s
                
                # SSL settings
                connection_class=None,  # Let redis-py auto-detect
                ssl=use_ssl,
                ssl_cert_reqs='required' if use_ssl else None,
            )

            self.client = Redis(connection_pool=self.pool)
            
            # Verify connection
            self.client.ping()
            logger.info(f"✅ Redis connected to {host}:{port}/{db} (SSL: {use_ssl})")
            
        except Exception as e:
            logger.error(f"❌ Failed to initialize Redis: {e}")
            raise

    def _get_healthy_client(self) -> Redis:
        """
        Get Redis client with automatic reconnection on stale connections.
        This is the KEY to fixing "Connection closed by server" errors.
        """
        if not self.client:
            raise RuntimeError("Redis client not initialized")
        
        try:
            # Quick ping to check if connection is alive
            self.client.ping()
            return self.client
        
        except (RedisConnectionError, ConnectionError, BrokenPipeError) as e:
            logger.warning(f"Redis connection stale ({e}), reconnecting...")
            
            # Recreate client from pool (pool will handle creating new connection)
            try:
                self.client = Redis(connection_pool=self.pool)
                self.client.ping()
                logger.info("✅ Redis reconnected successfully")
                return self.client
            
            except Exception as reconnect_err:
                logger.error(f"❌ Redis reconnection failed: {reconnect_err}")
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
        
        Args:
            key: Redis key
            value: Value to store
            expiry: TTL in seconds
            as_json: Auto-serialize dicts/lists to JSON
        
        Returns:
            True if successful
        """
        try:
            client = self._get_healthy_client()
            
            # Auto-serialize complex types
            if as_json and isinstance(value, (dict, list)):
                value = json.dumps(value)
            
            if expiry:
                return bool(client.setex(key, expiry, value))
            return bool(client.set(key, value))
        
        except RedisError as e:
            logger.error(f"Redis SET error for key '{key}': {e}")
            return False

    def get(
        self, 
        key: str, 
        as_json: bool = False,
        default: Any = None
    ) -> Optional[Any]:
        """
        Get value by key.
        
        Args:
            key: Redis key
            as_json: Auto-deserialize JSON
            default: Default value if key doesn't exist
        
        Returns:
            Value or default
        """
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

    def delete(self, *keys: str) -> int:
        """
        Delete one or more keys.
        
        Args:
            *keys: Keys to delete
        
        Returns:
            Number of keys deleted
        """
        try:
            client = self._get_healthy_client()
            return client.delete(*keys)
        
        except RedisError as e:
            logger.error(f"Redis DELETE error: {e}")
            return 0

    def exists(self, *keys: str) -> int:
        """
        Check if keys exist.
        
        Args:
            *keys: Keys to check
        
        Returns:
            Number of keys that exist
        """
        try:
            client = self._get_healthy_client()
            return client.exists(*keys)
        
        except RedisError as e:
            logger.error(f"Redis EXISTS error: {e}")
            return 0

    def increment_rate_limit(
        self, 
        key: str, 
        window: int = 60, 
        limit: int = 50
    ) -> tuple[int, bool]:
        """
        Increment rate limit counter with sliding window.
        
        Args:
            key: Rate limit key (e.g., "signup:192.168.1.1")
            window: Time window in seconds
            limit: Max requests in window
        
        Returns:
            (current_count, is_allowed)
        """
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
            # Fail open - allow request on Redis errors (prevents blocking users)
            return 0, True

    def ping(self) -> bool:
        """Test Redis connection"""
        try:
            client = self._get_healthy_client()
            return bool(client.ping())
        
        except Exception as e:
            logger.error(f"Redis PING failed: {e}")
            return False

    def close(self):
        """Close Redis connection pool"""
        try:
            if self.pool:
                self.pool.disconnect()
                logger.info("✅ Redis connection pool closed")
        
        except Exception as e:
            logger.error(f"Error closing Redis pool: {e}")

