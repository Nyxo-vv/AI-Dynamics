"""Briefing generator: time-window query → LLM top-10 selection → categorize → store.

Generates a daily briefing by:
1. Querying articles within the date's time window (prev day 09:00 ~ current day 09:00)
2. Sending processed articles to LLM to select Top 10 headlines
3. Categorizing remaining articles by tag
4. Storing structured JSON in the briefings table
"""

import json
import logging
from datetime import datetime, timedelta

from database import get_db
from llm.engine import generate_json

logger = logging.getLogger(__name__)

# Category label mapping
CATEGORY_LABELS = {
    "research": "研究突破",
    "product": "产品发布",
    "opensource": "开源动态",
    "news": "行业新闻",
    "funding": "投融资",
    "policy": "政策法规",
    "community": "社区讨论",
}

HEADLINE_PROMPT = """\
You are a senior AI industry analyst. Given the following articles, select the TOP 10 as today's headlines.

Ranking criteria (high → low priority):
1. **Technical breakthrough**: novel architecture, SOTA results, major capability leap
2. **Source authority**: official lab blogs (OpenAI/DeepMind/Anthropic) > established media > community posts
3. **Practical value**: open-source model/code releases > paper-only research without artifacts
4. **Industry impact**: significant product launches, major funding rounds, policy changes affecting AI development
5. **Cross-domain effect**: breakthroughs impacting non-AI fields (healthcare, law, science) get a boost

Negative signals (downrank):
- **Stale news**: if the same event was already covered by another article in this list, keep only the most authoritative source
- **Low-information**: routine updates, minor version bumps, promotional content
- **Topic duplication**: avoid picking multiple articles about the same story — prefer diversity

Use importance scores as a reference but apply your own judgment based on the criteria above.

Return a JSON array of exactly 10 article IDs, ordered by importance (most important first):
[42, 17, 8, ...]

If there are fewer than 10 articles total, return all article IDs in importance order.

IMPORTANT: Return ONLY the JSON array, no other text.

---
Articles:
{articles_text}
---
"""


def _compute_window(date_str: str) -> tuple[str, str]:
    """Compute the time window for a briefing date.

    Window: previous day 09:00 ~ current day 09:00 (local time).
    """
    date = datetime.strptime(date_str, "%Y-%m-%d")
    window_start = (date - timedelta(days=1)).replace(hour=9, minute=0, second=0)
    window_end = date.replace(hour=9, minute=0, second=0)
    return window_start.strftime("%Y-%m-%d %H:%M:%S"), window_end.strftime("%Y-%m-%d %H:%M:%S")


async def _fetch_window_articles(date_str: str) -> list[dict]:
    """Fetch all processed articles within the briefing time window.

    Falls back to fetched_at if published_at is NULL.
    """
    window_start, window_end = _compute_window(date_str)

    db = await get_db()
    try:
        cursor = await db.execute(
            """SELECT a.id, a.title, a.title_zh, a.summary_zh, a.url,
                      a.cover_image, a.importance, a.published_at, a.fetched_at,
                      s.name as source_name
               FROM articles a
               JOIN sources s ON a.source_id = s.id
               WHERE a.title_zh IS NOT NULL
                 AND a.importance > 0
                 AND REPLACE(REPLACE(COALESCE(a.published_at, a.fetched_at), 'T', ' '), '+00:00', '') >= ?
                 AND REPLACE(REPLACE(COALESCE(a.published_at, a.fetched_at), 'T', ' '), '+00:00', '') < ?
               ORDER BY a.importance DESC, a.published_at DESC""",
            (window_start, window_end),
        )
        rows = await cursor.fetchall()

        articles = []
        for row in rows:
            # Fetch tags for this article
            tag_cursor = await db.execute(
                "SELECT tag FROM article_tags WHERE article_id = ?",
                (row["id"],),
            )
            tag_rows = await tag_cursor.fetchall()
            tags = [t["tag"] for t in tag_rows]

            articles.append({
                "id": row["id"],
                "title": row["title"],
                "title_zh": row["title_zh"],
                "summary_zh": row["summary_zh"],
                "url": row["url"],
                "cover_image": row["cover_image"],
                "importance": row["importance"],
                "published_at": row["published_at"],
                "fetched_at": row["fetched_at"],
                "source_name": row["source_name"],
                "tags": tags,
            })

        return articles
    finally:
        await db.close()


