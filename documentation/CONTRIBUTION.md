# Developer Contribution Guidelines — AI-BOS Enterprise

This document guides developers through setting up their environment, creating branches, executing validation checks, and submitting pull requests.

---

## 1. Local Development Setup

To initialize the multi-repo workspace structure locally:

### 1. Verification of Prerequisites
Ensure the following utilities and services are installed:
- Node.js (version 18 or newer)
- Python (version 3.10 or newer)
- PostgreSQL Server (running on local port 5432)
- MongoDB Server (running on local port 27017)
- Redis Server (running on local port 6379)

### 2. Auto-installation of Dependencies
```bash
# On Windows PowerShell
npm run setup

# On Linux/macOS Bash
npm run setup:bash
```

### 3. Verify Layout and Configs
```bash
npm run verify
```

---

## 2. Git Branching Conventions

Ensure your commit history and branch creations follow these strict formats:

- **Feature additions:** `feature/AB-[ticket-number]-[short-description]` (e.g. `feature/AB-102-postgres-migration`)
- **Defect resolution:** `bugfix/AB-[ticket-number]-[short-description]`
- **Hotfix patches:** `hotfix/[short-description]`
- **Documentation edits:** `docs/[short-description]`

---

## 3. Pull Request (PR) Requirements

Before sending a PR to the integration branch:
1. Ensure the code builds cleanly:
   - Next.js compiles: `npm run build` inside `frontend/`
   - Python code passes type validation and linters: run `ruff check .` inside `backend/`
2. Update system documentation files under `documentation/` if your modifications introduce new architectural details or config parameters.
3. Verify that the system verification tool reports success: `npm run verify`.
