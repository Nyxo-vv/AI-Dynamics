"""RSS fetcher: pull feeds, extract articles, deduplicate, store."""

import asyncio
import json
import logging
import re
from datetime import datetime, timezone
from typing import Any

import feedparser
import httpx
from bs4 import BeautifulSoup

from database import get_db

logger = logging.getLogger(__name__)

USER_AGENT = "AI-Dynamics/0.1 (personal news aggregator; +https://github.com)"
FETCH_TIMEOUT = 30  # seconds


# ---------------------------------------------------------------------------
# Media extraction helpers
# ---------------------------------------------------------------------------

# Patterns for images that are usually icons/trackers, not content images
_JUNK_IMG_RE = re.compile(
    r"(logo|icon|avatar|badge|tracker|pixel|spacer|button|banner-ad|\.gif)",
    re.IGNORECASE,
)
MIN_IMG_DIMENSION = 80  # skip tiny images (likely icons)


def _extract_cover_image(entry: dict) -> str | None:
    """Extract cover image from RSS entry.

    Priority: media:content / media:thumbnail > enclosure > first <img> in content.
    """
    # media:content or media:thumbnail
    for key in ("media_content", "media_thumbnail"):
        media = entry.get(key)
        if media and isinstance(media, list) and media[0].get("url"):
            return media[0]["url"]

    # enclosure (often used for podcast art / article images)
    for link in entry.get("links", []):
        if link.get("rel") == "enclosure" and link.get("type", "").startswith("image/"):
            return link["url"]

    # fall back: first <img> in content
    html = _get_entry_html(entry)
    if html:
        soup = BeautifulSoup(html, "html.parser")
        img = soup.find("img", src=True)
        if img and not _JUNK_IMG_RE.search(img["src"]):
            return img["src"]

    return None


def _extract_images(entry: dict) -> list[str]:
    """Extract content images, filtering out junk."""
    html = _get_entry_html(entry)
    if not html:
        return []

    soup = BeautifulSoup(html, "html.parser")
    urls: list[str] = []
    for img in soup.find_all("img", src=True):
        src = img["src"]
        if _JUNK_IMG_RE.search(src):
            continue
        # skip tiny images if dimensions are specified
        w = img.get("width", "")
        h = img.get("height", "")
        if w and w.isdigit() and int(w) < MIN_IMG_DIMENSION:
            continue
        if h and h.isdigit() and int(h) < MIN_IMG_DIMENSION:
            continue
        if src not in urls:
            urls.append(src)
    return urls


def _get_entry_html(entry: dict) -> str | None:
    """Get the best HTML content from a feed entry."""
    # content field (list of dicts with 'value')
    content_list = entry.get("content", [])
    if content_list:
        for c in content_list:
            if c.get("type", "").startswith("text/html") or "<" in c.get("value", ""):
                return c["value"]
        return content_list[0].get("value")

    # summary / description
    for key in ("summary", "description"):
        val = entry.get(key, "")
        if val:
            return val

    return None


def _extract_text(entry: dict) -> str:
    """Extract plain text content from entry (for storage / LLM processing)."""
    html = _get_entry_html(entry)
    if not html:
        return ""
    soup = BeautifulSoup(html, "html.parser")
    return soup.get_text(separator="\n", strip=True)


def _detect_language(text: str) -> str:
    """Simple heuristic: if >30% of characters are CJK, treat as Chinese."""
    if not text:
        return "en"
    cjk_count = sum(1 for ch in text if "\u4e00" <= ch <= "\u9fff")
    ratio = cjk_count / len(text) if text else 0
    return "zh" if ratio > 0.3 else "en"


def _parse_published(entry: dict) -> str | None:
    """Parse published date from feed entry, return ISO 8601 string."""
    for key in ("published_parsed", "updated_parsed"):
        t = entry.get(key)
        if t:
            try:
                dt = datetime(*t[:6], tzinfo=timezone.utc)
                return dt.isoformat()
            except (ValueError, TypeError):
                continue
    return None


# ---------------------------------------------------------------------------
# Core fetch logic
# ---------------------------------------------------------------------------

