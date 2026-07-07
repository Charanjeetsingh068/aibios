# Enterprise Project Rules & Security Mandates — AI-BOS

This manual enforces system security policies, repository parameters, and strict boundary separations.

---

## 1. Secrets Management and Security Policies

### Zero plaintext secrets in version control
- Under no circumstances should passwords, OAuth tokens, API keys, or JWT secret variables be committed to Git.
- Use `.env.template` files as the structural template, and build an active `.env` configuration file locally (which must remain in `.gitignore`).
- For production environments, environment variables must be injected dynamically via secure vaults (e.g. AWS Secrets Manager, HashiCorp Vault) or container run variables.

### Network and DB Separation
- Database services (PostgreSQL, MongoDB, Redis) should be configured to listen only on loopback interfaces (`127.0.0.1` or `localhost`) for security in local development.
- Database ports (5432, 27017, 6379, 6333) should never be exposed directly to public internet gateways. Keep them isolated within secure internal networks or firewalled behind localhost configurations.

---

## 2. Directory Separation Rules

- **Shared Components (`shared/`):** Place only immutable schema types, basic structures, and shared constants here.
- **Agents separation (`agents/`):** LangGraph workflow definitions, state dict definitions, and agent nodes must reside in the dedicated agents workspace. Keep them isolated from specific API routes.
- **Frontend vs Backend decoupling:** The web frontend (`frontend/`) and the FastAPI backend (`backend/`) must remain entirely independent. Communicate exclusively via JSON REST endpoints.
- **Vanilla CSS styling constraint:** Keep custom themes inside `variables.css` using HSL variables. Tailwind CSS or inline component variables should be avoided.

---

## 3. Architecture Lock & Phase Boundaries

- **No Premature Feature Code:** Never write database models, API routing nodes, or business functions before their phase boundary is officially open. Refer to the [Future Phase Registry](file:///d:/react-website/aibios/documentation/PHASE_REGISTRY.md) for details.
- **Permanent Registries Compliance:** All code changes must align with [Module Registry](file:///d:/react-website/aibios/documentation/MODULE_REGISTRY.md) and [Folder Responsibility Map](file:///d:/react-website/aibios/documentation/FOLDER_RESPONSIBILITY_MAP.md) constraints.
