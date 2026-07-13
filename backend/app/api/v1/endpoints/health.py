import asyncio
import os
import logging
import psutil
import smtplib
import httpx
import boto3
from botocore.config import Config
from fastapi import APIRouter
from typing import Any, Dict

from app.core.config import settings
from app.core.database import verify_mongo, verify_postgres, verify_qdrant, verify_redis
from app.core.celery_app import celery_app

logger = logging.getLogger(__name__)
router = APIRouter()

def _workers_count() -> int:
    return int(os.environ.get("WEB_CONCURRENCY", os.environ.get("WORKERS", 1)))

async def check_postgres() -> bool:
    try:
        return await verify_postgres()
    except Exception as e:
        logger.warning(f"Health check PostgreSQL failed: {e}")
        return False

async def check_redis() -> bool:
    try:
        return await verify_redis()
    except Exception as e:
        logger.warning(f"Health check Redis failed: {e}")
        return False

async def check_mongo() -> bool:
    try:
        return await verify_mongo()
    except Exception as e:
        logger.warning(f"Health check MongoDB failed: {e}")
        return False

async def check_qdrant() -> bool:
    try:
        return await verify_qdrant()
    except Exception as e:
        logger.warning(f"Health check Qdrant failed: {e}")
        return False

async def check_celery() -> bool:
    try:
        def _check():
            inspect = celery_app.control.inspect(timeout=0.5)
            if inspect is None:
                return False
            stats = inspect.stats()
            return stats is not None and len(stats) > 0
        return await asyncio.to_thread(_check)
    except Exception as e:
        logger.warning(f"Health check Celery failed: {e}")
        return False

async def check_rabbitmq() -> bool:
    # Not configured in the codebase (Celery uses Redis broker)
    return False

async def check_openai() -> bool:
    if not settings.OPENAI_API_KEY:
        return False
    try:
        async with httpx.AsyncClient() as client:
            res = await client.get(
                "https://api.openai.com/v1/models",
                headers={"Authorization": f"Bearer {settings.OPENAI_API_KEY}"},
                timeout=1.0
            )
            return res.status_code == 200
    except Exception as e:
        logger.warning(f"Health check OpenAI failed: {e}")
        return False

async def check_meta_oauth() -> bool:
    if not settings.FACEBOOK_APP_ID or not settings.FACEBOOK_APP_SECRET:
        return False
    try:
        async with httpx.AsyncClient() as client:
            res = await client.get(
                f"https://graph.facebook.com/oauth/access_token?client_id={settings.FACEBOOK_APP_ID}&client_secret={settings.FACEBOOK_APP_SECRET}&grant_type=client_credentials",
                timeout=1.0
            )
            return res.status_code == 200
    except Exception as e:
        logger.warning(f"Health check Meta OAuth failed: {e}")
        return False

async def check_twilio() -> bool:
    if not settings.TWILIO_ACCOUNT_SID or not settings.TWILIO_AUTH_TOKEN:
        return False
    try:
        async with httpx.AsyncClient() as client:
            auth = httpx.BasicAuth(settings.TWILIO_ACCOUNT_SID, settings.TWILIO_AUTH_TOKEN)
            res = await client.get(
                f"https://api.twilio.com/2010-04-01/Accounts/{settings.TWILIO_ACCOUNT_SID}.json",
                auth=auth,
                timeout=1.0
            )
            return res.status_code == 200
    except Exception as e:
        logger.warning(f"Health check Twilio failed: {e}")
        return False

async def check_google_oauth() -> bool:
    if not settings.GOOGLE_CLIENT_ID or not settings.GOOGLE_CLIENT_SECRET:
        return False
    try:
        async with httpx.AsyncClient() as client:
            res = await client.get("https://accounts.google.com/.well-known/openid-configuration", timeout=1.0)
            return res.status_code == 200
    except Exception as e:
        logger.warning(f"Health check Google OAuth failed: {e}")
        return False

