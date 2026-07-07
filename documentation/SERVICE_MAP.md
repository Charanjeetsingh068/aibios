# Service Map — AI-BOS

This map documents the TCP port bindings and communication pathways utilized across the AI-BOS system in local, VPS, and cloud environments.

---

## 1. Port Configuration Registry

To avoid port conflicts, the following ports are officially allocated:

| Port | Service Name | Protocol | Access Boundary | Description |
| :--- | :--- | :--- | :--- | :--- |
| **3000** | Next.js Web Console | HTTP | Public / Host | Admin panel web user interface. |
| **8000** | FastAPI API Gateway | HTTP | Host Loopback | Core application REST endpoints and documentation. |
| **5432** | PostgreSQL Server | TCP | Localhost | ACID transactional relational storage. |
| **27017** | MongoDB Server | TCP | Localhost | Telemetry logs, chats, and metadata document storage. |
| **6379** | Redis Server | TCP | Localhost | Session store, sliding-window rate limiters, and pub/sub task queues. |
| **6333** | Qdrant REST API | HTTP | Localhost | High-performance vector database search client. |
| **6334** | Qdrant gRPC API | gRPC | Localhost | High-throughput vector search client. |

---

## 2. Communication Pathways

The components communicate over specific channels:

```text
[Web Browser Client] --(Port 3000)--> [Next.js Server (Next.js Dev Proxy)]
                                            |
                                            | (Next.js rewrites '/api' queries to port 8000)
                                            v
[Mobile Companion Portal] --(Port 8000)--> [FastAPI Backend Service]
                                            |
                                            +--(Port 5432)--> [PostgreSQL]
                                            +--(Port 27017)--> [MongoDB]
                                            +--(Port 6379)--> [Redis Cache & Queue]
                                            +--(Port 6333)--> [Qdrant Vector DB]
```

* **Client Access Route:** Browsers load the console dashboard directly on port 3000. Mobile companion instances query the FastAPI gateway directly on port 8000.
* **API Redirection Handler:** The Next.js frontend redirects REST endpoints starting with `/api` directly to port 8000 using standard development config rewrites. This resolves CORS limitations without introducing third-party gateways.
* **Database Isolations:** Database engines are bound to `localhost` (`127.0.0.1`) and are strictly inaccessible to public network ports in dev/staging.
