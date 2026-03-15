# Issues y Milestones — Resumen

## Milestones

| # | Milestone | Due Date | Issues |
|---|-----------|----------|--------|
| 1 | Fase 1 — Bot Responde | 2026-04-01 | #1 - #8 |
| 2 | Fase 2 — CRM + Dashboard | 2026-04-15 | #9 - #18 |
| 3 | Fase 3 — Follow-ups + Instagram | 2026-05-01 | #19 - #27 |
| 4 | Fase 4 — Analytics + Optimizacion | 2026-05-15 | #28 - #36 |

## Fase 1 — Bot Responde (8 issues)

| # | Issue | Labels |
|---|-------|--------|
| 1 | Setup proyecto: FastAPI + PostgreSQL + Docker Compose | backend, infra |
| 2 | Modelos de base de datos: companies, leads, conversations, messages | backend |
| 3 | Webhook WhatsApp Cloud API: recibir y enviar mensajes de texto | backend, integrations |
| 4 | Integracion Claude API: agente de ventas con system prompt dinamico | backend, ai |
| 5 | Catalogo de productos/servicios: modelo + CRUD + carga inicial | backend |
| 6 | Tools del agente IA: buscar_producto, consultar_precio, consultar_faq | backend, ai |
| 7 | Knowledge Base: modelo, embeddings y busqueda semantica con pgvector | backend, ai, knowledge-base |
| 8 | Flujo end-to-end: mensaje WhatsApp → IA → respuesta | backend, integrations, ai |

## Fase 2 — CRM + Dashboard (10 issues)

| # | Issue | Labels |
|---|-------|--------|
| 9 | Lead scoring automatico: reglas + clasificacion IA | backend, ai |
| 10 | Pipeline de ventas: etapas, transiciones, historial | backend |
| 11 | Handoff a humano: pausar IA, notificar vendedor | backend, integrations |
| 12 | Auth JWT: login, registro, roles (admin/seller) | backend |
| 13 | Setup frontend: SvelteKit + Tailwind + proxy a backend | frontend, infra |
| 14 | Dashboard principal: estadisticas y leads recientes | frontend |
| 15 | Vista de leads: lista + detalle + pipeline kanban | frontend |
| 16 | Visor de conversaciones: chat estilo WhatsApp | frontend |
| 17 | Mensajes interactivos: botones y listas en WhatsApp | backend, integrations |
| 18 | Envio de imagenes y galeria desde el bot | backend, integrations |

## Fase 3 — Follow-ups + Instagram (9 issues)

| # | Issue | Labels |
|---|-------|--------|
| 19 | Celery setup: workers + beat para tareas programadas | backend, infra |
| 20 | Secuencias de follow-up: motor de ejecucion automatica | backend |
| 21 | Templates de WhatsApp: creacion y envio fuera de ventana 24h | backend, integrations |
| 22 | Webhook Instagram: recibir DMs | backend, integrations |
| 23 | Webhook Instagram: comentarios → respuesta + DM lead capture | backend, integrations, ai |
| 24 | Auto-captura Instagram: posts y stories → knowledge base | backend, integrations, knowledge-base |
| 25 | Alertas al vendedor: notificacion WhatsApp de lead caliente | backend, integrations |
| 26 | Gestion de follow-ups en dashboard | frontend |
| 27 | Configuracion de empresa en dashboard | frontend |

## Fase 4 — Analytics + Optimizacion (9 issues)

| # | Issue | Labels |
|---|-------|--------|
| 28 | Metricas diarias: agregacion automatica | backend |
| 29 | Dashboard analytics: graficos de conversion y performance | frontend |
| 30 | Gestion de catalogo en dashboard: CRUD con fotos | frontend |
| 31 | Knowledge base manager: ver, agregar, editar items | frontend, knowledge-base |
| 32 | Agenda de visitas: programar, confirmar, tracking | backend, frontend |
| 33 | Reportes automaticos: resumen semanal por WhatsApp/email | backend |
| 34 | Broadcast masivo: enviar oferta a segmento de leads | backend, integrations, frontend |
| 35 | Calculadora de presupuesto: tool generico del agente IA | backend, ai |
| 36 | CI/CD: GitHub Actions (lint, test, build, deploy) | infra |

## Labels

| Label | Color | Uso |
|-------|-------|-----|
| fase-1 | verde | Milestone 1 |
| fase-2 | azul | Milestone 2 |
| fase-3 | rojo | Milestone 3 |
| fase-4 | violeta | Milestone 4 |
| backend | amarillo | FastAPI, DB, servicios |
| frontend | salmon | SvelteKit, componentes |
| ai | purpura | IA, RAG, prompts |
| integrations | celeste | WhatsApp, Instagram APIs |
| infra | verde claro | Docker, CI/CD, deploy |
| knowledge-base | lila | Knowledge base, ingestion |

## Agentes Claude por Issue

| Agente | Issues |
|--------|--------|
| @architect | #1, #2 |
| @backend | #1-#12, #17-#21, #25, #28, #32-#35 |
| @frontend | #13-#16, #26-#27, #29-#32, #34 |
| @ai-engineer | #4, #6-#7, #9, #23-#24, #35 |
| @integrations | #3, #8, #11, #17-#18, #21-#25, #34 |
| @qa | #36 |
| @growth | (Fase 5 — futuro) |
