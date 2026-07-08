import logging
import asyncio
from typing import AsyncGenerator
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from motor.motor_asyncio import AsyncIOMotorClient
import redis.asyncio as aioredis
from qdrant_client import QdrantClient
from app.core.config import settings

logger = logging.getLogger(__name__)

# ------------------------------------------------------------------------------
# 1. PostgreSQL (SQLAlchemy Async) Setup
# ------------------------------------------------------------------------------
postgres_engine = create_async_engine(
    settings.async_sqlalchemy_database_uri,
    pool_pre_ping=True,
    echo=False
)

AsyncSessionLocal = async_sessionmaker(
    bind=postgres_engine,
    autocommit=False,
    autoflush=False,
    expire_on_commit=False
)

# ------------------------------------------------------------------------------
# 1b. SQLite Fallback Setup (Local-First development safety)
# ------------------------------------------------------------------------------
import os
fallback_db_path = "d:/react-website/aibios/database/postgres/fallback.db"
os.makedirs(os.path.dirname(fallback_db_path), exist_ok=True)

sqlite_engine = create_async_engine(
    f"sqlite+aiosqlite:///{fallback_db_path}",
    echo=False
)

SqliteSessionLocal = async_sessionmaker(
    bind=sqlite_engine,
    autocommit=False,
    autoflush=False,
    expire_on_commit=False
)

_sqlite_fallback_active = None

async def is_postgres_offline() -> bool:
    global _sqlite_fallback_active
    if _sqlite_fallback_active is not None:
        return _sqlite_fallback_active
    try:
        async with AsyncSessionLocal() as session:
            from sqlalchemy import text
            await asyncio.wait_for(session.execute(text("SELECT 1")), timeout=1.0)
        _sqlite_fallback_active = False
    except Exception:
        logger.warning("PostgreSQL is unreachable. Falling back to local SQLite database.")
        _sqlite_fallback_active = True
    return _sqlite_fallback_active

async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """Dependency generator for database sessions in FastAPI routes."""
    use_sqlite = await is_postgres_offline()
    session_factory = SqliteSessionLocal if use_sqlite else AsyncSessionLocal
    
    async with session_factory() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()

# ------------------------------------------------------------------------------
# 2. MongoDB Setup
# ------------------------------------------------------------------------------
mongo_client = AsyncIOMotorClient(settings.MONGODB_URL)
mongo_db = mongo_client.get_default_database()

# ------------------------------------------------------------------------------
# 3. Redis Setup
# ------------------------------------------------------------------------------
redis_client = aioredis.Redis(
    host=settings.REDIS_HOST,
    port=settings.REDIS_PORT,
    db=settings.REDIS_DB,
    password=settings.REDIS_PASSWORD or None,
    decode_responses=True
)

# ------------------------------------------------------------------------------
# 4. Qdrant (Vector DB) Setup
# ------------------------------------------------------------------------------
def get_qdrant_client() -> QdrantClient:
    """Returns a connection to the Qdrant Vector database."""
    # Since Qdrant client connection is synchronous in standard API usage,
    # we instantiate it on request or keep it as a reusable singleton.
    return QdrantClient(
        host=settings.QDRANT_HOST,
        port=settings.QDRANT_PORT,
        api_key=settings.QDRANT_API_KEY or None,
        timeout=2.0
    )

# ------------------------------------------------------------------------------
# 5. Database Verification/Health Checks
# ------------------------------------------------------------------------------
async def verify_postgres() -> bool:
    try:
        use_sqlite = await is_postgres_offline()
        session_factory = SqliteSessionLocal if use_sqlite else AsyncSessionLocal
        async with session_factory() as session:
            from sqlalchemy import text
            await asyncio.wait_for(session.execute(text("SELECT 1")), timeout=2.0)
        return True
    except Exception as e:
        logger.error(f"Database connection verification failed: {e}")
        return False

async def verify_mongo() -> bool:
    try:
        # Motor has built-in connection timeouts configured in the URL or client
        await asyncio.wait_for(mongo_client.admin.command('ping'), timeout=2.0)
        return True
    except Exception as e:
        logger.error(f"MongoDB connection verification failed: {e}")
        return False

async def verify_redis() -> bool:
    try:
        await asyncio.wait_for(redis_client.ping(), timeout=2.0)
        return True
    except Exception as e:
        logger.error(f"Redis connection verification failed: {e}")
        return False

