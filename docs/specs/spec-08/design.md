# Spec 08 — Landing Page | Design

## Arquitectura

```
frontend/src/routes/
├── landing/
│   ├── +layout.svelte    # NUEVO: layout sin sidebar (público)
│   └── +page.svelte      # NUEVO: landing page completa
```

## Secciones de la landing

1. **Hero** — título, subtítulo, CTA, screenshot/mockup
2. **Problema** — 3 pain points con iconos
3. **Solución** — 3 features principales
4. **Cómo funciona** — 3 pasos (conectar, cargar, vender)
5. **Pricing** — 3 planes en cards
6. **FAQ** — accordion con 5-6 preguntas
7. **Footer** — links, contacto, legal

## Decisiones

### Layout separado
- **Decisión**: `/landing/+layout.svelte` sin sidebar ni auth guard
- **Razón**: La landing es pública, no debe tener elementos del dashboard
- **Nota**: El layout del dashboard sigue en `+layout.svelte` con auth

### Pricing informativo
- **Decisión**: Cards con precios y features, CTA lleva a /login (registro)
- **Razón**: No hay sistema de pagos aún, el pricing es informativo
- **Futuro**: Integrar Stripe cuando haya pagos reales

### Design system compartido
- **Decisión**: Mismos colores, tipografía y dark theme que el dashboard
- **Razón**: Coherencia visual, el usuario reconoce la marca al entrar

## Archivos a crear/modificar

| Archivo | Acción | Líneas aprox |
|---------|--------|-------------|
| `frontend/src/routes/landing/+layout.svelte` | crear | 20 |
| `frontend/src/routes/landing/+page.svelte` | crear | 250 |
| `frontend/src/routes/+layout.svelte` | modificar | redirect / → /landing si no auth |
