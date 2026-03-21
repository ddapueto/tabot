# Spec 03 — Mobile Responsive | Tasks

## Tareas (ejecutar en orden)

- [ ] **T1**: Modificar `+layout.svelte` — sidebar auto-hide <768px, hamburger button, overlay con backdrop
- [ ] **T2**: Modificar `+page.svelte` (Dashboard) — grid `grid-cols-2 md:grid-cols-4`, pipeline scroll horizontal
- [ ] **T3**: Modificar `conversations/+page.svelte` — stack navigation mobile: estado showChat, botón back, breakpoints 3→2→1 columnas
- [ ] **T4**: Modificar `leads/+page.svelte` — detalle en overlay/modal <768px, filtros colapsables
- [ ] **T5**: Modificar `app.css` — touch target mínimo 44x44px en botones, verificar breakpoints
- [ ] **T6**: Test visual en 375px (iPhone SE), 768px (tablet), 1024px+ (desktop)

## Verificación
```bash
# En browser: F12 → toggle device toolbar
# Probar en 375px (iPhone SE):
# - Login → Dashboard → Inbox → Leads → Catalog
# - Sidebar se oculta, hamburger visible
# - Inbox: solo lista, click → solo chat, back → lista
# - Sin horizontal scroll en ninguna página
```

## Criterios de aceptación
- [ ] Dashboard legible en 375px
- [ ] Inbox funcional en 375px (stack navigation)
- [ ] Sidebar oculto en mobile con hamburger
- [ ] Touch targets 44px+
- [ ] Sin horizontal scroll
- [ ] Desktop sin cambios visuales (no romper nada)
