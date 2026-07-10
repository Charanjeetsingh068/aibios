import re

schema_file = "backend/app/schemas/leads.py"

with open(schema_file, "r", encoding="utf-8") as f:
    content = f.read()

# Fields to add
extra_fields_create = """
    meta_lead_id: Optional[str] = None
    crm_lead_id: Optional[str] = None
    whatsapp_number: Optional[str] = None
    facebook_page_id: Optional[str] = None
    instagram_account_id: Optional[str] = None
    ad_set: Optional[str] = None
    ad: Optional[str] = None
    lead_form: Optional[str] = None
    country: Optional[str] = None
    state: Optional[str] = None
    city: Optional[str] = None
    address: Optional[str] = None
    priority: str = Field("medium", max_length=20)
"""

extra_fields_update = """
    meta_lead_id: Optional[str] = None
    crm_lead_id: Optional[str] = None
    whatsapp_number: Optional[str] = None
    facebook_page_id: Optional[str] = None
    instagram_account_id: Optional[str] = None
    ad_set: Optional[str] = None
    ad: Optional[str] = None
    lead_form: Optional[str] = None
    country: Optional[str] = None
    state: Optional[str] = None
    city: Optional[str] = None
    address: Optional[str] = None
    priority: Optional[str] = Field(None, max_length=20)
    score: Optional[int] = None
"""

extra_fields_response = """
    meta_lead_id: Optional[str] = None
    crm_lead_id: Optional[str] = None
    whatsapp_number: Optional[str] = None
    facebook_page_id: Optional[str] = None
    instagram_account_id: Optional[str] = None
    ad_set: Optional[str] = None
    ad: Optional[str] = None
    lead_form: Optional[str] = None
    country: Optional[str] = None
    state: Optional[str] = None
    city: Optional[str] = None
    address: Optional[str] = None
    priority: str
    score: int
"""

if "meta_lead_id" not in content:
    # Patch LeadCreate
    content = re.sub(r"(class LeadCreate\(BaseModel\):.*?campaign_id: Optional\[str\] = None)", r"\1" + extra_fields_create, content, flags=re.DOTALL)
    
    # Patch LeadUpdate
    content = re.sub(r"(class LeadUpdate\(BaseModel\):.*?assigned_to: Optional\[str\] = None)", r"\1" + extra_fields_update, content, flags=re.DOTALL)
    
    # Patch LeadResponse
    content = re.sub(r"(class LeadResponse\(BaseModel\):.*?updated_at: datetime)", r"\1" + extra_fields_response, content, flags=re.DOTALL)

with open(schema_file, "w", encoding="utf-8") as f:
    f.write(content)

print("Patched leads schemas")
