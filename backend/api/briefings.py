"""Briefings API: generate, get, recent, search."""

import json
import logging
from datetime import date, timedelta

from fastapi import APIRouter, HTTPException, Query

from database import get_db
from models import GenerateBriefingRequest
from llm.briefing import generate_briefing, get_briefing_with_articles

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/briefings", tags=["briefings"])


@router.post("/generate")
async def api_generate_briefing(req: GenerateBriefingRequest) -> dict:
    """Generate a daily briefing for the specified date."""
    try:
        result = await generate_briefing(req.date)
        return result
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc))
    except Exception as exc:
        logger.error("Briefing generation failed for %s: %s", req.date, exc)
        raise HTTPException(status_code=500, detail=f"Generation failed: {exc}")


@router.get("/recent")
async def list_recent_briefings(days: int = Query(default=7, ge=1, le=30)) -> dict:
    """List briefing status for the last N days."""
    db = await get_db()
    try:
        today = date.today()
        items = []

        for i in range(days):
            d = today - timedelta(days=i)
            date_str = d.isoformat()

            cursor = await db.execute(
                "SELECT article_count, generated_at FROM briefings WHERE date = ?",
                (date_str,),
            )
            row = await cursor.fetchone()

            # Count articles in the window for this date
            window_start = (d - timedelta(days=1)).isoformat() + " 09:00:00"
            window_end = d.isoformat() + " 09:00:00"
            count_cursor = await db.execute(
                """SELECT COUNT(*) as cnt FROM articles
                   WHERE title_zh IS NOT NULL AND importance > 0
                     AND REPLACE(REPLACE(COALESCE(published_at, fetched_at), 'T', ' '), '+00:00', '') >= ?
                     AND REPLACE(REPLACE(COALESCE(published_at, fetched_at), 'T', ' '), '+00:00', '') < ?""",
                (window_start, window_end),
            )
            count_row = await count_cursor.fetchone()
            available_count = count_row["cnt"]

            items.append({
                "date": date_str,
                "generated": row is not None,
                "article_count": row["article_count"] if row else available_count,
                "generated_at": row["generated_at"] if row else None,
            })

        return {"items": items}
    finally:
        await db.close()


@router.get("/search")
async def search_briefing_articles(
    q: str = Query(..., min_length=1),
    date_str: str | None = Query(default=None, alias="date"),
) -> dict:
    """Search articles within briefings by keyword.

    Matches against title, title_zh, summary_zh, and source name.
    If date is provided, search only that date's briefing; otherwise search all.
    """
    db = await get_db()
    try:
        search_pattern = f"%{q}%"

        if date_str:
            # Get article IDs from specific briefing
            cursor = await db.execute(
                "SELECT content FROM briefings WHERE date = ?", (date_str,)
            )
            row = await cursor.fetchone()
            if not row:
                raise HTTPException(status_code=404, detail=f"No briefing for {date_str}")

            content = json.loads(row["content"])
            all_ids = set()
            for h in content.get("headlines", []):
                all_ids.add(h["article_id"])
            for s in content.get("sections", []):
                all_ids.update(s["article_ids"])

            if not all_ids:
                return {"items": [], "total": 0}

            placeholders = ",".join("?" for _ in all_ids)
            article_cursor = await db.execute(
                f"""SELECT a.id, a.title, a.title_zh, a.url, a.summary_zh,
                           a.importance, a.published_at, s.name as source_name
                    FROM articles a
                    JOIN sources s ON a.source_id = s.id
                    WHERE a.id IN ({placeholders})
                      AND (a.title LIKE ? OR a.title_zh LIKE ?
                           OR a.summary_zh LIKE ? OR s.name LIKE ?)
                    ORDER BY a.importance DESC""",
                [*list(all_ids), search_pattern, search_pattern, search_pattern, search_pattern],
            )
        else:
            # Search across all briefing articles
            # First get all article IDs from all briefings
            briefing_cursor = await db.execute("SELECT content FROM briefings")
            briefing_rows = await briefing_cursor.fetchall()

            all_ids = set()
            for br in briefing_rows:
                content = json.loads(br["content"])
                for h in content.get("headlines", []):
                    all_ids.add(h["article_id"])
                for s in content.get("sections", []):
                    all_ids.update(s["article_ids"])

            if not all_ids:
                return {"items": [], "total": 0}

            placeholders = ",".join("?" for _ in all_ids)
            article_cursor = await db.execute(
                f"""SELECT a.id, a.title, a.title_zh, a.url, a.summary_zh,
                           a.importance, a.published_at, s.name as source_name
                    FROM articles a
                    JOIN sources s ON a.source_id = s.id
                    WHERE a.id IN ({placeholders})
                      AND (a.title LIKE ? OR a.title_zh LIKE ?
                           OR a.summary_zh LIKE ? OR s.name LIKE ?)
                    ORDER BY a.importance DESC
                    LIMIT 50""",
                [*list(all_ids), search_pattern, search_pattern, search_pattern, search_pattern],
            )

        rows = await article_cursor.fetchall()
        items = []
        for r in rows:
            tag_cursor = await db.execute(
                "SELECT tag FROM article_tags WHERE article_id = ?", (r["id"],)
            )
            tag_rows = await tag_cursor.fetchall()
            items.append({
                "id": r["id"],
                "title": r["title"],
                "title_zh": r["title_zh"],
                "url": r["url"],
                "summary_zh": r["summary_zh"],
                "importance": r["importance"],
                "published_at": r["published_at"],
                "source_name": r["source_name"],
                "tags": [t["tag"] for t in tag_rows],
            })

        return {"items": items, "total": len(items)}
    finally:
        await db.close()


@router.get("/{briefing_date}")
async def get_briefing(briefing_date: str) -> dict:
    """Get briefing for a specific date, with full article data."""
    result = await get_briefing_with_articles(briefing_date)
    if not result:
        raise HTTPException(status_code=404, detail=f"No briefing for {briefing_date}")
    return result
