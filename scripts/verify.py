#!/usr/bin/env python
# AI-BOS Project Architecture Verification Tool (Local-First Edition)
# ==============================================================================

import os
import sys
import subprocess
import socket
import re

# Define color codes for console outputs
GREEN = "\033[92m"
RED = "\033[91m"
YELLOW = "\033[93m"
CYAN = "\033[96m"
RESET = "\033[0m"

if sys.platform == 'win32':
    os.system('color')

def log_section(title):
    print(f"\n{CYAN}=== {title} ==={RESET}")

def log_success(message):
    print(f"  {GREEN}[PASS]{RESET} {message}")

def log_error(message):
    print(f"  {RED}[FAIL]{RESET} {message}")

def log_warning(message):
    print(f"  {YELLOW}[WARN]{RESET} {message}")

# Required folders for Local-First Architecture
REQUIRED_DIRECTORIES = [
    "agents",
    "assets",
    "backend",
    "config",
    "database",
    "documentation",
    "frontend",
    "integrations",
    "mobile",
    "scripts",
    "shared",
    "testing",
    
    # Backend structures
    "backend/app/api",
    "backend/app/core",
    "backend/app/config",
    "backend/app/database",
    "backend/app/models",
    "backend/app/schemas",
    "backend/app/services",
    "backend/app/repositories",
    "backend/app/middleware",
    "backend/app/security",
    "backend/app/utils",
    "backend/tests",
    
    # Frontend structures
    "frontend/src/components",
    "frontend/src/layouts",
    "frontend/src/hooks",
    "frontend/src/services",
    "frontend/src/styles",
    "frontend/src/utils",
    "frontend/src/types",
    "frontend/src/contexts",
    "frontend/src/providers",
    
    # Mobile structures
    "mobile/src/navigation",
    "mobile/src/theme",
    "mobile/src/screens",
    "mobile/src/services"
]

# Required files for Local-First Architecture
REQUIRED_FILES = [
    # Root configs
    "package.json",
    "README.md",
    ".gitignore",
    ".env.example",
    "LICENSE",
    ".editorconfig",
    ".prettierrc",
    ".eslintrc.json",
    ".vscode/settings.json",
    
    # Root setup scripts
    "setup.ps1",
    "setup.bat",
    "setup.sh",
    
    # Backend files
    "backend/requirements.txt",
    "backend/pyproject.toml",
    "backend/.env.example",
    "backend/app/main.py",
    "backend/app/core/config.py",
    "backend/app/core/database.py",
    "backend/app/core/security.py",
    "backend/app/api/v1/endpoints/health.py",
    "backend/app/api/v1/endpoints/system.py",
    "backend/app/api/v1/endpoints/auth.py",
    
    # Backend __init__.py markers
    "backend/app/api/__init__.py",
    "backend/app/core/__init__.py",
    "backend/app/config/__init__.py",
    "backend/app/database/__init__.py",
    "backend/app/models/__init__.py",
    "backend/app/models/auth.py",
    "backend/app/schemas/__init__.py",
    "backend/app/schemas/auth.py",
    "backend/app/services/__init__.py",
    "backend/app/repositories/__init__.py",
    "backend/app/middleware/__init__.py",
    "backend/app/security/__init__.py",
    "backend/app/utils/__init__.py",
    "backend/tests/__init__.py",
    
    # Frontend files
    "frontend/package.json",
    "frontend/tsconfig.json",
    "frontend/next.config.js",
    "frontend/.env.example",
    "frontend/src/styles/variables.css",
    "frontend/src/styles/globals.css",
    "frontend/src/styles/dashboard.css",
    "frontend/src/app/layout.tsx",
    "frontend/src/app/page.tsx",
    "frontend/src/app/auth/login/page.tsx",
    "frontend/src/app/auth/forgot-password/page.tsx",
    "frontend/src/app/auth/reset-password/page.tsx",
    "frontend/src/app/auth/unauthorized/page.tsx",
    "frontend/src/app/auth/session-expired/page.tsx",
    "frontend/src/app/profile/page.tsx",
    "frontend/src/app/profile/change-password/page.tsx",
    "frontend/src/services/systemService.ts",
    "frontend/src/services/authService.ts",
    
    # Mobile files
    "mobile/package.json",
    "mobile/tsconfig.json",
    "mobile/.env.example",
    "mobile/src/theme/tokens.ts",
    "mobile/App.tsx",
    
    # Agents files
    "agents/requirements.txt",
    "agents/graph/state.py",
    "agents/graph/workflow.py",
    
    # Database initialization files
    "database/postgres/init.sql",
    "database/mongodb/init-mongo.js",
    "database/redis/redis.conf",
    "database/vector_db/qdrant_collections.json",
    
    # Documentation files
    "documentation/ARCHITECTURE.md",
    "documentation/CODING_STANDARDS.md",
    "documentation/CONTRIBUTION.md",
    "documentation/PROJECT_RULES.md",
    "documentation/SECURITY.md",
    "documentation/MASTER_BLUEPRINT.md",
    "documentation/MODULE_REGISTRY.md",
    "documentation/PHASE_REGISTRY.md",
    "documentation/DEPENDENCY_MAP.md",
    "documentation/SERVICE_MAP.md",
    "documentation/DATA_FLOW_MAP.md",
    "documentation/FOLDER_RESPONSIBILITY_MAP.md",
    
    # Utility scripts
    "scripts/verify.py",
    "scripts/doctor.py",
    "scripts/health.py",
    "scripts/reset.ps1",
    "scripts/reset.sh",
    "scripts/test_dashboard_integration.py",
    "scripts/test_auth_integration.py"
]

