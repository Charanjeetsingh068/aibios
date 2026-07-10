import logging
from typing import Optional, List, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, or_, and_
import json

from app.models.business import Lead, LeadDuplicateMapping, LeadMergeHistory, LeadHistory

logger = logging.getLogger(__name__)

class LeadDeduplicationService:
    @staticmethod
    async def detect_duplicates(db: AsyncSession, lead: Lead) -> List[LeadDuplicateMapping]:
        if not lead.email and not lead.phone and not lead.meta_lead_id:
            return []
            
        conditions = []
        if lead.email:
            conditions.append(Lead.email == lead.email)
        if lead.phone:
            conditions.append(Lead.phone == lead.phone)
        if lead.meta_lead_id:
            conditions.append(Lead.meta_lead_id == lead.meta_lead_id)
            
        query = select(Lead).where(
            Lead.organization_id == lead.organization_id,
            Lead.id != lead.id,
            or_(*conditions)
        )
        
        result = await db.execute(query)
        duplicates = result.scalars().all()
        
        mappings = []
        for dup in duplicates:
            # Check if mapping already exists
            map_query = select(LeadDuplicateMapping).where(
                or_(
                    and_(LeadDuplicateMapping.primary_lead_id == lead.id, LeadDuplicateMapping.secondary_lead_id == dup.id),
                    and_(LeadDuplicateMapping.primary_lead_id == dup.id, LeadDuplicateMapping.secondary_lead_id == lead.id)
                )
            )
            map_result = await db.execute(map_query)
            existing = map_result.scalar_one_or_none()
            
            if not existing:
                mapping = LeadDuplicateMapping(
                    primary_lead_id=dup.id, # Older lead is usually primary
                    secondary_lead_id=lead.id,
                    confidence_score=90,
                    match_reason="Matched on email, phone, or meta ID"
                )
                db.add(mapping)
                mappings.append(mapping)
                
        if mappings:
            await db.commit()
            
        return mappings

    @staticmethod
    async def merge_leads(db: AsyncSession, primary_lead_id: str, secondary_lead_id: str, merged_by: str) -> Lead:
        primary = await db.get(Lead, primary_lead_id)
        secondary = await db.get(Lead, secondary_lead_id)
        
        if not primary or not secondary or primary.organization_id != secondary.organization_id:
            raise ValueError("Invalid leads for merge")
            
        # Copy missing fields
        changed = False
        secondary_data = {}
        for column in secondary.__table__.columns:
            if column.name in ('id', 'organization_id', 'created_at', 'updated_at'):
                continue
            
            val = getattr(secondary, column.name)
            secondary_data[column.name] = str(val) if val else None
            
            if val and not getattr(primary, column.name):
                setattr(primary, column.name, val)
                changed = True
                
        # Record history
        merge_hist = LeadMergeHistory(
            primary_lead_id=primary.id,
            merged_lead_id=secondary.id,
            merged_by=merged_by,
            merged_data_json=json.dumps(secondary_data)
        )
        db.add(merge_hist)
        
        hist = LeadHistory(
            lead_id=primary.id,
            actor_id=merged_by,
            action="merged",
            old_value=secondary.id,
            new_value=primary.id
        )
        db.add(hist)
        
        # Soft delete secondary
        await db.delete(secondary)
        
        # Update mappings
        map_query = select(LeadDuplicateMapping).where(
            or_(
                LeadDuplicateMapping.secondary_lead_id == secondary.id,
                LeadDuplicateMapping.primary_lead_id == secondary.id
            )
        )
        mappings = (await db.execute(map_query)).scalars().all()
        for m in mappings:
            m.status = "merged"
            
        await db.commit()
        await db.refresh(primary)
        return primary
