"""Seed all RSS sources into the database."""

import asyncio
from database import get_db, init_db

SOURCES = [
    # Labs / Official
    ("OpenAI", "https://openai.com/news/rss.xml", "rss", "lab"),
    ("Google DeepMind", "https://deepmind.google/blog/rss.xml", "rss", "lab"),
    ("Google AI Blog", "https://blog.google/technology/ai/rss/", "rss", "lab"),
    # Anthropic — 官方 RSS 已下线，RSSHub 公共实例 403，需自建 RSSHub 后启用
    # ("Anthropic", "https://rsshub.app/anthropic/news", "rss", "lab"),
    ("Engineering at Meta", "https://engineering.fb.com/feed/", "rss", "lab"),
    ("Microsoft AI", "https://blogs.microsoft.com/ai/feed/", "rss", "lab"),
    # Academic
    ("arXiv cs.AI", "https://arxiv.org/rss/cs.AI", "rss", "academic"),
    ("MarkTechPost", "https://www.marktechpost.com/feed/", "rss", "academic"),
    # Media
    ("MIT Technology Review", "https://www.technologyreview.com/topic/artificial-intelligence/feed/", "rss", "media"),
    ("WIRED AI", "https://www.wired.com/feed/tag/ai/latest/rss", "rss", "media"),
    ("Ars Technica AI", "https://arstechnica.com/tag/artificial-intelligence/feed/", "rss", "media"),
    # Open Source
    ("Hugging Face Blog", "https://huggingface.co/blog/feed.xml", "rss", "opensource"),
    # Community
    ("Reddit r/MachineLearning", "https://www.reddit.com/r/MachineLearning/.rss", "rss", "community"),
    ("Reddit r/LocalLLaMA", "https://www.reddit.com/r/LocalLLaMA/.rss", "rss", "community"),
    # Chinese (jiqizhixin RSS discontinued — disabled for now)
    # ("机器之心", "https://www.jiqizhixin.com/rss", "rss", "chinese"),
]


async def seed_sources():
    await init_db()
    db = await get_db()
    try:
        for name, url, type_, category in SOURCES:
            await db.execute(
                "INSERT OR IGNORE INTO sources (name, url, type, category) VALUES (?, ?, ?, ?)",
                (name, url, type_, category),
            )
        await db.commit()
        cursor = await db.execute("SELECT COUNT(*) FROM sources")
        row = await cursor.fetchone()
        print(f"Sources seeded: {row[0]} total")
    finally:
        await db.close()


if __name__ == "__main__":
    asyncio.run(seed_sources())
