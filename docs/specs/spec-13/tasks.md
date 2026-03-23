# Spec 13 — Desacoplamiento Backend | Tasks

## Pre-condición
- spec-11 completada (SSE extraido, message_handler refactorizado)
- Docker corriendo (PG 5435 + Redis 6379)
- Tests existentes pasan: `cd backend && uv run pytest -x -v`

## Tasks

- [ ] **T1**: Crear `app/api/kb.py` — extraer de `settings_api.py` todos los endpoints de KB (CRUD knowledge items). Crear router, mantener misma lógica. Imports solo los necesarios para KB (KnowledgeItem model, schemas, deps)

- [ ] **T2**: Actualizar `app/api/settings_api.py` — eliminar endpoints de KB extraidos en T1. Eliminar imports que ya no se necesitan (KnowledgeItem, KB schemas). Verificar que quedan solo endpoints de company config + AI config + promos

- [ ] **T3**: Registrar KB router en `app/main.py` — importar `kb_router` de `app.api.kb`, incluir con `prefix="/api/kb"`. Decidir si las URLs cambian de `/api/settings/kb/...` a `/api/kb/...` o se mantienen en `/api/settings/kb/...` con el router nuevo (preferir cambio limpio)

- [ ] **T4**: Actualizar frontend si URLs cambiaron — buscar en `frontend/src/` todas las referencias a endpoints KB (probablemente en `settings/+page.svelte` y `api.ts`). Actualizar URLs

- [ ] **T5**: Limpiar imports en follow-ups — revisar `app/services/follow_up_engine.py` y `app/tasks/follow_ups.py`. Eliminar imports no usados. Si hay imports condicionales o lazy que ya no son necesarios post spec-11, convertir a top-level

- [ ] **T6**: Extraer helper de Instagram — en `app/api/webhooks/instagram.py`, extraer el parsing del payload de Instagram (interpretar estructura anidada de Meta Graph API) a `_parse_instagram_event(body: dict) -> dict | None` que retorna un dict normalizado con sender_id, content, msg_type, etc.

- [ ] **T7**: Verificar que NO se rompió nada:
  - `cd backend && uv run pytest -x -v` — todos los tests pasan
  - `cd backend && uv run ruff check app/` — sin errores de lint
  - `cd backend && uv run python -c "from app.main import app; print('OK')"` — app importa OK
  - Verificar que no hay imports circulares
  - Si frontend cambió: `cd frontend && npm run build` pasa

## Criterio de éxito
- `settings_api.py`: imports <10 (antes: 13)
- `follow_up_engine.py`: imports <10 (antes: 11)
- `tasks/follow_ups.py`: imports <10 (antes: 11)
- Nuevo `kb.py` con imports <10
- Ningún archivo con >12 imports (excepto `auth.py` que se acepta)
- Todos los tests pasan sin cambios
