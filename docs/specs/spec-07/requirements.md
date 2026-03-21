# Spec 07 — Deploy (VPS + Docker + Caddy) | Requirements

## Meta
- Estado: ⏳ ready
- Prioridad: P0
- Impacto: Deploy 0/10 → 9/10
- Depende de: ninguna (recomendado tener Spec 01+02 antes)
- Branch: `feat/spec-07-deploy`

## Problema
Tabot solo corre en localhost. No se puede demostrar a clientes, no se puede
conectar WhatsApp real (requiere HTTPS), no se puede validar en condiciones reales.
Sin deploy no hay producto.

## Appetite
1 sesión de Claude para archivos + 1 hora manual de VPS setup.

## Requirements funcionales
- MUST: URL pública con HTTPS (Caddy automático)
- MUST: Dockerfiles para backend y frontend
- MUST: docker-compose.prod.yml con todos los servicios (api, frontend, postgres, redis, caddy, celery-worker, celery-beat)
- MUST: Caddyfile con reverse proxy (/api/* → backend, /webhooks/* → backend, / → frontend)
- MUST: script deploy.sh (pull, build, migrate, health check)
- MUST: health check accesible desde internet
- SHOULD: .env.example con todas las variables necesarias
- MUST NOT: exponer puertos de DB/Redis al exterior

## Escenarios clave

```
GIVEN el VPS con Docker instalado
WHEN se corre deploy.sh
THEN todos los servicios arrancan y https://app.tabot.com carga el login

GIVEN la app desplegada
WHEN Meta envía webhook a /webhooks/whatsapp
THEN el backend lo recibe y procesa correctamente

GIVEN un cambio en main
WHEN se corre deploy.sh en el VPS
THEN la nueva versión se despliega sin downtime (rebuild + restart)
```

## No-gos
- No configurar CD automático (deploy manual con script)
- No usar Kubernetes (overkill para MVP)
- No configurar backups automáticos de DB aún
- No comprar dominio en esta spec (usar IP o dominio temporal)
