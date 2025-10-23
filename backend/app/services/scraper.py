"""Web scraper fallback for collecting X/Twitter posts."""
import asyncio
import re
import time
from datetime import datetime
from typing import Any, Dict, List, Optional
from urllib.parse import urljoin, urlparse
from urllib.robotparser import RobotFileParser

import httpx
from bs4 import BeautifulSoup
from loguru import logger
from playwright.async_api import Browser, Page, Playwright, async_playwright
from tenacity import (
    retry,
    retry_if_exception_type,
    stop_after_attempt,
    wait_exponential,
)

from app.config import settings


class ScraperError(Exception):
    """Base exception for scraper errors."""

    pass


class RobotsTxtForbidden(ScraperError):
    """Raised when robots.txt disallows scraping."""

    pass


class XScraper:
    """
    Ethical web scraper for X/Twitter with robots.txt compliance.

    WARNING: Web scraping should only be used when official API access is unavailable.
    This scraper:
    - Checks robots.txt before scraping
    - Respects rate limits (configurable)
    - Uses exponential backoff on errors
    - Implements polite delays between requests
    - Logs all scraping activity
    """

    BASE_URL = "https://twitter.com"
    RATE_LIMIT_DELAY = 1.0 / settings.scraper_rate_limit  # Seconds between requests

    def __init__(self):
        """Initialize scraper with configuration."""
        self.last_request_time = 0.0
        self.robots_parser: Optional[RobotFileParser] = None
        self.playwright: Optional[Playwright] = None
        self.browser: Optional[Browser] = None
        self.user_agent = (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
            "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        )

    async def __aenter__(self):
        """Async context manager entry."""
        await self.start()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        await self.close()

    async def start(self) -> None:
        """Initialize browser and check robots.txt."""
        logger.info("Starting X scraper...")

        # Check robots.txt
        await self._check_robots_txt()

        # Initialize Playwright
        if settings.playwright_headless:
            self.playwright = await async_playwright().start()
            self.browser = await self.playwright.chromium.launch(
                headless=True,
                args=["--no-sandbox", "--disable-blink-features=AutomationControlled"],
            )
            logger.info("Playwright browser started")

    async def close(self) -> None:
        """Close browser and cleanup."""
        if self.browser:
            await self.browser.close()
        if self.playwright:
            await self.playwright.stop()
        logger.info("X scraper closed")

    async def _check_robots_txt(self) -> None:
        """
        Check robots.txt to see if scraping is allowed.

        Raises:
            RobotsTxtForbidden: If robots.txt disallows scraping
        """
        logger.info("Checking robots.txt...")

        robots_url = urljoin(self.BASE_URL, "/robots.txt")

        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(robots_url, timeout=10.0)
                response.raise_for_status()

            self.robots_parser = RobotFileParser()
            self.robots_parser.parse(response.text.splitlines())

            # Check if user-agent "*" can fetch user pages
            user_page = f"{self.BASE_URL}/{settings.x_target_username}"
            can_fetch = self.robots_parser.can_fetch("*", user_page)

            if not can_fetch:
                logger.error(
                    f"❌ robots.txt disallows scraping {user_page}. "
                    "Please use the official API instead."
                )
                raise RobotsTxtForbidden(
                    "Scraping is disallowed by robots.txt. Use API credentials."
                )

            logger.info(f"✓ robots.txt allows scraping {user_page}")

        except httpx.HTTPError as e:
            logger.warning(
                f"Could not fetch robots.txt ({e}). Proceeding with caution..."
            )

    async def _rate_limit_delay(self) -> None:
        """Enforce rate limiting between requests."""
        elapsed = time.time() - self.last_request_time
        if elapsed < self.RATE_LIMIT_DELAY:
            delay = self.RATE_LIMIT_DELAY - elapsed
            logger.debug(f"Rate limiting: waiting {delay:.2f}s")
            await asyncio.sleep(delay)
        self.last_request_time = time.time()

    @retry(
        stop=stop_after_attempt(settings.scraper_max_retries),
        wait=wait_exponential(
            multiplier=settings.scraper_backoff_factor,
            min=2,
            max=30,
        ),
        retry=retry_if_exception_type((httpx.HTTPError, asyncio.TimeoutError)),
    )
    async def _fetch_page_with_browser(self, url: str) -> str:
        """
        Fetch page content using headless browser (Playwright).

        Args:
            url: URL to fetch

        Returns:
            Page HTML content
        """
        if not self.browser:
            raise ScraperError("Browser not initialized. Call start() first.")

        await self._rate_limit_delay()

        logger.info(f"Fetching {url} with Playwright...")

        page: Page = await self.browser.new_page(user_agent=self.user_agent)

        try:
            # Navigate to page with timeout
            await page.goto(url, wait_until="networkidle", timeout=settings.scraper_timeout * 1000)

            # Wait for tweets to load
            await page.wait_for_selector('article[data-testid="tweet"]', timeout=10000)

            # Scroll to load more tweets
            for _ in range(3):
                await page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
                await asyncio.sleep(1)

            # Get page content
            content = await page.content()
            logger.debug(f"Fetched {len(content)} bytes from {url}")

            return content

        except Exception as e:
            logger.error(f"Error fetching {url}: {e}")
            raise

        finally:
            await page.close()

    def _parse_tweet_from_html(self, article_html: str) -> Optional[Dict[str, Any]]:
        """
        Parse tweet data from article HTML element.

        Args:
            article_html: HTML string of tweet article element

        Returns:
            Dict with tweet data or None if parsing fails
        """
        try:
            soup = BeautifulSoup(article_html, "lxml")

            # Extract tweet ID from article element or links
            tweet_id = None
            time_element = soup.find("time")
            if time_element and time_element.parent:
                link = time_element.parent.get("href", "")
                match = re.search(r"/status/(\d+)", link)
                if match:
                    tweet_id = match.group(1)

            if not tweet_id:
                logger.warning("Could not extract tweet ID")
                return None

            # Extract text content
            text_element = soup.find("div", {"data-testid": "tweetText"})
            text = text_element.get_text(strip=True) if text_element else ""

            # Extract timestamp
            created_at = None
            if time_element and time_element.get("datetime"):
                created_at = datetime.fromisoformat(
                    time_element["datetime"].replace("Z", "+00:00")
                )

            # Extract metrics (likes, retweets, replies)
            metrics = {"like": 0, "retweet": 0, "reply": 0}

            for metric_type in ["like", "retweet", "reply"]:
                metric_elem = soup.find("button", {"data-testid": metric_type})
                if metric_elem:
                    aria_label = metric_elem.get("aria-label", "")
                    match = re.search(r"(\d+)", aria_label.replace(",", ""))
                    if match:
                        metrics[metric_type] = int(match.group(1))

            # Extract media URLs
            media_urls = []
            media_elements = soup.find_all("img", {"alt": re.compile(r"Image|Photo")})
            for img in media_elements:
                src = img.get("src", "")
                if "pbs.twimg.com/media" in src:
                    media_urls.append(src)

            # Check if reply
            is_reply = bool(soup.find("div", {"data-testid": "reply"}))

            return {
                "post_id": tweet_id,
                "text": text,
                "created_at": created_at.isoformat() if created_at else None,
                "author_username": settings.x_target_username,
                "like_count": metrics["like"],
                "retweet_count": metrics["retweet"],
                "reply_count": metrics["reply"],
                "media_urls": media_urls,
                "is_reply": is_reply,
                "is_retweet": "RT @" in text,
                "is_quote": False,  # Hard to detect from HTML
                "replied_to_id": None,
                "retweeted_id": None,
                "quoted_id": None,
            }

        except Exception as e:
            logger.error(f"Error parsing tweet HTML: {e}")
            return None

    async def scrape_user_timeline(
        self,
        username: str,
        max_posts: int = 100,
    ) -> List[Dict[str, Any]]:
        """
        Scrape tweets from a user's timeline.

        Args:
            username: Twitter username (without @)
            max_posts: Maximum number of posts to scrape

        Returns:
            List of tweet dicts
        """
        user_url = f"{self.BASE_URL}/{username}"

        logger.info(f"Scraping timeline for @{username} (max {max_posts} posts)")

        try:
            # Fetch page content
            html_content = await self._fetch_page_with_browser(user_url)

            # Parse HTML
            soup = BeautifulSoup(html_content, "lxml")

            # Find all tweet articles
            articles = soup.find_all("article", {"data-testid": "tweet"}, limit=max_posts)

            logger.info(f"Found {len(articles)} tweet articles")

            # Parse each article
            tweets = []
            for article in articles:
                tweet_data = self._parse_tweet_from_html(str(article))
                if tweet_data:
                    tweets.append(tweet_data)

            logger.info(f"Successfully parsed {len(tweets)} tweets")
            return tweets

        except RobotsTxtForbidden:
            raise
        except Exception as e:
            logger.error(f"Error scraping @{username}: {e}")
            raise ScraperError(f"Scraping failed: {e}") from e

    async def test_scraping(self) -> bool:
        """
        Test scraper by fetching one page.

        Returns:
            True if scraping works, False otherwise
        """
        try:
            logger.info("Testing scraper...")
            tweets = await self.scrape_user_timeline(
                settings.x_target_username,
                max_posts=5,
            )
            logger.info(f"✓ Scraper test successful. Found {len(tweets)} tweets.")
            return len(tweets) > 0
        except RobotsTxtForbidden:
            logger.error("✗ Scraping forbidden by robots.txt")
            return False
        except Exception as e:
            logger.error(f"✗ Scraper test failed: {e}")
            return False


async def get_scraper() -> XScraper:
    """Get configured scraper instance."""
    scraper = XScraper()
    await scraper.start()
    return scraper
