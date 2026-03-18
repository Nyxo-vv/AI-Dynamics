"""LLM multi-engine: Gemini → Groq → OpenRouter → Ollama.

Provides a unified generate() interface that tries engines in order.
Rate-limited engines (429) are retried before falling back.
Engines with empty API keys are skipped automatically.
"""

import asyncio
import json
import logging
import re
from datetime import date

import httpx
from google import genai
from groq import AsyncGroq

from config import settings

logger = logging.getLogger(__name__)

GEMINI_MODEL = "gemini-2.0-flash"

# Retry config for rate-limited (429) responses
MAX_RETRIES = 3

# Daily quota exhaustion tracking — skip engine for the rest of the day
_daily_exhausted: dict[str, date] = {}  # engine_name -> date when exhausted


def _mark_daily_exhausted(engine: str):
    """Mark an engine as exhausted for today."""
    _daily_exhausted[engine] = date.today()
    logger.warning("%s daily quota exhausted, skipping for the rest of today", engine)


def _is_daily_exhausted(engine: str) -> bool:
    """Check if an engine is exhausted today."""
    return _daily_exhausted.get(engine) == date.today()


def _parse_retry_delay(exc: Exception) -> float | None:
    """Try to extract retry delay from error message (Gemini/Groq 429)."""
    text = str(exc)
    # Match patterns like "retry in 8.966s" or "retryDelay: 8s"
    m = re.search(r"retry.*?(\d+\.?\d*)\s*s", text, re.IGNORECASE)
    if m:
        return min(float(m.group(1)), 30.0)  # cap at 30s
    if "429" in text or "rate" in text.lower():
        return 10.0  # default retry for rate limits
    return None


async def _call_with_retry(call_fn, name: str, prompt: str) -> str:
    """Call an LLM engine with automatic retry on rate limits."""
    last_exc = None
    for attempt in range(1, MAX_RETRIES + 1):
        try:
            return await call_fn(prompt)
        except Exception as exc:
            last_exc = exc
            delay = _parse_retry_delay(exc)
            if delay is None or attempt == MAX_RETRIES:
                raise
            logger.info(
                "%s rate-limited, retrying in %.0fs (attempt %d/%d)",
                name, delay, attempt, MAX_RETRIES,
            )
            await asyncio.sleep(delay)
    raise last_exc  # unreachable, but makes type checker happy


async def _call_gemini(prompt: str) -> str:
    """Call Gemini API. Raises on failure."""
    client = genai.Client(api_key=settings.GEMINI_API_KEY)
    response = client.models.generate_content(
        model=GEMINI_MODEL,
        contents=prompt,
    )
    return response.text


async def _call_groq(prompt: str) -> str:
    """Call Groq API. Raises on failure."""
    client = AsyncGroq(api_key=settings.GROQ_API_KEY)
    response = await client.chat.completions.create(
        model=settings.GROQ_MODEL,
        messages=[{"role": "user", "content": prompt}],
        temperature=0.3,
    )
    return response.choices[0].message.content


async def _call_openrouter(prompt: str) -> str:
    """Call OpenRouter API (OpenAI-compatible). Raises on failure."""
    url = "https://openrouter.ai/api/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {settings.OPENROUTER_API_KEY}",
        "Content-Type": "application/json",
    }
    payload = {
        "model": settings.OPENROUTER_MODEL,
        "messages": [{"role": "user", "content": prompt}],
        "temperature": 0.3,
    }
    async with httpx.AsyncClient(timeout=120) as client:
        resp = await client.post(url, headers=headers, json=payload)
        resp.raise_for_status()
        data = resp.json()
        if "choices" not in data or not data["choices"]:
            error_msg = data.get("error", {}).get("message", str(data))
            raise RuntimeError(f"OpenRouter returned no choices: {error_msg}")
        return data["choices"][0]["message"]["content"]


async def _call_ollama(prompt: str) -> str:
    """Call local Ollama. Raises on failure."""
    url = f"{settings.OLLAMA_BASE_URL}/api/generate"
    payload = {
        "model": settings.OLLAMA_MODEL,
        "prompt": prompt,
        "stream": False,
    }
    async with httpx.AsyncClient(timeout=120) as client:
        resp = await client.post(url, json=payload)
        resp.raise_for_status()
        data = resp.json()
        return data.get("response", "")


async def generate(prompt: str) -> str:
    """Generate text using the multi-engine strategy.

    Priority: Gemini → Groq → OpenRouter → Ollama.
    Rate-limited (429) engines are retried up to 3 times before falling back.

    Returns:
        Generated text from the LLM.

    Raises:
        RuntimeError: if all engines fail.
    """
    errors = []

    def _is_daily_quota_error(exc: Exception) -> bool:
        """Check if error indicates daily quota exhaustion (not just per-minute rate limit)."""
        text = str(exc).lower()
        return ("per day" in text or "per_day" in text or "PerDay" in str(exc)
                or "daily" in text or "quota exceeded" in text)

    # 1. Gemini (primary)
    if settings.use_gemini and not _is_daily_exhausted("gemini"):
        try:
            result = await _call_gemini(prompt)
            logger.debug("Gemini response OK (%d chars)", len(result))
            return result
        except Exception as exc:
            if _is_daily_quota_error(exc):
                _mark_daily_exhausted("gemini")
            errors.append(f"Gemini: {exc}")
            logger.warning("Gemini failed (%s), trying next engine", exc)

    # 2. Groq (secondary)
    if settings.use_groq and not _is_daily_exhausted("groq"):
        try:
            result = await _call_with_retry(_call_groq, "Groq", prompt)
            logger.debug("Groq response OK (%d chars)", len(result))
            return result
        except Exception as exc:
            if _is_daily_quota_error(exc):
                _mark_daily_exhausted("groq")
            errors.append(f"Groq: {exc}")
            logger.warning("Groq failed (%s), trying next engine", exc)

    # 3. OpenRouter (tertiary)
    if settings.use_openrouter and not _is_daily_exhausted("openrouter"):
        try:
            result = await _call_with_retry(_call_openrouter, "OpenRouter", prompt)
            logger.debug("OpenRouter response OK (%d chars)", len(result))
            return result
        except Exception as exc:
            if _is_daily_quota_error(exc):
                _mark_daily_exhausted("openrouter")
            errors.append(f"OpenRouter: {exc}")
            logger.warning("OpenRouter failed (%s), falling back to Ollama", exc)

    # 4. Ollama (fallback, no retry needed — local)
    try:
        result = await _call_ollama(prompt)
        logger.debug("Ollama response OK (%d chars)", len(result))
        return result
    except Exception as exc:
        errors.append(f"Ollama: {exc}")
        raise RuntimeError(f"All LLM engines failed: {'; '.join(errors)}") from exc


async def generate_json(prompt: str) -> dict | list:
    """Generate and parse JSON from LLM output.

    Extracts JSON from the response even if wrapped in markdown code fences.
    """
    raw = await generate(prompt)

    # Strip markdown code fences if present
    text = raw.strip()
    if text.startswith("```"):
        lines = text.split("\n")
        if lines[0].startswith("```"):
            lines = lines[1:]
        if lines and lines[-1].strip() == "```":
            lines = lines[:-1]
        text = "\n".join(lines)

    return json.loads(text)
