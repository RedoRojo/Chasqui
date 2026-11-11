# Chasqui — Longitudinal News Aggregation & Media Blindspot Intelligence Platform

[![Next.js](https://img.shields.io/badge/Next.js-15-black?logo=next.js)](https://nextjs.org/)
[![React](https://img.shields.io/badge/React-19-149eca?logo=react)](https://react.dev/)
[![TypeScript](https://img.shields.io/badge/TypeScript-5.7-3178c6?logo=typescript)](https://www.typescriptlang.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.115+-009688?logo=fastapi)](https://fastapi.tiangolo.com/)
[![Python](https://img.shields.io/badge/Python-3.12+-3776ab?logo=python)](https://www.python.org/)
[![PostgreSQL + pgvector](https://img.shields.io/badge/PostgreSQL-pgvector-336791?logo=postgresql)](https://github.com/pgvector/pgvector)

**Chasqui** (named after the agile messengers of the Andean road system who connected distant regions) is a full-stack news intelligence and longitudinal tracking platform built to solve **media fragmentation, regional underrepresentation, and short-term news amnesia in Bolivia**.

Instead of presenting an ephemeral stream of isolated headlines, Chasqui ingests articles daily from **46 verified Bolivian news sources**—spanning mainstream television/newspapers, independent digital journalism, community radio networks, and regional press across all **9 departments**—and uses a **two-stage semantic clustering engine** to chain daily reports into evolving chronological timelines (`Articles` → `Events` → `Story Threads`).

---

## Why Chasqui Exists (Problem Statement)

In Bolivia, the information ecosystem suffers from three structural gaps:

1. **Geographic & Editorial Centralization (Media Blindspots):**
   Major television networks and legacy national newspapers concentrate their coverage on the central metropolitan axis. Critical developments in intermediate cities (such as El Alto, Montero, or Yacuiba), provincial municipalities, and rural territories are frequently covered only by local digital portals, regional newspapers, or community radio stations—never reaching national visibility.
2. **Fragmentation Across 40+ Independent & Regional Outlets:**
   Valuable investigative journalism, fact-checking, and grassroots reporting are scattered across dozens of heterogeneous websites and RSS feeds with no unified index or cross-source comparison.
3. **Ephemeral Headlines vs. Evolving Realities:**
   Standard news aggregators treat every article as a disconnected item. When a social conflict, judicial investigation, municipal budget crisis, or environmental emergency spans weeks or months, readers lose the historical thread of how the issue started, what agreements were signed, and how it evolved over time.

**Chasqui bridges this gap** by centralizing national and regional reporting into a single searchable observatory, automatically linking new daily developments to existing historical storylines, and quantifying the coverage balance between mainstream media and alternative/regional/community press.

---

## Key Engineering Highlights

- **Three-Tier Temporal Information Architecture:**
  Models news not as flat documents, but as a hierarchical graph:
  - **`Article`**: Individual source publication enriched with geographic department detection, named entities, thematic category, extractive summary, and a 128-dimensional semantic embedding vector.
  - **`StoryEvent`**: Time-windowed cluster ($\pm 96\text{h}$) grouping articles from multiple outlets that report on the same concrete occurrence, computing source-tier distribution.
  - **`StoryThread`**: Longitudinal storyline chaining sequential `StoryEvent` milestones over weeks or months to track the full lifecycle of a public issue.
- **Two-Stage Semantic & Entity Clustering Engine (`Python` / `NumPy` / `pgvector`):**
  Combines Spanish morphological stem normalization, domain-specific concept vectors, feature hashing of unigrams/bigrams, cosine similarity, named-entity overlap, and geographic weighting to automatically assign incoming articles to active events and link new events to historical threads.
- **Media Blindspot Detection & Coverage Asymmetry Metrics:**
  Classifies every source into four editorial tiers (`mainstream`, `alternative`, `community`, `regional`) and computes per-event and per-thread coverage ratios, surfacing **"Blindspot Events"** (*Puntos Ciegos*) that have $0\%$ coverage in traditional mass media.
- **High-Concurrency Multi-Strategy Scraper (`httpx` + `ThreadPoolExecutor` + `BeautifulSoup` + `feedparser`):**
  Scans **46 real Bolivian news portals** in parallel (~6 seconds per full national sweep), supporting both RSS/Atom syndication and heuristic DOM extraction with noise/navigation filtering and automated daily scheduling (`APScheduler` at `06:00 BOT`).
- **Performance-First & Accessible Editorial Web UI (`Next.js 15` + `React 19` + `Tailwind CSS v4`):**
  Implements `content-visibility: auto` paired with `contain-intrinsic-size` for zero-CLS off-screen feed rendering, native `<details>`/`<summary>` disclosures for Find-in-Page searchable source attributions, semantic `<search>` landmarks, and parallelized API data fetching.

---

## System Architecture

```mermaid
flowchart TD
    subgraph Sources["46 Verified Bolivian News Sources (9 Departments)"]
        S1["Mainstream TV & National Press\n(Unitel, Red Uno, El Deber, La Razón, Los Tiempos, Opinión...)"]
        S2["Digital Native, Investigative & Fact-Checking\n(Visión 360, Urgente.bo, Oxígeno, Brújula Digital, Bolivia Verifica...)"]
        S3["Community Radio Networks & Agencies\n(Red Erbol, ANF, Radio Fides, Panamericana, Kawsachun Coca, ACLO...)"]
        S4["Regional & Intermediate City Press\n(El Alteño, El País Tarija, La Patria Oruro, El Potosí, Sol de Pando...)"]
    end

    subgraph Engine["Ingestion & Temporal Intelligence Engine (Python / FastAPI)"]
        Scheduler["Daily Cron Scheduler (06:00 BOT) & CLI Runner"]
        Collector["Concurrent Collector (ThreadPoolExecutor + RSS + Clean DOM Parser)"]
        NLP["NLP Pipeline: 9-Dept Geo-Tagger + Entity Extractor + 128d Embeddings"]
        Stage1["Stage 1 Clustering: Intra-Window Event Grouping (StoryEvent)"]
        Stage2["Stage 2 Clustering: Longitudinal Thread Chaining (StoryThread)"]
    end

    subgraph Storage["Persistence Layer"]
        DB[("PostgreSQL 16 (pgvector) / SQLite\nSources · Articles · Events · Threads · ScrapeRuns")]
    end

    subgraph WebApp["Editorial Web Platform (Next.js 15 + TypeScript)"]
        Radar["Daily Radar & Media Blindspot Observatory (/)"]
        Timeline["Longitudinal Storyline Timeline (/hilos/[slug])"]
        Archive["Semantic & Historical Archive Search (/archivo)"]
        Directory["Source Observatory & Live Ingestion Sandbox (/fuentes)"]
    end

    S1 & S2 & S3 & S4 --> Collector
    Scheduler --> Collector
    Collector --> NLP
    NLP --> Stage1
    Stage1 --> Stage2
    Stage2 <--> DB
    DB --> Radar & Timeline & Archive & Directory
```

---

## Data Model (`PostgreSQL + pgvector` / `SQLAlchemy 2.0`)

```mermaid
erDiagram
    SOURCE ||--o{ ARTICLE : "publishes"
    STORY_EVENT ||--o{ ARTICLE : "clusters"
    STORY_THREAD ||--o{ STORY_EVENT : "evolves_through"

    SOURCE {
        string id PK
        string name
        string slug UK
        string url
        string rss_url
        string tier "mainstream | alternative | community | regional"
        string department "La Paz | Santa Cruz | Cochabamba | ..."
        string scrape_strategy "rss | html"
        int total_articles_collected
    }

    ARTICLE {
        string id PK
        string source_id FK
        string event_id FK
        string url UK
        string title
        text content
        text summary
        datetime published_at
        string department
        string category
        json entities
        vector embedding "128-dim semantic vector"
    }

    STORY_EVENT {
        string id PK
        string thread_id FK
        string title
        text summary
        datetime event_date
        string primary_department
        int mainstream_count
        int alternative_count
        int regional_count
        int community_count
        boolean is_blindspot
        vector centroid_embedding
    }

    STORY_THREAD {
        string id PK
        string title
        string slug UK
        text current_summary
        string status "active | monitoring | resolved"
        string category
        string primary_department
        json departments_affected
        json key_entities
        datetime first_seen_at
        datetime last_updated_at
        float blindspot_ratio
        vector thread_embedding
    }
```

---

## Monorepo Structure

```text
Chasqui/
├── Makefile                    # Unified developer & operations commands
├── package.json                # Root convenience scripts
├── docker-compose.yml          # PostgreSQL 16 + pgvector container definition
├── .github/workflows/ci.yml    # Automated CI pipeline for Backend (Python) & Frontend (Next.js)
└── apps/
    ├── api/                    # Python 3.12+ / FastAPI Backend & Scraping Engine
    │   ├── Dockerfile          # Production container image (Railway / Render / Fly.io / Cloud Run)
    │   ├── railway.json        # Railway deployment configuration
    │   ├── requirements.txt
    │   └── app/
    │       ├── main.py         # FastAPI endpoints & APScheduler lifecycle
    │       ├── cli.py          # CLI runner (scan, status, seed)
    │       ├── models.py       # SQLAlchemy 2.0 ORM models
    │       ├── schemas.py      # Pydantic v2 data contracts
    │       ├── scraper/
    │       │   ├── catalog.py  # 46 verified Bolivian news outlets across 4 tiers
    │       │   └── engine.py   # Concurrent RSS & HTML extraction engine
    │       └── intelligence/
    │           ├── nlp.py      # Bolivian geo-detector, NER, category classifier & embeddings
    │           └── clustering.py # Two-stage temporal clustering & blindspot scoring
    └── web/                    # Next.js 15 (App Router) + React 19 + TypeScript + Tailwind CSS v4
        ├── vercel.json         # Vercel deployment configuration
        └── src/
            ├── app/
            │   ├── page.tsx                # Daily Radar, Thread Evolution & Blindspot Filters
            │   ├── threads/[slug]/page.tsx # Interactive Longitudinal Timeline View
            │   ├── archive/page.tsx        # Historical & Semantic Search Archive
            │   └── sources/page.tsx        # Source Directory & Live Article Clustering Sandbox
            ├── components/
            │   ├── Navbar.tsx
            │   ├── CoverageMeter.tsx       # Visual bar comparing Alternative/Regional vs. Mainstream
            │   └── EventCard.tsx           # Event summary with searchable <details> source list
            └── lib/
                ├── api.ts
                └── types.ts
```

---

## Quick Start

### Prerequisites
- **Python** `>= 3.11`
- **Node.js** `>= 20` & `npm`
- *(Optional)* **Docker** for PostgreSQL 16 + `pgvector` (falls back automatically to local SQLite `chasqui.db` out of the box with zero configuration).

### 1. Install Dependencies
```bash
make setup
```

### 2. Initialize Database & Run Live Scan Across 46 Bolivian Portals
```bash
make seed
```

### 3. Start Backend & Frontend Servers
```bash
# Terminal 1 — Start FastAPI + Daily Scheduler on http://localhost:8000
make dev-api

# Terminal 2 — Start Next.js Web Application on http://localhost:3000
make dev-web
```

### 4. CLI Operations
```bash
# Trigger an on-demand live scan of all 46 Bolivian news sources
make scan

# Inspect current database metrics and top evolving story threads
make status

# Run Python compilation & TypeScript static type checks
make check
```

---

## REST API Overview

| Method | Endpoint | Description |
| :--- | :--- | :--- |
| `GET` | `/api/health` | Service health and daily cron schedule status (`06:00 BOT`) |
| `GET` | `/api/overview` | Global metrics, blindspot counts, department breakdown, and last scrape run |
| `GET` | `/api/threads` | List evolving story threads filtered by department, category, blindspot ratio, or semantic query `q` |
| `GET` | `/api/threads/{slug}` | Full chronological timeline of a story thread with all nested events and source articles |
| `GET` | `/api/events` | List clustered events filtered by department, category, or `blindspot_only=true` |
| `GET` | `/api/articles` | Historical archive search by semantic/keyword query, date range, department, and media tier |
| `GET` / `POST` | `/api/sources` | List all 46 monitored Bolivian sources or register a new media outlet |
| `POST` | `/api/scrape/run` | Trigger an immediate concurrent scrape across all active sources |
| `POST` | `/api/articles/ingest` | Ingest a custom article and return its automatically assigned `StoryEvent` and `StoryThread` |

---

## Deployment

The monorepo is pre-configured for independent cloud deployment:

- **Frontend (`apps/web`) → Vercel:** Import the repository into Vercel with **Root Directory** set to `apps/web` and set `NEXT_PUBLIC_API_URL` to your backend URL.
- **Backend & Daily Scraper (`apps/api`) → Railway / Render / Fly.io:** Connect the repository with **Root Directory** set to `apps/api` (uses `apps/api/Dockerfile` and `apps/api/railway.json`). Set `DATABASE_URL` to a PostgreSQL (`pgvector`) instance for persistent production storage.
