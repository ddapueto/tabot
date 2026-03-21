# Spec 01 — Tests | Tasks

## Tareas (ejecutar en orden)

- [ ] **T1**: Crear `tests/conftest.py` con fixtures: `client` (AsyncClient ASGI), `auth_headers` (via onboarding → token), `company_id`
- [ ] **T2**: Crear `tests/test_auth.py` — 8 tests: register success/duplicate/short-password, login success/wrong-password, me with/without token, refresh
- [ ] **T3**: Crear `tests/test_onboarding.py` — 2 tests: setup success, setup short password
- [ ] **T4**: Crear `tests/test_leads.py` — 8 tests: list empty, list with data (crear lead via webhook mock), get 404, update, stage valid/invalid, handoff, reactivate
- [ ] **T5**: Crear `tests/test_conversations.py` — 3 tests: list, send message, send to non-existent conv
- [ ] **T6**: Crear `tests/test_catalog.py` — 3 tests: list, create, update
- [ ] **T7**: Correr `uv run pytest -x -v` — verificar 25+ passed
- [ ] **T8**: Correr `uv run ruff check tests/` — verificar lint clean

## Verificación
```bash
cd backend && uv run pytest -x -v --tb=short
# Esperado: 25+ passed, 0 failed, 0 errors
```

## Criterios de aceptación
- [ ] 25+ tests pasando
- [ ] Todos los endpoints críticos cubiertos
- [ ] Fixtures reutilizables
- [ ] Sin mocks de DB
- [ ] Lint clean
