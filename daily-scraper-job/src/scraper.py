"""
Enhanced scraper with delta detection capabilities.
"""

import time
import logging
import requests
from datetime import datetime, timezone
from typing import List, Dict, Any, Optional
from urllib.parse import urljoin, urlparse

try:
    from bs4 import BeautifulSoup
except ImportError:
    print("❌ BeautifulSoup not installed. Run: pip install beautifulsoup4")
    BeautifulSoup = None

from config.settings import Settings
from .delta_detector import DeltaDetector


class EnhancedScraper:
    """Enhanced scraper with delta detection and improved error handling."""
    
    def __init__(self, settings: Settings):
        self.settings = settings
        self.logger = logging.getLogger(__name__)
        self.session = requests.Session()
        
        # Set up session with headers (use a normal browser user agent)
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Accept-Encoding': 'gzip, deflate',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1'
        })
        
        # Statistics
        self.stats = {
            'total_requests': 0,
            'successful_requests': 0,
            'failed_requests': 0,
            'articles_found': 0,
            'articles_processed': 0
        }
    
    def scrape_all_articles(self) -> List[Dict[str, Any]]:
        """
        Scrape all articles from the OptiSigns support site.
        
        Returns:
            List of article dictionaries with enhanced metadata
        """
        self.logger.info("🕷️ Starting enhanced article scraping...")
        
        try:
            # Get all article URLs
            article_urls = self._discover_article_urls()
            self.stats['articles_found'] = len(article_urls)
            
            if self.settings.max_articles:
                article_urls = article_urls[:self.settings.max_articles]
                self.logger.info(f"🔢 Limited to {len(article_urls)} articles for testing")
            
            self.logger.info(f"📄 Found {len(article_urls)} articles to process")
            
            # Process each article
            articles = []
            for i, url in enumerate(article_urls, 1):
                self.logger.info(f"📖 Processing article {i}/{len(article_urls)}: {url}")
                
                try:
                    article = self._scrape_article(url)
                    if article:
                        articles.append(article)
                        self.stats['articles_processed'] += 1
                    
                    # Rate limiting
                    if i < len(article_urls):
                        time.sleep(self.settings.request_delay)
                        
                except Exception as e:
                    self.logger.error(f"❌ Failed to process article {url}: {e}")
                    self.stats['failed_requests'] += 1
                    continue
            
            self.logger.info(f"✅ Successfully processed {len(articles)} articles")
            self._log_scraping_stats()
            
            return articles
            
        except Exception as e:
            self.logger.error(f"❌ Scraping failed: {e}")
            raise
    
    def _discover_article_urls(self) -> List[str]:
        """Discover all article URLs from the support site."""
        self.logger.info("🔍 Discovering article URLs...")
        
        # Start with the main support page
        base_url = self.settings.base_url
        sitemap_urls = [
            f"{base_url}/hc/en-us/articles",
            f"{base_url}/hc/en-us/sections"
        ]
        
        article_urls = set()
        
        for sitemap_url in sitemap_urls:
            try:
                self.logger.debug(f"🔍 Checking {sitemap_url}")
                response = self._make_request(sitemap_url)
                
                if response:
                    soup = BeautifulSoup(response.content, 'html.parser')
                    
                    # Find article links
                    for link in soup.find_all('a', href=True):
                        href = link['href']
                        
                        # Check if it's an article URL
                        if '/articles/' in href:
                            full_url = urljoin(base_url, href)
                            article_urls.add(full_url)
                
            except Exception as e:
                self.logger.warning(f"⚠️ Failed to process sitemap {sitemap_url}: {e}")
                continue
        
        # Also try to find articles through category pages
        try:
            self._discover_from_categories(base_url, article_urls)
        except Exception as e:
            self.logger.warning(f"⚠️ Failed to discover from categories: {e}")
        
        return sorted(list(article_urls))
    
    def _discover_from_categories(self, base_url: str, article_urls: set):
        """Discover articles from category and section pages."""
        categories_url = f"{base_url}/hc/en-us/categories"
        
        response = self._make_request(categories_url)
        if not response:
            return
        
        soup = BeautifulSoup(response.content, 'html.parser')
        
        # Find category and section links
        for link in soup.find_all('a', href=True):
            href = link['href']
            
            if '/sections/' in href or '/categories/' in href:
                section_url = urljoin(base_url, href)
                
                try:
                    section_response = self._make_request(section_url)
                    if section_response:
                        section_soup = BeautifulSoup(section_response.content, 'html.parser')
                        
                        # Find article links in this section
                        for article_link in section_soup.find_all('a', href=True):
                            article_href = article_link['href']
                            if '/articles/' in article_href:
                                full_url = urljoin(base_url, article_href)
                                article_urls.add(full_url)
                
                except Exception as e:
                    self.logger.debug(f"Failed to process section {section_url}: {e}")
                    continue
                
                # Rate limiting for section discovery
                time.sleep(0.5)
    
    def _scrape_article(self, url: str) -> Optional[Dict[str, Any]]:
        """
        Scrape a single article with enhanced metadata.
        
        Args:
            url: Article URL to scrape
            
        Returns:
            Article dictionary with metadata, None if failed
        """
        response = self._make_request(url)
        if not response:
            return None
        
        try:
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Extract article content
            title = self._extract_title(soup)
            content = self._extract_content(soup)
            
            if not title or not content:
                self.logger.warning(f"Missing title or content for {url}")
                return None
            
            # Generate article ID from URL
            article_id = self._generate_article_id(url)
            
            # Compute content hash for delta detection
            content_hash = DeltaDetector.compute_content_hash(content)
            
            # Extract metadata
            metadata = self._extract_metadata(soup, response)
            
            article = {
                'id': article_id,
                'title': title.strip(),
                'content': content.strip(),
                'content_hash': content_hash,
                'url': url,
                'scraped_at': datetime.now(timezone.utc).isoformat(),
                'last_modified': metadata.get('last_modified'),
                'category': metadata.get('category', 'Unknown'),
                'section': metadata.get('section', 'Unknown'),
                'tags': metadata.get('tags', []),
                'word_count': len(content.split()),
                'char_count': len(content)
            }
            
            self.logger.debug(f"✅ Scraped article: {title[:50]}...")
            return article
            
        except Exception as e:
            self.logger.error(f"❌ Failed to parse article {url}: {e}")
            return None
    
    def _make_request(self, url: str) -> Optional[requests.Response]:
        """Make HTTP request with retry logic."""
        for attempt in range(self.settings.max_retries + 1):
            try:
                self.stats['total_requests'] += 1
                
                response = self.session.get(url, timeout=30)
                response.raise_for_status()
                
                self.stats['successful_requests'] += 1
                return response
                
            except requests.RequestException as e:
                if attempt < self.settings.max_retries:
                    wait_time = (attempt + 1) * 2
                    self.logger.warning(f"Request failed (attempt {attempt + 1}), retrying in {wait_time}s: {e}")
                    time.sleep(wait_time)
                else:
                    self.logger.error(f"Request failed after {self.settings.max_retries + 1} attempts: {e}")
                    self.stats['failed_requests'] += 1
                    return None
    
    def _extract_title(self, soup: BeautifulSoup) -> Optional[str]:
        """Extract article title from HTML."""
        # Try multiple selectors for title
        selectors = [
            'h1.article-title',
            'h1[data-testid="article-title"]',
            '.article-header h1',
            'h1',
            'title'
        ]
        
        for selector in selectors:
            element = soup.select_one(selector)
            if element:
                return element.get_text().strip()
        
        return None
    
    def _extract_content(self, soup: BeautifulSoup) -> Optional[str]:
        """Extract article content from HTML."""
        # Try multiple selectors for content
        selectors = [
            '.article-body',
            '[data-testid="article-body"]',
            '.article-content',
            '.content',
            'main'
        ]
        
        for selector in selectors:
            element = soup.select_one(selector)
            if element:
                # Clean up the content
                return self._clean_content(element.get_text())
        
        return None
    
    def _extract_metadata(self, soup: BeautifulSoup, response: requests.Response) -> Dict[str, Any]:
        """Extract metadata from article page and HTTP response."""
        metadata = {}
        
        # Extract Last-Modified from HTTP headers
        if 'Last-Modified' in response.headers:
            metadata['last_modified'] = response.headers['Last-Modified']
        
        # Extract category and section from breadcrumbs or navigation
        breadcrumbs = soup.select('.breadcrumbs a, .nav-breadcrumbs a')
        if breadcrumbs:
            if len(breadcrumbs) >= 2:
                metadata['category'] = breadcrumbs[-2].get_text().strip()
            if len(breadcrumbs) >= 1:
                metadata['section'] = breadcrumbs[-1].get_text().strip()
        
        # Extract tags
        tags = []
        tag_elements = soup.select('.article-tags a, .tags a')
        for tag_elem in tag_elements:
            tags.append(tag_elem.get_text().strip())
        metadata['tags'] = tags
        
        return metadata
    
    def _clean_content(self, content: str) -> str:
        """Clean and normalize article content."""
        # Remove extra whitespace
        lines = [line.strip() for line in content.split('\n')]
        lines = [line for line in lines if line]
        
        return '\n'.join(lines)
    
    def _generate_article_id(self, url: str) -> str:
        """Generate a consistent article ID from URL."""
        parsed = urlparse(url)
        path_parts = parsed.path.split('/')
        
        # Look for article ID in URL
        for part in reversed(path_parts):
            if part.isdigit():
                return f"article_{part}"
            elif part and part != 'articles':
                # Use the last meaningful path component
                return f"article_{part.replace('-', '_')}"
        
        # Fallback to hash of URL
        import hashlib
        url_hash = hashlib.md5(url.encode()).hexdigest()[:8]
        return f"article_{url_hash}"
    
    def _log_scraping_stats(self):
        """Log scraping statistics."""
        self.logger.info("📊 Scraping Statistics:")
        self.logger.info(f"  Total requests: {self.stats['total_requests']}")
        self.logger.info(f"  Successful requests: {self.stats['successful_requests']}")
        self.logger.info(f"  Failed requests: {self.stats['failed_requests']}")
        self.logger.info(f"  Articles found: {self.stats['articles_found']}")
        self.logger.info(f"  Articles processed: {self.stats['articles_processed']}")
        
        if self.stats['total_requests'] > 0:
            success_rate = (self.stats['successful_requests'] / self.stats['total_requests']) * 100
            self.logger.info(f"  Success rate: {success_rate:.1f}%")
    
    def get_stats(self) -> Dict[str, int]:
        """Get scraping statistics."""
        return self.stats.copy()
