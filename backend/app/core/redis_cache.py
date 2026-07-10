import logging
from typing import Optional

from app.core.database import redis_client

logger = logging.getLogger(__name__)

async def get_cache(key: str) -> Optional[str]:
    """Retrieves value from Redis cache."""
    try:
        return await redis_client.get(key)
    except Exception as e:
        logger.error(f"Redis get cache failed for key {key}: {e}")
        return None

async def set_cache(key: str, value: str, expire_seconds: int = 3600) -> bool:
    """Writes value to Redis cache with expiration."""
    try:
        await redis_client.set(key, value, ex=expire_seconds)
        return True
    except Exception as e:
        logger.error(f"Redis set cache failed for key {key}: {e}")
        return False

async def invalidate_cache(pattern: str) -> bool:
    """Invalidates keys matching a glob pattern."""
    try:
        keys = await redis_client.keys(pattern)
        if keys:
            await redis_client.delete(*keys)
        return True
    except Exception as e:
        logger.error(f"Redis invalidate cache failed for pattern {pattern}: {e}")
        return False


class RedisRateLimiter:
    """Production Redis-backed request rate limiter."""
    def __init__(self):
        self.redis = redis_client

    async def is_rate_limited(self, ip_address: str, endpoint: str, limit: int = 60, period_seconds: int = 60) -> bool:
        """Checks if a client has exceeded rate limits."""
        key = f"rate_limit:{ip_address}:{endpoint}"
        try:
            current = await self.redis.get(key)
            if current is not None:
                if int(current) >= limit:
                    return True
                await self.redis.incr(key)
            else:
                async with self.redis.pipeline(transaction=True) as pipe:
                    pipe.set(key, 1)
                    pipe.expire(key, period_seconds)
                    await pipe.execute()
            return False
        except Exception as e:
            logger.error(f"Rate limiting check failed for key {key}: {e}")
            # Fail-open in development to prevent service blocking if Redis server is down
            return False
