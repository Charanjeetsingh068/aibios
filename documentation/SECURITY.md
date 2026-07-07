# Security Architecture & Configurations — AI-BOS

AI-BOS enforces strict, enterprise-grade security controls. To ensure a smooth local development workflow, security configurations are dynamically adapted based on the environment context (`ENVIRONMENT=development` vs. `ENVIRONMENT=production`).

> [!NOTE]
> For database access scopes and port allocations, refer to the [Service Map](file:///d:/react-website/aibios/documentation/SERVICE_MAP.md) and [Data Flow Map](file:///d:/react-website/aibios/documentation/DATA_FLOW_MAP.md).

---

## 1. Security Configuration Profiles

### Development Security Profile
When the application is run with `ENVIRONMENT=development` (defined in the active environment configs), the security controls are relaxed just enough to enable developer tooling like the FastAPI Swagger UI and Redoc, and allow communication with a locally running Next.js development server.

- **Content Security Policy (CSP):**
  - `default-src 'self';`
  - `script-src 'self' 'unsafe-inline' cdn.jsdelivr.net;` (allows CDN script resources and inline Swagger/Redoc startup scripts)
  - `style-src 'self' 'unsafe-inline' cdn.jsdelivr.net;` (allows CDN styling sheets)
  - `img-src 'self' data: fastapi.tiangolo.com cdn.jsdelivr.net;` (allows swagger UI icons and favicons)
  - `connect-src 'self' http://localhost:8000 http://localhost:3000 http://127.0.0.1:8000 http://127.0.0.1:3000 ws://localhost:3000 ws://127.0.0.1:3000;` (allows local client connections and WebSocket reloading)
  - `frame-ancestors 'none';` (clickjacking protection remains active)
- **HTTPS Redirection:** Disabled (permits standard local development HTTP protocol requests).
- **Trusted Hosts:** Restricted to `["localhost", "127.0.0.1", "*.localhost"]` to mitigate Host Header injection.

---

### Production Security Profile
When `ENVIRONMENT` is set to any value other than `development` (e.g. `production`), strict enterprise security bounds are activated.

- **Content Security Policy (CSP):**
  - `default-src 'self';` (no external CDNs, no inline script executions, no external domains allowed)
  - `frame-ancestors 'none';` (blocks embedding inside frames or iframes)
- **HTTPS Redirection:** Enabled (forces all incoming requests to secure TLS/SSL protocols).
- **Trusted Hosts:** Strictly configured to production domain boundaries (e.g. `example.com`, `*.example.com`).

---

## 2. Shared Security Headers
Regardless of the environment, the following defensive security headers are applied to every HTTP response:

| Header Name | Value | Purpose |
| :--- | :--- | :--- |
| **`X-Frame-Options`** | `DENY` | Prevents page embedding (Clickjacking protection). |
| **`X-Content-Type-Options`** | `nosniff` | Disables MIME type sniffing (blocks cross-site scripting uploads). |
| **`X-XSS-Protection`** | `1; mode=block` | Enforces browser XSS filters if a cross-site script is detected. |
| **`Referrer-Policy`** | `strict-origin-when-cross-origin` | Protects privacy by omitting request origins during third-party redirections. |
| **`Permissions-Policy`** | `geolocation=(), microphone=(), camera=()` | Disables browser hardware permissions access. |
| **`X-Permitted-Cross-Domain-Policies`** | `none` | Blocks Flash/PDF policy XML loading. |
| **`Cross-Origin-Opener-Policy`** | `same-origin` | Isolates browser browsing contexts. |
| **`Cross-Origin-Resource-Policy`** | `same-origin` | Prevents cross-origin reading of assets. |
