# Spec 06 — Logging Estructurado (structlog) | Requirements

## Meta
- Estado: ⏳ ready
- Prioridad: P1
- Impacto: Logging 1/10 → 7/10
- Depende de: ninguna
- Branch: `feat/spec-06-logging`

## Problema
No hay logging estructurado. En producción será imposible debuggear problemas
sin logs parseables. Print statements y logging básico no escalan. No hay
request tracing, no hay timing de IA, no hay correlación entre eventos.

## Appetite
1 sesión de Claude, max 1.5 horas.

## Requirements funcionales
- MUST: structlog configurado con JSON en producción y pretty en desarrollo
- MUST: middleware que loguee cada request (method, path, status, duration_ms)
- MUST: request_id (UUID) en todos los logs del mismo request
- MUST: company_id bindeado cuando hay auth
- MUST: AI calls logueadas (modelo, tokens in/out, tiempo, tools)
- MUST: webhook processing logueado (canal, resultado, lead_id)
- SHOULD: timing de response_validator
- MUST NOT: loguear datos sensibles (tokens, passwords, contenido completo)

## Escenarios clave

```
GIVEN un request GET /api/leads/
WHEN se procesa exitosamente
THEN log con request_id, company_id, method, path, status=200, duration_ms

GIVEN un mensaje de WhatsApp procesado
WHEN la IA responde
THEN log con request_id, lead_id, channel=whatsapp, ai_model, ai_tokens, ai_time_ms

GIVEN env ENVIRONMENT=production
WHEN se loguea
THEN output es JSON parseable (una línea por log)
```

## No-gos
- No agregar Sentry aún (futuro, Spec 10)
- No loguear contenido completo de mensajes (privacy)
- No agregar log rotation (Docker maneja stdout)