async def check_smtp() -> bool:
    if not settings.SMTP_HOST:
        return False
    try:
        def _check():
            with smtplib.SMTP(settings.SMTP_HOST, settings.SMTP_PORT, timeout=1.0) as server:
                if settings.SMTP_USE_TLS:
                    server.starttls()
                return True
        return await asyncio.to_thread(_check)
    except Exception as e:
        logger.warning(f"Health check SMTP failed: {e}")
        return False

async def check_storage() -> bool:
    if not settings.AWS_ACCESS_KEY_ID or not settings.AWS_SECRET_ACCESS_KEY:
        return False
    try:
        def _check():
            session = boto3.session.Session()
            client = session.client(
                "s3",
                aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
                aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
                endpoint_url=settings.AWS_S3_ENDPOINT_URL or None,
                config=Config(signature_version="s3v4", connect_timeout=1.0, read_timeout=1.0)
            )
            client.list_buckets()
            return True
        return await asyncio.to_thread(_check)
    except Exception as e:
        logger.warning(f"Health check Storage failed: {e}")
        return False

@router.get("/health", response_model=Dict[str, Any])
async def health_check():
    """
    Validates connectivity across database and infrastructure systems in parallel.
    Reports CPU, memory, and disk utilization along with connectivity states.
    """
    tasks = {
        "postgres": check_postgres(),
        "redis": check_redis(),
        "mongodb": check_mongo(),
        "qdrant": check_qdrant(),
        "celery": check_celery(),
        "rabbitmq": check_rabbitmq(),
        "openai": check_openai(),
        "meta_oauth": check_meta_oauth(),
        "twilio": check_twilio(),
        "google_oauth": check_google_oauth(),
        "smtp": check_smtp(),
        "storage": check_storage()
    }
    
    keys = list(tasks.keys())
    results = await asyncio.gather(*tasks.values())
    status_map = dict(zip(keys, results))
    
    # Requirements mapping
    requirements = {
        "postgres": "REQUIRED",
        "redis": "OPTIONAL",
        "mongodb": "OPTIONAL",
        "qdrant": "OPTIONAL",
        "celery": "OPTIONAL",
        "rabbitmq": "OPTIONAL",
        "openai": "OPTIONAL",
        "meta_oauth": "OPTIONAL",
        "twilio": "OPTIONAL",
        "google_oauth": "OPTIONAL",
        "smtp": "OPTIONAL",
        "storage": "OPTIONAL"
    }
    
    dependencies = {}
    for name in keys:
        connected = status_map[name]
        status_str = "CONNECTED" if connected else "DISCONNECTED"
        if not connected and requirements[name] == "OPTIONAL":
            status_str = "Optional / Not Configured"
        dependencies[name] = {
            "status": status_str,
            "requirement": requirements[name]
        }
        
    # App is degraded if any REQUIRED dependency is disconnected
    system_status = "healthy"
    for name, req in requirements.items():
        if req == "REQUIRED" and not status_map[name]:
            system_status = "degraded"
            break
            
    cpu_percent = psutil.cpu_percent(interval=0.1)
    vm = psutil.virtual_memory()
    disk = psutil.disk_usage(os.path.abspath(os.sep))
    
    return {
        "status": system_status,
        "environment": settings.ENVIRONMENT,
        "backend": "online",
        "cpu": {
            "percent": cpu_percent,
            "cores": os.cpu_count() or 1,
        },
        "memory": {
            "percent": vm.percent,
            "used_gb": round(vm.used / (1024 ** 3), 2),
            "total_gb": round(vm.total / (1024 ** 3), 2),
        },
        "disk": {
            "percent": round((disk.used / disk.total) * 100, 1) if disk.total else 0,
            "used_gb": round(disk.used / (1024 ** 3), 2),
            "total_gb": round(disk.total / (1024 ** 3), 2),
        },
        "workers": _workers_count(),
        "dependencies": dependencies
    }

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
