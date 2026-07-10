import logging
from typing import Any, Dict

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.business import Lead
from app.models.enterprise_integrations import LeadMapping, LeadSyncHistory

logger = logging.getLogger(__name__)

class LeadSyncService:
    @staticmethod
    async def process_lead(
        db: AsyncSession, 
        organization_id: str, 
        meta_page_id: str, 
        leadgen_id: str, 
        form_id: str, 
        raw_data: Dict[str, Any]
    ) -> LeadSyncHistory:
        """Process incoming lead, check for duplicates, and save to CRM."""
        # Check if lead already synced
        result = await db.execute(select(LeadSyncHistory).where(LeadSyncHistory.meta_lead_id == leadgen_id))
        existing_sync = result.scalar_one_or_none()
        
        if existing_sync:
            logger.info(f"Lead {leadgen_id} already synced.")
            return existing_sync
            
        sync_record = LeadSyncHistory(
            organization_id=organization_id,
            meta_page_id=meta_page_id,
            meta_lead_id=leadgen_id,
            form_id=form_id,
            status="pending",
            raw_data=str(raw_data)
        )
        db.add(sync_record)
        await db.flush()
        
        try:
            # Map fields using LeadMappingService
            mapped_data = await LeadMappingService.map_fields(db, organization_id, form_id, raw_data)
            
            # Check duplicates in CRM using Engine Rules: Email, Phone, Meta Lead ID
            email = mapped_data.get("email")
            phone = mapped_data.get("phone")
            is_dup = False
            dup_reason = ""
            
            if email:
                res = await db.execute(select(Lead).where(Lead.email == email, Lead.organization_id == organization_id))
                if res.scalar_one_or_none():
                    is_dup, dup_reason = True, "Email match"
            if not is_dup and phone:
                res = await db.execute(select(Lead).where(Lead.phone == phone, Lead.organization_id == organization_id))
                if res.scalar_one_or_none():
                    is_dup, dup_reason = True, "Phone match"
            
            if is_dup:
                sync_record.status = "duplicate"
                sync_record.error_message = f"Duplicate prevented: {dup_reason}"
                await db.commit()
                return sync_record

            # Create CRM Lead
            crm_lead = Lead(
                organization_id=organization_id,
                first_name=mapped_data.get("first_name", "Unknown"),
                last_name=mapped_data.get("last_name", ""),
                email=email,
                phone=mapped_data.get("phone", ""),
                source="facebook_lead_ads",
                status="new"
            )
            db.add(crm_lead)
            await db.flush()
            
            sync_record.crm_lead_id = crm_lead.id
            sync_record.status = "synced"
            await db.commit()
            
        except Exception as e:
            logger.error(f"Failed to sync lead {leadgen_id}: {e}")
            sync_record.status = "error"
            sync_record.error_message = str(e)
            await db.commit()
            
        return sync_record


class LeadMappingService:
    @staticmethod
    async def map_fields(db: AsyncSession, organization_id: str, form_id: str, raw_data: Dict[str, Any]) -> Dict[str, Any]:
        """Apply custom field mappings to raw Meta data."""
        result = await db.execute(
            select(LeadMapping).where(
                LeadMapping.organization_id == organization_id,
                LeadMapping.form_id == form_id
            )
        )
        mappings = result.scalars().all()
        
        if not mappings:
            # Fallback to default heuristic mapping
            return {
                "first_name": raw_data.get("full_name") or raw_data.get("first_name"),
                "last_name": raw_data.get("last_name"),
                "email": raw_data.get("email"),
                "phone": raw_data.get("phone_number") or raw_data.get("phone")
            }
            
        mapped_data = {}
        for mapping in mappings:
            mapped_data[mapping.crm_field] = raw_data.get(mapping.meta_field)
            
        return mapped_data