async def verify_qdrant() -> bool:
    try:
        client = get_qdrant_client()
        await asyncio.wait_for(asyncio.to_thread(client.get_collections), timeout=2.0)
        return True
    except Exception as e:
        logger.error(f"Qdrant connection verification failed: {e}")
        return False

# ------------------------------------------------------------------------------
# 6. Database Seeding Routine
# ------------------------------------------------------------------------------
async def seed_database(session):
    """
    Seeds the relational database with default Roles, Permissions, a Demo Org,
    and a Super Admin account. Self-healing/idempotent.
    """
    from app.models.auth import Permission, Role, Organization, User
    from app.core.security import get_password_hash
    from sqlalchemy import select
    
    # 1. Seed Permissions
    permissions_data = [
        {"id": "admin:all", "name": "All Administration", "description": "Unrestricted administrative privilege"},
        {"id": "org:read", "name": "Read Organization", "description": "Read tenant organization parameters"},
        {"id": "org:write", "name": "Write Organization", "description": "Modify tenant organization parameters"},
        {"id": "leads:read", "name": "Read Leads", "description": "Read leads metrics and profiles"},
        {"id": "leads:write", "name": "Write Leads", "description": "Create and edit lead profiles"},
        {"id": "agents:read", "name": "Read Agents", "description": "Read LangGraph agent statuses and nodes"},
        {"id": "agents:write", "name": "Write Agents", "description": "Configure agent flows and tools"}
    ]
    
    for p in permissions_data:
        perm = await session.get(Permission, p["id"])
        if not perm:
            session.add(Permission(**p))
    await session.commit()
    
    # 2. Seed Roles
    roles_data = [
        {"id": "super_admin", "name": "Super Admin", "description": "Global administrator control", "permissions": ["admin:all"]},
        {"id": "org_admin", "name": "Organization Admin", "description": "Tenant administrator control", "permissions": ["org:read", "org:write", "leads:read", "leads:write", "agents:read", "agents:write"]},
        {"id": "manager", "name": "Manager", "description": "Team lead manager", "permissions": ["leads:read", "leads:write", "agents:read"]},
        {"id": "sales_executive", "name": "Sales Executive", "description": "CRM executive worker", "permissions": ["leads:read", "leads:write"]},
        {"id": "ai_agent", "name": "AI Agent", "description": "Autonomous worker agent", "permissions": ["leads:read", "leads:write", "agents:read"]},
        {"id": "developer", "name": "Developer", "description": "Developer node configurer", "permissions": ["agents:read", "agents:write"]},
        {"id": "auditor", "name": "Auditor", "description": "Security logs auditor", "permissions": ["leads:read", "agents:read"]},
        {"id": "viewer", "name": "Viewer", "description": "Read-only access", "permissions": ["leads:read"]}
    ]
    
    for r in roles_data:
        role = await session.get(Role, r["id"])
        if not role:
            role_obj = Role(id=r["id"], name=r["name"], description=r["description"])
            for p_id in r["permissions"]:
                perm = await session.get(Permission, p_id)
                if perm:
                    role_obj.permissions.append(perm)
            session.add(role_obj)
    await session.commit()
    
    # 3. Seed Demo Organization
    demo_org_slug = "demo"
    q_org = await session.execute(select(Organization).where(Organization.slug == demo_org_slug))
    demo_org = q_org.scalar_one_or_none()
    
    if not demo_org:
        demo_org = Organization(
            id="demo-org-uuid-placeholder-123456",
            name="Demo Corp",
            slug=demo_org_slug,
            status="active"
        )
        session.add(demo_org)
        await session.commit()
        
    # 4. Seed Super Admin User
    admin_email = "charanjeet.s7730@gmail.com"
    q_user = await session.execute(select(User).where(User.email == admin_email))
    admin_user = q_user.scalar_one_or_none()
    
    if not admin_user:
        admin_user = User(
            id="superadmin-uuid-placeholder-123456",
            organization_id=demo_org.id,
            first_name="Charanjeet",
            last_name="Singh",
            email=admin_email,
            password_hash=get_password_hash("123456"),
            role_id="super_admin",
            status="active"
        )
        session.add(admin_user)
        await session.commit()
