.PHONY: help setup dev-api dev-web scan seed status check clean

PYTHON := apps/api/.venv/bin/python
UVICORN := apps/api/.venv/bin/uvicorn

help:
	@echo "=== Chasqui Monorepo Commands ==="
	@echo "  make setup     - Install Backend (Python venv) and Frontend (Next.js) dependencies"
	@echo "  make dev-api   - Start FastAPI server + Daily Scheduler on http://localhost:8000"
	@echo "  make dev-web   - Start Next.js web application on http://localhost:3000"
	@echo "  make scan      - Run a live concurrent scan across all 46 Bolivian news sources"
	@echo "  make status    - Print current database metrics, threads, events, and coverage share"
	@echo "  make seed      - Initialize source catalog, historical baseline, and initial live scan"
	@echo "  make check     - Validate Python syntax and TypeScript types (tsc --noEmit)"

setup:
	cd apps/api && python3 -m venv .venv && .venv/bin/pip install --upgrade pip && .venv/bin/pip install -r requirements.txt
	cd apps/web && npm install

dev-api:
	cd apps/api && .venv/bin/uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

dev-web:
	cd apps/web && npm run dev

scan:
	cd apps/api && .venv/bin/python -m app.cli scan

status:
	cd apps/api && .venv/bin/python -m app.cli status

seed:
	cd apps/api && .venv/bin/python -m app.cli seed

check:
	cd apps/api && .venv/bin/python -m py_compile app/*.py app/intelligence/*.py app/scraper/*.py
	cd apps/web && npx tsc --noEmit
