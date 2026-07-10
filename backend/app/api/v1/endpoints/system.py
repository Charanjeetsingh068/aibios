import asyncio
import datetime
import logging
import os
import platform
import socket
import sys
import time
from typing import Any, Dict

from fastapi import APIRouter

# Resolve workspace root directory to import the agents module
_current = os.path.abspath(__file__)
while _current:
    _parent = os.path.dirname(_current)
    if _parent == _current:
        break
    if os.path.exists(os.path.join(_parent, "agents", "graph", "workflow.py")):
        if _parent not in sys.path:
            sys.path.append(_parent)
        break
    _current = _parent

from agents.graph.workflow import graph

from app.core.config import settings
from app.core.database import (
    AsyncSessionLocal,
    SqliteSessionLocal,
    is_postgres_offline,
    mongo_client,
    redis_client,
    verify_mongo,
    verify_postgres,
    verify_qdrant,
    verify_redis,
)

logger = logging.getLogger(__name__)
router = APIRouter()

START_TIME = time.time()

def get_uptime() -> str:
    uptime_seconds = int(time.time() - START_TIME)
    days, extra = divmod(uptime_seconds, 86400)
    hours, extra = divmod(extra, 3600)
    minutes, extra = divmod(extra, 60)
    
    parts = []
    if days > 0:
        parts.append(f"{days}d")
    if hours > 0:
        parts.append(f"{hours}h")
    if minutes > 0:
        parts.append(f"{minutes}m")
    parts.append(f"{extra}s")
    return " ".join(parts)

def get_memory_info() -> Dict[str, str]:
    try:
        if platform.system() == "Windows":
            import ctypes
            class MEMORYSTATUSEX(ctypes.Structure):
                _fields_ = [
                    ("dwLength", ctypes.c_ulong),
                    ("dwMemoryLoad", ctypes.c_ulong),
                    ("ullTotalPhys", ctypes.c_ulonglong),
                    ("ullAvailPhys", ctypes.c_ulonglong),
                    ("ullTotalPageFile", ctypes.c_ulonglong),
                    ("ullAvailPageFile", ctypes.c_ulonglong),
                    ("ullTotalVirtual", ctypes.c_ulonglong),
                    ("ullAvailVirtual", ctypes.c_ulonglong),
                    ("ullAvailExtendedVirtual", ctypes.c_ulonglong)
                ]
            stat = MEMORYSTATUSEX()
            stat.dwLength = ctypes.sizeof(stat)
            if ctypes.windll.kernel32.GlobalMemoryStatusEx(ctypes.byref(stat)):
                total = stat.ullTotalPhys
                avail = stat.ullAvailPhys
                used = total - avail
                load = stat.dwMemoryLoad
                return {
                    "total": f"{total / (1024**3):.2f} GB",
                    "available": f"{avail / (1024**3):.2f} GB",
                    "used": f"{used / (1024**3):.2f} GB",
                    "percent_used": f"{load}%"
                }
        else:
            with open('/proc/meminfo', 'r') as f:
                lines = f.readlines()
            total = 0
            free = 0
            buffers = 0
            cached = 0
            for line in lines:
                if line.strip().startswith('MemTotal:'):
                    total = int(line.split()[1]) * 1024
                elif line.strip().startswith('MemFree:'):
                    free = int(line.split()[1]) * 1024
                elif line.strip().startswith('Buffers:'):
                    buffers = int(line.split()[1]) * 1024
                elif line.strip().startswith('Cached:'):
                    cached = int(line.split()[1]) * 1024
            available = free + buffers + cached
            used = total - available
            pct = (used / total) * 100 if total > 0 else 0
            return {
                "total": f"{total / (1024**3):.2f} GB",
                "available": f"{available / (1024**3):.2f} GB",
                "used": f"{used / (1024**3):.2f} GB",
                "percent_used": f"{pct:.1f}%"
            }
    except Exception as e:
        return {"error": f"Failed memory query: {e}"}
    return {"total": "N/A", "available": "N/A", "used": "N/A", "percent_used": "0%"}

