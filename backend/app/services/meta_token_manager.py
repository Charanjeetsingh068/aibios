import logging
from datetime import datetime
from typing import Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.crypto import CryptoNotConfiguredError, decrypt_value, encrypt_value
from app.models.enterprise_integrations import IntegrationCredential, TokenHistory
from app.services import meta_service

logger = logging.getLogger(__name__)

class TokenManager:
    @staticmethod
    async def refresh_token_if_needed(db: AsyncSession, credential_id: str) -> Optional[str]:
        """Check if token needs refresh and do it via meta_service."""
        result = await db.execute(select(IntegrationCredential).where(IntegrationCredential.id == credential_id))
        credential = result.scalar_one_or_none()
        
        if not credential or not credential.access_token_encrypted:
            return None
            
        try:
            token = decrypt_value(credential.access_token_encrypted)
        except (CryptoNotConfiguredError, ValueError):
            logger.error(f"Failed to decrypt token for credential {credential_id}")
            return None

        # Example check: if token expires in less than 5 days, refresh it
        # Real Meta long-lived tokens last ~60 days
        if credential.expires_at and (credential.expires_at - datetime.utcnow()).days < 5:
            try:
                long_lived = await meta_service.exchange_for_long_lived_token(token)
                new_token = long_lived.get("access_token")
                if new_token:
                    credential.access_token_encrypted = encrypt_value(new_token)
                    credential.last_refreshed_at = datetime.utcnow()
                    
                    history = TokenHistory(
                        credential_id=credential.id,
                        action="refreshed",
                        detail="Auto-refreshed via TokenManager"
                    )
                    db.add(history)
                    await db.commit()
                    return new_token
            except meta_service.MetaAPIError as e:
                credential.status = "error"
                credential.last_error = str(e)
                history = TokenHistory(credential_id=credential.id, action="error", detail=str(e))
                db.add(history)
                await db.commit()
                return None

        return token

    @staticmethod
    async def log_disconnect(db: AsyncSession, credential_id: str, reason: str = "User initiated disconnect"):
        result = await db.execute(select(IntegrationCredential).where(IntegrationCredential.id == credential_id))
        credential = result.scalar_one_or_none()
        if credential:
            credential.status = "disconnected"
            credential.access_token_encrypted = None
            history = TokenHistory(credential_id=credential_id, action="disconnected", detail=reason)
            db.add(history)
            await db.commit()
