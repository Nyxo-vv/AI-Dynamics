"""Pre-filters for high-volume RSS sources (e.g. arXiv cs.AI).

arXiv cs.AI publishes 50-100+ papers daily. We use keyword matching on
title + abstract to keep only high-relevance papers (~10-20/day) before
sending them through the LLM pipeline.
"""

import re
from typing import Any

# High-value keywords — papers matching any of these are kept.
# Case-insensitive, word-boundary matching.
ARXIV_KEYWORDS: list[str] = [
    # Core LLM / foundation model topics
    r"large language model",
    r"LLM",
    r"GPT",
    r"transformer",
    r"foundation model",
    r"pre-?train",
    r"fine-?tun",
    r"instruction[\s-]?tun",
    r"RLHF",
    r"reinforcement learning from human",
    r"DPO",
    r"alignment",
    # Reasoning & agents
    r"chain[\s-]?of[\s-]?thought",
    r"reasoning",
    r"agent",
    r"tool[\s-]?use",
    r"function[\s-]?call",
    r"planning",
    r"multi[\s-]?agent",
    # Retrieval & generation
    r"RAG",
    r"retrieval[\s-]?augmented",
    r"in[\s-]?context[\s-]?learning",
    r"prompt",
    # Multimodal
    r"multimodal",
    r"vision[\s-]?language",
    r"text[\s-]?to[\s-]?image",
    r"diffusion",
    r"video[\s-]?generation",
    # Efficiency & deployment
    r"quantiz",
    r"distill",
    r"MoE",
    r"mixture[\s-]?of[\s-]?expert",
    r"sparse",
    r"efficient",
    r"inference",
    r"speculative[\s-]?decod",
    # Safety & evaluation
    r"safety",
    r"hallucination",
    r"benchmark",
    r"evaluat",
    r"red[\s-]?team",
    r"jailbreak",
    # Notable architectures / methods
    r"mamba",
    r"state[\s-]?space",
    r"attention",
    r"KV[\s-]?cache",
    r"context[\s-]?window",
    r"long[\s-]?context",
    # Specific model families (catch announcements)
    r"LLaMA",
    r"Gemini",
    r"Claude",
    r"Mistral",
    r"Qwen",
    r"DeepSeek",
]

# Compile a single pattern for performance
_KEYWORD_PATTERN = re.compile(
    "|".join(ARXIV_KEYWORDS),
    re.IGNORECASE,
)


async def arxiv_keyword_filter(entry: dict[str, Any]) -> bool:
    """Return True if the arXiv entry matches high-value keywords.

    Checks title + summary (abstract). The function is async to match
    the filter_fn signature expected by fetch_single_source.
    """
    title = entry.get("title", "")
    summary = entry.get("summary", "")
    text = f"{title} {summary}"
    return bool(_KEYWORD_PATTERN.search(text))
