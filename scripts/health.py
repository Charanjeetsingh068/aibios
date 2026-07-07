#!/usr/bin/env python
# AI-BOS Operational System Health Monitor (Local-First Edition)
# ==============================================================================

import json
import urllib.request
import urllib.error
import sys
import os

# Setup Colors
GREEN = "\033[92m"
RED = "\033[91m"
YELLOW = "\033[93m"
CYAN = "\033[96m"
RESET = "\033[0m"

if sys.platform == 'win32':
    os.system('color')

BACKEND_URL = "http://localhost:8000/api/v1/health"

def format_status(status):
    status_clean = status.lower().strip()
    if status_clean in ["online", "healthy", "up"]:
        return f"{GREEN}ONLINE{RESET}"
    elif status_clean in ["degraded", "warning"]:
        return f"{YELLOW}DEGRADED{RESET}"
    else:
        return f"{RED}OFFLINE / ERROR{RESET}"

def query_health_endpoint(url):
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "AI-BOS Health Checker"})
        with urllib.request.urlopen(req, timeout=10.0) as response:
            if response.status == 200:
                data = json.loads(response.read().decode('utf-8'))
                return data
    except Exception:
        return None

def main():
    print(f"\n{CYAN}=========================================================={RESET}")
    print(f"{CYAN}   AI-BOS Enterprise Operational Health Monitor           {RESET}")
    print(f"{CYAN}=========================================================={RESET}")

    # Query local backend directly
    print(f"Connecting to FastAPI backend health API: {BACKEND_URL}...")
    health_data = query_health_endpoint(BACKEND_URL)

    if health_data:
        print(f"\n{GREEN}Success: Connected to operational backend settings.{RESET}")
        print(f"System State: {format_status(health_data.get('status', 'OFFLINE'))}")
        print(f"Environment : {health_data.get('environment', 'unknown')}")
        
        deps = health_data.get("dependencies", {})
        print(f"\nOperational Dependencies:")
        for dep_name, status in deps.items():
            print(f"  - {dep_name.capitalize().replace('_', ' '):<16} : {format_status(status)}")
        
        print(f"\n{CYAN}=========================================================={RESET}\n")
        sys.exit(0)
    else:
        print(f"\n{RED}Error: Cannot connect to AI-BOS backend health services.{RESET}")
        print(f"Troubleshooting checks:")
        print("  1. Verify the FastAPI backend is running: 'npm run dev:backend'")
        print("  2. Verify database services status by executing: 'python scripts/doctor.py'")
        print("  3. Check that your local PostgreSQL, MongoDB, and Redis ports are listening.")
        print(f"\n{CYAN}=========================================================={RESET}\n")
        sys.exit(1)

if __name__ == "__main__":
    main()
