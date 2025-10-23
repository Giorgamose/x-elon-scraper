"""Unit tests for X API client."""
import pytest
from unittest.mock import Mock, patch

from app.services.x_api_client import XAPIClient, RateLimitError


class TestXAPIClient:
    """Tests for X API client."""

    @patch("app.services.x_api_client.tweepy.Client")
    def test_client_initialization(self, mock_tweepy):
        """Test client initialization with bearer token."""
        client = XAPIClient(bearer_token="test_bearer_token")

        assert client.bearer_token == "test_bearer_token"
        mock_tweepy.assert_called_once()

    @patch("app.services.x_api_client.tweepy.Client")
    def test_client_requires_credentials(self, mock_tweepy):
        """Test that client requires credentials."""
        with pytest.raises(ValueError, match="Either bearer_token"):
            XAPIClient(
                bearer_token=None,
                api_key=None,
                api_secret=None,
            )

    @patch("app.services.x_api_client.tweepy.Client")
    def test_get_user_by_username(self, mock_tweepy):
        """Test fetching user by username."""
        # Mock response
        mock_user = Mock()
        mock_user.id = "44196397"
        mock_user.username = "elonmusk"
        mock_user.name = "Elon Musk"
        mock_user.data = {"public_metrics": {"followers_count": 1000000}}

        mock_response = Mock()
        mock_response.data = mock_user

        mock_client_instance = Mock()
        mock_client_instance.get_user.return_value = mock_response
        mock_tweepy.return_value = mock_client_instance

        client = XAPIClient(bearer_token="test_token")
        user = client.get_user_by_username("elonmusk")

        assert user is not None
        assert user["id"] == "44196397"
        assert user["username"] == "elonmusk"
        mock_client_instance.get_user.assert_called_once()

    @patch("app.services.x_api_client.tweepy.Client")
    def test_get_user_tweets(self, mock_tweepy, sample_post_data):
        """Test fetching user tweets."""
        # Mock user response
        mock_user_response = Mock()
        mock_user_response.data = Mock()
        mock_user_response.data.id = "44196397"
        mock_user_response.data.username = "elonmusk"

        # Mock tweets response
        mock_tweet = Mock()
        mock_tweet.data = sample_post_data

        mock_tweets_response = Mock()
        mock_tweets_response.data = [mock_tweet]
        mock_tweets_response.meta = {}

        mock_client_instance = Mock()
        mock_client_instance.get_user.return_value = mock_user_response
        mock_client_instance.get_users_tweets.return_value = mock_tweets_response
        mock_tweepy.return_value = mock_client_instance

        client = XAPIClient(bearer_token="test_token")
        tweets = client.get_user_tweets("elonmusk", max_results=10)

        assert len(tweets) > 0
        assert tweets[0]["id"] == "1234567890"
        mock_client_instance.get_users_tweets.assert_called_once()