def _format_articles_for_llm(articles: list[dict]) -> str:
    """Format articles into a concise text block for the LLM prompt."""
    lines = []
    for a in articles:
        tags_str = ", ".join(a["tags"]) if a["tags"] else "news"
        lines.append(
            f"ID:{a['id']} | Importance:{a['importance']} | "
            f"Source:{a['source_name']} | Tags:{tags_str}\n"
            f"  Title: {a['title']}\n"
            f"  中文: {a['title_zh']}\n"
            f"  摘要: {(a['summary_zh'] or '')[:100]}"
        )
    return "\n\n".join(lines)


async def _select_headlines(articles: list[dict]) -> list[int]:
    """Use LLM to select the top 10 headline article IDs."""
    if len(articles) <= 10:
        # No need for LLM if 10 or fewer articles
        return [a["id"] for a in articles]

    articles_text = _format_articles_for_llm(articles)
    prompt = HEADLINE_PROMPT.format(articles_text=articles_text)

    try:
        result = await generate_json(prompt)
        # Validate: must be a list of ints that exist in our articles
        valid_ids = {a["id"] for a in articles}
        if isinstance(result, list):
            headline_ids = [int(x) for x in result if int(x) in valid_ids]
            # Ensure we have up to 10
            if len(headline_ids) < 10:
                # Fill with remaining high-importance articles
                remaining = [a["id"] for a in articles if a["id"] not in set(headline_ids)]
                headline_ids.extend(remaining[: 10 - len(headline_ids)])
            return headline_ids[:10]
    except Exception as exc:
        logger.warning("LLM headline selection failed (%s), using importance fallback", exc)

    # Fallback: top 10 by importance (already sorted)
    return [a["id"] for a in articles[:10]]


def _build_sections(articles: list[dict], headline_ids: set[int]) -> list[dict]:
    """Group non-headline articles by their primary tag into sections."""
    category_articles: dict[str, list[int]] = {}

    for a in articles:
        if a["id"] in headline_ids:
            continue
        # Use first tag as primary category
        primary_tag = a["tags"][0] if a["tags"] else "news"
        category_articles.setdefault(primary_tag, []).append(a["id"])

    sections = []
    # Preserve a consistent order
    for cat in ["research", "product", "opensource", "news", "funding", "policy", "community"]:
        if cat in category_articles:
            sections.append({
                "category": cat,
                "label": CATEGORY_LABELS.get(cat, cat),
                "article_ids": category_articles[cat],
            })

    return sections


def _build_stats(articles: list[dict], headline_ids: list[int]) -> dict:
    """Build statistics for the briefing."""
    by_category: dict[str, int] = {}
    by_source: dict[str, int] = {}

    for a in articles:
        # Count by category (first tag)
        primary_tag = a["tags"][0] if a["tags"] else "news"
        by_category[primary_tag] = by_category.get(primary_tag, 0) + 1
        # Count by source
        by_source[a["source_name"]] = by_source.get(a["source_name"], 0) + 1

    return {
        "total": len(articles),
        "headline_count": len(headline_ids),
        "by_category": by_category,
        "by_source": by_source,
    }


