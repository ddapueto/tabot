# Spec 02 — CI/CD (GitHub Actions) | Design

## Arquitectura

```
.github/workflows/
└── ci.yml          # NUEVO: pipeline CI completo
    ├── job: backend   (ubuntu + PG + Redis)
    └── job: frontend  (ubuntu + Node 22)
```

## Decisiones

### Services en CI
- **Decisión**: Usar PostgreSQL (pgvector/pgvector:pg16) y Redis como GitHub Actions services
- **Razón**: Misma DB que producción, tests reales sin mocks
- **Nota**: pgvector extension se crea con psql antes de migraciones

### Herramientas de lint
- **Decisión**: ruff check + ruff format --check + mypy
- **Razón**: Ya están en el proyecto, consistente con desarrollo local
- **Alternativa descartada**: flake8/black (ruff los reemplaza)

### Variables de entorno en CI
- **Decisión**: AI_PROVIDER=groq con GROQ_API_KEY vacío, SECRET_KEY=test-secret
- **Razón**: Tests no llaman APIs reales, solo necesitan que la config no falle

### Frontend check
- **Decisión**: svelte-check + npm run build (no tests unitarios aún)
- **Razón**: svelte-check detecta errores de tipos, build verifica que compila

## Archivos a crear/modificar

| Archivo | Acción | Líneas aprox |
|---------|--------|-------------|
| `.github/workflows/ci.yml` | crear | 60 |
| `README.md` | modificar | +1 (badge) |
