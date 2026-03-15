---
description: Multi-tenant isolation rules
globs: ["backend/**/*.py"]
---

# Multi-Tenant Rules

Tabot is a multi-tenant platform. Every company's data MUST be isolated.

1. Every database table that holds company data MUST have a `company_id` column
2. Every query MUST filter by `company_id` — no exceptions
3. API endpoints that access company data must extract company_id from JWT claims
4. Webhook endpoints identify company by phone_number_id or ig_account_id lookup
5. Knowledge base embeddings are scoped by company_id in vector search
6. Redis keys must be namespaced by company: `tabot:{company_id}:{key}`
7. File uploads (images, docs) must be stored in company-specific paths
8. Never return data from one company in another company's API response
9. Admin endpoints (super-admin) are separate and require elevated auth