async def fetch_single_source(
    source_id: int,
    source_name: str,
    feed_url: str,
    *,
    filter_fn: Any | None = None,
) -> int:
    """Fetch one RSS source and store new articles.

    Args:
        source_id: database source id
        source_name: human-readable name (for logging)
        feed_url: RSS feed URL
        filter_fn: optional async callable(entry) -> bool for pre-filtering
                   (used for arXiv volume control)

    Returns:
        Number of new articles inserted.
    """
    logger.info("Fetching %s: %s", source_name, feed_url)

    # Custom UA — Reddit blocks default Python UA with 403
    headers = {"User-Agent": USER_AGENT}

    async with httpx.AsyncClient(timeout=FETCH_TIMEOUT, follow_redirects=True) as client:
        try:
            resp = await client.get(feed_url, headers=headers)
            resp.raise_for_status()
        except httpx.HTTPError as exc:
            logger.error("Failed to fetch %s: %s", source_name, exc)
            return 0

    feed = feedparser.parse(resp.text)
    if feed.bozo and not feed.entries:
        logger.warning("Feed parse error for %s: %s", source_name, feed.bozo_exception)
        return 0

    db = await get_db()
    new_count = 0
    try:
        for entry in feed.entries:
            url = entry.get("link", "").strip()
            title = entry.get("title", "").strip()
            if not url or not title:
                continue

            # Dedup by URL
            cursor = await db.execute(
                "SELECT 1 FROM articles WHERE url = ?", (url,)
            )
            if await cursor.fetchone():
                continue

            # Optional pre-filter (e.g. arXiv keyword matching)
            if filter_fn and not await filter_fn(entry):
                continue

            content = _extract_text(entry)
            language = _detect_language(title + " " + content[:200])
            cover_image = _extract_cover_image(entry)
            images = _extract_images(entry)
            published_at = _parse_published(entry)
            author = entry.get("author", "")

            await db.execute(
                """INSERT INTO articles
                   (source_id, title, url, author, content,
                    cover_image, images, language, published_at)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (
                    source_id,
                    title,
                    url,
                    author or None,
                    content or None,
                    cover_image,
                    json.dumps(images) if images else None,
                    language,
                    published_at,
                ),
            )
            new_count += 1

        await db.commit()

        # Update last_fetched_at on source
        await db.execute(
            "UPDATE sources SET last_fetched_at = ? WHERE id = ?",
            (datetime.now(timezone.utc).isoformat(), source_id),
        )
        await db.commit()

    finally:
        await db.close()

    logger.info("%s: %d new articles", source_name, new_count)
    return new_count


async def fetch_all_sources(
    *,
    filter_registry: dict[str, Any] | None = None,
    on_progress: Any | None = None,
) -> dict[str, int]:
    """Fetch all enabled RSS sources.

    Args:
        filter_registry: optional mapping of source name -> filter function
                         (e.g. {"arXiv cs.AI": arxiv_keyword_filter})
        on_progress: optional callable(processed: int, new_articles: int)
                     called after each source completes

    Returns:
        Dict of {source_name: new_article_count}
    """
    filter_registry = filter_registry or {}

    db = await get_db()
    try:
        cursor = await db.execute(
            "SELECT id, name, url FROM sources WHERE enabled = 1 AND type = 'rss'"
        )
        sources = await cursor.fetchall()
    finally:
        await db.close()

    # Concurrent fetch with semaphore (avoid overwhelming network/sites)
    sem = asyncio.Semaphore(5)
    results: dict[str, int] = {}
    lock = asyncio.Lock()

    async def _fetch_one(src):
        source_id, name, url = src["id"], src["name"], src["url"]
        filter_fn = filter_registry.get(name)
        async with sem:
            count = await fetch_single_source(
                source_id, name, url, filter_fn=filter_fn
            )
        async with lock:
            results[name] = count
            if on_progress:
                on_progress(len(results), sum(results.values()))

    await asyncio.gather(*[_fetch_one(src) for src in sources])

    total = sum(results.values())
    logger.info("Fetch complete: %d new articles from %d sources", total, len(results))
    return results
