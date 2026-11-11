import uuid
from datetime import datetime, timezone
from typing import Any

from sqlalchemy import Boolean, DateTime, Float, ForeignKey, Integer, JSON, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


def new_id() -> str:
    return str(uuid.uuid4())


class Source(Base):
    """News outlet or media source monitored by Chasqui."""

    __tablename__ = "sources"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    name: Mapped[str] = mapped_column(String(140), nullable=False)
    slug: Mapped[str] = mapped_column(String(100), unique=True, index=True, nullable=False)
    url: Mapped[str] = mapped_column(String(500), nullable=False)
    rss_url: Mapped[str | None] = mapped_column(String(500), nullable=True)
    # mainstream | alternative | regional | community
    tier: Mapped[str] = mapped_column(String(40), index=True, nullable=False)
    department: Mapped[str] = mapped_column(String(60), index=True, default="National")
    scrape_strategy: Mapped[str] = mapped_column(String(40), default="rss")
    description: Mapped[str] = mapped_column(Text, default="")
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    last_scraped_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    total_articles_collected: Mapped[int] = mapped_column(Integer, default=0)

    articles: Mapped[list["Article"]] = relationship("Article", back_populates="source")


class StoryThread(Base):
    """Longitudinal storyline or public issue evolving over time."""

    __tablename__ = "story_threads"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    title: Mapped[str] = mapped_column(String(280), nullable=False)
    slug: Mapped[str] = mapped_column(String(200), unique=True, index=True, nullable=False)
    current_summary: Mapped[str] = mapped_column(Text, nullable=False)
    # active | monitoring | resolved
    status: Mapped[str] = mapped_column(String(40), index=True, default="active")
    category: Mapped[str] = mapped_column(String(80), index=True, nullable=False)
    primary_department: Mapped[str] = mapped_column(String(60), index=True, default="National")
    departments_affected: Mapped[list[str]] = mapped_column(JSON, default=list)
    key_entities: Mapped[list[str]] = mapped_column(JSON, default=list)
    first_seen_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, index=True)
    last_updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, index=True)
    events_count: Mapped[int] = mapped_column(Integer, default=0)
    articles_count: Mapped[int] = mapped_column(Integer, default=0)
    mainstream_count: Mapped[int] = mapped_column(Integer, default=0)
    alternative_count: Mapped[int] = mapped_column(Integer, default=0)
    # Percentage (0..100) of non-mainstream coverage (alternative, community, regional)
    blindspot_ratio: Mapped[float] = mapped_column(Float, default=0.0, index=True)
    thread_embedding: Mapped[list[float]] = mapped_column(JSON, default=list)

    events: Mapped[list["StoryEvent"]] = relationship(
        "StoryEvent",
        back_populates="thread",
        order_by="StoryEvent.event_date.desc()",
    )


class StoryEvent(Base):
    """Concrete occurrence within a time window grouping articles from multiple sources."""

    __tablename__ = "story_events"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    thread_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("story_threads.id", ondelete="CASCADE"), index=True, nullable=False
    )
    title: Mapped[str] = mapped_column(String(280), nullable=False)
    summary: Mapped[str] = mapped_column(Text, nullable=False)
    event_date: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, index=True)
    primary_department: Mapped[str] = mapped_column(String(60), index=True, default="National")
    category: Mapped[str] = mapped_column(String(80), index=True, default="General")
    entities: Mapped[list[str]] = mapped_column(JSON, default=list)
    mainstream_count: Mapped[int] = mapped_column(Integer, default=0)
    alternative_count: Mapped[int] = mapped_column(Integer, default=0)
    regional_count: Mapped[int] = mapped_column(Integer, default=0)
    community_count: Mapped[int] = mapped_column(Integer, default=0)
    is_blindspot: Mapped[bool] = mapped_column(Boolean, default=False, index=True)
    centroid_embedding: Mapped[list[float]] = mapped_column(JSON, default=list)

    thread: Mapped["StoryThread"] = relationship("StoryThread", back_populates="events")
    articles: Mapped[list["Article"]] = relationship(
        "Article",
        back_populates="event",
        order_by="Article.published_at.desc()",
    )


class Article(Base):
    """Individual news article published by a monitored source."""

    __tablename__ = "articles"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    source_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("sources.id", ondelete="CASCADE"), index=True, nullable=False
    )
    event_id: Mapped[str | None] = mapped_column(
        String(36), ForeignKey("story_events.id", ondelete="SET NULL"), index=True, nullable=True
    )
    url: Mapped[str] = mapped_column(String(600), unique=True, index=True, nullable=False)
    title: Mapped[str] = mapped_column(String(320), nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    summary: Mapped[str] = mapped_column(Text, nullable=False)
    published_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, index=True)
    scraped_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    department: Mapped[str] = mapped_column(String(60), index=True, default="National")
    category: Mapped[str] = mapped_column(String(80), index=True, default="Politics & Governance")
    entities: Mapped[list[str]] = mapped_column(JSON, default=list)
    embedding: Mapped[list[float]] = mapped_column(JSON, default=list)

    source: Mapped["Source"] = relationship("Source", back_populates="articles")
    event: Mapped["StoryEvent | None"] = relationship("StoryEvent", back_populates="articles")


class ScrapeRun(Base):
    """Execution log for each scheduled or on-demand scraping run."""

    __tablename__ = "scrape_runs"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, index=True)
    finished_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    trigger: Mapped[str] = mapped_column(String(40), default="manual")  # scheduled | manual | cli | seed
    status: Mapped[str] = mapped_column(String(40), default="running")  # running | completed | partial | failed
    sources_scanned: Mapped[int] = mapped_column(Integer, default=0)
    new_articles: Mapped[int] = mapped_column(Integer, default=0)
    new_events: Mapped[int] = mapped_column(Integer, default=0)
    updated_threads: Mapped[int] = mapped_column(Integer, default=0)
    details: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict)
