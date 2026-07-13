import os

filepath = "c:/react/aibios/frontend/src/services/integrationsService.ts"
with open(filepath, "r", encoding="utf-8") as f:
    content = f.read()

content = content.replace("delete(/api/v1/integrations/meta/sync/mappings/);", "delete(`/api/v1/integrations/meta/sync/mappings/${mappingId}`);")

with open(filepath, "w", encoding="utf-8") as f:
    f.write(content)

print("Fixed deleteLeadMapping")
