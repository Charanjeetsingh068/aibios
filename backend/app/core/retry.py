import asyncio
import logging
from functools import wraps

import httpx

logger = logging.getLogger(__name__)

def with_retry(max_retries=3, base_delay=1.0):
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            retries = 0
            while True:
                try:
                    return await func(*args, **kwargs)
                except httpx.HTTPStatusError as e:
                    status = e.response.status_code
                    if status in (429, 500, 502, 503, 504):
                        if retries >= max_retries:
                            raise
                        delay = base_delay * (2 ** retries)
                        logger.warning(f"API Error {status}. Retrying in {delay}s... (Attempt {retries + 1}/{max_retries})")
                        await asyncio.sleep(delay)
                        retries += 1
                    else:
                        raise
                except (httpx.RequestError, asyncio.TimeoutError) as e:
                    if retries >= max_retries:
                        raise
                    delay = base_delay * (2 ** retries)
                    logger.warning(f"Network error {type(e).__name__}. Retrying in {delay}s... (Attempt {retries + 1}/{max_retries})")
                    await asyncio.sleep(delay)
                    retries += 1
        return wrapper
    return decorator
