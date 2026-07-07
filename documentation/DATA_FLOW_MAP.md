# Data Flow Map — AI-BOS

This map documents the pathways, validation nodes, and persistence destinations of incoming data streams in the AI-BOS platform.

---

## 1. Live Lead Ingestion Pipeline

The diagram below traces the real-time processing flow of a lead from ingestion to notification delivery:

```text
[Facebook / Instagram Webhook] -----\
[Manual CSV Upload] -----------------+---> [FastAPI Ingestion Router]
[Landing Pages / Form APIs] --------/                   |
                                                        | (Publishes JSON payload)
                                                        v
                                             [Redis Ingestion Queue]
                                                        |
                                                        | (Consumes async jobs)
                                                        v
                                             [Validation & Clean Engine]
                                                        |
                                                        +--> [Deduplication Checker] (Verifies email/phone in PostgreSQL)
                                                        +--> [Scoring Engine] (Calculates quality score)
                                                        |
                                                        v
                                             [Storage & Delegation Layer]
                                                        |
                                                        +--> Save to PostgreSQL (Structured Lead Metadata)
                                                        +--> Save to MongoDB (Raw Webhook Telemetry & History Log)
                                                        |
                                                        v
                                             [Notification & Router Nodes]
                                                        |
                                                        +--> Publish to Redis alert channels
                                                        +--> Dispatch WhatsApp templates (WhatsApp Business API)
                                                        +--> Route call queues (Voice AI Calling API)
```

---

## 2. Persistence Layer Assignments

Different classes of data are routed to specialized storage engines:

* **PostgreSQL (ACID Relational):**
  - User accounts, crypt hashes, and RBAC role states.
  - Active leads details (email, phone, status, assigned owner, custom attributes).
  - Campaign metrics, analytics summaries, and billing metadata.
* **MongoDB (High-Volume JSON Documents):**
  - Raw incoming HTTP payloads (webhook parameters) for audit trails.
  - Chat transcripts from WhatsApp or SMS.
  - Call recording logs, call duration metadata, and AI voice transcriptions.
  - Audit history logs of lead updates and movements.
* **Redis (In-Memory Key-Value):**
  - Session tokens and login locks.
  - API sliding-window rate limit counters.
  - Background task queues (Lead Queue) and transient pub/sub notifications.
* **Qdrant (Vector DB):**
  - High-dimensional vector embeddings for context documentation.
  - RAG episodic memory nodes used by autonomous AI Agents.
