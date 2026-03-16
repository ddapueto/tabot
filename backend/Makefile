.PHONY: dev test lint migrate

dev:
	uv run uvicorn app.main:app --reload --port 8000

test:
	uv run pytest -x -v

lint:
	uv run ruff check --fix .
	uv run ruff format .

typecheck:
	uv run mypy app/

migrate:
	uv run alembic upgrade head

migrate-create:
	uv run alembic revision --autogenerate -m "$(msg)"

install:
	uv sync --all-extras
