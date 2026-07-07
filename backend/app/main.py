import time
import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.middleware.httpsredirect import HTTPSRedirectMiddleware
from app.core.config import settings
from app.core.security import get_security_headers
from app.api.v1.endpoints import health, system, auth
from app.core.database import is_postgres_offline, sqlite_engine, postgres_engine, seed_database, SqliteSessionLocal, AsyncSessionLocal
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
    
    yield

# Initialize FastAPI application with lifespan context
app = FastAPI(
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
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.BACKEND_CORS_ORIGINS,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

# Apply HTTPS Redirection in Production
if settings.ENVIRONMENT == "production":
    app.add_middleware(HTTPSRedirectMiddleware)

# Apply Trusted Hosts Middleware
if settings.ENVIRONMENT == "production":
    # Strict list of allowed hosts in production
    app.add_middleware(TrustedHostMiddleware, allowed_hosts=["example.com", "*.example.com"])
else:
    # Allow localhost, 127.0.0.1, and subdomains in development
    app.add_middleware(TrustedHostMiddleware, allowed_hosts=["localhost", "127.0.0.1", "*.localhost"])

# Execution Time & Security Headers Middleware
@app.middleware("http")
async def add_timing_and_security_headers(request: Request, call_next):
    start_time = time.time()
    response = await call_next(request)
    
    # Custom timing header
    process_time = time.time() - start_time
    response.headers["X-Response-Time-Sec"] = f"{process_time:.4f}"
    
    # Fetch environment-specific security headers dynamically
    security_headers = get_security_headers(settings.ENVIRONMENT)
    for header_name, header_value in security_headers.items():
        response.headers[header_name] = header_value
        
    return response

app.include_router(health.router, prefix=settings.API_V1_STR, tags=["System Health"])
app.include_router(system.router, prefix=settings.API_V1_STR + "/system", tags=["System Diagnostics"])
app.include_router(auth.router, prefix=settings.API_V1_STR + "/auth", tags=["Enterprise Authentication"])

@app.get("/")
async def root():
    return {
        "message": f"Welcome to the {settings.PROJECT_NAME} Platform",
        "api_documentation": "/docs",
        "status": "online"
    }
# Trigger reload to load new env settings
