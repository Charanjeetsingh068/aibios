# Changelog — AI-BOS

All notable architectural adjustments, code refactors, configuration additions, and file removals completed during this environment audit and repair phase are recorded below.

---

## [Phase 2.1] — Enterprise Multi-Tenant Authentication Foundation

### Added Files
* **[`backend/app/models/auth.py`](file:///d:/react-website/aibios/backend/app/models/auth.py):** Implemented relational schemas for Organizations, Users, Roles, Permissions, Sessions, RefreshTokens, and logs.
* **[`backend/app/schemas/auth.py`](file:///d:/react-website/aibios/backend/app/schemas/auth.py):** Declared Pydantic request/response model schemas for JWT payloads.
* **[`backend/app/api/v1/endpoints/auth.py`](file:///d:/react-website/aibios/backend/app/api/v1/endpoints/auth.py):** Developed authentication controllers (login, logout, refresh, recovery, change, and me).
* **[`frontend/src/services/authService.ts`](file:///d:/react-website/aibios/frontend/src/services/authService.ts):** Created centralized API fetch wrappers for managing token rotation and authorization bearer headers.
* **[`frontend/src/app/auth/login/page.tsx`](file:///d:/react-website/aibios/frontend/src/app/auth/login/page.tsx):** Implemented corporate login screen with remember me selection.
* **[`frontend/src/app/auth/forgot-password/page.tsx`](file:///d:/react-website/aibios/frontend/src/app/auth/forgot-password/page.tsx):** Developed password recovery request page.
* **[`frontend/src/app/auth/reset-password/page.tsx`](file:///d:/react-website/aibios/frontend/src/app/auth/reset-password/page.tsx):** Created password reset confirmation screen.
* **[`frontend/src/app/auth/unauthorized/page.tsx`](file:///d:/react-website/aibios/frontend/src/app/auth/unauthorized/page.tsx):** Formulated access denied error screen.
* **[`frontend/src/app/auth/session-expired/page.tsx`](file:///d:/react-website/aibios/frontend/src/app/auth/session-expired/page.tsx):** Configured token expiry redirect screen.
* **[`frontend/src/app/profile/page.tsx`](file:///d:/react-website/aibios/frontend/src/app/profile/page.tsx):** Implemented user details settings page.
* **[`frontend/src/app/profile/change-password/page.tsx`](file:///d:/react-website/aibios/frontend/src/app/profile/change-password/page.tsx):** Designed old password verification change form.
* **[`scripts/test_auth_integration.py`](file:///d:/react-website/aibios/scripts/test_auth_integration.py):** Created automated E2E authentication validation script.
* **[`AUTHENTICATION.md`](file:///d:/react-website/aibios/AUTHENTICATION.md):** User authentication architecture documentation.
* **[`DATABASE_SCHEMA.md`](file:///d:/react-website/aibios/DATABASE_SCHEMA.md):** Multitenancy ER schema diagram and mappings.
* **[`API_REFERENCE.md`](file:///d:/react-website/aibios/API_REFERENCE.md):** Endpoint payloads reference manual.
* **[`SECURITY_REPORT.md`](file:///d:/react-website/aibios/SECURITY_REPORT.md):** Cryptography review and security assessment.

### Modified Files
* **[`backend/app/main.py`](file:///d:/react-website/aibios/backend/app/main.py):** Added lifespan context handlers triggering table initialization and default data seeding (Demo Corp, admin credentials, roles, and permissions) on startup.
* **[`backend/app/core/database.py`](file:///d:/react-website/aibios/backend/app/core/database.py):** Enabled dynamic async SQLite fallback connections.
* **[`frontend/src/app/page.tsx`](file:///d:/react-website/aibios/frontend/src/app/page.tsx):** Added mount checking hooks redirecting unauthenticated sessions, and linked avatar initials.
* **[`scripts/verify.py`](file:///d:/react-website/aibios/scripts/verify.py):** Appended new routes, controllers, and services to validation checklists.

---

## [Phase Gate 1] — E2E Testing & Verification Gate

### Added Files
* **[`scripts/test_dashboard_integration.py`](file:///d:/react-website/aibios/scripts/test_dashboard_integration.py):** Added automated validation script checking endpoints status codes, JSON responses, and matching frontend console bindings.
* **[`TEST_REPORT.md`](file:///d:/react-website/aibios/TEST_REPORT.md):** Consolidated test report logging REST endpoints results and browser testing session outputs.
* **[`KNOWN_ISSUES.md`](file:///d:/react-website/aibios/KNOWN_ISSUES.md):** Logs guidelines for database offlines and local-first port profiles.

### Modified Files
* **[`scripts/verify.py`](file:///d:/react-website/aibios/scripts/verify.py):** Added the new integration test file to validation checklists.

---

## [Phase 1.1] — Core Infrastructure & Live API Integration

### Added Files
* **[`backend/app/api/v1/endpoints/system.py`](file:///d:/react-website/aibios/backend/app/api/v1/endpoints/system.py):** Implemented system status, info, parallel database checks, and LangGraph agents registry APIs.
* **[`frontend/src/services/systemService.ts`](file:///d:/react-website/aibios/frontend/src/services/systemService.ts):** Created reusable API service wrappers for frontend client data fetching.
* **[`scripts/test_dashboard_integration.py`](file:///d:/react-website/aibios/scripts/test_dashboard_integration.py):** Created automated validation script verifying Status 200 codes, JSON payloads, and frontend layout bindings.

### Modified & Refactored Files
* **[`backend/app/main.py`](file:///d:/react-website/aibios/backend/app/main.py):** Registered the new system diagnostics router prefix.
* **[`backend/app/core/database.py`](file:///d:/react-website/aibios/backend/app/core/database.py):** Bound Postgres, Redis, and Qdrant verification connections to 2.0-second timeouts to avoid blocking the event loop when offline.
* **[`frontend/src/app/page.tsx`](file:///d:/react-website/aibios/frontend/src/app/page.tsx):** Rewrote dashboard layout to pull data from backend APIs dynamically, added loading skeletons, and integrated retry frames.
* **[`frontend/src/styles/dashboard.css`](file:///d:/react-website/aibios/frontend/src/styles/dashboard.css):** Added loading shimmers, pulse keyframes, and layout configurations.
* **[`scripts/verify.py`](file:///d:/react-website/aibios/scripts/verify.py):** Added new endpoints and service modules to the file integrity verification list.
* **[`.env` files](file:///d:/react-website/aibios/.env):** Updated local MongoDB URL parameters to reflect direct unauthenticated localhost connection standard.

---

## [Phase 0 Lock] — Local-First Standard Migration

### Repaired / Refactored Files
* **[`backend/app/core/config.py`](file:///d:/react-website/aibios/backend/app/core/config.py):** Modified `BACKEND_CORS_ORIGINS` annotation to `Union[List[str], str]` to prevent Pydantic Settings from raising parsing exceptions for comma-separated lists in `.env`.
* **[`frontend/src/app/page.tsx`](file:///d:/react-website/aibios/frontend/src/app/page.tsx):** 
  - Removed unused icon imports (`Settings`, `Layers`, `ArrowRight`, `FolderTree`, `FileText`) to resolve build-time ESLint warnings.
  - Replaced Nginx metrics cards with FastAPI Gateway UI indicators.
  - Scrubbed Nginx rate limiting descriptions and replaced them with API endpoint details.
* **[`scripts/verify.py`](file:///d:/react-website/aibios/scripts/verify.py):** Fixed python syntax indentation error in the `except` block and appended automated Docker artifact check logic.

### Added Files
* **[`setup.ps1`](file:///d:/react-website/aibios/setup.ps1):** Local Windows PowerShell setup script.
* **[`setup.bat`](file:///d:/react-website/aibios/setup.bat):** Windows Command Prompt wrapper.
* **[`setup.sh`](file:///d:/react-website/aibios/setup.sh):** Linux/Unix/macOS setup shell script.
* **[`backend/.env.example`](file:///d:/react-website/aibios/backend/.env.example):** Commented backend configuration template.
* **[`frontend/.env.example`](file:///d:/react-website/aibios/frontend/.env.example):** Commented frontend configuration template.
* **[`mobile/.env.example`](file:///d:/react-website/aibios/mobile/.env.example):** Commented mobile configuration template.
* **[`documentation/MASTER_BLUEPRINT.md`](file:///d:/react-website/aibios/documentation/MASTER_BLUEPRINT.md):** Main systems blueprint.
* **[`documentation/MODULE_REGISTRY.md`](file:///d:/react-website/aibios/documentation/MODULE_REGISTRY.md):** Master list of locked core modules.
* **[`documentation/PHASE_REGISTRY.md`](file:///d:/react-website/aibios/documentation/PHASE_REGISTRY.md):** Stage boundaries definitions.
* **[`documentation/DEPENDENCY_MAP.md`](file:///d:/react-website/aibios/documentation/DEPENDENCY_MAP.md):** System-wide dependency register.
* **[`documentation/SERVICE_MAP.md`](file:///d:/react-website/aibios/documentation/SERVICE_MAP.md):** Port bindings configuration guide.
* **[`documentation/DATA_FLOW_MAP.md`](file:///d:/react-website/aibios/documentation/DATA_FLOW_MAP.md):** Data ingestion processing paths chart.
* **[`documentation/FOLDER_RESPONSIBILITY_MAP.md`](file:///d:/react-website/aibios/documentation/FOLDER_RESPONSIBILITY_MAP.md):** Directory mapping and boundaries checklist.
* **[`documentation/SECURITY.md`](file:///d:/react-website/aibios/documentation/SECURITY.md):** Security configurations manual.
* **[`PROJECT_HEALTH.md`](file:///d:/react-website/aibios/PROJECT_HEALTH.md):** Repository health evaluation report.
* **[`NEXT_PHASE_READY.md`](file:///d:/react-website/aibios/NEXT_PHASE_READY.md):** Phase 1 readiness report.

### Modified Files
* **[`package.json`](file:///d:/react-website/aibios/package.json):** Pointed setup commands to root scripts and removed Docker compose execution scripts.
* **[`.env.example`](file:///d:/react-website/aibios/.env.example):** Changed MongoDB URL to localhost and detailed all comments.
* **[`backend/.env`](file:///d:/react-website/aibios/backend/.env):** Updated database servers location parameters to localhost.
* **[`backend/app/main.py`](file:///d:/react-website/aibios/backend/app/main.py):** Integrated dynamic middleware (CORS, Trusted Hosts, security headers) based on settings environment.
* **[`scripts/doctor.py`](file:///d:/react-website/aibios/scripts/doctor.py):** Removed Docker CLI checks.
* **[`scripts/health.py`](file:///d:/react-website/aibios/scripts/health.py):** Replaced Nginx port queries with direct API connection check logic.
* **[`scripts/reset.ps1`](file:///d:/react-website/aibios/scripts/reset.ps1) & [`scripts/reset.sh`](file:///d:/react-website/aibios/scripts/reset.sh):** Removed Docker compose volume delete tasks.
* **[`frontend/package.json`](file:///d:/react-website/aibios/frontend/package.json):** Added `eslint` and `eslint-config-next` devDependencies.
* **[`README.md`](file:///d:/react-website/aibios/README.md):** Rewritten for local installation guides.
* **[`documentation/ARCHITECTURE.md`](file:///d:/react-website/aibios/documentation/ARCHITECTURE.md):** References added to all new blueprints.
* **[`documentation/PROJECT_RULES.md`](file:///d:/react-website/aibios/documentation/PROJECT_RULES.md):** Added rules prohibiting premature business logic.

### Deleted Files & Folders
All Dockerfiles, Docker configurations, and historical Docker script files have been permanently deleted from the repository:
* `docker-compose.yml` (Root)
* `docker/nginx/nginx.conf`
* `docker/` (Root directory)
* `backend/Dockerfile`
* `frontend/Dockerfile`
* `backend/.env.template`
* `scripts/setup.ps1` & `scripts/setup.sh`
* `scripts/start.ps1` & `scripts/start.sh`
* `scripts/stop.ps1` & `scripts/stop.sh`
* `documentation/archive/docker_reference/` (Archive folder and all contents)
