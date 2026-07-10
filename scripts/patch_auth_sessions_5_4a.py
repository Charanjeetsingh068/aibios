import os

auth_api_file = "backend/app/api/v1/endpoints/auth.py"
auth_schema_file = "backend/app/schemas/auth.py"

# --- Patch Schemas ---
with open(auth_schema_file, "r", encoding="utf-8") as f:
    schema_content = f.read()

session_schema = """
class SessionResponse(BaseModel):
    id: str
    device_info: Optional[str] = None
    ip_address: Optional[str] = None
    is_active: bool
    created_at: datetime
    last_activity: Optional[datetime] = None

    class Config:
        from_attributes = True
"""

if "class SessionResponse" not in schema_content:
    schema_content += "\n" + session_schema
    with open(auth_schema_file, "w", encoding="utf-8") as f:
        f.write(schema_content)
    print("Patched auth schemas")


# --- Patch API ---
with open(auth_api_file, "r", encoding="utf-8") as f:
    api_content = f.read()

sessions_api = """
from app.schemas.auth import SessionResponse
from typing import List

@router.get("/sessions", response_model=List[SessionResponse])
async def list_sessions(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    result = await db.execute(
        select(UserSession)
        .where(UserSession.user_id == current_user.id)
        .order_by(UserSession.created_at.desc())
        .limit(20)
    )
    return result.scalars().all()

@router.post("/logout-all-devices")
async def logout_all_devices(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    query = select(UserSession).where(UserSession.user_id == current_user.id, UserSession.is_active == True)
    result = await db.execute(query)
    sessions = result.scalars().all()
    for s in sessions:
        s.is_active = False
        
        # Revoke refresh tokens
        rt_query = select(RefreshToken).where(RefreshToken.session_id == s.id)
        rt_result = await db.execute(rt_query)
        for rt in rt_result.scalars():
            rt.is_revoked = True
            
    audit = AuditLog(
        user_id=current_user.id,
        organization_id=current_user.organization_id,
        action="logout_all_devices",
        description="User logged out of all devices",
        resource="users",
        resource_id=current_user.id
    )
    db.add(audit)
    
    await db.commit()
    return {"message": "Successfully logged out of all devices"}
"""

if "logout_all_devices" not in api_content:
    api_content += "\n" + sessions_api
    with open(auth_api_file, "w", encoding="utf-8") as f:
        f.write(api_content)
    print("Patched auth API")
