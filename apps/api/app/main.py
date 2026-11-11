from contextlib import asynccontextmanager
from datetime import datetime
from typing import Any

from apscheduler.schedulers.background import BackgroundScheduler
from fastapi import Depends, FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import func, or_
from sqlalchemy.orm import Session, joinedload

from app.config import settings
from app.database import SessionLocal, get_db, init_db
from app.intelligence.clustering import ingest_and_cluster_article
from app.intelligence.nlp import compute_embedding, cosine_similarity, slugify
from app.models import Article, ScrapeRun, Source, StoryEvent, StoryThread
from app.schemas import (
    ArticleIngestRequest,
    ArticleOut,
    DashboardOverviewOut,
    ScrapeRunOut,
    SourceCreate,
    SourceOut,
    StoryEventOut,
    StoryThreadDetailOut,
    StoryThreadOut,
)
from app.scraper.engine import run_daily_scan
from app.seed import seed_database

scheduler = BackgroundScheduler(timezone="America/La_Paz")


def scheduled_daily_job() -> None:
    db = SessionLocal()
    try:
        run_daily_scan(db, trigger="scheduled", try_live_network=True)
    finally:
        db.close()


@asynccontextmanager
async def lifespan(_app: FastAPI):
    init_db()
    db = SessionLocal()
    try:
        seed_database(db)
    finally:
        db.close()

    if settings.daily_scrape_enabled and not scheduler.running:
        scheduler.add_job(
            scheduled_daily_job,
            trigger="cron",
            hour=settings.daily_scrape_hour,
            minute=settings.daily_scrape_minute,
            id="chasqui_daily_scan",
            replace_existing=True,
        )
        scheduler.start()
    yield
    if scheduler.running:
        scheduler.shutdown(wait=False)


