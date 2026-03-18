"""Sources API: list and enable/disable RSS sources."""

from fastapi import APIRouter

from database import get_db

router = APIRouter(prefix="/api/sources", tags=["sources"])


@router.get("")
async def list_sources() -> list[dict]:
    """List all sources with article counts."""
    db = await get_db()
    try:
        cursor = await db.execute(
            """SELECT s.*, COUNT(a.id) as article_count
               FROM sources s LEFT JOIN articles a ON s.id = a.source_id
               GROUP BY s.id
               ORDER BY s.category, s.name"""
        )
        return [dict(row) for row in await cursor.fetchall()]
    finally:
        await db.close()


@router.patch("/{source_id}")
async def toggle_source(source_id: int, enabled: bool) -> dict:
    """Enable or disable a source."""
    db = await get_db()
    try:
        await db.execute(
            "UPDATE sources SET enabled = ? WHERE id = ?",
            (1 if enabled else 0, source_id),
        )
        await db.commit()
        return {"ok": True}
    finally:
        await db.close()
