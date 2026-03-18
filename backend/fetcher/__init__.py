"""Fetcher package — full pipeline: RSS fetch → dedupe → LLM process → store."""

import logging

from fetcher.filter import arxiv_keyword_filter
from fetcher.rss import fetch_all_sources
from llm.processor import process_unprocessed

logger = logging.getLogger(__name__)

# Sources that need pre-filtering
FILTER_REGISTRY = {
    "arXiv cs.AI": arxiv_keyword_filter,
}


async def run_pipeline(*, llm_batch_size: int = 50, on_progress=None) -> dict:
    """Run the full fetch + process pipeline.

    1. Fetch all enabled RSS sources (with arXiv pre-filtering)
    2. Process new articles through LLM (translation, classification, scoring)

    Returns:
        {"fetch": {source: count}, "llm": {"processed": N, "failed": M}}
    """
    logger.info("=== Starting fetch pipeline ===")

    # Step 1: Fetch RSS
    fetch_results = await fetch_all_sources(
        filter_registry=FILTER_REGISTRY,
        on_progress=on_progress,
    )

    # Step 2: LLM processing
    llm_results = await process_unprocessed(limit=llm_batch_size)

    logger.info(
        "=== Pipeline complete: %d new articles, %d processed by LLM ===",
        sum(fetch_results.values()),
        llm_results["processed"],
    )

    return {"fetch": fetch_results, "llm": llm_results}
