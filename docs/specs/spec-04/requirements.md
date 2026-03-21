# Spec 04 — Notificaciones | Requirements

## Meta
- Estado: ⏳ ready
- Prioridad: P1
- Impacto: Notificaciones 2/10 → 7/10
- Depende de: ninguna (SSE ya existe)
- Branch: `feat/spec-04-notifications`

## Problema
El vendedor no se entera cuando llega un mensaje nuevo si no está mirando
la pantalla. Pierde ventas por no responder a tiempo. No hay sonido,
no hay badge, no hay push notification.

## Appetite
1 sesión de Claude, max 1.5 horas.

## Requirements funcionales
- MUST: sonido cuando llega mensaje y la conversación no está seleccionada
- MUST: desktop notification con preview del mensaje (requiere permiso)
- MUST: tab title muestra "(N) Tabot" con mensajes no leídos
- MUST: badge con count en lista de conversaciones
- MUST: click en notification abre la conversación correspondiente
- SHOULD: pedir permiso de notificaciones en primer login
- MUST NOT: sonar si la conversación ya está seleccionada (ya la estás viendo)
- MUST NOT: usar archivos de audio externos — generar beep con Web Audio API

## Escenarios clave

```
GIVEN un vendedor viendo la conversación de Lead A
WHEN llega mensaje de Lead B
THEN suena beep + desktop notification + tab "(1) Tabot"

GIVEN un vendedor viendo la conversación de Lead A
WHEN llega mensaje de Lead A
THEN NO suena, NO notification (ya está viéndola)

GIVEN 3 mensajes sin leer
WHEN el vendedor selecciona una conversación
THEN su badge se resetea y el tab se actualiza
```

## No-gos
- No implementar push notifications nativas (service worker) — solo Notification API
- No agregar preferencias de sonido/volumen (futuro)
- No persistir unread count en backend (solo estado frontend)
