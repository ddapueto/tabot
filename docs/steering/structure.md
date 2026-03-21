# Tabot — Structure Steering

## Organización del código

### Backend (`backend/app/`)

```
app/
├── main.py              # FastAPI app, middleware, router includes
├── config.py            # pydantic-settings (28 vars)
├── database.py          # AsyncEngine + session factory + get_db
├── celery_app.py        # Celery config + beat schedule
│
├── api/                 # 13 routers (thin — solo HTTP, no lógica)
│   ├── deps.py          # Auth dependencies (get_current_company_id, require_admin)
│   ├── auth.py          # register, login, refresh, me
│   ├── leads.py         # CRUD + stage + handoff + reactivate
│   ├── conversations.py # list + messages + send + SSE stream
│   ├── catalog.py       # CRUD productos
│   ├── dashboard.py     # stats agregados
│   ├── analytics.py     # funnel, times, AI stats, products, scoring
│   ├── follow_ups.py    # sequences + pending + schedule + cancel
│   ├── broadcasts.py    # preview + send masivo
│   ├── settings_api.py  # company + AI config + KB CRUD + promos + health
│   ├── onboarding.py    # POST /setup (empresa + user en 1 paso)
│   ├── health.py        # health check
│   └── webhooks/
│       ├── whatsapp.py  # GET verify + POST receive (HMAC)
│       └── instagram.py # GET verify + POST receive (DMs, comments, content)
│
├── services/            # 9 servicios (lógica de negocio)
│   ├── ai_agent.py      # generate_response() → Groq o Anthropic
│   ├── ai_tools.py      # TOOLS (Anthropic) + TOOLS_OPENAI (Groq) + execute_tool()
│   ├── message_handler.py # handle_inbound_message() — el flujo central
│   ├── whatsapp_client.py # send_text/image/buttons via Cloud API
│   ├── instagram_client.py # send_dm, reply_to_comment via Graph API
│   ├── lead_scorer.py   # extract_signals, update_score, change_stage
│   ├── kb_manager.py    # sync_product, create_promo, deactivate_expired, get_relevant_kb
│   ├── follow_up_engine.py # schedule, execute, cancel (DB-backed)
│   └── response_validator.py # validate_response (prices, forbidden, escalation)
│
├── models/              # 8 SQLAlchemy models (Base en database.py)
│   ├── __init__.py      # Re-exports all models
│   ├── company.py       # Company (tenant root)
│   ├── lead.py          # Lead + LeadStageHistory
│   ├── product.py       # Product + ProductOption
│   ├── conversation.py  # Conversation
│   ├── message.py       # Message
│   ├── knowledge.py     # KnowledgeItem (lifecycle: type, expires, priority, channels)
│   ├── user.py          # User (roles: admin, seller)
│   └── follow_up.py     # FollowUp + FollowUpSequence
│
├── schemas/             # Pydantic v2 schemas
│   ├── catalog.py       # ProductCreate, ProductUpdate, ProductResponse
│   ├── conversation.py  # ConversationResponse, MessageResponse
│   └── lead.py          # LeadResponse, LeadUpdate
│
├── tasks/               # Celery tasks (async background jobs)
│   ├── follow_ups.py    # execute_pending (5min), check_stale (9am daily)
│   ├── kb_maintenance.py # expire_items (1h), flag_stale (8am daily)
│   └── notifications.py # alert_hot_lead (score>=76)
│
├── migrations/          # Alembic
│   ├── env.py           # Async migration runner
│   └── versions/        # Migration files
│
└── scripts/
    └── seed_demo.py     # 25 leads, 70 msgs, 24 KB items, 6 products, 3 users
```

### Frontend (`frontend/src/`)

```
src/
├── app.css              # Design tokens (@theme), animations, bubbles, glass, utilities
├── app.html             # HTML template (Inter font, lang=es)
├── app.d.ts             # TypeScript ambient declarations
│
├── lib/
│   ├── api.ts           # HTTP client: JWT management, all API calls, SSE connection
│   ├── theme.svelte.ts  # 3 themes (Ocean, Midnight, Warm) + persistence + apply
│   ├── utils.ts         # formatTime/Date/Relative, initials, stageBadge, priorityConfig, channelConfig
│   └── index.ts         # Re-exports
│
└── routes/
    ├── +layout.svelte    # Sidebar (colapsable Cmd+B), nav, theme picker, auth guard, logout
    ├── +page.svelte      # Dashboard: stat cards, pipeline, priority bars, recent leads
    ├── login/+page.svelte # Glass card, register/login, company ID
    ├── leads/+page.svelte # Lista + filtros + detalle panel + handoff + reactivar
    ├── conversations/+page.svelte # Inbox 3 cols, WhatsApp bubbles, send, SSE, contact panel
    ├── catalog/+page.svelte # Product cards con specs, features, precios
    ├── follow-ups/+page.svelte # Secuencias + follow-ups activos
    ├── analytics/+page.svelte # Funnel, times, AI stats, top products, scoring dist
    └── settings/+page.svelte # Company + AI config + KB manager + promos + sync
```

### Documentación (`docs/`)

```
docs/
├── architecture.md       # Diagrama sistema, componentes, flujo, decisiones
├── database-schema.md    # SQL completo con indexes
├── ai-agent-design.md    # System prompt, tools, flows, scoring
├── knowledge-base-design.md # Fuentes, pipeline, RAG
├── roadmap.md            # Fases 1-4 + futuro
├── competitive-analysis.md # Mapa competidores, ventajas, pricing
├── issues-summary.md     # 36 issues por milestone
├── steering/             # Contexto persistente (product, tech, structure)
└── specs/                # Especificaciones de implementación
```

### Claude Code (`.claude/`)

```
.claude/
├── agents/       # 7 agentes con expertise específico
├── commands/     # 6 skills/shortcuts
└── rules/        # 5 reglas que se aplican siempre
```

## Convenciones de naming

| Tipo | Convención | Ejemplo |
|------|-----------|---------|
| Archivos Python | snake_case | `lead_scorer.py` |
| Clases Python | PascalCase | `KnowledgeItem` |
| Funciones Python | snake_case async | `async def get_relevant_kb()` |
| Archivos Svelte | PascalCase para componentes, +page para rutas | `+page.svelte` |
| Variables Svelte | camelCase con runes | `let loading = $state(true)` |
| API routes | kebab-case | `/api/follow-ups/`, `/api/kb-health` |
| DB tables | snake_case plural | `knowledge_items`, `follow_ups` |
| DB columns | snake_case | `company_id`, `last_message_at` |
| CSS classes | Tailwind utilities | `bg-surface border-theme-subtle` |
| Git branches | `feat/spec-N-slug` o `fix/issue-N-slug` | `feat/spec-01-tests` |
| Commits | `tipo: descripción en español` | `feat: agregar tests de auth` |

## Imports (orden)

### Python
```python
# 1. stdlib
import uuid
from datetime import datetime

# 2. third-party
from fastapi import APIRouter, Depends
from sqlalchemy import select

# 3. local
from app.database import get_db
from app.models.lead import Lead
from app.api.deps import get_current_company_id
```

### Svelte/TypeScript
```typescript
// 1. Svelte
import { onMount } from 'svelte';
import { goto } from '$app/navigation';

// 2. Local
import { api } from '$lib/api';
import { formatTime, initials } from '$lib/utils';
```
