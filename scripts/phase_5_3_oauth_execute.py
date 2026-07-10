import os
import re

BACKEND_DIR = "d:/react-website/aibios/backend/app"
meta_int_path = os.path.join(BACKEND_DIR, "api", "v1", "endpoints", "meta_integration.py")

with open(meta_int_path, "r", encoding="utf-8") as f:
    code = f.read()

# 1. Import OAuthSession
if "OAuthSession" not in code:
    code = code.replace("from app.models.enterprise_integrations import MetaPage, MetaLeadForm", "from app.models.enterprise_integrations import MetaPage, MetaLeadForm, OAuthSession")
    # If the above fails because the import is split or different:
    if "OAuthSession" not in code:
        code = code.replace("from app.models.enterprise_integrations import", "from app.models.enterprise_integrations import OAuthSession,")

# 2. Rewrite get_meta_oauth_url
url_old = """@router.get("/oauth/url", response_model=Dict[str, Any])
async def get_meta_oauth_url(current_user: User = Depends(require_meta_write)):
    \"\"\"Returns a real Meta OAuth dialog URL with business-integration scopes
    (pages_show_list, leads_retrieval, business_management, instagram_basic, ...).\"\"\"
    try:
        state = secrets.token_urlsafe(24)
        url = meta_service.build_oauth_url(state)
        return {"url": url, "state": state}
    except MetaNotConfiguredError as e:
        raise HTTPException(status_code=503, detail=str(e))"""

url_new = """@router.get("/oauth/url", response_model=Dict[str, Any])
async def get_meta_oauth_url(current_user: User = Depends(require_meta_write), db: AsyncSession = Depends(get_db)):
    \"\"\"Returns a real Meta OAuth dialog URL with business-integration scopes.\"\"\"
    try:
        state = secrets.token_urlsafe(24)
        url = meta_service.build_oauth_url(state)
        
        session = OAuthSession(
            organization_id=current_user.organization_id,
            user_id=current_user.id,
            state=state,
            provider="facebook"
        )
        db.add(session)
        await db.commit()
        
        return {"url": url, "state": state}
    except MetaNotConfiguredError as e:
        raise HTTPException(status_code=503, detail=str(e))"""

code = code.replace(url_old, url_new)

# 3. Rewrite meta_oauth_callback to verify state
callback_old = """async def meta_oauth_callback(
    body: OAuthCallbackBody,
    current_user: User = Depends(require_meta_write),
    db: AsyncSession = Depends(get_db),
):
    \"\"\"Exchanges the OAuth code for a real long-lived user access token and stores it
    (encrypted) for this organization. This is the real replacement for the previous
    fake `secrets.token_hex(8)` external_account_id.\"\"\"
    try:"""

callback_new = """async def meta_oauth_callback(
    body: OAuthCallbackBody,
    current_user: User = Depends(require_meta_write),
    db: AsyncSession = Depends(get_db),
):
    \"\"\"Exchanges the OAuth code for a real long-lived user access token.\"\"\"
    
    if body.state:
        res = await db.execute(select(OAuthSession).where(OAuthSession.state == body.state))
        session_row = res.scalar_one_or_none()
        if not session_row:
            raise HTTPException(status_code=400, detail="Invalid or expired OAuth state")
        if session_row.organization_id != current_user.organization_id:
            raise HTTPException(status_code=403, detail="State organization mismatch")
        await db.delete(session_row)
        await db.commit()

    try:"""

code = code.replace(callback_old, callback_new)

with open(meta_int_path, "w", encoding="utf-8") as f:
    f.write(code)

print("OAuth updated")
