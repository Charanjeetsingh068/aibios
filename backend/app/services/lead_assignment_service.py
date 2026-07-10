import logging
from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func

from app.models.business import Lead, LeadAssignment, LeadHistory
from app.models.auth import User

logger = logging.getLogger(__name__)

class LeadAssignmentService:
    @staticmethod
    async def assign_manual(db: AsyncSession, lead: Lead, user_id: str, assigner_id: Optional[str] = None) -> Lead:
        user = await db.get(User, user_id)
        if not user or user.organization_id != lead.organization_id:
            raise ValueError("Invalid user assignment")
            
        old_assigned = lead.assigned_to
        lead.assigned_to = user_id
        
        assignment = LeadAssignment(
            lead_id=lead.id,
            assigned_from=old_assigned,
            assigned_to=user_id,
            assigned_by=assigner_id
        )
        db.add(assignment)
        
        history = LeadHistory(
            lead_id=lead.id,
            actor_id=assigner_id,
            action="assigned",
            field="assigned_to",
            old_value=old_assigned,
            new_value=user_id
        )
        db.add(history)
        
        await db.commit()
        await db.refresh(lead)
        return lead
        
    @staticmethod
    async def assign_least_busy(db: AsyncSession, lead: Lead, role_id: str = "sales_executive") -> Lead:
        # Simple least busy assignment
        query = select(User.id, func.count(Lead.id).label("lead_count")) \
            .outerjoin(Lead, User.id == Lead.assigned_to) \
            .where(User.organization_id == lead.organization_id, User.role_id == role_id) \
            .group_by(User.id) \
            .order_by("lead_count") \
            .limit(1)
            
        result = await db.execute(query)
        row = result.first()
        
        if row:
            user_id = row.id
            return await LeadAssignmentService.assign_manual(db, lead, user_id, assigner_id=None)
        return lead
