import logging
import secrets
from datetime import datetime
from typing import Any, Dict

import httpx
from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.api.v1.endpoints.auth import issue_session_tokens
from app.core.config import settings
from app.core.database import get_db
from app.core.security import get_password_hash
from app.models.auth import LoginHistory, Organization, User
from app.schemas.auth import TokenResponse

logger = logging.getLogger(__name__)
router = APIRouter()

# Google Identity Services' "code client" popup flow (used by the login page — no page
# redirect/new route involved) exchanges its authorization code with this literal,
# protocol-defined redirect_uri value instead of a real URL. See:
# https://developers.google.com/identity/oauth2/web/guides/use-code-model
GOOGLE_POPUP_REDIRECT_URI = "postmessage"


class OAuthCallbackPayload(BaseModel):
    code: str
    state: str


@router.get("/url/{provider}", response_model=Dict[str, Any])
async def get_oauth_url(provider: str):
    """Returns the authorization redirect URI for the specified OAuth provider."""
    provider = provider.lower()
    if provider == "google":
        if not settings.GOOGLE_CLIENT_ID:
            raise HTTPException(status_code=501, detail="Google OAuth is not configured (missing GOOGLE_CLIENT_ID).")
        redirect_uri = f"{settings.FRONTEND_URL}/auth/callback/google"
        scope = "https://www.googleapis.com/auth/userinfo.profile https://www.googleapis.com/auth/userinfo.email"
        url = f"https://accounts.google.com/o/oauth2/v2/auth?response_type=code&client_id={settings.GOOGLE_CLIENT_ID}&redirect_uri={redirect_uri}&scope={scope}&state=state_google"
        return {"url": url}
    elif provider == "facebook":
        if not settings.FACEBOOK_APP_ID:
            raise HTTPException(status_code=501, detail="Facebook OAuth is not configured (missing FACEBOOK_APP_ID).")
        redirect_uri = settings.FACEBOOK_REDIRECT_URI or f"{settings.FRONTEND_URL}/auth/callback/facebook"
        url = f"https://www.facebook.com/v18.0/dialog/oauth?client_id={settings.FACEBOOK_APP_ID}&redirect_uri={redirect_uri}&state=state_facebook&scope=email,public_profile"
        return {"url": url}
    elif provider == "instagram":
        if not settings.FACEBOOK_APP_ID:
            raise HTTPException(status_code=501, detail="Instagram OAuth is not configured (missing FACEBOOK_APP_ID).")
        redirect_uri = settings.FACEBOOK_REDIRECT_URI or f"{settings.FRONTEND_URL}/auth/callback/instagram"
        url = f"https://api.instagram.com/oauth/authorize?client_id={settings.FACEBOOK_APP_ID}&redirect_uri={redirect_uri}&scope=user_profile,user_media&response_type=code&state=state_instagram"
        return {"url": url}
    elif provider == "microsoft":
        if not settings.MICROSOFT_CLIENT_ID:
            raise HTTPException(status_code=501, detail="Microsoft OAuth is not configured (missing MICROSOFT_CLIENT_ID).")
        redirect_uri = f"{settings.FRONTEND_URL}/auth/callback/microsoft"
        scope = "openid profile email User.Read"
        url = f"https://login.microsoftonline.com/common/oauth2/v2.0/authorize?client_id={settings.MICROSOFT_CLIENT_ID}&response_type=code&redirect_uri={redirect_uri}&response_mode=query&scope={scope}&state=state_microsoft"
        return {"url": url}
    else:
        raise HTTPException(status_code=400, detail=f"Unsupported OAuth provider: {provider}")


