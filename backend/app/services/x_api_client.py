"""X/Twitter API v2 client with rate limiting and error handling."""
import time
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

import tweepy
from loguru import logger
from tenacity import (
    retry,
    retry_if_exception_type,
    stop_after_attempt,
    wait_exponential,
)

from app.config import settings


class RateLimitError(Exception):
    """Raised when rate limit is exceeded."""

    pass


class XAPIClient:
    """
    Twitter/X API v2 client with automatic rate limiting and retry logic.

    Features:
    - Automatic rate limit handling (respects X-Rate-Limit headers)
    - Exponential backoff on transient errors
    - Incremental sync (fetch only new posts since last collection)
    - Pagination support for large timelines
    """

    def __init__(
        self,
        bearer_token: Optional[str] = None,
        api_key: Optional[str] = None,
        api_secret: Optional[str] = None,
        access_token: Optional[str] = None,
        access_secret: Optional[str] = None,
    ):
        """
        Initialize X API client.

        Args:
            bearer_token: OAuth 2.0 Bearer Token (preferred)
            api_key: Consumer API key (alternative auth)
            api_secret: Consumer API secret
            access_token: Access token
            access_secret: Access token secret
        """
        self.bearer_token = bearer_token or settings.x_api_bearer_token
        self.api_key = api_key or settings.x_api_key
        self.api_secret = api_secret or settings.x_api_secret
        self.access_token = access_token or settings.x_api_access_token
        self.access_secret = access_secret or settings.x_api_access_secret

        # Initialize Tweepy client
        self.client = self._create_client()

        # Rate limit tracking
        self.rate_limit_remaining: Optional[int] = None
        self.rate_limit_reset: Optional[datetime] = None

    def _create_client(self) -> tweepy.Client:
        """Create Tweepy client with configured credentials."""
        if not self.bearer_token and not (self.api_key and self.api_secret):
            raise ValueError(
                "Either bearer_token or (api_key + api_secret) must be provided"
            )

        # Prefer OAuth 2.0 Bearer Token
        if self.bearer_token:
            return tweepy.Client(
                bearer_token=self.bearer_token,
                wait_on_rate_limit=True,
            )

        # Fall back to OAuth 1.0a
        return tweepy.Client(
            consumer_key=self.api_key,
            consumer_secret=self.api_secret,
            access_token=self.access_token,
            access_token_secret=self.access_secret,
            wait_on_rate_limit=True,
        )

    def _check_rate_limit(self) -> None:
        """Check if we're rate limited and wait if necessary."""
        if self.rate_limit_remaining is not None and self.rate_limit_remaining == 0:
            if self.rate_limit_reset:
                wait_seconds = (self.rate_limit_reset - datetime.utcnow()).total_seconds()
                if wait_seconds > 0:
                    logger.warning(
                        f"Rate limit exceeded. Waiting {wait_seconds:.0f} seconds..."
                    )
                    time.sleep(wait_seconds + 1)
                    self.rate_limit_remaining = None

    def _update_rate_limit(self, response_meta: Optional[Dict[str, Any]]) -> None:
        """Update rate limit info from response headers."""
        # Tweepy handles rate limits automatically with wait_on_rate_limit=True
        # This is for logging/monitoring purposes
        pass

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=4, max=60),
        retry=retry_if_exception_type((tweepy.TooManyRequests, tweepy.TwitterServerError)),
    )
    def get_user_by_username(self, username: str) -> Optional[Dict[str, Any]]:
        """
        Get user information by username.

        Args:
            username: Twitter username (without @)

        Returns:
            User data dict or None if not found
        """
        try:
            logger.info(f"Fetching user info for @{username}")
            response = self.client.get_user(
                username=username,
                user_fields=["id", "name", "username", "created_at", "description", "public_metrics"],
            )

            if response.data:
                user = response.data
                return {
                    "id": user.id,
                    "username": user.username,
                    "name": user.name,
                    "created_at": user.created_at,
                    "description": user.description,
                    "public_metrics": user.data.get("public_metrics", {}),
                }

            return None

        except tweepy.NotFound:
            logger.error(f"User @{username} not found")
            return None
        except tweepy.Unauthorized:
            logger.error("Authentication failed. Check your API credentials.")
            raise
        except Exception as e:
            logger.error(f"Error fetching user @{username}: {e}")
            raise

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=4, max=60),
        retry=retry_if_exception_type((tweepy.TooManyRequests, tweepy.TwitterServerError)),
    )
    def get_user_tweets(
        self,
        username: str,
        max_results: int = 100,
        since_id: Optional[str] = None,
        until_id: Optional[str] = None,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
    ) -> List[Dict[str, Any]]:
        """
        Get tweets from a user's timeline.

        Args:
            username: Twitter username (without @)
            max_results: Maximum number of tweets to fetch (10-100 per request)
            since_id: Fetch tweets after this ID (for incremental sync)
            until_id: Fetch tweets before this ID
            start_time: Fetch tweets after this timestamp
            end_time: Fetch tweets before this timestamp

        Returns:
            List of tweet dicts
        """
        self._check_rate_limit()

        try:
            # Get user ID first
            user = self.get_user_by_username(username)
            if not user:
                logger.error(f"Cannot fetch tweets: user @{username} not found")
                return []

            user_id = user["id"]
            logger.info(
                f"Fetching tweets for @{username} (user_id={user_id}, "
                f"max_results={max_results}, since_id={since_id})"
            )

            # Fetch tweets with pagination
            tweets = []
            pagination_token = None

            # API v2 limits: max 100 per request, 3200 most recent tweets
            max_per_request = min(max_results, 100)
            remaining = max_results

            while remaining > 0:
                fetch_count = min(remaining, max_per_request)

                response = self.client.get_users_tweets(
                    id=user_id,
                    max_results=fetch_count,
                    tweet_fields=[
                        "id",
                        "text",
                        "created_at",
                        "author_id",
                        "conversation_id",
                        "public_metrics",
                        "referenced_tweets",
                        "attachments",
                        "lang",
                    ],
                    expansions=["attachments.media_keys", "referenced_tweets.id"],
                    media_fields=["url", "preview_image_url", "type", "duration_ms"],
                    since_id=since_id,
                    until_id=until_id,
                    start_time=start_time,
                    end_time=end_time,
                    pagination_token=pagination_token,
                )

                if not response.data:
                    logger.info("No more tweets found")
                    break

                # Process tweets and attach media data
                media_map = {}
                if response.includes and "media" in response.includes:
                    for media in response.includes["media"]:
                        media_map[media.media_key] = {
                            "url": getattr(media, "url", None),
                            "preview_image_url": getattr(media, "preview_image_url", None),
                            "type": media.type,
                        }

                for tweet in response.data:
                    tweet_dict = tweet.data
                    tweet_dict["author_id"] = user_id

                    # Attach media data
                    if hasattr(tweet, "attachments") and tweet.attachments:
                        media_keys = tweet.attachments.get("media_keys", [])
                        tweet_dict["media"] = [
                            media_map.get(key) for key in media_keys if key in media_map
                        ]

                    tweets.append(tweet_dict)

                remaining -= len(response.data)

                # Check for more pages
                if hasattr(response, "meta") and "next_token" in response.meta:
                    pagination_token = response.meta["next_token"]
                else:
                    break

            logger.info(f"Fetched {len(tweets)} tweets for @{username}")
            return tweets

        except tweepy.TooManyRequests as e:
            logger.error(f"Rate limit exceeded: {e}")
            raise RateLimitError("Rate limit exceeded") from e
        except tweepy.Unauthorized:
            logger.error("Authentication failed. Check your API credentials.")
            raise
        except Exception as e:
            logger.error(f"Error fetching tweets for @{username}: {e}")
            raise

    def get_recent_tweets(
        self,
        username: str,
        max_count: int = 100,
        since_id: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """
        Convenience method to get recent tweets.

        Args:
            username: Twitter username
            max_count: Maximum number of tweets to fetch
            since_id: Fetch tweets after this ID

        Returns:
            List of tweet dicts
        """
        return self.get_user_tweets(
            username=username,
            max_results=max_count,
            since_id=since_id,
        )

    def get_tweets_since(
        self,
        username: str,
        since_date: datetime,
        max_count: int = 200,
    ) -> List[Dict[str, Any]]:
        """
        Get tweets since a specific date.

        Args:
            username: Twitter username
            since_date: Fetch tweets after this date
            max_count: Maximum number of tweets to fetch

        Returns:
            List of tweet dicts
        """
        return self.get_user_tweets(
            username=username,
            max_results=max_count,
            start_time=since_date,
        )

    def test_connection(self) -> bool:
        """
        Test API connection and credentials.

        Returns:
            True if connection successful, False otherwise
        """
        try:
            logger.info("Testing X API connection...")
            user = self.get_user_by_username(settings.x_target_username)
            if user:
                logger.info(f"✓ Connected to X API. Target user: @{user['username']}")
                return True
            return False
        except Exception as e:
            logger.error(f"✗ X API connection failed: {e}")
            return False


# Singleton instance
_client_instance: Optional[XAPIClient] = None


def get_api_client() -> XAPIClient:
    """Get or create X API client singleton."""
    global _client_instance
    if _client_instance is None:
        _client_instance = XAPIClient()
    return _client_instance
