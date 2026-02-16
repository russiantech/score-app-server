"""
Redis dependency injection - BULLETPROOF version
Never crashes, always returns (even if None)
"""
import logging
import traceback
from typing import Generator, Optional

from app.core.config import get_app_config
from app.services.redis_service import RedisService
from redis.exceptions import RedisError

logger = logging.getLogger(__name__)

# Global Redis instance (singleton)
_redis_instance: Optional[RedisService] = None


def get_redis_instance() -> Optional[RedisService]:
    """
    Get or create global Redis instance (singleton pattern).
    NEVER crashes - returns None if Redis unavailable.
    """
    global _redis_instance
    
    if _redis_instance is None:
        try:
            config = get_app_config()
            redis_url = config.redis_config.redis_connection_string
            
            if not redis_url:
                logger.warning("Redis connection string not configured")
                return None
            
            _redis_instance = RedisService(redis_url)
            logger.info("Redis instance initialized")
            
        except Exception as e:
            logger.error(f"Failed to create Redis instance: {e}")
            logger.info("App will continue without Redis")
            return None
    
    return _redis_instance


# def get_redis_service() -> Generator[Optional[RedisService], None, None]:
#     """
#     FastAPI dependency for Redis service.
#     NEVER crashes - yields None if Redis unavailable.
    
#     Usage:
#         @router.post("/endpoint")
#         async def endpoint(redis: Optional[RedisService] = Depends(get_redis_service)):
#             if not redis:
#                 raise HTTPException(503, "Cache temporarily unavailable")
#             redis.set("key", "value")
#     """
#     redis_service = None
    
#     try:
#         redis_service = get_redis_instance()
        
#         # Health check (don't fail if it doesn't work)
#         if redis_service:
#             try:
#                 if not redis_service.ping():
#                     logger.warning("Redis health check failed")
#                     redis_service = None
#             except RedisError as e:
#                 logger.warning(f"Redis ping failed: {e}")
#                 redis_service = None
    
#     except Exception as e:
#         logger.error(f"Redis service error: {e}")
#         redis_service = None
    
#     # ALWAYS yield (even if None) - NEVER raise
#     yield redis_service

# v2
def get_redis_service() -> Generator[Optional[RedisService], None, None]:
    """
    FastAPI dependency for Redis service.
    BULLETPROOF - never crashes, even during cleanup.
    """
    redis_service = None
    
    try:
        redis_service = get_redis_instance()
        
        # Health check (don't fail if it doesn't work)
        if redis_service:
            try:
                if not redis_service.ping():
                    logger.warning("Redis health check failed")
                    redis_service = None
            except Exception as e:
                logger.warning(f"Redis ping failed: {e}")
                redis_service = None
        
        # ALWAYS yield (even if None)
        yield redis_service

    except Exception as e:
        # Log but don't crash
        logger.error(f"Redis dependency error: {e}")
        logger.error(traceback.format_exc())
        yield None
    
    finally:
        # Cleanup - NEVER crash
        try:
            if redis_service:
                # No cleanup needed for redis_service (connection pool managed globally)
                pass
        except Exception as cleanup_error:
            logger.error(f"Redis cleanup error (ignored): {cleanup_error}")
            pass


def close_redis():
    """
    Cleanup - close Redis connection pool.
    NEVER crashes.
    """
    global _redis_instance
    
    if _redis_instance:
        try:
            _redis_instance.close()
            _redis_instance = None
            logger.info("Redis connection closed")
        except Exception as e:
            logger.error(f"Error closing Redis: {e}")


def init_redis_on_startup():
    """
    Initialize Redis eagerly on startup.
    NEVER crashes - just logs errors.
    """
    try:
        redis = get_redis_instance()
        if redis and redis.ping():
            logger.info("Redis startup check passed")
            return True
        else:
            logger.warning("Redis startup check failed (will retry on demand)")
            return False
    except Exception as e:
        logger.error(f"Redis startup failed: {e}")
        logger.info("App will continue - Redis will auto-connect when available")
        return False
        # NEVER RAISE
