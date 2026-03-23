# Specs de Implementación — Tabot

## Sistema de specs

Cada spec tiene 3 archivos:
- `requirements.md` — Qué necesitamos (problema, MUST/SHOULD, escenarios, no-gos)
- `design.md` — Cómo lo resolvemos (arquitectura, decisiones ADR, archivos)
- `tasks.md` — Pasos atómicos con checkboxes (1 task = 1 acción de Claude)

## Contexto (steering docs)

Antes de ejecutar una spec, leer:
- `docs/steering/product.md` — visión, usuarios, métricas
- `docs/steering/tech.md` — stack, constraints, patrones
- `docs/steering/structure.md` — organización de archivos, convenciones

## Cómo ejecutar

```
Claude, leé docs/specs/spec-01/ y ejecutá las tasks
```

## Estado

| # | Spec | Prioridad | Impacto | Depende de | Estado |
|---|------|-----------|---------|------------|--------|
| 01 | Tests (25+) | P0 | +1.5 pts | spec-11 | ⏳ ready |
| 02 | CI/CD (GitHub Actions) | P0 | +1.0 pts | spec-01 | ⏳ ready |
| 03 | Mobile responsive | P1 | +0.5 pts | — | ⏳ ready |
| 04 | Notifications | P1 | +0.5 pts | — | ⏳ ready |
| 05 | Frontend polish | P1 | +0.5 pts | — | ⏳ ready |
| 06 | Logging (structlog) | P1 | +0.5 pts | — | ⏳ ready |
| 07 | Deploy (VPS) | P0 | +1.0 pts | 01, 02 | ⏳ ready |
| 08 | Landing page | P2 | +0.5 pts | 07 | ⏳ ready |
| 09 | WhatsApp real | P0 | +1.0 pts | 07 | ⏳ ready |
| 10 | Monitoring | P2 | +0.5 pts | 06, 07 | ⏳ ready |
| 11 | **Refactoring backend** | **P0** | riesgo 100→30 | — | ⏳ ready |
| 12 | **Doc drift cleanup** | **P1** | 15 drift→0 | — | ⏳ ready |
| 13 | **Desacoplamiento** | **P2** | smells 25→15 | spec-11 | ⏳ ready |

## Dependencias

```
spec-11 (refactoring) ──→ spec-01 (tests) ──→ spec-02 (CI/CD) ──→ spec-07 (deploy) ──→ spec-09 (WA real)
                      └──→ spec-13 (desacoplamiento)              └──→ spec-08 (landing)
spec-06 (logging) ──→ spec-10 (monitoring) ←── spec-07

spec-03 (mobile), spec-04 (notifications), spec-05 (frontend), spec-12 (doc drift): independientes
```

## Orden recomendado

```
Paralelo 0: spec-11 (refactoring) + spec-12 (doc drift)
    ↓
Paralelo 1: spec-01 (tests) + spec-03 + spec-04 + spec-06
    ↓
Paralelo 2: spec-02 + spec-05 + spec-13 (desacoplamiento)
    ↓
spec-07 (deploy)
    ↓
Paralelo 3: spec-08 + spec-09 + spec-10
```
