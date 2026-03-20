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
from llm.engine import generate_json, generate_quality_ollama

logger = logging.getLogger(__name__)

# Truncate content to avoid excessive token usage
MAX_CONTENT_CHARS = 3000

# Concurrent LLM requests — keep at 1 for free-tier rate limits
MAX_CONCURRENCY = 1

# Batch processing: how many articles per single LLM call
BATCH_SIZE = 10

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

# Japanese kana + CJK Extension A (very rare) + known garbled Chinese characters
_GARBLED_RE = re.compile(
    r"[\u3040-\u309F\u30A0-\u30FF]"  # Hiragana + Katakana
    r"|[\u3400-\u4DBF]"  # CJK Extension A (extremely rare chars)
    r"|[罤邭犸徛帡曈穹絷穽徖雩嶸罷昮跼徟棜覄]"
    r"|服加.*宝统|和提为访"
)

# Top ~500 most common Chinese characters (covers ~80% of modern text)
# Used as a baseline to detect garbled text with too many rare characters
_COMMON_CJK = set(
    "的一是不了在人有我他这个们中来上大为和国地到以说时要就出会也你对生能而子"
    "那得于着下自之年后作里家多日发成都然后那自己并第与从用但被十么所好过还"
    "进没吗起想可开它两如些间长问行动方面定事前把同经分让先已次手新工外等给"
    "候老实意很向感使种心道主力理明加当化因关什各去话儿更别法现回再打全找比"
    "真看正太头只学通入做本知少门部分相点或政高电话书其市该张认将白体应名美"
    "几水平文机数小表特许百完资见提论单西公指重建世思利走教海解安万信路转受"
    "风条形件最位情带品步者反民众场业内系月今总保正被满每直区程放义制活度清"
    "线别处治台原题必越设组示件术连记号南算基达证团华光往观身变共命员战科联"
    "局北近八九七六五四三二持色据支无研究报告发展技术模型语言智能系统数据网"
    "络服务器平台产品更新版本功能训练推理安全开源社区索引论文代码测试性能提升"
)


def _is_garbled(text: str) -> bool:
    """Check if translated text contains garbled/Japanese characters."""
    if not text:
        return False
    # Check known garbled patterns
    if _GARBLED_RE.search(text):
        return True
    # Statistical check: too many rare CJK characters indicates garbled text
    cjk_chars = [c for c in text if '\u4e00' <= c <= '\u9fff']
    if len(cjk_chars) < 6:
        return False
    rare_count = sum(1 for c in cjk_chars if c not in _COMMON_CJK)
    return rare_count / len(cjk_chars) > 0.3


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
AI news analyst. Return JSON object for this article:
- "title_zh": Chinese title (keep proper nouns in English like GPT-5, OpenAI)
- "summary_zh": 2-3 sentence Chinese summary, keep technical terms in English
- "tags": 1-3 from ["research","product","opensource","news","funding","policy","community"]
- "importance": 1-5 (5=major breakthrough, 4=significant, 3=noteworthy, 2=routine, 1=noise)
- "related_links": [{{"label":"..","url":".."}}] for paper/GitHub/demo links. [] if none.

Return ONLY valid JSON.

---
Source: {source_name} | Title: {title} | URL: {url}
{content}
---
"""

PROCESS_PROMPT_ZH = """\
AI news analyst. Return JSON object for this Chinese article:
- "title_zh": keep original title as-is
- "summary_zh": 2-3 sentence Chinese summary
- "tags": 1-3 from ["research","product","opensource","news","funding","policy","community"]
- "importance": 1-5 (5=major breakthrough, 4=significant, 3=noteworthy, 2=routine, 1=noise)
- "related_links": [{{"label":"..","url":".."}}] for paper/GitHub/demo links. [] if none.

Return ONLY valid JSON.

---
Title: {title} | URL: {url}
{content}
---
"""


BATCH_PROMPT = """\
AI news analyst. Return a JSON ARRAY ({count} objects, same order as input).

Fields per object:
- "id": article ID (copy from input)
- "title_zh": Chinese title (keep proper nouns in English like GPT-5, OpenAI). If already Chinese, keep as-is.
- "summary_zh": 2-3 sentence Chinese summary. Keep technical terms in English.
- "tags": 1-3 from ["research","product","opensource","news","funding","policy","community"]
- "importance": 1-5 (5=major breakthrough, 4=significant, 3=noteworthy, 2=routine, 1=noise)
- "related_links": [{{"label":"..","url":".."}}] for paper/GitHub/demo links. [] if none.

Return ONLY valid JSON array.

