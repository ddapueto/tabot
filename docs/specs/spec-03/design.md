# Spec 03 — Mobile Responsive | Design

## Arquitectura de breakpoints

```
<768px   → mobile  (1 col, sidebar hidden, stack nav)
768-1024 → tablet  (2 cols inbox, sidebar colapsado)
>1024px  → desktop (3 cols inbox, sidebar expandido)
```

## Decisiones

### Inbox mobile navigation
- **Decisión**: Stack navigation con estado reactivo (showChat flag)
- **Razón**: Patrón estándar mobile, no necesita router adicional
- **Alternativa descartada**: Tabs (no aprovecha el espacio vertical)

### Sidebar mobile
- **Decisión**: Overlay con backdrop oscuro, hamburger button fijo
- **Razón**: No ocupa espacio del contenido, patrón familiar
- **Nota**: Cerrar al hacer click fuera o al navegar

### Touch targets
- **Decisión**: Mínimo 44x44px en todos los botones/links interactivos
- **Razón**: Apple HIG y WCAG recomiendan 44px mínimo

## Archivos a crear/modificar

| Archivo | Acción | Cambio |
|---------|--------|--------|
| `frontend/src/routes/+layout.svelte` | modificar | sidebar overlay, hamburger, media query |
| `frontend/src/routes/+page.svelte` | modificar | grid responsive 2→4 cols |
| `frontend/src/routes/conversations/+page.svelte` | modificar | stack nav mobile, breakpoints 3→2→1 col |
| `frontend/src/routes/leads/+page.svelte` | modificar | detalle en overlay, filtros colapsables |
| `frontend/src/app.css` | modificar | touch targets, breakpoint utilities |
