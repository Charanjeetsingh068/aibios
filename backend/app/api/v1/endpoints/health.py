from typing import Any, Dict
import asyncio
from fastapi import APIRouter
from app.core.database import verify_postgres, verify_mongo, verify_redis, verify_qdrant

router = APIRouter()

@router.get("/health", response_model=Dict[str, Any])
async def health_check():
    """
    Validates connectivity across database systems in parallel.
    Runs active pings for PostgreSQL, MongoDB, Redis, and Qdrant.
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

    return {
        "status": system_status,
        "environment": "development",
        "dependencies": {
            "postgres": "online" if postgres_status else "offline",
            "mongodb": "online" if mongo_status else "offline",
            "redis": "online" if redis_status else "offline",
            "qdrant_vector_db": "online" if qdrant_status else "offline",
        }
    }
