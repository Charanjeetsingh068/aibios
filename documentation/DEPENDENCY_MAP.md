# Dependency Map — AI-BOS

This map details all package, tool, database, and library dependencies required across the AI-BOS Enterprise system.

---

## 1. System-Level Dependencies

The root workspace orchestrates three distinct client contexts and four polyglot database instances:
* **Runtime Environments:**
  - Python >= 3.10 (Backend server, agents orchestration, utility scripts)
  - Node.js >= 18.0.0 (Next.js admin console, Expo CLI host runner)
  - npm >= 9.0.0 (Node packages installer)
  - Git (Workspace control and consistency tracking)
* **Database Services:**
  - PostgreSQL 15+ (Transactional storage engine, listening on local port `5432`)
  - MongoDB 6.0 (Telemetry and log document database, listening on local port `27017`)
  - Redis 7.0 (Ephemeral caching, rate limiter, and message queue broker, listening on local port `6379`)
  - Qdrant Vector DB (Semantic vector memory store, listening on REST port `6333` / gRPC port `6334`)

---

## 2. Backend Service Dependencies (Python Packages)
Defined inside [backend/requirements.txt](file:///d:/react-website/aibios/backend/requirements.txt):

* **FastAPI Core:**
  - `fastapi==0.115.0` (FastAPI REST routing gateway)
  - `uvicorn[standard]==0.30.6` (Asynchronous HTTP server runner)
  - `pydantic[email]==2.9.2` (Data validation schemas)
  - `pydantic-settings==2.5.2` (Environment configuration loader)
  - `python-multipart==0.0.12` (Form data parsing)
* **Database Connectors:**
  - `SQLAlchemy==2.0.35` (Object Relational Mapper)
  - `asyncpg==0.30.0` (Asynchronous PostgreSQL client)
  - `motor==3.6.0` (Asynchronous MongoDB client)
  - `redis==5.0.8` (Asynchronous Redis client)
  - `qdrant-client==1.11.1` (Qdrant client driver)
* **Security & Auth:**
  - `python-jose[cryptography]==3.3.0` (JWT encode/decode helper)
  - `passlib[bcrypt]==1.7.4` (Password hashing utilities)
  - `bcrypt==4.2.0` (Password encryption engine)
* **AI & Workflows:**
  - `httpx==0.27.2` (Async HTTP requests client)
  - `langchain-core==0.2.30` (AI schema definitions wrapper)
  - `langgraph==0.2.16` (Multi-agent state graph pipeline)

---

## 3. Frontend & Mobile Dependencies (Node Packages)

### Frontend (Next.js Console)
Defined inside [frontend/package.json](file:///d:/react-website/aibios/frontend/package.json):
- `next` (Next.js App Router framework)
- `react` / `react-dom` (React UI rendering framework)
- `lucide-react` (SVG icons package)
- `typescript` (Static typing configurations)

### Mobile (React Native CLI / Expo Portal)
Defined inside [mobile/package.json](file:///d:/react-website/aibios/mobile/package.json):
- `expo` (Mobile application helper suite)
- `react-native` (Native UI rendering components wrapper)
- `react` / `react-dom` (React mobile interface builder)
- `typescript` (Static typing configurations)
