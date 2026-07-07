#!/usr/bin/env bash
# AI-BOS Enterprise Local Setup Script (Unix Bash)
# ==============================================================================

set -euo pipefail

# Console Colors
GREEN="\033[0;32m"
RED="\033[0;31m"
YELLOW="\033[0;33m"
CYAN="\033[0;36m"
GRAY="\033[0;90m"
RESET="\033[0m"

log_header() {
    echo -e "\n${CYAN}=== $1 ===${RESET}"
}

log_success() {
    echo -e "  ${GREEN}[PASS]${RESET} $1"
}

log_warning() {
    echo -e "  ${YELLOW}[WARN]${RESET} $1"
}

log_failure() {
    echo -e "  ${RED}[FAIL]${RESET} $1"
}

echo -e "${CYAN}==========================================================${RESET}"
echo -e "${CYAN}   AI-BOS Enterprise Local Setup & Environment Builder    ${RESET}"
echo -e "${CYAN}==========================================================${RESET}"

# ------------------------------------------------------------------------------
# 1. Verify Basic CLI Tools
# ------------------------------------------------------------------------------
log_header "Verifying CLI Tool Prerequisites"

# Resolve python command
if command -v python3 &>/dev/null; then
    PYTHON_CMD="python3"
elif command -v python &>/dev/null; then
    PYTHON_CMD="python"
else
    log_failure "Python is not installed. Please install Python 3.10+ before executing."
    exit 1
fi

# Verify Python version >= 3.10
PYTHON_VERSION=$($PYTHON_CMD -c 'import sys; print(f"{sys.version_info.major}.{sys.version_info.minor}")')
MAJOR=$(echo "$PYTHON_VERSION" | cut -d'.' -f1)
MINOR=$(echo "$PYTHON_VERSION" | cut -d'.' -f2)

if [ "$MAJOR" -lt 3 ] || { [ "$MAJOR" -eq 3 ] && [ "$MINOR" -lt 10 ]; }; then
    log_failure "Python version must be >= 3.10. Found: $($PYTHON_CMD --version)"
    exit 1
fi
log_success "Python installation: $($PYTHON_CMD --version)"

# Verify Node.js
if command -v node &>/dev/null; then
    NODE_VERSION=$(node -v)
    NODE_MAJOR=$(echo "$NODE_VERSION" | tr -d 'v' | cut -d'.' -f1)
    if [ "$NODE_MAJOR" -lt 18 ]; then
        log_failure "Node.js version must be >= 18.0.0. Found: $NODE_VERSION"
        exit 1
    fi
    log_success "Node.js installation: $NODE_VERSION"
else
    log_failure "Node.js is not installed. Please install Node.js >= 18.0.0."
    exit 1
fi

# Verify npm
if command -v npm &>/dev/null; then
    log_success "npm installation: v$(npm --version)"
else
    log_failure "npm is not installed."
    exit 1
fi

# ------------------------------------------------------------------------------
# 2. Setup Configuration Files (.env)
# ------------------------------------------------------------------------------
log_header "Generating Environment Configurations"

declare -A env_files
env_files[".env"]=".env.example"
env_files["backend/.env"]="backend/.env.example"
env_files["frontend/.env"]="frontend/.env.example"
env_files["mobile/.env"]="mobile/.env.example"

for key in "${!env_files[@]}"; do
    if [ ! -f "$key" ]; then
        if [ -f "${env_files[$key]}" ]; then
            cp "${env_files[$key]}" "$key"
            log_success "Created configuration file: $key"
        else
            log_warning "Configuration template missing: ${env_files[$key]}"
        fi
    else
        echo -e "  ${GRAY}[SKIP]${RESET} Configuration file already exists: $key"
    fi
done

# ------------------------------------------------------------------------------
# 3. Setup Python Virtual Environment and Backend Dependencies
# ------------------------------------------------------------------------------
log_header "Setting Up Python Virtual Environment (Backend)"

VENV_DIR="./backend/venv"
if [ ! -d "$VENV_DIR" ]; then
    echo -e "Creating Virtual Environment at $VENV_DIR..."
    $PYTHON_CMD -m venv "$VENV_DIR"
    log_success "Created python virtual environment."
else
    echo -e "  ${GRAY}[SKIP]${RESET} Virtual environment already exists at $VENV_DIR"
fi

echo -e "Installing/Upgrading dependencies inside virtual environment..."
source "$VENV_DIR/bin/activate"
pip install --upgrade pip
pip install -r ./backend/requirements.txt
log_success "Backend dependencies installed successfully."

# ------------------------------------------------------------------------------
# 4. Setup Node.js Dependencies (Frontend & Mobile)
# ------------------------------------------------------------------------------
log_header "Installing Node.js Package Dependencies"

# Frontend dependencies
if [ -d "./frontend" ]; then
    echo -e "Installing frontend console packages (Next.js)..."
    cd ./frontend
    npm install
    cd ..
    log_success "Frontend console packages installed."
fi

# Mobile dependencies
if [ -d "./mobile" ]; then
    echo -e "Installing mobile companion packages (React Native)..."
    cd ./mobile
    npm install
    cd ..
    log_success "Mobile companion packages installed."
fi

# ------------------------------------------------------------------------------
# 5. Verify Local Database Dependencies Connectivity
# ------------------------------------------------------------------------------
log_header "Verifying Database Connection Ports (Local)"

test_port() {
    local db_name=$1
    local port=$2
    
    # We use a quick python network socket call to verify connection status
    if $PYTHON_CMD -c "import socket; s = socket.socket(); s.settimeout(1.5); s.connect(('127.0.0.1', $port))" &>/dev/null; then
        log_success "$db_name is online and listening on port $port."
        return 0
    else
        log_failure "$db_name is unreachable on port $port."
        return 1
    fi
}

db_failures=0
test_port "PostgreSQL" 5432 || db_failures=$((db_failures+1))
test_port "MongoDB" 27017 || db_failures=$((db_failures+1))
test_port "Redis" 6379 || db_failures=$((db_failures+1))

# ------------------------------------------------------------------------------
# Success / Status Report
# ------------------------------------------------------------------------------
echo -e "\n${CYAN}==========================================================${RESET}"
if [ "$db_failures" -eq 0 ]; then
    echo -e "   ${GREEN}AI-BOS Setup Successful! All components are ready.${RESET}"
else
    echo -e "   ${YELLOW}AI-BOS Setup Incomplete: $db_failures database service(s) offline.${RESET}"
    echo -e "   Please ensure PostgreSQL (5432), MongoDB (27017), and Redis (6379)"
    echo -e "   are running locally on your system."
fi
echo -e "   To run verification check, execute: npm run verify"
echo -e "${CYAN}==========================================================${RESET}"
