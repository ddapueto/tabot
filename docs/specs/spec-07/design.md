# Spec 07 — Deploy (VPS + Docker + Caddy) | Design

## Arquitectura de producción

```
Internet → Caddy (HTTPS :443)
  ├── /api/*        → api:8000 (FastAPI)
  ├── /webhooks/*   → api:8000
  └── /*            → frontend:3000 (SvelteKit node)

Internal network (Docker):
  ├── postgres:5435 (pgvector:pg16)
  ├── redis:6379
  ├── celery-worker (same image as api)
  └── celery-beat (same image as api)
```

## Decisiones

### Caddy como reverse proxy
- **Decisión**: Caddy con HTTPS automático (Let's Encrypt)
- **Razón**: Zero-config HTTPS, más simple que nginx + certbot
- **Alternativa descartada**: Traefik (más complejo para un solo servicio)

### Frontend como Node server
- **Decisión**: SvelteKit build → node build/ (SSR)
- **Razón**: SvelteKit adapter-node es el default, soporta SSR
- **Alternativa descartada**: Static build + nginx (pierde SSR)

### VPS Hetzner CX22
- **Decisión**: 2 vCPU, 4GB RAM, $5/mes
- **Razón**: Suficiente para MVP, buena relación precio/rendimiento
- **Costo total**: ~$6/mes (VPS + dominio)

### Deploy manual con script
- **Decisión**: deploy.sh con SSH + git pull + docker compose up --build
- **Razón**: Simple, controlado, suficiente para MVP
- **Futuro**: CD automático en Spec futura

## Archivos a crear/modificar

| Archivo | Acción | Líneas aprox |
|---------|--------|-------------|
| `backend/Dockerfile` | crear | 15 |
| `frontend/Dockerfile` | crear | 15 |
| `docker-compose.prod.yml` | crear | 80 |
| `Caddyfile` | crear | 15 |
| `deploy.sh` | crear | 25 |
| `backend/.env.example` | crear/modificar | 20 |
