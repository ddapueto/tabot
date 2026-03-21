# Spec 10 — Monitoreo (Health Checks + Uptime) | Tasks

## Tareas (ejecutar en orden)

- [ ] **T1**: Modificar `backend/app/api/health.py` — mejorar `/health`: verificar DB (SELECT 1), Redis (ping), retornar status ok/degraded, version, ai_provider
- [ ] **T2**: Agregar endpoint `/health/metrics` — queries: total_companies, total_leads, total_messages_today, ai_errors_today, webhook_errors_today, pending_followups, kb_items_expiring_7d, uptime_seconds
- [ ] **T3**: Proteger `/health/metrics` con auth (JWT required), `/health` queda público
- [ ] **T4**: Agregar APP_VERSION a config (default "0.1.0")
- [ ] **T5**: Correr tests: `uv run pytest -x -v` — verificar que /health sigue pasando
- [ ] **T6**: (Manual) Crear cuenta en UptimeRobot, agregar monitor HTTP para /health
- [ ] **T7**: (Manual) Configurar alerta email en UptimeRobot

## Verificación
```bash
# Health check básico:
curl http://localhost:8001/health | python3 -m json.tool
# → {"status": "ok", "version": "0.1.0", "checks": {"database": "ok", "redis": "ok"}}

# Métricas (con auth):
curl -H "Authorization: Bearer TOKEN" http://localhost:8001/health/metrics | python3 -m json.tool
# → {"uptime_seconds": ..., "total_companies": ..., ...}

# Simular Redis caído:
docker compose stop redis
curl http://localhost:8001/health
# → {"status": "degraded", "checks": {"database": "ok", "redis": "error"}}
```

## Criterios de aceptación
- [ ] `/health` verifica DB + Redis, retorna ok/degraded
- [ ] `/health/metrics` retorna métricas internas (auth required)
- [ ] UptimeRobot configurado y monitoreando
- [ ] Alerta por email funciona cuando servicio cae
- [ ] Tests existentes siguen pasando
