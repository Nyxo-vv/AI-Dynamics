from datetime import datetime
from pydantic import BaseModel


class Source(BaseModel):
    id: int
    name: str
    url: str
    type: str = "rss"
    category: str = "media"
    enabled: bool = True
    fetch_interval_min: int = 60
    last_fetched_at: str | None = None
    created_at: str | None = None


class Article(BaseModel):
    id: int
    source_id: int
    title: str
    title_zh: str | None = None
    url: str
    author: str | None = None
    content: str | None = None
    summary_zh: str | None = None
    cover_image: str | None = None
    images: str | None = None
    related_links: str | None = None
    language: str = "en"
    published_at: str | None = None
    fetched_at: str | None = None
    importance: int = 0
    is_read: bool = False
    is_starred: bool = False
    # joined fields
    source_name: str | None = None
    tags: list[str] | None = None


class ArticleUpdate(BaseModel):
    is_read: bool | None = None
    is_starred: bool | None = None


class BriefingHeadline(BaseModel):
    article_id: int
    rank: int


class BriefingSection(BaseModel):
    category: str
    label: str
    article_ids: list[int]


class BriefingStats(BaseModel):
    total: int
    headline_count: int
    by_category: dict[str, int]
    by_source: dict[str, int]


class BriefingContent(BaseModel):
    headlines: list[BriefingHeadline]
    sections: list[BriefingSection]
    stats: BriefingStats


class Briefing(BaseModel):
    id: int
    date: str
    window_start: str
    window_end: str
    content: BriefingContent | None = None
    article_count: int
    generated_at: str | None = None


class BriefingStatus(BaseModel):
    date: str
    generated: bool
    article_count: int


class GenerateBriefingRequest(BaseModel):
    date: str


class FetchStatus(BaseModel):
    status: str = "idle"  # idle | fetching | processing | running
    total_sources: int = 0
    processed_sources: int = 0
    new_articles: int = 0
    llm_total: int = 0
    llm_processed: int = 0
