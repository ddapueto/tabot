---
description: Rules for the AI sales agent implementation
globs: ["backend/app/services/ai_*.py", "backend/app/services/knowledge*.py"]
---

# AI Agent Rules

1. The AI agent is DOMAIN-AGNOSTIC — it adapts to any business type via company config
2. System prompt is dynamically assembled per company (never hardcoded for one industry)
3. The agent MUST use tools for factual data (prices, availability, specs) — never hallucinate
4. RAG context is ALWAYS scoped by company_id
5. Conversation history is stored in Redis (last 20 messages) + PostgreSQL (permanent)
6. If the AI is uncertain, it should offer to check with the team — never guess
7. Handoff to human must be smooth: notify seller, pause AI, preserve context
8. All AI costs (tokens in/out, model used) must be tracked per message
9. Knowledge base updates trigger re-embedding automatically
10. Instagram content captured via webhooks auto-feeds into knowledge base