async def generate_briefing(date_str: str) -> dict:
    """Generate a daily briefing for the given date.

    Args:
        date_str: Date string in YYYY-MM-DD format.

    Returns:
        The saved briefing record as a dict.

    Raises:
        ValueError: If no processed articles found in the time window.
    """
    window_start, window_end = _compute_window(date_str)

    # Fetch articles
    articles = await _fetch_window_articles(date_str)
    if not articles:
        raise ValueError(
            f"No processed articles found for {date_str} "
            f"(window: {window_start} ~ {window_end}). "
            "Run the fetch pipeline and LLM processing first."
        )

    logger.info("Generating briefing for %s: %d articles in window", date_str, len(articles))

    # Select headlines via LLM
    headline_ids = await _select_headlines(articles)
    headline_set = set(headline_ids)

    # Build structured content
    headlines = [{"article_id": aid, "rank": i + 1} for i, aid in enumerate(headline_ids)]
    sections = _build_sections(articles, headline_set)
    stats = _build_stats(articles, headline_ids)

    content = {
        "headlines": headlines,
        "sections": sections,
        "stats": stats,
    }

    # Store in database (upsert by date)
    db = await get_db()
    try:
        await db.execute(
            """INSERT INTO briefings (date, window_start, window_end, content, article_count)
               VALUES (?, ?, ?, ?, ?)
               ON CONFLICT(date) DO UPDATE SET
                   window_start = excluded.window_start,
                   window_end = excluded.window_end,
                   content = excluded.content,
                   article_count = excluded.article_count,
                   generated_at = CURRENT_TIMESTAMP""",
            (date_str, window_start, window_end, json.dumps(content, ensure_ascii=False), len(articles)),
        )
        await db.commit()

        # Fetch the saved record
        cursor = await db.execute(
            "SELECT * FROM briefings WHERE date = ?", (date_str,)
        )
        row = await cursor.fetchone()

        logger.info(
            "Briefing for %s saved: %d headlines, %d sections, %d total articles",
            date_str, len(headlines), len(sections), len(articles),
        )

        return {
            "id": row["id"],
            "date": row["date"],
            "window_start": row["window_start"],
            "window_end": row["window_end"],
            "content": json.loads(row["content"]),
            "article_count": row["article_count"],
            "generated_at": row["generated_at"],
        }
    finally:
        await db.close()


async def get_briefing_with_articles(date_str: str) -> dict | None:
    """Get a briefing with full article data joined in.

    Returns None if no briefing exists for the date.
    """
    db = await get_db()
    try:
        cursor = await db.execute(
            "SELECT * FROM briefings WHERE date = ?", (date_str,)
        )
        row = await cursor.fetchone()
        if not row:
            return None

        content = json.loads(row["content"])

        # Collect all article IDs referenced in the briefing
        all_ids = set()
        for h in content.get("headlines", []):
            all_ids.add(h["article_id"])
        for s in content.get("sections", []):
            all_ids.update(s["article_ids"])

        if not all_ids:
            return {
                "id": row["id"],
                "date": row["date"],
                "window_start": row["window_start"],
                "window_end": row["window_end"],
                "content": content,
                "article_count": row["article_count"],
                "generated_at": row["generated_at"],
                "articles": {},
            }

        # Fetch all referenced articles in one query
        placeholders = ",".join("?" for _ in all_ids)
        article_cursor = await db.execute(
            f"""SELECT a.id, a.title, a.title_zh, a.url, a.summary_zh,
                       a.cover_image, a.images, a.related_links,
                       a.importance, a.published_at, a.is_read, a.is_starred,
                       s.name as source_name
                FROM articles a
                JOIN sources s ON a.source_id = s.id
                WHERE a.id IN ({placeholders})""",
            list(all_ids),
        )
        article_rows = await article_cursor.fetchall()

        # Build article lookup dict keyed by ID
        articles_map = {}
        for ar in article_rows:
            aid = ar["id"]
            # Fetch tags
            tag_cursor = await db.execute(
                "SELECT tag FROM article_tags WHERE article_id = ?", (aid,)
            )
            tag_rows = await tag_cursor.fetchall()

            articles_map[aid] = {
                "id": aid,
                "title": ar["title"],
                "title_zh": ar["title_zh"],
                "url": ar["url"],
                "summary_zh": ar["summary_zh"],
                "cover_image": ar["cover_image"],
                "images": json.loads(ar["images"]) if ar["images"] else [],
                "related_links": json.loads(ar["related_links"]) if ar["related_links"] else [],
                "importance": ar["importance"],
                "published_at": ar["published_at"],
                "is_read": bool(ar["is_read"]),
                "is_starred": bool(ar["is_starred"]),
                "source_name": ar["source_name"],
                "tags": [t["tag"] for t in tag_rows],
            }

        return {
            "id": row["id"],
            "date": row["date"],
            "window_start": row["window_start"],
            "window_end": row["window_end"],
            "content": content,
            "article_count": row["article_count"],
            "generated_at": row["generated_at"],
            "articles": articles_map,
        }
    finally:
        await db.close()
