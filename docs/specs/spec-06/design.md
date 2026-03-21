# Spec 06 — Logging Estructurado (structlog) | Design

## Arquitectura

```
Request → Middleware (bind request_id, log start/end)
  → Router (bind company_id via auth)
    → Service (log business events)
      → structlog → JSON (prod) / ConsoleRenderer (dev)
```

## Decisiones

### structlog como librería
- **Decisión**: structlog con processors chain
- **Razón**: Estándar Python para logging estructurado, contextvars para tracing
- **Alternativa descartada**: python-json-logger (menos features, sin contextvars)

### Renderer por entorno
- **Decisión**: JSONRenderer en producción, ConsoleRenderer(colors=True) en desarrollo
- **Razón**: JSON para parsing automatizado en prod, pretty para legibilidad en dev
- **Config**: Variable ENVIRONMENT en settings

### Request ID
- **Decisión**: UUID4 generado en middleware, bindeado via contextvars
- **Razón**: Permite correlacionar todos los logs de un request sin pasar params

### Datos sensibles
- **Decisión**: Nunca loguear tokens, passwords, contenido completo de mensajes
- **Razón**: GDPR, seguridad; truncar a primeros 50 chars si necesario

## Archivos a crear/modificar

| Archivo | Acción | Cambio principal |
|---------|--------|-----------------|
| `backend/pyproject.toml` | modificar | +structlog>=24.0.0 |
| `backend/app/logging_config.py` | crear | setup_logging(), processors chain |
| `backend/app/main.py` | modificar | llamar setup_logging(), middleware request logging |
| `backend/app/services/ai_agent.py` | modificar | log modelo, tokens, timing, tools |
| `backend/app/services/message_handler.py` | modificar | log canal, lead_id, response time |
| `backend/app/api/webhooks/whatsapp.py` | modificar | log mensaje recibido, resultado |
