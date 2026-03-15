---
description: Performance rules for webhook and API endpoints
globs: ["backend/app/api/**/*.py"]
---

# Performance Rules

Webhook endpoints must respond FAST — Meta expects < 5 seconds or will retry.

1. Webhook handler: acknowledge immediately (return 200), process async
2. AI response generation happens in background (Celery task or asyncio.create_task)
3. Database queries must use proper indexes (see models for index definitions)
4. Avoid N+1 queries — use joinedload/selectinload for relationships
5. Cache frequently accessed data in Redis (company config, product catalog summaries)
6. pgvector queries: limit to top 5 results, use HNSW index for speed
7. Message sending: retry with exponential backoff on failure
8. Bulk operations (broadcasts): use Celery tasks, not synchronous loops
