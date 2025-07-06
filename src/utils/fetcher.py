import logging
from typing import List, Dict
import requests
from bs4 import BeautifulSoup
from googlesearch import search  # type: ignore
from duckduckgo_search import ddg  # type: ignore
from readability import Document  # type: ignore

# Rate limiting – at most 10 HTTP GETs per 60 seconds
from ratelimit import limits, sleep_and_retry  # type: ignore

# Constants for ratelimit decorator
CALLS = 10
PERIOD = 60  # seconds

HEADERS = {
    "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0 Safari/537.36"
}

def _clean_text(html: str) -> str:
    soup = BeautifulSoup(html, "html.parser")
    # Remove scripts and style
    for tag in soup(["script", "style", "noscript"]):
        tag.decompose()
    text = " ".join(soup.stripped_strings)
    return text

@sleep_and_retry
@limits(calls=CALLS, period=PERIOD)
def _safe_get(url: str) -> requests.Response:
    """Rate-limited HTTP GET wrapper."""
    return requests.get(url, headers=HEADERS, timeout=10)

def _search_urls(topic: str, max_results: int) -> List[str]:
    """Find URLs using Google search first, then DuckDuckGo as fallback."""
    query = f"{topic} news"
    urls: List[str] = []
    try:
        urls = list(search(query, num_results=max_results, lang="en"))  # type: ignore
        logging.debug("Google search returned %d urls", len(urls))
    except Exception as exc:
        logging.warning("Google search failed (%s). Falling back to DuckDuckGo.", exc)

    if not urls:
        try:
            ddg_results = ddg(query, max_results)
            urls = [r["href"] for r in ddg_results]
            logging.debug("DuckDuckGo returned %d urls", len(urls))
        except Exception as exc:
            logging.error("DuckDuckGo search failed: %s", exc)
    return urls[:max_results]

def _extract_readable(html: str) -> str:
    try:
        doc = Document(html)
        return _clean_text(doc.summary())
    except Exception:
        return _clean_text(html)

def fetch_articles(topic: str, max_results: int = 5) -> List[Dict[str, str]]:
    """Return title & cleaned text for up to *max_results* articles on *topic*."""
    urls = _search_urls(topic, max_results)
    if not urls:
        return []

    articles: List[Dict[str, str]] = []
    for url in urls:
        try:
            resp = _safe_get(url)
            resp.raise_for_status()
            text = _extract_readable(resp.text)
            title = url.split("//")[-1][:100]
            articles.append({"url": url, "title": title, "content": text})
        except Exception as exc:
            logging.warning("Failed to fetch %s: %s", url, exc)
            continue

    return articles