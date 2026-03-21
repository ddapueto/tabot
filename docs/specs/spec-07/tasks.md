# Spec 07 — Deploy (VPS + Docker + Caddy) | Tasks

## Tareas (ejecutar en orden)

- [ ] **T1**: Crear `backend/Dockerfile` — python:3.12-slim, uv sync --no-dev, copy app/, uvicorn
- [ ] **T2**: Crear `frontend/Dockerfile` — multi-stage: node:22-alpine build → node:22-alpine run build/
- [ ] **T3**: Crear `docker-compose.prod.yml` — services: api, frontend, postgres (pgvector:pg16), redis, caddy, celery-worker, celery-beat; internal network; volumes para DB y caddy data
- [ ] **T4**: Crear `Caddyfile` — reverse proxy: /api/* y /webhooks/* → api:8000, /* → frontend:3000
- [ ] **T5**: Crear `deploy.sh` — ssh al VPS, git pull, docker compose up -d --build, run migrations, health check
- [ ] **T6**: Crear/actualizar `backend/.env.example` con todas las variables necesarias
- [ ] **T7**: (Manual) Contratar VPS, instalar Docker, clonar repo, configurar .env
- [ ] **T8**: (Manual) Ejecutar deploy.sh y verificar que todo arranca
- [ ] **T9**: Verificar health check desde internet: `curl https://DOMAIN/health`

## Verificación
```bash
# Local: probar que los Dockerfiles buildan
docker build -t tabot-api backend/
docker build -t tabot-frontend frontend/

# Producción:
curl https://app.tabot.com/health
# → {"status": "ok", ...}

# Verificar HTTPS:
curl -I https://app.tabot.com
# → HTTP/2 200, strict-transport-security header
```

## Criterios de aceptación
- [ ] URL pública carga el login con HTTPS
- [ ] Caddy genera certificado automáticamente
- [ ] Todos los servicios corriendo (api, frontend, db, redis, celery)
- [ ] Webhooks accesibles desde internet
- [ ] Health check responde OK
- [ ] DB y Redis no expuestos al exterior
