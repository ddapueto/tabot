# Spec 10 — Monitoreo (Health Checks + Uptime) | Design

## Arquitectura

```
UptimeRobot (externo, 5min checks)
  → GET /health → {"status": "ok|degraded", "checks": {...}}

Dashboard interno (auth required)
  → GET /health/metrics → {"uptime_seconds", "total_companies", ...}
```

## Decisiones

### Health check detallado
- **Decisión**: Verificar DB (SELECT 1) y Redis (ping) en cada llamada
- **Razón**: Detectar degradación parcial (ej: Redis caído pero DB OK)
- **Nota**: Status "ok" si todo bien, "degraded" si algo falla

### UptimeRobot
- **Decisión**: Servicio externo gratuito (5min checks, alerta email)
- **Razón**: Gratis hasta 50 monitors, no necesita infraestructura propia
- **Alternativa descartada**: BetterStack (paid), self-hosted (overhead)

### Métricas internas
- **Decisión**: Endpoint `/health/metrics` con queries a DB (conteos)
- **Razón**: Visibilidad básica sin infraestructura de métricas
- **Seguridad**: Requiere auth (JWT) para acceder

### Error tracking (futuro)
- **Decisión**: Diferido — Sentry cuando haya volumen real
- **Razón**: Los logs estructurados de Spec 06 son suficientes para MVP

## Archivos a crear/modificar

| Archivo | Acción | Cambio principal |
|---------|--------|-----------------|
| `backend/app/api/health.py` | modificar | /health mejorado (DB+Redis check), /health/metrics nuevo |
| `backend/app/core/config.py` | modificar | agregar APP_VERSION |
