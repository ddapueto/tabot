# Spec 04 — Notificaciones | Tasks

## Tareas (ejecutar en orden)

- [ ] **T1**: Crear `frontend/src/lib/notifications.ts` con funciones: `requestPermission()`, `notify(title, body, onClick)`, `playSound()` (Web Audio API), `updateTabBadge(count)`
- [ ] **T2**: Modificar `+layout.svelte` — listener SSE `new_message`: si conversación no seleccionada → playSound + notify + incrementar unread count + updateTabBadge
- [ ] **T3**: Pedir permiso de notificaciones al primer login (Notification.requestPermission)
- [ ] **T4**: Modificar `conversations/+page.svelte` — badge de unread count en cada conversación de la lista
- [ ] **T5**: Al seleccionar conversación → resetear su unread count y actualizar tab badge
- [ ] **T6**: Test manual: enviar webhook simulado, verificar sonido + notification + badge

## Verificación
```bash
# 1. Abrir dashboard en browser, permitir notificaciones
# 2. Enviar mensaje simulado:
curl -X POST http://localhost:8001/webhooks/whatsapp \
  -H "Content-Type: application/json" \
  -d '{"object":"whatsapp_business_account","entry":[...]}'
# 3. Verificar: sonido + desktop notification + "(1) Tabot" en tab
```

## Criterios de aceptación
- [ ] Sonido suena al recibir mensaje (conversación no activa)
- [ ] Desktop notification con preview del mensaje
- [ ] Tab title "(N) Tabot" con count
- [ ] Badge en lista de conversaciones
- [ ] Click en notification abre conversación
- [ ] No suena si la conversación está seleccionada
