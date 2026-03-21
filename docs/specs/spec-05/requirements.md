# Spec 05 — Frontend Polish | Requirements

## Meta
- Estado: ⏳ ready
- Prioridad: P2
- Impacto: Frontend 6/10 → 8/10
- Depende de: ninguna
- Branch: `feat/spec-05-polish`

## Problema
Las páginas de leads, catalog, analytics y settings son funcionales pero básicas.
No tienen skeleton loaders, empty states, ni animaciones. El inbox ya tiene nivel
profesional pero el resto se siente "prototipo".

## Appetite
2 sesiones de Claude, max 3 horas total.

## Requirements funcionales
- MUST: skeleton loaders en todas las páginas (no "Cargando...")
- MUST: empty states con mensaje descriptivo en todas las listas vacías
- MUST: leads — búsqueda por nombre/teléfono con debounce 300ms
- MUST: leads — dropdown de cambio de stage, timeline de stage history
- MUST: catalog — botón "Agregar producto" con formulario modal
- MUST: analytics — selector de período (7d, 30d, 90d)
- SHOULD: catalog — editar producto inline
- SHOULD: analytics — funnel con barras horizontales y colores por stage
- SHOULD: settings — KB health card (total/active/expired)
- SHOULD: animaciones fade-in consistentes
- MUST: usar design tokens del tema activo (no colores hardcoded)

## Escenarios clave

```
GIVEN una empresa sin leads
WHEN el vendedor abre /leads
THEN ve empty state "No hay leads aún. Los leads se crean automáticamente..."

GIVEN un vendedor en /leads con 50 leads
WHEN escribe "Juan" en la búsqueda
THEN la lista se filtra mostrando solo leads que matchean (debounce 300ms)

GIVEN un vendedor en /analytics
WHEN cambia el período a "30d"
THEN las métricas se recalculan para los últimos 30 días
```

## No-gos
- No agregar chart library externa (SVG manual o HTML)
- No rediseñar el inbox (ya está bien)
- No agregar funcionalidad nueva de backend (solo consumir APIs existentes)
