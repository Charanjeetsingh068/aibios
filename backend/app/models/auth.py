import uuid
from datetime import datetime
from typing import List, Optional

from sqlalchemy import Boolean, Column, DateTime, ForeignKey, Integer, String, Table
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


# Custom UUID generator helper that works across SQLite and Postgres
def generate_uuid():
    return str(uuid.uuid4())

class Base(DeclarativeBase):
    pass

# Many-to-Many Association Table for Roles and Permissions
role_permissions = Table(
    "role_permissions",
    Base.metadata,
    Column("role_id", String(50), ForeignKey("roles.id", ondelete="CASCADE"), primary_key=True),
    Column("permission_id", String(100), ForeignKey("permissions.id", ondelete="CASCADE"), primary_key=True)
)

# Many-to-Many Association Table for Users and additional (non-primary) Roles.
# User.role_id remains the primary role (used for JWT claims and quick display); this
# table lets Super Admin assign/remove extra roles per spec section 1 without disturbing
# the primary-role column every other query already relies on.
user_roles = Table(
    "user_roles",
    Base.metadata,
    Column("user_id", String(36), ForeignKey("users.id", ondelete="CASCADE"), primary_key=True),
    Column("role_id", String(50), ForeignKey("roles.id", ondelete="CASCADE"), primary_key=True),
    Column("assigned_at", DateTime, default=datetime.utcnow),
    Column("assigned_by", String(36), ForeignKey("users.id", ondelete="SET NULL"), nullable=True),
)

