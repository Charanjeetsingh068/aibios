import logging
import asyncio
import time
import uuid
from typing import AsyncGenerator, Optional, List, Dict, Any
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
    if settings.ENVIRONMENT in ("production", "prod"):
        return False
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
_raw_redis_client = aioredis.Redis(
    host=settings.REDIS_HOST,
    port=settings.REDIS_PORT,
    db=settings.REDIS_DB,
    password=settings.REDIS_PASSWORD or None,
    decode_responses=True
)

class SafeRedisPipeline:
    def __init__(self, safe_client):
        self.safe_client = safe_client
        self.commands = []

    def set(self, key, value):
        self.commands.append(("set", key, value))

    def expire(self, key, seconds):
        self.commands.append(("expire", key, seconds))

    async def execute(self):
        for cmd in self.commands:
            if cmd[0] == "set":
                await self.safe_client.set(cmd[1], cmd[2])
            elif cmd[0] == "expire":
                await self.safe_client.expire(cmd[1], cmd[2])
        return []

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        pass

class SafeRedisClient:
    # How often to retry a real connection after Redis was last seen offline. Without this,
    # a transient outage would be cached as "offline" forever until the process restarts.
    RECHECK_INTERVAL_SECONDS = 30

    def __init__(self, real_client):
        self.real_client = real_client
        self._local_storage = {}
        self._local_expiry: Dict[str, float] = {}
        self._is_online = None
        self._last_checked_at = 0.0

    def _purge_if_expired(self, key: str) -> None:
        expires_at = self._local_expiry.get(key)
        if expires_at is not None and time.monotonic() >= expires_at:
            self._local_storage.pop(key, None)
            self._local_expiry.pop(key, None)

    async def _test_connection(self) -> bool:
        now = time.monotonic()
        if self._is_online is not None and (now - self._last_checked_at) < self.RECHECK_INTERVAL_SECONDS:
            return self._is_online
        try:
            await asyncio.wait_for(self.real_client.ping(), timeout=1.0)
            if not self._is_online:
                logger.info("Redis connection restored.")
            self._is_online = True
        except Exception:
            if self._is_online is not False:
                logger.warning("Redis is offline. Falling back to local mock storage.")
            self._is_online = False
        self._last_checked_at = now
        return self._is_online

    async def ping(self) -> bool:
        if await self._test_connection():
            try:
                return await self.real_client.ping()
            except Exception:
                self._is_online = False
        return True

    async def get(self, key: str) -> Optional[str]:
        if await self._test_connection():
            try:
                return await self.real_client.get(key)
            except Exception:
                self._is_online = False
        self._purge_if_expired(key)
        return self._local_storage.get(key)

    async def set(self, key: str, value: Any, ex: Optional[int] = None) -> bool:
        if await self._test_connection():
            try:
                return await self.real_client.set(key, value, ex=ex)
            except Exception:
                self._is_online = False
        self._local_storage[key] = str(value)
        if ex is not None:
            self._local_expiry[key] = time.monotonic() + ex
        else:
            self._local_expiry.pop(key, None)
        return True

    async def expire(self, key: str, seconds: int) -> bool:
        if await self._test_connection():
            try:
                return await self.real_client.expire(key, seconds)
            except Exception:
                self._is_online = False
        if key in self._local_storage:
            self._local_expiry[key] = time.monotonic() + seconds
        return True

    async def incr(self, key: str) -> int:
        if await self._test_connection():
            try:
                return await self.real_client.incr(key)
            except Exception:
                self._is_online = False
        self._purge_if_expired(key)
        current = int(self._local_storage.get(key, 0)) + 1
        self._local_storage[key] = str(current)
        return current

    async def keys(self, pattern: str) -> List[str]:
        if await self._test_connection():
            try:
                return await self.real_client.keys(pattern)
            except Exception:
                self._is_online = False
        import fnmatch
        for k in list(self._local_storage.keys()):
            self._purge_if_expired(k)
        return [k for k in self._local_storage.keys() if fnmatch.fnmatch(k, pattern)]

    async def delete(self, *keys) -> int:
        if await self._test_connection():
            try:
                return await self.real_client.delete(*keys)
            except Exception:
                self._is_online = False
        deleted = 0
        for k in keys:
            if k in self._local_storage:
                del self._local_storage[k]
                deleted += 1
        return deleted

    def pipeline(self, transaction: bool = True) -> SafeRedisPipeline:
        return SafeRedisPipeline(self)

    async def info(self) -> Dict[str, Any]:
        if await self._test_connection():
            try:
                return await self.real_client.info()
            except Exception:
                self._is_online = False
        return {"redis_version": "mock-fallback-5.0.0"}

