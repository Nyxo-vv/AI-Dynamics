"""Article processor: LLM-based translation, classification, and scoring.

Processes raw articles through the LLM to produce:
- title_zh: Chinese translation of the title
- summary_zh: 2-3 sentence Chinese summary
- tags: category classification (research/product/opensource/news/funding/policy/community)
- importance: 1-5 score
- related_links: extracted resource links
"""

import asyncio
import json
import logging
import re
from typing import Any

from database import get_db
from llm.engine import generate_json

logger = logging.getLogger(__name__)

# Truncate content to avoid excessive token usage
MAX_CONTENT_CHARS = 3000

# Concurrent LLM requests (Gemini free: 15 RPM, stay under limit)
MAX_CONCURRENCY = 5

# Batch processing: how many articles per single LLM call
BATCH_SIZE = 5

# ---- Low-value article filter (skip before LLM) ----
# Articles matching these patterns are noise — mark as importance=1, skip LLM
_SKIP_TITLE_PATTERNS = re.compile(
    r"|".join([
        r"weekly digest",
        r"newsletter",
        r"podcast",
        r"episode\s*\d",
        r"this week in",
        r"open thread",
        r"daily discussion",
        r"megathread",
        r"hiring|job posting|we.re hiring",
        r"\bAMA\b",
        r"show hn:.*\bmy\b",  # "Show HN: my personal project" type
    ]),
    re.IGNORECASE,
)

# Too short to be meaningful (title < 15 chars AND no content)
MIN_TITLE_LEN = 15


def _is_low_value(title: str, content: str) -> bool:
    """Quick check if an article is likely low-value noise."""
    if _SKIP_TITLE_PATTERNS.search(title):
        return True
    if len(title) < MIN_TITLE_LEN and len(content) < 50:
        return True
    return False


def _normalize_title(title: str) -> str:
    """Normalize a title for similarity matching.

    Strips common prefixes, lowercases, removes punctuation and extra spaces.
    """
    # Remove common prefixes like "[R]", "[D]", "[N]", "[P]" (Reddit tags)
    text = re.sub(r"^\s*\[[A-Z]\]\s*", "", title)
    # Lowercase, strip punctuation, collapse whitespace
    text = re.sub(r"[^\w\s]", " ", text.lower())
    text = re.sub(r"\s+", " ", text).strip()
    return text


SIMILARITY_THRESHOLD = 0.8


def _titles_similar(a: str, b: str) -> bool:
    """Check if two normalized titles are similar enough to be the same article."""
    if not a or not b:
        return False
    # Exact match after normalization
    if a == b:
        return True
    # One contains the other (common with reposts adding source prefix)
    if a in b or b in a:
        return True
    # Word overlap ratio
    words_a = set(a.split())
    words_b = set(b.split())
    if not words_a or not words_b:
        return False
    overlap = len(words_a & words_b)
    ratio = overlap / min(len(words_a), len(words_b))
    return ratio >= SIMILARITY_THRESHOLD

VALID_TAGS = {"research", "product", "opensource", "news", "funding", "policy", "community"}

async def _find_similar_processed(db, norm_title: str, exclude_id: int):
    """Find an already-processed article with a similar title.

    Searches recent processed articles (last 7 days) for a match.
    Returns the matched row dict or None.
    """
    cursor = await db.execute(
        """SELECT id, title, title_zh, summary_zh, importance, related_links
           FROM articles
           WHERE title_zh IS NOT NULL AND importance > 0
             AND id != ?
             AND fetched_at >= datetime('now', '-7 days')
           ORDER BY fetched_at DESC
           LIMIT 500""",
        (exclude_id,),
    )
    rows = await cursor.fetchall()
    for row in rows:
        if _titles_similar(norm_title, _normalize_title(row["title"])):
            return dict(row)
    return None


