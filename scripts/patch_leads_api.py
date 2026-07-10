import os

file_path = "backend/app/api/v1/endpoints/leads.py"
with open(file_path, "r", encoding="utf-8") as f:
    content = f.read()

# Append new routes at the end
new_routes = """

# ---------------------------------------------------------
# NEW PHASE 5.4 ROUTES: Bulk Actions, Merge, Sub-resources
# ---------------------------------------------------------

from app.schemas.leads import LeadBulkUpdate, LeadMergeRequest, LeadNoteCreate, LeadNoteResponse, LeadTaskCreate, LeadMeetingCreate, TagCreate, TagResponse
from app.models.business import LeadNote, Tag, LeadTag, TaskItem, Meeting, LeadHistory

@router.post("/bulk/update", response_model=Dict[str, Any])
async def bulk_update_leads(
    body: LeadBulkUpdate,
    current_user: User = Depends(require_crm_write),
    db: AsyncSession = Depends(get_db),
):
    query = select(Lead).where(Lead.id.in_(body.lead_ids), Lead.organization_id == current_user.organization_id)
    result = await db.execute(query)
    leads = result.scalars().all()
    
    for lead in leads:
        if body.status is not None:
            lead.status = body.status
        if body.assigned_to is not None:
            lead.assigned_to = body.assigned_to
        if body.campaign_id is not None:
            lead.campaign_id = body.campaign_id
        lead.updated_by = current_user.id
        
    await db.commit()
    return {"updated": len(leads)}

@router.post("/bulk/delete", response_model=Dict[str, Any])
async def bulk_delete_leads(
    body: LeadBulkUpdate, # Reuse schema for lead_ids list
    current_user: User = Depends(require_crm_delete),
    db: AsyncSession = Depends(get_db),
):
    query = select(Lead).where(Lead.id.in_(body.lead_ids), Lead.organization_id == current_user.organization_id)
    result = await db.execute(query)
    leads = result.scalars().all()
    for lead in leads:
        await db.delete(lead)
    await db.commit()
    return {"deleted": len(leads)}

@router.post("/{lead_id}/merge", response_model=Dict[str, Any])
async def merge_leads(
    lead_id: str,
    body: LeadMergeRequest,
    current_user: User = Depends(require_crm_write),
    db: AsyncSession = Depends(get_db),
):
    target_lead = await db.get(Lead, lead_id)
    source_lead = await db.get(Lead, body.source_lead_id)
    
    if not target_lead or target_lead.organization_id != current_user.organization_id:
        raise HTTPException(status_code=404, detail="Target lead not found")
    if not source_lead or source_lead.organization_id != current_user.organization_id:
        raise HTTPException(status_code=404, detail="Source lead not found")

    target_lead.phone = target_lead.phone or source_lead.phone
    target_lead.email = target_lead.email or source_lead.email
    target_lead.company = target_lead.company or source_lead.company
    target_lead.value = max(float(target_lead.value or 0), float(source_lead.value or 0))

    await db.delete(source_lead)
    
    history = LeadHistory(
        lead_id=target_lead.id,
        actor_id=current_user.id,
        action="merge",
        old_value=body.source_lead_id,
        new_value=target_lead.id
    )
    db.add(history)
    
    await db.commit()
    return _serialize(target_lead)

@router.get("/{lead_id}/notes", response_model=List[LeadNoteResponse])
async def get_lead_notes(lead_id: str, current_user: User = Depends(require_crm_read), db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(LeadNote).where(LeadNote.lead_id == lead_id).order_by(LeadNote.created_at.desc()))
    return result.scalars().all()

@router.post("/{lead_id}/notes", response_model=LeadNoteResponse)
async def create_lead_note(lead_id: str, body: LeadNoteCreate, current_user: User = Depends(require_crm_write), db: AsyncSession = Depends(get_db)):
    lead = await db.get(Lead, lead_id)
    if not lead or lead.organization_id != current_user.organization_id:
        raise HTTPException(status_code=404, detail="Lead not found")
    note = LeadNote(lead_id=lead_id, author_id=current_user.id, content=body.content)
    db.add(note)
    await db.commit()
    await db.refresh(note)
    return note

@router.get("/{lead_id}/tags", response_model=List[TagResponse])
async def get_lead_tags(lead_id: str, current_user: User = Depends(require_crm_read), db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(Tag).join(LeadTag, LeadTag.tag_id == Tag.id).where(LeadTag.lead_id == lead_id)
    )
    return result.scalars().all()

@router.post("/{lead_id}/tags", response_model=Dict[str, Any])
async def add_lead_tag(lead_id: str, body: TagCreate, current_user: User = Depends(require_crm_write), db: AsyncSession = Depends(get_db)):
    lead = await db.get(Lead, lead_id)
    if not lead or lead.organization_id != current_user.organization_id:
        raise HTTPException(status_code=404, detail="Lead not found")
    
    result = await db.execute(select(Tag).where(Tag.name == body.name, Tag.organization_id == current_user.organization_id))
    tag = result.scalar_one_or_none()
    if not tag:
        tag = Tag(organization_id=current_user.organization_id, name=body.name.strip(), color=body.color)
        db.add(tag)
        await db.commit()
        await db.refresh(tag)
        
    lead_tag = LeadTag(lead_id=lead_id, tag_id=tag.id)
    db.add(lead_tag)
    await db.commit()
    return {"success": True, "tag": {"id": tag.id, "name": tag.name, "color": tag.color}}
"""

if "LeadBulkUpdate" not in content:
    content += new_routes

with open(file_path, "w", encoding="utf-8") as f:
    f.write(content)
print("leads.py patched")
