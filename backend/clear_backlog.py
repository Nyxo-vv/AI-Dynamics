"""Clear all unprocessed article backlog using batch processing."""

import asyncio
import logging
import sys
import time

sys.path.insert(0, ".")

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s: %(message)s",
)
logger = logging.getLogger("clear_backlog")


async def main():
    from database import init_db, get_db
    from llm.processor import process_unprocessed

    await init_db()

    # Check how many are pending
    db = await get_db()
    try:
        cursor = await db.execute(
            "SELECT COUNT(*) FROM articles WHERE title_zh IS NULL AND importance = 0"
        )
        total = (await cursor.fetchone())[0]
    finally:
        await db.close()

    if total == 0:
        print("没有积压文章，无需处理。")
        return

    print(f"\n积压文章: {total} 篇")
    print(f"预计分 {(total + 4) // 5} 个 batch 处理\n")

    t0 = time.time()
    done = 0
    failed_total = 0

    # Process in rounds of 200 to show progress
    while True:
        db = await get_db()
        try:
            cursor = await db.execute(
                "SELECT COUNT(*) FROM articles WHERE title_zh IS NULL AND importance = 0"
            )
            remaining = (await cursor.fetchone())[0]
        finally:
            await db.close()

        if remaining == 0:
            break

        elapsed = time.time() - t0
        print(f"[{elapsed:.0f}s] 剩余 {remaining} 篇，已完成 {done} 篇，失败 {failed_total} 篇")

        result = await process_unprocessed(limit=200)
        done += result["processed"]
        failed_total += result["failed"]

        if result["processed"] == 0 and result["failed"] == 0:
            print("本轮无文章处理，退出。")
            break

    elapsed = time.time() - t0
    print(f"\n===== 积压清理完成 =====")
    print(f"总处理: {done} 篇, 失败: {failed_total} 篇, 耗时: {elapsed:.0f}s ({elapsed/60:.1f}min)")


if __name__ == "__main__":
    asyncio.run(main())
