# Spec 11 — Refactoring Backend Critico | Requirements

## Meta
- Estado: ⏳ ready
- Prioridad: P0
- Impacto: Riesgo message_handler 100→30, code smells 25→10
- Depende de: ninguna (ejecutar ANTES de spec-01)
- Branch: `feat/spec-11-refactoring`

## Problema
Kagami detectó 1 archivo en riesgo critico (100/100) y 2 en riesgo alto (60+).
`message_handler.py` tiene una función de 171 lineas, 17 imports, y es el hub
que conecta 5 comunidades del grafo de dependencias. `ai_agent.py` duplica
logica entre Groq y Anthropic. `conversations.py` creció +194% en un commit.
Hay 8 funciones >50 lineas en total. Si escribimos tests sobre este código
frágil, después refactorizar va a ser doloroso.

## Appetite
1 sesión de Claude, max 2 horas.

## Requirements funcionales

### message_handler.py (riesgo 100)
- MUST: `handle_inbound_message` dividida en subfunciones de <50 lineas cada una
- MUST: extraer paso de scoring + alerta a función `_score_and_alert`
- MUST: extraer paso de validación + envio a función `_validate_and_send`
- MUST: extraer paso de notificación SSE a función `_notify_sse`
- MUST: imports lazy (follow_up_engine, notifications, config) pasan a ser imports top-level
- MUST: eliminar bare `except Exception: pass` — loggear warnings minimo
- MUST NOT: cambiar la firma publica de `handle_inbound_message`
- MUST NOT: cambiar el comportamiento funcional (refactoring puro)

### ai_agent.py (riesgo 61)
- MUST: unificar `_generate_groq` y `_generate_anthropic` — extraer lógica compartida
- MUST: extraer enrichment de prompt (catalog + KB) a `_enrich_system_prompt`
- MUST: eliminar `_get_kb_context` (función muerta, ya se usa `kb_manager.get_relevant_kb`)
- SHOULD: reducir imports de 15 a <12

### conversations.py (riesgo 62)
- MUST: `send_human_message` (75 lineas) dividida — extraer envio WhatsApp a helper
- SHOULD: extraer lógica de SSE `_notify` + `_listeners` a modulo compartido (message_handler también lo usa)
- MUST NOT: cambiar endpoints ni schemas publicos

### Funciones largas restantes (>50 lineas)
- SHOULD: `send_broadcast` (78 lineas) — extraer loop de envio
- SHOULD: `setup_company` (81 lineas) — extraer creación de entidades
- SHOULD: `validate_response` (91 lineas) — extraer cada capa a subfunción
- SHOULD: `alert_hot_lead` / `_alert` (67+62 lineas) — simplificar

## Escenarios clave

```
GIVEN message_handler.py actual
WHEN cuento lineas de la funcion mas larga
THEN es <50 lineas

GIVEN ai_agent.py con 2 providers
WHEN agrego un tercer provider (ej: OpenAI)
THEN solo necesito agregar 1 función, no duplicar toda la lógica

GIVEN conversations.py con SSE
WHEN message_handler.py necesita notificar SSE
THEN usa el mismo modulo compartido (no import circular)
```

## No-gos
- No cambiar firmas publicas de funciones
- No cambiar schemas de API
- No agregar dependencias nuevas
- No cambiar tests existentes (deben seguir pasando)
- No mezclar refactoring con features nuevas