PROCESS_PROMPT = """\
You are an AI news analyst. Analyze the following article and return a JSON object with these fields:

1. "title_zh": Translate the title into natural, fluent Chinese. Keep proper nouns in English (e.g., GPT-5, LLaMA, OpenAI, Transformer, RLHF). This should convey the meaning, not be a word-for-word translation.
2. "summary_zh": Write a 2-3 sentence Chinese summary highlighting the core information. Use natural Chinese expressions. Keep technical terms and proper nouns in English.
3. "tags": An array of 1-3 tags from this set: ["research", "product", "opensource", "news", "funding", "policy", "community"]. Pick the most relevant.
4. "importance": An integer from 1 to 5:
   - 5: Major breakthrough or industry-shaping announcement
   - 4: Significant development worth attention
   - 3: Noteworthy update
   - 2: Routine update or minor news
   - 1: Low relevance or noise
5. "related_links": An array of objects {{"label": "...", "url": "..."}} for any resource links found in the content (paper PDFs, GitHub repos, demos, model pages). Empty array if none found.

IMPORTANT: Return ONLY valid JSON, no other text.

---
Source: {source_name}
Title: {title}
URL: {url}
Content (truncated):
{content}
---
"""

PROCESS_PROMPT_ZH = """\
You are an AI news analyst. Analyze the following Chinese article and return a JSON object with these fields:

1. "title_zh": Use the original title as-is (it's already in Chinese).
2. "summary_zh": Write a 2-3 sentence Chinese summary highlighting the core information.
3. "tags": An array of 1-3 tags from this set: ["research", "product", "opensource", "news", "funding", "policy", "community"]. Pick the most relevant.
4. "importance": An integer from 1 to 5:
   - 5: Major breakthrough or industry-shaping announcement
   - 4: Significant development worth attention
   - 3: Noteworthy update
   - 2: Routine update or minor news
   - 1: Low relevance or noise
5. "related_links": An array of objects {{"label": "...", "url": "..."}} for any resource links found in the content (paper PDFs, GitHub repos, demos, model pages). Empty array if none found.

IMPORTANT: Return ONLY valid JSON, no other text.

---
Title: {title}
URL: {url}
Content (truncated):
{content}
---
"""


BATCH_PROMPT = """\
You are an AI news analyst. Analyze each of the following articles and return a JSON ARRAY with one object per article, in the same order.

Each object must have these fields:
- "id": the article ID (integer, copy from input)
- "title_zh": Translate the title into natural, fluent Chinese. Keep proper nouns in English.
- "summary_zh": 2-3 sentence Chinese summary highlighting the core information.
- "tags": array of 1-3 tags from ["research", "product", "opensource", "news", "funding", "policy", "community"]
- "importance": integer 1-5 (5=major breakthrough, 4=significant, 3=noteworthy, 2=routine, 1=noise)
- "related_links": array of {{"label": "...", "url": "..."}} for resource links found in content. Empty array if none.

IMPORTANT: Return ONLY a valid JSON array, no other text. The array must have exactly {count} objects.

---
{articles_text}
---
"""


async def _save_llm_result(db, article_id: int, result: dict) -> bool:
    """Save a single LLM result dict to the database."""
    title_zh = result.get("title_zh", "")
    summary_zh = result.get("summary_zh", "")
    tags = result.get("tags", [])
    importance = result.get("importance") or 0
    related_links = result.get("related_links", [])

    tags = [t for t in (tags if isinstance(tags, list) else []) if t in VALID_TAGS]
    if not tags:
        tags = ["news"]
    importance = max(1, min(5, int(importance)))

    await db.execute(
        """UPDATE articles
           SET title_zh = ?, summary_zh = ?, importance = ?, related_links = ?
           WHERE id = ?""",
        (
            title_zh or None,
            summary_zh or None,
            importance,
            json.dumps(related_links) if related_links else None,
            article_id,
        ),
    )
    for tag in tags:
        await db.execute(
            "INSERT OR IGNORE INTO article_tags (article_id, tag) VALUES (?, ?)",
            (article_id, tag),
        )
    return True


