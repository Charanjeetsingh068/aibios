import os

files = [
    "backend/app/services/meta_sync_service.py",
    "backend/app/services/meta_token_manager.py",
    "backend/app/api/v1/endpoints/meta_webhooks.py",
    "backend/app/api/v1/endpoints/meta_sync.py"
]

for fpath in files:
    full_path = os.path.join("c:/react/aibios", fpath)
    with open(full_path, "r", encoding="utf-8") as f:
        content = f.read()
    
    content = content.replace('\\"\\"\\"', '"""')
    
    with open(full_path, "w", encoding="utf-8") as f:
        f.write(content)

print("Fixed")
