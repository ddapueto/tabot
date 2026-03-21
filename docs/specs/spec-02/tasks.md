# Spec 02 — CI/CD (GitHub Actions) | Tasks

## Tareas (ejecutar en orden)

- [ ] **T1**: Crear `.github/workflows/ci.yml` con 2 jobs: backend y frontend
- [ ] **T2**: Job backend — services: postgres (pgvector:pg16) + redis, steps: checkout, setup-uv, install, lint, format, typecheck, create pgvector extension, migrations, pytest
- [ ] **T3**: Job frontend — steps: checkout, setup-node 22, npm ci, svelte-check, build
- [ ] **T4**: Configurar env vars del job backend: DATABASE_URL, AI_PROVIDER, GROQ_API_KEY, META_VERIFY_TOKEN, SECRET_KEY
- [ ] **T5**: Agregar badge CI en README.md
- [ ] **T6**: Push a branch, crear PR, verificar que CI corre verde

## Verificación
```bash
# Crear PR y verificar en GitHub Actions
git push origin feat/spec-02-cicd
# Ver: https://github.com/ddapueto/tabot/actions
# Esperado: ambos jobs backend y frontend pasan verde
```

## Criterios de aceptación
- [ ] CI corre en push a main y en PRs
- [ ] Backend: lint + format + typecheck + migrations + tests pasan
- [ ] Frontend: svelte-check + build pasan
- [ ] Services PostgreSQL+pgvector+Redis funcionan en CI
- [ ] Badge visible en README
