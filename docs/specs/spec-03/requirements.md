# Spec 03 — Mobile Responsive | Requirements

## Meta
- Estado: ⏳ ready
- Prioridad: P1
- Impacto: Responsive 2/10 → 7/10
- Depende de: ninguna
- Branch: `feat/spec-03-mobile`

## Problema
El dashboard no es usable desde el celular del vendedor. El inbox (la página
más importante) no funciona en pantallas <768px. Sidebar siempre visible ocupa
espacio. Vendedores en calle necesitan responder desde el móvil.

## Appetite
1 sesión de Claude, max 2 horas.

## Requirements funcionales
- MUST: sidebar auto-colapsado en <768px con hamburger menu
- MUST: inbox en modo stack navigation en mobile (lista → chat → back)
- MUST: dashboard grid responsive (2 cols en mobile, 4 en desktop)
- MUST: leads detalle en modal/overlay en mobile
- MUST: touch targets mínimo 44x44px
- SHOULD: swipe right para abrir sidebar
- SHOULD: filtros colapsables en mobile
- MUST NOT: scroll horizontal en ninguna página

## Escenarios clave

```
GIVEN un vendedor en iPhone SE (375px)
WHEN abre el inbox
THEN ve solo la lista de conversaciones, sin chat ni panel

GIVEN un vendedor viendo la lista de conversaciones
WHEN toca una conversación
THEN ve solo el chat con botón back para volver a la lista

GIVEN una pantalla >1024px
WHEN abre el inbox
THEN ve las 3 columnas (lista + chat + panel contacto)
```

## No-gos
- No crear app nativa (PWA es suficiente por ahora)
- No cambiar el design system (mismos colores y tipografía)
- No optimizar para tablets específicamente (solo mobile + desktop)
