from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timezone
from email.utils import parsedate_to_datetime
import json
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

SOCIAL_GENERIC_STREAM_PATTERNS = (
    "revista informativa en vivo",
    "informativo digital de panamericana",
    "noticiero al día",
    "noticiero cochabamba",
    "telepaís meridiano",
    "la mañana en directo",
    "contacto sur",
    "detrás de la verdad",
    "ultimo momento",
    "último momento",
    "en directo",
    "concurso de talentos",
    "game of thrones",
)


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


def clean_social_title(raw_title: str) -> str:
    """Normalizes social media / YouTube video titles and filters out generic full-program live streams."""
    if not raw_title:
        return ""
    # Strip leading decorative emojis and symbols
    cleaned = re.sub(r"^[\s🔴🔥📚🇧🇴🟢📰⚡⚠️🚨📢🎙️📺▶️•\-|]+", "", raw_title).strip()
    # Remove trailing date/show pipes such as '| El XQ de las Noticias | 11-11-2026' or '|12.11.26|'
    cleaned = re.sub(r"\s*[|l]\s*(?:El XQ de las Noticias|RTP Informa).*$", "", cleaned, flags=re.IGNORECASE)
    cleaned = re.sub(r"\s*\|?\s*\d{1,2}[./-]\d{1,2}[./-]\d{2,4}\s*\|?$", "", cleaned)
    cleaned = re.sub(r"\s+", " ", cleaned).strip(" -|.")

    lower = cleaned.lower()
    if any(pat in lower for pat in SOCIAL_GENERIC_STREAM_PATTERNS) and len(cleaned) < 68:
        return ""
    if lower.startswith("en vivo") and len(cleaned) < 48:
        return ""
    return cleaned


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
                try:
                    dt = datetime.fromisoformat(str(val).replace("Z", "+00:00"))
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


def resolve_youtube_feed_url(source: Source, client: httpx.Client) -> str | None:
    """Resolves a YouTube channel URL or @handle into an official Atom XML feed URL."""
    if source.rss_url and "youtube.com/feeds/videos.xml" in source.rss_url:
        return source.rss_url
    url = source.url.strip()
    m_direct = re.search(r"channel/(UC[a-zA-Z0-9_-]+)", url)
    if m_direct:
        return f"https://www.youtube.com/feeds/videos.xml?channel_id={m_direct.group(1)}"
    try:
        resp = client.get(url, timeout=7.5, follow_redirects=True)
        resp.raise_for_status()
        m_cid = re.search(r'"(?:channelId|externalId)":"(UC[a-zA-Z0-9_-]+)"', resp.text)
        if m_cid:
            return f"https://www.youtube.com/feeds/videos.xml?channel_id={m_cid.group(1)}"
    except Exception:
        return source.rss_url
    return source.rss_url


def fetch_youtube_items(source: Source, client: httpx.Client, limit: int) -> list[dict[str, Any]]:
    """Scrapes video dispatches from a Bolivian YouTube channel via its native Atom XML feed."""
    feed_url = resolve_youtube_feed_url(source, client)
    if not feed_url:
        return []
    resp = client.get(feed_url, timeout=7.5, follow_redirects=True)
    resp.raise_for_status()
    feed = feedparser.parse(resp.text)
    items: list[dict[str, Any]] = []
    for entry in feed.entries:
        raw_title = clean_html_text(entry.get("title", ""))
        title = clean_social_title(raw_title)
        link = entry.get("link", "").strip()
        if not link or not is_valid_news_title(title):
            continue
        raw_desc = entry.get("summary", "") or entry.get("media_description", "")
        desc = clean_html_text(raw_desc)
        # Filter boilerplate channel links from descriptions
        desc_lines = [
            ln.strip()
            for ln in desc.splitlines()
            if ln.strip() and not ln.strip().lower().startswith(("suscríbete", "siguenos", "síguenos", "http"))
        ]
        clean_desc = " ".join(desc_lines).strip()
        if not clean_desc or len(clean_desc) < 35 or clean_desc.lower() == raw_title.lower():
            content = f"[YouTube Video Dispatch · {source.name}] {title}"
        else:
            content = f"{title}. {clean_desc}"
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


