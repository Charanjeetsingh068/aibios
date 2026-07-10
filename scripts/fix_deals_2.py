import os

filepath = r"d:\react-website\aibios\backend\app\models\business.py"
with open(filepath, "r", encoding="utf-8") as f:
    content = f.read()

# Replace "(Base, TenantResourceMixin):\n\n    __tablename__ = \"deals\""
# with "class Deal(Base, TenantResourceMixin):\n\n    __tablename__ = \"deals\""
content = content.replace("(Base, TenantResourceMixin):\n\n    __tablename__ = \"deals\"", "class Deal(Base, TenantResourceMixin):\n\n    __tablename__ = \"deals\"")

with open(filepath, "w", encoding="utf-8") as f:
    f.write(content)

print("Successfully fixed class Deal in business.py")
