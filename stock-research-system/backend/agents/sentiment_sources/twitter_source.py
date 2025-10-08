"""
Twitter (X) Sentiment Source
Real-time social sentiment from Twitter/X platform
"""

from typing import Optional, List, Dict, Any
import asyncio
import aiohttp
from datetime import datetime, timedelta
import logging
from .base_source import BaseSentimentSource, SentimentData

logger = logging.getLogger(__name__)


class TwitterSentimentSource(BaseSentimentSource):
    """
    Twitter/X sentiment data source

    Uses Twitter API v2 for:
    - Recent tweets about stock symbol
    - Engagement metrics (likes, retweets)
    - Tweet sentiment analysis
    """

    def __init__(self, api_key: Optional[str] = None, bearer_token: Optional[str] = None):
        """
        Initialize Twitter sentiment source

        Args:
            api_key: Twitter API key (optional, bearer_token preferred)
            bearer_token: Twitter Bearer Token for API v2
        """
        super().__init__("twitter", api_key)
        self.bearer_token = bearer_token or api_key
        self.base_url = "https://api.twitter.com/2"

        # Rate limiting
        self.max_requests_per_15min = 180
        self.request_count = 0
        self.rate_limit_reset = datetime.utcnow()

    async def is_available(self) -> bool:
        """Check if Twitter API is configured and available"""
        if not self.bearer_token:
            self.logger.warning("Twitter Bearer Token not configured")
            return False

        # Test API connectivity
        try:
            async with aiohttp.ClientSession() as session:
                headers = {"Authorization": f"Bearer {self.bearer_token}"}
                async with session.get(f"{self.base_url}/tweets/search/recent?query=test&max_results=10", headers=headers, timeout=aiohttp.ClientTimeout(total=5)) as response:
                    return response.status == 200 or response.status == 429  # 429 = rate limited but valid
        except Exception as e:
            self.logger.error(f"Twitter API availability check failed: {e}")
            return False

    async def fetch_sentiment(self, symbol: str, timeframe: str = "24h") -> Optional[SentimentData]:
        """
        Fetch Twitter sentiment for a stock symbol

        Args:
            symbol: Stock symbol (e.g., AAPL)
            timeframe: Time range (24h, 7d, 30d)

        Returns:
            SentimentData object or None if fetch fails
        """
        if not await self.is_available():
            return None

        try:
            # Search for tweets
            tweets = await self._search_tweets(symbol, timeframe)

            if not tweets:
                self.logger.warning(f"No tweets found for ${symbol}")
                return None

            # Analyze sentiment
            sentiment_analysis = await self._analyze_tweets(tweets, symbol)

            return sentiment_analysis

        except Exception as e:
            self.logger.error(f"Twitter sentiment fetch failed for {symbol}: {e}")
            return None

    async def _search_tweets(self, symbol: str, timeframe: str) -> List[Dict[str, Any]]:
        """
        Search for tweets about the stock symbol

        Args:
            symbol: Stock symbol
            timeframe: Time range

        Returns:
            List of tweet data
        """
        # Parse timeframe
        hours = self._parse_timeframe(timeframe)
        start_time = (datetime.utcnow() - timedelta(hours=hours)).isoformat() + "Z"

        # Build search query - exclude retweets, focus on cashtags
        query = f"${symbol} OR #{symbol} -is:retweet lang:en"

        try:
            async with aiohttp.ClientSession() as session:
                headers = {"Authorization": f"Bearer {self.bearer_token}"}
                params = {
                    "query": query,
                    "max_results": 100,  # Maximum allowed by API
                    "start_time": start_time,
                    "tweet.fields": "created_at,public_metrics,text,author_id",
                    "expansions": "author_id",
                    "user.fields": "username,verified"
                }

                async with session.get(
                    f"{self.base_url}/tweets/search/recent",
                    headers=headers,
                    params=params,
                    timeout=aiohttp.ClientTimeout(total=10)
                ) as response:
                    if response.status == 200:
                        data = await response.json()
                        return data.get("data", [])
                    else:
                        self.logger.warning(f"Twitter API returned status {response.status}")
                        return []

        except Exception as e:
            self.logger.error(f"Tweet search failed: {e}")
            return []

    async def _analyze_tweets(self, tweets: List[Dict], symbol: str) -> SentimentData:
        """
        Analyze sentiment from tweets

        Args:
            tweets: List of tweet data
            symbol: Stock symbol

        Returns:
            SentimentData object
        """
        if not tweets:
            return self._empty_sentiment(symbol)

        # Sentiment classification using keyword analysis
        positive_keywords = ['bullish', 'moon', 'rocket', 'buy', 'calls', 'long', 'breakout', 'rally', 'surge', 'gains']
        negative_keywords = ['bearish', 'crash', 'dump', 'sell', 'puts', 'short', 'tank', 'decline', 'drop', 'loss']

        positive_count = 0
        negative_count = 0
        neutral_count = 0

        bull_args = []
        bear_args = []
        sample_tweets = []

        for tweet in tweets:
            text = tweet.get("text", "").lower()

            # Calculate sentiment
            pos_score = sum(1 for kw in positive_keywords if kw in text)
            neg_score = sum(1 for kw in negative_keywords if kw in text)

            if pos_score > neg_score:
                positive_count += 1
                if len(bull_args) < 3 and len(text) > 20:
                    bull_args.append(text[:100])
            elif neg_score > pos_score:
                negative_count += 1
                if len(bear_args) < 3 and len(text) > 20:
                    bear_args.append(text[:100])
            else:
                neutral_count += 1

            # Collect sample tweets
            if len(sample_tweets) < 5:
                sample_tweets.append({
                    "text": text[:150],
                    "created_at": tweet.get("created_at"),
                    "metrics": tweet.get("public_metrics", {})
                })

        # Calculate overall sentiment score
        total = positive_count + negative_count + neutral_count
        if total == 0:
            return self._empty_sentiment(symbol)

        # Weighted score: positive = +1, neutral = 0, negative = -1
        raw_score = (positive_count - negative_count) / total
        sentiment_score = max(-1.0, min(1.0, raw_score))

        sentiment_label = self.classify_sentiment(sentiment_score)
        confidence = self.calculate_confidence(total, min_volume=20)

        return SentimentData(
            source="twitter",
            symbol=symbol,
            sentiment_score=sentiment_score,
            sentiment_label=sentiment_label,
            confidence=confidence,
            volume=total,
            timeframe="24h",
            positive_count=positive_count,
            neutral_count=neutral_count,
            negative_count=negative_count,
            top_topics=[f"${symbol} twitter mentions"],
            bull_arguments=bull_args[:3],
            bear_arguments=bear_args[:3],
            sample_posts=sample_tweets,
            metadata={
                "api": "Twitter API v2",
                "total_tweets": len(tweets),
                "engagement_rate": self._calculate_engagement(tweets)
            }
        )

    def _calculate_engagement(self, tweets: List[Dict]) -> float:
        """Calculate average engagement rate"""
        if not tweets:
            return 0.0

        total_engagement = 0
        for tweet in tweets:
            metrics = tweet.get("public_metrics", {})
            total_engagement += (
                metrics.get("like_count", 0) +
                metrics.get("retweet_count", 0) +
                metrics.get("reply_count", 0)
            )

        return round(total_engagement / len(tweets), 2)

    def _parse_timeframe(self, timeframe: str) -> int:
        """Parse timeframe string to hours"""
        if timeframe == "24h" or timeframe == "1d":
            return 24
        elif timeframe == "7d":
            return 168
        elif timeframe == "30d":
            return 720
        else:
            return 24  # Default to 24 hours

    def _empty_sentiment(self, symbol: str) -> SentimentData:
        """Return empty sentiment data"""
        return SentimentData(
            source="twitter",
            symbol=symbol,
            sentiment_score=0.0,
            sentiment_label="neutral",
            confidence=0.0,
            volume=0,
            timeframe="24h",
            metadata={"status": "no_data"}
        )
