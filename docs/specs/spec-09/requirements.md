# Spec 09 — WhatsApp Real (Meta Business API) | Requirements

## Meta
- Estado: ⏳ ready
- Prioridad: P0
- Impacto: WhatsApp 0/10 → 9/10
- Depende de: Spec 07 (deploy — necesita HTTPS para webhooks Meta)
- Branch: `feat/spec-09-whatsapp-real`

## Problema
WhatsApp solo funciona con webhooks simulados. No hay conexión real con Meta Cloud API.
Sin esto, Tabot no puede recibir ni responder mensajes de WhatsApp reales.
Es el core del producto.

## Appetite
1 sesión de Claude para código + 2 horas manual de configuración Meta.

## Requirements funcionales
- MUST: cuentas creadas (Gmail, Facebook, Meta Business, Meta Developer)
- MUST: app Meta con producto WhatsApp configurado
- MUST: credenciales en .env (META_APP_SECRET, WHATSAPP_PHONE_NUMBER_ID, WHATSAPP_ACCESS_TOKEN, META_VERIFY_TOKEN)
- MUST: webhook verificado por Meta (GET /webhooks/whatsapp → 200)
- MUST: mensaje de WhatsApp llega al servidor y crea lead
- MUST: IA responde con datos del catálogo
- MUST: respuesta llega al WhatsApp del cliente
- SHOULD: token permanente (System User Token, no temporal 24h)
- MUST NOT: usar token temporal en producción

## Escenarios clave

```
GIVEN Tabot desplegado con HTTPS
WHEN Meta envía verification request al webhook
THEN responde con hub.challenge y Meta verifica OK

GIVEN un cliente envía "Hola" por WhatsApp
WHEN el webhook recibe el mensaje
THEN se crea lead + la IA responde + el cliente recibe la respuesta

GIVEN el token de Meta expira
WHEN se usa System User Token
THEN el token no expira y el servicio sigue funcionando
```

## No-gos
- No pagar por número de teléfono de producción aún (usar test number)
- No configurar Instagram en esta spec (solo WhatsApp)
- No implementar templates de mensajes (solo mensajes de respuesta)
- No hacer tests E2E automatizados contra Meta (manual)
