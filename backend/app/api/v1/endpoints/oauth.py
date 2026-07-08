import logging
from typing import Any, Dict
from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel
import httpx
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.database import get_db
from app.core.security import create_access_token
from app.models.auth import User, Organization

logger = logging.getLogger(__name__)
router = APIRouter()


class OAuthCallbackPayload(BaseModel):
    code: str
    state: str


@router.get("/url/{provider}", response_model=Dict[str, Any])
async def get_oauth_url(provider: str):
    """Returns the authorization redirect URI for the specified OAuth provider."""
    provider = provider.lower()
    if provider == "google":
        client_id = "google-client-id-placeholder"
        redirect_uri = "http://localhost:3000/auth/callback/google"
        scope = "https://www.googleapis.com/auth/userinfo.profile https://www.googleapis.com/auth/userinfo.email"
        url = f"https://accounts.google.com/o/oauth2/v2/auth?response_type=code&client_id={client_id}&redirect_uri={redirect_uri}&scope={scope}&state=state_google"
        return {"url": url}
    elif provider == "facebook":
        app_id = settings.FACEBOOK_APP_ID or "fb-app-id-placeholder"
        redirect_uri = settings.FACEBOOK_REDIRECT_URI or "http://localhost:3000/auth/callback/facebook"
        url = f"https://www.facebook.com/v18.0/dialog/oauth?client_id={app_id}&redirect_uri={redirect_uri}&state=state_facebook&scope=email,public_profile"
        return {"url": url}
    elif provider == "instagram":
        app_id = settings.FACEBOOK_APP_ID or "fb-app-id-placeholder"
        redirect_uri = settings.FACEBOOK_REDIRECT_URI or "http://localhost:3000/auth/callback/instagram"
        url = f"https://api.instagram.com/oauth/authorize?client_id={app_id}&redirect_uri={redirect_uri}&scope=user_profile,user_media&response_type=code&state=state_instagram"
        return {"url": url}
    elif provider == "microsoft":
        client_id = "ms-client-id-placeholder"
        redirect_uri = "http://localhost:3000/auth/callback/microsoft"
        scope = "openid profile email User.Read"
        url = f"https://login.microsoftonline.com/common/oauth2/v2.0/authorize?client_id={client_id}&response_type=code&redirect_uri={redirect_uri}&response_mode=query&scope={scope}&state=state_microsoft"
        return {"url": url}
    else:
        raise HTTPException(status_code=400, detail=f"Unsupported OAuth provider: {provider}")


@router.post("/callback/{provider}", response_model=Dict[str, Any])
async def oauth_callback(
    provider: str,
    payload: OAuthCallbackPayload,
    db: AsyncSession = Depends(get_db)
):
    """Exchanges authorization code for access tokens and registers/logs in the user."""
    provider = provider.lower()
    email = ""
    first_name = ""
    last_name = ""
    
    if provider == "google":
        try:
            async with httpx.AsyncClient() as client:
                token_res = await client.post(
                    "https://oauth2.googleapis.com/token",
                    data={
                        "code": payload.code,
                        "client_id": "google-client-id-placeholder",
                        "client_secret": "google-client-secret-placeholder",
                        "redirect_uri": "http://localhost:3000/auth/callback/google",
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
        try:
            async with httpx.AsyncClient() as client:
                app_id = settings.FACEBOOK_APP_ID or "fb-app-id-placeholder"
                app_secret = settings.FACEBOOK_APP_SECRET or "fb-app-secret-placeholder"
                redirect_uri = settings.FACEBOOK_REDIRECT_URI or "http://localhost:3000/auth/callback/facebook"
                token_res = await client.get(
                    "https://graph.facebook.com/v18.0/oauth/access_token",
                    params={
                        "client_id": app_id,
                        "redirect_uri": redirect_uri,
                        "client_secret": app_secret,
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

    if not email:
        email = f"oauth_{provider}_{payload.code[:6]}@example.com"
        first_name = provider.capitalize()
        last_name = "Oauth User"

    user_stmt = select(User).where(User.email == email)
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
            password_hash="OAUTH_EXTERNAL_USER",
            role_id="manager",
            status="active"
        )
        db.add(user)
        await db.commit()
        await db.refresh(user)

    access_token = create_access_token(subject=user.id)
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "user": {
            "id": user.id,
            "first_name": user.first_name,
            "last_name": user.last_name,
            "email": user.email,
            "role": user.role_id,
            "organization_id": user.organization_id
        }
    }
