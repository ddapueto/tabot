# Spec 12 — Doc Drift Cleanup | Tasks

## Pre-condición
- Leer `docs/specs/spec-12/design.md` para entender qué es falso positivo vs corrección real

## Tasks

- [ ] **T1**: Corregir config_drift — abrir `docs/specs/spec-07/design.md`, buscar puerto 5432, cambiar a 5435

- [ ] **T2**: Corregir example_drift — abrir `docs/design-code-intel-mcp.md`, ir a linea ~630, corregir error de indentación Python

- [ ] **T3**: Verificar tech_drift en CLAUDE.md — buscar la linea 68 que Kagami reportó como "react". Si es "reactivar"/"reactivo", ignorar. Si realmente dice "React" como framework, corregir a "Svelte"

- [ ] **T4**: Eliminar dependencia unused — en `backend/pyproject.toml`, eliminar `"passlib[bcrypt]>=1.7.4"` de dependencies. Correr `cd backend && uv lock` para actualizar lockfile

- [ ] **T5**: Verificar resultado — correr Kagami `detect_drift` y confirmar que los issues reales están resueltos (los falsos positivos van a seguir apareciendo, eso es OK)

## Criterio de éxito
- Puerto correcto (5435) en spec-07
- Ejemplo Python válido en design-code-intel-mcp.md
- `passlib[bcrypt]` eliminada de pyproject.toml
- `uv lock` exitoso sin errores
