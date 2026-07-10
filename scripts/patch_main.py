import os

file_path = "backend/app/main.py"
with open(file_path, "r", encoding="utf-8") as f:
    content = f.read()

# Add import
import_statement = "from app.api.v1.endpoints import pipelines"
if import_statement not in content:
    content = content.replace(
        "from app.api.v1.endpoints import (",
        "from app.api.v1.endpoints import (\n    pipelines,"
    )

# Add route
router_registration = 'fastapi_app.include_router(pipelines.router, prefix=settings.API_V1_STR + "/pipelines", tags=["Pipelines"])'
if router_registration not in content:
    content = content.replace(
        'fastapi_app.include_router(leads.router, prefix=settings.API_V1_STR + "/leads", tags=["Leads"])',
        'fastapi_app.include_router(leads.router, prefix=settings.API_V1_STR + "/leads", tags=["Leads"])\n    fastapi_app.include_router(pipelines.router, prefix=settings.API_V1_STR + "/pipelines", tags=["Pipelines"])'
    )

with open(file_path, "w", encoding="utf-8") as f:
    f.write(content)
print("main.py patched")
