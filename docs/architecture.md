# Arquitectura de Tabot

## Vision
Tabot es una plataforma SaaS multi-tenant de asistencia IA para ventas.
Cualquier empresa conecta sus canales (WhatsApp, Instagram, Web) y Tabot
responde automaticamente, captura leads, hace seguimiento y optimiza conversiones.

## Diagrama General

```
                    ┌─────────────────────┐
                    │    Meta Platform     │
                    │                      │
     WhatsApp ──────│── Cloud API ─────────│
     Business       │                      │
                    │                      │
     Instagram ─────│── Graph API ─────────│
     DMs/Comments   │                      │
                    └──────────┬───────────┘
                               │ Webhooks (HTTPS POST)
                               ▼
                    ┌─────────────────────┐
                    │   Caddy (HTTPS)     │
                    │   Reverse Proxy     │
                    └──────────┬──────────┘
                               │
                    ┌──────────▼──────────┐
                    │      FastAPI        │
                    │                     │
                    │  /webhooks/*        │◄── Mensajes entrantes
                    │  /api/*             │◄── Dashboard API
                    │  /api/catalog/*     │◄── Gestion catalogo
                    │  /api/knowledge/*   │◄── Knowledge base
                    └──┬──────┬───────┬───┘
                       │      │       │
             ┌─────────┘      │       └──────────┐
             ▼                ▼                  ▼
       ┌──────────┐    ┌──────────┐      ┌────────────┐
       │PostgreSQL│    │  Redis   │      │   Celery    │
       │ +pgvector│    │          │      │  Workers    │
       │          │    │ - sesion │      │             │
       │ - leads  │    │ - cache  │      │ - follow-up │
       │ - chats  │    │ - rate   │      │ - templates │
       │ - catalog│    │   limit  │      │ - reportes  │
       │ - kb     │    │ - pubsub │      │ - scoring   │
       │ - users  │    │          │      │ - kb ingest │
       └──────────┘    └──────────┘      └──────┬─────┘
                                                │
                                        ┌───────▼──────┐
                                        │  Claude API  │
                                        │  (Anthropic) │
                                        │              │
                                        │  Tools:      │
                                        │  - catalogo  │
                                        │  - precios   │
                                        │  - agenda    │
                                        │  - faq       │
                                        │  - lead      │
                                        │  - handoff   │
                                        └──────────────┘
```

## Componentes

### Backend (FastAPI)
- **Webhooks**: Reciben mensajes de WhatsApp e Instagram, validan HMAC, normalizan
- **API REST**: CRUD de leads, catalogo, conversaciones, analytics, auth
- **Services**: Logica de negocio (AI agent, WhatsApp client, lead scorer, follow-up engine)
- **Celery Tasks**: Tareas asincronas (follow-ups, notificaciones, ingestion KB, reportes)

### Base de Datos (PostgreSQL + pgvector)
- Multi-tenant: toda tabla tiene `company_id`
- pgvector: embeddings para busqueda semantica en catalogo y knowledge base
- HNSW index para queries rapidos de vectores

### Cache y Colas (Redis)
- Sesiones de conversacion (ultimos 20 mensajes por lead)
- Cache de config de empresa
- Rate limiting por empresa
- Cola de mensajes para Celery

### IA (Claude API)
- System prompt dinamico por empresa (personalidad, dominio, reglas)
- Function calling con tools genericos (buscar, cotizar, agendar, escalar)
- RAG: contexto del catalogo y knowledge base via pgvector
- Tracking de costos por mensaje

### Knowledge Base
- Fuentes: catalogo, documentos, Instagram posts, website, FAQ, conversaciones
- Auto-ingestion: Instagram posts capturados via webhook → embeddings automaticos
- Busqueda semantica para enriquecer respuestas del agente

### Frontend (SvelteKit)
- Dashboard admin para gestionar leads, catalogo, conversaciones
- Analytics de conversion, tiempos de respuesta, productos populares
- Configuracion de empresa y agente IA

### Infraestructura
- Docker Compose para todos los servicios
- Caddy como reverse proxy con HTTPS automatico
- VPS (Hetzner/DigitalOcean, ~$20-40/mes)

## Flujo de un Mensaje

1. Cliente envia mensaje por WhatsApp/Instagram
2. Meta envia webhook POST a nuestro servidor
3. FastAPI valida firma HMAC-SHA256
4. Normaliza mensaje a formato interno (`InboundMessage`)
5. Busca/crea lead por sender_id del canal
6. Busca/crea conversacion activa
7. Guarda mensaje inbound en DB
8. Si `ai_enabled=true` en la conversacion:
   a. Carga contexto: historial (Redis) + datos lead (PG) + catalogo relevante (pgvector)
   b. Envia a Claude con system prompt + tools
   c. Si Claude llama un tool → ejecuta → retroalimenta
   d. Obtiene respuesta final
9. Envia respuesta por el canal correspondiente (WhatsApp Cloud API / Instagram API)
10. Guarda mensaje outbound en DB
11. Actualiza lead: score, last_message_at, datos extraidos
12. Si aplica: programa follow-up en Celery

## Decisiones Tecnicas

| Decision | Eleccion | Alternativas descartadas | Razon |
|----------|----------|--------------------------|-------|
| API WhatsApp | Cloud API oficial | Baileys, Evolution API | Estabilidad, sin riesgo de ban, gratis para servicio |
| AI Model | Claude (Sonnet/Haiku) | GPT-4o, modelo local | Superior en espanol, mejor function calling, pricing competitivo |
| Vector DB | pgvector (en PostgreSQL) | Pinecone, Weaviate, Qdrant | Una sola DB, suficiente para <10K items por empresa |
| Task Queue | Celery + Redis | APScheduler, dramatiq | Robusto, reintentos, probado en produccion |
| Frontend | SvelteKit + Svelte 5 | React, Next.js | Mas rapido de desarrollar, menos boilerplate |
| Auth | JWT (access + refresh) | Session cookies | Mejor para SPA + API |
| Deploy | Docker Compose + VPS | Kubernetes, serverless | Simple, barato, suficiente para MVP |
| Multi-tenant | Row-level (company_id) | Schema-per-tenant, DB-per-tenant | Mas simple, escala bien hasta miles de empresas |
