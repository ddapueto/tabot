# Spec 09 — WhatsApp Real (Meta Business API) | Tasks

## Tareas (ejecutar en orden)

- [ ] **T1**: (Manual) Crear email tabotapp@gmail.com
- [ ] **T2**: (Manual) Crear cuenta Facebook + página "Tabot"
- [ ] **T3**: (Manual) Crear Meta Business account en business.facebook.com
- [ ] **T4**: (Manual) Crear app en developers.facebook.com con producto WhatsApp
- [ ] **T5**: (Manual) Obtener credenciales: META_APP_SECRET, WHATSAPP_PHONE_NUMBER_ID, WHATSAPP_ACCESS_TOKEN, META_VERIFY_TOKEN
- [ ] **T6**: Configurar webhook en Meta Dashboard: URL = `https://DOMAIN/webhooks/whatsapp`, suscribir a `messages`
- [ ] **T7**: Actualizar .env en VPS con credenciales reales, restart api
- [ ] **T8**: Verificar webhook verification (Meta envía GET, server responde hub.challenge)
- [ ] **T9**: Agregar número personal como test number en Meta Dashboard
- [ ] **T10**: Test E2E: enviar "Hola" desde WhatsApp → verificar respuesta IA + lead en dashboard
- [ ] **T11**: (Futuro) Crear System User Token para token permanente

## Verificación
```bash
# Desde tu celular:
# 1. Enviar "Hola, qué productos tienen?" al test number
# 2. Verificar respuesta de la IA en WhatsApp
# 3. Verificar lead creado en dashboard

# Dev local alternativo:
ngrok http 8001
# Copiar URL HTTPS → Meta Dashboard → Webhook URL
```

## Criterios de aceptación
- [ ] Webhook verificado por Meta (GET → 200)
- [ ] Mensaje de WhatsApp llega al servidor
- [ ] Lead creado automáticamente
- [ ] IA responde con datos del catálogo
- [ ] Respuesta llega al WhatsApp del cliente
- [ ] Dashboard muestra la conversación
