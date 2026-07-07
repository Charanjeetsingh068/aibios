# Database Schema Manual — AI-BOS

This document details the relational entity diagrams, schema models, and data types configured for the AI-BOS Enterprise multitenancy foundation.

---

## 1. Entity Relationship Model

The relational tables map user credentials, sessions, and logs to their respective tenant organizations:

```mermaid
erDiagram
    organizations {
        string id PK
        string name
        string slug UK
        string status
        datetime created_at
        datetime updated_at
    }
    roles {
        string id PK
        string name
        string description
        datetime created_at
        datetime updated_at
    }
    permissions {
        string id PK
        string name
        string description
    }
    role_permissions {
        string role_id PK, FK
        string permission_id PK, FK
    }
    users {
        string id PK
        string organization_id FK
        string first_name
        string last_name
        string email UK
        string phone
        string password_hash
        string profile_image
        string status
        string role_id FK
        string timezone
        string language
        datetime created_at
        datetime updated_at
        datetime last_login
    }
    sessions {
        string id PK
        string user_id FK
        string organization_id FK
        string access_token_id UK
        string device_info
        string ip_address
        boolean is_active
        datetime expires_at
        datetime created_at
        datetime updated_at
    }
    refresh_tokens {
        string id PK
        string session_id FK
        string token_hash UK
        boolean is_revoked
        datetime expires_at
        datetime created_at
    }
    login_history {
        string id PK
        string user_id FK
        string organization_id FK
        string email
        string status
        string failure_reason
        string ip_address
        string device_info
        datetime created_at
    }
    audit_logs {
        string id PK
        string user_id FK
        string organization_id FK
        string action
        string description
        string resource
        string resource_id
        string ip_address
        datetime created_at
    }
    password_reset_tokens {
        string id PK
        string user_id FK
        string token_hash UK
        boolean is_used
        datetime expires_at
        datetime created_at
    }

    organizations ||--o{ users : "hosts"
    organizations ||--o{ sessions : "contains"
    roles ||--o{ users : "assigns"
    roles ||--o{ role_permissions : "contains"
    permissions ||--o{ role_permissions : "granted_to"
    users ||--o{ sessions : "starts"
    users ||--o{ login_history : "records"
    users ||--o{ audit_logs : "records"
    users ||--o{ password_reset_tokens : "requests"
    sessions ||--o{ refresh_tokens : "signs"
```

---

## 2. Seed Data Specifications

The relational schema initializes and seeds the following core values on server lifespan startup:

### Roles & Default Permissions Mappings
1. **`super_admin`:** Has `admin:all` (Full global control).
2. **`org_admin`:** Has `org:read`, `org:write`, `leads:read`, `leads:write`, `agents:read`, `agents:write` (Tenant operations controller).
3. **`manager`:** Has `leads:read`, `leads:write`, `agents:read` (CRM team managers).
4. **`sales_executive`:** Has `leads:read`, `leads:write` (Lead operations).
5. **`ai_agent`:** Has `leads:read`, `leads:write`, `agents:read` (Cognitive automations).
6. **`developer`:** Has `agents:read`, `agents:write` (Agent configs developer).
7. **`auditor`:** Has `leads:read`, `agents:read` (Security reviewer).
8. **`viewer`:** Has `leads:read` (Read-only access).

### Seeded Credentials
* **Demo Organization:** `Demo Corp` (slug: `demo`)
* **Default Super Admin:**
  - **Email:** `admin@aibios.com`
  - **Password:** `admin123`
