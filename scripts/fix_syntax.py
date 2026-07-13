import os

filepath = "c:/react/aibios/scripts/phase_5_3_execute.py"
with open(filepath, "r", encoding="utf-8") as f:
    content = f.read()

content = content.replace('if "@fastapi_app.on_event(\\"startup\\")" in main_code:', 'if \'@fastapi_app.on_event("startup")\' in main_code:')

with open(filepath, "w", encoding="utf-8") as f:
    f.write(content)

print("Fixed syntax")