def load_env(path):
    env_data = {}
    if os.path.isfile(path):
        with open(path, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith('#'):
                    continue
                if '=' in line:
                    k, v = line.split('=', 1)
                    env_data[k.strip()] = v.strip().strip('"').strip("'")
    return env_data

def verify_port(host, port):
    try:
        with socket.create_connection((host, port), timeout=1.0):
            return True
    except Exception:
        return False

def check_version(command, pattern):
    try:
        use_shell = os.name == 'nt'
        res = subprocess.run(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, shell=use_shell)
        output = res.stdout.strip() or res.stderr.strip()
        match = re.search(pattern, output)
        if match:
            return match.group(0)
        return output.split('\n')[0] if output else None
    except Exception:
        return None

def main():
    root_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
    print(f"\n{CYAN}=========================================================={RESET}")
    print(f"{CYAN}   AI-BOS Local-First Architecture Integrity Check        {RESET}")
    print(f"{CYAN}=========================================================={RESET}")
    print(f"Target Root: {root_dir}")
    
    failures = 0
    
    # 1. Check CLI Tools Versions
    log_section("Checking Prerequisite CLI Tools")
    
    # Python Version
    python_ver = f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}"
    if sys.version_info >= (3, 10):
        log_success(f"Python version: {python_ver} (>= 3.10)")
    else:
        log_error(f"Python version: {python_ver} is too old (Requires >= 3.10)")
        failures += 1
        
    # Node.js Version
    node_ver = check_version(["node", "--version"], r"v\d+\.\d+\.\d+")
    if node_ver:
        major = int(node_ver.strip('v').split('.')[0])
        if major >= 18:
            log_success(f"Node.js version: {node_ver} (>= v18)")
        else:
            log_error(f"Node.js version: {node_ver} is too old (Requires >= v18)")
            failures += 1
    else:
        log_error("Node.js: Not installed or not in PATH (Requires >= v18)")
        failures += 1
        
    # npm Version
    npm_ver = check_version(["npm", "--version"], r"\d+\.\d+\.\d+")
    if npm_ver:
        log_success(f"npm version: v{npm_ver}")
    else:
        log_error("npm: Not installed or not in PATH")
        failures += 1

    # Git Version
    git_ver = check_version(["git", "--version"], r"\d+\.\d+\.\d+")
    if git_ver:
        log_success(f"Git version: v{git_ver}")
    else:
        log_error("Git: Not installed or not in PATH")
        failures += 1

    # 2. Check Virtual Environment
    log_section("Checking Python Virtual Environment")
    venv_dir = os.path.join(root_dir, "backend", "venv")
    if os.path.isdir(venv_dir):
        log_success("Backend virtual environment (venv) folder exists.")
        
        # Check active packages path resolving
        if sys.platform == "win32":
            site_packages = os.path.join(venv_dir, "Lib", "site-packages")
        else:
            site_packages = os.path.join(venv_dir, "lib", f"python{sys.version_info.major}.{sys.version_info.minor}", "site-packages")
            
        if os.path.isdir(site_packages):
            log_success(f"Virtual environment dependencies folder verified: {site_packages}")
        else:
            log_warning("Virtual environment site-packages folder missing. Run setup script.")
    else:
        log_error("Backend virtual environment (venv) folder is missing.")
        failures += 1

    # 3. Check Directory Structure
    log_section("Checking Directory Structure")
    for directory in REQUIRED_DIRECTORIES:
        dir_path = os.path.join(root_dir, directory)
        if os.path.isdir(dir_path):
            log_success(f"Directory verified: {directory}/")
        else:
            log_error(f"Directory missing: {directory}/")
            failures += 1
            
    # 4. Check Core Files
    log_section("Checking Core Configuration & Code Files")
    for file_rel_path in REQUIRED_FILES:
        file_path = os.path.join(root_dir, file_rel_path)
        if os.path.isfile(file_path):
            log_success(f"File verified: {file_rel_path}")
        else:
            log_error(f"File missing: {file_rel_path}")
            failures += 1

    # 5. Check Environment Files
    log_section("Checking Environment Files")
    env_files = [".env", "backend/.env", "frontend/.env", "mobile/.env"]
    for env_file in env_files:
        path = os.path.join(root_dir, env_file)
        if os.path.isfile(path):
            log_success(f"Active environment file verified: {env_file}")
        else:
            log_warning(f"Active environment file missing: {env_file} (Run setup to generate it from example)")
            # Do not increment failures for missing active .env as setup will generate them

    # 6. Check Database Connectivity
    log_section("Checking Local Database Services Connectivity")
    
    # Load backend configurations if present
    backend_env = load_env(os.path.join(root_dir, "backend", ".env"))
    
    # PostgreSQL Check
    pg_host = backend_env.get("POSTGRES_SERVER", "localhost")
    pg_port = int(backend_env.get("POSTGRES_PORT", 5432))
    if verify_port(pg_host, pg_port):
        log_success(f"PostgreSQL connection verified on {pg_host}:{pg_port}.")
    else:
        log_error(f"PostgreSQL unreachable on {pg_host}:{pg_port}. Ensure PostgreSQL service is running.")
        failures += 1
        
    # MongoDB Check
    # Extract host/port from MONGODB_URL: mongodb://user:pass@host:port/db
    mongo_url = backend_env.get("MONGODB_URL", "")
    mongo_host = "localhost"
    mongo_port = 27017
    if mongo_url:
        match = re.search(r"@([^:/]+):?(\d+)?", mongo_url)
        if match:
            mongo_host = match.group(1)
            if match.group(2):
                mongo_port = int(match.group(2))
    if verify_port(mongo_host, mongo_port):
        log_success(f"MongoDB connection verified on {mongo_host}:{mongo_port}.")
    else:
        log_error(f"MongoDB unreachable on {mongo_host}:{mongo_port}. Ensure MongoDB service is running.")
        failures += 1
        
    # Redis Check
    redis_host = backend_env.get("REDIS_HOST", "localhost")
    redis_port = int(backend_env.get("REDIS_PORT", 6379))
    if verify_port(redis_host, redis_port):
        log_success(f"Redis connection verified on {redis_host}:{redis_port}.")
    else:
        log_error(f"Redis unreachable on {redis_host}:{redis_port}. Ensure Redis service is running.")
        failures += 1

    # 7. Check Config Integrations Loading
    log_section("Validating Backend Config Classes")
    try:
        # Dynamically append backend and venv site-packages to path to test config parsing
        sys.path.append(os.path.join(root_dir, "backend"))
        if sys.platform == "win32":
            sys.path.append(os.path.join(venv_dir, "Lib", "site-packages"))
        else:
            sys.path.append(os.path.join(venv_dir, "lib", f"python{sys.version_info.major}.{sys.version_info.minor}", "site-packages"))
            
        # Mock environment variables to verify config parsing
        os.environ.setdefault("SECRET_KEY", "verification_mock_key")
        os.environ.setdefault("POSTGRES_SERVER", "localhost")
        os.environ.setdefault("POSTGRES_USER", "postgres")
        os.environ.setdefault("POSTGRES_PASSWORD", "postgres")
        os.environ.setdefault("POSTGRES_DB", "postgres")
        os.environ.setdefault("MONGODB_URL", "mongodb://localhost:27017")
        os.environ.setdefault("REDIS_HOST", "localhost")
        os.environ.setdefault("QDRANT_HOST", "localhost")
        
        from app.core.config import settings
        log_success(f"Backend settings parsed successfully. Project Name: {settings.PROJECT_NAME}")
    except Exception as e:
        log_warning(f"Could not load backend Pydantic settings schema: {e}")

    # 8. Check for Docker Artifacts (Local-First mandate: zero Docker files/folders)
    log_section("Checking for Unauthorized Docker Artifacts")
    docker_artifacts = []
    for root, dirs, files in os.walk(root_dir):
        # Exclude node_modules, venv, and git/ide metadata
        if any(ignored in root for ignored in ["node_modules", "venv", ".git", ".gemini"]):
            continue
        
        # Check directories
        for d in dirs:
            if "docker" in d.lower():
                docker_artifacts.append(os.path.join(root, d))
                
        # Check files
        for f in files:
            if "docker" in f.lower() or "dockerfile" in f.lower() or "docker-compose" in f.lower():
                docker_artifacts.append(os.path.join(root, f))
                
    if not docker_artifacts:
        log_success("Zero Docker files or folders detected in the repository.")
    else:
        for artifact in docker_artifacts:
            rel_path = os.path.relpath(artifact, root_dir)
            log_error(f"Unauthorized Docker artifact found: {rel_path}")
            failures += 1

    # Conclusion
    print(f"\n{CYAN}=========================================================={RESET}")
    if failures == 0:
        print(f"{GREEN}   VERIFICATION SUCCESS: System foundation complies with Local-First. {RESET}")
        print(f"{CYAN}=========================================================={RESET}\n")
        sys.exit(0)
    else:
        print(f"{RED}   VERIFICATION FAILURE: {failures} issues detected. Check diagnostics above. {RESET}")
        print(f"{CYAN}=========================================================={RESET}\n")
        sys.exit(1)

if __name__ == "__main__":
    main()
