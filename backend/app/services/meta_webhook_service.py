import hashlib
import hmac
import logging

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.models.enterprise_integrations import WebhookLog

logger = logging.getLogger(__name__)

class WebhookValidator:
    @staticmethod
    def verify_signature(payload_body: bytes, signature_header: str) -> bool:
        if not signature_header or not signature_header.startswith("sha256="):
            return False
            
        expected_signature = signature_header.split("=")[1]
        
        # Calculate expected HMAC
        secret = settings.FACEBOOK_APP_SECRET.encode('utf-8')
        mac = hmac.new(secret, msg=payload_body, digestmod=hashlib.sha256)
        return hmac.compare_digest(mac.hexdigest(), expected_signature)


class MetaWebhookService:
    @staticmethod
    async def log_webhook(
        db: AsyncSession, 
        event_type: str, 
        payload: str, 
        signature: str,
        status: str = "pending",
        error_message: str = None
    ) -> WebhookLog:
        """Log an incoming webhook for later processing or debugging."""
        log_entry = WebhookLog(
            event_type=event_type,
            payload=payload,
            signature=signature,
            status=status,
            error_message=error_message
        )
        db.add(log_entry)
        await db.commit()
        return log_entry
