import aiosqlite
from pathlib import Path
from config import settings

_db_path = settings.DATABASE_PATH


async def init_db():
    Path(_db_path).parent.mkdir(parents=True, exist_ok=True)
    async with aiosqlite.connect(_db_path) as db:
        await db.execute("PRAGMA journal_mode=WAL")

        await db.execute("""
            CREATE TABLE IF NOT EXISTS sources (
                id              INTEGER PRIMARY KEY,
                name            TEXT NOT NULL,
                url             TEXT NOT NULL UNIQUE,
                type            TEXT NOT NULL DEFAULT 'rss',
                category        TEXT NOT NULL DEFAULT 'media',
                enabled         BOOLEAN DEFAULT 1,
                fetch_interval_min INTEGER DEFAULT 60,
                last_fetched_at DATETIME,
                created_at      DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        """)

        await db.execute("""
            CREATE TABLE IF NOT EXISTS articles (
                id              INTEGER PRIMARY KEY,
                source_id       INTEGER NOT NULL REFERENCES sources(id),
                title           TEXT NOT NULL,
                title_zh        TEXT,
                url             TEXT NOT NULL UNIQUE,
                author          TEXT,
                content         TEXT,
                summary_zh      TEXT,
                cover_image     TEXT,
                images          TEXT,
                related_links   TEXT,
                language        TEXT DEFAULT 'en',
                published_at    DATETIME,
                fetched_at      DATETIME DEFAULT CURRENT_TIMESTAMP,
                importance      INTEGER DEFAULT 0,
                is_read         BOOLEAN DEFAULT 0,
                is_starred      BOOLEAN DEFAULT 0
            )
        """)

        await db.execute("""
            CREATE TABLE IF NOT EXISTS article_tags (
                article_id  INTEGER NOT NULL REFERENCES articles(id),
                tag         TEXT NOT NULL,
                PRIMARY KEY (article_id, tag)
            )
        """)

        await db.execute("""
            CREATE TABLE IF NOT EXISTS briefings (
                id              INTEGER PRIMARY KEY,
                date            DATE NOT NULL UNIQUE,
                window_start    DATETIME NOT NULL,
                window_end      DATETIME NOT NULL,
                content         TEXT NOT NULL,
                article_count   INTEGER NOT NULL,
                generated_at    DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        """)

        await db.execute("CREATE INDEX IF NOT EXISTS idx_articles_url ON articles(url)")
        await db.execute("CREATE INDEX IF NOT EXISTS idx_articles_published ON articles(published_at)")
        await db.execute("CREATE INDEX IF NOT EXISTS idx_articles_source ON articles(source_id)")
        await db.execute("CREATE INDEX IF NOT EXISTS idx_briefings_date ON briefings(date)")

        await db.commit()


async def get_db() -> aiosqlite.Connection:
    db = await aiosqlite.connect(_db_path)
    db.row_factory = aiosqlite.Row
    await db.execute("PRAGMA journal_mode=WAL")
    return db
