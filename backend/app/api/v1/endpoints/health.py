import asyncio
import os
from typing import Any, Dict

import psutil
from fastapi import APIRouter

from app.core.config import settings
from app.core.database import verify_mongo, verify_postgres, verify_qdrant, verify_redis
from app.core.env_check import get_integration_statuses

router = APIRouter()


def _workers_count() -> int:
    return int(os.environ.get("WEB_CONCURRENCY", os.environ.get("WORKERS", 1)))


@router.get("/health", response_model=Dict[str, Any])
async def health_check():
    """
    Validates connectivity across database systems in parallel.
    Runs active pings for PostgreSQL, MongoDB, Redis, and Qdrant, and reports
    live CPU, memory, and disk utilization for the backend host.
    """
    postgres_task = verify_postgres()
    mongo_task = verify_mongo()
    redis_task = verify_redis()
    qdrant_task = verify_qdrant()

    postgres_status, mongo_status, redis_status, qdrant_status = await asyncio.gather(
        postgres_task, mongo_task, redis_task, qdrant_task
    )

    system_status = "healthy"
    if not (postgres_status and mongo_status and redis_status and qdrant_status):
        system_status = "degraded"

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
        "dependencies": {
            "postgres": "online" if postgres_status else "offline",
            "mongodb": "online" if mongo_status else "offline",
            "redis": "online" if redis_status else "offline",
            "qdrant_vector_db": "online" if qdrant_status else "offline",
        },
        "integrations": get_integration_statuses(),
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
