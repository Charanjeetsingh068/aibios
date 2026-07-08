import time
import logging
import socketio
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.middleware.httpsredirect import HTTPSRedirectMiddleware
from app.core.config import settings
from app.core.security import get_security_headers
from app.core import telemetry
from app.core.realtime import sio
from app.api.v1.endpoints import health, system, auth, dashboard, leads, deals, integrations, workflows, kb, documents, voice, reports, billing, oauth, whatsapp, twilio_integration
from app.core.database import is_postgres_offline, sqlite_engine, postgres_engine, seed_database, SqliteSessionLocal, AsyncSessionLocal, init_mongo_indexes
from app.models.auth import Base
from app.models import business as _business_models  # noqa: F401 ensures tables register on Base.metadata
from app.models import integrations as _integrations_models  # noqa: F401 ensures tables register on Base.metadata

# Setup logger
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    handlers=[logging.StreamHandler()]
)
logger = logging.getLogger(__name__)

@asynccontextmanager
async def lifespan(app: FastAPI):
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
fastapi_app.include_router(deals.router, prefix=settings.API_V1_STR + "/deals", tags=["Deals / Pipeline"])
fastapi_app.include_router(integrations.router, prefix=settings.API_V1_STR + "/integrations", tags=["Integrations"])
fastapi_app.include_router(workflows.router, prefix=settings.API_V1_STR + "/workflows", tags=["Workflows / Automations"])
fastapi_app.include_router(kb.router, prefix=settings.API_V1_STR + "/kb", tags=["Knowledge Base"])
fastapi_app.include_router(documents.router, prefix=settings.API_V1_STR + "/documents", tags=["Documents"])
fastapi_app.include_router(voice.router, prefix=settings.API_V1_STR + "/voice", tags=["AI Voice"])
fastapi_app.include_router(reports.router, prefix=settings.API_V1_STR + "/reports", tags=["Reports"])
fastapi_app.include_router(billing.router, prefix=settings.API_V1_STR + "/billing", tags=["Billing"])
fastapi_app.include_router(oauth.router, prefix=settings.API_V1_STR + "/oauth", tags=["OAuth Authentication"])
fastapi_app.include_router(whatsapp.router, prefix=settings.API_V1_STR + "/whatsapp", tags=["WhatsApp Platform"])
fastapi_app.include_router(twilio_integration.router, prefix=settings.API_V1_STR + "/twilio", tags=["Twilio Platform"])

@fastapi_app.get("/")
async def root():
    return {
        "message": f"Welcome to the {settings.PROJECT_NAME} Platform",
        "api_documentation": "/docs",
        "status": "online"
    }

# Mount Socket.IO alongside the REST API so `uvicorn app.main:app` serves both.
app = socketio.ASGIApp(sio, other_asgi_app=fastapi_app, socketio_path="socket.io")
