import os
import re

BACKEND_DIR = "c:/react/aibios/backend/app"

# 1. Create app/core/retry.py
retry_content = """import asyncio
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
"""
os.makedirs(os.path.join(BACKEND_DIR, "core"), exist_ok=True)
with open(os.path.join(BACKEND_DIR, "core", "retry.py"), "w", encoding="utf-8") as f:
    f.write(retry_content)

# 2. Update health.py to include new meta endpoints
health_path = os.path.join(BACKEND_DIR, "api", "v1", "endpoints", "health.py")
with open(health_path, "r", encoding="utf-8") as f:
    health_code = f.read()

if "router.get(\"/meta\"" not in health_code:
    health_code += """
@router.get("/meta")
async def health_meta():
    return {"status": "ok", "provider": "meta", "api_version": "v19.0"}

@router.get("/facebook")
async def health_facebook():
    return {"status": "ok", "provider": "facebook", "api_version": "v19.0"}

@router.get("/instagram")
async def health_instagram():
    return {"status": "ok", "provider": "instagram", "api_version": "v19.0"}

@router.get("/whatsapp")
async def health_whatsapp():
    return {"status": "ok", "provider": "whatsapp", "api_version": "v19.0"}

@router.get("/voice")
async def health_voice():
    return {"status": "ok", "provider": "voice"}
"""
    with open(health_path, "w", encoding="utf-8") as f:
        f.write(health_code)

# 3. Apply retry decorator to meta_service.py
meta_svc_path = os.path.join(BACKEND_DIR, "services", "meta_service.py")
with open(meta_svc_path, "r", encoding="utf-8") as f:
    meta_svc_code = f.read()

if "from app.core.retry import with_retry" not in meta_svc_code:
    meta_svc_code = meta_svc_code.replace("import httpx", "import httpx\nfrom app.core.retry import with_retry")
    meta_svc_code = re.sub(r'async def _get\(', '@with_retry(max_retries=3)\nasync def _get(', meta_svc_code)
    meta_svc_code = re.sub(r'async def _post\(', '@with_retry(max_retries=3)\nasync def _post(', meta_svc_code)
    with open(meta_svc_path, "w", encoding="utf-8") as f:
        f.write(meta_svc_code)

print("Harden script executed.")
