"""Monthly data cleanup + JSON.gz archive.

On startup, checks if last month's data still exists and archives + deletes it.
Keeps only ~2 months of active data in the database.
"""

import gzip
import json
import logging
from datetime import date, datetime
from pathlib import Path

import aiosqlite

from config import settings

logger = logging.getLogger(__name__)

ARCHIVE_DIR = Path(settings.DATABASE_PATH).parent / "archive"


def _last_month_range() -> tuple[str, str]:
    """Return (start, end) ISO date strings for last month."""
    today = date.today()
    # First day of current month
    first_of_this_month = today.replace(day=1)
    # Last day of previous month
    last_of_prev_month = first_of_this_month.replace(day=1)
    # First day of previous month
    if today.month == 1:
        first_of_prev_month = date(today.year - 1, 12, 1)
    else:
        first_of_prev_month = date(today.year, today.month - 1, 1)

    return first_of_prev_month.isoformat(), first_of_this_month.isoformat()


async def _export_archive(db: aiosqlite.Connection, month_start: str, month_end: str) -> Path | None:
    """Export articles, tags, and briefings for the month to a .json.gz file."""
    ARCHIVE_DIR.mkdir(parents=True, exist_ok=True)

    # Collect articles
    db.row_factory = aiosqlite.Row
    cursor = await db.execute(
        """SELECT * FROM articles
           WHERE (published_at >= ? AND published_at < ?)
              OR (published_at IS NULL AND fetched_at >= ? AND fetched_at < ?)""",
        (month_start, month_end, month_start, month_end),
    )
    articles = [dict(row) for row in await cursor.fetchall()]

    if not articles:
        return None

    article_ids = [a["id"] for a in articles]

    # Collect tags
    placeholders = ",".join("?" * len(article_ids))
    cursor = await db.execute(
        f"SELECT * FROM article_tags WHERE article_id IN ({placeholders})",
        article_ids,
    )
    tags = [dict(row) for row in await cursor.fetchall()]

    # Collect briefings
    cursor = await db.execute(
        "SELECT * FROM briefings WHERE date >= ? AND date < ?",
        (month_start, month_end),
    )
    briefings = [dict(row) for row in await cursor.fetchall()]

    archive_data = {
        "month": month_start[:7],
        "exported_at": datetime.now().isoformat(),
        "articles": articles,
        "article_tags": tags,
        "briefings": briefings,
    }

    # Write compressed JSON
    filename = f"{month_start[:7]}.json.gz"
    filepath = ARCHIVE_DIR / filename
    with gzip.open(filepath, "wt", encoding="utf-8") as f:
        json.dump(archive_data, f, ensure_ascii=False, default=str)

    logger.info(
        "Archived %s: %d articles, %d tags, %d briefings → %s",
        month_start[:7], len(articles), len(tags), len(briefings), filepath,
    )
    return filepath


async def _delete_month_data(db: aiosqlite.Connection, month_start: str, month_end: str) -> int:
    """Delete articles, tags, and briefings for the given month. Returns article count deleted."""
    # Delete tags first (FK dependency)
    await db.execute(
        """DELETE FROM article_tags WHERE article_id IN (
               SELECT id FROM articles
               WHERE (published_at >= ? AND published_at < ?)
                  OR (published_at IS NULL AND fetched_at >= ? AND fetched_at < ?))""",
        (month_start, month_end, month_start, month_end),
    )

    # Delete briefings
    await db.execute(
        "DELETE FROM briefings WHERE date >= ? AND date < ?",
        (month_start, month_end),
    )

    # Delete articles
    cursor = await db.execute(
        """DELETE FROM articles
           WHERE (published_at >= ? AND published_at < ?)
              OR (published_at IS NULL AND fetched_at >= ? AND fetched_at < ?)""",
        (month_start, month_end, month_start, month_end),
    )
    deleted = cursor.rowcount

    await db.commit()

    # Reclaim space
    await db.execute("VACUUM")

    return deleted


async def check_and_cleanup():
    """Startup check: archive and clean up last month's data if still present.

    Safe to call multiple times — skips if archive already exists.
    """
    month_start, month_end = _last_month_range()
    month_label = month_start[:7]

    # Skip if already archived
    archive_file = ARCHIVE_DIR / f"{month_label}.json.gz"
    if archive_file.exists():
        logger.info("Archive for %s already exists, skipping cleanup", month_label)
        return

    db = await aiosqlite.connect(settings.DATABASE_PATH)
    db.row_factory = aiosqlite.Row
    try:
        # Check if there's data to clean
        cursor = await db.execute(
            """SELECT COUNT(*) FROM articles
               WHERE (published_at >= ? AND published_at < ?)
                  OR (published_at IS NULL AND fetched_at >= ? AND fetched_at < ?)""",
            (month_start, month_end, month_start, month_end),
        )
        row = await cursor.fetchone()
        count = row[0] if row else 0

        if count == 0:
            logger.info("No data for %s to clean up", month_label)
            return

        logger.info("Found %d articles for %s — archiving and cleaning up", count, month_label)

        # Archive first
        await _export_archive(db, month_start, month_end)

        # Then delete
        deleted = await _delete_month_data(db, month_start, month_end)
        logger.info("Cleanup complete: %d articles deleted for %s", deleted, month_label)

    finally:
        await db.close()
