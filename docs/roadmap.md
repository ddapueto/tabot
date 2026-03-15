# Roadmap de Tabot

## Fases de Desarrollo

---

## Fase 1 — Bot Responde (2 semanas)
**Objetivo**: El bot responde por WhatsApp con IA, catalogo y precios. MVP funcional end-to-end.
**Milestone**: `Fase 1 — Bot Responde`
**Deadline**: 2026-04-01

### Issues

| # | Titulo | Labels | Descripcion |
|---|--------|--------|-------------|
| 1 | Setup proyecto: FastAPI + PostgreSQL + Docker Compose | backend, infra | pyproject.toml, FastAPI app, config, database, Docker Compose, Makefile |
| 2 | Modelos de base de datos: companies, leads, conversations, messages | backend | SQLAlchemy models multi-tenant, migracion Alembic inicial |
| 3 | Webhook WhatsApp Cloud API: recibir y enviar mensajes de texto | backend, integrations | GET/POST webhooks, HMAC validation, WhatsApp client, normalizar mensajes |
| 4 | Integracion Claude API: agente de ventas con system prompt dinamico | backend, ai | SalesAgent con Claude, system prompt por empresa, contexto Redis, cost tracking |
| 5 | Catalogo de productos/servicios: modelo + CRUD + carga inicial | backend | Modelo Product generico, CRUD, carga masiva CSV/JSON |
| 6 | Tools del agente IA: buscar_producto, consultar_precio, consultar_faq | backend, ai | Function calling tools, registro de uso, tests |
| 7 | Knowledge Base: modelo, embeddings y busqueda semantica con pgvector | backend, ai, knowledge-base | KnowledgeItem, embeddings, HNSW index, busqueda semantica |
| 8 | Flujo end-to-end: mensaje WhatsApp → IA → respuesta | backend, integrations, ai | Integrar todos los componentes, test E2E |

---

## Fase 2 — CRM + Dashboard (2 semanas)
**Objetivo**: Dashboard admin, lead tracking, scoring, handoff a humano. No se pierde ningun lead.
**Milestone**: `Fase 2 — CRM + Dashboard`
**Deadline**: 2026-04-15

### Issues

| # | Titulo | Labels | Descripcion |
|---|--------|--------|-------------|
| 9 | Setup frontend: SvelteKit + Svelte 5 + Tailwind v4 | frontend, infra | Proyecto SvelteKit, Tailwind dark theme, layout base, proxy a backend |
| 10 | Auth: registro, login JWT, roles (admin/seller) | backend, frontend | JWT access+refresh, register, login, middleware, role-based access |
| 11 | Dashboard principal: stats, leads recientes, actividad | frontend | StatCards, leads recientes, grafico de actividad, conexion a API |
| 12 | Pagina de Leads: listado, filtros, detalle, pipeline kanban | frontend, backend | Lista con filtros (stage, score, canal), vista detalle, pipeline drag-and-drop |
| 13 | Lead scoring automatico: reglas + actualizacion por conversacion | backend, ai | Motor de scoring configurable, actualiza en cada mensaje, alertas por prioridad |
| 14 | Pagina de Conversaciones: chat viewer estilo WhatsApp | frontend, backend | Burbujas de chat, timeline, metadata IA, scroll infinito |
| 15 | Handoff a humano: pausar IA, notificar vendedor, reactivar | backend, integrations | Endpoint escalar, notificacion WhatsApp al vendedor, pausar AI, boton reactivar |
| 16 | Mensajes interactivos: botones y listas en WhatsApp | backend, integrations | Enviar interactive messages (buttons, lists), parsear respuestas interactivas |
| 17 | Envio de imagenes y galeria desde el bot | backend, integrations | Enviar imagenes del catalogo, carruseles, documentos PDF |

---

## Fase 3 — Follow-ups + Instagram (2 semanas)
**Objetivo**: Secuencias de seguimiento automatico, Instagram DMs y comentarios, alertas al vendedor.
**Milestone**: `Fase 3 — Follow-ups + Instagram`
**Deadline**: 2026-05-01

### Issues

