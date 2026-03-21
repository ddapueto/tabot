# Tabot — Asistente IA de Ventas Multicanal

## Que es Tabot
Plataforma SaaS multi-tenant de asistente IA para ventas. Cualquier empresa conecta
WhatsApp Business + Instagram y Tabot responde automaticamente, captura leads,
hace seguimiento, y optimiza conversiones. Domain-agnostic (sirve para cualquier industria).
Nombre: "Ta" (uruguayo: "dale, listo") + "bot".

## Estado del Proyecto
- Fases 1-4: COMPLETADAS
- Sprint consolidacion: COMPLETADO (auth, real-time, inbox profesional)
- Sprint hardening: COMPLETADO (KB lifecycle, validador precios, onboarding, follow-ups DB)
- Madurez: 7/10 — MVP funcional, falta deploy + tests + WhatsApp real
- Repo: github.com/ddapueto/tabot (public)

## Stack Tecnico
- **Backend**: Python 3.12 + FastAPI + Celery + Redis
- **DB**: PostgreSQL 16 + pgvector (embeddings para RAG)
- **IA**: Groq (llama-3.3-70b, default dev) O Anthropic Claude (produccion)
- **IA Config**: `AI_PROVIDER=groq|anthropic` en .env
- **WhatsApp**: Meta Cloud API oficial
- **Instagram**: Meta Graph API + Webhooks
- **Frontend**: SvelteKit + Svelte 5 (runes) + Tailwind v4
- **Auth**: JWT (PBKDF2-SHA256, no bcrypt)
- **Deploy**: Docker Compose + Caddy (HTTPS) + VPS

## Estructura del Proyecto
```
tabot/
├── backend/app/
│   ├── api/                  # 13 routers REST
│   │   ├── webhooks/         # whatsapp.py, instagram.py (HMAC, no auth)
│   │   ├── auth.py           # register, login, refresh, me (JWT)
│   │   ├── deps.py           # get_current_company_id, require_admin
│   │   ├── leads.py          # CRUD + scoring + stage + handoff
│   │   ├── conversations.py  # list + messages + send + SSE stream
│   │   ├── catalog.py        # CRUD productos
│   │   ├── dashboard.py      # stats agregados
│   │   ├── analytics.py      # funnel, response times, AI stats, top products
│   │   ├── follow_ups.py     # sequences + pending + schedule + cancel
│   │   ├── broadcasts.py     # preview + send masivo
│   │   ├── settings_api.py   # company config + AI config + KB CRUD + promos
│   │   ├── onboarding.py     # POST /setup (crear empresa en 1 paso)
│   │   └── health.py
│   ├── services/             # 9 servicios
│   │   ├── ai_agent.py       # Groq/Anthropic, system prompt dinamico, inline RAG
│   │   ├── ai_tools.py       # 5 tools function calling + TOOLS_OPENAI format
│   │   ├── message_handler.py # Webhook → lead → IA → respuesta → SSE
│   │   ├── whatsapp_client.py # Cloud API: text, image, buttons
│   │   ├── instagram_client.py # Graph API: DM, comment reply
│   │   ├── lead_scorer.py    # Keywords + scoring rules + stage transitions
│   │   ├── kb_manager.py     # Lifecycle, auto-sync, expiracion, channel targeting
│   │   ├── follow_up_engine.py # DB-backed sequences + execution
│   │   └── response_validator.py # Price check + forbidden patterns + escalation
│   ├── models/               # 8 SQLAlchemy models (multi-tenant, company_id)
│   ├── schemas/              # Pydantic v2 schemas
│   ├── tasks/                # 3 Celery task modules
│   │   ├── follow_ups.py     # execute_pending (5min), check_stale (9am)
│   │   ├── kb_maintenance.py # expire_items (1h), flag_stale (8am)
│   │   └── notifications.py  # alert_hot_lead (score>=76)
│   ├── migrations/           # Alembic (2 migrations)
│   └── scripts/seed_demo.py  # 25 leads, 70 msgs, 24 KB items, 3 users
├── frontend/src/
│   ├── routes/               # 9 pages
│   │   ├── +layout.svelte    # Sidebar colapsable (Cmd+B), theme switcher, auth guard
│   │   ├── +page.svelte      # Dashboard: stats, pipeline, priority bars, leads recientes
│   │   ├── login/            # Glass card, register/login
│   │   ├── leads/            # Lista + filtros + detalle + handoff + reactivar IA
│   │   ├── conversations/    # Inbox 3 columnas, chat WhatsApp-style, SSE real-time
│   │   ├── catalog/          # Cards con specs, features, precios
│   │   ├── follow-ups/       # Secuencias + follow-ups activos
│   │   ├── analytics/        # Funnel, response times, AI stats, top products, scoring dist
│   │   └── settings/         # Config empresa + IA + KB manager + promos
│   └── lib/
│       ├── api.ts            # HTTP client con JWT, auto-redirect 401
│       ├── theme.svelte.ts   # 3 temas: Ocean, Midnight Blue, Warm Dark
│       └── utils.ts          # formatters, badges, priority/channel config
├── docs/                     # 8 docs (architecture, DB, AI, KB, roadmap, competitive)
└── .claude/                  # 7 agents, 6 skills, 5 rules
```

## Auth
- Todos los endpoints de negocio requieren JWT (via `deps.py:get_current_company_id`)
- company_id se extrae del token, NO de la URL
- Webhooks usan HMAC (no JWT)
- SSE usa company_id en URL (EventSource no envia headers)
- Password hashing: PBKDF2-SHA256 (stdlib, no bcrypt)

## KB Inteligente
- Precios NUNCA en KB — siempre del catalogo en real-time
- Promos con expires_at — se desactivan automaticamente
- Auto-sync: producto creado/editado → KB entry generada
- Max 50 items activos por empresa
- items sin uso 90d → flagged para review
- Canales: cada item define en que canales se usa (whatsapp, instagram, web)

## Validador de Respuestas (response_validator.py)
- Capa 1: precios correctos vs catalogo (regex + DB check + auto-correccion)
- Capa 2: patrones prohibidos ("te garantizo", comparaciones negativas)
- Capa 3: keywords escalacion ("demanda", "estafa") → handoff automatico
- Se ejecuta ANTES de enviar la respuesta al cliente

## DB Port
PostgreSQL Docker en puerto **5435** (no 5432, hay otro PG local)

## Reglas de Desarrollo
- Codigo en ingles, UI en espanol, commits en espanol
- Tests: pytest (backend), vitest (frontend)
- No mockear DB — test real
- Nunca hardcodear tokens — .env
- Schema changes via Alembic
- Max 500 lineas por archivo

## Como correr
```bash
docker compose up -d                          # PG (5435) + Redis (6379)
cd backend && uv run python scripts/seed_demo.py  # Cargar demo
cd backend && uv run uvicorn app.main:app --port 8001 --reload
cd frontend && npm run dev                    # Puerto 5173+
# Login: martin@casasdelbosque.uy / demo1234
```

## Agentes: ver .claude/agents/
architect, backend, frontend, ai-engineer, integrations, qa, growth

## Skills: ver .claude/commands/
test, lint, review, new-feature, deploy, kb-ingest
