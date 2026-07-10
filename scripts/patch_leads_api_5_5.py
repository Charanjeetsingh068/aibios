import re

api_file = "backend/app/api/v1/endpoints/leads.py"

with open(api_file, "r", encoding="utf-8") as f:
    content = f.read()

# 1. Update _serialize
serialize_new = """    return {
        "id": lead.id,
        "organization_id": lead.organization_id,
        "name": lead.name,
        "company": lead.company,
        "phone": lead.phone,
        "email": lead.email,
        "source": lead.source,
        "status": lead.status,
        "value": float(lead.value or 0),
        "campaign_id": lead.campaign_id,
        "assigned_to": lead.assigned_to,
        "meta_lead_id": lead.meta_lead_id,
        "crm_lead_id": lead.crm_lead_id,
        "whatsapp_number": lead.whatsapp_number,
        "facebook_page_id": lead.facebook_page_id,
        "instagram_account_id": lead.instagram_account_id,
        "ad_set": lead.ad_set,
        "ad": lead.ad,
        "lead_form": lead.lead_form,
        "country": lead.country,
        "state": lead.state,
        "city": lead.city,
        "address": lead.address,
        "priority": lead.priority,
        "score": lead.score,
        "created_at": lead.created_at.isoformat() if lead.created_at else None,
        "updated_at": lead.updated_at.isoformat() if lead.updated_at else None,
    }"""
content = re.sub(r'    return \{\n        "id": lead\.id,.*?        "updated_at": lead\.updated_at\.isoformat\(\) if lead\.updated_at else None,\n    \}', serialize_new, content, flags=re.DOTALL)

# 2. Update create_lead args
create_lead_new = """    lead = Lead(
        organization_id=current_user.organization_id,
        name=body.name.strip(),
        company=body.company,
        phone=body.phone,
        email=body.email,
        source=body.source,
        value=body.value,
        campaign_id=body.campaign_id,
        meta_lead_id=body.meta_lead_id,
        crm_lead_id=body.crm_lead_id,
        whatsapp_number=body.whatsapp_number,
        facebook_page_id=body.facebook_page_id,
        instagram_account_id=body.instagram_account_id,
        ad_set=body.ad_set,
        ad=body.ad,
        lead_form=body.lead_form,
        country=body.country,
        state=body.state,
        city=body.city,
        address=body.address,
        priority=body.priority,
        status="new",
        created_by=current_user.id,
        updated_by=current_user.id,
    )"""
content = re.sub(r'    lead = Lead\(\n        organization_id=current_user\.organization_id,.*?\n        updated_by=current_user\.id,\n    \)', create_lead_new, content, flags=re.DOTALL)

# 3. Add Import / Export Endpoints
import_export_endpoints = """
from fastapi import UploadFile, File
import csv
import io

@router.post("/import", response_model=Dict[str, Any])
async def import_leads(
    file: UploadFile = File(...),
    current_user: User = Depends(require_crm_write),
    db: AsyncSession = Depends(get_db),
):
    if not file.filename.endswith(".csv"):
        raise HTTPException(status_code=400, detail="Invalid file format. Only CSV is allowed.")
        
    contents = await file.read()
    decoded = contents.decode("utf-8")
    reader = csv.DictReader(io.StringIO(decoded))
    
    imported = 0
    errors = []
    
    for row in reader:
        try:
            lead = Lead(
                organization_id=current_user.organization_id,
                name=row.get("name", "Unknown"),
                email=row.get("email"),
                phone=row.get("phone"),
                source="manual",
                status="new",
                created_by=current_user.id,
                updated_by=current_user.id
            )
            db.add(lead)
            imported += 1
        except Exception as e:
            errors.append(str(e))
            
    await db.commit()
    return {"imported": imported, "errors": errors}

@router.get("/export", response_model=Dict[str, Any])
async def export_leads(
    current_user: User = Depends(require_crm_read),
    db: AsyncSession = Depends(get_db),
):
    query = select(Lead).where(Lead.organization_id == current_user.organization_id)
    result = await db.execute(query)
    leads = result.scalars().all()
    
    return {"leads": [_serialize(l) for l in leads]}
"""

if "@router.post(\"/import\"" not in content:
    content += "\n" + import_export_endpoints

# 4. Integrate Deduplication and Assignment in Create
dedupe_import = """
from app.services.lead_deduplication_service import LeadDeduplicationService
from app.services.lead_assignment_service import LeadAssignmentService
"""
if "LeadDeduplicationService" not in content:
    content = content.replace("from app.services.event_bus import dispatch_event", "from app.services.event_bus import dispatch_event" + "\n" + dedupe_import)

# Hook into create_lead
create_hook = """    await db.commit()
    await db.refresh(lead)

    # Trigger Duplicate Detection
    await LeadDeduplicationService.detect_duplicates(db, lead)
    
    # Optional Round Robin or Least Busy Assignment could happen here
    # await LeadAssignmentService.assign_least_busy(db, lead)"""
    
content = content.replace("    await db.commit()\n    await db.refresh(lead)", create_hook)

with open(api_file, "w", encoding="utf-8") as f:
    f.write(content)

print("Patched leads.py endpoints.")
