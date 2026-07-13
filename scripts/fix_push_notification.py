import os

filepath = "c:/react/aibios/frontend/src/app/page.tsx"
with open(filepath, "r", encoding="utf-8") as f:
    content = f.read()

content = content.replace(', "error")', ')')

with open(filepath, "w", encoding="utf-8") as f:
    f.write(content)

print("Fixed pushNotification usages")
