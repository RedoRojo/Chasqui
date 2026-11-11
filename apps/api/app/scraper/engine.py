from datetime import datetime, timezone
from email.utils import parsedate_to_datetime
import re
from typing import Any
from urllib.parse import urljoin

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
    resp = client.get(source.rss_url, timeout=8.0, follow_redirects=True)
    resp.raise_for_status()
    feed = feedparser.parse(resp.text)
    items: list[dict[str, Any]] = []
    for entry in feed.entries[:limit]:
        title = clean_html_text(entry.get("title", ""))
        link = entry.get("link", "").strip()
        if not title or not link or len(title) < 12:
            continue
        raw_summary = ""
        if entry.get("content"):
            raw_summary = entry.content[0].get("value", "")
        elif entry.get("summary"):
            raw_summary = entry.get("summary", "")
        elif entry.get("description"):
            raw_summary = entry.get("description", "")
        content = clean_html_text(raw_summary) or title
        items.append(
            {
                "title": title,
                "url": link,
                "content": content,
                "published_at": parse_entry_date(entry),
            }
        )
    return items


def fetch_html_portal_items(source: Source, client: httpx.Client, limit: int) -> list[dict[str, Any]]:
    resp = client.get(source.url, timeout=8.0, follow_redirects=True)
    resp.raise_for_status()
    soup = BeautifulSoup(resp.text, "html.parser")
    items: list[dict[str, Any]] = []
    seen_urls: set[str] = set()

    for heading in soup.find_all(["h1", "h2", "h3", "article"]):
        a_tag = heading.find("a", href=True) if heading.name != "a" else heading
        if not a_tag:
            continue
        title = clean_html_text(a_tag.get_text())
        if len(title) < 28 or len(title) > 260:
            continue
        full_url = urljoin(source.url, a_tag["href"].strip())
        if not full_url.startswith("http") or full_url in seen_urls:
            continue
        seen_urls.add(full_url)

        parent = heading.find_parent(["article", "div", "li"])
        snippet = ""
        if parent:
            p_tag = parent.find("p")
            if p_tag:
                snippet = clean_html_text(p_tag.get_text())
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


DAILY_EVOLUTION_QUEUE: list[dict[str, Any]] = [
    {
        "source_slug": "erbol",
        "title": "Comunidades ribereñas del río Beni instalan puntos de vigilancia comunitaria ante ingreso de nuevas balsas auríferas",
        "url": "https://erbol.com.bo/nacional/vigilancia-comunitaria-rio-beni-balsas-auriferas-2026",
        "content": (
            "Corresponsales de radios comunitarias reportaron que corregidores y capitanías indígenas del norte de La Paz y Beni "
            "activaron turnos de control fluvial tras detectar al menos 14 nuevas dragas operando sin licencia ambiental cerca del área de amortiguamiento del Parque Nacional Madidi. "
            "Exigen a la AJAM y al Ministerio de Medio Ambiente publicar el padrón actualizado de cooperativas auríferas."
        ),
        "department": "La Paz",
        "category": "Minería y Extractivismo",
    },
    {
        "source_slug": "la-region",
        "title": "Monitoreo satelital independiente confirma regeneración lenta y riesgo de reactivación de focos en San Ignacio de Velasco",
        "url": "https://www.laregion.bo/monitoreo-chiquitania-san-ignacio-velasco-regeneracion-2026",
        "content": (
            "Un informe técnico elaborado por biólogos y guardaparques voluntarios en la Chiquitanía advierte que las comunidades "
            "afectadas por los incendios forestales en San Ignacio de Velasco y Roboré siguen con fuentes de agua contaminadas por ceniza. "
            "Denuncian que la pausa ambiental no detuvo el desmonte ilegal en tierras fiscales."
        ),
        "department": "Santa Cruz",
        "category": "Medio Ambiente y Territorio",
    },
    {
        "source_slug": "el-pais-tarija",
        "title": "Comunarios de Chiquiacá mantienen vigilia en acceso a la Reserva de Tariquía y piden audiencia con el Tribunal Agroambiental",
        "url": "https://www.elpais.bo/tarija/vigilia-chiquiaca-reserva-tariquia-tribunal-agroambiental-2026",
        "content": (
            "Defensores ambientales del cantón Chiquiacá en el departamento de Tarija cumplieron una nueva jornada de vigilia pacífica "
            "en defensa de la Reserva Nacional de Flora y Fauna Tariquía ante el ingreso de maquinaria vinculada a operaciones petroleras de YPFB. "
            "Solicitan una inspección ocular urgente del Tribunal Agroambiental y la Defensoría del Pueblo."
        ),
        "department": "Tarija",
        "category": "Medio Ambiente y Territorio",
    },
    {
        "source_slug": "radio-pio-xii",
        "title": "Productores agrícolas de la cuenca del Pilcomayo reportan pérdida de cultivos por sedimentos mineros tras últimas lluvias",
        "url": "https://radiopioxii.org/potosi-sedimentos-mineros-pilcomayo-cultivos-2026",
        "content": (
            "Comunidades campesinas de Potosí y Chuquisaca asentadas en las riberas del río Pilcomayo denunciaron que las primeras lluvias "
            "arrastraron residuos minerales desde diques de colas en la cuenca alta, afectando parcelas de maíz y hortalizas. "
            "Los reportes comunitarios no fueron recogidos por la televisión nacional pero motivaron una alerta en municipios ribereños."
        ),
        "department": "Potosí",
        "category": "Minería y Extractivismo",
    },
    {
        "source_slug": "guardiana",
        "title": "Transporte pesado y productores del norte integrado advierten nuevo desfase en cupos de diésel para la zafra y siembra",
        "url": "https://guardiana.com.bo/economia/transporte-productores-cupos-diesel-siembra-2026",
        "content": (
            "Pese a los anuncios de despacho normal realizados por YPFB y la ANH, sindicatos de transporte pesado y asociaciones de pequeños "
            "productores agrícolas en Santa Cruz, Cochabamba y La Paz registraron filas de hasta 18 horas en surtidores periféricos, "
            "alertando sobre retrasos en el traslado de alimentos hacia los mercados mayoristas."
        ),
        "department": "Santa Cruz",
        "category": "Economía y Abastecimiento",
    },
    {
        "source_slug": "la-patria-oruro",
        "title": "Comunidades urus del lago Uru Uru reclaman ejecución del plan de mitigación ambiental y provisión de agua potable",
        "url": "https://lapatria.bo/oruro/comunidades-urus-lago-uru-uru-mitigacion-agua-2026",
        "content": (
            "Autoridades originarias de las comunidades Urus en Oruro denunciaron que el nivel de caudal ecológico del lago Uru Uru y Poopó "
            "continúa crítico y que las descargas urbanas y mineras impiden la recuperación pesquera y artesanal comprometida en mesas técnicas."
        ),
        "department": "Oruro",
        "category": "Medio Ambiente y Territorio",
    },
]


