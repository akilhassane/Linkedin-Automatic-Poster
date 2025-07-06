"""summariser.py

Unified interface for generating abstractive summaries of raw article text.

Priority order:
1. HuggingFace *hosted* inference endpoint (free tier, rate-limited).
2. Local inference via ``transformers`` (downloads the same model), triggered
   automatically on API failure or when ``OFFLINE=1`` env var is present.

Public functions
----------------
- summarise(text: str) -> str
- summarise_batch(texts: list[str]) -> list[str]

Typical usage
-------------
>>> import crawler, summariser, config
>>> raw_articles = crawler.fetch_articles(config.TOPIC, 3)
>>> summaries = [summariser.summarise(a["text"]) for a in raw_articles]
"""
from __future__ import annotations

import json
import logging
import os
import time
from typing import List, Optional

import requests

import config

logger = logging.getLogger("summariser")
logging.basicConfig(level=logging.INFO, format="%(levelname)s:%(name)s:%(message)s")

# HF Inference API -----------------------------------------------------------

API_URL = f"https://api-inference.huggingface.co/models/{config.HUGGINGFACE_MODEL}"
HEADERS = {
    "Authorization": f"Bearer {config.HUGGINGFACE_TOKEN}"
} if config.HUGGINGFACE_TOKEN else {}

# Local transformers pipeline objects are created lazily only if needed.
_SUMMARY_PIPELINE = None  # type: ignore

# HuggingFace free tier limits input length to ~ 600-1000 tokens depending on model.
_MAX_CHARS = 4000  # safe upper bound – we'll truncate longer inputs.


def _remote_summarise(text: str, *, max_len: int = 120) -> str:
    """Call the hosted HF inference API. Raises ``RuntimeError`` if it fails."""
    truncated = text[:_MAX_CHARS]
    payload = {
        "inputs": truncated,
        "parameters": {"max_length": max_len, "do_sample": False},
        "options": {"wait_for_model": True},
    }
    try:
        response = requests.post(API_URL, headers=HEADERS, json=payload, timeout=60)
    except requests.RequestException as exc:  # network errors etc.
        raise RuntimeError(f"Network error contacting HF API: {exc}") from exc

    if response.status_code == 200:
        data = response.json()
        # Either a list of dicts or list of str depending on model
        if isinstance(data, list):
            maybe = data[0]
            if isinstance(maybe, dict) and "summary_text" in maybe:
                return maybe["summary_text"].strip()
            if isinstance(maybe, str):
                return maybe.strip()
        raise RuntimeError(f"Unexpected response format: {data[:100]}")

    # Non-200: could be loading, rate-limited, or error.
    if response.status_code == 503 and "estimated_time" in response.text:
        # Model is loading – sleep and retry once.
        logger.info("Model loading, retrying once after 10 s…")
        time.sleep(10)
        return _remote_summarise(text, max_len=max_len)

    try:
        err = response.json()
    except json.JSONDecodeError:
        err = response.text
    raise RuntimeError(f"HF API error {response.status_code}: {err}")


# Local fallback -------------------------------------------------------------

def _ensure_local_pipeline():
    """Lazy-initialise the local transformers summarisation pipeline."""
    global _SUMMARY_PIPELINE  # noqa: PLW0603
    if _SUMMARY_PIPELINE is None:
        from transformers import pipeline  # type: ignore # heavy import

        logger.info("Loading local summarisation model '%s'…", config.HUGGINGFACE_MODEL)
        _SUMMARY_PIPELINE = pipeline(
            "summarization",
            model=config.HUGGINGFACE_MODEL,
            tokenizer=config.HUGGINGFACE_MODEL,
            framework="pt",
            device=-1,  # CPU
        )


def _local_summarise(text: str, *, max_len: int = 120) -> str:
    _ensure_local_pipeline()
    assert _SUMMARY_PIPELINE is not None
    truncated = text[:_MAX_CHARS]
    outputs = _SUMMARY_PIPELINE(truncated, max_length=max_len, do_sample=False)
    return outputs[0]["summary_text"].strip()


# Public API -----------------------------------------------------------------

def summarise(text: str, *, max_len: int = 120) -> str:
    """Return an abstractive summary of *text* (~``max_len`` tokens)."""
    if os.getenv("OFFLINE") == "1":
        logger.debug("OFFLINE=1 -> forcing local summarisation")
        return _local_summarise(text, max_len=max_len)

    try:
        return _remote_summarise(text, max_len=max_len)
    except RuntimeError as exc:
        logger.warning("Remote summarisation failed (%s). Falling back to local.", exc)
        return _local_summarise(text, max_len=max_len)


def summarise_batch(texts: List[str], *, max_len: int = 120, sleep_s: int = 1) -> List[str]:
    """Summarise many *texts* in sequence. Remote API is rate-limited, so we sleep between calls."""
    summaries: List[str] = []
    for idx, txt in enumerate(texts, 1):
        logger.info("Summarising article %d/%d", idx, len(texts))
        summaries.append(summarise(txt, max_len=max_len))
        if idx < len(texts):
            time.sleep(sleep_s)
    return summaries


if __name__ == "__main__":
    # Lightweight self-test from CLI.
    sample = (
        "Quantum computing is an area of computing focused on developing computer technology based on the principles of quantum theory,"
        " which explains the nature and behavior of energy and matter on the quantum (atomic and subatomic) level. …"
    )
    print(summarise(sample))