# Spec 05 — Frontend Polish | Tasks

## Tareas (ejecutar en orden)

- [ ] **T1**: Crear `SkeletonLoader.svelte` — variantes: lines, cards, table; animación pulse CSS
- [ ] **T2**: Crear `EmptyState.svelte` — props: icon, message, actionLabel, onAction
- [ ] **T3**: Modificar `leads/+page.svelte` — agregar búsqueda (input + debounce 300ms), skeleton loader, empty state
- [ ] **T4**: Modificar `leads/+page.svelte` — dropdown cambio de stage en detalle, timeline de stage history
- [ ] **T5**: Modificar `catalog/+page.svelte` — botón "Agregar producto" + modal formulario, skeleton, empty state
- [ ] **T6**: Modificar `catalog/+page.svelte` — filtros por categoría como pills, precio formateado
- [ ] **T7**: Modificar `analytics/+page.svelte` — selector período (7d/30d/90d), funnel barras horizontales, skeleton
- [ ] **T8**: Modificar `settings/+page.svelte` — KB health card arriba (total/active/expired/needs_review)
- [ ] **T9**: Verificar que todas las páginas usan design tokens del tema activo
- [ ] **T10**: Agregar animaciones fade-in consistentes en listas y detalles

## Verificación
```bash
cd frontend && npm run dev
# Abrir cada página y verificar:
# - Skeleton loaders al cargar (throttle network en DevTools)
# - Empty states cuando no hay datos
# - Búsqueda en leads funciona
# - Crear producto en catalog funciona
# - Período en analytics cambia datos
```

## Criterios de aceptación
- [ ] Skeleton loaders en todas las páginas
- [ ] Empty states en todas las listas vacías
- [ ] Búsqueda funcional en leads
- [ ] Crear producto desde UI en catalog
- [ ] Selector de período en analytics
- [ ] Design tokens consistentes (no colores hardcoded)
- [ ] Animaciones fade-in en listas
