"""
Web scraper for gathering information from various sources.
"""

import requests
import feedparser
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
from newspaper import Article
from typing import List, Dict, Optional
import time
import random
from urllib.parse import urljoin, urlparse
from config import config
from logger import logger

class WebScraper:
    """Web scraper for gathering information from various sources."""
    
    def __init__(self):
        self.logger = logger.get_logger("web_scraper")
        self.user_agent = config.get("web_scraping.user_agent")
        self.timeout = config.get("web_scraping.timeout", 30)
        self.max_pages = config.get("web_scraping.max_pages", 10)
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': self.user_agent
        })
        
        # News sources and tech blogs
        self.news_sources = [
            "https://techcrunch.com/feed/",
            "https://www.wired.com/feed/",
            "https://www.theverge.com/rss/index.xml",
            "https://arstechnica.com/feed/",
            "https://feeds.feedburner.com/venturebeat/SZYF",
            "https://www.engadget.com/rss.xml",
            "https://feeds.feedburner.com/TechCrunch/",
            "https://rss.cnn.com/rss/edition.rss",
            "https://feeds.bbci.co.uk/news/technology/rss.xml"
        ]
        
        # Search engines for topic-specific content
        self.search_engines = {
            "google": "https://www.google.com/search?q={query}&tbm=nws",
            "bing": "https://www.bing.com/search?q={query}&qft=interval%3d\"7\""
        }
    
    def setup_selenium_driver(self) -> webdriver.Chrome:
        """Set up Selenium Chrome driver."""
        try:
            chrome_options = Options()
            chrome_options.add_argument("--headless")
            chrome_options.add_argument("--no-sandbox")
            chrome_options.add_argument("--disable-dev-shm-usage")
            chrome_options.add_argument("--disable-gpu")
            chrome_options.add_argument("--window-size=1920,1080")
            chrome_options.add_argument(f"--user-agent={self.user_agent}")
            
            driver = webdriver.Chrome(
                service=webdriver.chrome.service.Service(ChromeDriverManager().install()),
                options=chrome_options
            )
            driver.implicitly_wait(10)
            return driver
        except Exception as e:
            self.logger.error(f"Error setting up Selenium driver: {e}")
            return None
    
    def scrape_rss_feeds(self, topic: str) -> List[Dict]:
        """Scrape RSS feeds for relevant articles."""
        articles = []
        
        for feed_url in self.news_sources:
            try:
                self.logger.info(f"Scraping RSS feed: {feed_url}")
                feed = feedparser.parse(feed_url)
                
                for entry in feed.entries[:5]:  # Limit to 5 articles per feed
                    if self.is_relevant_to_topic(entry.title + " " + entry.get('summary', ''), topic):
                        article = {
                            'title': entry.title,
                            'url': entry.link,
                            'summary': entry.get('summary', ''),
                            'published': entry.get('published', ''),
                            'source': feed_url,
                            'type': 'rss'
                        }
                        articles.append(article)
                        
                time.sleep(random.uniform(1, 3))  # Be respectful to servers
                
            except Exception as e:
                self.logger.error(f"Error scraping RSS feed {feed_url}: {e}")
                continue
        
        return articles
    
    def scrape_news_article(self, url: str) -> Optional[Dict]:
        """Scrape full content from a news article."""
        try:
            article = Article(url)
            article.download()
            article.parse()
            
            return {
                'title': article.title,
                'text': article.text,
                'authors': article.authors,
                'publish_date': article.publish_date,
                'url': url,
                'summary': article.summary if hasattr(article, 'summary') else '',
                'keywords': article.keywords if hasattr(article, 'keywords') else []
            }
        except Exception as e:
            self.logger.error(f"Error scraping article {url}: {e}")
            return None
    
    def search_google_news(self, query: str) -> List[Dict]:
        """Search Google News for specific topics."""
        articles = []
        
        try:
            driver = self.setup_selenium_driver()
            if not driver:
                return articles
            
            search_url = self.search_engines['google'].format(query=query)
            driver.get(search_url)
            
            # Wait for results to load
            WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "div[data-sokoban-container]"))
            )
            
            # Find news articles
            news_elements = driver.find_elements(By.CSS_SELECTOR, "div[data-sokoban-container] a")
            
            for element in news_elements[:10]:  # Limit to 10 results
                try:
                    link = element.get_attribute('href')
                    title = element.text
                    
                    if link and title and 'http' in link:
                        articles.append({
                            'title': title,
                            'url': link,
                            'source': 'google_news',
                            'type': 'search'
                        })
                except Exception as e:
                    continue
            
            driver.quit()
            
        except Exception as e:
            self.logger.error(f"Error searching Google News: {e}")
            if 'driver' in locals():
                driver.quit()
        
        return articles
    
    def scrape_reddit(self, topic: str) -> List[Dict]:
        """Scrape Reddit for discussions about the topic."""
        articles = []
        
        try:
            # Use Reddit's JSON API
            subreddits = ['technology', 'MachineLearning', 'artificial', 'programming', 'science']
            
            for subreddit in subreddits:
                url = f"https://www.reddit.com/r/{subreddit}/hot.json?limit=10"
                
                response = self.session.get(url)
                if response.status_code == 200:
                    data = response.json()
                    
                    for post in data['data']['children']:
                        post_data = post['data']
                        
                        if self.is_relevant_to_topic(post_data['title'] + " " + post_data.get('selftext', ''), topic):
                            articles.append({
                                'title': post_data['title'],
                                'url': post_data['url'],
                                'text': post_data.get('selftext', ''),
                                'score': post_data['score'],
                                'comments': post_data['num_comments'],
                                'subreddit': subreddit,
                                'source': 'reddit',
                                'type': 'discussion'
                            })
                
                time.sleep(random.uniform(1, 2))
                
        except Exception as e:
            self.logger.error(f"Error scraping Reddit: {e}")
        
        return articles
    
    def scrape_github_trending(self, topic: str) -> List[Dict]:
        """Scrape GitHub trending repositories related to the topic."""
        articles = []
        
        try:
            driver = self.setup_selenium_driver()
            if not driver:
                return articles
            
            # Search GitHub trending
            search_query = topic.replace(' ', '+')
            url = f"https://github.com/trending?q={search_query}"
            
            driver.get(url)
            
            # Wait for repositories to load
            WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "article.Box-row"))
            )
            
            repos = driver.find_elements(By.CSS_SELECTOR, "article.Box-row")
            
            for repo in repos[:5]:  # Limit to 5 repositories
                try:
                    title_element = repo.find_element(By.CSS_SELECTOR, "h2 a")
                    title = title_element.text
                    link = title_element.get_attribute('href')
                    
                    description_element = repo.find_element(By.CSS_SELECTOR, "p")
                    description = description_element.text if description_element else ""
                    
                    articles.append({
                        'title': title,
                        'url': link,
                        'description': description,
                        'source': 'github',
                        'type': 'repository'
                    })
                except Exception as e:
                    continue
            
            driver.quit()
            
        except Exception as e:
            self.logger.error(f"Error scraping GitHub trending: {e}")
            if 'driver' in locals():
                driver.quit()
        
        return articles
    
    def is_relevant_to_topic(self, text: str, topic: str) -> bool:
        """Check if text is relevant to the given topic."""
        if not text:
            return False
        
        text_lower = text.lower()
        topic_lower = topic.lower()
        
        # Check for direct topic match
        if topic_lower in text_lower:
            return True
        
        # Check for related keywords based on topic
        keyword_mapping = {
            'artificial intelligence': ['ai', 'machine learning', 'deep learning', 'neural', 'llm', 'gpt', 'chatbot'],
            'machine learning': ['ml', 'ai', 'neural', 'algorithm', 'model', 'training', 'data science'],
            'technology trends': ['tech', 'innovation', 'startup', 'digital', 'cloud', 'mobile', 'web'],
            'blockchain': ['crypto', 'bitcoin', 'ethereum', 'defi', 'nft', 'web3'],
            'cybersecurity': ['security', 'hacking', 'breach', 'malware', 'encryption', 'vulnerability']
        }
        
        related_keywords = keyword_mapping.get(topic_lower, [])
        
        for keyword in related_keywords:
            if keyword in text_lower:
                return True
        
        return False
    
    def gather_information(self, topic: str, max_sources: int = 5) -> List[Dict]:
        """Gather information from multiple sources about the topic."""
        self.logger.info(f"Starting information gathering for topic: {topic}")
        
        all_articles = []
        
        # Scrape RSS feeds
        rss_articles = self.scrape_rss_feeds(topic)
        all_articles.extend(rss_articles)
        self.logger.info(f"Found {len(rss_articles)} articles from RSS feeds")
        
        # Search Google News
        google_articles = self.search_google_news(topic)
        all_articles.extend(google_articles)
        self.logger.info(f"Found {len(google_articles)} articles from Google News")
        
        # Scrape Reddit
        reddit_articles = self.scrape_reddit(topic)
        all_articles.extend(reddit_articles)
        self.logger.info(f"Found {len(reddit_articles)} articles from Reddit")
        
        # Scrape GitHub trending
        github_articles = self.scrape_github_trending(topic)
        all_articles.extend(github_articles)
        self.logger.info(f"Found {len(github_articles)} articles from GitHub")
        
        # Remove duplicates and limit results
        unique_articles = []
        seen_urls = set()
        
        for article in all_articles:
            if article.get('url') not in seen_urls:
                seen_urls.add(article.get('url'))
                unique_articles.append(article)
        
        # Sort by relevance and limit
        unique_articles = unique_articles[:max_sources]
        
        # Get full content for the most relevant articles
        for article in unique_articles:
            if article.get('type') in ['rss', 'search'] and article.get('url'):
                full_content = self.scrape_news_article(article['url'])
                if full_content:
                    article.update(full_content)
        
        self.logger.info(f"Gathered {len(unique_articles)} unique articles")
        return unique_articles