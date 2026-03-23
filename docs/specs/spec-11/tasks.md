# Spec 11 — Refactoring Backend Critico | Tasks

## Pre-condición
- Docker corriendo (PG 5435 + Redis 6379)
- Tests existentes pasan: `cd backend && uv run pytest -x -v`

## Tasks

- [ ] **T1**: Crear `app/services/sse.py` — mover `_listeners` dict y `notify()` desde `conversations.py`. Exportar `notify(company_id: str, event: dict)` y `subscribe(company_id: str) -> asyncio.Queue` / `unsubscribe(company_id: str, queue)`

- [ ] **T2**: Actualizar `app/api/conversations.py` — importar `notify` y `subscribe`/`unsubscribe` de `sse.py`. Eliminar `_listeners` y `_notify` locales. `sse_stream` usa `subscribe`/`unsubscribe`. Extraer lógica de envío WhatsApp de `send_human_message` a `_send_via_whatsapp(conversation, lead, company_id, content, db)`. Verificar que los endpoints no cambian de firma

- [ ] **T3**: Actualizar `app/services/message_handler.py`:
  - Mover imports lazy a top-level (follow_up_engine, notifications, config, response_validator, sse)
  - Extraer `_score_and_alert(db, lead, company, content)` — contiene pasos 4c+4d (cancel follow-ups + scoring + hot alert)
  - Extraer `_validate_and_send(db, company, conversation, lead, ai_result, channel, phone_number_id, sender_id)` — contiene pasos 6b+7 (validación + envío WhatsApp)
  - Extraer `_notify_sse(company_id, conversation_id, lead_name, inbound_content, response_text)` — contiene paso 9
  - `handle_inbound_message` queda como orquestador llamando a las subfunciones
  - Eliminar bare `except Exception: pass` — usar `logger.debug` o `logger.warning`

- [ ] **T4**: Refactorizar `app/services/ai_agent.py`:
  - Extraer `_enrich_system_prompt(db, company_id, base_prompt, channel)` — carga catalog + KB y concatena al prompt
  - Usar `_enrich_system_prompt` tanto en `_generate_groq` como en `_generate_anthropic`
  - Eliminar `_get_kb_context()` (función muerta — `_generate_groq` ya usa `kb_manager.get_relevant_kb` directamente)
  - Extraer `_format_error_result(error)` para el bloque except compartido

- [ ] **T5**: Refactorizar funciones SHOULD (>50 lineas):
  - `app/api/broadcasts.py`: extraer loop de envío de `send_broadcast` a `_send_to_leads(db, leads, message, company)`
  - `app/api/onboarding.py`: extraer creación de entidades de `setup_company` a `_create_demo_data(db, company_id)` si aplica
  - `app/services/response_validator.py`: extraer cada capa de `validate_response` a `_check_prices`, `_check_forbidden`, `_check_escalation`

- [ ] **T6**: Verificar que NO se rompió nada:
  - `cd backend && uv run pytest -x -v` — todos los tests existentes pasan
  - `cd backend && uv run ruff check app/` — sin errores de lint
  - `cd backend && uv run python -c "from app.main import app; print('OK')"` — app importa sin error
  - Verificar que no hay imports circulares

## Criterio de éxito
- Función más larga del proyecto: <60 lineas (antes: 171)
- `message_handler.py`: imports <14 (antes: 17), no bare except
- `ai_agent.py`: sin función `_get_kb_context`, lógica de enrich compartida
- `conversations.py`: sin `_listeners`/`_notify` locales (usa sse.py)
- Todos los tests existentes pasan sin cambios
