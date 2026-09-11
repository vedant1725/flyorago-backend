# FlyoraGo Backend Security Architecture & Policy

This document defines the security architecture, policies, controls, and deployment guidelines for the FlyoraGo backend API.

---

## 1. Authentication Model
FlyoraGo employs a **Zero-Trust Token-Based Authentication model** using JSON Web Tokens (JWT) via `django-rest-framework-simplejwt`.
* **Access Tokens**: Short-lived (`60 minutes`) passed via HTTP headers (`Authorization: Bearer <token>`).
* **Refresh Tokens**: Issued with a `7-day` lifetime for session renewal.
* **Cookie Security**: SameSite Lax, HttpOnly, and secure cookie variables enabled by default when `DEBUG=False`.

---

## 2. Role-Based Access Control (RBAC)
Every endpoint checks authentication and enforces role validation on the backend. Client-side state is completely ignored for authorization.
* **Roles**: `user`, `sender`, `traveler`, `agency`, `admin`, `superadmin`.
* **Authorization Checks**: Custom permission classes (`IsSystemAdmin`, `IsKYCApproved`) ensure that standard users cannot perform actions matching administrative paths.

---

## 3. Object-Level Access (IDOR Protection)
No client-supplied `userId`, `bookingId`, or `luggageId` is trusted without validation.
* **Detail Views**: Detail retrieve querysets filter by `Q(sender=request.user) | Q(traveler=request.user)`, preventing users from accessing tracking details of bookings they do not own or carry.
* **State Operations**: Accept, reject, payment confirmations, QR scans, OTP entries, ratings, and disputes verify user relationships before modifying state or initiating database transactions.

---

## 4. OTP Security
One-Time Passwords (OTPs) verify account registration and password resets.
* **Generation**: Utilizes Python's cryptographically secure `secrets` module (`secrets.SystemRandom().randint(100000, 999999)`).
* **Delivery Protection**: Plaintext OTP codes are never logged and are completely omitted from JSON payloads when `settings.DEBUG` is `False`.
* **Lifetime**: Expires strictly after `10 minutes`. Verified OTPs are immediately invalidated.

---

## 5. Password Security
Enforces Django's standard password complexity validation rules during signup and password reset:
* Disallows weak, common, or sequential combinations (e.g., `12345678`, `password`).
* Hashes passwords using PBKDF2 with SHA-256 by default.

---

## 6. Rate Limiting (Throttling)
Protects against brute-force attacks and abuse:
* **Anonymous Clients**: `60 requests / minute`
* **Authenticated Clients**: `120 requests / minute`
* **Sensitive Endpoints** (Login, Signup, OTP, Reset): `5 requests / minute`
* **AI Bot Queries**: `20 requests / minute`

---

## 7. Financial & Payment Integrity
* **Amount Checks**: Transaction amounts are computed and verified server-side.
* **Atomicity**: Wallet updates and payouts run inside `@transaction.atomic` blocks to prevent race conditions or partial transactions.
* **Idempotency**: Prevent double payments or double-clicks from double-charging user wallets.

---

## 8. KYC & Document Protection
* Documents are stored in secure storage spaces.
* Only System Administrators can access the KYC dashboard or execute approvals.

---

## 9. Centralized Security Logging
A structured JSON audit trail is written directly to `logs/security.log`.
* **Events Recorded**: Logins, registrations, OTP requests, wallet transfers, dispute resolutions, and KYC actions.
* **Data Sanitization**: Passwords, OTP codes, and JWT tokens are scrubbed from log data.

---

## 10. Deployment Security Checklist
Ensure these values are configured inside `.env` in production:
* `DEBUG = False`
* `CORS_ALLOW_ALL_ORIGINS = False`
* `ALLOWED_HOSTS = <specific-domain>`
* `SECURE_SSL_REDIRECT = True`
* `SESSION_COOKIE_SECURE = True`
* `CSRF_COOKIE_SECURE = True`
* `SECURE_HSTS_SECONDS = 31536000` (1 year)
* `SECURE_HSTS_INCLUDE_SUBDOMAINS = True`
* `SECURE_HSTS_PRELOAD = True`
* `SECURE_REFERRER_POLICY = 'same-origin'`
