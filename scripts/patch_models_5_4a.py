import os
import re

auth_file = "backend/app/models/auth.py"
business_file = "backend/app/models/business.py"

# --- Patch auth.py ---
with open(auth_file, "r", encoding="utf-8") as f:
    auth_content = f.read()

team_models = """

class Team(Base):
    __tablename__ = "teams"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=generate_uuid)
    organization_id: Mapped[str] = mapped_column(String(36), ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    manager_id: Mapped[Optional[str]] = mapped_column(String(36), ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    deleted_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)

class TeamMember(Base):
    __tablename__ = "team_members"

    team_id: Mapped[str] = mapped_column(String(36), ForeignKey("teams.id", ondelete="CASCADE"), primary_key=True)
    user_id: Mapped[str] = mapped_column(String(36), ForeignKey("users.id", ondelete="CASCADE"), primary_key=True)
    role: Mapped[str] = mapped_column(String(50), default="member") # manager, member
    joined_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

class VisibilityRule(Base):
    __tablename__ = "visibility_rules"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=generate_uuid)
    organization_id: Mapped[str] = mapped_column(String(36), ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False, index=True)
    resource_type: Mapped[str] = mapped_column(String(50), nullable=False) # e.g. "leads"
    resource_id: Mapped[Optional[str]] = mapped_column(String(36), nullable=True)
    rule_type: Mapped[str] = mapped_column(String(50), nullable=False) # e.g. "team", "organization", "global"
    target_id: Mapped[Optional[str]] = mapped_column(String(36), nullable=True) # team_id or user_id
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
"""

if "class Team(" not in auth_content:
    auth_content += team_models
    with open(auth_file, "w", encoding="utf-8") as f:
        f.write(auth_content)
    print("Patched auth.py with Team models")


# --- Patch business.py ---
with open(business_file, "r", encoding="utf-8") as f:
    biz_content = f.read()

mixin_code = """
class TenantResourceMixin:
    \"\"\"Mixin to apply multi-tenant isolation, ownership, and visibility to any resource.\"\"\"
    owner_id: Mapped[Optional[str]] = mapped_column(String(36), ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    owner_team_id: Mapped[Optional[str]] = mapped_column(String(36), ForeignKey("teams.id", ondelete="SET NULL"), nullable=True)
    visibility: Mapped[str] = mapped_column(String(20), default="private")  # private, team, department, organization, global
"""

# Insert mixin right after Base, generate_uuid import
if "TenantResourceMixin" not in biz_content:
    biz_content = biz_content.replace(
        'from app.models.auth import Base, generate_uuid\n',
        'from app.models.auth import Base, generate_uuid\n\n' + mixin_code
    )

    # Make every model inherit from TenantResourceMixin in addition to Base
    # Example: class Lead(Base): -> class Lead(Base, TenantResourceMixin):
    
    # We want to replace `class X(Base):` with `class X(Base, TenantResourceMixin):`
    # for main business entities.
    classes_to_mixin = [
        "Lead", "Deal", "Campaign", "CallLog", "Meeting", "TaskItem",
        "Workflow", "KbArticle", "DocumentFile"
    ]
    for cls in classes_to_mixin:
        biz_content = re.sub(rf"class {cls}\(Base\):", rf"class {cls}(Base, TenantResourceMixin):", biz_content)
        
    with open(business_file, "w", encoding="utf-8") as f:
        f.write(biz_content)
    print("Patched business.py with TenantResourceMixin")
else:
    print("business.py already patched")
