import logging
from typing import Any, Dict, List

from app.core.config import settings

logger = logging.getLogger(__name__)

# Each external integration's readiness is reported as "configured" / "not_configured"
# based on whether its required credentials are present. Shared by the health endpoint
# and the startup validation log so both report the exact same thing.
INTEGRATION_REQUIREMENTS: Dict[str, List[str]] = {
    "openai": ["OPENAI_API_KEY"],
    "twilio": ["TWILIO_ACCOUNT_SID", "TWILIO_AUTH_TOKEN", "TWILIO_PHONE_NUMBER"],
    "whatsapp": ["WHATSAPP_ACCESS_TOKEN", "WHATSAPP_PHONE_NUMBER_ID", "WHATSAPP_APP_SECRET"],
    "google_oauth": ["GOOGLE_CLIENT_ID", "GOOGLE_CLIENT_SECRET"],
    "microsoft_oauth": ["MICROSOFT_CLIENT_ID", "MICROSOFT_CLIENT_SECRET"],
    "facebook_oauth": ["FACEBOOK_APP_ID", "FACEBOOK_APP_SECRET"],
    "smtp": ["SMTP_HOST", "SMTP_USER", "SMTP_PASSWORD", "SMTP_FROM_EMAIL"],
    "s3_storage": ["AWS_ACCESS_KEY_ID", "AWS_SECRET_ACCESS_KEY", "AWS_STORAGE_BUCKET_NAME"],
    "elevenlabs": ["ELEVENLABS_API_KEY"],
    "cartesia": ["CARTESIA_API_KEY"],
    "azure_speech": ["AZURE_SPEECH_KEY", "AZURE_SPEECH_REGION"],
    "google_tts": ["GOOGLE_TTS_API_KEY"],
    # Not a third-party integration, but a prerequisite for storing any of them per-organization
    # (Meta/WhatsApp/voice/n8n OAuth tokens & API keys) — surfaced here so /health and the
    # startup log make the dependency visible rather than failing silently on first use.
    "encryption": ["ENCRYPTION_KEY"],
}

# The exact placeholder value shipped in .env.example — if this is still active in
# production, JWTs are effectively signed with a publicly-known key.
_DEFAULT_SECRET_KEY_PLACEHOLDER = "supersecretchangeinproduction_2026_aibos_token_generation_key"


def get_integration_statuses() -> Dict[str, Dict[str, Any]]:
    result = {}
    for name, required_keys in INTEGRATION_REQUIREMENTS.items():
        missing = [k for k in required_keys if not getattr(settings, k, None)]
        result[name] = {
            "status": "configured" if not missing else "not_configured",
            "missing": missing,
        }
    return result


def validate_environment_on_startup() -> None:
    """Logs a clear, one-time summary at boot: which integrations are configured, and
    (in production) which critical settings are missing or still at their insecure
    development defaults. Never raises — a misconfigured optional integration should
    degrade that integration, not prevent the whole app from starting."""
    is_production = settings.ENVIRONMENT in ("production", "prod")

    if is_production:
        if settings.SECRET_KEY == _DEFAULT_SECRET_KEY_PLACEHOLDER:
            logger.error(
                "SECURITY: SECRET_KEY is still the default placeholder value from .env.example. "
                "JWTs can be forged by anyone who has read the source. Set a unique SECRET_KEY."
            )
        if not settings.ALLOWED_HOSTS:
            logger.error(
                "SECURITY: ALLOWED_HOSTS is empty in production — TrustedHostMiddleware will "
                "reject every request until it's set to your real domain(s)."
            )
        if settings.FRONTEND_URL.startswith("http://localhost"):
            logger.warning(
                "FRONTEND_URL is still localhost in production — password reset/invite links "
                "sent to users will point at the wrong host."
            )
        if not settings.ADMIN_EMAIL or not settings.ADMIN_PASSWORD:
            logger.warning(
                "ADMIN_EMAIL/ADMIN_PASSWORD are not both set — no super-admin account will be "
                "bootstrapped unless one already exists in the database."
            )

    statuses = get_integration_statuses()
    configured = [name for name, s in statuses.items() if s["status"] == "configured"]
    not_configured = [name for name, s in statuses.items() if s["status"] == "not_configured"]
    logger.info(f"Integrations configured: {configured or 'none'}")
    logger.info(f"Integrations not configured (will fail closed / degrade gracefully): {not_configured or 'none'}")
