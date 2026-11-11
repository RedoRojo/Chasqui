from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class SourceOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    name: str
    slug: str
    url: str
    rss_url: str | None = None
    tier: str
    department: str
    scrape_strategy: str
    description: str
    is_active: bool
    last_scraped_at: datetime | None = None
    total_articles_collected: int


class SourceCreate(BaseModel):
    name: str
    url: str
    rss_url: str | None = None
    tier: str = Field(default="alternative", description="mainstream | alternative | regional | community")
    department: str = "National"
    scrape_strategy: str = "rss"
    description: str = ""


class ArticleOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    source_id: str
    event_id: str | None = None
    url: str
    title: str
    content: str
    summary: str
    published_at: datetime
    scraped_at: datetime
    department: str
    category: str
    entities: list[str]
    source: SourceOut | None = None


class StoryEventOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    thread_id: str
    title: str
    summary: str
    event_date: datetime
    primary_department: str
    category: str
    entities: list[str]
    mainstream_count: int
    alternative_count: int
    regional_count: int
    community_count: int
    is_blindspot: bool
    articles: list[ArticleOut] = []
    thread_title: str | None = None
    thread_slug: str | None = None


class StoryThreadOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    title: str
    slug: str
    current_summary: str
    status: str
    category: str
    primary_department: str
    departments_affected: list[str]
    key_entities: list[str]
    first_seen_at: datetime
    last_updated_at: datetime
    events_count: int
    articles_count: int
    mainstream_count: int
    alternative_count: int
    blindspot_ratio: float


class StoryThreadDetailOut(StoryThreadOut):
    events: list[StoryEventOut] = []


class ScrapeRunOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    started_at: datetime
    finished_at: datetime | None = None
    trigger: str
    status: str
    sources_scanned: int
    new_articles: int
    new_events: int
    updated_threads: int
    details: dict[str, Any] = {}


class ArticleIngestRequest(BaseModel):
    source_slug: str
    title: str
    url: str
    content: str
    published_at: datetime | None = None
    department: str | None = None
    category: str | None = None


class DashboardOverviewOut(BaseModel):
    total_threads: int
    active_threads: int
    total_events: int
    total_articles: int
    total_sources: int
    blindspot_events_count: int
    alternative_coverage_share: float
    departments_summary: list[dict[str, Any]]
    categories_summary: list[dict[str, Any]]
    last_scrape: ScrapeRunOut | None = None