async def process_article_batch(article_rows: list[dict]) -> dict[str, int]:
    """Process multiple articles in a single LLM call.

    Each row must have: id, title, url, content, language, source_name.
    Returns {"processed": N, "failed": M}.
    """
    if not article_rows:
        return {"processed": 0, "failed": 0}

    # Build combined prompt
    parts = []
    for a in article_rows:
        content = (a["content"] or "")[:MAX_CONTENT_CHARS]
        parts.append(
            f"[Article ID:{a['id']}]\n"
            f"Source: {a['source_name']}\n"
            f"Title: {a['title']}\n"
            f"URL: {a['url']}\n"
            f"Content: {content[:800]}\n"
        )

    prompt = BATCH_PROMPT.format(
        count=len(article_rows),
        articles_text="\n---\n".join(parts),
    )

    try:
        results = await generate_json(prompt)
    except Exception as exc:
        logger.warning("Batch LLM failed (%s), falling back to single processing", exc)
        # Fallback: process individually
        processed = 0
        failed = 0
        for a in article_rows:
            ok = await process_article(a["id"])
            if ok:
                processed += 1
            else:
                failed += 1
        return {"processed": processed, "failed": failed}

    if not isinstance(results, list):
        logger.warning("Batch LLM returned non-array, falling back to single processing")
        processed = 0
        failed = 0
        for a in article_rows:
            ok = await process_article(a["id"])
            if ok:
                processed += 1
            else:
                failed += 1
        return {"processed": processed, "failed": failed}

    # Map results by ID
    result_map = {}
    for r in results:
        if isinstance(r, dict) and "id" in r:
            result_map[int(r["id"])] = r

    db = await get_db()
    processed = 0
    failed = 0
    try:
        for a in article_rows:
            aid = a["id"]
            if aid in result_map:
                await _save_llm_result(db, aid, result_map[aid])
                title_zh = result_map[aid].get("title_zh", "")
                logger.info("Batch processed article %d: %s", aid, title_zh[:40])
                processed += 1
            else:
                logger.warning("Article %d missing from batch result, processing individually", aid)
                await db.close()
                ok = await process_article(aid)
                db = await get_db()
                if ok:
                    processed += 1
                else:
                    failed += 1
        await db.commit()
    finally:
        await db.close()

    return {"processed": processed, "failed": failed}


