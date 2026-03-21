# Spec 05 — Frontend Polish | Design

## Arquitectura de componentes

```
frontend/src/
├── lib/
│   └── components/
│       ├── SkeletonLoader.svelte    # Reutilizable (líneas/cards/table)
│       └── EmptyState.svelte        # Reutilizable (icon + message + CTA)
├── routes/
│   ├── leads/+page.svelte           # + búsqueda, stage dropdown, timeline
│   ├── catalog/+page.svelte         # + modal crear, editar inline, filtros
│   ├── analytics/+page.svelte       # + período selector, funnel bars, donut
│   └── settings/+page.svelte        # + KB health card, sync button
```

## Decisiones

### Skeleton loaders
- **Decisión**: Componente reutilizable con variantes (lines, cards, table)
- **Razón**: Consistencia, reusable en todas las páginas
- **Implementación**: CSS animation pulse sobre divs con border-radius

### Búsqueda en leads
- **Decisión**: Filtro client-side con debounce 300ms
- **Razón**: Dataset pequeño por empresa (<500 leads), evita requests extra
- **Alternativa descartada**: Search API endpoint (overhead innecesario)

### Selector de período analytics
- **Decisión**: Pills arriba (7d/30d/90d) que pasan query param al endpoint
- **Razón**: Las APIs de analytics ya soportan parámetro de período

### Charts
- **Decisión**: SVG/HTML manual (barras, donut)
- **Razón**: Evitar dependencia pesada (Chart.js ~200KB), pocos gráficos simples

## Archivos a crear/modificar

| Archivo | Acción | Cambio principal |
|---------|--------|-----------------|
| `frontend/src/lib/components/SkeletonLoader.svelte` | crear | Componente reutilizable |
| `frontend/src/lib/components/EmptyState.svelte` | crear | Componente reutilizable |
| `frontend/src/routes/leads/+page.svelte` | modificar | búsqueda, stage, timeline, skeletons |
| `frontend/src/routes/catalog/+page.svelte` | modificar | modal crear, filtros, skeletons |
| `frontend/src/routes/analytics/+page.svelte` | modificar | período, funnel bars, skeletons |
| `frontend/src/routes/settings/+page.svelte` | modificar | KB health card |
