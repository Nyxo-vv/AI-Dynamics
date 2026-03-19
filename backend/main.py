import asyncio
import logging
from contextlib import asynccontextmanager

import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from database import init_db, get_db
from fetcher.cleanup import check_and_cleanup

# Shared event: set when briefing generation is in progress
# Backlog processing pauses while this is set
briefing_in_progress = asyncio.Event()
from fetcher.scheduler import start_scheduler, stop_scheduler, _check_startup_catchup
from api.articles import router as articles_router
from api.sources import router as sources_router
from api.briefings import router as briefings_router
from api.fetch import router as fetch_router

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s: %(message)s",
)


logger = logging.getLogger(__name__)


async def _process_backlog():
    """Background task: process unprocessed articles on startup.

    Only processes articles from the last 7 days. Older unprocessed
    articles are deleted as they are outside the display window.
    """
    from llm.processor import process_unprocessed

    db = await get_db()
    try:
        # Delete unprocessed articles older than 7 days
        await db.execute(
            """DELETE FROM article_tags WHERE article_id IN (
                SELECT id FROM articles
                WHERE title_zh IS NULL AND importance = 0
                  AND COALESCE(published_at, fetched_at) < datetime('now', '-7 days')
            )"""
        )
        cursor = await db.execute(
            """DELETE FROM articles
               WHERE title_zh IS NULL AND importance = 0
                 AND COALESCE(published_at, fetched_at) < datetime('now', '-7 days')"""
        )
        if cursor.rowcount > 0:
            await db.commit()
            logger.info("Deleted %d old unprocessed articles (>7 days)", cursor.rowcount)

        # Count remaining
        cursor = await db.execute(
            "SELECT COUNT(*) FROM articles WHERE title_zh IS NULL AND importance = 0"
        )
        count = (await cursor.fetchone())[0]
    finally:
        await db.close()

    if count == 0:
        return

    logger.info("Found %d unprocessed articles (last 7 days), starting backlog processing...", count)

    while True:
        # Pause if a manual fetch or briefing generation is running
        from api.fetch import get_fetch_status
        if get_fetch_status().status != "idle":
            logger.info("Backlog paused: manual fetch in progress")
            await asyncio.sleep(10)
            continue
        if briefing_in_progress.is_set():
            logger.info("Backlog paused: briefing generation in progress")
            await asyncio.sleep(5)
            continue

        db = await get_db()
        try:
            cursor = await db.execute(
                "SELECT COUNT(*) FROM articles WHERE title_zh IS NULL AND importance = 0"
            )
            remaining = (await cursor.fetchone())[0]
        finally:
            await db.close()

        if remaining == 0:
            logger.info("Backlog processing complete")
            break

        # process_unprocessed already orders by newest first
        result = await process_unprocessed(limit=200)
        if result["processed"] == 0 and result["failed"] == 0:
            break

        logger.info("Backlog progress: %d remaining", remaining)


@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_db()
    await check_and_cleanup()
    start_scheduler()
    # Process backlog in background (non-blocking)
    asyncio.create_task(_process_backlog())
    yield
    stop_scheduler()


app = FastAPI(title="AI Dynamics", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:5174"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(articles_router)
app.include_router(sources_router)
app.include_router(briefings_router)
app.include_router(fetch_router)


@app.get("/api/health")
async def health():
    return {"status": "ok"}


if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=9100, reload=True)
