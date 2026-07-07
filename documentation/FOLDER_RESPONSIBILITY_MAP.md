# Folder Responsibility Map — AI-BOS

This map specifies the directory organization conventions and file-level responsibility limits for the AI-BOS workspace. All modifications must be saved in their respective directories.

---

## 1. Directory Structure Mappings

| Directory | Scope / Responsibility | Primary Target Files |
| :--- | :--- | :--- |
| **`agents/`** | Cognitive workflow topologies and agent scripts. | LangGraph workflow nodes, agent run state variables. |
| **`assets/`** | Centralized design tokens and theme templates. | Global parameters, variables templates. |
| **`backend/`** | FastAPI Rest APIs, database controllers, and schemas. | Backend routers, repository queries, models definitions. |
| **`config/`** | Shared system templates and environment files. | Shared constants blueprints. |
| **`database/`** | Database schema configurations and SQL setup scripts. | Database migrations, Postgres setup schemas, MongoDB collections. |
| **`documentation/`** | System architecture designs, registries, and rules. | Master blueprints, phase maps, security guidelines. |
| **`frontend/`** | Next.js administration portal client interface. | React templates, components, styles, Next.js routers. |
| **`integrations/`** | Sandbox mock connections for Stripe, Slack, etc. | Stripe payment drivers, webhook mock tests. |
| **`mobile/`** | React Native Expo application client portal. | Expo UI templates, navigation systems, native hooks. |
| **`scripts/`** | Diagnostic automations and setup helpers. | Verification checks, health testing scripts, reset scripts. |
| **`shared/`** | Shared constant mappings and invariant structures. | Immutable constant definitions. |
| **`testing/`** | E2E automation tests and integration validation. | Playwright playbooks, system tests scripts. |

---

## 2. Developer Responsibility Boundaries

To maintain clean architecture and prevent code churn:
* **Decoupled Business Logic:** All API routing endpoints must live inside `backend/app/api/`. Core business workflows must live inside `backend/app/services/` or `backend/app/repositories/`. No SQL queries or raw database interactions may occur inside routing files.
* **Component Styling Bounds:** Frontend developers must store custom styling properties inside `frontend/src/styles/variables.css` using HSL CSS variables. Ad-hoc styles inside React views are prohibited.
* **Cognitive Agents Isolation:** LangGraph state graph declarations must be maintained inside `agents/graph/`. Standard API routers inside `backend/` invoke agent graphs via a wrapper client interface, keeping routing and reasoning decoupled.
* **Locked Dependencies:** Backend dependency edits must be recorded inside `backend/requirements.txt`. Frontend and mobile dependencies must be recorded inside `frontend/package.json` and `mobile/package.json` respectively.
