"""
Reddit Sentiment Source
Retail investor sentiment from Reddit (WallStreetBets, r/stocks, etc.)
"""

from typing import Optional, List, Dict, Any
import asyncio
import aiohttp
from datetime import datetime, timedelta
import logging
from .base_source import BaseSentimentSource, SentimentData

logger = logging.getLogger(__name__)


class RedditSentimentSource(BaseSentimentSource):
    """
    Reddit sentiment data source

    Monitors subreddits:
    - r/wallstreetbets (retail sentiment)
    - r/stocks (general discussion)
    - r/investing (long-term investors)
    - r/StockMarket (market discussion)
    """

    def __init__(self, client_id: Optional[str] = None, client_secret: Optional[str] = None, user_agent: Optional[str] = None):
        """
        Initialize Reddit sentiment source

        Args:
            client_id: Reddit app client ID
            client_secret: Reddit app client secret
            user_agent: User agent string
        """
        super().__init__("reddit", None)
        self.client_id = client_id
        self.client_secret = client_secret
        self.user_agent = user_agent or "StockResearchBot/1.0"
        self.access_token = None
        self.token_expires = datetime.utcnow()

        # Target subreddits
        self.subreddits = [
            "wallstreetbets",
            "stocks",
            "investing",
            "StockMarket"
        ]

    async def is_available(self) -> bool:
        """Check if Reddit API is configured and available"""
        if not self.client_id or not self.client_secret:
            self.logger.warning("Reddit API credentials not configured")
            return False

        # Try to get access token
        try:
            await self._get_access_token()
            return self.access_token is not None
        except Exception as e:
            self.logger.error(f"Reddit API availability check failed: {e}")
            return False

    async def fetch_sentiment(self, symbol: str, timeframe: str = "24h") -> Optional[SentimentData]:
        """
        Fetch Reddit sentiment for a stock symbol

        Args:
            symbol: Stock symbol (e.g., AAPL)
            timeframe: Time range (24h, 7d, 30d)

        Returns:
            SentimentData object or None if fetch fails
        """
        if not await self.is_available():
            return None

        try:
            # Search across subreddits
            posts = await self._search_reddit(symbol, timeframe)

            if not posts:
                self.logger.warning(f"No Reddit posts found for ${symbol}")
                return None

            # Analyze sentiment
            sentiment_analysis = await self._analyze_posts(posts, symbol)

            return sentiment_analysis

        except Exception as e:
            self.logger.error(f"Reddit sentiment fetch failed for {symbol}: {e}")
            return None

    async def _get_access_token(self):
        """Get Reddit OAuth access token"""
        if self.access_token and datetime.utcnow() < self.token_expires:
            return  # Token still valid

        try:
            async with aiohttp.ClientSession() as session:
                auth = aiohttp.BasicAuth(self.client_id, self.client_secret)
                headers = {"User-Agent": self.user_agent}
                data = {"grant_type": "client_credentials"}

                async with session.post(
                    "https://www.reddit.com/api/v1/access_token",
                    auth=auth,
                    headers=headers,
                    data=data,
                    timeout=aiohttp.ClientTimeout(total=10)
                ) as response:
                    if response.status == 200:
                        token_data = await response.json()
                        self.access_token = token_data.get("access_token")
                        expires_in = token_data.get("expires_in", 3600)
                        self.token_expires = datetime.utcnow() + timedelta(seconds=expires_in - 60)
                        self.logger.info("Reddit access token obtained")
                    else:
                        self.logger.error(f"Failed to get Reddit token: {response.status}")

        except Exception as e:
            self.logger.error(f"Reddit token request failed: {e}")

    async def _search_reddit(self, symbol: str, timeframe: str) -> List[Dict[str, Any]]:
        """
        Search Reddit for posts about the stock symbol

        Args:
            symbol: Stock symbol
            timeframe: Time range

        Returns:
            List of post data
        """
        await self._get_access_token()

        if not self.access_token:
            return []

        all_posts = []

        # Parse timeframe
        time_filter = self._parse_timeframe_reddit(timeframe)

        try:
            async with aiohttp.ClientSession() as session:
                headers = {
                    "Authorization": f"Bearer {self.access_token}",
                    "User-Agent": self.user_agent
                }

                # Search each subreddit
                for subreddit in self.subreddits:
                    # Search by symbol
                    params = {
                        "q": f"${symbol} OR {symbol}",
                        "restrict_sr": "on",
                        "sort": "relevance",
                        "t": time_filter,
                        "limit": 25
                    }

                    try:
                        async with session.get(
                            f"https://oauth.reddit.com/r/{subreddit}/search",
                            headers=headers,
                            params=params,
                            timeout=aiohttp.ClientTimeout(total=10)
                        ) as response:
                            if response.status == 200:
                                data = await response.json()
                                posts = data.get("data", {}).get("children", [])

                                for post in posts:
                                    post_data = post.get("data", {})
                                    all_posts.append({
                                        "subreddit": subreddit,
                                        "title": post_data.get("title", ""),
                                        "text": post_data.get("selftext", ""),
                                        "score": post_data.get("score", 0),
                                        "upvote_ratio": post_data.get("upvote_ratio", 0),
                                        "num_comments": post_data.get("num_comments", 0),
                                        "created_utc": post_data.get("created_utc", 0),
                                        "url": f"https://reddit.com{post_data.get('permalink', '')}",
                                        "author": post_data.get("author", "unknown")
                                    })

                    except Exception as e:
                        self.logger.error(f"Reddit search failed for r/{subreddit}: {e}")
                        continue

                    # Rate limiting - wait between requests
                    await asyncio.sleep(0.5)

        except Exception as e:
            self.logger.error(f"Reddit search failed: {e}")

        return all_posts

    async def _analyze_posts(self, posts: List[Dict], symbol: str) -> SentimentData:
        """
        Analyze sentiment from Reddit posts

        Args:
            posts: List of post data
            symbol: Stock symbol

        Returns:
            SentimentData object
        """
        if not posts:
            return self._empty_sentiment(symbol)

        # Sentiment keywords
        bullish_keywords = ['buy', 'moon', 'rocket', 'calls', 'yolo', 'long', 'bullish', 'breakout', 'gains', 'squeeze']
        bearish_keywords = ['sell', 'puts', 'short', 'bearish', 'crash', 'dump', 'overvalued', 'bubble', 'loss', 'tank']

        positive_count = 0
        negative_count = 0
        neutral_count = 0

        bull_args = []
        bear_args = []
        sample_posts = []

        for post in posts:
            # Combine title and text for analysis
            text = (post.get("title", "") + " " + post.get("text", "")).lower()

            # Sentiment scoring with upvote weight
            pos_score = sum(1 for kw in bullish_keywords if kw in text)
            neg_score = sum(1 for kw in bearish_keywords if kw in text)

            # Weight by Reddit upvotes (popular posts matter more)
            score = post.get("score", 0)
            weight = min(score / 100, 3.0) if score > 0 else 1.0

            if pos_score > neg_score:
                positive_count += weight
                if len(bull_args) < 3 and len(text) > 20:
                    bull_args.append(f"{post.get('title', '')} (r/{post.get('subreddit', 'unknown')})")
            elif neg_score > pos_score:
                negative_count += weight
                if len(bear_args) < 3 and len(text) > 20:
                    bear_args.append(f"{post.get('title', '')} (r/{post.get('subreddit', 'unknown')})")
            else:
                neutral_count += weight

            # Collect sample posts
            if len(sample_posts) < 5:
                sample_posts.append({
                    "subreddit": post.get("subreddit"),
                    "title": post.get("title", "")[:100],
                    "score": post.get("score", 0),
                    "num_comments": post.get("num_comments", 0),
                    "url": post.get("url", "")
                })

        # Calculate overall sentiment
        total = positive_count + negative_count + neutral_count
        if total == 0:
            return self._empty_sentiment(symbol)

        raw_score = (positive_count - negative_count) / total
        sentiment_score = max(-1.0, min(1.0, raw_score))

        sentiment_label = self.classify_sentiment(sentiment_score)
        confidence = self.calculate_confidence(len(posts), min_volume=10)

        # Extract top subreddits
        subreddit_counts = {}
        for post in posts:
            sub = post.get("subreddit", "unknown")
            subreddit_counts[sub] = subreddit_counts.get(sub, 0) + 1

        top_subreddits = sorted(subreddit_counts.items(), key=lambda x: x[1], reverse=True)[:3]

        return SentimentData(
            source="reddit",
            symbol=symbol,
            sentiment_score=sentiment_score,
            sentiment_label=sentiment_label,
            confidence=confidence,
            volume=len(posts),
            timeframe="24h",
            positive_count=int(positive_count),
            neutral_count=int(neutral_count),
            negative_count=int(negative_count),
            top_topics=[f"r/{sub}" for sub, _ in top_subreddits],
            bull_arguments=bull_args[:3],
            bear_arguments=bear_args[:3],
            sample_posts=sample_posts,
            metadata={
                "api": "Reddit API",
                "subreddits_searched": self.subreddits,
                "total_posts": len(posts),
                "avg_score": sum(p.get("score", 0) for p in posts) / len(posts) if posts else 0
            }
        )

    def _parse_timeframe_reddit(self, timeframe: str) -> str:
        """Parse timeframe to Reddit time filter"""
        if timeframe == "24h" or timeframe == "1d":
            return "day"
        elif timeframe == "7d":
            return "week"
        elif timeframe == "30d":
            return "month"
        else:
            return "day"

    def _empty_sentiment(self, symbol: str) -> SentimentData:
        """Return empty sentiment data"""
        return SentimentData(
            source="reddit",
            symbol=symbol,
            sentiment_score=0.0,
            sentiment_label="neutral",
            confidence=0.0,
            volume=0,
            timeframe="24h",
            metadata={"status": "no_data"}
        )
