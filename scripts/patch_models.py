import os

file_path = "backend/app/models/business.py"

with open(file_path, "r", encoding="utf-8") as f:
    content = f.read()

# Add archived_at to Lead
lead_archived = '    deleted_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)\n    archived_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)'
content = content.replace('    deleted_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)', lead_archived)

# Add lead_id to TaskItem
task_additions = '    text: Mapped[str] = mapped_column(String(500), nullable=False)\n    lead_id: Mapped[Optional[str]] = mapped_column(String(36), ForeignKey("leads.id", ondelete="CASCADE"), nullable=True)\n    assigned_to: Mapped[Optional[str]] = mapped_column(String(36), ForeignKey("users.id", ondelete="SET NULL"), nullable=True)'
content = content.replace('    text: Mapped[str] = mapped_column(String(500), nullable=False)', task_additions)

# Add lead_id to Meeting
meeting_additions = '    title: Mapped[str] = mapped_column(String(200), nullable=False)\n    lead_id: Mapped[Optional[str]] = mapped_column(String(36), ForeignKey("leads.id", ondelete="CASCADE"), nullable=True)'
content = content.replace('    title: Mapped[str] = mapped_column(String(200), nullable=False)', meeting_additions)

# Append new models
new_models = """

class LeadHistory(Base):
    __tablename__ = "lead_history"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=generate_uuid)
    lead_id: Mapped[str] = mapped_column(String(36), ForeignKey("leads.id", ondelete="CASCADE"), nullable=False, index=True)
    actor_id: Mapped[Optional[str]] = mapped_column(String(36), ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    action: Mapped[str] = mapped_column(String(100), nullable=False)
    field: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    old_value: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    new_value: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

class LeadNote(Base):
    __tablename__ = "lead_notes"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=generate_uuid)
    lead_id: Mapped[str] = mapped_column(String(36), ForeignKey("leads.id", ondelete="CASCADE"), nullable=False, index=True)
    author_id: Mapped[Optional[str]] = mapped_column(String(36), ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    content: Mapped[str] = mapped_column(String(2000), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class Tag(Base):
    __tablename__ = "tags"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=generate_uuid)
    organization_id: Mapped[str] = mapped_column(String(36), ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(50), nullable=False)
    color: Mapped[str] = mapped_column(String(20), default="#CCCCCC")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

class LeadTag(Base):
    __tablename__ = "lead_tags"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=generate_uuid)
    lead_id: Mapped[str] = mapped_column(String(36), ForeignKey("leads.id", ondelete="CASCADE"), nullable=False, index=True)
    tag_id: Mapped[str] = mapped_column(String(36), ForeignKey("tags.id", ondelete="CASCADE"), nullable=False, index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

class Pipeline(Base):
    __tablename__ = "pipelines"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=generate_uuid)
    organization_id: Mapped[str] = mapped_column(String(36), ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    is_default: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

class PipelineStage(Base):
    __tablename__ = "pipeline_stages"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=generate_uuid)
    pipeline_id: Mapped[str] = mapped_column(String(36), ForeignKey("pipelines.id", ondelete="CASCADE"), nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    order_index: Mapped[int] = mapped_column(Integer, default=0)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

class LeadAssignment(Base):
    __tablename__ = "lead_assignments"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=generate_uuid)
    lead_id: Mapped[str] = mapped_column(String(36), ForeignKey("leads.id", ondelete="CASCADE"), nullable=False, index=True)
    assigned_from: Mapped[Optional[str]] = mapped_column(String(36), ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    assigned_to: Mapped[Optional[str]] = mapped_column(String(36), ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    assigned_by: Mapped[Optional[str]] = mapped_column(String(36), ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

class LeadScore(Base):
    __tablename__ = "lead_scores"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=generate_uuid)
    lead_id: Mapped[str] = mapped_column(String(36), ForeignKey("leads.id", ondelete="CASCADE"), nullable=False, unique=True)
    score: Mapped[int] = mapped_column(Integer, default=0)
    breakdown_json: Mapped[Optional[str]] = mapped_column(String(1000), nullable=True)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class LeadActivity(Base):
    __tablename__ = "lead_activities"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=generate_uuid)
    lead_id: Mapped[str] = mapped_column(String(36), ForeignKey("leads.id", ondelete="CASCADE"), nullable=False, index=True)
    activity_type: Mapped[str] = mapped_column(String(50), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(String(1000), nullable=True)
    created_by: Mapped[Optional[str]] = mapped_column(String(36), ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
"""

content += new_models

with open(file_path, "w", encoding="utf-8") as f:
    f.write(content)

print("Models patched")
