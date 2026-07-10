from datetime import datetime

from typing import Optional



from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, Numeric, String

from sqlalchemy.orm import Mapped, mapped_column



from app.models.auth import Base, generate_uuid





class TenantResourceMixin:

    """Mixin to apply multi-tenant isolation, ownership, and visibility to any resource."""

    owner_id: Mapped[Optional[str]] = mapped_column(String(36), ForeignKey("users.id", ondelete="SET NULL"), nullable=True)

    owner_team_id: Mapped[Optional[str]] = mapped_column(String(36), ForeignKey("teams.id", ondelete="SET NULL"), nullable=True)

    visibility: Mapped[str] = mapped_column(String(20), default="private")  # private, team, department, organization, global





class Lead(Base, TenantResourceMixin):

    __tablename__ = "leads"



    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=generate_uuid)

    organization_id: Mapped[str] = mapped_column(String(36), ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False, index=True)

    name: Mapped[str] = mapped_column(String(150), nullable=False)

    company: Mapped[Optional[str]] = mapped_column(String(150), nullable=True)

    phone: Mapped[Optional[str]] = mapped_column(String(30), nullable=True)

    email: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)

    source: Mapped[str] = mapped_column(String(30), default="website")  # facebook, instagram, whatsapp, ai_voice, website

    status: Mapped[str] = mapped_column(String(20), default="new")  # new, qualified, pending, spam, assigned, closed

    value: Mapped[float] = mapped_column(Numeric(12, 2), default=0)

    campaign_id: Mapped[Optional[str]] = mapped_column(String(36), ForeignKey("campaigns.id", ondelete="SET NULL"), nullable=True)

    assigned_to: Mapped[Optional[str]] = mapped_column(String(36), ForeignKey("users.id", ondelete="SET NULL"), nullable=True)

    created_by: Mapped[Optional[str]] = mapped_column(String(36), ForeignKey("users.id", ondelete="SET NULL"), nullable=True)

    updated_by: Mapped[Optional[str]] = mapped_column(String(36), ForeignKey("users.id", ondelete="SET NULL"), nullable=True)

    deleted_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)

    archived_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)

    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)







    # Meta & Source Fields

    meta_lead_id: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)

    crm_lead_id: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)

    whatsapp_number: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)

    facebook_page_id: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)

    instagram_account_id: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)

    ad_set: Mapped[Optional[str]] = mapped_column(String(150), nullable=True)

    ad: Mapped[Optional[str]] = mapped_column(String(150), nullable=True)

    lead_form: Mapped[Optional[str]] = mapped_column(String(150), nullable=True)

    

    # Address & Profiling

    country: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)

    state: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)

    city: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)

    address: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)

    priority: Mapped[str] = mapped_column(String(20), default="medium") # low, medium, high

    score: Mapped[int] = mapped_column(Integer, default=0)





class Deal(Base, TenantResourceMixin):

    __tablename__ = "deals"



    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=generate_uuid)

    organization_id: Mapped[str] = mapped_column(String(36), ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False, index=True)

    lead_id: Mapped[Optional[str]] = mapped_column(String(36), ForeignKey("leads.id", ondelete="SET NULL"), nullable=True)

    name: Mapped[str] = mapped_column(String(150), nullable=False)

    company: Mapped[Optional[str]] = mapped_column(String(150), nullable=True)

    stage: Mapped[str] = mapped_column(String(20), default="lead")  # lead, qualified, meeting, proposal, negotiation, won, lost

    value: Mapped[float] = mapped_column(Numeric(12, 2), default=0)

    assigned_to: Mapped[Optional[str]] = mapped_column(String(36), ForeignKey("users.id", ondelete="SET NULL"), nullable=True)

    created_by: Mapped[Optional[str]] = mapped_column(String(36), ForeignKey("users.id", ondelete="SET NULL"), nullable=True)

    updated_by: Mapped[Optional[str]] = mapped_column(String(36), ForeignKey("users.id", ondelete="SET NULL"), nullable=True)

    deleted_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)

    archived_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)

    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)