async def process_article(article_id: int) -> bool:
    """Process a single article through LLM.

    Reads the article from DB, sends to LLM, updates with results.
    Returns True if successful, False otherwise.
    """
    db = await get_db()
    try:
        cursor = await db.execute(
            """SELECT a.id, a.title, a.url, a.content, a.language,
                      s.name as source_name
               FROM articles a JOIN sources s ON a.source_id = s.id
               WHERE a.id = ?""",
            (article_id,),
        )
        row = await cursor.fetchone()
        if not row:
            logger.warning("Article %d not found", article_id)
            return False

        title = row["title"]
        url = row["url"]
        content = (row["content"] or "")[:MAX_CONTENT_CHARS]
        language = row["language"]
        source_name = row["source_name"]

        # Skip low-value articles without calling LLM
        if _is_low_value(title, content):
            await db.execute(
                "UPDATE articles SET title_zh = ?, summary_zh = ?, importance = ? WHERE id = ?",
                (title, "（低价值内容，已跳过）", 1, article_id),
            )
            await db.execute(
                "INSERT OR IGNORE INTO article_tags (article_id, tag) VALUES (?, ?)",
                (article_id, "news"),
            )
            await db.commit()
            logger.info("Skipped low-value article %d: %s", article_id, title[:50])
            return True

        # Check for similar already-processed article — reuse LLM result
        norm_title = _normalize_title(title)
        similar = await _find_similar_processed(db, norm_title, article_id)
        if similar:
            await db.execute(
                """UPDATE articles
                   SET title_zh = ?, summary_zh = ?, importance = ?,
                       related_links = ?
                   WHERE id = ?""",
                (
                    similar["title_zh"],
                    similar["summary_zh"],
                    similar["importance"],
                    similar["related_links"],
                    article_id,
                ),
            )
            # Copy tags
            tag_cursor = await db.execute(
                "SELECT tag FROM article_tags WHERE article_id = ?",
                (similar["id"],),
            )
            for tag_row in await tag_cursor.fetchall():
                await db.execute(
                    "INSERT OR IGNORE INTO article_tags (article_id, tag) VALUES (?, ?)",
                    (article_id, tag_row["tag"]),
                )
            await db.commit()
            logger.info(
                "Reused result from article %d for %d: %s",
                similar["id"], article_id, title[:50],
            )
            return True

        # Choose prompt based on language
        if language == "zh":
            prompt = PROCESS_PROMPT_ZH.format(
                title=title, url=url, content=content,
            )
        else:
            prompt = PROCESS_PROMPT.format(
                source_name=source_name, title=title, url=url, content=content,
            )

        try:
            result = await generate_json(prompt)
        except Exception as exc:
            logger.error("LLM failed for article %d (%s): %s", article_id, title[:50], exc)
            return False

        # Validate and extract fields
        title_zh = result.get("title_zh", "")
        summary_zh = result.get("summary_zh", "")
        tags = result.get("tags", [])
        importance = result.get("importance", 0)
        related_links = result.get("related_links", [])

        # Sanitize tags
        tags = [t for t in tags if t in VALID_TAGS]
        if not tags:
            tags = ["news"]  # default

        # Clamp importance
        importance = max(1, min(5, int(importance)))

        # Update article
        await db.execute(
            """UPDATE articles
               SET title_zh = ?, summary_zh = ?, importance = ?,
                   related_links = ?
               WHERE id = ?""",
            (
                title_zh or None,
                summary_zh or None,
                importance,
                json.dumps(related_links) if related_links else None,
                article_id,
            ),
        )

        # Insert tags
        for tag in tags:
            await db.execute(
                "INSERT OR IGNORE INTO article_tags (article_id, tag) VALUES (?, ?)",
                (article_id, tag),
            )

        await db.commit()
        logger.info("Processed article %d: [%d] %s", article_id, importance, title_zh or title[:40])
        return True

    finally:
        await db.close()


