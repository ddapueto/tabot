---
description: Security rules for all code in the project
globs: ["**/*.py", "**/*.ts", "**/*.svelte"]
---

# Security Rules

1. NEVER hardcode API keys, tokens, or secrets — always use environment variables
2. ALWAYS verify HMAC-SHA256 signature on webhook endpoints before processing
3. ALWAYS use SQLAlchemy ORM for queries — never raw SQL strings
4. ALWAYS add company_id filter on ALL database queries (tenant isolation)
5. ALWAYS validate input with Pydantic schemas before processing
6. ALWAYS sanitize user content before rendering in frontend (XSS prevention)
7. ALWAYS use parameterized queries if raw SQL is ever needed
8. NEVER log sensitive data (tokens, passwords, full message content in production)
9. ALWAYS use HTTPS in production (Caddy handles this)
10. JWT tokens must expire (max 24h for dashboard, refresh token pattern)
