from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timezone
from email.utils import parsedate_to_datetime
import re
from typing import Any
from urllib.parse import urljoin, urlparse

from bs4 import BeautifulSoup
import feedparser
import httpx
from sqlalchemy.orm import Session

from app.config import settings
from app.intelligence.clustering import ingest_and_cluster_article
from app.models import Article, ScrapeRun, Source

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/130.0.0.0 Safari/537.36 ChasquiBot/1.0"
    ),
    "Accept": "application/rss+xml, application/xml, text/xml, text/html;q=0.9, */*;q=0.8",
}

NAV_JUNK = {
    "inicio", "portada", "contacto", "quienes somos", "publicidad", "terminos",
    "privacidad", "señal en vivo", "nuestra señal", "radio fm", "iniciar sesion",
    "suscribete", "edicion impresa", "multimedia", "galeria", "convocatoria externa",
    "the practical guide", "casino", "betting", "settlement rules",
}


def is_valid_news_title(title: str) -> bool:
    if not title or len(title) < 28 or len(title) > 250:
        return False
    lower = title.lower().strip()
    if lower in {"blanco", "noticias", "nacional", "economia", "politica", "sociedad"}:
        return False
    if any(j in lower for j in NAV_JUNK):
        return False
    if lower.startswith("por ") and len(lower.split()) <= 5:
        return False
    return True


def clean_html_text(raw_html: str) -> str:
    if not raw_html:
        return ""
    soup = BeautifulSoup(raw_html, "html.parser")
    for tag in soup(["script", "style", "nav", "footer", "aside", "noscript"]):
        tag.decompose()
    text = soup.get_text(separator=" ", strip=True)
    return re.sub(r"\s+", " ", text).strip()


def parse_entry_date(entry: Any) -> datetime:
    for field in ("published", "updated", "created"):
        val = getattr(entry, field, None) or entry.get(field)
        if val:
            try:
                dt = parsedate_to_datetime(val)
                if dt.tzinfo is None:
                    dt = dt.replace(tzinfo=timezone.utc)
                return dt
            except Exception:
                pass
    return datetime.now(timezone.utc)


def fetch_rss_items(source: Source, client: httpx.Client, limit: int) -> list[dict[str, Any]]:
    if not source.rss_url:
        return []
    resp = client.get(source.rss_url, timeout=7.5, follow_redirects=True)
    resp.raise_for_status()
    feed = feedparser.parse(resp.text)
    items: list[dict[str, Any]] = []
    for entry in feed.entries:
        title = clean_html_text(entry.get("title", ""))
        link = entry.get("link", "").strip()
        if not link or not is_valid_news_title(title):
            continue
        raw_summary = ""
        if entry.get("content"):
            raw_summary = entry.content[0].get("value", "")
        elif entry.get("summary"):
            raw_summary = entry.get("summary", "")
        elif entry.get("description"):
            raw_summary = entry.get("description", "")
        content = clean_html_text(raw_summary)
        if not content or len(content) < 30:
            content = title
        items.append(
            {
                "title": title,
                "url": link,
                "content": content[:1800],
                "published_at": parse_entry_date(entry),
            }
        )
        if len(items) >= limit:
            break
    return items


def fetch_html_portal_items(source: Source, client: httpx.Client, limit: int) -> list[dict[str, Any]]:
    resp = client.get(source.url, timeout=7.5, follow_redirects=True)
    resp.raise_for_status()
    soup = BeautifulSoup(resp.text, "html.parser")
    for tag in soup(["script", "style", "nav", "footer", "header", "noscript", "aside"]):
        tag.decompose()

    items: list[dict[str, Any]] = []
    seen_urls: set[str] = set()
    base_host = urlparse(source.url).netloc.replace("www.", "")

    for a_tag in soup.find_all("a", href=True):
        href = a_tag["href"].strip()
        full_url = urljoin(source.url, href)
        parsed = urlparse(full_url)
        if base_host not in parsed.netloc:
            continue
        path = parsed.path.rstrip("/")
        if len(path) < 18 or path.count("/") < 1:
            continue
        if any(seg in path.lower() for seg in ("/autor/", "/tag/", "/etiqueta/", "/categoria/", "/seccion/")):
            continue

        heading = a_tag.find(["h1", "h2", "h3", "h4", "span", "p"])
        raw_title = heading.get_text(" ", strip=True) if heading else a_tag.get_text(" ", strip=True)
        title = " ".join(raw_title.split())
        if not is_valid_news_title(title):
            continue
        if full_url in seen_urls:
            continue
        seen_urls.add(full_url)

        parent = a_tag.find_parent(["article", "div", "li"])
        snippet = ""
        if parent:
            for p_tag in parent.find_all("p"):
                txt = clean_html_text(p_tag.get_text())
                if len(txt) > 40 and txt.lower() != title.lower():
                    snippet = txt
                    break

        items.append(
            {
                "title": title,
                "url": full_url,
                "content": snippet if len(snippet) > 40 else title,
                "published_at": datetime.now(timezone.utc),
            }
        )
        if len(items) >= limit:
            break
    return items


