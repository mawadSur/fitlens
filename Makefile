.PHONY: install test api web migrate e2e

install:
	uv venv apps/api/.venv
	uv pip install --python apps/api/.venv/bin/python -r apps/api/requirements-dev.txt
	cd apps/web && npm install

test:
	cd apps/api && .venv/bin/python -m pytest -q
	cd apps/web && npx tsc --noEmit

api:
	cd apps/api && .venv/bin/uvicorn app.main:app --port 8000

web:
	cd apps/web && API_BASE=http://localhost:8000 npm run dev

migrate:
	cd apps/api && .venv/bin/alembic upgrade head

e2e:
	cd apps/web && npx playwright test