@router.get("/status", response_model=Dict[str, Any])
async def system_status():
    """Returns general application environment status, runtime version, and uptime."""
    return {
        "backend": "online",
        "version": "1.0.0",
        "environment": settings.ENVIRONMENT,
        "uptime": get_uptime(),
        "python_version": platform.python_version(),
        "fastapi": "running"
    }

@router.get("/info", response_model=Dict[str, Any])
async def system_info():
    """Returns system parameters, platform specs, CPU count, and timezone info."""
    mem = get_memory_info()
    return {
        "app_name": settings.PROJECT_NAME,
        "app_version": "1.0.0",
        "os": platform.system(),
        "hostname": socket.gethostname(),
        "current_time": datetime.datetime.now().isoformat(),
        "timezone": time.tzname[0] if time.tzname else "UTC",
        "memory": f"{mem.get('used', 'N/A')} / {mem.get('total', 'N/A')} ({mem.get('percent_used', 'N/A')})",
        "cpu_count": os.cpu_count() or 1,
        "platform": platform.platform()
    }

async def _check_with_latency(check_fn):
    start = time.perf_counter()
    ok = await check_fn()
    latency_ms = round((time.perf_counter() - start) * 1000, 2)
    return ok, latency_ms


async def _postgres_version(use_sqlite: bool) -> str:
    try:
        from sqlalchemy import text
        session_factory = SqliteSessionLocal if use_sqlite else AsyncSessionLocal
        async with session_factory() as session:
            if use_sqlite:
                result = await session.execute(text("SELECT sqlite_version()"))
            else:
                result = await session.execute(text("SHOW server_version"))
            return str(result.scalar() or "unknown")
    except Exception as e:
        logger.error(f"Failed to read database version: {e}")
        return "unknown"


async def _mongo_version() -> str:
    try:
        info = await asyncio.wait_for(mongo_client.admin.command("buildInfo"), timeout=2.0)
        return str(info.get("version", "unknown"))
    except Exception as e:
        logger.error(f"Failed to read MongoDB version: {e}")
        return "unknown"


async def _redis_version() -> str:
    try:
        info = await asyncio.wait_for(redis_client.info(), timeout=2.0)
        return str(info.get("redis_version", "unknown"))
    except Exception as e:
        logger.error(f"Failed to read Redis version: {e}")
        return "unknown"


@router.get("/database", response_model=Dict[str, Any])
async def system_database():
    """Runs live connectivity checks on all configured databases in parallel (Postgres, Mongo, Redis, Qdrant),
    reporting connection status, round-trip latency, and server version for each."""
    use_sqlite = await is_postgres_offline()

    (postgres_ok, postgres_latency), (mongo_ok, mongo_latency), (redis_ok, redis_latency), (qdrant_ok, qdrant_latency) = await asyncio.gather(
        _check_with_latency(verify_postgres),
        _check_with_latency(verify_mongo),
        _check_with_latency(verify_redis),
        _check_with_latency(verify_qdrant),
    )

    postgres_version, mongo_version, redis_version = await asyncio.gather(
        _postgres_version(use_sqlite), _mongo_version(), _redis_version()
    )

    return {
        "postgres": {
            "connected": postgres_ok,
            "latency_ms": postgres_latency,
            "version": postgres_version,
            "engine": "SQLite (fallback)" if use_sqlite else "PostgreSQL",
        },
        "mongodb": {"connected": mongo_ok, "latency_ms": mongo_latency, "version": mongo_version},
        "redis": {"connected": redis_ok, "latency_ms": redis_latency, "version": redis_version},
        "qdrant": {"connected": qdrant_ok, "latency_ms": qdrant_latency, "version": "unknown"},
    }

@router.get("/agents", response_model=Dict[str, Any])
async def system_agents():
    """Queries compiled LangGraph workflows to report current installation status of worker agents."""
    nodes = list(graph.nodes.keys()) if hasattr(graph, 'nodes') else []
    return {
        "supervisor_agent": "Running" if "supervisor" in nodes else "Not Installed",
        "planner_agent": "Running" if "planner" in nodes else "Not Installed",
        "executor_agent": "Running" if "crm_agent" in nodes or "db_agent" in nodes else "Not Installed",
        "developer_agent": "Running" if "developer" in nodes else "Not Installed"
    }
