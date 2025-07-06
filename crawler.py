"""crawler.py

Responsible for discovering fresh URLs about ``config.TOPIC`` and extracting
clean article text that downstream components (summariser, generator, etc.)
can work with.

1. Uses duckduckgo_search to get a list of candidate links (non-tracking).
2. Runs newspaper3k to download and parse each page into title & raw text.

Returned objects are simple ``dict`` instances – easy to JSON-serialise or
put into pandas, but lightweight enough for quick scripting.

Example
-------
>>> import config, crawler
>>> crawler.fetch_articles(config.TOPIC, 3)
[{"title": "…", "text": "…", "url": "https://…"}, …]
"""

from __future__ import annotations

import logging
from typing import List, Dict, Optional, Any

from duckduckgo_search import DDGS
from newspaper import Article

import config

# Configure a basic logger. Downstream apps can override this.
logging.basicConfig(level=logging.INFO, format="%(levelname)s:%(name)s:%(message)s")
logger = logging.getLogger("crawler")

# ----------------------------
# Core helpers
# ----------------------------


def _search_urls(query: str, max_results: int) -> List[str]:
    """Return up to *max_results* unique HTTP(S) URLs for *query*.

    We hit DuckDuckGo through the ``duckduckgo_search`` library which scrapes
    the HTML search results page (no API key required). Each result dict has
    an ``href`` key (the raw link). We de-duplicate on the fly.
    """
    urls: List[str] = []
    with DDGS() as ddgs:
        for hit in ddgs.text(query, safesearch="off", max_results=max_results):
            url: Optional[str] = hit.get("href") or hit.get("url")
            if url and url.startswith("http") and url not in urls:
                urls.append(url)
            if len(urls) >= max_results:
                break
    logger.info("Found %d candidate URLs for query '%s'", len(urls), query)
    return urls


def _parse_article(url: str, *, min_length: int = 200) -> Optional[Dict[str, Any]]:
    """Download *url* and return a dict with title & cleaned text.

    ``newspaper3k`` handles boilerplate removal, language detection, etc.
    We discard results that are too short (< *min_length* characters) because
    they are unlikely to be substantive.
    """
    try:
        article = Article(url, language="en")  # let it auto-detect language but prefer EN
        article.download()
        article.parse()
        text = article.text.strip()
        if len(text) < min_length:
            logger.debug("Skipping %s – content too short (%d chars)", url, len(text))
            return None
        return {
            "url": url,
            "title": article.title or "Untitled",
            "text": text,
            "authors": article.authors,
            "publish_date": article.publish_date.isoformat() if article.publish_date else None,
        }
    except Exception as exc:  # noqa: BLE001
        logger.warning("Failed to parse %s: %s", url, exc)
        return None


# ----------------------------
# Public API
# ----------------------------


def fetch_articles(topic: str, k: int | None = None) -> List[Dict[str, Any]]:
    """Return up to *k* solid articles about *topic*.

    We query ~4× more links than we strictly need to account for parsing
    failures and paywalls, then stop once we've collected *k* good ones.
    """
    if k is None:
        k = config.NUM_ARTICLES

    candidate_urls = _search_urls(topic, max_results=k * 4)

    articles: List[Dict[str, Any]] = []
    for url in candidate_urls:
        parsed = _parse_article(url)
        if parsed:
            articles.append(parsed)
        if len(articles) >= k:
            break

    logger.info("Returning %d/%d requested articles", len(articles), k)
    return articles


if __name__ == "__main__":
    # Quick manual test when running `python crawler.py` locally.
    import json

    res = fetch_articles(config.TOPIC, 2)
    print(json.dumps(res, indent=2)[:2000])  # print first 2k chars only