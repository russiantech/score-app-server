# ========================================================================
# FastAPI Dependency Injection for Redis
# ========================================================================
from functools import lru_cache
import logging
from app.core.config import get_app_config
from app.services.redis_service import RedisService

logger = logging.getLogger(__name__)

@lru_cache()
def get_redis_service() -> RedisService:
    """Return a cached RedisService instance"""
    app_config = get_app_config()
    redis_conn_string = app_config.redis_config.redis_connection_string

    if not redis_conn_string:
        logger.warning("Redis connection string not configured")
        raise RuntimeError("Redis not configured")

    return RedisService(redis_conn_string)
