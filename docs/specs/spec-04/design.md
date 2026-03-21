# Spec 04 — Notificaciones | Design

## Arquitectura

```
SSE event (new_message)
  → +layout.svelte listener
    → notifications.ts
      ├── playSound()       ← Web Audio API (beep 800Hz, 150ms)
      ├── notify()          ← Notification API (desktop push)
      └── updateTabBadge()  ← document.title = "(N) Tabot"
```

## Decisiones

### Sonido con Web Audio API
- **Decisión**: Generar beep por código (oscillator 800Hz, gain 0.1, 150ms)
- **Razón**: Sin archivos externos, sin problemas de carga/path
- **Alternativa descartada**: Archivo .mp3 (necesita hosting, más complejidad)

### Conteo de unread
- **Decisión**: Estado en frontend (no en backend)
- **Razón**: Simplidad, un solo usuario por sesión, se resetea al recargar
- **Nota**: Si en futuro se necesita persistencia, agregar campo en DB

### Permisos de notificación
- **Decisión**: Pedir Notification.requestPermission() al primer login
- **Razón**: Necesita interacción del usuario (browser lo exige)
- **Alternativa descartada**: Pedir en landing (bloqueado por browsers)

## Archivos a crear/modificar

| Archivo | Acción | Líneas aprox |
|---------|--------|-------------|
| `frontend/src/lib/notifications.ts` | crear | 40 |
| `frontend/src/routes/+layout.svelte` | modificar | +15 (SSE listener) |
| `frontend/src/routes/conversations/+page.svelte` | modificar | +10 (badges, reset) |
