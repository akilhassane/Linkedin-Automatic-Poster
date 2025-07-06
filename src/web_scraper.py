import asyncio
import logging
import time
from typing import List, Dict, Optional
from dataclasses import dataclass
from urllib.parse import urljoin, urlparse
import requests
from bs4 import BeautifulSoup
import feedparser
from newspaper import Article
import httpx
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager

from config.settings import settings

@dataclass
class WebContent:
    """Structure for web content"""
    title: str
    content: str
    url: str
    source: str
    publish_date: Optional[str] = None
    summary: Optional[str] = None
    keywords: Optional[List[str]] = None
    relevance_score: float = 0.0

class WebScraper:
    """Web scraper for gathering content about specific topics"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': settings.web_scraping.user_agent
        })
        self.search_engines = [
            "https://www.google.com/search?q=",
            "https://duckduckgo.com/?q=",
            "https://www.bing.com/search?q="
        ]
        self.news_sources = [
            "https://news.google.com/rss/search?q=",
            "https://feeds.feedburner.com/oreilly/radar",
            "https://techcrunch.com/feed/",
            "https://www.wired.com/feed/",
            "https://www.theverge.com/rss/index.xml"
        ]
    
    def get_selenium_driver(self) -> webdriver.Chrome:
        """Create and configure Chrome driver"""
        options = Options()
        if settings.web_scraping.selenium_headless:
            options.add_argument("--headless")
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")
        options.add_argument("--disable-gpu")
        options.add_argument(f"--user-agent={settings.web_scraping.user_agent}")
        
        driver = webdriver.Chrome(
            ChromeDriverManager().install(),
            options=options
        )
        driver.set_page_load_timeout(settings.web_scraping.selenium_timeout)
        return driver
    
    def search_google(self, query: str, num_results: int = 10) -> List[Dict]:
        """Search Google for relevant content"""
        try:
            driver = self.get_selenium_driver()
            search_url = f"https://www.google.com/search?q={query}&num={num_results}"
            driver.get(search_url)
            
            # Wait for results to load
            WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "div.g"))
            )
            
            results = []
            result_elements = driver.find_elements(By.CSS_SELECTOR, "div.g")
            
            for element in result_elements[:num_results]:
                try:
                    title_element = element.find_element(By.CSS_SELECTOR, "h3")
                    link_element = element.find_element(By.CSS_SELECTOR, "a")
                    
                    title = title_element.text
                    url = link_element.get_attribute("href")
                    
                    # Get snippet if available
                    snippet = ""
                    try:
                        snippet_element = element.find_element(By.CSS_SELECTOR, "div.VwiC3b")
                        snippet = snippet_element.text
                    except:
                        pass
                    
                    results.append({
                        'title': title,
                        'url': url,
                        'snippet': snippet
                    })
                except Exception as e:
                    self.logger.warning(f"Error parsing search result: {e}")
                    continue
            
            driver.quit()
            return results
            
        except Exception as e:
            self.logger.error(f"Error searching Google: {e}")
            return []
    
    def scrape_article(self, url: str) -> Optional[WebContent]:
        """Scrape article content from a URL"""
        try:
            article = Article(url)
            article.download()
            article.parse()
            article.nlp()
            
            content = WebContent(
                title=article.title,
                content=article.text,
                url=url,
                source=urlparse(url).netloc,
                publish_date=article.publish_date.isoformat() if article.publish_date else None,
                summary=article.summary,
                keywords=article.keywords,
                relevance_score=self._calculate_relevance_score(article.text, settings.content.topic)
            )
            
            return content
            
        except Exception as e:
            self.logger.error(f"Error scraping article {url}: {e}")
            return None
    
    def scrape_with_selenium(self, url: str) -> Optional[WebContent]:
        """Scrape content using Selenium for JavaScript-heavy sites"""
        try:
            driver = self.get_selenium_driver()
            driver.get(url)
            
            # Wait for content to load
            time.sleep(3)
            
            # Extract title
            title = driver.title
            
            # Extract main content
            content_selectors = [
                "article",
                "main",
                "[role='main']",
                ".content",
                ".post-content",
                ".entry-content",
                ".article-content"
            ]
            
            content = ""
            for selector in content_selectors:
                try:
                    element = driver.find_element(By.CSS_SELECTOR, selector)
                    content = element.text
                    break
                except:
                    continue
            
            # Fallback to body content
            if not content:
                content = driver.find_element(By.TAG_NAME, "body").text
            
            driver.quit()
            
            web_content = WebContent(
                title=title,
                content=content,
                url=url,
                source=urlparse(url).netloc,
                relevance_score=self._calculate_relevance_score(content, settings.content.topic)
            )
            
            return web_content
            
        except Exception as e:
            self.logger.error(f"Error scraping with Selenium {url}: {e}")
            return None
    
    def get_news_feed(self, feed_url: str) -> List[Dict]:
        """Get articles from RSS/Atom feeds"""
        try:
            feed = feedparser.parse(feed_url)
            articles = []
            
            for entry in feed.entries[:10]:  # Limit to 10 most recent
                articles.append({
                    'title': entry.title,
                    'url': entry.link,
                    'summary': getattr(entry, 'summary', ''),
                    'published': getattr(entry, 'published', ''),
                    'source': feed.feed.title if hasattr(feed.feed, 'title') else 'Unknown'
                })
            
            return articles
            
        except Exception as e:
            self.logger.error(f"Error parsing feed {feed_url}: {e}")
            return []
    
    def _calculate_relevance_score(self, content: str, topic: str) -> float:
        """Calculate relevance score based on keyword matching"""
        if not content or not topic:
            return 0.0
        
        content_lower = content.lower()
        topic_words = topic.lower().split()
        
        # Count topic keyword occurrences
        total_score = 0
        for word in topic_words:
            count = content_lower.count(word)
            total_score += count
        
        # Normalize by content length
        content_length = len(content.split())
        relevance_score = (total_score / content_length) * 100 if content_length > 0 else 0
        
        return min(relevance_score, 100.0)  # Cap at 100
    
    async def gather_content_async(self, topic: str, max_articles: int = 20) -> List[WebContent]:
        """Asynchronously gather content about a topic"""
        self.logger.info(f"Starting content gathering for topic: {topic}")
        
        all_content = []
        
        # Search for recent articles
        search_results = self.search_google(f"{topic} news latest", 10)
        
        # Get content from search results
        for result in search_results:
            content = self.scrape_article(result['url'])
            if content and content.relevance_score > 1.0:  # Filter by relevance
                all_content.append(content)
        
        # Get content from news feeds
        for feed_url in self.news_sources:
            if topic.lower() in ["technology", "tech", "ai", "artificial intelligence"]:
                articles = self.get_news_feed(feed_url)
                for article in articles:
                    if any(keyword in article['title'].lower() for keyword in topic.lower().split()):
                        content = self.scrape_article(article['url'])
                        if content and content.relevance_score > 1.0:
                            all_content.append(content)
        
        # Sort by relevance and return top articles
        all_content.sort(key=lambda x: x.relevance_score, reverse=True)
        
        self.logger.info(f"Gathered {len(all_content)} relevant articles")
        return all_content[:max_articles]
    
    def gather_content(self, topic: str, max_articles: int = 20) -> List[WebContent]:
        """Synchronous wrapper for content gathering"""
        return asyncio.run(self.gather_content_async(topic, max_articles))
    
    def get_trending_topics(self) -> List[str]:
        """Get trending topics related to the main topic"""
        try:
            driver = self.get_selenium_driver()
            
            # Google Trends
            trends_url = f"https://trends.google.com/trends/explore?q={settings.content.topic}"
            driver.get(trends_url)
            time.sleep(5)
            
            # Extract related topics (this is a simplified example)
            trending_topics = []
            
            # You would need to implement proper Google Trends scraping here
            # For now, return some default trending topics
            default_topics = [
                f"{settings.content.topic} trends",
                f"{settings.content.topic} news",
                f"{settings.content.topic} innovations",
                f"{settings.content.topic} applications",
                f"{settings.content.topic} future"
            ]
            
            driver.quit()
            return default_topics
            
        except Exception as e:
            self.logger.error(f"Error getting trending topics: {e}")
            return [f"{settings.content.topic} latest"]