redis_client = SafeRedisClient(_raw_redis_client)

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
    
    # 1. Seed Permissions — dot notation "module.action" per spec (e.g. "leads.read"),
    # so the permission catalog can be listed/assigned generically by the role-management
    # UI instead of the module needing hardcoded knowledge of each permission's shape.
    permissions_data = [
        {"id": "admin.all", "name": "All Administration", "description": "Unrestricted administrative privilege (super admin wildcard)"},
        # Organizations (platform-level, super admin only)
        {"id": "organizations.read", "name": "Read Organizations", "description": "List/view tenant organizations"},
        {"id": "organizations.write", "name": "Write Organizations", "description": "Create/edit tenant organizations"},
        {"id": "organizations.delete", "name": "Delete Organizations", "description": "Delete tenant organizations"},
        {"id": "organizations.suspend", "name": "Suspend Organizations", "description": "Suspend/reactivate tenant organizations"},
        # Users
        {"id": "users.read", "name": "Read Users", "description": "List/view users"},
        {"id": "users.write", "name": "Write Users", "description": "Create/edit users"},
        {"id": "users.delete", "name": "Delete Users", "description": "Delete (soft-delete) users"},
        {"id": "users.suspend", "name": "Suspend Users", "description": "Suspend/reactivate users"},
        {"id": "users.invite", "name": "Invite Users", "description": "Invite new users by email"},
        {"id": "users.reset_password", "name": "Reset User Password", "description": "Trigger a password reset for another user"},
        {"id": "users.assign_role", "name": "Assign User Roles", "description": "Assign/remove roles on a user"},
        # Roles & permissions
        {"id": "roles.read", "name": "Read Roles", "description": "List/view roles and the permission catalog"},
        {"id": "roles.write", "name": "Write Roles", "description": "Create/edit roles"},
        {"id": "roles.delete", "name": "Delete Roles", "description": "Delete roles"},
        {"id": "roles.assign_permission", "name": "Assign Role Permissions", "description": "Assign/remove permissions on a role"},
        # Audit
        {"id": "audit.read", "name": "Read Audit Log", "description": "View audit log entries"},
        # Integrations — module-level
        {"id": "integrations.read", "name": "Read Integrations", "description": "View integration connection status and health"},
        {"id": "integrations.write", "name": "Write Integrations", "description": "Connect/disconnect integrations and manage their configuration"},
        # Facebook / Instagram
        {"id": "facebook.read", "name": "Read Facebook", "description": "View Facebook pages, forms, and leads"},
        {"id": "facebook.write", "name": "Write Facebook", "description": "Connect/configure Facebook Business integration"},
        {"id": "instagram.read", "name": "Read Instagram", "description": "View Instagram business accounts"},
        {"id": "instagram.write", "name": "Write Instagram", "description": "Connect/configure Instagram Business integration"},
        # WhatsApp
        {"id": "whatsapp.read", "name": "Read WhatsApp", "description": "View WhatsApp numbers, templates, and conversations"},
        {"id": "whatsapp.write", "name": "Write WhatsApp", "description": "Send WhatsApp messages and manage templates"},
        {"id": "whatsapp.admin", "name": "Administer WhatsApp", "description": "Register phone numbers, manage webhooks"},
        # AI Voice
        {"id": "voice.read", "name": "Read Voice", "description": "View voice library, providers, and call logs"},
        {"id": "voice.write", "name": "Write Voice", "description": "Manage voice library and campaign voice assignments"},
        {"id": "voice.admin", "name": "Administer Voice", "description": "Connect/configure AI voice providers"},
        {"id": "voice.call", "name": "Place AI Voice Calls", "description": "Initiate outbound AI voice calls"},
        {"id": "voice.train", "name": "Train Voice Agents", "description": "Manage voice agent scripts/training data"},
        # Automation Engine
        {"id": "automation.read", "name": "Read Automation", "description": "View workflows and execution history"},
        {"id": "automation.write", "name": "Write Automation", "description": "Create/edit/run workflows"},
        {"id": "automation.admin", "name": "Administer Automation", "description": "Manage workflow templates and engine-wide settings"},
        # CRM (leads/deals)
        {"id": "crm.read", "name": "Read CRM", "description": "Read leads, deals, and pipeline data"},
        {"id": "crm.write", "name": "Write CRM", "description": "Create/edit leads and deals"},
        {"id": "crm.delete", "name": "Delete CRM", "description": "Delete leads and deals"},
        {"id": "crm.export", "name": "Export CRM", "description": "Export leads/deals to CSV/Excel/PDF"},
        # Campaigns
        {"id": "campaign.read", "name": "Read Campaigns", "description": "View campaigns and their analytics"},
        {"id": "campaign.write", "name": "Write Campaigns", "description": "Create/edit/schedule campaigns"},
        {"id": "campaign.execute", "name": "Execute Campaigns", "description": "Start/pause/resume/stop/retry campaigns"},
        # Reports
        {"id": "reports.read", "name": "Read Reports", "description": "View dashboards and reports"},
        {"id": "reports.export", "name": "Export Reports", "description": "Export reports to CSV/Excel/PDF"},
        # Billing
        {"id": "billing.read", "name": "Read Billing", "description": "View invoices and subscription plan"},
        {"id": "billing.admin", "name": "Administer Billing", "description": "Manage subscription plans and payment methods"},
        # Knowledge base
        {"id": "knowledge.read", "name": "Read Knowledge Base", "description": "Search/view knowledge base documents"},
        {"id": "knowledge.manage", "name": "Manage Knowledge Base", "description": "Upload/edit/delete knowledge base documents"},
        # AI Agents
        {"id": "agents.read", "name": "Read Agents", "description": "Read LangGraph agent statuses and nodes"},
        {"id": "agents.write", "name": "Write Agents", "description": "Configure agent flows and tools"},
        # System
        {"id": "system.health", "name": "View System Health", "description": "View system/database health status"},
    ]

    for p in permissions_data:
        perm = await session.get(Permission, p["id"])
        if not perm:
            session.add(Permission(**p))
    await session.commit()

    # 2. Seed Roles
    roles_data = [
        {"id": "super_admin", "name": "Super Admin", "description": "Global administrator control", "permissions": ["admin.all"]},
        {"id": "org_admin", "name": "Organization Admin", "description": "Tenant administrator control — scoped to their own organization only", "permissions": [
            "users.read", "users.write", "users.delete", "users.suspend", "users.invite",
            "users.reset_password", "users.assign_role", "roles.read", "audit.read",
            "integrations.read", "integrations.write",
            "facebook.read", "facebook.write", "instagram.read", "instagram.write",
            "whatsapp.read", "whatsapp.write", "whatsapp.admin",
            "voice.read", "voice.write", "voice.admin", "voice.call", "voice.train",
            "automation.read", "automation.write", "automation.admin",
            "crm.read", "crm.write", "crm.delete", "crm.export",
            "campaign.read", "campaign.write", "campaign.execute",
            "reports.read", "reports.export", "billing.read",
            "knowledge.read", "knowledge.manage", "agents.read", "agents.write",
        ]},
        {"id": "manager", "name": "Manager", "description": "Team lead manager", "permissions": [
            "crm.read", "crm.write", "agents.read", "integrations.read", "voice.read",
            "campaign.read", "reports.read",
        ]},
        {"id": "sales_executive", "name": "Sales Executive", "description": "CRM executive worker", "permissions": ["crm.read", "crm.write", "campaign.read"]},
        {"id": "ai_agent", "name": "AI Agent", "description": "Autonomous worker agent", "permissions": ["crm.read", "crm.write", "agents.read", "automation.write"]},
        {"id": "developer", "name": "Developer", "description": "Developer node configurer", "permissions": ["agents.read", "agents.write", "automation.read", "automation.write", "automation.admin"]},
        {"id": "auditor", "name": "Auditor", "description": "Security logs auditor", "permissions": ["crm.read", "agents.read", "integrations.read", "audit.read", "reports.read"]},
        {"id": "viewer", "name": "Viewer", "description": "Read-only access", "permissions": ["crm.read"]}
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
        else:
            # Existing deployments: union in any permissions newly added to this role's seed
            # list above without ever removing permissions an admin may have added manually —
            # otherwise permissions added here would never reach an already-seeded database.
            existing_ids = {p.id for p in role.permissions}
            for p_id in r["permissions"]:
                if p_id not in existing_ids:
                    perm = await session.get(Permission, p_id)
                    if perm:
                        role.permissions.append(perm)
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
    # Local-dev convenience account: only ever created when running in development,
    # never with a hardcoded password in a production database.
    if settings.ENVIRONMENT not in ("production", "prod"):
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
    elif settings.ADMIN_EMAIL and settings.ADMIN_PASSWORD:
        # Production bootstrap: first admin is created from operator-supplied env vars,
        # once, and never re-seeded with a fixed password on subsequent restarts.
        q_user = await session.execute(select(User).where(User.email == settings.ADMIN_EMAIL))
        admin_user = q_user.scalar_one_or_none()

        if not admin_user:
            admin_user = User(
                id=str(uuid.uuid4()),
                organization_id=demo_org.id,
                first_name="Admin",
                last_name="User",
                email=settings.ADMIN_EMAIL,
                password_hash=get_password_hash(settings.ADMIN_PASSWORD),
                role_id="super_admin",
                status="active"
            )
            session.add(admin_user)
            await session.commit()
            logger.info(f"Production admin account bootstrapped for {settings.ADMIN_EMAIL}.")
    else:
        logger.warning(
            "Running in production with no existing admin and no ADMIN_EMAIL/ADMIN_PASSWORD "
            "set — skipping admin account seeding. Set both env vars to bootstrap the first "
            "administrator, or create one manually."
        )


from contextlib import asynccontextmanager

@asynccontextmanager
async def mongo_transaction():
    """Context manager to execute multi-document operations in MongoDB transactions."""
    async with await mongo_client.start_session() as session:
        async with session.start_transaction():
            try:
                yield session
                await session.commit_transaction()
            except Exception:
                await session.abort_transaction()
                raise


async def init_mongo_indexes():
    """Verifies and creates necessary production indexes for MongoDB collections."""
    try:
        db = mongo_client.get_default_database()
        # Index audit logs on timestamp for retrieval performance
        await db.audit_logs.create_index("timestamp")
        # Index chat/message histories for conversation sync
        await db.chat_history.create_index([("session_id", 1), ("created_at", 1)])
        logger.info("MongoDB indexes verified successfully.")
    except Exception as e:
        logger.error(f"Failed to verify/create MongoDB indexes: {e}")
