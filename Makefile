.PHONY: help setup dev-api dev-web scan seed status check clean

PYTHON := apps/api/.venv/bin/python
UVICORN := apps/api/.venv/bin/uvicorn

help:
	@echo "=== Comandos del Monorepo Chasqui ==="
	@echo "  make setup     - Instala dependencias de Backend (Python venv) y Frontend (Next.js)"
	@echo "  make dev-api   - Inicia el servidor FastAPI + Scheduler en http://localhost:8000"
	@echo "  make dev-web   - Inicia la aplicación web Next.js en http://localhost:3000"
	@echo "  make scan      - Ejecuta un escaneo en vivo de las 46 fuentes bolivianas desde CLI"
	@echo "  make status    - Muestra las estadísticas actuales de hilos, eventos y cobertura"
	@echo "  make seed      - Inicializa catálogo, base histórica y ejecuta escaneo inicial"
	@echo "  make check     - Valida sintaxis Python y chequeo de tipos TypeScript (tsc)"

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
