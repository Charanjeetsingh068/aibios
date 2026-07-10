import os

filepath = "d:/react-website/aibios/frontend/src/app/page.tsx"
with open(filepath, "r", encoding="utf-8") as f:
    content = f.read()

content = content.replace('Key,', '')

with open(filepath, "w", encoding="utf-8") as f:
    f.write(content)

print("Fixed unused import")