@router.post("/callback/{provider}", response_model=TokenResponse)
async def oauth_callback(
    provider: str,
    payload: OAuthCallbackPayload,
    request: Request,
    db: AsyncSession = Depends(get_db)
):
    """Exchanges authorization code for access tokens and registers/logs in the user."""
    provider = provider.lower()
    email = ""
    first_name = ""
    last_name = ""

    if provider == "google":
        if not settings.GOOGLE_CLIENT_ID or not settings.GOOGLE_CLIENT_SECRET:
            raise HTTPException(status_code=501, detail="Google OAuth is not configured on this server.")
        try:
            async with httpx.AsyncClient() as client:
                token_res = await client.post(
                    "https://oauth2.googleapis.com/token",
                    data={
                        "code": payload.code,
                        "client_id": settings.GOOGLE_CLIENT_ID,
                        "client_secret": settings.GOOGLE_CLIENT_SECRET,
                        "redirect_uri": GOOGLE_POPUP_REDIRECT_URI,
                        "grant_type": "authorization_code"
                    }
                )
                if token_res.status_code == 200:
                    access_token = token_res.json().get("access_token")
                    profile_res = await client.get(
                        "https://www.googleapis.com/oauth2/v1/userinfo",
                        headers={"Authorization": f"Bearer {access_token}"}
                    )
                    if profile_res.status_code == 200:
                        profile = profile_res.json()
                        email = profile.get("email")
                        first_name = profile.get("given_name", "Google")
                        last_name = profile.get("family_name", "User")
        except Exception as e:
            logger.error(f"Google OAuth failed: {e}")

    elif provider == "facebook":
        if not settings.FACEBOOK_APP_ID or not settings.FACEBOOK_APP_SECRET:
            raise HTTPException(status_code=501, detail="Facebook OAuth is not configured on this server.")
        try:
            async with httpx.AsyncClient() as client:
                redirect_uri = settings.FACEBOOK_REDIRECT_URI or f"{settings.FRONTEND_URL}/auth/callback/facebook"
                token_res = await client.get(
                    "https://graph.facebook.com/v18.0/oauth/access_token",
                    params={
                        "client_id": settings.FACEBOOK_APP_ID,
                        "redirect_uri": redirect_uri,
                        "client_secret": settings.FACEBOOK_APP_SECRET,
                        "code": payload.code
                    }
                )
                if token_res.status_code == 200:
                    access_token = token_res.json().get("access_token")
                    profile_res = await client.get(
                        "https://graph.facebook.com/me",
                        params={
                            "fields": "id,name,email,first_name,last_name",
                            "access_token": access_token
                        }
                    )
                    if profile_res.status_code == 200:
                        profile = profile_res.json()
                        email = profile.get("email", f"{profile['id']}@facebook.com")
                        first_name = profile.get("first_name", "Facebook")
                        last_name = profile.get("last_name", "User")
        except Exception as e:
            logger.error(f"Facebook OAuth failed: {e}")

    elif provider == "microsoft":
        if not settings.MICROSOFT_CLIENT_ID or not settings.MICROSOFT_CLIENT_SECRET:
            raise HTTPException(status_code=501, detail="Microsoft OAuth is not configured on this server.")
        try:
            async with httpx.AsyncClient() as client:
                token_res = await client.post(
                    "https://login.microsoftonline.com/common/oauth2/v2.0/token",
                    data={
                        "code": payload.code,
                        "client_id": settings.MICROSOFT_CLIENT_ID,
                        "client_secret": settings.MICROSOFT_CLIENT_SECRET,
                        "redirect_uri": f"{settings.FRONTEND_URL}/auth/callback/microsoft",
                        "grant_type": "authorization_code",
                        "scope": "openid profile email User.Read",
                    }
                )
                if token_res.status_code == 200:
                    access_token = token_res.json().get("access_token")
                    profile_res = await client.get(
                        "https://graph.microsoft.com/v1.0/me",
                        headers={"Authorization": f"Bearer {access_token}"}
                    )
                    if profile_res.status_code == 200:
                        profile = profile_res.json()
                        email = profile.get("mail") or profile.get("userPrincipalName")
                        display_name = profile.get("displayName", "Microsoft User")
                        name_parts = display_name.split(" ", 1)
                        first_name = profile.get("givenName") or name_parts[0]
                        last_name = profile.get("surname") or (name_parts[1] if len(name_parts) > 1 else "")
        except Exception as e:
            logger.error(f"Microsoft OAuth failed: {e}")

    else:
        raise HTTPException(status_code=400, detail=f"Unsupported OAuth provider: {provider}")

    if not email:
        # Token exchange or profile fetch failed/returned no email — do not fabricate an
        # identity and log the caller in anyway; that would be an authentication bypass.
        raise HTTPException(status_code=400, detail=f"{provider.capitalize()} authentication failed: could not verify identity.")

    user_stmt = select(User).where(User.email == email).options(selectinload(User.organization))
    user_res = await db.execute(user_stmt)
    user = user_res.scalar_one_or_none()

    if not user:
        org_stmt = select(Organization).limit(1)
        org_res = await db.execute(org_stmt)
        org = org_res.scalar_one_or_none()
        if not org:
            org = Organization(name="OAuth Seed Org", slug="oauth-seed")
            db.add(org)
            await db.commit()
            await db.refresh(org)

        user = User(
            organization_id=org.id,
            first_name=first_name,
            last_name=last_name,
            email=email,
            password_hash=get_password_hash(secrets.token_urlsafe(32)),  # OAuth-only account, no usable password
            role_id="manager",
            status="active"
        )
        db.add(user)
        await db.commit()
        await db.refresh(user)
        user.organization = org  # populate the relationship in-memory; avoids a second query

    if user.status != "active":
        raise HTTPException(status_code=403, detail="Your user account is deactivated")
    if user.organization.status != "active":
        raise HTTPException(status_code=403, detail="Your tenant organization is deactivated")

    ip_address = request.client.host if request.client else None
    device_info = request.headers.get("user-agent", "Unknown Device")

    # Issue a full session + rotatable refresh token (same as password login) so token
    # refresh and logout work identically regardless of how the user signed in.
    token_response = await issue_session_tokens(db, user, ip_address, device_info, remember_me=True)

    db.add(LoginHistory(
        user_id=user.id,
        organization_id=user.organization_id,
        email=user.email,
        status="success",
        ip_address=ip_address,
        device_info=f"{device_info} (OAuth: {provider})",
    ))
    user.last_login = datetime.utcnow()
    await db.commit()

    return token_response
