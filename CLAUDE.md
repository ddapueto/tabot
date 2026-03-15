# Tabot — Asistente IA de Ventas Multicanal

## Que es Tabot
Bot de ventas inteligente para empresas. WhatsApp Business + Instagram + Web.
IA especializada en el negocio del cliente, CRM integrado, follow-ups automaticos.
Nombre: "Ta" (uruguayo: "dale, listo") + "bot". El bot que dice dale.

## Stack Tecnico
- **Backend**: Python 3.12 + FastAPI + Celery + Redis
- **DB**: PostgreSQL 16 + pgvector (embeddings para RAG)
- **IA**: Claude API (Sonnet para mensajes, Haiku para clasificacion)
- **WhatsApp**: Meta Cloud API oficial (no Baileys, no Evolution API)
- **Instagram**: Meta Graph API + Webhooks
- **Frontend**: SvelteKit + Svelte 5 (runes) + Tailwind v4
- **Deploy**: Docker Compose + Caddy (HTTPS) + VPS

## Estructura del Proyecto
```
tabot/
├── backend/app/          # FastAPI application
│   ├── api/webhooks/     # WhatsApp + Instagram webhook handlers
│   ├── api/              # REST API (leads, catalog, analytics, auth)
│   ├── services/         # Business logic (ai_agent, whatsapp_client, lead_scorer)
│   ├── models/           # SQLAlchemy models
│   ├── schemas/          # Pydantic schemas
│   ├── tasks/            # Celery async tasks (follow-ups, notifications)
│   └── migrations/       # Alembic migrations
├── frontend/src/         # SvelteKit dashboard
│   ├── routes/           # Pages (leads, conversations, catalog, analytics)
│   └── lib/              # Stores, components
├── docs/                 # Architecture docs, API specs
└── .claude/              # Claude Code config (agents, skills, rules)
```

## Reglas de Desarrollo
- Idioma del codigo: ingles (variables, funciones, clases)
- Idioma de la UI y mensajes al usuario: espanol
- Idioma de commits y PRs: espanol
- Tests obligatorios para cada feature (pytest backend, vitest frontend)
- Cada PR debe tener issue asociado
- Branch naming: `feat/issue-N-descripcion`, `fix/issue-N-descripcion`
- No mockear la DB en tests — usar testcontainers o DB de test real
- Nunca hardcodear tokens o API keys — usar .env
- Preferir editar archivos existentes a crear nuevos
- Schema changes via Alembic migrations (nunca ALTER directo)
- Max 500 lineas por archivo — si crece, splitear

## Convenciones
- FastAPI routers en `api/`, logica en `services/`
- Pydantic schemas separados de SQLAlchemy models
- Async everywhere (async def, await, asyncpg)
- Type hints obligatorios en Python
- Svelte 5 runes ($state, $derived, $effect) — no stores legacy
- Tailwind: dark theme default, glassmorphism style

## Variables de Entorno Requeridas
```
# Meta APIs
META_VERIFY_TOKEN=         # Webhook verification
META_APP_SECRET=           # HMAC validation
WHATSAPP_PHONE_NUMBER_ID=  # Phone number ID
WHATSAPP_ACCESS_TOKEN=     # Permanent token
INSTAGRAM_ACCOUNT_ID=      # IG Business Account

# Database
DATABASE_URL=postgresql+asyncpg://tabot:tabot@localhost:5432/tabot

# Redis
REDIS_URL=redis://localhost:6379/0

# AI
ANTHROPIC_API_KEY=         # Claude API

# App
SECRET_KEY=                # JWT signing
ENVIRONMENT=development    # development|staging|production
```

## Como correr el proyecto
```bash
# Development
docker compose up -d postgres redis
cd backend && uv run uvicorn app.main:app --reload --port 8000
cd frontend && npm run dev

# Full stack con Docker
docker compose up -d
```

## Agentes disponibles
Ver `.claude/agents/` — cada agente tiene su dominio:
- `architect`: diseno de sistema y decisiones tecnicas
- `backend`: desarrollo FastAPI, DB, servicios
- `frontend`: desarrollo SvelteKit, componentes, stores
- `ai-engineer`: agente de ventas IA, RAG, tools, prompts
- `integrations`: WhatsApp Cloud API, Instagram Graph API, webhooks
- `qa`: tests, CI/CD, calidad
- `growth`: features de producto, metricas, optimizacion

## Skills disponibles
Ver `.claude/commands/` — shortcuts para tareas comunes
