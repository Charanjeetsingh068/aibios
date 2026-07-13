import logging
import time
from contextlib import asynccontextmanager

import socketio
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.httpsredirect import HTTPSRedirectMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware

from app.api.v1.endpoints import (
    pipelines,
    ai,
    audit,
    auth,
    billing,
    dashboard,
    deals,
    documents,
    health,
    integration_manager,
    integrations,
    kb,
    leads,
    meta_integration,
    meta_sync,
    meta_webhooks,
    oauth,
    organizations,
    reports,
    roles,
    system,
    teams,
    twilio_integration,
    users,
    voice,
    voice_providers,
    whatsapp,
    workflows,
)
from app.core import telemetry
from app.core.config import settings
from app.core.database import (
    AsyncSessionLocal,
    SqliteSessionLocal,
    init_mongo_indexes,
    is_postgres_offline,
    postgres_engine,
    seed_database,
    sqlite_engine,
)
from app.core.realtime import sio
from app.core.security import get_security_headers
from app.models import (
    business as _business_models,  # noqa: F401 ensures tables register on Base.metadata
)
from app.models import (
    enterprise_integrations as _enterprise_integrations_models,  # noqa: F401 ensures tables register on Base.metadata
)
from app.models import (
    integrations as _integrations_models,  # noqa: F401 ensures tables register on Base.metadata
)
from app.models.auth import Base

# Setup logger
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    handlers=[logging.StreamHandler()]
)
logger = logging.getLogger(__name__)

@asynccontextmanager
async def lifespan(app: FastAPI):
    from app.core.env_check import validate_environment_on_startup
    validate_environment_on_startup()

    # Startup: Run schema migrations and seed data
    logger.info("Initializing relational database schema...")
    use_sqlite = await is_postgres_offline()
    engine = sqlite_engine if use_sqlite else postgres_engine
    
    # Create all tables dynamically
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    logger.info("Relational database schema initialized.")
    
    # Seed default roles, permissions, organization, and super admin
    session_factory = SqliteSessionLocal if use_sqlite else AsyncSessionLocal
    async with session_factory() as session:
        await seed_database(session)
    logger.info("Default seed metadata successfully populated.")
    
    # Initialize MongoDB collections index
    logger.info("Initializing MongoDB indexes...")
    await init_mongo_indexes()

    # Initialize Qdrant collection
    logger.info("Initializing Qdrant collections...")
    from app.core.qdrant_vector import init_qdrant_collection
    init_qdrant_collection()
    
    yield

# Initialize FastAPI application with lifespan context
fastapi_app = FastAPI(
    title=settings.PROJECT_NAME,
    description="AI-BOS Enterprise Business Operating System Backend Gateway",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
    lifespan=lifespan
)

# Apply CORS Middleware
if settings.BACKEND_CORS_ORIGINS:
    fastapi_app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.BACKEND_CORS_ORIGINS,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

# Apply HTTPS Redirection in Production
if settings.ENVIRONMENT == "production":
    fastapi_app.add_middleware(HTTPSRedirectMiddleware)

# Apply Trusted Hosts Middleware
if settings.ENVIRONMENT == "production":
    # Strict list of allowed hosts in production, driven by ALLOWED_HOSTS env var
    if not settings.ALLOWED_HOSTS:
        logger.warning(
            "ENVIRONMENT=production but ALLOWED_HOSTS is not set — all Host headers will be "
            "rejected by TrustedHostMiddleware. Set ALLOWED_HOSTS to your real domain(s)."
        )
    fastapi_app.add_middleware(TrustedHostMiddleware, allowed_hosts=settings.ALLOWED_HOSTS or [])
else:
    # Allow localhost, 127.0.0.1, and subdomains in development
    fastapi_app.add_middleware(TrustedHostMiddleware, allowed_hosts=["localhost", "127.0.0.1", "*.localhost"])

from fastapi.responses import JSONResponse

from app.core.redis_cache import RedisRateLimiter

limiter = RedisRateLimiter()


@fastapi_app.middleware("http")
async def rate_limiting_middleware(request: Request, call_next):
    if request.url.path.startswith(settings.API_V1_STR) and not request.url.path.endswith("/health"):
        client_ip = request.client.host if request.client else "unknown"
        endpoint = request.url.path
        if await limiter.is_rate_limited(client_ip, endpoint, limit=120, period_seconds=60):
            return JSONResponse(
                status_code=429,
                content={"detail": "Too many requests. Please check back in a minute."}
            )
    return await call_next(request)


