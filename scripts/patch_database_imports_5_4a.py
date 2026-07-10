import os

database_file = "backend/app/core/database.py"

with open(database_file, "r", encoding="utf-8") as f:
    content = f.read()

# We need to make sure all models are imported before create_all
imports = """
import app.models.auth
import app.models.business
import app.models.integrations
import app.models.enterprise_integrations
"""

if "import app.models.business" not in content:
    content = content.replace("from app.models.auth import Base", imports + "\nfrom app.models.auth import Base")
    with open(database_file, "w", encoding="utf-8") as f:
        f.write(content)
    print("Patched database.py to import all models before create_all")
else:
    print("Already patched")