async def _process_batch(rows: list, on_progress=None) -> dict[str, int]:
    """Process article rows using batch LLM calls.

    1. Pre-filter: low-value and similar articles handled without LLM
    2. Remaining articles grouped into batches of BATCH_SIZE
    3. Batches sent concurrently (up to MAX_CONCURRENCY)
    """
    if not rows:
        return {"processed": 0, "failed": 0}

    logger.info("Processing %d articles (batch=%d, concurrency=%d)",
                len(rows), BATCH_SIZE, MAX_CONCURRENCY)

    # Phase 1: Pre-filter (low-value + similar dedup) — no LLM needed
    need_llm = []
    processed = 0
    failed = 0
    lock = asyncio.Lock()

    for row in rows:
        aid = row["id"]
        db = await get_db()
        try:
            cursor = await db.execute(
                """SELECT a.id, a.title, a.url, a.content, a.language,
                          s.name as source_name
                   FROM articles a JOIN sources s ON a.source_id = s.id
                   WHERE a.id = ?""",
                (aid,),
            )
            article = await cursor.fetchone()
            if not article:
                failed += 1
                continue

            title = article["title"]
            content = article["content"] or ""

            # Low-value filter
            if _is_low_value(title, content):
                await db.execute(
                    "UPDATE articles SET title_zh = ?, summary_zh = ?, importance = ? WHERE id = ?",
                    (title, "（低价值内容，已跳过）", 1, aid),
                )
                await db.execute(
                    "INSERT OR IGNORE INTO article_tags (article_id, tag) VALUES (?, ?)",
                    (aid, "news"),
                )
                await db.commit()
                logger.info("Skipped low-value article %d: %s", aid, title[:50])
                processed += 1
                if on_progress:
                    on_progress(processed, failed)
                continue

            # Similar dedup
            norm_title = _normalize_title(title)
            similar = await _find_similar_processed(db, norm_title, aid)
            if similar:
                await db.execute(
                    """UPDATE articles SET title_zh = ?, summary_zh = ?, importance = ?, related_links = ?
                       WHERE id = ?""",
                    (similar["title_zh"], similar["summary_zh"], similar["importance"],
                     similar["related_links"], aid),
                )
                tag_cursor = await db.execute(
                    "SELECT tag FROM article_tags WHERE article_id = ?", (similar["id"],),
                )
                for tag_row in await tag_cursor.fetchall():
                    await db.execute(
                        "INSERT OR IGNORE INTO article_tags (article_id, tag) VALUES (?, ?)",
                        (aid, tag_row["tag"]),
                    )
                await db.commit()
                logger.info("Reused result from article %d for %d: %s", similar["id"], aid, title[:50])
                processed += 1
                if on_progress:
                    on_progress(processed, failed)
                continue

            need_llm.append(dict(article))
        finally:
            await db.close()

    if not need_llm:
        logger.info("All articles handled by filter/dedup, no LLM needed")
        return {"processed": processed, "failed": failed}

    # Phase 2: Batch LLM processing
    logger.info("%d articles need LLM, sending in batches of %d", len(need_llm), BATCH_SIZE)
    sem = asyncio.Semaphore(MAX_CONCURRENCY)

    # Split into chunks of BATCH_SIZE
    chunks = [need_llm[i:i + BATCH_SIZE] for i in range(0, len(need_llm), BATCH_SIZE)]

    async def _process_chunk(chunk):
        nonlocal processed, failed
        async with sem:
            result = await process_article_batch(chunk)
        async with lock:
            processed += result["processed"]
            failed += result["failed"]
            if on_progress:
                on_progress(processed, failed)

    await asyncio.gather(*[_process_chunk(c) for c in chunks])

    logger.info("Processing complete: %d processed, %d failed", processed, failed)
    return {"processed": processed, "failed": failed}


async def process_unprocessed(*, limit: int = 50, on_progress=None) -> dict[str, int]:
    """Process all articles that haven't been through LLM yet.

    Articles with title_zh IS NULL and importance = 0 are considered unprocessed.
    Processes up to MAX_CONCURRENCY articles in parallel.
    """
    db = await get_db()
    try:
        cursor = await db.execute(
            """SELECT id FROM articles
               WHERE title_zh IS NULL AND importance = 0
               ORDER BY published_at DESC
               LIMIT ?""",
            (limit,),
        )
        rows = await cursor.fetchall()
    finally:
        await db.close()

    if not rows:
        logger.info("No unprocessed articles found")
        return {"processed": 0, "failed": 0}

    return await _process_batch(rows, on_progress)


async def process_unprocessed_since(*, since: str, on_progress=None) -> dict[str, int]:
    """Process unprocessed articles fetched since the given timestamp.

    Processes up to MAX_CONCURRENCY articles in parallel.
    """
    db = await get_db()
    try:
        cursor = await db.execute(
            """SELECT id FROM articles
               WHERE title_zh IS NULL AND importance = 0
                 AND fetched_at >= ?
               ORDER BY published_at DESC""",
            (since,),
        )
        rows = await cursor.fetchall()
    finally:
        await db.close()

    if not rows:
        logger.info("No unprocessed articles since %s", since)
        return {"processed": 0, "failed": 0}

    return await _process_batch(rows, on_progress)
