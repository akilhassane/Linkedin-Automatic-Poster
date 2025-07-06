import logging
from typing import List, Dict
import requests
from bs4 import BeautifulSoup
from googlesearch import search


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


def fetch_articles(topic: str, max_results: int = 5) -> List[Dict[str, str]]:
    """Searches Google for the topic and returns a list of dicts with title & content."""
    query = f"{topic} latest news"
    urls = []
    try:
        for url in search(query, num_results=max_results, lang="en"):
            urls.append(url)
    except Exception as exc:
        logging.error("Google search failed: %s", exc)
        return []

    articles = []
    for url in urls:
        try:
            resp = requests.get(url, headers=HEADERS, timeout=10)
            resp.raise_for_status()
            text = _clean_text(resp.text)
            title = url.split("//")[-1][:80]
            articles.append({"url": url, "title": title, "content": text})
        except Exception as exc:
            logging.warning("Failed to fetch %s: %s", url, exc)
            continue

    return articles