# Module Registry — AI-BOS

This registry lists all **Core and Extension Modules** permanently locked into the AI-BOS architecture. It defines the structural limits, database assignments, and sub-components for each module.

---

## 1. Foundation & Core Modules

### Foundation
- **Role:** Handles core systems bootstrapping, base exception classes, HTTP routers, configuration loadings, and base database connector initializations.
- **Data Store:** Relational metadata schemas in PostgreSQL.

### Authentication
- **Role:** Handles identity management, token generation (JWT OAuth2), role assignments (RBAC), and authentication checks.
- **Data Store:** `users` and `roles` tables in PostgreSQL; tokens invalidated via Redis cache.

### User Management
- **Role:** Provides profiles management, user creations, password resets, and permission validations.
- **Data Store:** PostgreSQL.

### Security
- **Role:** Implements CSP headers injection, trusted hosts middleware, CORS configurations, rate-limiting, and request validation filters.
- **Data Store:** Redis (for sliding-window rate limit counters).

### Audit Logs
- **Role:** Implements system-wide tracking of user login attempts, database updates, and config changes.
- **Data Store:** PostgreSQL for structured security logs; MongoDB for transient system action documents.

### Dashboard
- **Role:** Consolidated administrative console providing system health parameters, user statistics, and lead metrics.

---

## 2. Marketing & Leads Pipeline

### Marketing
- **Role:** Handles campaign templates, campaign parameters, and analytics dashboards.

### Live Lead Engine
- **Role:** Automatically ingests, scores, cleans, and delegates leads in real-time.
- **Sub-Components:**
  - **Ingestion Channels:** Facebook Lead Ads webhook, Instagram Lead Ads webhook, Landing Pages API, Website HTML Forms, CSV Manual Upload, and generic Webhook endpoints.
  - **Pipeline Handlers:** Lead Ingestion Queue, Lead Scoring algorithm, Lead Deduplication rules, Lead Validation filters, Lead Assignment engine, and Lead History logger.
- **Data Store:** PostgreSQL for active leads metadata; MongoDB for historical webhook payloads and lead activities records.

### WhatsApp Integration
- **Role:** Handles template communications, follow-ups, and catalog views via the Official WhatsApp Business API.
- **Sub-Components:** Broadcast templates manager, media uploads tracker, Catalog integration, Conversation History, follow-up scheduler, and Appointment Confirmations workflow.
- **Data Store:** PostgreSQL for templates metadata; MongoDB for message history logs.

### Editable Lead Sheets
- **Role:** Excel-like inline web editor console enabling administrators to filter, edit, and export leads.
- **Sub-Components:** Excel Export, CSV Export, PDF Export, Google Sheets Sync, and Editable Lead Workspace UI.

---

## 3. Cognitive & AI Engine Modules

### Voice AI (Calling Gateway)
- **Role:** Interfaces with VoIP providers to conduct outgoing calls and handle incoming leads via voice agents.
- **Sub-Components:** Incoming Calls, Outgoing Calls, Call Queue dispatcher, Voice Selection (TTS/STT), Custom Voice models, Conversation Analysis, Appointment Booking, Call Summary, and Call Recording Metadata.
- **Data Store:** PostgreSQL for call logs and metadata; MongoDB for conversation analysis and summary payloads.

### CRM
- **Role:** Manages customer records, pipeline stages, lead notes, and communication logs.

### AI Learning Engine
- **Role:** Dynamically refines conversational templates and prompts based on call ratings and customer feedback.
- **Sub-Components:** Conversation Learning, Campaign Learning, Lead Quality Learning, Sales Script Optimization, and Prompt Optimization.
- **Data Store:** MongoDB for training telemetry; Qdrant vector database for semantic memory context.

### Developer AI
- **Role:** Developer-facing tool providing diagnostic assistants, system logs parsing, and automated troubleshooting recommendations.

---

## 4. Automation & Utility Modules

### Workflow Builder
- **Role:** Visual canvas enabling users to draw triggers and actions to map customer journeys.

### Automation
- **Role:** Background task runner executing schedules and follow-up templates (e.g. sending SMS/WhatsApp 1 day after lead signup).

### Reports
- **Role:** Formulates and compiles static reports for campaigns, agents performance, and calling metrics.

### Analytics
- **Role:** Consolidates analytics widgets and maps real-time data flows.

### Notifications
- **Role:** Manages system alerts, SMS alerts, WhatsApp notices, and email alerts.
- **Data Store:** Redis for transient queues.

### Billing
- **Role:** Manages subscription tiers, payment gateways (Stripe stubs), and usage invoices.

### Plugin Marketplace
- **Role:** Manages installation configurations for third-party extensions.

### Knowledge Base
- **Role:** Stores document nodes and wikis utilized by AI Agents for RAG context extraction.
- **Data Store:** Qdrant for vector embeddings; PostgreSQL for raw articles metadata.

### Documentation
- **Role:** Serves static developer blueprints and system contribution manuals directly on the console dashboard.

### Deployment
- **Role:** Provides systemd service files, ecosystem configs (PM2), and deployment script references.
