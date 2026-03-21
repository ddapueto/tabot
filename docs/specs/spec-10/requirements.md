# Spec 10 — Monitoreo (Health Checks + Uptime) | Requirements

## Meta
- Estado: ⏳ ready
- Prioridad: P1
- Impacto: Monitoreo 0/10 → 7/10
- Depende de: Spec 06 (logging — necesita logs estructurados)
- Branch: `feat/spec-10-monitoring`

## Problema
Si algo falla en producción, nos enteramos cuando el cliente se queja.
No hay health checks detallados, no hay monitoreo de uptime, no hay métricas
internas. Imposible operar un SaaS sin saber cuándo algo se rompe.

## Appetite
1 sesión de Claude, max 1 hora.

## Requirements funcionales
- MUST: `/health` mejorado que verifique DB + Redis + retorne status (ok/degraded)
- MUST: `/health/metrics` con métricas internas (uptime, companies, leads, messages hoy, errores)
- MUST: UptimeRobot (o similar gratuito) configurado contra /health
- MUST: alerta por email cuando el servicio cae
- SHOULD: incluir versión de la app en /health
- SHOULD: incluir AI provider y modelo en /health
- MAY: integrar Sentry para error tracking (futuro)
- MUST NOT: exponer métricas sensibles sin auth en /health/metrics

## Escenarios clave

```
GIVEN la app corriendo con DB y Redis OK
WHEN se llama GET /health
THEN responde {"status": "ok", "checks": {"database": "ok", "redis": "ok"}}

GIVEN Redis caído
WHEN se llama GET /health
THEN responde {"status": "degraded", "checks": {"database": "ok", "redis": "error"}}

GIVEN UptimeRobot monitoreando /health
WHEN el servidor se cae
THEN llega email de alerta en <5 minutos
```

## No-gos
- No implementar Prometheus/Grafana (overkill para MVP)
- No agregar APM completo (DataDog, New Relic)
- No crear dashboard de métricas propio (usar UptimeRobot gratis)
