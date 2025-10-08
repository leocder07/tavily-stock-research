"""
Enhanced Sentiment Tracker Agent
Professional-grade multi-source sentiment analysis with fallback support
"""

import logging
from typing import Dict, Any, Optional
from datetime import datetime

from ..sentiment_aggregator import SentimentAggregator

logger = logging.getLogger(__name__)


class EnhancedSentimentTrackerAgent:
    """
    Enhanced sentiment tracker using multiple professional data sources

    Data Sources (priority order):
    1. Twitter API - Real-time social sentiment (30% weight)
    2. Reddit API - Retail investor sentiment (20% weight)
    3. News APIs - Professional analysis (30% weight)
    4. Tavily Search - Fallback/supplementary (20% weight)

    Features:
    - Multi-source aggregation with weighted scoring
    - Automatic fallback to available sources
    - Source attribution and breakdown
    - Divergence detection (sources disagreeing)
    """

    def __init__(
        self,
        tavily_api_key: str,
        twitter_api_key: Optional[str] = None,
        reddit_client_id: Optional[str] = None,
        reddit_client_secret: Optional[str] = None,
        news_api_key: Optional[str] = None,
        alpha_vantage_key: Optional[str] = None,
        custom_weights: Optional[Dict[str, float]] = None,
        use_legacy_fallback: bool = True
    ):
        """
        Initialize enhanced sentiment tracker

        Args:
            tavily_api_key: Tavily API key (required)
            twitter_api_key: Twitter Bearer Token (optional)
            reddit_client_id: Reddit app client ID (optional)
            reddit_client_secret: Reddit app client secret (optional)
            news_api_key: NewsAPI.org key (optional)
            alpha_vantage_key: Alpha Vantage API key (optional, preferred for news)
            custom_weights: Custom source weights (optional)
            use_legacy_fallback: If True, falls back to legacy Tavily-only mode if all APIs unavailable
        """
        self.name = "EnhancedSentimentTrackerAgent"
        self.use_legacy_fallback = use_legacy_fallback

        # Initialize aggregator
        self.aggregator = SentimentAggregator(
            twitter_api_key=twitter_api_key,
            reddit_client_id=reddit_client_id,
            reddit_client_secret=reddit_client_secret,
            news_api_key=news_api_key,
            alpha_vantage_key=alpha_vantage_key,
            tavily_api_key=tavily_api_key,
            weights=custom_weights
        )

        # Legacy fallback (original Tavily-only implementation)
        if use_legacy_fallback:
            from .sentiment_tracker_agent import TavilySentimentTrackerAgent
            from langchain_openai import ChatOpenAI

            # Initialize legacy agent as fallback
            self.legacy_agent = TavilySentimentTrackerAgent(
                tavily_api_key=tavily_api_key,
                llm=ChatOpenAI(model="gpt-3.5-turbo", temperature=0.2)
            )
        else:
            self.legacy_agent = None

        logger.info(f"[{self.name}] Initialized with multi-source sentiment aggregation")

    async def track(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Track sentiment using multi-source aggregation

        Args:
            context: Analysis context dict with 'symbol' key

        Returns:
            Enhanced sentiment analysis results
        """
        return await self.analyze(context)

    async def analyze(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Analyze sentiment from multiple professional sources

        Args:
            context: {
                'symbol': str,
                'timeframe': str (optional, default '24h'),
                'market_data': dict (optional),
                'news_sentiment': dict (optional, for divergence calculation)
            }

        Returns:
            {
                'agent': str,
                'symbol': str,
                'aggregated_sentiment': dict (overall sentiment),
                'source_breakdown': list (individual source results),
                'bull_arguments': list,
                'bear_arguments': list,
                'divergence_score': float,
                'data_lineage': dict,
                'timestamp': str
            }
        """
        symbol = context.get('symbol', 'UNKNOWN')
        timeframe = context.get('timeframe', '24h')

        logger.info(f"[{self.name}] Analyzing sentiment for {symbol} ({timeframe})")

        try:
            # Attempt multi-source aggregation
            result = await self.aggregator.aggregate_sentiment(symbol, timeframe)

            # Check if we got useful results
            if result['aggregated_sentiment']['source_count'] == 0:
                logger.warning(f"[{self.name}] No sources available, attempting fallback")

                if self.legacy_agent and self.use_legacy_fallback:
                    logger.info(f"[{self.name}] Using legacy Tavily-only fallback")
                    return await self.legacy_agent.analyze(context)
                else:
                    logger.error(f"[{self.name}] No fallback available")
                    return self._error_result(symbol, "No sentiment sources available")

            # Enhance result with additional fields
            enhanced_result = self._enhance_result(result, context)

            logger.info(
                f"[{self.name}] Sentiment aggregated: {enhanced_result['aggregated_sentiment']['sentiment_label']} "
                f"(score: {enhanced_result['aggregated_sentiment']['sentiment_score']:.3f}, "
                f"sources: {enhanced_result['aggregated_sentiment']['source_count']})"
            )

            return enhanced_result

        except Exception as e:
            logger.error(f"[{self.name}] Error analyzing sentiment: {e}", exc_info=True)

            # Try legacy fallback
            if self.legacy_agent and self.use_legacy_fallback:
                logger.info(f"[{self.name}] Exception occurred, using legacy fallback")
                try:
                    return await self.legacy_agent.analyze(context)
                except Exception as fallback_error:
                    logger.error(f"[{self.name}] Legacy fallback also failed: {fallback_error}")

            return self._error_result(symbol, str(e))

    def _enhance_result(self, result: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Enhance aggregated result with additional fields

        Args:
            result: Aggregated sentiment result
            context: Original context

        Returns:
            Enhanced result dictionary
        """
        symbol = result['symbol']

        # Calculate divergence with news sentiment if available
        news_sentiment_score = context.get('news_sentiment', {}).get('score', 0)
        retail_sentiment_score = result['aggregated_sentiment']['sentiment_score']

        sentiment_divergence = abs(retail_sentiment_score - news_sentiment_score)

        # Build data lineage
        available_sources = result['metadata']['available_sources']
        unavailable_sources = result['metadata']['unavailable_sources']

        data_lineage = {
            'source_type': 'Multi-Source Aggregation',
            'available_sources': available_sources,
            'unavailable_sources': unavailable_sources,
            'aggregation_method': 'Weighted Average',
            'weights': result['weights_used'],
            'total_data_points': result['aggregated_sentiment']['total_volume'],
            'source_divergence': result['aggregated_sentiment']['divergence'],
            'quality_tier': self._determine_quality_tier(available_sources)
        }

        # Build enhanced result
        enhanced = {
            'agent': self.name,
            'symbol': symbol,
            'aggregated_sentiment': result['aggregated_sentiment'],
            'source_breakdown': result['source_breakdown'],
            'bull_arguments': result['bull_arguments'],
            'bear_arguments': result['bear_arguments'],
            'divergence_score': round(sentiment_divergence, 3),
            'data_lineage': data_lineage,
            'timestamp': result['metadata']['timestamp'],
            'status': 'success'
        }

        return enhanced

    def _determine_quality_tier(self, sources: list) -> str:
        """Determine quality tier based on available sources"""
        if len(sources) >= 4:
            return "Premium (All Sources)"
        elif len(sources) >= 3:
            return "Professional (3+ Sources)"
        elif len(sources) >= 2:
            return "Standard (2 Sources)"
        elif len(sources) == 1:
            return "Basic (Single Source)"
        else:
            return "No Data"

    def _error_result(self, symbol: str, error: str) -> Dict[str, Any]:
        """Return error result"""
        return {
            'agent': self.name,
            'symbol': symbol,
            'aggregated_sentiment': {
                'sentiment_score': 0.0,
                'sentiment_label': 'neutral',
                'confidence': 0.0,
                'total_volume': 0,
                'source_count': 0,
                'divergence': 0.0
            },
            'source_breakdown': [],
            'bull_arguments': [],
            'bear_arguments': [],
            'divergence_score': 0.0,
            'data_lineage': {
                'source_type': 'Error',
                'error': error
            },
            'timestamp': datetime.utcnow().isoformat(),
            'status': 'failed',
            'error': error
        }
