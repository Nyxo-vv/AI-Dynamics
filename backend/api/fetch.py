"""Fetch control API: manual trigger + status."""

import asyncio
import logging
from datetime import datetime, timezone

from fastapi import APIRouter

from models import FetchStatus

router = APIRouter(prefix="/api/fetch", tags=["fetch"])
logger = logging.getLogger(__name__)

# Shared state for fetch status
_status = FetchStatus()
_lock = asyncio.Lock()


def get_fetch_status() -> FetchStatus:
    return _status


@router.get("/status")
async def fetch_status() -> FetchStatus:
    """Get current fetch status."""
    return _status


@router.get("/backlog")
async def backlog_status(date: str | None = None) -> dict:
    """Get count of unprocessed articles (backlog).

    If date is provided (YYYY-MM-DD), returns backlog for that briefing window
    (previous day 09:00 ~ current day 09:00). Otherwise returns global backlog.
    """
    from database import get_db
    db = await get_db()
    try:
        if date:
            from datetime import datetime, timedelta
            d = datetime.strptime(date, "%Y-%m-%d")
            window_start = (d - timedelta(days=1)).strftime("%Y-%m-%d 09:00:00")
            window_end = d.strftime("%Y-%m-%d 09:00:00")
            cursor = await db.execute(
                """SELECT COUNT(*) FROM articles
                   WHERE title_zh IS NULL AND importance = 0
                     AND REPLACE(REPLACE(COALESCE(published_at, fetched_at), 'T', ' '), '+00:00', '') >= ?
                     AND REPLACE(REPLACE(COALESCE(published_at, fetched_at), 'T', ' '), '+00:00', '') < ?""",
                (window_start, window_end),
            )
            unprocessed = (await cursor.fetchone())[0]
            cursor = await db.execute(
                """SELECT COUNT(*) FROM articles
                   WHERE REPLACE(REPLACE(COALESCE(published_at, fetched_at), 'T', ' '), '+00:00', '') >= ?
                     AND REPLACE(REPLACE(COALESCE(published_at, fetched_at), 'T', ' '), '+00:00', '') < ?""",
                (window_start, window_end),
            )
            total = (await cursor.fetchone())[0]
        else:
            cursor = await db.execute(
                "SELECT COUNT(*) FROM articles WHERE title_zh IS NULL AND importance = 0"
            )
            unprocessed = (await cursor.fetchone())[0]
            cursor = await db.execute("SELECT COUNT(*) FROM articles")
            total = (await cursor.fetchone())[0]
    finally:
        await db.close()
    return {"unprocessed": unprocessed, "total": total}


@router.post("/run")
async def trigger_fetch() -> dict:
    """Manually trigger a fetch + LLM processing run."""
    if _status.status != "idle":
        return {"message": "Fetch already in progress", "status": _status}

    # Run in background so the API returns immediately
    asyncio.create_task(_run_fetch())
    return {"message": "Fetch started", "status": _status}


async def _run_fetch():
    """Background fetch task that updates shared status."""
    async with _lock:
        from database import get_db

        # Count enabled sources
        db = await get_db()
        try:
            cursor = await db.execute(
                "SELECT COUNT(*) FROM sources WHERE enabled = 1 AND type = 'rss'"
            )
            total = (await cursor.fetchone())[0]
        finally:
            await db.close()

        # Record start time to identify articles fetched in this run
        fetch_start = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S")

        _status.status = "fetching"
        _status.total_sources = total
        _status.processed_sources = 0
        _status.new_articles = 0
        _status.llm_total = 0
        _status.llm_processed = 0

        def _on_progress(processed: int, new_articles: int):
            _status.processed_sources = processed
            _status.new_articles = new_articles

        try:
            from fetcher.rss import fetch_all_sources
            from fetcher.filter import arxiv_keyword_filter
            from llm.processor import process_unprocessed_since

            # Phase 1: Fetch RSS
            fetch_results = await fetch_all_sources(
                filter_registry={"arXiv cs.AI": arxiv_keyword_filter},
                on_progress=_on_progress,
            )
            _status.processed_sources = len(fetch_results)
            _status.new_articles = sum(fetch_results.values())

            # Phase 2: LLM processing — only process articles fetched in this run
            db = await get_db()
            try:
                cursor = await db.execute(
                    """SELECT COUNT(*) FROM articles
                       WHERE title_zh IS NULL AND importance = 0
                         AND fetched_at >= ?""",
                    (fetch_start,),
                )
                llm_total = (await cursor.fetchone())[0]
            finally:
                await db.close()

            if llm_total > 0:
                _status.status = "processing"
                _status.llm_total = llm_total
                _status.llm_processed = 0

                llm_results = await process_unprocessed_since(
                    since=fetch_start,
                    on_progress=lambda done, _failed: setattr(_status, "llm_processed", done),
                )
            else:
                llm_results = {"processed": 0, "failed": 0}

            logger.info(
                "Pipeline complete: %d new articles, %d processed by LLM",
                sum(fetch_results.values()),
                llm_results["processed"],
            )
        except Exception as exc:
            logger.error("Fetch pipeline error: %s", exc)
        finally:
            _status.status = "idle"
