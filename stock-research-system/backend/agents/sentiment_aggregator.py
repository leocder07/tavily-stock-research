"""
Unified Sentiment Aggregator
Combines sentiment from multiple professional-grade sources with weighted scoring
"""

from typing import Dict, Any, List, Optional
import asyncio
import logging
from datetime import datetime

from .sentiment_sources import (
    TwitterSentimentSource,
    RedditSentimentSource,
    NewsAPISentimentSource,
    TavilySentimentSource,
    SentimentData
)

logger = logging.getLogger(__name__)


class SentimentAggregator:
    """
    Aggregates sentiment from multiple sources with configurable weighting

    Default Weights:
    - Twitter: 30% (real-time social sentiment)
    - Reddit: 20% (retail investor sentiment)
    - News: 30% (professional analysis)
    - Tavily: 20% (fallback/supplementary)
    """

    def __init__(
        self,
        twitter_api_key: Optional[str] = None,
        reddit_client_id: Optional[str] = None,
        reddit_client_secret: Optional[str] = None,
        news_api_key: Optional[str] = None,
        alpha_vantage_key: Optional[str] = None,
        tavily_api_key: Optional[str] = None,
        weights: Optional[Dict[str, float]] = None
    ):
        """
        Initialize sentiment aggregator

        Args:
            twitter_api_key: Twitter Bearer Token
            reddit_client_id: Reddit app client ID
            reddit_client_secret: Reddit app client secret
            news_api_key: NewsAPI.org key
            alpha_vantage_key: Alpha Vantage API key (preferred for news)
            tavily_api_key: Tavily API key
            weights: Custom source weights (default: Twitter 30%, Reddit 20%, News 30%, Tavily 20%)
        """
        # Initialize sources
        self.sources = {
            "twitter": TwitterSentimentSource(bearer_token=twitter_api_key),
            "reddit": RedditSentimentSource(client_id=reddit_client_id, client_secret=reddit_client_secret),
            "news": NewsAPISentimentSource(news_api_key=news_api_key, alpha_vantage_key=alpha_vantage_key),
            "tavily": TavilySentimentSource(tavily_api_key=tavily_api_key)
        }

        # Default weights
        self.weights = weights or {
            "twitter": 0.30,
            "reddit": 0.20,
            "news": 0.30,
            "tavily": 0.20
        }

        # Validate weights sum to 1.0
        total_weight = sum(self.weights.values())
        if abs(total_weight - 1.0) > 0.01:
            logger.warning(f"Weights sum to {total_weight}, normalizing to 1.0")
            self.weights = {k: v / total_weight for k, v in self.weights.items()}

    async def aggregate_sentiment(self, symbol: str, timeframe: str = "24h") -> Dict[str, Any]:
        """
        Aggregate sentiment from all available sources

        Args:
            symbol: Stock symbol (e.g., AAPL)
            timeframe: Time range (24h, 7d, 30d)

        Returns:
            Aggregated sentiment data with source breakdown
        """
        logger.info(f"[SentimentAggregator] Aggregating sentiment for {symbol} ({timeframe})")

        # Check which sources are available
        available_sources = await self._check_available_sources()

        if not available_sources:
            logger.error("No sentiment sources available")
            return self._empty_result(symbol)

        logger.info(f"Available sources: {', '.join(available_sources)}")

        # Fetch sentiment from all available sources concurrently
        tasks = []
        source_names = []

        for source_name in available_sources:
            source = self.sources[source_name]
            tasks.append(source.fetch_sentiment(symbol, timeframe))
            source_names.append(source_name)

        # Execute all requests concurrently with timeout
        try:
            results = await asyncio.wait_for(
                asyncio.gather(*tasks, return_exceptions=True),
                timeout=30.0
            )
        except asyncio.TimeoutError:
            logger.error("Sentiment aggregation timed out")
            results = [None] * len(tasks)

        # Process results
        source_data = {}
        for source_name, result in zip(source_names, results):
            if isinstance(result, Exception):
                logger.error(f"Source {source_name} failed: {result}")
                source_data[source_name] = None
            elif result is not None:
                source_data[source_name] = result
                logger.info(f"Source {source_name}: {result.sentiment_label} ({result.sentiment_score:.3f})")
            else:
                logger.warning(f"Source {source_name} returned no data")
                source_data[source_name] = None

        # Aggregate scores with weighted average
        aggregated = self._compute_weighted_sentiment(source_data)

        return aggregated

    async def _check_available_sources(self) -> List[str]:
        """Check which sources are available and configured"""
        availability_checks = []
        source_names = []

        for source_name, source in self.sources.items():
            availability_checks.append(source.is_available())
            source_names.append(source_name)

        try:
            results = await asyncio.wait_for(
                asyncio.gather(*availability_checks, return_exceptions=True),
                timeout=10.0
            )
        except asyncio.TimeoutError:
            logger.warning("Source availability check timed out")
            return []

        available = []
        for source_name, is_available in zip(source_names, results):
            if isinstance(is_available, Exception):
                logger.error(f"Availability check failed for {source_name}: {is_available}")
            elif is_available:
                available.append(source_name)

        return available

    def _compute_weighted_sentiment(self, source_data: Dict[str, Optional[SentimentData]]) -> Dict[str, Any]:
        """
        Compute weighted sentiment score from multiple sources

        Args:
            source_data: Dictionary of source_name -> SentimentData

        Returns:
            Aggregated sentiment result
        """
        # Filter out None values
        valid_sources = {k: v for k, v in source_data.items() if v is not None}

        if not valid_sources:
            symbol = "UNKNOWN"
            if source_data:
                for data in source_data.values():
                    if data is not None:
                        symbol = data.symbol
                        break
            return self._empty_result(symbol)

        # Normalize weights for available sources only
        total_weight = sum(self.weights.get(source, 0) for source in valid_sources.keys())
        if total_weight == 0:
            logger.error("Total weight is zero for available sources")
            return self._empty_result(list(valid_sources.values())[0].symbol)

        normalized_weights = {
            source: self.weights.get(source, 0) / total_weight
            for source in valid_sources.keys()
        }

        # Compute weighted sentiment score
        weighted_score = 0.0
        weighted_confidence = 0.0
        total_volume = 0

        for source_name, sentiment_data in valid_sources.items():
            weight = normalized_weights[source_name]
            weighted_score += sentiment_data.sentiment_score * weight
            weighted_confidence += sentiment_data.confidence * weight
            total_volume += sentiment_data.volume

        # Classify overall sentiment
        if weighted_score > 0.15:
            sentiment_label = "bullish"
        elif weighted_score < -0.15:
            sentiment_label = "bearish"
        else:
            sentiment_label = "neutral"

        # Collect all bull/bear arguments
        all_bull_args = []
        all_bear_args = []
        source_breakdown = []

        for source_name, sentiment_data in valid_sources.items():
            all_bull_args.extend(sentiment_data.bull_arguments)
            all_bear_args.extend(sentiment_data.bear_arguments)

            source_breakdown.append({
                "source": source_name,
                "weight": normalized_weights[source_name],
                "sentiment_score": sentiment_data.sentiment_score,
                "sentiment_label": sentiment_data.sentiment_label,
                "confidence": sentiment_data.confidence,
                "volume": sentiment_data.volume,
                "top_topics": sentiment_data.top_topics
            })

        # Get symbol from any valid source
        symbol = list(valid_sources.values())[0].symbol

        # Calculate divergence (variance across sources)
        scores = [data.sentiment_score for data in valid_sources.values()]
        divergence = self._calculate_divergence(scores)

        return {
            "agent": "SentimentAggregator",
            "symbol": symbol,
            "aggregated_sentiment": {
                "sentiment_score": round(weighted_score, 3),
                "sentiment_label": sentiment_label,
                "confidence": round(weighted_confidence, 3),
                "total_volume": total_volume,
                "source_count": len(valid_sources),
                "divergence": divergence
            },
            "source_breakdown": source_breakdown,
            "bull_arguments": all_bull_args[:5],  # Top 5
            "bear_arguments": all_bear_args[:5],  # Top 5
            "weights_used": normalized_weights,
            "metadata": {
                "available_sources": list(valid_sources.keys()),
                "unavailable_sources": [s for s in self.sources.keys() if s not in valid_sources],
                "aggregation_method": "weighted_average",
                "timestamp": datetime.utcnow().isoformat()
            }
        }

    def _calculate_divergence(self, scores: List[float]) -> float:
        """
        Calculate sentiment divergence across sources

        High divergence indicates disagreement between sources

        Args:
            scores: List of sentiment scores

        Returns:
            Divergence score 0-1
        """
        if len(scores) < 2:
            return 0.0

        # Calculate standard deviation
        mean = sum(scores) / len(scores)
        variance = sum((x - mean) ** 2 for x in scores) / len(scores)
        std_dev = variance ** 0.5

        # Normalize to 0-1 range (std dev can be 0 to 2 for -1 to 1 scores)
        divergence = min(std_dev / 2.0, 1.0)

        return round(divergence, 3)

    def _empty_result(self, symbol: str) -> Dict[str, Any]:
        """Return empty result when no data available"""
        return {
            "agent": "SentimentAggregator",
            "symbol": symbol,
            "aggregated_sentiment": {
                "sentiment_score": 0.0,
                "sentiment_label": "neutral",
                "confidence": 0.0,
                "total_volume": 0,
                "source_count": 0,
                "divergence": 0.0
            },
            "source_breakdown": [],
            "bull_arguments": [],
            "bear_arguments": [],
            "weights_used": {},
            "metadata": {
                "available_sources": [],
                "unavailable_sources": list(self.sources.keys()),
                "aggregation_method": "none",
                "error": "No sentiment sources available",
                "timestamp": datetime.utcnow().isoformat()
            }
        }