app = FastAPI(
    title="Chasqui API",
    description="API de centralización de noticias de Bolivia y seguimiento longitudinal de problemáticas.",
    version="0.1.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


def serialize_event(ev: StoryEvent) -> StoryEventOut:
    out = StoryEventOut.model_validate(ev)
    if ev.thread:
        out.thread_title = ev.thread.title
        out.thread_slug = ev.thread.slug
    return out


@app.get("/api/health")
def health_check() -> dict[str, Any]:
    return {
        "status": "ok",
        "service": "chasqui-api",
        "scheduler_active": scheduler.running,
        "daily_schedule": f"{settings.daily_scrape_hour:02d}:{settings.daily_scrape_minute:02d} BOT",
    }


@app.get("/api/overview", response_model=DashboardOverviewOut)
def get_overview(db: Session = Depends(get_db)) -> DashboardOverviewOut:
    total_threads = db.query(func.count(StoryThread.id)).scalar() or 0
    active_threads = (
        db.query(func.count(StoryThread.id)).filter(StoryThread.status == "active").scalar() or 0
    )
    total_events = db.query(func.count(StoryEvent.id)).scalar() or 0
    total_articles = db.query(func.count(Article.id)).scalar() or 0
    total_sources = db.query(func.count(Source.id)).filter(Source.is_active == True).scalar() or 0  # noqa: E712
    blindspot_events = (
        db.query(func.count(StoryEvent.id)).filter(StoryEvent.is_blindspot == True).scalar() or 0  # noqa: E712
    )

    mainstream_articles = (
        db.query(func.count(Article.id))
        .join(Source, Article.source_id == Source.id)
        .filter(Source.tier == "mainstream")
        .scalar()
        or 0
    )
    non_mainstream_articles = max(total_articles - mainstream_articles, 0)
    alt_share = round((non_mainstream_articles / total_articles) * 100.0, 1) if total_articles > 0 else 0.0

    dept_rows = (
        db.query(Article.department, func.count(Article.id))
        .group_by(Article.department)
        .order_by(func.count(Article.id).desc())
        .all()
    )
    departments_summary = [{"department": d, "articles_count": c} for d, c in dept_rows]

    cat_rows = (
        db.query(StoryThread.category, func.count(StoryThread.id))
        .group_by(StoryThread.category)
        .order_by(func.count(StoryThread.id).desc())
        .all()
    )
    categories_summary = [{"category": cat, "threads_count": c} for cat, c in cat_rows]

    last_scrape = db.query(ScrapeRun).order_by(ScrapeRun.started_at.desc()).first()

    return DashboardOverviewOut(
        total_threads=total_threads,
        active_threads=active_threads,
        total_events=total_events,
        total_articles=total_articles,
        total_sources=total_sources,
        blindspot_events_count=blindspot_events,
        alternative_coverage_share=alt_share,
        departments_summary=departments_summary,
        categories_summary=categories_summary,
        last_scrape=ScrapeRunOut.model_validate(last_scrape) if last_scrape else None,
    )


@app.get("/api/threads", response_model=list[StoryThreadOut])
def list_threads(
    department: str | None = Query(default=None),
    category: str | None = Query(default=None),
    status: str | None = Query(default=None),
    blindspot_only: bool = Query(default=False),
    q: str | None = Query(default=None),
    db: Session = Depends(get_db),
) -> list[StoryThreadOut]:
    query = db.query(StoryThread)
    if category and category != "Todas":
        query = query.filter(StoryThread.category == category)
    if status:
        query = query.filter(StoryThread.status == status)
    if blindspot_only:
        query = query.filter(StoryThread.blindspot_ratio >= 75.0)

    threads = query.order_by(StoryThread.last_updated_at.desc()).all()

    if department and department != "Todos":
        threads = [
            t
            for t in threads
            if t.primary_department == department or department in (t.departments_affected or [])
        ]

    if q and q.strip():
        q_clean = q.strip().lower()
        q_vec = compute_embedding(q_clean)
        scored: list[tuple[float, StoryThread]] = []
        for t in threads:
            lexical_hit = (
                q_clean in t.title.lower()
                or q_clean in t.current_summary.lower()
                or any(q_clean in ent.lower() for ent in (t.key_entities or []))
            )
            sem_sim = cosine_similarity(q_vec, t.thread_embedding or [])
            if lexical_hit or sem_sim >= 0.22:
                scored.append(((1.0 if lexical_hit else 0.0) + sem_sim, t))
        scored.sort(key=lambda item: item[0], reverse=True)
        threads = [t for _, t in scored]

    return [StoryThreadOut.model_validate(t) for t in threads]


@app.get("/api/threads/{slug}", response_model=StoryThreadDetailOut)
def get_thread_detail(slug: str, db: Session = Depends(get_db)) -> StoryThreadDetailOut:
    thread = (
        db.query(StoryThread)
        .options(
            joinedload(StoryThread.events)
            .joinedload(StoryEvent.articles)
            .joinedload(Article.source)
        )
        .filter(StoryThread.slug == slug)
        .first()
    )
    if not thread:
        raise HTTPException(status_code=404, detail="Hilo informativo no encontrado")

    # Sort events chronologically descending (with frontend option to toggle ascending/descending)
    thread.events.sort(key=lambda e: e.event_date, reverse=True)
    return StoryThreadDetailOut.model_validate(thread)


@app.get("/api/events", response_model=list[StoryEventOut])
def list_events(
    department: str | None = Query(default=None),
    category: str | None = Query(default=None),
    blindspot_only: bool = Query(default=False),
    limit: int = Query(default=30, ge=1, le=100),
    db: Session = Depends(get_db),
) -> list[StoryEventOut]:
    query = db.query(StoryEvent).options(
        joinedload(StoryEvent.articles).joinedload(Article.source),
        joinedload(StoryEvent.thread),
    )
    if department and department != "Todos":
        query = query.filter(StoryEvent.primary_department == department)
    if category and category != "Todas":
        query = query.filter(StoryEvent.category == category)
    if blindspot_only:
        query = query.filter(StoryEvent.is_blindspot == True)  # noqa: E712

    events = query.order_by(StoryEvent.event_date.desc()).limit(limit).all()
    return [serialize_event(ev) for ev in events]


@app.get("/api/articles", response_model=list[ArticleOut])
def search_articles(
    q: str | None = Query(default=None),
    department: str | None = Query(default=None),
    category: str | None = Query(default=None),
    tier: str | None = Query(default=None),
    source_slug: str | None = Query(default=None),
    from_date: str | None = Query(default=None),
    to_date: str | None = Query(default=None),
    limit: int = Query(default=60, ge=1, le=200),
    db: Session = Depends(get_db),
) -> list[ArticleOut]:
    query = db.query(Article).options(joinedload(Article.source)).join(Source, Article.source_id == Source.id)

    if department and department != "Todos":
        query = query.filter(Article.department == department)
    if category and category != "Todas":
        query = query.filter(Article.category == category)
    if tier and tier != "all":
        query = query.filter(Source.tier == tier)
    if source_slug:
        query = query.filter(Source.slug == source_slug)
    if from_date:
        try:
            dt_from = datetime.fromisoformat(from_date)
            query = query.filter(Article.published_at >= dt_from)
        except ValueError:
            pass
    if to_date:
        try:
            dt_to = datetime.fromisoformat(to_date)
            query = query.filter(Article.published_at <= dt_to)
        except ValueError:
            pass

    articles = query.order_by(Article.published_at.desc()).limit(limit).all()

    if q and q.strip():
        q_clean = q.strip().lower()
        q_vec = compute_embedding(q_clean)
        scored: list[tuple[float, Article]] = []
        for art in articles:
            lexical = (
                q_clean in art.title.lower()
                or q_clean in art.summary.lower()
                or q_clean in art.content.lower()
            )
            sem = cosine_similarity(q_vec, art.embedding or [])
            if lexical or sem >= 0.20:
                scored.append(((1.0 if lexical else 0.0) + sem, art))
        scored.sort(key=lambda item: item[0], reverse=True)
        articles = [art for _, art in scored]

    return [ArticleOut.model_validate(a) for a in articles]


@app.get("/api/sources", response_model=list[SourceOut])
def list_sources(
    tier: str | None = Query(default=None),
    department: str | None = Query(default=None),
    db: Session = Depends(get_db),
) -> list[SourceOut]:
    query = db.query(Source)
    if tier and tier != "all":
        query = query.filter(Source.tier == tier)
    if department and department != "Todos":
        query = query.filter(Source.department == department)
    sources = query.order_by(Source.tier.asc(), Source.name.asc()).all()
    return [SourceOut.model_validate(s) for s in sources]


@app.post("/api/sources", response_model=SourceOut)
def create_source(payload: SourceCreate, db: Session = Depends(get_db)) -> SourceOut:
    slug = slugify(payload.name)
    existing = db.query(Source).filter(or_(Source.slug == slug, Source.url == payload.url)).first()
    if existing:
        raise HTTPException(status_code=400, detail="Ya existe una fuente con ese nombre o URL.")
    src = Source(
        name=payload.name.strip(),
        slug=slug,
        url=payload.url.strip(),
        rss_url=payload.rss_url.strip() if payload.rss_url else None,
        tier=payload.tier,
        department=payload.department,
        scrape_strategy=payload.scrape_strategy,
        description=payload.description,
        is_active=True,
    )
    db.add(src)
    db.commit()
    db.refresh(src)
    return SourceOut.model_validate(src)


@app.post("/api/scrape/run", response_model=ScrapeRunOut)
def trigger_scrape(
    live_network: bool = Query(default=False, description="Intentar conexión en vivo a RSS/portales además de la cola diaria"),
    db: Session = Depends(get_db),
) -> ScrapeRunOut:
    run = run_daily_scan(db, trigger="manual", try_live_network=live_network)
    return ScrapeRunOut.model_validate(run)


@app.get("/api/scrape/runs", response_model=list[ScrapeRunOut])
def list_scrape_runs(limit: int = Query(default=10, ge=1, le=50), db: Session = Depends(get_db)) -> list[ScrapeRunOut]:
    runs = db.query(ScrapeRun).order_by(ScrapeRun.started_at.desc()).limit(limit).all()
    return [ScrapeRunOut.model_validate(r) for r in runs]


@app.post("/api/articles/ingest")
def ingest_custom_article(payload: ArticleIngestRequest, db: Session = Depends(get_db)) -> dict[str, Any]:
    source = db.query(Source).filter(Source.slug == payload.source_slug).first()
    if not source:
        raise HTTPException(status_code=404, detail="Fuente no encontrada")

    article, created_event, updated_thread = ingest_and_cluster_article(
        db=db,
        source=source,
        title=payload.title,
        url=payload.url,
        content=payload.content,
        published_at=payload.published_at,
        department_override=payload.department,
        category_override=payload.category,
    )
    db.commit()
    db.refresh(article)

    event = db.query(StoryEvent).filter(StoryEvent.id == article.event_id).first() if article.event_id else None
    thread = db.query(StoryThread).filter(StoryThread.id == event.thread_id).first() if event else None

    return {
        "article": ArticleOut.model_validate(article),
        "created_new_event": created_event,
        "updated_or_created_thread": updated_thread,
        "event_id": event.id if event else None,
        "event_title": event.title if event else None,
        "thread_slug": thread.slug if thread else None,
        "thread_title": thread.title if thread else None,
    }