| # | Titulo | Labels | Descripcion |
|---|--------|--------|-------------|
| 18 | Celery setup: workers, beat, tareas base | backend, infra | Celery config, Redis broker, beat scheduler, health check task |
| 19 | Follow-up engine: secuencias automaticas multi-dia | backend | FollowUpSequence, programar steps, ejecutar con Celery beat, cancelar si lead responde |
| 20 | Templates WhatsApp: crear, enviar, gestionar aprobacion | backend, integrations | Crear templates via API, enviar fuera de ventana 24h, gestionar estados |
| 21 | Instagram DMs: recibir y responder mensajes directos | backend, integrations | Webhook Instagram messaging, parsear DMs, responder via Graph API |
| 22 | Instagram comentarios: auto-respuesta + captura de lead | backend, integrations | Webhook comments, responder en comentario, enviar DM proactivo, crear lead |
| 23 | Instagram content auto-capture: posts → knowledge base | backend, integrations, knowledge-base | Webhook media, capturar caption + media → embeddings → knowledge_items |
| 24 | Alertas al vendedor: notificacion por WhatsApp de lead caliente | backend, integrations | Cuando score > 75: enviar WhatsApp al vendedor asignado con resumen |
| 25 | Broadcasts masivos: enviar oferta a segmento de leads | backend, frontend | Seleccionar leads por filtro, enviar template masivo, tracking de entrega |

---

## Fase 4 — Analytics + Optimizacion (2 semanas)
**Objetivo**: Dashboard analytics completo, gestion catalogo, agenda visitas, reportes.
**Milestone**: `Fase 4 — Analytics + Optimizacion`
**Deadline**: 2026-05-15

### Issues

| # | Titulo | Labels | Descripcion |
|---|--------|--------|-------------|
| 26 | Dashboard analytics: graficos de conversion, tiempos, productos | frontend, backend | Chart.js graficos, endpoints de agregacion, filtros por periodo/canal |
| 27 | Gestion de catalogo desde dashboard: CRUD con fotos | frontend, backend | Cards con preview, upload de imagenes, edicion inline, reordenar |
| 28 | Knowledge base management: ver, agregar, editar, fuentes | frontend, backend | Lista de items por fuente, agregar manual, editar, desactivar, ver embedding status |
| 29 | Agenda de visitas: agendar, confirmar, completar | frontend, backend | Calendario visual, crear visita desde lead, confirmacion automatica 24h antes |
| 30 | Reportes automaticos: semanal por email/WhatsApp | backend | Celery task semanal, generar resumen, enviar por WhatsApp al admin |
| 31 | Configuracion de empresa desde dashboard | frontend, backend | Editar perfil, AI personality, business hours, canales conectados |
| 32 | Configuracion del agente IA desde dashboard | frontend, backend | Editar system prompt, reglas custom, tono, idioma, ver tools activos |
| 33 | Onboarding wizard: setup rapido para nueva empresa | frontend, backend | Wizard step-by-step: datos empresa, conectar WhatsApp, cargar catalogo, configurar IA |
| 34 | Multi-idioma: deteccion automatica + respuesta en idioma del lead | backend, ai | Detectar idioma del mensaje, responder en mismo idioma, portugues para Brasil |

---

## Fase 5 — Escala (futuro)
**Objetivo**: Features para crecer como SaaS y agregar nuevos canales.

### Ideas (sin issues aun)
- Web chat widget embebible
- TikTok DM integration
- MercadoLibre: responder preguntas de publicaciones
- Email channel
- Voice messages: speech-to-text → IA → text-to-speech
- AI-generated follow-up sequences (auto-crear secuencias)
- Landing page builder con chat embebido
- Mobile app para vendedores (push notifications)
- API publica para integraciones custom
- Marketplace de templates de agente por industria
- White-label: empresas venden Tabot con su marca
- Stripe/MercadoPago billing integration

---

## Costos Estimados

### Infraestructura MVP
| Componente | Costo/mes |
|------------|-----------|
| VPS (Hetzner CX31: 4 vCPU, 8GB RAM) | ~$12 USD |
| Dominio (.com o .ai) | ~$1-5 USD |
| Claude API (~5000 msgs/mes, ~500 tokens promedio) | ~$15-25 USD |
| WhatsApp Cloud API (1000 conv servicio gratis) | ~$10-30 USD |
| Embedding API (voyage/openai) | ~$5-10 USD |
| Backups S3 | ~$2 USD |
| **TOTAL MVP** | **~$45-85 USD/mes** |

### Modelo de Pricing SaaS (futuro)
| Plan | Precio | Incluye |
|------|--------|---------|
| Starter | $49/mes | 1 WhatsApp, 1000 conv IA/mes, 2 agentes, web chat |
| Pro | $99/mes | WhatsApp + IG, 5000 conv IA/mes, 5 agentes, CRM, broadcasts |
| Business | $199/mes | Todo ilimitado, API, webhooks, reportes avanzados |