class Organization(Base):
    __tablename__ = "organizations"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=generate_uuid)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    slug: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
    status: Mapped[str] = mapped_column(String(20), default="active")
    logo_char: Mapped[Optional[str]] = mapped_column(String(10), default="Ω", nullable=True)
    gst_number: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    address: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    timezone: Mapped[Optional[str]] = mapped_column(String(100), default="Asia/Kolkata", nullable=True)
    brand_color: Mapped[Optional[str]] = mapped_column(String(10), default="#3b82f6", nullable=True)
    subscription_plan: Mapped[Optional[str]] = mapped_column(String(30), default="enterprise", nullable=True)
    smtp_host: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    smtp_port: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    smtp_user: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    smtp_pass: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    created_by: Mapped[Optional[str]] = mapped_column(String(36), ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    updated_by: Mapped[Optional[str]] = mapped_column(String(36), ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    deleted_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    users: Mapped[List["User"]] = relationship("User", back_populates="organization", cascade="all, delete-orphan", foreign_keys="User.organization_id")
    sessions: Mapped[List["Session"]] = relationship("Session", back_populates="organization", cascade="all, delete-orphan")

class Permission(Base):
    __tablename__ = "permissions"

    id: Mapped[str] = mapped_column(String(100), primary_key=True)  # e.g., "leads:read"
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    description: Mapped[str] = mapped_column(String(255), nullable=True)

class Role(Base):
    __tablename__ = "roles"

    id: Mapped[str] = mapped_column(String(50), primary_key=True)  # e.g., "super_admin", "org_admin"
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    description: Mapped[str] = mapped_column(String(255), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    permissions: Mapped[List[Permission]] = relationship(
        "Permission",
        secondary=role_permissions,
        lazy="selectin"
    )
    users: Mapped[List["User"]] = relationship("User", back_populates="role")

class User(Base):
    __tablename__ = "users"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=generate_uuid)
    organization_id: Mapped[str] = mapped_column(String(36), ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False, index=True)
    first_name: Mapped[str] = mapped_column(String(50), nullable=False)
    last_name: Mapped[str] = mapped_column(String(50), nullable=False)
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True, nullable=False)
    phone: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    profile_image: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    status: Mapped[str] = mapped_column(String(20), default="active")  # active, inactive, suspended, deleted
    role_id: Mapped[str] = mapped_column(String(50), ForeignKey("roles.id"), nullable=False)
    timezone: Mapped[str] = mapped_column(String(50), default="UTC")
    language: Mapped[str] = mapped_column(String(10), default="en")
    department: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    designation: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    email_verified: Mapped[bool] = mapped_column(Boolean, default=False)
    mfa_enabled: Mapped[bool] = mapped_column(Boolean, default=False)
    # Team lead for the Manager role's "assigned team only" scope (users.read_team /
    # users.write_team) — self-referential, not the org hierarchy itself.
    manager_id: Mapped[Optional[str]] = mapped_column(String(36), ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    created_by: Mapped[Optional[str]] = mapped_column(String(36), ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    updated_by: Mapped[Optional[str]] = mapped_column(String(36), ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    deleted_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    last_login: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    last_activity: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)

    # Relationships
    organization: Mapped[Organization] = relationship("Organization", back_populates="users", foreign_keys=[organization_id])
    role: Mapped[Role] = relationship("Role", back_populates="users", foreign_keys=[role_id])
    additional_roles: Mapped[List[Role]] = relationship(
        "Role",
        secondary=user_roles,
        primaryjoin="User.id==user_roles.c.user_id",
        secondaryjoin="Role.id==user_roles.c.role_id",
        lazy="selectin",
    )
    manager: Mapped[Optional["User"]] = relationship("User", remote_side=[id], foreign_keys=[manager_id])
    sessions: Mapped[List["Session"]] = relationship("Session", back_populates="user", cascade="all, delete-orphan", foreign_keys="Session.user_id")

    def all_permission_ids(self) -> set:
        """Union of permission ids from the primary role plus any additional assigned roles."""
        perm_ids = {p.id for p in (self.role.permissions if self.role else [])}
        for r in self.additional_roles:
            perm_ids.update(p.id for p in r.permissions)
        return perm_ids

    def all_role_ids(self) -> List[str]:
        ids = [self.role_id] if self.role_id else []
        ids.extend(r.id for r in self.additional_roles if r.id not in ids)
        return ids

    @property
    def permissions(self) -> List[str]:
        """Exposed so UserResponse (from_attributes) can serialize the effective permission
        set straight from the ORM object — this is what the frontend's AuthContext/RouteGuard
        gate on, so /auth/me must return it."""
        return sorted(self.all_permission_ids())

    @property
    def roles(self) -> List[str]:
        return self.all_role_ids()

class Session(Base):
    __tablename__ = "sessions"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=generate_uuid)
    user_id: Mapped[str] = mapped_column(String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    organization_id: Mapped[str] = mapped_column(String(36), ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False)
    access_token_id: Mapped[str] = mapped_column(String(255), unique=True, index=True, nullable=False)
    device_info: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    ip_address: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    expires_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    user: Mapped[User] = relationship("User", back_populates="sessions")
    organization: Mapped[Organization] = relationship("Organization", back_populates="sessions")
    refresh_tokens: Mapped[List["RefreshToken"]] = relationship("RefreshToken", back_populates="session", cascade="all, delete-orphan")

class RefreshToken(Base):
    __tablename__ = "refresh_tokens"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=generate_uuid)
    session_id: Mapped[str] = mapped_column(String(36), ForeignKey("sessions.id", ondelete="CASCADE"), nullable=False)
    token_hash: Mapped[str] = mapped_column(String(255), unique=True, index=True, nullable=False)
    is_revoked: Mapped[bool] = mapped_column(Boolean, default=False)
    expires_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    # Relationships
    session: Mapped[Session] = relationship("Session", back_populates="refresh_tokens")

class LoginHistory(Base):
    __tablename__ = "login_history"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=generate_uuid)
    user_id: Mapped[Optional[str]] = mapped_column(String(36), ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    organization_id: Mapped[Optional[str]] = mapped_column(String(36), ForeignKey("organizations.id", ondelete="SET NULL"), nullable=True)
    email: Mapped[str] = mapped_column(String(255), nullable=False)
    status: Mapped[str] = mapped_column(String(20), nullable=False)  # "success" or "failed"
    failure_reason: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    ip_address: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    device_info: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

class AuditLog(Base):
    __tablename__ = "audit_logs"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=generate_uuid)
    user_id: Mapped[Optional[str]] = mapped_column(String(36), ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    organization_id: Mapped[Optional[str]] = mapped_column(String(36), ForeignKey("organizations.id", ondelete="SET NULL"), nullable=True)
    action: Mapped[str] = mapped_column(String(100), nullable=False)
    description: Mapped[str] = mapped_column(String(255), nullable=False)
    resource: Mapped[str] = mapped_column(String(50), nullable=False)
    resource_id: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    ip_address: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

class PasswordResetToken(Base):
    __tablename__ = "password_reset_tokens"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=generate_uuid)
    user_id: Mapped[str] = mapped_column(String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    token_hash: Mapped[str] = mapped_column(String(255), unique=True, index=True, nullable=False)
    is_used: Mapped[bool] = mapped_column(Boolean, default=False)
    expires_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    # Relationships
    user: Mapped[User] = relationship("User")


class EmailVerificationToken(Base):
    __tablename__ = "email_verification_tokens"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=generate_uuid)
    user_id: Mapped[str] = mapped_column(String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    token_hash: Mapped[str] = mapped_column(String(255), unique=True, index=True, nullable=False)
    is_used: Mapped[bool] = mapped_column(Boolean, default=False)
    expires_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    # Relationships
    user: Mapped[User] = relationship("User")
