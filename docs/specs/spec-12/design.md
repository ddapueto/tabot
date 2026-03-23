# Spec 12 — Doc Drift Cleanup | Design

## Análisis de cada drift issue

### config_drift (1 issue — corregir)
| Archivo | Linea | Problema | Acción |
|---------|-------|----------|--------|
| `docs/specs/spec-07/design.md` | 12 | Puerto 5432 | Cambiar a 5435 |

### example_drift (1 issue — corregir)
| Archivo | Linea | Problema | Acción |
|---------|-------|----------|--------|
| `docs/design-code-intel-mcp.md` | 630 | Error sintaxis Python | Corregir indentación |

### tech_drift "react" (11 issues — analizar uno por uno)
| Archivo | Linea | Contexto real | Acción |
|---------|-------|---------------|--------|
| `.claude/agents/frontend.md` | 50 | Kagami reportó pero grep no encuentra "react" | **Ignorar** (falso positivo) |
| `CLAUDE.md` | 68 | Contiene "reactivar" o "reactivo" | **Verificar** — si es falso positivo, ignorar |
| `docs/architecture.md` | 130 | "React, Next.js" como alternativa descartada | **OK** — mención legítima, no es drift |
| `docs/database-schema.md` | 257 | "reactivation" (tipo de follow-up) | **Ignorar** (falso positivo) |
| `docs/roadmap.md` | 42 | "reactivar" (feature de handoff) | **Ignorar** (falso positivo) |
| `docs/specs/spec-01/requirements.md` | 22 | "reactivate" (test scenario) | **Ignorar** (falso positivo) |
| `docs/specs/spec-01/tasks.md` | 8 | "reactivate" (task) | **Ignorar** (falso positivo) |
| `docs/specs/spec-03/design.md` | 14 | "reactivo" (estado reactivo Svelte) | **Ignorar** (falso positivo) |
| `docs/steering/structure.md` | 17 | "reactivate" | **Ignorar** (falso positivo) |
| `docs/steering/structure.md` | 89 | "reactivar" | **Ignorar** (falso positivo) |

### tech_drift "pbkdf2/bcrypt" (3 issues — falso positivo de Kagami)
| Archivo | Problema | Realidad | Acción |
|---------|----------|----------|--------|
| `CLAUDE.md` | "Doc says pbkdf2 but code uses bcrypt" | Código usa PBKDF2 (hashlib). bcrypt está en deps pero unused | **Ignorar** doc (es correcto). Eliminar dep unused |
| `CLAUDE.md` | Misma issue, otra linea | Idem | **Ignorar** |
| `docs/steering/tech.md` | Idem | Idem | **Ignorar** (doc es correcto) |

### Dependencia unused
| Archivo | Problema | Acción |
|---------|----------|--------|
| `backend/pyproject.toml` | `passlib[bcrypt]` listada como dependencia | Verificar que no se importa en ningún lado → eliminar |

## Resumen de acciones reales

Solo 2-3 correcciones reales + 1 limpieza de dependencia:
1. Puerto 5432→5435 en spec-07/design.md
2. Fix sintaxis Python en design-code-intel-mcp.md
3. Eliminar `passlib[bcrypt]` de pyproject.toml + `uv lock`
4. Verificar los 2-3 casos dudosos de CLAUDE.md

La mayoría de los 15 issues son falsos positivos de Kagami (regex matching "react" dentro de "reactivar").
