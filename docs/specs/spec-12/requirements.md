# Spec 12 — Doc Drift Cleanup | Requirements

## Meta
- Estado: ⏳ ready
- Prioridad: P1
- Impacto: 15 drift issues → 0
- Depende de: ninguna (independiente)
- Branch: `feat/spec-12-doc-drift`

## Problema
Kagami detectó 15 issues de drift entre documentación y código:
- 1 config_drift: puerto 5432 en spec-07 debería ser 5435
- 1 example_drift: error de sintaxis Python en ejemplo
- 13 tech_drift: la mayoría son falsos positivos ("react" en contextos como
  "reactivar", "reactivo", o la mención legítima de React como alternativa
  descartada en architecture.md). Hay que revisar cada uno y solo corregir
  los que realmente son erróneos.

Nota sobre pbkdf2/bcrypt: Kagami reportó drift, pero el código real usa
PBKDF2-SHA256 (hashlib stdlib). `passlib[bcrypt]` está en pyproject.toml
como dependencia no usada. Los docs que dicen PBKDF2 son correctos.
La acción es eliminar la dependencia unused de pyproject.toml.

## Appetite
30 minutos de Claude, max 1 hora.

## Requirements funcionales
- MUST: corregir config_drift en spec-07/design.md (puerto 5432 → 5435)
- MUST: corregir example_drift en design-code-intel-mcp.md (sintaxis Python)
- MUST: revisar cada tech_drift de "react" y corregir solo los erróneos
- MUST: eliminar `passlib[bcrypt]` de pyproject.toml si no se usa en el código
- SHOULD: verificar que steering/tech.md es coherente con el código real
- MUST NOT: cambiar código funcional — solo docs y dependencias no usadas
- MUST NOT: inventar contenido nuevo en docs — solo corregir lo existente

## Escenarios clave

```
GIVEN Kagami detect_drift sobre el proyecto
WHEN ejecuto después de esta spec
THEN reporta 0 warnings y 0 errors

GIVEN pyproject.toml con passlib[bcrypt]
WHEN busco usos de bcrypt/passlib en el código
THEN no hay usos → se elimina la dependencia
```

## No-gos
- No reescribir documentación completa
- No cambiar la arquitectura real del proyecto
- No agregar docs nuevos
