# Chasqui — Centralización y Evolución de Noticias de Bolivia

**Chasqui** es una plataforma web diseñada para centralizar noticias de Bolivia desde **46 fuentes activas** (medios tradicionales, portales digitales independientes, redes de radios comunitarias/sindicales y prensa regional de los 9 departamentos), haciendo seguimiento longitudinal de cómo evolucionan las problemáticas a lo largo del tiempo.

---

## Estructura del Monorepo

```text
Chasqui/
├── Makefile                    # Comandos unificados para desarrollo, escaneo y verificación
├── package.json                # Scripts de conveniencia en la raíz
├── docker-compose.yml          # PostgreSQL 16 + pgvector (opcional en local)
├── .github/workflows/ci.yml    # Integración continua separada para Backend y Frontend
└── apps/
    ├── api/                    # Backend (Python + FastAPI + Scraper + Clustering Temporal)
    │   ├── Dockerfile          # Listo para desplegar en Railway / Render / Fly.io / Cloud Run
    │   ├── railway.json        # Configuración de despliegue para Railway
    │   └── app/
    │       ├── main.py         # API REST + Scheduler diario (06:00 BOT)
    │       ├── cli.py          # CLI: scan, status, seed
    │       ├── scraper/        # Catálogo de 46 fuentes bolivianas + colector concurrente RSS/HTML
    │       └── intelligence/   # NLP, detector de los 9 departamentos y clustering en 2 etapas
    └── web/                    # Frontend (Next.js App Router + TypeScript + Tailwind CSS)
        ├── vercel.json         # Listo para desplegar en Vercel (Root Directory: apps/web)
        └── src/                # Vistas: Radar, Línea de Tiempo (/hilos/[slug]), Archivo y Fuentes
```

---

## Comandos Rápidos (`Makefile`)

Desde la raíz del proyecto (`/home/redo/Documents/projects/Chasqui`):

```bash
# Instalar dependencias de ambos servicios (Python venv + npm)
make setup

# Iniciar Backend (http://localhost:8000)
make dev-api

# Iniciar Frontend (http://localhost:3000)
make dev-web

# Ejecutar un escaneo en vivo de las 46 fuentes bolivianas desde la terminal
make scan

# Ver resumen de hilos, eventos y distribución por departamento en la terminal
make status

# Validar código Python y tipos TypeScript
make check
```

---

## Despliegue Independiente desde el Monorepo

1. **Frontend (`apps/web`) en Vercel:**
   - Importa el repositorio `RedoRojo/Chasqui` en Vercel.
   - Define **Root Directory** = `apps/web`.
   - Configura la variable de entorno `NEXT_PUBLIC_API_URL` apuntando a la URL pública de tu backend.

2. **Backend + Cron Diario (`apps/api`) en Railway / Render / Fly.io:**
   - Conecta el mismo repositorio `RedoRojo/Chasqui`.
   - Define **Root Directory** = `apps/api` (detectará automáticamente `Dockerfile` y `railway.json`).
   - Opcionalmente vincula una instancia de PostgreSQL (`pgvector`) en la variable `DATABASE_URL`.
