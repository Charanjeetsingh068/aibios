import re

file_path = "d:/react-website/aibios/backend/app/api/v1/endpoints/users.py"
with open(file_path, "r", encoding="utf-8") as f:
    content = f.read()

new_endpoint = """
class ForcePasswordBody(BaseModel):
    password: str = Field(..., min_length=8)

@router.post("/{user_id}/force-password", response_model=Dict[str, Any])
async def admin_force_password(
    user_id: str,
    body: ForcePasswordBody,
    request: Request,
    current_user: User = Depends(require_users_reset_password),
    db: AsyncSession = Depends(get_db),
):
    user = await db.get(User, user_id)
    if not user or user.deleted_at is not None:
        raise HTTPException(status_code=404, detail="User not found")
    _check_org_scope(current_user, user.organization_id)

    user.password_hash = get_password_hash(body.password)
    user.updated_by = current_user.id
    await record_audit_log(
        db, actor=current_user, organization_id=user.organization_id, action="user.admin_force_password",
        description=f"Password forcibly changed for '{user.email}' by admin", resource="users", resource_id=user.id,
        ip_address=request.client.host if request.client else None,
    )
    await db.commit()
    return {"success": True}

"""

if "admin_force_password" not in content:
    content = content.replace("class RoleAssignmentBody(BaseModel):", new_endpoint + "class RoleAssignmentBody(BaseModel):")
    with open(file_path, "w", encoding="utf-8") as f:
        f.write(content)
    print("Backend users.py patched with force-password endpoint")
else:
    print("Endpoint already exists in users.py")
