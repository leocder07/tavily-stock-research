"""
Tavily Sentiment Source
Fallback sentiment data using Tavily Search API
"""

from typing import Optional, List, Dict, Any
import asyncio
from datetime import datetime
import logging
from tavily import TavilyClient
from .base_source import BaseSentimentSource, SentimentData

logger = logging.getLogger(__name__)


class TavilySentimentSource(BaseSentimentSource):
    """
    Tavily sentiment data source (fallback)

    Uses Tavily's advanced search to find sentiment from:
    - Financial news sites
    - Social media platforms
    - Analysis platforms
    """

    def __init__(self, tavily_api_key: Optional[str] = None):
        """
        Initialize Tavily sentiment source

        Args:
            tavily_api_key: Tavily API key
        """
        super().__init__("tavily", tavily_api_key)
        self.tavily = TavilyClient(api_key=tavily_api_key) if tavily_api_key else None

    async def is_available(self) -> bool:
        """Check if Tavily API is configured and available"""
        if not self.tavily:
            self.logger.warning("Tavily API key not configured")
            return False
        return True

    async def fetch_sentiment(self, symbol: str, timeframe: str = "24h") -> Optional[SentimentData]:
        """
        Fetch Tavily sentiment for a stock symbol

        Args:
            symbol: Stock symbol (e.g., AAPL)
            timeframe: Time range (24h, 7d, 30d)

        Returns:
            SentimentData object or None if fetch fails
        """
        if not await self.is_available():
            return None

        try:
            # Search for sentiment data
            results = await self._search_sentiment(symbol, timeframe)

            if not results or not results.get("results"):
                self.logger.warning(f"No Tavily results found for ${symbol}")
                return None

            # Analyze sentiment
            sentiment_analysis = await self._analyze_results(results, symbol)

            return sentiment_analysis

        except Exception as e:
            self.logger.error(f"Tavily sentiment fetch failed for {symbol}: {e}")
            return None

    async def _search_sentiment(self, symbol: str, timeframe: str) -> Dict[str, Any]:
        """
        Search Tavily for sentiment data

        Args:
            symbol: Stock symbol
            timeframe: Time range

        Returns:
            Tavily search results
        """
        days = self._parse_timeframe(timeframe)

        try:
            query = f"${symbol} stock sentiment analysis latest discussion opinion"

            # Run Tavily search in thread pool (it's synchronous)
            results = await asyncio.to_thread(
                self.tavily.search,
                query=query,
                search_depth="advanced",
                max_results=25,
                days=days,
                include_domains=[
                    "seekingalpha.com",
                    "benzinga.com",
                    "marketwatch.com",
                    "barrons.com",
                    "investors.com",
                    "fool.com",
                    "investing.com",
                    "stocktwits.com",
                    "twitter.com",
                    "x.com"
                ],
                include_answer=True
            )

            return results

        except Exception as e:
            self.logger.error(f"Tavily search failed: {e}")
            return {}

    async def _analyze_results(self, results: Dict, symbol: str) -> SentimentData:
        """
        Analyze sentiment from Tavily results

        Args:
            results: Tavily search results
            symbol: Stock symbol

        Returns:
            SentimentData object
        """
        articles = results.get("results", [])
        if not articles:
            return self._empty_sentiment(symbol)

        # Sentiment keywords
        positive_keywords = ['bullish', 'buy', 'moon', 'rocket', 'calls', 'long', 'breakout', 'rally', 'surge', 'gains', 'upgrade']
        negative_keywords = ['bearish', 'sell', 'puts', 'short', 'crash', 'dump', 'decline', 'drop', 'loss', 'downgrade', 'warning']

        positive_count = 0
        negative_count = 0
        neutral_count = 0

        bull_args = []
        bear_args = []
        sample_articles = []

        for article in articles:
            # Combine title and content for analysis
            text = (article.get("title", "") + " " + article.get("content", "")).lower()

            # Score sentiment
            pos_score = sum(1 for kw in positive_keywords if kw in text)
            neg_score = sum(1 for kw in negative_keywords if kw in text)

            if pos_score > neg_score:
                positive_count += 1
                if len(bull_args) < 3 and len(article.get("title", "")) > 20:
                    bull_args.append(article.get("title", "")[:100])
            elif neg_score > pos_score:
                negative_count += 1
                if len(bear_args) < 3 and len(article.get("title", "")) > 20:
                    bear_args.append(article.get("title", "")[:100])
            else:
                neutral_count += 1

            # Collect samples
            if len(sample_articles) < 5:
                sample_articles.append({
                    "title": article.get("title", ""),
                    "url": article.get("url", ""),
                    "score": article.get("score", 0),
                    "content": article.get("content", "")[:150]
                })

        # Calculate overall sentiment
        total = positive_count + negative_count + neutral_count
        if total == 0:
            return self._empty_sentiment(symbol)

        raw_score = (positive_count - negative_count) / total
        sentiment_score = max(-1.0, min(1.0, raw_score))

        sentiment_label = self.classify_sentiment(sentiment_score)
        confidence = self.calculate_confidence(total, min_volume=10)

        # Extract platforms
        platforms = set()
        for article in articles:
            url = article.get("url", "")
            if "seekingalpha" in url:
                platforms.add("Seeking Alpha")
            elif "benzinga" in url:
                platforms.add("Benzinga")
            elif "marketwatch" in url:
                platforms.add("MarketWatch")
            elif "stocktwits" in url:
                platforms.add("StockTwits")
            elif "twitter.com" in url or "x.com" in url:
                platforms.add("Twitter/X")

        return SentimentData(
            source="tavily",
            symbol=symbol,
            sentiment_score=sentiment_score,
            sentiment_label=sentiment_label,
            confidence=confidence,
            volume=total,
            timeframe="24h",
            positive_count=positive_count,
            neutral_count=neutral_count,
            negative_count=negative_count,
            top_topics=list(platforms)[:5],
            bull_arguments=bull_args[:3],
            bear_arguments=bear_args[:3],
            sample_posts=sample_articles,
            metadata={
                "api": "Tavily Advanced Search",
                "total_results": len(articles),
                "platforms": list(platforms)
            }
        )

    def _parse_timeframe(self, timeframe: str) -> int:
        """Parse timeframe string to days"""
        if timeframe == "24h" or timeframe == "1d":
            return 1
        elif timeframe == "7d":
            return 7
        elif timeframe == "30d":
            return 30
        else:
            return 1

    def _empty_sentiment(self, symbol: str) -> SentimentData:
        """Return empty sentiment data"""
        return SentimentData(
            source="tavily",
            symbol=symbol,
            sentiment_score=0.0,
            sentiment_label="neutral",
            confidence=0.0,
            volume=0,
            timeframe="24h",
            metadata={"status": "no_data"}
        )
