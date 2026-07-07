# AI Business Operating System (AI-BOS) — Enterprise Edition

AI-BOS is a highly modular, scalable, multi-agent AI business operating system foundation designed for local-first enterprise development. It decouples the core API, frontend console, mobile portal, multi-agent pipelines, and database layers, enabling developers to run and test the complete system directly on their local machines.

---

## Technology Stack Overview

- **Backend API Gateway:** Python 3.10+ + FastAPI
- **Frontend Admin Console:** React 18 + Next.js 14 (App Router)
- **Mobile Companion Portal:** React Native + Expo (TypeScript)
- **Cognitive Agents Framework:** LangGraph Multi-Agent Workflows
- **Polyglot Persistence Layer:** 
  - PostgreSQL (ACID Relational transactional storage)
  - MongoDB (Telemetry logs, agent run logs)
  - Redis (Ephemeral token caching, Session state)
  - Qdrant (High-performance vector database memory store - optional for local dev)

---

## Folder Structure

```text
aibios/
├── agents/                   # LangGraph Multi-Agent Architecture
├── assets/                   # Design system tokens, assets
├── backend/                  # FastAPI python web services
├── config/                   # Global configuration templates
├── database/                 # PostgreSQL schemas, Mongo collections, Redis configurations
├── documentation/            # Systems architecture, coding standards, contribution guidelines
├── frontend/                 # React Next.js administration portal
├── integrations/             # Third-party integrations (Slack, Stripe stubs)
├── mobile/                   # React Native Expo configurations
├── scripts/                  # Workspace utility scripts (verify, doctor, health, reset)
├── shared/                   # Shared type definitions and constants
└── testing/                  # System tests (E2E playbooks)
```

---

## Installation

The AI-BOS system is fully set up for direct local development.

### Prerequisites

Ensure the following programs are installed and running locally on your computer:
1. **Node.js** >= 18.0.0
2. **Python** >= 3.10
3. **PostgreSQL** (Active on port `5432`)
4. **MongoDB** (Active on port `27017`)
5. **Redis** (Active on port `6379`)

### Automated Setup

To create the virtual environments, install all workspace packages, generate the default environment files, and verify configuration settings:

#### On Windows (PowerShell):
```powershell
npm run setup
```

#### On Windows (Batch Command Line):
```cmd
setup.bat
```

#### On Linux / macOS (Bash):
```bash
npm run setup:bash
```

---

## Local Development

Once the setup completes, run the services locally in separate terminal windows.

### Starting Backend

Execute the FastAPI developer server:
```bash
npm run dev:backend
```
The API server will launch at:
- **Server Endpoint:** [http://localhost:8000](http://localhost:8000)
- **Swagger Documentation:** [http://localhost:8000/docs](http://localhost:8000/docs)

### Starting Frontend

Execute the Next.js development server:
```bash
npm run dev:frontend
```
The administration portal will launch at:
- **Console Endpoint:** [http://localhost:3000](http://localhost:3000)

### Starting Mobile

Navigate to the `mobile` workspace and start the Expo dev client:
```bash
cd mobile
npx expo start
```
You can run it on an iOS simulator (`i`), Android emulator (`a`), or via the Expo Go application by scanning the terminal QR code.

---

## Environment Variables

Local setups require `.env` files in specific directories. The setup scripts copy them from `.env.example` templates automatically if missing.

- **`/.env`**: Global environment variables for root orchestrators.
- **`/backend/.env`**: Backend configurations (database URLs, CORS allowed domains, auth settings).
- **`/frontend/.env`**: Next.js client settings.
- **`/mobile/.env`**: React Native API references.

Read the comments in the respective `.env.example` templates for detailed descriptions of each variable.

---

## Security Configurations

AI-BOS features separate security configs that toggle dynamically according to the `ENVIRONMENT` parameter in `.env`:
* **Development Mode (`ENVIRONMENT=development`):** Automatically enables Swagger UI (`/docs`), Redoc, and OpenAPI assets via relaxed Content Security Policies, trusts loopback hosts, and permits HTTP requests for simple local debugging.
* **Production Mode:** Enforces a strict Enterprise Content Security Policy (`default-src 'self'`), restricts trusted host requests to your specific production domains, and redirects all HTTP requests to secure HTTPS protocols.

For a full breakdown of the security headers, policies, and environment configurations, refer to the [Security Documentation](file:///d:/react-website/aibios/documentation/SECURITY.md).

---

## Troubleshooting

### Verification Diagnostics

Run the architectural verification check to confirm files, folders, tool versions, and database connectivity:
```bash
npm run verify
```

To run detailed port conflict and environment directory diagnostics, execute the workspace doctor script:
```bash
python scripts/doctor.py
```

To test active server connections and query endpoint health metrics:
```bash
python scripts/health.py
```

### Complete Environment Reset

If you need to delete all caches, remove the Python virtual environment and `node_modules` folders, and start with a fresh installation:
- **Windows:** Run `powershell ./scripts/reset.ps1`
- **Linux/macOS:** Run `bash ./scripts/reset.sh`

---

## Future Roadmap

- **Phase 0:** Core Architecture & Local-First Foundation *(Completed)*
- **Phase 1:** Multi-Agent Pipeline & LangGraph Integrations
- **Phase 2:** Polyglot Schema Migrations & Identity Services
- **Phase 3:** Production Containerization & Kubernetes Blueprints
