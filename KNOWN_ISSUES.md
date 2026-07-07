# Known Issues — AI-BOS

This document logs any known development limitations, service connection profiles, and environment requirements for the local development workspace of AI-BOS.

---

## 1. Local Database Status Offlines (Expected Behavior)

Under the **Local-First Architecture Standard**, Docker is not used during local development. All operational database services must run directly on the developer host computer.

* **Issue Description:** The admin console dashboard may display `DISCONNECTED` (in red) for **PostgreSQL**, **Redis**, or **Qdrant Vector Database**.
* **Impact:** System status is reported as `DEGRADED`.
* **Root Cause:** The database engines are not actively running or listening on their respective default host ports (`5432`, `6379`, `6333`).
* **Resolution Guidelines:** Developers must ensure the services are started natively on Windows:
  - **PostgreSQL:** Start the Postgres service (e.g. via `pg_ctl start` or standard Windows Service manager).
  - **Redis:** Start `redis-server.exe` on port `6379`.
  - **Qdrant:** Start Qdrant server locally on port `6333`.

*(Note: MongoDB is currently reported as `CONNECTED` (green) because the native MongoDB service is actively running on your local port `27017`).*
