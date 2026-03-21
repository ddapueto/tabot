# Spec 01 — Tests | Design

## Arquitectura de tests

```
tests/
├── conftest.py          # Fixtures compartidos (client, auth, company)
├── test_health.py       # ✅ Ya existe (1 test)
├── test_auth.py         # NUEVO: 8 tests de auth
├── test_leads.py        # NUEVO: 8 tests de leads
├── test_conversations.py # NUEVO: 3 tests de conversations
├── test_catalog.py      # NUEVO: 3 tests de catalog
├── test_onboarding.py   # NUEVO: 2 tests de onboarding
└── test_webhook_whatsapp.py # ✅ Ya existe (4 tests, mantener)
```

## Decisiones

### Fixture de auth
- **Decisión**: Usar endpoint de onboarding para crear empresa+user en cada test
- **Razón**: Es el flujo real, testea onboarding y genera token válido
- **Alternativa descartada**: Insertar directo en DB (no testea el flujo real)

### DB de test
- **Decisión**: Usar la misma DB de Docker (puerto 5435)
- **Razón**: Simplidad, ya está corriendo
- **Nota**: Los tests crean datos con onboarding, no contaminan datos del seed

### Patrón de test
```python
async def test_something(client, auth_headers):
    response = await client.get("/api/endpoint", headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert "expected_field" in data
```

## Archivos a crear/modificar

| Archivo | Acción | Líneas aprox |
|---------|--------|-------------|
| `tests/conftest.py` | crear | 30 |
| `tests/test_auth.py` | crear | 80 |
| `tests/test_leads.py` | crear | 90 |
| `tests/test_conversations.py` | crear | 40 |
| `tests/test_catalog.py` | crear | 40 |
| `tests/test_onboarding.py` | crear | 30 |
