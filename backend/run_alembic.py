import os
import subprocess
import sys

try:
    subprocess.run([sys.executable, "-m", "alembic", "revision", "--autogenerate", "-m", "Phase 5.4 Lead Engine"], check=True)
    subprocess.run([sys.executable, "-m", "alembic", "upgrade", "head"], check=True)
except Exception:
    print("Failed via module, trying direct alembic.exe")
    alembic_path = os.path.join(os.path.dirname(sys.executable), "alembic.exe")
    try:
        subprocess.run([alembic_path, "revision", "--autogenerate", "-m", "Phase 5.4 Lead Engine"], check=True)
        subprocess.run([alembic_path, "upgrade", "head"], check=True)
    except Exception as e2:
        print("Failed both:", e2)