---
{articles_text}
---
"""


async def _retry_with_quality_model(article_row: dict) -> dict | None:
    """Retry a single article with the higher-quality Ollama model.

    Returns parsed JSON result or None on failure.
    """
    title = article_row.get("title", "")
    url = article_row.get("url", "")
    content = (article_row.get("content") or "")[:MAX_CONTENT_CHARS]
    language = article_row.get("language", "")
    source_name = article_row.get("source_name", "")

    if language == "zh":
        prompt = PROCESS_PROMPT_ZH.format(title=title, url=url, content=content)
    else:
        prompt = PROCESS_PROMPT.format(
            source_name=source_name, title=title, url=url, content=content,
        )

    try:
        raw = await generate_quality_ollama(prompt)
        text = raw.strip()
        if text.startswith("```"):
            lines = text.split("\n")
            if lines[0].startswith("```"):
                lines = lines[1:]
            if lines and lines[-1].strip().startswith("```"):
                lines = lines[:-1]
            text = "\n".join(lines)
        return json.loads(text)
    except Exception as exc:
        logger.warning("Quality model retry failed: %s", exc)
        return None


async def _save_llm_result(db, article_id: int, result: dict, article_row: dict | None = None) -> bool:
    """Save a single LLM result dict to the database.

    If garbled text is detected and article_row is provided, retries with the
    higher-quality Ollama model before giving up.
    """
    title_zh = result.get("title_zh", "")
    summary_zh = result.get("summary_zh", "")
    tags = result.get("tags", [])
    importance = result.get("importance") or 0
    related_links = result.get("related_links", [])

    # Reject garbled translations — retry with quality model
    if _is_garbled(title_zh or "") or _is_garbled(summary_zh or ""):
        logger.warning("Garbled translation for article %d: %s, retrying with quality model", article_id, (title_zh or "")[:50])
        if article_row:
            retry_result = await _retry_with_quality_model(article_row)
            if retry_result:
                title_zh = retry_result.get("title_zh", "")
                summary_zh = retry_result.get("summary_zh", "")
                tags = retry_result.get("tags", tags)
                importance = retry_result.get("importance", importance) or importance
                related_links = retry_result.get("related_links", related_links)
                if _is_garbled(title_zh or "") or _is_garbled(summary_zh or ""):
                    logger.warning("Quality model also garbled for article %d, giving up", article_id)
                    return False
                logger.info("Quality model retry succeeded for article %d", article_id)
            else:
                return False
        else:
            return False

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
        content = (a["content"] or "")[:800]
        lang_hint = " [ZH-keep title]" if a.get("language") == "zh" else ""
        parts.append(
            f"[ID:{a['id']}]{lang_hint} {a['source_name']}\n"
            f"Title: {a['title']}\n"
            f"URL: {a['url']}\n"
            f"{content}\n"
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
                await _save_llm_result(db, aid, result_map[aid], article_row=a)
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

        # Garbled text retry with quality model
        if _is_garbled(title_zh or "") or _is_garbled(summary_zh or ""):
            logger.warning("Garbled in article %d, retrying with quality model", article_id)
            article_row = {
                "title": title, "url": url, "content": content,
                "language": language, "source_name": source_name,
            }
            retry_result = await _retry_with_quality_model(article_row)
            if retry_result:
                title_zh = retry_result.get("title_zh", title_zh)
                summary_zh = retry_result.get("summary_zh", summary_zh)
                tags = retry_result.get("tags", tags)
                importance = retry_result.get("importance", importance)
                related_links = retry_result.get("related_links", related_links)
                if _is_garbled(title_zh or "") or _is_garbled(summary_zh or ""):
                    logger.warning("Quality model also garbled for article %d", article_id)
                    return False
            else:
                return False

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

    async def _process_chunk(chunk, delay: float = 0):
        nonlocal processed, failed
        if delay > 0:
            await asyncio.sleep(delay)
        async with sem:
            result = await process_article_batch(chunk)
        async with lock:
            processed += result["processed"]
            failed += result["failed"]
            if on_progress:
                on_progress(processed, failed)

    # Process chunks sequentially with delay to respect free-tier rate limits
    for i, c in enumerate(chunks):
        if i > 0:
            await asyncio.sleep(10.0)
        await _process_chunk(c)

    logger.info("Processing complete: %d processed, %d failed", processed, failed)
    return {"processed": processed, "failed": failed}


async def process_unprocessed(*, limit: int = 50, on_progress=None) -> dict[str, int]:
    """Process all articles that haven't been through LLM yet.

    Articles with title_zh IS NULL and importance = 0 are considered unprocessed.
    Order: today's articles first, then backlog from newest to oldest.
    """
    db = await get_db()
    try:
        cursor = await db.execute(
            """SELECT id FROM articles
               WHERE title_zh IS NULL AND importance = 0
               ORDER BY COALESCE(fetched_at, published_at) DESC
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
               ORDER BY COALESCE(fetched_at, published_at) DESC""",
            (since,),
        )
        rows = await cursor.fetchall()
    finally:
        await db.close()

    if not rows:
        logger.info("No unprocessed articles since %s", since)
        return {"processed": 0, "failed": 0}

    return await _process_batch(rows, on_progress)
