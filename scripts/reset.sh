#!/usr/bin/env bash
# AI-BOS Complete Reset Script (Unix Bash)
# ==============================================================================

set -euo pipefail

# Console Colors
RED="\033[0;31m"
YELLOW="\033[0;33m"
GREEN="\033[0;32m"
RESET="\033[0m"

echo -e "${RED}==========================================================${RESET}"
echo -e "${RED}   Resetting AI-BOS Enterprise Workspace...              ${RESET}"
echo -e "${RED}==========================================================${RESET}"

# 1. Delete Dependencies & Builds
echo -e "\n${YELLOW}[1/2] Cleaning package and environment folders...${RESET}"
rm -rf ./backend/.venv
rm -rf ./node_modules
rm -rf ./frontend/node_modules
rm -rf ./frontend/.next
rm -rf ./mobile/node_modules
echo -e "${GREEN}Clean completed successfully.${RESET}"

# 2. Rerun Setup
echo -e "\n${YELLOW}[2/2] Re-executing system setup.sh...${RESET}"
bash ./setup.sh
