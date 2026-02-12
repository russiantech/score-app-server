# app/api/deps/storage.py
"""
Redis dependency injection with singleton pattern and proper lifecycle management
"""
import logging
from typing import Generator

from fastapi import HTTPException, status

from app.core.config import get_app_config
from app.services.redis_service import RedisService

logger = logging.getLogger(__name__)

# Global Redis instance (singleton)
_redis_instance: RedisService | None = None


def get_redis_instance() -> RedisService:
    """
    Get or create global Redis instance (singleton pattern).
    
    This ensures we reuse the same connection pool across all requests,
    which is critical for performance and connection management.
    """
    global _redis_instance
    
    if _redis_instance is None:
        config = get_app_config()
        redis_url = config.redis_config.redis_connection_string
        # print(redis_url)
        if not redis_url:
            raise RuntimeError("Redis connection string not configured in environment")
        
        try:
            _redis_instance = RedisService(redis_url)
            logger.info(" Redis instance initialized")
        
        except Exception as e:
            logger.error(f"Failed to create Redis instance: {e}")
            raise RuntimeError(f"Redis initialization failed: {e}")
    
    return _redis_instance


def get_redis_service() -> Generator[RedisService, None, None]:
    """
    FastAPI dependency for Redis service.
    
    Yields a Redis service instance for dependency injection.
    Automatically handles connection health checks.
    
    Usage:
        @router.post("/endpoint")
        async def endpoint(redis: RedisService = Depends(get_redis_service)):
            redis.set("key", "value")
    """
    try:
        redis_service = get_redis_instance()
        
        # Optional: Pre-check health before yielding
        # This ensures we don't yield a dead connection
        # (The service itself handles reconnection, so this is optional)
        if not redis_service.ping():
            logger.warning("  Redis health check failed before yielding")
            # Continue anyway - will fail gracefully in the endpoint
        
        yield redis_service
    
    except Exception as e:
        logger.error(f" Redis service error in dependency: {e}")
        
        # For critical endpoints, raise error
        # For non-critical, you could yield a mock/fallback service
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Cache service temporarily unavailable. Please try again. 1 {e}"
        )


def close_redis():
    """
    Cleanup function to close Redis connection pool.
    
    Call this during FastAPI app shutdown (in lifespan context).
    """
    global _redis_instance
    
    if _redis_instance:
        try:
            _redis_instance.close()
            _redis_instance = None
            logger.info("  Redis connection closed during shutdown")
        
        except Exception as e:
            logger.error(f" Error closing Redis during shutdown: {e}")


# Optional: Initialize Redis eagerly on module import
# This can be useful for early error detection
def init_redis_on_startup():
    """
    Initialize Redis connection pool eagerly.
    Call this from your FastAPI lifespan startup.
    """
    try:
        redis = get_redis_instance()
        if redis.ping():
            logger.info("Redis startup check passed")
        else:
            logger.warning("Redis startup check failed (will retry on first use)")
    
    except Exception as e:
        logger.error(f" Redis startup initialization failed: {e}")
        # Don't raise - let app start even if Redis is temporarily down
        # The _get_healthy_client() method will reconnect when needed

    