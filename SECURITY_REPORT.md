# Security Assessment Report — AI-BOS Auth Services

This document performs a security threat review and details the cryptography specifications, token protection models, and CORS/CSP gates configured for the authentication subsystem.

---

## 1. Cryptography & Credentials Protection

* **Password Hashing:** Plain-text passwords are encrypted using **Bcrypt** (configured with standard work factor settings via Passlib). No plain-text passwords or weak hashes (MD5/SHA1) are stored in the database.
* **Token Signatures:** Access tokens are signed using the **HS256** algorithm with a cryptographically secure 256-bit secret key.
* **Random Generative Entropy:** Reset tokens and refresh tokens are generated using the Python standard `secrets` library (producing secure entropy outputs via `/dev/urllib` system resources).

---

## 2. Session Security Protection Policies

* **Refresh Token Rotation (RTR):** Refresh tokens can only be used once. If a replayed token attempt is captured, the entire parent session is marked inactive immediately.
* **Session Invalidation:** Manual password changes and logout actions explicitly deactivate all active database sessions associated with the user account, rendering old access tokens useless on subsequent router requests.
* **Safe Forgot-Password Routines:** The forgot-password endpoint returns an identical confirmation message regardless of whether the email exists in the database. This prevents **email harvesting / enumeration** by malicious scanner bots.

---

## 3. Network & Middleware Gates

* **Secure Headers:** The response headers enforce standard security policies:
  - `X-Frame-Options: DENY` (Prevent clickjacking).
  - `X-Content-Type-Options: nosniff` (Prevent MIME-type sniffing).
  - `Content-Security-Policy` (Relaxed in development for CDNs, strict in production).
* **Cross-Origin Resource Sharing (CORS):** Restricted strictly to allowed origins config inside settings (e.g. `http://localhost:3000` during local dev).
* **Multi-Tenant Data Separation:** All core controllers (leads, workflows) enforce organization-level scoping:
  ```python
  # Multi-tenant data check rule
  query = select(Lead).where(Lead.organization_id == current_user.organization_id)
  ```
  This ensures strict **Data Isolation**; no authenticated user can query data belonging to a different tenant ID.
