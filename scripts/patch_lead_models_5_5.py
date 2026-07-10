import os
import re

business_file = "backend/app/models/business.py"

with open(business_file, "r", encoding="utf-8") as f:
    content = f.read()

# 1. Add fields to Lead
lead_additions = """    # Meta & Source Fields
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
"""

if "meta_lead_id: Mapped" not in content:
    # Find insertion point: after updated_at in Lead
    pattern = r"(class Lead.*?updated_at: Mapped.*?)(class Deal)"
    replacement = r"\1\n" + lead_additions + "\n\n\2"
    content = re.sub(pattern, replacement, content, flags=re.DOTALL)


# 2. Add new tables at the end
new_tables = """
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
"""

if "class LeadCustomField" not in content:
    content += "\n" + new_tables

with open(business_file, "w", encoding="utf-8") as f:
    f.write(content)

print("Patched business.py with Phase 5.5 Lead fields and tables.")
