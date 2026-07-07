# Future Phase Registry — AI-BOS

This document specifies the official boundaries of the development phases for the AI-BOS system. All subsequent execution tasks must align with this phased roadmap to ensure structural integrity and prevent premature feature creep.

---

## Phase 0: Foundation (Completed ✅)
- **Focus:** Directory layout setups, local workspace automation scripts, config parsers, diagnostic utilities, global environment setups, and baseline security profiles.
- **Core Deliverables:**
  - Setup scripts (`setup.ps1`, `setup.bat`, `setup.sh`) and reset helpers.
  - Baseline Next.js UI console and React Native boilerplate structures.
  - Automated project integrity checker (`verify.py`) and health monitor.

---

## Phase 1: Core Infrastructure
- **Focus:** Configure local relational, document, and vector database engines, and database migrations.
- **Core Deliverables:**
  - Alembic migrations directory configuration for PostgreSQL schemas.
  - Database schema connection pools setup and shared connector instances.
  - Vector index creation scripts for Qdrant.
  - NoSQL collection seeding scripts for MongoDB.

---

## Phase 2: Authentication
- **Focus:** Set up identity verification, session handling, and role validations.
- **Core Deliverables:**
  - JWT token encoder/decoder wrappers (OAuth2).
  - RBAC (Role-Based Access Control) validator middlewares.
  - Redis token blacklisting/invalidation services.
  - Sign-in, sign-out, and register stubs.

---

## Phase 3: Organization / Company
- **Focus:** Implement multi-tenant organizational isolation structures.
- **Core Deliverables:**
  - Tenant (Company) schemas and migration tables.
  - Multi-tenant routing utilities.
  - Company settings profile models and APIs.

---

## Phase 4: User Management
- **Focus:** Provide administrative controls for accounts, profiles, and permissions.
- **Core Deliverables:**
  - User invitation pipelines and permission activation handlers.
  - User profiles CRUD endpoints.
  - Admin users settings management views.

---

## Phase 5: Lead Engine (Live Lead Engine)
- **Focus:** Build real-time lead ingestion webhooks, deduplication filters, and scoring logic.
- **Core Deliverables:**
  - Ingestion webhooks for Facebook Ads, Instagram Ads, and Landing Page Forms.
  - Redis ingestion task queues.
  - Verification scoring functions and lead assignment rules.

---

## Phase 6: CRM
- **Focus:** Design client workspaces, sales pipelines, and spreadsheets exporter tools.
- **Core Deliverables:**
  - CRM pipelines, stages, and communication histories database models.
  - Next.js Editable Lead Sheets console.
  - CSV, Excel, and PDF data exporters.

---

## Phase 7: AI Voice (Voice AI)
- **Focus:** Integrate VoIP telephony gateways, STT/TTS models, and call transcriptions.
- **Core Deliverables:**
  - Inbound and Outbound calling interfaces (Twilio / Retell stubs).
  - Call routing queues.
  - Call recording telemetry metadata, transcripts, and LLM summary generators.

---

## Phase 8: WhatsApp
- **Focus:** Connect template messaging and chat histories with WhatsApp APIs.
- **Core Deliverables:**
  - Meta WhatsApp Business API integration.
  - Broadcast campaign template schedulers.
  - Media templates and catalog synchronization pipelines.

---

## Phase 9: Facebook & Instagram Integration
- **Focus:** Integrate social marketing APIs and target audience sync tools.
- **Core Deliverables:**
  - Facebook/Instagram Graph API connector.
  - Custom Audience sync schedulers.
  - Ad Campaign tracking metrics telemetry dashboard.
