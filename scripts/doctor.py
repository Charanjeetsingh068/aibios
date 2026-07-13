#!/usr/bin/env python
# AI-BOS Environmental Doctor & Diagnostics Tool (Local-First Edition)
# ==============================================================================

import os
import sys
import subprocess
import socket

# Setup Console Color Codes
GREEN = "\033[92m"
RED = "\033[91m"
YELLOW = "\033[93m"
CYAN = "\033[96m"
RESET = "\033[0m"

if sys.platform == 'win32':
    os.system('color')

def log_section(title):
    print(f"\n{CYAN}=== {title} ==={RESET}")

def log_pass(message):
    print(f"  {GREEN}[OK]{RESET} {message}")

def log_fail(message, recommendation=None):
    print(f"  {RED}[ERROR]{RESET} {message}")
    if recommendation:
        print(f"    {YELLOW}Recommendation:{RESET} {recommendation}")

def log_warning(message, recommendation=None):
    print(f"  {YELLOW}[WARN]{RESET} {message}")
    if recommendation:
        print(f"    {YELLOW}Recommendation:{RESET} {recommendation}")

def check_command(args):
    try:
        use_shell = os.name == 'nt'
        cmd = " ".join(args) if use_shell else args
        result = subprocess.run(
            cmd, 
            stdout=subprocess.PIPE, 
            stderr=subprocess.PIPE, 
            text=True, 
            check=True, 
            shell=use_shell
        )
        version_str = result.stdout.strip().split('\n')[0]
        return version_str if version_str else "Installed"
    except Exception:
        return None

def check_port_in_use(port):
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.settimeout(0.5)
        try:
            s.bind(("127.0.0.1", port))
            return False # Port is free
        except socket.error:
            return True # Port is in use

def main():
    print(f"\n{CYAN}=========================================================={RESET}")
    print(f"{CYAN}   AI-BOS Workspace Diagnostic Doctor (Local-First)       {RESET}")
    print(f"{CYAN}=========================================================={RESET}")

    # 1. Check Tool Dependencies
    log_section("Checking Prerequisite Tools")
    
    tools = [
        {"name": "Python 3", "cmd": ["python", "--version"]},
        {"name": "Node.js", "cmd": ["node", "--version"]},
        {"name": "npm", "cmd": ["npm", "--version"]},
        {"name": "Git", "cmd": ["git", "--version"]}
    ]
    
    doctor_issues = 0
    
    for tool in tools:
        v = check_command(tool["cmd"])
        if v:
            log_pass(f"{tool['name']}: {v}")
        else:
            log_fail(f"{tool['name']} not found in path.", 
                     f"Ensure {tool['name']} is installed and added to your environmental PATH variables.")
            doctor_issues += 1

    # 2. Check Database Service Status
    log_section("Checking Database Services Status (Should be running)")
    
    db_ports = [
        {"port": 5432, "service": "PostgreSQL Relational DB Server"},
        {"port": 27017, "service": "MongoDB Document DB Server"},
        {"port": 6379, "service": "Redis Broker Cache Server"},
        {"port": 6333, "service": "Qdrant Vector Database Server"}
    ]
    
    for p in db_ports:
        in_use = check_port_in_use(p["port"])
        if in_use:
            log_pass(f"Port {p['port']} is active: {p['service']} is running.")
        else:
            # Qdrant is optional, warn instead of fail
            if p["port"] == 6333:
                log_warning(f"Port {p['port']} is closed: {p['service']} is not running.",
                            "If you use semantic search agent logic, make sure to start Qdrant.")
            else:
                log_fail(f"Port {p['port']} is closed: {p['service']} is offline.", 
                         f"Please start the {p['service']} service locally on your host.")
                doctor_issues += 1

    # 3. Check App Server Conflicts (Should be free)
    log_section("Checking App Server Ports Availability (Should be free)")
    
    app_ports = [
        {"port": 3000, "service": "Next.js Frontend Developer Server"},
        {"port": 8000, "service": "FastAPI Backend REST Server"}
    ]
    
    for p in app_ports:
        in_use = check_port_in_use(p["port"])
        if in_use:
            log_fail(f"Port {p['port']} is in use. Conflict for: {p['service']}.",
                     f"Terminate the process running on port {p['port']} so you can start the application servers.")
            doctor_issues += 1
        else:
            log_pass(f"Port {p['port']} is free: {p['service']} can start.")

    # 4. Check Workspace Files
    log_section("Checking Local Configurations")
    
    root_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
    backend_env = os.path.join(root_dir, "backend", ".env")
    backend_venv = os.path.join(root_dir, "backend", ".venv")
    
    if os.path.isfile(backend_env):
        log_pass("backend/.env configuration file exists")
    else:
        log_fail("backend/.env configuration file is missing", "Run 'npm run setup' to initialize it from example templates")
        doctor_issues += 1
        
    if os.path.isdir(backend_venv):
        log_pass("backend/.venv virtual environment exists")
    else:
        log_fail("backend/.venv virtual environment is missing", "Run 'npm run setup' to compile dependencies and create the virtual environment")
        doctor_issues += 1

    # Conclusion
    print(f"\n{CYAN}=========================================================={RESET}")
    if doctor_issues == 0:
        print(f"{GREEN}   DOCTOR REPORT: Healthy workspace. All diagnostic checks PASS. {RESET}")
        print(f"{CYAN}=========================================================={RESET}\n")
        sys.exit(0)
    else:
        print(f"{RED}   DOCTOR REPORT: {doctor_issues} workspace diagnostic issue(s) detected.   {RESET}")
        print(f"{CYAN}=========================================================={RESET}\n")
        sys.exit(1)

if __name__ == "__main__":
    main()
