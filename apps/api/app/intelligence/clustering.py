from datetime import datetime, timedelta, timezone
from sqlalchemy.orm import Session

from app.config import settings
from app.intelligence.nlp import (
    average_embeddings,
    classify_category,
    compute_embedding,
    cosine_similarity,
    detect_all_departments,
    detect_department,
    extract_entities,
    generate_summary,
    slugify,
)
from app.models import Article, Source, StoryEvent, StoryThread


def ensure_aware(dt: datetime) -> datetime:
    if dt.tzinfo is None:
        return dt.replace(tzinfo=timezone.utc)
    return dt


def recompute_event_metrics(db: Session, event: StoryEvent) -> None:
    articles = db.query(Article).filter(Article.event_id == event.id).all()
    if not articles:
        return

    mainstream = 0
    alternative = 0
    regional = 0
    community = 0
    vectors: list[list[float]] = []
    entities_seen: list[str] = list(event.entities or [])

    for art in articles:
        source = art.source or db.query(Source).filter(Source.id == art.source_id).first()
        tier = source.tier if source else "alternative"
        if tier == "mainstream":
            mainstream += 1
        elif tier == "regional":
            regional += 1
        elif tier == "community":
            community += 1
        else:
            alternative += 1

        if art.embedding:
            vectors.append(art.embedding)
        for ent in art.entities or []:
            if ent not in entities_seen:
                entities_seen.append(ent)

    non_mainstream = alternative + regional + community
    total = mainstream + non_mainstream
    event.mainstream_count = mainstream
    event.alternative_count = alternative
    event.regional_count = regional
    event.community_count = community
    event.is_blindspot = mainstream == 0 or (total >= 3 and (non_mainstream / total) >= 0.8)
    event.entities = entities_seen[:8]
    if vectors:
        event.centroid_embedding = average_embeddings(vectors)


def recompute_thread_metrics(db: Session, thread: StoryThread) -> None:
    events = (
        db.query(StoryEvent)
        .filter(StoryEvent.thread_id == thread.id)
        .order_by(StoryEvent.event_date.asc())
        .all()
    )
    if not events:
        return

    total_articles = 0
    mainstream_total = 0
    non_mainstream_total = 0
    depts: list[str] = list(thread.departments_affected or [])
    entities: list[str] = list(thread.key_entities or [])
    vectors: list[list[float]] = []

    for ev in events:
        recompute_event_metrics(db, ev)
        ev_non_main = ev.alternative_count + ev.regional_count + ev.community_count
        ev_total = ev.mainstream_count + ev_non_main
        total_articles += max(ev_total, 1)
        mainstream_total += ev.mainstream_count
        non_mainstream_total += ev_non_main
        if ev.primary_department and ev.primary_department not in depts and ev.primary_department != "Nacional":
            depts.append(ev.primary_department)
        for ent in ev.entities or []:
            if ent not in entities:
                entities.append(ent)
        if ev.centroid_embedding:
            vectors.append(ev.centroid_embedding)

    thread.events_count = len(events)
    thread.articles_count = total_articles
    thread.mainstream_count = mainstream_total
    thread.alternative_count = non_mainstream_total
    denom = mainstream_total + non_mainstream_total
    thread.blindspot_ratio = round((non_mainstream_total / denom) * 100.0, 1) if denom > 0 else 100.0
    thread.first_seen_at = ensure_aware(events[0].event_date)
    thread.last_updated_at = ensure_aware(events[-1].event_date)
    thread.departments_affected = depts or [thread.primary_department]
    thread.key_entities = entities[:10]
    if vectors:
        thread.thread_embedding = average_embeddings(vectors)


def match_or_create_thread(
    db: Session,
    title: str,
    summary: str,
    category: str,
    department: str,
    entities: list[str],
    embedding: list[float],
    event_date: datetime,
) -> tuple[StoryThread, bool]:
    """Busca un hilo histórico o activo al que pertenezca este evento, o crea uno nuevo."""
    threads = db.query(StoryThread).all()
    best_thread: StoryThread | None = None
    best_score = 0.0

    for th in threads:
        sim = cosine_similarity(embedding, th.thread_embedding or [])
        shared_entities = len(set(e.lower() for e in entities) & set(e.lower() for e in (th.key_entities or [])))
        dept_bonus = 0.07 if (department != "Nacional" and (department == th.primary_department or department in (th.departments_affected or []))) else 0.0
        cat_bonus = 0.06 if category == th.category else 0.0
        entity_bonus = min(shared_entities * 0.10, 0.25)
        score = sim + dept_bonus + cat_bonus + entity_bonus

        if score > best_score:
            best_score = score
            best_thread = th

    if best_thread and best_score >= settings.thread_similarity_threshold:
        best_thread.current_summary = summary
        if ensure_aware(event_date) > ensure_aware(best_thread.last_updated_at):
            best_thread.last_updated_at = ensure_aware(event_date)
        return best_thread, False

    base_slug = slugify(title)
    slug = base_slug
    counter = 2
    while db.query(StoryThread).filter(StoryThread.slug == slug).first() is not None:
        slug = f"{base_slug}-{counter}"
        counter += 1

    new_thread = StoryThread(
        title=title,
        slug=slug,
        current_summary=summary,
        status="active",
        category=category,
        primary_department=department,
        departments_affected=[department] if department != "Nacional" else ["Nacional"],
        key_entities=entities[:8],
        first_seen_at=ensure_aware(event_date),
        last_updated_at=ensure_aware(event_date),
        thread_embedding=embedding,
    )
    db.add(new_thread)
    db.flush()
    return new_thread, True


