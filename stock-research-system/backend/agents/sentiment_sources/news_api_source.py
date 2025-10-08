"""
News API Sentiment Source
Professional news sentiment from multiple news sources
"""

from typing import Optional, List, Dict, Any
import asyncio
import aiohttp
from datetime import datetime, timedelta
import logging
from .base_source import BaseSentimentSource, SentimentData

logger = logging.getLogger(__name__)


class NewsAPISentimentSource(BaseSentimentSource):
    """
    NewsAPI sentiment data source

    Supports multiple news sentiment APIs:
    - NewsAPI.org (general news)
    - Alpha Vantage News Sentiment (financial news with sentiment scores)
    - Finnhub News (financial news)
    """

    def __init__(self, news_api_key: Optional[str] = None, alpha_vantage_key: Optional[str] = None):
        """
        Initialize News API sentiment source

        Args:
            news_api_key: NewsAPI.org API key
            alpha_vantage_key: Alpha Vantage API key (preferred for sentiment)
        """
        super().__init__("news", news_api_key)
        self.news_api_key = news_api_key
        self.alpha_vantage_key = alpha_vantage_key

        # Prefer Alpha Vantage as it provides native sentiment scoring
        self.primary_api = "alpha_vantage" if alpha_vantage_key else "newsapi"

    async def is_available(self) -> bool:
        """Check if News API is configured and available"""
        if self.primary_api == "alpha_vantage":
            return self.alpha_vantage_key is not None
        elif self.primary_api == "newsapi":
            return self.news_api_key is not None
        return False

    async def fetch_sentiment(self, symbol: str, timeframe: str = "24h") -> Optional[SentimentData]:
        """
        Fetch news sentiment for a stock symbol

        Args:
            symbol: Stock symbol (e.g., AAPL)
            timeframe: Time range (24h, 7d, 30d)

        Returns:
            SentimentData object or None if fetch fails
        """
        if not await self.is_available():
            return None

        try:
            if self.primary_api == "alpha_vantage":
                return await self._fetch_alpha_vantage_sentiment(symbol, timeframe)
            else:
                return await self._fetch_newsapi_sentiment(symbol, timeframe)

        except Exception as e:
            self.logger.error(f"News sentiment fetch failed for {symbol}: {e}")
            return None

    async def _fetch_alpha_vantage_sentiment(self, symbol: str, timeframe: str) -> Optional[SentimentData]:
        """
        Fetch sentiment from Alpha Vantage News Sentiment API

        This API provides:
        - News articles with sentiment scores
        - Overall sentiment score
        - Relevance scores
        """
        try:
            async with aiohttp.ClientSession() as session:
                params = {
                    "function": "NEWS_SENTIMENT",
                    "tickers": symbol,
                    "apikey": self.alpha_vantage_key,
                    "limit": 50  # Get up to 50 articles
                }

                async with session.get(
                    "https://www.alphavantage.co/query",
                    params=params,
                    timeout=aiohttp.ClientTimeout(total=15)
                ) as response:
                    if response.status != 200:
                        self.logger.warning(f"Alpha Vantage API returned status {response.status}")
                        return None

                    data = await response.json()

                    # Check for API errors
                    if "Error Message" in data or "Note" in data:
                        self.logger.warning(f"Alpha Vantage API error: {data.get('Error Message') or data.get('Note')}")
                        return None

                    feed = data.get("feed", [])
                    if not feed:
                        return self._empty_sentiment(symbol)

                    return await self._analyze_alpha_vantage_news(feed, symbol)

        except Exception as e:
            self.logger.error(f"Alpha Vantage sentiment fetch failed: {e}")
            return None

    async def _analyze_alpha_vantage_news(self, articles: List[Dict], symbol: str) -> SentimentData:
        """
        Analyze sentiment from Alpha Vantage news articles

        Alpha Vantage provides:
        - overall_sentiment_score (-1 to 1)
        - overall_sentiment_label (Bearish, Neutral, Bullish, etc.)
        - relevance_score (0 to 1)
        """
        if not articles:
            return self._empty_sentiment(symbol)

        sentiment_scores = []
        relevance_scores = []
        positive_count = 0
        negative_count = 0
        neutral_count = 0

        bull_args = []
        bear_args = []
        sample_articles = []

        for article in articles:
            # Get ticker-specific sentiment
            ticker_sentiment = None
            for ticker_data in article.get("ticker_sentiment", []):
                if ticker_data.get("ticker") == symbol:
                    ticker_sentiment = ticker_data
                    break

            if not ticker_sentiment:
                continue

            # Extract sentiment score and relevance
            sentiment_score = float(ticker_sentiment.get("ticker_sentiment_score", 0))
            relevance = float(ticker_sentiment.get("relevance_score", 0))
            sentiment_label = ticker_sentiment.get("ticker_sentiment_label", "Neutral")

            # Weight by relevance
            if relevance > 0.3:  # Only consider relevant articles
                sentiment_scores.append(sentiment_score)
                relevance_scores.append(relevance)

                # Categorize
                if sentiment_label in ["Bullish", "Somewhat-Bullish"]:
                    positive_count += 1
                    if len(bull_args) < 3:
                        bull_args.append(article.get("title", "")[:100])
                elif sentiment_label in ["Bearish", "Somewhat-Bearish"]:
                    negative_count += 1
                    if len(bear_args) < 3:
                        bear_args.append(article.get("title", "")[:100])
                else:
                    neutral_count += 1

            # Collect sample articles
            if len(sample_articles) < 5:
                sample_articles.append({
                    "title": article.get("title", ""),
                    "source": article.get("source", ""),
                    "url": article.get("url", ""),
                    "sentiment_score": sentiment_score,
                    "sentiment_label": sentiment_label,
                    "time_published": article.get("time_published", "")
                })

        # Calculate overall sentiment
        if not sentiment_scores:
            return self._empty_sentiment(symbol)

        # Weighted average by relevance
        total_relevance = sum(relevance_scores)
        if total_relevance > 0:
            weighted_sentiment = sum(s * r for s, r in zip(sentiment_scores, relevance_scores)) / total_relevance
        else:
            weighted_sentiment = sum(sentiment_scores) / len(sentiment_scores)

        # Normalize to -1 to 1 range
        sentiment_score = max(-1.0, min(1.0, weighted_sentiment))
        sentiment_label = self.classify_sentiment(sentiment_score)

        total_articles = len(sentiment_scores)
        confidence = self.calculate_confidence(total_articles, min_volume=10)

        return SentimentData(
            source="news",
            symbol=symbol,
            sentiment_score=sentiment_score,
            sentiment_label=sentiment_label,
            confidence=confidence,
            volume=total_articles,
            timeframe="24h",
            positive_count=positive_count,
            neutral_count=neutral_count,
            negative_count=negative_count,
            top_topics=["Financial News", "Market Analysis"],
            bull_arguments=bull_args[:3],
            bear_arguments=bear_args[:3],
            sample_posts=sample_articles,
            metadata={
                "api": "Alpha Vantage News Sentiment",
                "total_articles": len(articles),
                "relevant_articles": total_articles,
                "avg_relevance": sum(relevance_scores) / len(relevance_scores) if relevance_scores else 0
            }
        )

    async def _fetch_newsapi_sentiment(self, symbol: str, timeframe: str) -> Optional[SentimentData]:
        """
        Fetch sentiment from NewsAPI.org (fallback)

        NewsAPI doesn't provide sentiment scores, so we need to analyze titles/descriptions
        """
        try:
            # Parse timeframe
            hours = self._parse_timeframe(timeframe)
            from_date = (datetime.utcnow() - timedelta(hours=hours)).strftime("%Y-%m-%d")

            async with aiohttp.ClientSession() as session:
                params = {
                    "q": f"{symbol} OR ${symbol}",
                    "from": from_date,
                    "sortBy": "relevancy",
                    "language": "en",
                    "apiKey": self.news_api_key,
                    "pageSize": 50
                }

                async with session.get(
                    "https://newsapi.org/v2/everything",
                    params=params,
                    timeout=aiohttp.ClientTimeout(total=15)
                ) as response:
                    if response.status != 200:
                        self.logger.warning(f"NewsAPI returned status {response.status}")
                        return None

                    data = await response.json()

                    if data.get("status") != "ok":
                        self.logger.warning(f"NewsAPI error: {data.get('message')}")
                        return None

                    articles = data.get("articles", [])
                    if not articles:
                        return self._empty_sentiment(symbol)

                    return await self._analyze_newsapi_articles(articles, symbol)

        except Exception as e:
            self.logger.error(f"NewsAPI sentiment fetch failed: {e}")
            return None

    async def _analyze_newsapi_articles(self, articles: List[Dict], symbol: str) -> SentimentData:
        """
        Analyze sentiment from NewsAPI articles (keyword-based)
        """
        if not articles:
            return self._empty_sentiment(symbol)

        # Sentiment keywords
        positive_keywords = ['surge', 'gains', 'bullish', 'rally', 'growth', 'profit', 'beat', 'outperform', 'upgrade']
        negative_keywords = ['decline', 'loss', 'bearish', 'crash', 'downgrade', 'miss', 'warning', 'concern', 'risk']

        positive_count = 0
        negative_count = 0
        neutral_count = 0

        bull_args = []
        bear_args = []
        sample_articles = []

        for article in articles:
            text = (article.get("title", "") + " " + article.get("description", "")).lower()

            pos_score = sum(1 for kw in positive_keywords if kw in text)
            neg_score = sum(1 for kw in negative_keywords if kw in text)

            if pos_score > neg_score:
                positive_count += 1
                if len(bull_args) < 3:
                    bull_args.append(article.get("title", "")[:100])
            elif neg_score > pos_score:
                negative_count += 1
                if len(bear_args) < 3:
                    bear_args.append(article.get("title", "")[:100])
            else:
                neutral_count += 1

            if len(sample_articles) < 5:
                sample_articles.append({
                    "title": article.get("title", ""),
                    "source": article.get("source", {}).get("name", ""),
                    "url": article.get("url", ""),
                    "published_at": article.get("publishedAt", "")
                })

        total = positive_count + negative_count + neutral_count
        if total == 0:
            return self._empty_sentiment(symbol)

        raw_score = (positive_count - negative_count) / total
        sentiment_score = max(-1.0, min(1.0, raw_score))
        sentiment_label = self.classify_sentiment(sentiment_score)
        confidence = self.calculate_confidence(total, min_volume=10)

        return SentimentData(
            source="news",
            symbol=symbol,
            sentiment_score=sentiment_score,
            sentiment_label=sentiment_label,
            confidence=confidence,
            volume=total,
            timeframe="24h",
            positive_count=positive_count,
            neutral_count=neutral_count,
            negative_count=negative_count,
            top_topics=["Financial News"],
            bull_arguments=bull_args[:3],
            bear_arguments=bear_args[:3],
            sample_posts=sample_articles,
            metadata={
                "api": "NewsAPI.org",
                "total_articles": len(articles)
            }
        )

    def _parse_timeframe(self, timeframe: str) -> int:
        """Parse timeframe string to hours"""
        if timeframe == "24h" or timeframe == "1d":
            return 24
        elif timeframe == "7d":
            return 168
        elif timeframe == "30d":
            return 720
        else:
            return 24

    def _empty_sentiment(self, symbol: str) -> SentimentData:
        """Return empty sentiment data"""
        return SentimentData(
            source="news",
            symbol=symbol,
            sentiment_score=0.0,
            sentiment_label="neutral",
            confidence=0.0,
            volume=0,
            timeframe="24h",
            metadata={"status": "no_data"}
        )
