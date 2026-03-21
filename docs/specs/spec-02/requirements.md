# Spec 02 — CI/CD (GitHub Actions) | Requirements

## Meta
- Estado: ⏳ ready
- Prioridad: P0
- Impacto: CI/CD 0/10 → 8/10
- Depende de: Spec 01 (tests)
- Branch: `feat/spec-02-cicd`

## Problema
No hay pipeline automático. Código roto puede llegar a main sin que nadie lo detecte.
Sin CI, los tests de Spec 01 solo corren manualmente — se van a olvidar.

## Appetite
1 sesión de Claude, max 1 hora.

## Requirements funcionales
- MUST: workflow que corra en push a main y en PRs
- MUST: backend job con lint (ruff check), format (ruff format --check), typecheck (mypy)
- MUST: backend job con PostgreSQL+pgvector+Redis como services
- MUST: backend job corra migraciones y luego pytest
- MUST: frontend job con svelte-check + build
- SHOULD: badge de CI status en README
- MAY: cache de dependencias (uv cache, npm cache)

## Escenarios clave

```
GIVEN un PR con lint errors
WHEN se pushea al PR
THEN CI falla en el step "Lint" y el PR queda bloqueado

GIVEN un PR con tests pasando
WHEN CI corre completo
THEN todos los jobs pasan verde

GIVEN un push directo a main
WHEN CI corre
THEN ejecuta el mismo pipeline que PRs
```

## No-gos
- No hacer CD automático (deploy manual por ahora)
- No agregar coverage reports aún
- No correr tests E2E con APIs externas (Groq, Meta)
