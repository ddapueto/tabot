# Spec 08 — Landing Page | Requirements

## Meta
- Estado: ⏳ ready
- Prioridad: P2
- Impacto: Landing 0/10 → 8/10
- Depende de: ninguna (recomendado tener Spec 07 para que esté online)
- Branch: `feat/spec-08-landing`

## Problema
No hay página pública que explique qué es Tabot. Sin landing page no hay forma
de captar clientes nuevos. Un potencial usuario llega a la URL y ve solo un login.

## Appetite
1 sesión de Claude, max 2 horas.

## Requirements funcionales
- MUST: landing accesible sin login en `/` o `/landing`
- MUST: hero section con CTA prominente "Probalo gratis" → /login
- MUST: sección features (3 principales con descripciones)
- MUST: sección pricing con 3 planes (Starter $49, Pro $99, Business $199)
- MUST: responsive mobile-first
- MUST: mismo design system que el dashboard (dark theme, colores del tema)
- SHOULD: sección "Cómo funciona" (3 pasos)
- SHOULD: FAQ (5-6 preguntas)
- SHOULD: footer con links y contacto
- MAY: animaciones scroll-reveal

## Escenarios clave

```
GIVEN un usuario no registrado
WHEN visita la URL raíz
THEN ve la landing page con hero, features, pricing, CTA

GIVEN un usuario en la landing
WHEN hace click en "Probalo gratis"
THEN navega a /login con formulario de registro

GIVEN un usuario en móvil (375px)
WHEN ve la landing
THEN todo es legible y funcional sin horizontal scroll
```

## No-gos
- No usar framework de landing externo (hacer en SvelteKit)
- No agregar analytics de landing aún (Google Analytics futuro)
- No implementar registro real de planes/pagos (solo info)
- No usar screenshots del dashboard real (mockups o ilustraciones simples)
