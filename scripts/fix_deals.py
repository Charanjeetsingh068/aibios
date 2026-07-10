import os

filepath = r"d:\react-website\aibios\backend\app\models\business.py"
with open(filepath, "rb") as f:
    content_bytes = f.read()

# Replace any byte sequence of U+0002 or whatever is wrong.
# Let's decode as utf-8, replace, and write back.
content_str = content_bytes.decode("utf-8")

# Let's inspect the U+0002 characters and replace them.
# The error was: E   SyntaxError: invalid non-printable character U+0002
# at line 59: E     File "D:\react-website\aibios\backend\app\models\business.py", line 59
# E        (Base, TenantResourceMixin):

print("Number of U+0002 in content:", content_str.count("\x02"))
content_str = content_str.replace("\x02", "")
content_str = content_str.replace(" (Base, TenantResourceMixin):", "class Deal(Base, TenantResourceMixin):")

with open(filepath, "w", encoding="utf-8") as f:
    f.write(content_str)

print("Successfully fixed business.py")
