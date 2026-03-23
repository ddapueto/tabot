# Spec 13 — Desacoplamiento Backend | Design

## Decisiones arquitectónicas

### ADR-1: Separar KB endpoints de settings_api.py
- **Contexto**: `settings_api.py` tiene 13 imports y maneja company config + AI config + KB CRUD + promos.
  Son 4 dominios en un archivo
- **Decisión**: Extraer KB endpoints a `app/api/kb.py` con su propio router.
  Registrar en `main.py` como `/api/kb`
- **Razón**: KB es un dominio independiente con sus propios modelos, schemas y lógica
- **Trade-off**: Un archivo más en api/, pero reduce imports de settings_api de 13 a ~8

### ADR-2: Extraer queries de analytics
- **Contexto**: `analytics.py` tiene queries SQL complejas inline que aumentan imports
  y hacen el archivo difícil de leer
- **Decisión**: Extraer queries pesadas a funciones en el mismo archivo (no crear archivo
  nuevo — las queries son específicas de analytics)
- **Razón**: Reduce largo de funciones, no agrega archivos innecesarios

### ADR-3: NO separar auth.py
- **Contexto**: `auth.py` tiene 13 imports pero es un dominio cohesivo (register, login,
  refresh, token creation, password hashing)
- **Decisión**: No separar. Los 13 imports son todos necesarios para auth
- **Razón**: Separar token logic de auth logic crearía acoplamiento artificial.
  13 imports es aceptable para un modulo de auth

### ADR-4: Instagram webhook helper
- **Contexto**: `webhooks/instagram.py` tiene 12 imports y mezcla HMAC verification,
  payload parsing, y handler dispatch
- **Decisión**: Extraer parsing de payload de Instagram a `_parse_instagram_event(body)`
  como función interna
- **Razón**: No reduce imports pero mejora legibilidad y testabilidad

## Archivos a modificar/crear

| Archivo | Acción | Imports antes→después |
|---------|--------|----------------------|
| `app/api/kb.py` | **CREAR** — KB CRUD endpoints extraidos de settings_api | ~8 imports |
| `app/api/settings_api.py` | Remover endpoints KB, reducir imports | 13→~8 |
| `app/api/analytics.py` | Extraer queries a helpers internos | 11→11 (mejora estructura) |
| `app/api/webhooks/instagram.py` | Extraer parser de payload | 12→12 (mejora estructura) |
| `app/services/follow_up_engine.py` | Revisar/eliminar imports no usados | 11→~9 |
| `app/tasks/follow_ups.py` | Revisar/eliminar imports no usados | 11→~9 |
| `app/main.py` | Registrar router `/api/kb` | +2 lineas |

## Registro de rutas (después)

```python
# main.py — routers
app.include_router(auth_router, prefix="/api/auth")
app.include_router(leads_router, prefix="/api/leads")
app.include_router(conversations_router, prefix="/api/conversations")
app.include_router(catalog_router, prefix="/api/catalog")
app.include_router(kb_router, prefix="/api/kb")        # ← NUEVO
app.include_router(settings_router, prefix="/api/settings")
app.include_router(analytics_router, prefix="/api/analytics")
# ... etc
```

## Impacto en frontend
- Si KB endpoints cambian de `/api/settings/kb/*` a `/api/kb/*`, actualizar `frontend/src/lib/api.ts`
  y `frontend/src/routes/settings/+page.svelte`
- Alternativa: mantener rutas viejas con redirect 301 (pero agrega complejidad innecesaria —
  mejor cambiar frontend directamente)
