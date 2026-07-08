# API Reference Manual — AI-BOS Auth Services

This document catalogues the authentication REST API endpoints exposed by the FastAPI gateway under the `/api/v1/auth` namespace.

---

## 1. Authentication Endpoints Summary

All request and response payloads are structured in JSON. Protected endpoints require a valid JWT Access Token passed in the HTTP headers as a Bearer authorization token.

| Method   | Endpoint Path      | Authentication | Description                                               |
| :------- | :----------------- | :------------- | :-------------------------------------------------------- |
| **POST** | `/login`           | None           | Verify user credentials and return access/refresh tokens. |
| **POST** | `/logout`          | Bearer Token   | Invalidate current session and revoke refresh tokens.     |
| **POST** | `/refresh`         | None           | Rotate expired access tokens using a valid refresh token. |
| **POST** | `/forgot-password` | None           | Generate recovery token for password resets.              |
| **POST** | `/reset-password`  | None           | Save new password using a recovery token.                 |
| **POST** | `/change-password` | Bearer Token   | Update current user's password.                           |
| **GET**  | `/me`              | Bearer Token   | Retrieve logged-in user details.                          |

---

## 2. Endpoint Specifications

### 1. User Sign In

- **Endpoint:** `POST /api/v1/auth/login`
- **Request Payload (`LoginRequest`):**

```json
{
  "email": "admin@aibios.com",
  "password": "admin123",
  "remember_me": false
}
```

- **Success Response (`TokenResponse`):**

```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsIn...",
  "token_type": "bearer",
  "expires_in": 3600,
  "refresh_token": "a1b2c3d4...",
  "user_id": "superadmin-uuid-placeholder-123456",
  "organization_id": "demo-org-uuid-placeholder-123456",
  "role": "super_admin"
}
```

### 2. User Sign Out

- **Endpoint:** `POST /api/v1/auth/logout`
- **Headers:** `Authorization: Bearer <access_token>`
- **Success Response:**

```json
{
  "message": "Successfully logged out"
}
```

### 3. Token Rotation Refresh

- **Endpoint:** `POST /api/v1/auth/refresh`
- **Request Payload (`RefreshTokenRequest`):**

```json
{
  "refresh_token": "a1b2c3d4..."
}
```

- **Success Response (`TokenResponse`):** Returns new access/refresh tokens.

### 4. Forgot Password Recovery

- **Endpoint:** `POST /api/v1/auth/forgot-password`
- **Request Payload (`ForgotPasswordRequest`):**

```json
{
  "email": "admin@aibios.com"
}
```

- **Success Response:**

```json
{
  "message": "If the email is registered, a password reset link has been dispatched"
}
```

### 5. Reset Password Confirmation

- **Endpoint:** `POST /api/v1/auth/reset-password`
- **Request Payload (`ResetPasswordRequest`):**

```json
{
  "token": "recovery_token_string",
  "new_password": "securenewpassword123"
}
```

- **Success Response:**

```json
{
  "message": "Password updated successfully"
}
```

### 6. User Profile Fetch

- **Endpoint:** `GET /api/v1/auth/me`
- **Headers:** `Authorization: Bearer <access_token>`
- **Success Response (`UserResponse`):**

```json
{
  "id": "superadmin-uuid-placeholder-123456",
  "organization_id": "demo-org-uuid-placeholder-123456",
  "first_name": "Admin",
  "last_name": "Super",
  "email": "admin@aibios.com",
  "phone": null,
  "status": "active",
  "role_id": "super_admin",
  "timezone": "UTC",
  "language": "en",
  "created_at": "2026-07-07T10:17:56.379688",
  "updated_at": "2026-07-07T10:17:56.379688",
  "last_login": "2026-07-07T10:17:56.379688"
}
```
