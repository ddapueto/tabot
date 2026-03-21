# Spec 08 — Landing Page | Tasks

## Tareas (ejecutar en orden)

- [ ] **T1**: Crear `frontend/src/routes/landing/+layout.svelte` — layout público sin sidebar, sin auth guard
- [ ] **T2**: Crear `frontend/src/routes/landing/+page.svelte` — hero section con título, subtítulo, CTA "Probalo gratis"
- [ ] **T3**: Agregar sección "Problema" — 3 pain points con iconos SVG inline
- [ ] **T4**: Agregar sección "Solución/Features" — 3 features principales con descripciones
- [ ] **T5**: Agregar sección "Cómo funciona" — 3 pasos (conectar WhatsApp, cargar catálogo, Tabot vende)
- [ ] **T6**: Agregar sección "Pricing" — 3 cards (Starter $49, Pro $99, Business $199) con features list
- [ ] **T7**: Agregar FAQ accordion (5-6 preguntas) + footer con links
- [ ] **T8**: Hacer responsive: verificar en 375px, ajustar grids y tipografía
- [ ] **T9**: Configurar redirect: `/` → `/landing` si usuario no autenticado

## Verificación
```bash
cd frontend && npm run dev
# Abrir http://localhost:5173/landing
# Verificar: hero, features, pricing, FAQ, footer
# F12 → 375px: todo legible sin horizontal scroll
# Click "Probalo gratis" → navega a /login
```

## Criterios de aceptación
- [ ] Landing accesible sin login
- [ ] Hero con CTA que lleva a /login
- [ ] Pricing con 3 planes
- [ ] Responsive en 375px
- [ ] Mismo design system que el dashboard
- [ ] FAQ funcional (accordion)
- [ ] CTA prominente y visible
