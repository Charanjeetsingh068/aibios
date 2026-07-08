import logging
from typing import Any, Dict, List, Optional
from urllib.parse import urlencode

import httpx
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type

from app.core.config import settings

logger = logging.getLogger(__name__)

GRAPH_API_VERSION = "v18.0"
GRAPH_API_BASE = f"https://graph.facebook.com/{GRAPH_API_VERSION}"

# Business-integration scopes (page/lead/instagram management) — distinct from the
# user-login scopes (`email,public_profile`) used by app/api/v1/endpoints/oauth.py.
META_BUSINESS_SCOPES = [
    "pages_show_list",
    "pages_manage_metadata",
    "leads_retrieval",
    "business_management",
    "instagram_basic",
    "instagram_manage_messages",
]

REQUEST_TIMEOUT_SECONDS = 15.0

# Transient failures worth retrying; a 4xx application error (bad token, bad request) never
# succeeds on retry so those are not included.
RETRYABLE_EXCEPTIONS = (httpx.ConnectError, httpx.ConnectTimeout, httpx.ReadTimeout)


class MetaNotConfiguredError(Exception):
    """Raised when FACEBOOK_APP_ID/FACEBOOK_APP_SECRET/FACEBOOK_REDIRECT_URI aren't set."""


class MetaAPIError(Exception):
    """Raised when the Graph API itself returns an error response (bad token, revoked
    permission, rate limit, etc.) — distinct from MetaNotConfiguredError and from transient
    network failures, so callers can report an honest, specific error."""

    def __init__(self, message: str, status_code: Optional[int] = None):
        super().__init__(message)
        self.status_code = status_code


def _require_configured() -> None:
    if not (settings.FACEBOOK_APP_ID and settings.FACEBOOK_APP_SECRET and settings.FACEBOOK_REDIRECT_URI):
        raise MetaNotConfiguredError(
            "Meta integration is not configured (missing FACEBOOK_APP_ID/FACEBOOK_APP_SECRET/FACEBOOK_REDIRECT_URI)."
        )


def build_oauth_url(state: str) -> str:
    """Builds the real Meta OAuth dialog URL with business-integration scopes."""
    _require_configured()
    params = {
        "client_id": settings.FACEBOOK_APP_ID,
        "redirect_uri": settings.FACEBOOK_REDIRECT_URI,
        "state": state,
        "scope": ",".join(META_BUSINESS_SCOPES),
        "response_type": "code",
    }
    return f"https://www.facebook.com/{GRAPH_API_VERSION}/dialog/oauth?{urlencode(params)}"


@retry(
    reraise=True,
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=1, max=8),
    retry=retry_if_exception_type(RETRYABLE_EXCEPTIONS),
)
async def _get(path: str, params: Dict[str, Any]) -> Dict[str, Any]:
    async with httpx.AsyncClient(timeout=REQUEST_TIMEOUT_SECONDS) as client:
        res = await client.get(f"{GRAPH_API_BASE}{path}", params=params)
    body = res.json() if res.content else {}
    if res.status_code != 200 or "error" in body:
        err = body.get("error", {})
        raise MetaAPIError(err.get("message", res.text), status_code=res.status_code)
    return body


@retry(
    reraise=True,
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=1, max=8),
    retry=retry_if_exception_type(RETRYABLE_EXCEPTIONS),
)
async def _post(path: str, params: Dict[str, Any]) -> Dict[str, Any]:
    async with httpx.AsyncClient(timeout=REQUEST_TIMEOUT_SECONDS) as client:
        res = await client.post(f"{GRAPH_API_BASE}{path}", params=params)
    body = res.json() if res.content else {}
    if res.status_code != 200 or "error" in body:
        err = body.get("error", {})
        raise MetaAPIError(err.get("message", res.text), status_code=res.status_code)
    return body


