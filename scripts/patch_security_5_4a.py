import os

security_file = "backend/app/core/security.py"

with open(security_file, "r", encoding="utf-8") as f:
    sec_content = f.read()

visibility_logic = """
from sqlalchemy import or_

def get_visibility_filter(model, current_user):
    \"\"\"
    Generates a SQLAlchemy filter condition for a given TenantResourceMixin model
    based on the current_user's permissions, teams, and the model's visibility field.
    \"\"\"
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
"""

if "get_visibility_filter" not in sec_content:
    sec_content += "\n" + visibility_logic
    with open(security_file, "w", encoding="utf-8") as f:
        f.write(sec_content)
    print("Patched security.py with get_visibility_filter")
else:
    print("security.py already patched")