class Campaign(Base, TenantResourceMixin):

    __tablename__ = "campaigns"



    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=generate_uuid)

    organization_id: Mapped[str] = mapped_column(String(36), ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False, index=True)

    name: Mapped[str] = mapped_column(String(150), nullable=False)

    channel: Mapped[str] = mapped_column(String(30), default="general")

    status: Mapped[str] = mapped_column(String(20), default="paused")  # running, paused

    progress: Mapped[int] = mapped_column(Integer, default=0)

    created_by: Mapped[Optional[str]] = mapped_column(String(36), ForeignKey("users.id", ondelete="SET NULL"), nullable=True)

    updated_by: Mapped[Optional[str]] = mapped_column(String(36), ForeignKey("users.id", ondelete="SET NULL"), nullable=True)

    deleted_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)

    archived_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)

    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)





class CallLog(Base, TenantResourceMixin):

    __tablename__ = "call_logs"



    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=generate_uuid)

    organization_id: Mapped[str] = mapped_column(String(36), ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False, index=True)

    direction: Mapped[str] = mapped_column(String(20), default="outbound")

    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)





class Meeting(Base, TenantResourceMixin):

    __tablename__ = "meetings"



    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=generate_uuid)

    organization_id: Mapped[str] = mapped_column(String(36), ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False, index=True)

    title: Mapped[str] = mapped_column(String(200), nullable=False)

    lead_id: Mapped[Optional[str]] = mapped_column(String(36), ForeignKey("leads.id", ondelete="CASCADE"), nullable=True)

    scheduled_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)

    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)





class TaskItem(Base, TenantResourceMixin):

    __tablename__ = "task_items"



    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=generate_uuid)

    organization_id: Mapped[str] = mapped_column(String(36), ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False, index=True)

    text: Mapped[str] = mapped_column(String(500), nullable=False)

    lead_id: Mapped[Optional[str]] = mapped_column(String(36), ForeignKey("leads.id", ondelete="CASCADE"), nullable=True)

    assigned_to: Mapped[Optional[str]] = mapped_column(String(36), ForeignKey("users.id", ondelete="SET NULL"), nullable=True)

    completed: Mapped[bool] = mapped_column(Boolean, default=False)

    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)





class EmailQueueItem(Base):

    __tablename__ = "email_queue_items"



    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=generate_uuid)

    organization_id: Mapped[str] = mapped_column(String(36), ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False, index=True)

    status: Mapped[str] = mapped_column(String(20), default="pending")  # pending, sent, failed

    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)





class TokenUsageEvent(Base):

    __tablename__ = "token_usage_events"



    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=generate_uuid)

    organization_id: Mapped[str] = mapped_column(String(36), ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False, index=True)

    input_tokens: Mapped[int] = mapped_column(Integer, default=0)

    output_tokens: Mapped[int] = mapped_column(Integer, default=0)

    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)





class Workflow(Base, TenantResourceMixin):

    __tablename__ = "workflows"



    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=generate_uuid)

    organization_id: Mapped[str] = mapped_column(String(36), ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False, index=True)

    name: Mapped[str] = mapped_column(String(150), nullable=False)

    trigger: Mapped[str] = mapped_column(String(150), nullable=False)

    status: Mapped[str] = mapped_column(String(20), default="active")  # active, paused

    runs: Mapped[int] = mapped_column(Integer, default=0)

    created_by: Mapped[Optional[str]] = mapped_column(String(36), ForeignKey("users.id", ondelete="SET NULL"), nullable=True)

    updated_by: Mapped[Optional[str]] = mapped_column(String(36), ForeignKey("users.id", ondelete="SET NULL"), nullable=True)

    deleted_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)

    archived_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)

    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)





