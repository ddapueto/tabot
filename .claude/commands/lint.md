Run linting and formatting checks. Fix any issues found.

Backend:
```bash
cd backend && uv run ruff check --fix . && uv run ruff format . && uv run mypy app/
```

Frontend:
```bash
cd frontend && npm run lint -- --fix && npm run check
```

Report what was fixed and what needs manual attention.
