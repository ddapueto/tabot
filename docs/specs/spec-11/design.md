# Spec 11 — Refactoring Backend Critico | Design

## Decisiones arquitectonicas

### ADR-1: Extraer SSE pub/sub a modulo compartido
- **Contexto**: `conversations.py` define `_listeners` y `_notify()`, y `message_handler.py`
  hace `from app.api.conversations import _notify` (import circular potencial)
- **Decisión**: Crear `app/services/sse.py` con `notify()` y `listeners` dict
- **Razón**: Elimina acoplamiento circular api→service→api, centraliza el pub/sub
- **Archivos**: `app/services/sse.py` (nuevo, ~20 lineas)

### ADR-2: Estrategia de unificación AI providers
- **Contexto**: `_generate_groq` y `_generate_anthropic` comparten: build prompt, enrich
  con catalog+KB, crear messages, manejar error, formatear resultado
- **Decisión**: Extraer `_enrich_system_prompt()` y `_format_result()` como helpers compartidos.
  Mantener funciones separadas por provider (no usar ABC/strategy pattern — overengineering
  para 2 providers)
- **Razón**: Reduce duplicación sin agregar complejidad innecesaria
- **Trade-off**: Si se agregan 3+ providers, reconsiderar con strategy pattern

### ADR-3: Subfunciones de message_handler
- **Contexto**: `handle_inbound_message` tiene 9 pasos secuenciales en 171 lineas
- **Decisión**: Extraer 3 helpers internos que agrupan pasos relacionados:
  - `_score_and_alert(db, lead, company, content)` — pasos 4c, 4d
  - `_validate_and_send(db, company, conversation, lead, ai_result, channel, phone_number_id, sender_id)` — pasos 6b, 7
  - `_notify_sse(company_id, conversation_id, lead_name, inbound_content, response_text)` — paso 9
- **Razón**: Cada helper tiene responsabilidad clara, `handle_inbound_message` queda como orquestador de ~60 lineas

### ADR-4: Imports lazy → top-level
- **Contexto**: `message_handler.py` tiene imports inline (`from app.services.follow_up_engine import ...`)
  para evitar circular imports
- **Decisión**: Con SSE extraido a `sse.py`, los imports circulares se resuelven.
  Mover todos los imports a top-level
- **Razón**: Imports top-level fallan rápido al startup (detectan errores antes)

## Archivos a modificar

| Archivo | Acción | Lineas estimadas |
|---------|--------|------------------|
| `app/services/sse.py` | **CREAR** — pub/sub SSE | ~25 |
| `app/services/message_handler.py` | Refactorizar — extraer 3 helpers, imports top-level | ~320→~280 |
| `app/services/ai_agent.py` | Refactorizar — extraer `_enrich_system_prompt`, eliminar `_get_kb_context` | ~261→~220 |
| `app/api/conversations.py` | Refactorizar — usar sse.py, extraer WA send helper | ~229→~200 |
| `app/api/broadcasts.py` | Refactorizar — extraer loop de envío | ~130→~130 |
| `app/api/onboarding.py` | Refactorizar — extraer creación de entidades | ~110→~110 |
| `app/services/response_validator.py` | Refactorizar — extraer capas | ~150→~150 |

## Diagrama de dependencias (después)

```
message_handler.py
  ├── ai_agent.py (generate_response)
  ├── lead_scorer.py (extract_signals, update_score)
  ├── follow_up_engine.py (cancel_followups)
  ├── response_validator.py (validate_response)
  ├── whatsapp_client.py (send_text_message)
  └── sse.py (notify)  ← NUEVO

conversations.py
  ├── sse.py (notify)  ← ANTES: definía _notify inline
  └── whatsapp_client.py (send_text_message)

ai_agent.py
  ├── ai_tools.py (TOOLS, execute_tool)
  └── kb_manager.py (get_relevant_kb)
```
