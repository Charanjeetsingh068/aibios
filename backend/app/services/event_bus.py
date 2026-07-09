import json
import logging
from typing import Any, Dict

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.business import AutomationEvent

logger = logging.getLogger(__name__)


async def dispatch_event(db: AsyncSession, organization_id: str, event_name: str, payload: Dict[str, Any]) -> AutomationEvent:
    """Publishes a trigger-worthy event for an organization. Persists it to AutomationEvent
    and commits its own transaction so a failure here never rolls back the caller's primary
    write. The native automation engine's trigger dispatcher (Phase 3) will read from this
    table to actually run matching workflows; for now the event is durably recorded but not
    yet executed against anything."""
    event = AutomationEvent(
        organization_id=organization_id,
        event_name=event_name,
        payload_json=json.dumps(payload)[:2000],
    )
    db.add(event)
    try:
        await db.commit()
    except Exception:
        logger.exception(f"Failed to persist automation event '{event_name}' for org {organization_id}")
        await db.rollback()
    return event
