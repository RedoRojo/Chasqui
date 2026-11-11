# Chasqui — Centralización y Evolución de Noticias de Bolivia

**Chasqui** es una plataforma web diseñada para centralizar noticias de Bolivia desde fuentes tradicionales, regionales, comunitarias y medios digitales alternativos, haciendo seguimiento longitudinal de cómo evolucionan las problemáticas a lo largo del tiempo.

## Arquitectura del Proyecto

- `apps/api`: Backend en **Python + FastAPI + SQLAlchemy + pgvector**, motor de extracción y escaneo diario (`APScheduler`, `feedparser`, `BeautifulSoup`, `httpx`), detector geográfico de los 9 departamentos de Bolivia, generador de embeddings semánticos y motor de clustering temporal en 2 etapas (`Article` → `StoryEvent` → `StoryThread`).
- `apps/web`: Aplicación web en **Next.js (App Router) + TypeScript + Tailwind CSS**, con:
  - **Radar y Evolución (`/`)**: Hilos/problemáticas activas, medidor de brecha mediática (Alternativos/Comunitarios/Regionales vs. Masivos), filtro de puntos ciegos y botón de escaneo diario bajo demanda.
  - **Línea de Tiempo Longitudinal (`/hilos/[slug]`)**: Evolución cronológica de cada problemática desde su primer registro hasta el último suceso, con acceso a todas las fuentes que cubrieron cada hito.
  - **Archivo Histórico (`/archivo`)**: Buscador histórico y semántico por texto, rango de fechas, departamento, categoría y tipo de medio.
  - **Fuentes e Ingesta (`/fuentes`)**: Catálogo de 20 medios bolivianos monitoreados + formulario para agregar nuevas fuentes o ingresar reportes y comprobar en tiempo real cómo se agrupan en eventos e hilos.

## Cómo ejecutar el proyecto

### 1. Backend API (`http://localhost:8000`)

```bash
cd apps/api
.venv/bin/uvicorn app.main:app --reload --port 8000
```

*(Por defecto funciona directamente con SQLite local `chasqui.db` sin requerir Docker; para usar PostgreSQL 16 + `pgvector`, levanta `docker compose up -d` y configura `DATABASE_URL` en `.env`).*

### 2. Frontend Web (`http://localhost:3000`)

```bash
cd apps/web
npm run dev
```
