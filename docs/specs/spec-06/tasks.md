# Spec 06 — Logging Estructurado (structlog) | Tasks

## Tareas (ejecutar en orden)

- [ ] **T1**: Agregar `structlog>=24.0.0` a `backend/pyproject.toml` y correr `uv sync`
- [ ] **T2**: Crear `backend/app/logging_config.py` — `setup_logging(env)` con processors: contextvars, log_level, logger_name, timestamper, exc_info, renderer (JSON prod / pretty dev)
- [ ] **T3**: Modificar `backend/app/main.py` — llamar `setup_logging()` en lifespan, agregar middleware: generar request_id (UUID), bind company_id si auth, log method/path/status/duration_ms
- [ ] **T4**: Modificar `backend/app/services/ai_agent.py` — log: modelo, tokens_in, tokens_out, ai_time_ms, tools llamados
- [ ] **T5**: Modificar `backend/app/services/message_handler.py` — log: canal, lead_id, total_time_ms, price_validated, escalated
- [ ] **T6**: Modificar `backend/app/api/webhooks/whatsapp.py` — log: type, from (truncado), processing result
- [ ] **T7**: Verificar que no se loguean datos sensibles (buscar tokens, password en logs)
- [ ] **T8**: Correr `uv run ruff check .` y `uv run pytest -x -v`

## Verificación
```bash
# Dev: logs con colores
cd backend && ENVIRONMENT=development uv run uvicorn app.main:app --port 8001
curl http://localhost:8001/health
# → log bonito con request_id, method=GET, path=/health, status=200, duration_ms

# Producción: JSON parseable
ENVIRONMENT=production uv run uvicorn app.main:app --port 8001 2>&1 | head -5
# → cada línea es JSON válido
```

## Criterios de aceptación
- [ ] structlog configurado (JSON prod, pretty dev)
- [ ] Cada request logueado con method, path, status, duration_ms
- [ ] request_id presente en todos los logs del mismo request
- [ ] AI calls logueadas con tokens y timing
- [ ] Webhooks logueados con resultado
- [ ] Sin datos sensibles en logs
- [ ] Tests siguen pasando
