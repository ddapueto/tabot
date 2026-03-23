# Spec 13 — Desacoplamiento Backend | Requirements

## Meta
- Estado: ⏳ ready
- Prioridad: P2
- Impacto: Smells 25→15, zonas de riesgo 4→2
- Depende de: spec-11 (refactoring primero)
- Branch: `feat/spec-13-desacoplamiento`

## Problema
Kagami detectó 4 "zonas de riesgo" en el grafo de comunidades del código,
con un total de 36 archivos y 23 code smells concentrados. El problema
principal es alto acoplamiento: archivos con 11-19 imports que dependen
de demasiados modulos. Esto hace que un cambio en un archivo tenga impacto
impredecible en otros.

Zonas de riesgo:
1. **KB + IA + Instagram** (12 files, 7 smells) — mezcla settings, AI, KB e Instagram
2. **Leads + Conversations** (12 files, 9 smells) — mayor cant. de smells
3. **Auth + Onboarding** (7 files, 2 smells) — database.py es bridge de 6 comunidades
4. **Follow-ups** (5 files, 5 smells) — funciones largas, alto acoplamiento

## Appetite
1 sesión de Claude, max 2 horas.

## Requirements funcionales

### Reducción de imports (acoplamiento)
- MUST: archivos con >15 imports bajan a <12
- MUST: archivos con >12 imports bajan a <10
- SHOULD: ningún archivo con >10 imports

### Zona KB + IA + Instagram
- MUST: `settings_api.py` (13 imports) — separar endpoints de KB a `kb_api.py`
- SHOULD: `instagram.py` webhook (12 imports) — extraer parsing de payload a helper

### Zona Leads + Conversations
- MUST: `conversations.py` (19 imports) — reducir post spec-11 (SSE extraido)
- MUST: `analytics.py` (11 imports) — extraer queries pesadas a helpers
- SHOULD: `leads.py` (11 imports) — evaluar si se puede reducir

### Zona Follow-ups
- MUST: `follow_up_engine.py` (11 imports) — revisar si hay imports innecesarios
- MUST: `tasks/follow_ups.py` (11 imports) — idem

### Zona Auth + Onboarding
- SHOULD: `auth.py` (13 imports) — evaluar si token logic se puede separar
- La zona 3 tiene solo 2 smells — es la menos urgente

## Escenarios clave

```
GIVEN la lista de archivos con >12 imports
WHEN cuento imports después de esta spec
THEN ninguno tiene >12

GIVEN settings_api.py con endpoints de company + AI + KB + promos
WHEN quiero modificar solo KB
THEN solo toco kb_api.py sin riesgo de romper settings
```

## No-gos
- No cambiar APIs publicas (URLs, schemas, responses)
- No mover modelos entre archivos (rompe migraciones)
- No crear abstracciones prematuras (no ABC, no factories, no registries)
- No separar por separar — solo si reduce acoplamiento real
- No tocar `database.py` (es bridge legítimo de infraestructura)
