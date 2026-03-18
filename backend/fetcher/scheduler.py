"""Scheduler: daily fetch at 10:00 and 17:00, plus startup catch-up."""

import logging
from datetime import datetime, date

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger

from database import get_db

logger = logging.getLogger(__name__)

_scheduler: AsyncIOScheduler | None = None


async def _run_scheduled_fetch():
    """Scheduled fetch job — imports lazily to avoid circular deps."""
    from fetcher import run_pipeline
    logger.info("Scheduled fetch triggered at %s", datetime.now().strftime("%H:%M"))
    await run_pipeline()


async def _check_startup_catchup():
    """If today's scheduled fetches haven't run yet, trigger one now.

    Checks last_fetched_at on any enabled source. If no source was fetched
    today, run a catch-up fetch.
    """
    db = await get_db()
    try:
        today = date.today().isoformat()
        cursor = await db.execute(
            "SELECT COUNT(*) FROM sources WHERE enabled = 1 AND last_fetched_at >= ?",
            (today,),
        )
        row = await cursor.fetchone()
        fetched_today = row[0] if row else 0
    finally:
        await db.close()

    if fetched_today == 0:
        logger.info("No fetches today — running startup catch-up")
        await _run_scheduled_fetch()
    else:
        logger.info("Sources already fetched today (%d), skipping catch-up", fetched_today)


def start_scheduler():
    """Start the APScheduler with daily 10:00 and 17:00 jobs."""
    global _scheduler
    _scheduler = AsyncIOScheduler()

    _scheduler.add_job(
        _run_scheduled_fetch,
        CronTrigger(hour=10, minute=0),
        id="fetch_morning",
        name="Morning fetch (10:00)",
    )
    _scheduler.add_job(
        _run_scheduled_fetch,
        CronTrigger(hour=17, minute=0),
        id="fetch_evening",
        name="Evening fetch (17:00)",
    )

    _scheduler.start()
    logger.info("Scheduler started: daily fetches at 10:00 and 17:00")


def stop_scheduler():
    """Stop the scheduler gracefully."""
    global _scheduler
    if _scheduler:
        _scheduler.shutdown(wait=False)
        _scheduler = None
        logger.info("Scheduler stopped")
