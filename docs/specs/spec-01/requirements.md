# Spec 01 — Tests | Requirements

## Meta
- Estado: ⏳ ready
- Prioridad: P0
- Impacto: Madurez tests 3/10 → 7/10
- Depende de: ninguna
- Branch: `feat/spec-01-tests`

## Problema
Solo hay 5 tests básicos (health + webhook verify). Cualquier cambio puede
romper funcionalidad sin que nos enteremos. No hay tests de auth, leads,
conversations, catalog ni onboarding. Para un producto que se va a vender
esto es inaceptable.

## Appetite
1 sesión de Claude, max 2 horas.

## Requirements funcionales
- MUST: 25+ tests pasando con `pytest -x -v`
- MUST: cubrir auth (register, login, refresh, me, token inválido)
- MUST: cubrir leads (CRUD, stage change, handoff, reactivate)
- MUST: cubrir conversations (list, send message)
- MUST: cubrir catalog (list, create, update)
- MUST: cubrir onboarding (setup company)
- MUST: fixtures reutilizables en conftest.py
- SHOULD: cubrir analytics y settings
- MUST NOT: mockear la DB — usar PostgreSQL real de Docker

## Escenarios clave

```
GIVEN un usuario no registrado
WHEN hace POST /api/auth/register con datos válidos
THEN recibe 201 + access_token + refresh_token

GIVEN un usuario registrado
WHEN hace POST /api/auth/login con password incorrecto
THEN recibe 401

GIVEN un usuario autenticado
WHEN hace GET /api/leads/ sin leads en su empresa
THEN recibe 200 + []

GIVEN un lead en stage "new"
WHEN se cambia stage a "interested"
THEN el cambio se registra en lead_stage_history

GIVEN un lead con conversación activa
WHEN se hace handoff
THEN ai_enabled = false y status = "handed_off"
```

## No-gos
- No hacer tests E2E con Groq/Anthropic real (costoso, lento)
- No testear webhooks con Meta real (usar payloads mock)
- No agregar framework de test coverage aún (futuro)