def fetch_source_bundle(source_snapshot: dict[str, Any], limit: int) -> dict[str, Any]:
    """Executed concurrently in a worker pool to fetch articles from a source without blocking the DB."""
    dummy_src = Source(**source_snapshot)
    collected: list[dict[str, Any]] = []
    error_msg: str | None = None
    try:
        with httpx.Client(headers=HEADERS, verify=True) as client:
            if dummy_src.rss_url:
                collected = fetch_rss_items(dummy_src, client, limit=limit)
            if not collected:
                collected = fetch_html_portal_items(dummy_src, client, limit=limit)
    except Exception as exc:
        error_msg = str(exc)[:120]
    return {
        "slug": dummy_src.slug,
        "items": collected,
        "error": error_msg,
    }


def run_daily_scan(
    db: Session,
    trigger: str = "manual",
    source_slugs: list[str] | None = None,
    try_live_network: bool = True,
    max_per_source: int = 4,
) -> ScrapeRun:
    """
    Runs a concurrent scan across all active Bolivian news sources:
    Fetches live articles via RSS and clean HTML parsing, deduplicates by URL,
    and clusters them into StoryEvents and longitudinal StoryThreads.
    """
    run = ScrapeRun(
        started_at=datetime.now(timezone.utc),
        trigger=trigger,
        status="running",
    )
    db.add(run)
    db.commit()
    db.refresh(run)

    query = db.query(Source).filter(Source.is_active == True)  # noqa: E712
    if source_slugs:
        query = query.filter(Source.slug.in_(source_slugs))
    sources = query.all()
    source_map = {s.slug: s for s in sources}

    new_articles_count = 0
    new_events_count = 0
    updated_threads_count = 0
    per_source_stats: dict[str, Any] = {}

    if try_live_network and sources:
        snapshots = [
            {
                "id": s.id,
                "name": s.name,
                "slug": s.slug,
                "url": s.url,
                "rss_url": s.rss_url,
                "tier": s.tier,
                "department": s.department,
                "scrape_strategy": s.scrape_strategy,
            }
            for s in sources
        ]
        limit = min(max_per_source, settings.max_articles_per_source)
        bundles: list[dict[str, Any]] = []
        with ThreadPoolExecutor(max_workers=12) as pool:
            futures = [pool.submit(fetch_source_bundle, snap, limit) for snap in snapshots]
            for fut in as_completed(futures):
                bundles.append(fut.result())

        for bundle in bundles:
            slug = bundle["slug"]
            src = source_map.get(slug)
            if not src:
                continue
            items = bundle["items"]
            added_for_source = 0
            for item in items:
                existing = db.query(Article).filter(Article.url == item["url"]).first()
                if existing:
                    continue
                _, created_event, updated_thread = ingest_and_cluster_article(
                    db=db,
                    source=src,
                    title=item["title"],
                    url=item["url"],
                    content=item["content"],
                    published_at=item["published_at"],
                )
                added_for_source += 1
                new_articles_count += 1
                if created_event:
                    new_events_count += 1
                if updated_thread:
                    updated_threads_count += 1

            src.last_scraped_at = datetime.now(timezone.utc)
            per_source_stats[slug] = {
                "fetched": len(items),
                "new_articles": added_for_source,
                "status": "ok" if not bundle["error"] else "partial",
            }
        db.commit()

    run.finished_at = datetime.now(timezone.utc)
    run.status = "completed"
    run.sources_scanned = len(sources)
    run.new_articles = new_articles_count
    run.new_events = new_events_count
    run.updated_threads = updated_threads_count
    run.details = {"sources": per_source_stats}
    db.commit()
    db.refresh(run)
    return run
