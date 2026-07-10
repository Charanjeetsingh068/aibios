import base64
import hashlib
import hmac
from datetime import datetime, timedelta
from typing import Any, Dict, Optional, Union

from fastapi.security import OAuth2PasswordBearer
from jose import jwt
from passlib.context import CryptContext

from app.core.config import settings

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl=f"{settings.API_V1_STR}/auth/login", auto_error=False)

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verifies that a plain password matches its hashed equivalent."""
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password: str) -> str:
    """Generates a secure hash from a plain text password."""
    return pwd_context.hash(password)

def create_access_token(subject: Union[str, Any], expires_delta: Optional[timedelta] = None) -> str:
    """Creates a JWT access token containing a subject claims payload."""
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    
    to_encode = {"exp": expire, "sub": str(subject)}
    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm="HS256")
    return encoded_jwt

# ==============================================================================
# Webhook signature verification (Meta Graph API / WhatsApp Cloud API / Twilio)
# ==============================================================================

def verify_meta_signature(app_secret: Optional[str], payload: bytes, signature_header: Optional[str]) -> bool:
    """
    Validates Meta's X-Hub-Signature-256 header (used by both the Facebook Graph API
    leadgen webhook and the WhatsApp Cloud API webhook) against the raw request body.
    Fails closed: returns False if the app secret isn't configured or anything is missing.
    """
    if not app_secret or not signature_header:
        return False
    try:
        algo, _, signature = signature_header.partition("=")
        if algo != "sha256" or not signature:
            return False
        expected = hmac.new(app_secret.encode("utf-8"), payload, hashlib.sha256).hexdigest()
        return hmac.compare_digest(expected, signature)
    except Exception:
        return False


def verify_twilio_signature(auth_token: Optional[str], full_url: str, params: Dict[str, Any], signature_header: Optional[str]) -> bool:
    """
    Validates Twilio's X-Twilio-Signature header per Twilio's documented algorithm:
    HMAC-SHA1 of the request URL plus each POST param (sorted by key, key+value concatenated),
    base64-encoded. Fails closed if the auth token isn't configured.
    Note: `full_url` must exactly match the URL configured in the Twilio console (scheme/host
    included) — if this app runs behind a reverse proxy, that must preserve the public https URL.
    """
    if not auth_token or not signature_header:
        return False
    try:
        data = full_url
        for key in sorted(params.keys()):
            data += key + str(params[key])
        expected = base64.b64encode(
            hmac.new(auth_token.encode("utf-8"), data.encode("utf-8"), hashlib.sha1).digest()
        ).decode("utf-8")
        return hmac.compare_digest(expected, signature_header)
    except Exception:
        return False


def sign_hmac_sha256(secret: str, payload: bytes, prefix: str = "sha256=") -> str:
    """Produces an HMAC-SHA256 signature header value for outbound webhook calls
    (e.g. this server calling out to an n8n webhook), in the same `prefix=hexdigest`
    shape Meta uses for X-Hub-Signature-256 — the paired counterpart to
    verify_hmac_sha256_signature below, so callers can be verified with the same helper."""
    digest = hmac.new(secret.encode("utf-8"), payload, hashlib.sha256).hexdigest()
    return f"{prefix}{digest}"


def verify_hmac_sha256_signature(secret: Optional[str], payload: bytes, signature_header: Optional[str], prefix: str = "sha256=") -> bool:
    """Generic HMAC-SHA256 webhook signature verification for callers that don't follow
    Meta's exact `X-Hub-Signature-256` conventions (e.g. n8n inbound callbacks signed with a
    per-organization webhook_secret). Fails closed: returns False if the secret or header is
    missing. Uses hmac.compare_digest to avoid timing attacks."""
    if not secret or not signature_header:
        return False
    try:
        if not signature_header.startswith(prefix):
            return False
        signature = signature_header[len(prefix):]
        expected = hmac.new(secret.encode("utf-8"), payload, hashlib.sha256).hexdigest()
        return hmac.compare_digest(expected, signature)
    except Exception:
        return False


def get_security_headers(environment: str) -> dict[str, str]:
    """
    Returns security headers based on the active environment (development or production).
    """
    # Enterprise-grade base headers
    headers = {
        "X-Frame-Options": "DENY",
        "X-Content-Type-Options": "nosniff",
        "X-XSS-Protection": "1; mode=block",
        "Referrer-Policy": "strict-origin-when-cross-origin",
        "Permissions-Policy": "geolocation=(), microphone=(), camera=()",
        "X-Permitted-Cross-Domain-Policies": "none",
        "Cross-Origin-Opener-Policy": "same-origin",
        "Cross-Origin-Resource-Policy": "same-origin"
    }
    
    if environment.lower() == "development":
        # Relaxed CSP for local development to allow Swagger UI, ReDoc, and OpenAPI assets (from CDN / localhost)
        headers["Content-Security-Policy"] = (
            "default-src 'self'; "
            "script-src 'self' 'unsafe-inline' cdn.jsdelivr.net; "
            "style-src 'self' 'unsafe-inline' cdn.jsdelivr.net; "
            "img-src 'self' data: fastapi.tiangolo.com cdn.jsdelivr.net; "
            "connect-src 'self' http://localhost:8000 http://localhost:3000 http://127.0.0.1:8000 http://127.0.0.1:3000 ws://localhost:3000 ws://127.0.0.1:3000; "
            "frame-ancestors 'none';"
        )
    else:
        # Strict security headers for production environment
        headers["Content-Security-Policy"] = (
            "default-src 'self'; "
            "frame-ancestors 'none';"
        )
        
    return headers


from sqlalchemy import or_

def get_visibility_filter(model, current_user):
    """
    Generates a SQLAlchemy filter condition for a given TenantResourceMixin model
    based on the current_user's permissions, teams, and the model's visibility field.
    """
    # If the user is a super admin, they see all records in their organization.
    permissions = current_user.all_permission_ids()
    if "admin.all" in permissions:
        return True # No extra filtering needed beyond organization_id

    # Base filter: User owns the record
    owner_filter = getattr(model, "owner_id") == current_user.id
    
    # Global / Organization visibility: anyone in the org can see
    org_filter = getattr(model, "visibility").in_(["global", "organization"])
    
    # Team visibility: if the record belongs to a team the user is part of
    # We would need to query the user's teams, but we can do a subquery or pass team_ids.
    # For now, if the user isn't an admin, they see records they own or org-level records.
    return or_(owner_filter, org_filter)
