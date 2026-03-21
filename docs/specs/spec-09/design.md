# Spec 09 — WhatsApp Real (Meta Business API) | Design

## Arquitectura

```
WhatsApp user → Meta Cloud API → Webhook HTTPS
  → /webhooks/whatsapp (HMAC verify)
    → message_handler (lead + IA + response_validator)
      → whatsapp_client.send_message()
        → Meta Cloud API → WhatsApp user
```

## Decisiones

### Cuentas necesarias
- **Decisión**: Email dedicado (tabotapp@gmail.com), Facebook page "Tabot", Meta Business, Meta Developer App
- **Razón**: Separar cuentas personales de las del producto

### Token permanente
- **Decisión**: System User Token (no expira) en vez de temporal (24h)
- **Razón**: Token temporal requiere regenerar cada día — inaceptable en producción
- **Proceso**: Meta Business Settings → System Users → Generate Token

### Dev local con ngrok
- **Decisión**: Usar ngrok para desarrollo local (tunneling HTTPS)
- **Razón**: Meta requiere HTTPS para webhooks, ngrok lo provee gratis
- **Nota**: URL cambia cada reinicio — actualizar en Meta Dashboard

### HMAC validation
- **Decisión**: Ya implementada en whatsapp.py, mantener habilitada
- **Razón**: Seguridad — verificar que el request viene de Meta

## Archivos a crear/modificar

| Archivo | Acción | Cambio |
|---------|--------|--------|
| `backend/.env` | modificar | agregar credenciales Meta reales |
| `backend/app/services/whatsapp_client.py` | verificar | ya implementado, testear con creds reales |
| `backend/app/api/webhooks/whatsapp.py` | verificar | HMAC + processing, testear E2E |

## Gotchas
- Token temporal de Meta expira en 24h — crear System User Token
- ngrok gratis cambia URL cada reinicio — actualizar en Meta Dashboard
- Test number solo permite 5 destinatarios
- Webhook debe responder <5s (processing async ya implementado)
