"""Articles API: list, search, filter, read/star management."""

import json

from fastapi import APIRouter, Query

from database import get_db
from models import Article, ArticleUpdate

router = APIRouter(prefix="/api/articles", tags=["articles"])


@router.get("")
async def list_articles(
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=100),
    category: str | None = None,
    source_id: int | None = None,
    is_starred: bool | None = None,
    search: str | None = None,
) -> dict:
    """List articles with pagination and filtering."""
    db = await get_db()
    try:
        conditions = []
        params: list = []

        if category:
            conditions.append(
                "a.id IN (SELECT article_id FROM article_tags WHERE tag = ?)"
            )
            params.append(category)

        if source_id is not None:
            conditions.append("a.source_id = ?")
            params.append(source_id)

        if is_starred is not None:
            conditions.append("a.is_starred = ?")
            params.append(1 if is_starred else 0)

        if search:
            conditions.append(
                "(a.title LIKE ? OR a.title_zh LIKE ? OR a.summary_zh LIKE ?)"
            )
            term = f"%{search}%"
            params.extend([term, term, term])

        where = " AND ".join(conditions) if conditions else "1=1"

        # Count
        cursor = await db.execute(
            f"SELECT COUNT(*) FROM articles a WHERE {where}", params
        )
        total = (await cursor.fetchone())[0]

        # Fetch page
        offset = (page - 1) * per_page
        cursor = await db.execute(
            f"""SELECT a.*, s.name as source_name
                FROM articles a
                JOIN sources s ON a.source_id = s.id
                WHERE {where}
                ORDER BY a.published_at DESC NULLS LAST, a.fetched_at DESC
                LIMIT ? OFFSET ?""",
            params + [per_page, offset],
        )
        rows = await cursor.fetchall()

        # Attach tags
        articles = []
        for row in rows:
            article = dict(row)
            tag_cursor = await db.execute(
                "SELECT tag FROM article_tags WHERE article_id = ?",
                (article["id"],),
            )
            article["tags"] = [t["tag"] for t in await tag_cursor.fetchall()]
            # Parse JSON fields
            for field in ("images", "related_links"):
                if article.get(field):
                    try:
                        article[field] = json.loads(article[field])
                    except (json.JSONDecodeError, TypeError):
                        pass
            articles.append(article)

        return {
            "items": articles,
            "total": total,
            "page": page,
            "per_page": per_page,
            "pages": (total + per_page - 1) // per_page,
        }
    finally:
        await db.close()


@router.get("/{article_id}")
async def get_article(article_id: int) -> dict:
    """Get a single article by ID."""
    db = await get_db()
    try:
        cursor = await db.execute(
            """SELECT a.*, s.name as source_name
               FROM articles a JOIN sources s ON a.source_id = s.id
               WHERE a.id = ?""",
            (article_id,),
        )
        row = await cursor.fetchone()
        if not row:
            return {"error": "not found"}

        article = dict(row)
        tag_cursor = await db.execute(
            "SELECT tag FROM article_tags WHERE article_id = ?", (article_id,)
        )
        article["tags"] = [t["tag"] for t in await tag_cursor.fetchall()]
        for field in ("images", "related_links"):
            if article.get(field):
                try:
                    article[field] = json.loads(article[field])
                except (json.JSONDecodeError, TypeError):
                    pass
        return article
    finally:
        await db.close()


@router.patch("/{article_id}")
async def update_article(article_id: int, update: ArticleUpdate) -> dict:
    """Update article read/starred status."""
    db = await get_db()
    try:
        sets = []
        params: list = []
        if update.is_read is not None:
            sets.append("is_read = ?")
            params.append(1 if update.is_read else 0)
        if update.is_starred is not None:
            sets.append("is_starred = ?")
            params.append(1 if update.is_starred else 0)

        if not sets:
            return {"error": "no fields to update"}

        params.append(article_id)
        await db.execute(
            f"UPDATE articles SET {', '.join(sets)} WHERE id = ?", params
        )
        await db.commit()
        return {"ok": True}
    finally:
        await db.close()
