import redis.asyncio as redis
from ..config.settings import settings
import logging

logger = logging.getLogger(__name__)

# Create Redis connection pool
redis_pool = redis.ConnectionPool.from_url(settings.redis_url)


async def get_redis() -> redis.Redis:
    """
    Get Redis connection
    """
    return redis.Redis(connection_pool=redis_pool)


async def close_redis():
    """
    Close Redis connections
    """
    await redis_pool.disconnect()