# Execution Time & Security Headers Middleware
@fastapi_app.middleware("http")
async def add_timing_and_security_headers(request: Request, call_next):
    start_time = time.time()
    response = await call_next(request)

    # Custom timing header
    process_time = time.time() - start_time
    response.headers["X-Response-Time-Sec"] = f"{process_time:.4f}"
    telemetry.record_request(process_time * 1000)

    # Fetch environment-specific security headers dynamically
    security_headers = get_security_headers(settings.ENVIRONMENT)
    for header_name, header_value in security_headers.items():
        response.headers[header_name] = header_value

    return response

fastapi_app.include_router(health.router, prefix=settings.API_V1_STR, tags=["System Health"])
fastapi_app.include_router(system.router, prefix=settings.API_V1_STR + "/system", tags=["System Diagnostics"])
fastapi_app.include_router(auth.router, prefix=settings.API_V1_STR + "/auth", tags=["Enterprise Authentication"])
fastapi_app.include_router(dashboard.router, prefix=settings.API_V1_STR + "/dashboard", tags=["Enterprise Dashboard"])
fastapi_app.include_router(leads.router, prefix=settings.API_V1_STR + "/leads", tags=["Leads"])
fastapi_app.include_router(pipelines.router, prefix=settings.API_V1_STR + "/pipelines", tags=["Pipelines"])
fastapi_app.include_router(deals.router, prefix=settings.API_V1_STR + "/deals", tags=["Deals / Pipeline"])
fastapi_app.include_router(integrations.router, prefix=settings.API_V1_STR + "/integrations", tags=["Integrations"])
fastapi_app.include_router(meta_integration.router, prefix=settings.API_V1_STR + "/integrations/meta", tags=["Meta Platform Integration"])
fastapi_app.include_router(meta_webhooks.router, prefix=settings.API_V1_STR + "/integrations/meta/webhook", tags=["Meta Webhooks"])
fastapi_app.include_router(meta_sync.router, prefix=settings.API_V1_STR + "/integrations/meta/sync", tags=["Meta Sync"])
fastapi_app.include_router(integration_manager.router, prefix=settings.API_V1_STR + "/integrations/manager", tags=["Integration Manager"])
fastapi_app.include_router(organizations.router, prefix=settings.API_V1_STR + "/organizations", tags=["Organizations (Super Admin)"])
fastapi_app.include_router(users.router, prefix=settings.API_V1_STR + "/users", tags=["User Management"])
fastapi_app.include_router(teams.router, prefix=settings.API_V1_STR + "/teams", tags=["Team Management"])
fastapi_app.include_router(roles.router, prefix=settings.API_V1_STR + "/roles", tags=["Role Management"])
fastapi_app.include_router(audit.router, prefix=settings.API_V1_STR + "/audit", tags=["Audit Log"])
fastapi_app.include_router(workflows.router, prefix=settings.API_V1_STR + "/workflows", tags=["Workflows / Automations"])
fastapi_app.include_router(kb.router, prefix=settings.API_V1_STR + "/kb", tags=["Knowledge Base"])
fastapi_app.include_router(documents.router, prefix=settings.API_V1_STR + "/documents", tags=["Documents"])
fastapi_app.include_router(voice.router, prefix=settings.API_V1_STR + "/voice", tags=["AI Voice"])
fastapi_app.include_router(voice_providers.router, prefix=settings.API_V1_STR + "/voice", tags=["AI Voice Platform"])
fastapi_app.include_router(reports.router, prefix=settings.API_V1_STR + "/reports", tags=["Reports"])
fastapi_app.include_router(billing.router, prefix=settings.API_V1_STR + "/billing", tags=["Billing"])
fastapi_app.include_router(oauth.router, prefix=settings.API_V1_STR + "/oauth", tags=["OAuth Authentication"])
fastapi_app.include_router(whatsapp.router, prefix=settings.API_V1_STR + "/whatsapp", tags=["WhatsApp Platform"])
fastapi_app.include_router(twilio_integration.router, prefix=settings.API_V1_STR + "/twilio", tags=["Twilio Platform"])
fastapi_app.include_router(ai.router, prefix=settings.API_V1_STR + "/ai", tags=["AI / OpenAI"])

@fastapi_app.get("/")
async def root():
    return {
        "message": f"Welcome to the {settings.PROJECT_NAME} Platform",
        "api_documentation": "/docs",
        "status": "online"
    }

# Mount Socket.IO alongside the REST API so `uvicorn app.main:app` serves both.
app = socketio.ASGIApp(sio, other_asgi_app=fastapi_app, socketio_path="socket.io")