def fetch_telegram_items(source: Source, client: httpx.Client, limit: int) -> list[dict[str, Any]]:
    """Scrapes public Telegram channels via Telegram's static web preview (https://t.me/s/<channel>)."""
    url = source.url.strip()
    parsed = urlparse(url)
    path_parts = [p for p in parsed.path.split("/") if p]
    if not path_parts:
        return []
    handle = path_parts[-1].lstrip("@")
    preview_url = f"https://t.me/s/{handle}"

    resp = client.get(preview_url, timeout=7.5, follow_redirects=True)
    resp.raise_for_status()
    soup = BeautifulSoup(resp.text, "html.parser")
    wraps = soup.select(".tgme_widget_message_wrap")
    items: list[dict[str, Any]] = []

    for wrap in reversed(wraps):
        text_el = wrap.select_one(".tgme_widget_message_text")
        if not text_el:
            continue
        full_text = clean_html_text(text_el.decode_contents())
        if len(full_text) < 35:
            continue
        first_sentence = re.split(r"(?<=[.!?])\s+|\n", full_text)[0]
        title = clean_social_title(first_sentence[:140])
        if len(title) < 28:
            title = clean_social_title(full_text[:120])
        if not is_valid_news_title(title):
            continue

        date_link = wrap.select_one("a.tgme_widget_message_date")
        post_url = date_link["href"] if date_link and date_link.has_attr("href") else preview_url
        pub_dt = datetime.now(timezone.utc)
        time_el = wrap.select_one("time[datetime]")
        if time_el and time_el.has_attr("datetime"):
            try:
                pub_dt = datetime.fromisoformat(str(time_el["datetime"]).replace("Z", "+00:00"))
            except Exception:
                pass

        items.append(
            {
                "title": title,
                "url": post_url,
                "content": full_text[:1800],
                "published_at": pub_dt,
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


def detect_social_platform(url: str) -> str:
    host = urlparse(url).netloc.lower()
    if "youtube.com" in host or "youtu.be" in host:
        return "youtube"
    if "tiktok.com" in host:
        return "tiktok"
    if "t.me" in host or "telegram.me" in host:
        return "telegram"
    if "x.com" in host or "twitter.com" in host:
        return "x"
    if "facebook.com" in host or "fb.watch" in host or "fb.com" in host:
        return "facebook"
    return "web"


def extract_social_or_web_post(url: str) -> dict[str, Any]:
    """
    Extracts structured headline, full text/description, author/outlet, and platform metadata
    from a single social media post/video URL (YouTube, TikTok, X/Twitter, Telegram, Facebook)
    or digital news article URL.
    """
    clean_url = url.strip()
    platform = detect_social_platform(clean_url)
    title = ""
    content = ""
    author = ""

    with httpx.Client(headers=HEADERS, follow_redirects=True, timeout=10.0) as client:
        if platform == "youtube":
            # 1. Query YouTube oEmbed for accurate title and channel name
            try:
                oembed = client.get(
                    "https://www.youtube.com/oembed",
                    params={"url": clean_url, "format": "json"},
                )
                if oembed.status_code == 200:
                    data = oembed.json()
                    title = clean_social_title(data.get("title", "")) or data.get("title", "")
                    author = data.get("author_name", "YouTube Channel")
            except Exception:
                pass

            # 2. Fetch watch page to extract full video description (shortDescription)
            try:
                page = client.get(clean_url)
                m_desc = re.search(r'"shortDescription":"((?:\\.|[^"\\])*)"', page.text)
                if m_desc:
                    decoded_desc = json.loads(f'"{m_desc.group(1)}"')
                    cleaned_desc = re.sub(r"\s+", " ", decoded_desc).strip()
                    if cleaned_desc:
                        content = f"{title}. {cleaned_desc}" if title else cleaned_desc
                if not title:
                    m_title = re.search(r'"title":"((?:\\.|[^"\\])*)"', page.text)
                    if m_title:
                        title = clean_social_title(json.loads(f'"{m_title.group(1)}"'))
            except Exception:
                pass

        elif platform == "tiktok":
            # TikTok official oEmbed returns full video caption and creator handle without login walls
            try:
                oembed = client.get("https://www.tiktok.com/oembed", params={"url": clean_url})
                if oembed.status_code == 200:
                    data = oembed.json()
                    caption = (data.get("title") or "").strip()
                    author = data.get("author_name") or "TikTok Creator"
                    title = clean_social_title(caption[:140]) or caption[:140]
                    content = f"[TikTok Dispatch · @{author}] {caption}"
            except Exception:
                pass

        elif platform == "x":
            # Use FxTwitter public JSON API for zero-auth tweet extraction
            parsed = urlparse(clean_url)
            api_url = f"https://api.fxtwitter.com{parsed.path}"
            try:
                resp = client.get(api_url)
                if resp.status_code == 200:
                    tweet = resp.json().get("tweet", {})
                    tweet_text = (tweet.get("text") or "").strip()
                    author_obj = tweet.get("author") or {}
                    author = author_obj.get("name") or author_obj.get("screen_name") or "X / Twitter"
                    title = clean_social_title(tweet_text[:135]) or tweet_text[:135]
                    content = f"[X/Twitter Dispatch · {author}] {tweet_text}"
            except Exception:
                pass

        elif platform == "telegram":
            # Append ?embed=1 to fetch Telegram's clean single-post widget HTML
            embed_url = clean_url if "embed=1" in clean_url else f"{clean_url.rstrip('/')}?embed=1"
            try:
                resp = client.get(embed_url)
                soup = BeautifulSoup(resp.text, "html.parser")
                author_el = soup.select_one(".tgme_widget_message_owner_name")
                text_el = soup.select_one(".tgme_widget_message_text")
                author = clean_html_text(author_el.get_text()) if author_el else "Telegram Channel"
                if text_el:
                    full_text = clean_html_text(text_el.decode_contents())
                    title = clean_social_title(full_text[:135]) or full_text[:135]
                    content = full_text
            except Exception:
                pass

        # Fallback / Primary OpenGraph & Article body extraction (Facebook & Web portals)
        if not title or not content:
            try:
                resp = client.get(clean_url)
                soup = BeautifulSoup(resp.text, "html.parser")

                def meta_content(prop: str) -> str:
                    tag = soup.find("meta", attrs={"property": prop}) or soup.find(
                        "meta", attrs={"name": prop}
                    )
                    return tag["content"].strip() if tag and tag.has_attr("content") else ""

                if not title:
                    og_title = meta_content("og:title") or meta_content("twitter:title")
                    if not og_title and soup.title:
                        og_title = soup.title.get_text(strip=True)
                    title = clean_social_title(og_title) or og_title

                if not author:
                    author = (
                        meta_content("og:site_name")
                        or meta_content("author")
                        or urlparse(clean_url).netloc.replace("www.", "")
                    )

                if not content:
                    og_desc = meta_content("og:description") or meta_content("description")
                    paragraphs = [
                        clean_html_text(p.get_text())
                        for p in soup.find_all("p")
                        if len(clean_html_text(p.get_text())) > 45
                    ]
                    body_text = " ".join(paragraphs[:6])
                    content = body_text if len(body_text) > len(og_desc) else og_desc
            except Exception:
                pass

    if not title:
        raise ValueError("Could not extract a headline from the provided URL.")
    if not content:
        content = title

    return {
        "url": clean_url,
        "platform": platform,
        "author_or_outlet": author or platform.capitalize(),
        "title": title[:240],
        "content": content[:2200],
        "published_at": datetime.now(timezone.utc),
    }


def fetch_source_bundle(source_snapshot: dict[str, Any], limit: int) -> dict[str, Any]:
    """Executed concurrently in a worker pool to fetch articles from a source without blocking the DB."""
    dummy_src = Source(**source_snapshot)
    collected: list[dict[str, Any]] = []
    error_msg: str | None = None
    try:
        with httpx.Client(headers=HEADERS, verify=True) as client:
            strategy = (dummy_src.scrape_strategy or "").lower()
            if strategy == "youtube" or "youtube.com" in dummy_src.url.lower():
                collected = fetch_youtube_items(dummy_src, client, limit=limit)
            elif strategy == "telegram" or "t.me/" in dummy_src.url.lower():
                collected = fetch_telegram_items(dummy_src, client, limit=limit)
            else:
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
    Runs a concurrent scan across all active Bolivian news sources (RSS, HTML portals,
    YouTube broadcast channels, and Telegram public channels):
    Fetches live dispatches, deduplicates by URL, and clusters them into StoryEvents
    and longitudinal StoryThreads.
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
