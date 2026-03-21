# Tabot — Tech Steering

## Stack y justificación

| Capa | Tecnología | Por qué |
|------|------------|---------|
| Backend | Python 3.12 + FastAPI | Async, tipado, rápido de desarrollar |
| DB | PostgreSQL 16 + pgvector | Una sola DB para todo (relacional + vectores) |
| Cache/Queue | Redis | Celery broker + cache + SSE pubsub |
| Tasks | Celery + Beat | Follow-ups, KB maintenance, notificaciones |
| AI (dev) | Groq (llama-3.3-70b) | Gratis, rápido, bueno en español |
| AI (prod) | Anthropic Claude Sonnet | Superior en razonamiento y español |
| WhatsApp | Meta Cloud API | Oficial, gratis para servicio, estable |
| Instagram | Meta Graph API | Mismo ecosistema Meta |
| Frontend | SvelteKit + Svelte 5 | Rápido, ligero, runes moderno |
| CSS | Tailwind v4 | Utilidades, dark theme, design tokens |
| Auth | JWT + PBKDF2-SHA256 | Stateless, stdlib Python (sin bcrypt issues) |
| Deploy | Docker Compose + Caddy | Simple, HTTPS auto, barato |

## Constraints técnicos

### MUST
- Multi-tenant: TODA query filtra por company_id (del JWT, no URL)
- Webhooks Meta responden < 5s (o Meta reintenta/desconecta)
- Precios NUNCA se almacenan en KB — siempre del catálogo en tiempo real
- Validador de respuestas corre ANTES de enviar al cliente
- No hardcodear secrets — todo via .env
- HMAC-SHA256 en webhooks (no JWT — Meta no lo soporta)

### SHOULD
- Async everywhere (async def, await)
- Type hints en Python
- Svelte 5 runes (no stores legacy)
- Tests con DB real (no mocks)
- Max 500 líneas por archivo

### SHOULD NOT
- No usar ORM lazy loading (causa N+1)
- No bcrypt (incompatible con Python 3.12 passlib)
- No Baileys/Evolution API para WhatsApp (riesgo de ban)
- No chart libraries pesadas (SVG manual para analytics)

## Patrones arquitectónicos

### Request flow
```
Meta webhook → HMAC validate → normalize message → find/create lead
→ load conversation history → build AI context (catalog + KB) →
generate response → validate response (prices, forbidden) →
send via channel API → save to DB → notify SSE → update score
```

### Multi-tenant isolation
```
JWT token → extract company_id → deps.py:get_current_company_id
→ ALL queries WHERE company_id = X
```

### KB lifecycle
```
Create → active (priority 1-10, channels) → used (times_used++)
→ expires? → auto-deactivate | stale 90d? → flag for review
```

### AI provider abstraction
```
config.ai_provider == "groq" → _generate_groq() (inline RAG, no tools)
config.ai_provider == "anthropic" → _generate_anthropic() (function calling)
```

## Puertos (desarrollo local)
- PostgreSQL: **5435** (no 5432 — hay PG local)
- Redis: 6379
- Backend: 8001
- Frontend: 5173+ (Vite asigna disponible)

## Dependencias críticas
- groq>=1.1.1 (AI dev)
- anthropic>=0.42.0 (AI prod)
- sqlalchemy[asyncio]>=2.0.36 (ORM async)
- pgvector>=0.3.6 (embeddings)
- python-jose[cryptography] (JWT)
- httpx (HTTP client para APIs Meta)

## Testing
- Framework: pytest + pytest-asyncio + httpx AsyncClient
- DB: PostgreSQL real en Docker (no mocks)
- Pattern: onboarding fixture → auth headers → test endpoint
- Coverage target: 80% backend, 70% frontend