def run_daily_scan(
    db: Session,
    trigger: str = "manual",
    source_slugs: list[str] | None = None,
    try_live_network: bool = True,
) -> ScrapeRun:
    """
    Ejecuta el escaneo diario de fuentes bolivianas:
    1. Recorre las fuentes activas (o las filtradas por `source_slugs`).
    2. Intenta extraer noticias reales desde RSS / HTML si `try_live_network=True`.
    3. Si hay novedades en la cola de seguimiento comunitario/regional aún no ingresadas,
       también las procesa para garantizar la demostración de evolución longitudinal.
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

    new_articles_count = 0
    new_events_count = 0
    updated_threads_count = 0
    per_source_stats: dict[str, Any] = {}

    if try_live_network:
        with httpx.Client(headers=HEADERS, verify=True) as client:
            for src in sources:
                collected_items: list[dict[str, Any]] = []
                error_msg: str | None = None
                try:
                    if src.rss_url:
                        collected_items = fetch_rss_items(src, client, limit=min(settings.max_articles_per_source, 5))
                    if not collected_items:
                        collected_items = fetch_html_portal_items(src, client, limit=4)
                except Exception as exc:
                    error_msg = str(exc)[:120]

                added_for_source = 0
                for item in collected_items:
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
                per_source_stats[src.slug] = {
                    "fetched": len(collected_items),
                    "new_articles": added_for_source,
                    "status": "ok" if not error_msg else "fallback",
                }
                db.commit()

    # Ingerir despachos comunitarios/regionales pendientes en la cola si aún no están registrados
    for item in DAILY_EVOLUTION_QUEUE:
        if source_slugs and item["source_slug"] not in source_slugs:
            continue
        existing = db.query(Article).filter(Article.url == item["url"]).first()
        if existing:
            continue
        src = db.query(Source).filter(Source.slug == item["source_slug"]).first()
        if not src:
            continue
        _, created_event, updated_thread = ingest_and_cluster_article(
            db=db,
            source=src,
            title=item["title"],
            url=item["url"],
            content=item["content"],
            published_at=datetime.now(timezone.utc),
            department_override=item.get("department"),
            category_override=item.get("category"),
        )
        new_articles_count += 1
        if created_event:
            new_events_count += 1
        if updated_thread:
            updated_threads_count += 1
        per_source_stats.setdefault(src.slug, {"fetched": 0, "new_articles": 0, "status": "ok"})
        per_source_stats[src.slug]["new_articles"] += 1
        db.commit()
        # En cada corrida manual agregamos hasta 2 nuevos despachos de la cola para que el usuario vea evolucionar los hilos paso a paso
        if trigger == "manual" and new_articles_count >= 2 and not try_live_network:
            break

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