class AutomationEvent(Base):

    """Append-only log of trigger-worthy events (lead.created, whatsapp.message.received,

    etc.) published by the rest of the app. This is the hook point the native automation

    engine's trigger dispatcher (Phase 3) will subscribe against — recorded now so no event

    is silently dropped in the meantime, without yet pretending workflows execute from it."""

    __tablename__ = "automation_events"



    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=generate_uuid)

    organization_id: Mapped[str] = mapped_column(String(36), ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False, index=True)

    event_name: Mapped[str] = mapped_column(String(60), nullable=False, index=True)  # e.g. lead.created, whatsapp.message.received

    payload_json: Mapped[Optional[str]] = mapped_column(String(2000), nullable=True)

    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)





class KbArticle(Base, TenantResourceMixin):

    __tablename__ = "kb_articles"



    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=generate_uuid)

    organization_id: Mapped[str] = mapped_column(String(36), ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False, index=True)

    title: Mapped[str] = mapped_column(String(200), nullable=False)

    lead_id: Mapped[Optional[str]] = mapped_column(String(36), ForeignKey("leads.id", ondelete="CASCADE"), nullable=True)

    category: Mapped[str] = mapped_column(String(100), nullable=False)

    views: Mapped[int] = mapped_column(Integer, default=0)

    created_by: Mapped[Optional[str]] = mapped_column(String(36), ForeignKey("users.id", ondelete="SET NULL"), nullable=True)

    updated_by: Mapped[Optional[str]] = mapped_column(String(36), ForeignKey("users.id", ondelete="SET NULL"), nullable=True)

    deleted_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)

    archived_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)

    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)





class DocumentFile(Base, TenantResourceMixin):

    __tablename__ = "document_files"



    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=generate_uuid)

    organization_id: Mapped[str] = mapped_column(String(36), ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False, index=True)

    name: Mapped[str] = mapped_column(String(200), nullable=False)

    file_type: Mapped[str] = mapped_column(String(30), nullable=False)

    size_bytes: Mapped[int] = mapped_column(Integer, default=0)

    created_by: Mapped[Optional[str]] = mapped_column(String(36), ForeignKey("users.id", ondelete="SET NULL"), nullable=True)

    updated_by: Mapped[Optional[str]] = mapped_column(String(36), ForeignKey("users.id", ondelete="SET NULL"), nullable=True)

    deleted_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)

    archived_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)

    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)





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





class LeadCustomField(Base):

    __tablename__ = "lead_custom_fields"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=generate_uuid)

    lead_id: Mapped[str] = mapped_column(String(36), ForeignKey("leads.id", ondelete="CASCADE"), nullable=False, index=True)

    field_name: Mapped[str] = mapped_column(String(100), nullable=False)

    field_value: Mapped[str] = mapped_column(String(1000), nullable=False)

    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)



class LeadDuplicateMapping(Base):

    __tablename__ = "lead_duplicate_mappings"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=generate_uuid)

    primary_lead_id: Mapped[str] = mapped_column(String(36), ForeignKey("leads.id", ondelete="CASCADE"), nullable=False, index=True)

    secondary_lead_id: Mapped[str] = mapped_column(String(36), ForeignKey("leads.id", ondelete="CASCADE"), nullable=False, index=True)

    confidence_score: Mapped[int] = mapped_column(Integer, default=100)

    match_reason: Mapped[Optional[str]] = mapped_column(String(200), nullable=True)

    status: Mapped[str] = mapped_column(String(20), default="pending") # pending, merged, ignored

    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)



class LeadMergeHistory(Base):

    __tablename__ = "lead_merge_history"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=generate_uuid)

    primary_lead_id: Mapped[str] = mapped_column(String(36), ForeignKey("leads.id", ondelete="CASCADE"), nullable=False)

    merged_lead_id: Mapped[str] = mapped_column(String(36), nullable=False) # Not a foreign key because it was deleted/merged

    merged_by: Mapped[Optional[str]] = mapped_column(String(36), ForeignKey("users.id", ondelete="SET NULL"), nullable=True)

    merged_data_json: Mapped[Optional[str]] = mapped_column(String(4000), nullable=True)

    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

