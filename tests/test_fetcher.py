from unittest import mock

from src.utils.fetcher import fetch_articles, _search_urls


def test_search_fallback(monkeypatch):
    """If Google search fails, DuckDuckGo should be used."""
    # Force googlesearch.search to raise error
    with mock.patch("src.utils.fetcher.search", side_effect=Exception("Google down")):
        with mock.patch("src.utils.fetcher.ddg", return_value=[{"href": "https://example.com"}]):
            urls = _search_urls("test", 1)
    assert urls == ["https://example.com"]


def test_fetch_articles(monkeypatch):
    html = "<html><body><h1>Title</h1><p>Some content.</p></body></html>"
    with mock.patch("src.utils.fetcher._safe_get") as fake_get:
        fake_get.return_value.status_code = 200
        fake_get.return_value.text = html
        articles = fetch_articles("test", 1)
    assert len(articles) == 1
    assert "content" in articles[0]