async def exchange_code_for_user_token(code: str) -> Dict[str, Any]:
    """Exchanges an OAuth authorization code for a short-lived user access token."""
    _require_configured()
    return await _get("/oauth/access_token", {
        "client_id": settings.FACEBOOK_APP_ID,
        "client_secret": settings.FACEBOOK_APP_SECRET,
        "redirect_uri": settings.FACEBOOK_REDIRECT_URI,
        "code": code,
    })


async def exchange_for_long_lived_token(short_lived_token: str) -> Dict[str, Any]:
    """Exchanges a short-lived (or an about-to-expire long-lived) user token for a fresh
    long-lived token (~60 days). This is also the real token-refresh mechanism used by
    the Integration Manager (Stage 5)."""
    _require_configured()
    return await _get("/oauth/access_token", {
        "grant_type": "fb_exchange_token",
        "client_id": settings.FACEBOOK_APP_ID,
        "client_secret": settings.FACEBOOK_APP_SECRET,
        "fb_exchange_token": short_lived_token,
    })


async def list_managed_pages(user_access_token: str) -> List[Dict[str, Any]]:
    """Lists the Facebook Pages the authenticated user manages, each with its own
    non-expiring page access token — the real replacement for the previous
    `secrets.token_hex(8)` fake external_account_id."""
    body = await _get("/me/accounts", {"access_token": user_access_token, "fields": "id,name,category,access_token,tasks"})
    return body.get("data", [])


async def subscribe_page_webhook(page_id: str, page_access_token: str, fields: str = "leadgen") -> Dict[str, Any]:
    """Subscribes this app to the given Page's leadgen (and optionally other) webhook fields."""
    return await _post(f"/{page_id}/subscribed_apps", {
        "access_token": page_access_token,
        "subscribed_fields": fields,
    })


async def list_lead_forms(page_id: str, page_access_token: str) -> List[Dict[str, Any]]:
    """Discovers Lead Ads forms configured on a Page."""
    body = await _get(f"/{page_id}/leadgen_forms", {"access_token": page_access_token, "fields": "id,name,status"})
    return body.get("data", [])


async def retrieve_lead_data(leadgen_id: str, page_access_token: str) -> Dict[str, Optional[str]]:
    """Retrieves the actual submitted field answers (name/email/phone) for a leadgen event.
    The webhook payload itself only carries the leadgen_id — this call is required to get
    real contact details, closing the gap the leadgen webhook handler previously left as
    permanently-null fields."""
    body = await _get(f"/{leadgen_id}", {"access_token": page_access_token, "fields": "field_data,created_time"})
    fields: Dict[str, Optional[str]] = {"full_name": None, "email": None, "phone_number": None}
    for entry in body.get("field_data", []):
        name = (entry.get("name") or "").lower()
        values = entry.get("values") or []
        value = values[0] if values else None
        if name in ("full_name", "name"):
            fields["full_name"] = value
        elif name == "email":
            fields["email"] = value
        elif name in ("phone_number", "phone"):
            fields["phone_number"] = value
    return fields


async def get_instagram_business_account(page_id: str, page_access_token: str) -> Optional[Dict[str, Any]]:
    """Resolves the Instagram Business account linked to a Page, if any."""
    body = await _get(f"/{page_id}", {
        "access_token": page_access_token,
        "fields": "instagram_business_account{id,username}",
    })
    return body.get("instagram_business_account")


async def revoke_user_permissions(user_id: str, user_access_token: str) -> None:
    """Revokes this app's permissions on behalf of the user (real disconnect, not just a
    local status flip) — used by the Integration Manager's disconnect flow."""
    async with httpx.AsyncClient(timeout=REQUEST_TIMEOUT_SECONDS) as client:
        res = await client.delete(f"{GRAPH_API_BASE}/{user_id}/permissions", params={"access_token": user_access_token})
    if res.status_code != 200:
        logger.warning(f"Meta permission revoke returned non-200 ({res.status_code}): {res.text}")