def ingest_and_cluster_article(
    db: Session,
    source: Source,
    title: str,
    url: str,
    content: str,
    published_at: datetime | None = None,
    department_override: str | None = None,
    category_override: str | None = None,
) -> tuple[Article, bool, bool]:
    """
    Procesa un artículo entrante:
    - Si ya existe por URL, lo devuelve sin duplicar.
    - Si es nuevo, extrae metadatos y vector, lo agrupa en un StoryEvent (nuevo o existente)
      y vincula ese evento a un StoryThread longitudinal (nuevo o en evolución).
    Retorna: (article, created_new_event, updated_or_created_thread)
    """
    existing = db.query(Article).filter(Article.url == url).first()
    if existing:
        return existing, False, False

    pub_dt = ensure_aware(published_at or datetime.now(timezone.utc))
    dept = department_override or detect_department(title, content, fallback=source.department)
    category = category_override or classify_category(title, content)
    entities = extract_entities(title, content)
    summary = generate_summary(title, content)
    embedding = compute_embedding(f"{title} {title} {summary} {' '.join(entities)} {dept}")

    article = Article(
        source_id=source.id,
        url=url,
        title=title.strip(),
        content=content.strip() or summary,
        summary=summary,
        published_at=pub_dt,
        department=dept,
        category=category,
        entities=entities,
        embedding=embedding,
    )
    db.add(article)
    db.flush()

    # Etapa 1: Buscar StoryEvent cercano en el tiempo (±96 horas)
    window_start = pub_dt - timedelta(hours=96)
    window_end = pub_dt + timedelta(hours=96)
    recent_events = (
        db.query(StoryEvent)
        .filter(StoryEvent.event_date >= window_start, StoryEvent.event_date <= window_end)
        .all()
    )

    best_event: StoryEvent | None = None
    best_event_score = 0.0
    for ev in recent_events:
        sim = cosine_similarity(embedding, ev.centroid_embedding or [])
        shared_ent = len(set(e.lower() for e in entities) & set(e.lower() for e in (ev.entities or [])))
        dept_bonus = 0.06 if (dept != "Nacional" and dept == ev.primary_department) else 0.0
        cat_bonus = 0.05 if category == ev.category else 0.0
        score = sim + min(shared_ent * 0.09, 0.22) + dept_bonus + cat_bonus
        if score > best_event_score:
            best_event_score = score
            best_event = ev

    created_new_event = False
    if best_event and best_event_score >= settings.event_similarity_threshold:
        article.event_id = best_event.id
        db.flush()
        recompute_event_metrics(db, best_event)
        thread = db.query(StoryThread).filter(StoryThread.id == best_event.thread_id).first()
        if thread:
            recompute_thread_metrics(db, thread)
        return article, False, True

    # Etapa 2: Es un suceso nuevo -> Vincular a un StoryThread existente o crear uno nuevo
    thread, _ = match_or_create_thread(
        db=db,
        title=title.strip(),
        summary=summary,
        category=category,
        department=dept,
        entities=entities,
        embedding=embedding,
        event_date=pub_dt,
    )

    new_event = StoryEvent(
        thread_id=thread.id,
        title=title.strip(),
        summary=summary,
        event_date=pub_dt,
        primary_department=dept,
        category=category,
        entities=entities,
        centroid_embedding=embedding,
    )
    db.add(new_event)
    db.flush()

    article.event_id = new_event.id
    source.total_articles_collected = (source.total_articles_collected or 0) + 1
    source.last_scraped_at = datetime.now(timezone.utc)
    db.flush()

    recompute_event_metrics(db, new_event)
    recompute_thread_metrics(db, thread)
    created_new_event = True
    return article, created_new_event, True
