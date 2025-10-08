"""
Integrated News-Sentiment Agent
Combines NewsIntelligenceAgent + SentimentTrackerAgent with correlation
"""

import logging
from typing import Dict, Any, List, Optional
from datetime import datetime
import asyncio

from langchain_openai import ChatOpenAI
from tavily import TavilyClient

from agents.tavily_agents.news_intelligence_agent import TavilyNewsIntelligenceAgent
from agents.tavily_agents.sentiment_tracker_agent import TavilySentimentTrackerAgent
from services.news_sentiment_correlator import NewsSentimentCorrelator

logger = logging.getLogger(__name__)


class IntegratedNewsSentimentAgent:
    """
    Integrates news fetching, sentiment tracking, and correlation

    Architecture:
    1. Fetch news via NewsIntelligenceAgent
    2. Track social sentiment via SentimentTrackerAgent
    3. Correlate news articles with sentiment using NewsSentimentCorrelator
    4. Return unified analysis with clear news → sentiment mapping

    Key Innovation:
    - Each news article gets individual sentiment score
    - Identifies which news items drive overall sentiment
    - Shows sentiment timeline aligned with news events
    - Provides source attribution (which outlets are bullish/bearish)
    """

    def __init__(
        self,
        tavily_api_key: str,
        llm: ChatOpenAI,
        cache=None,
        router=None
    ):
        """
        Initialize integrated agent

        Args:
            tavily_api_key: Tavily API key
            llm: LangChain LLM for analysis
            cache: Optional TavilyCache instance
            router: Optional SmartModelRouter
        """
        self.tavily = TavilyClient(api_key=tavily_api_key)
        self.llm = llm
        self.name = "IntegratedNewsSentimentAgent"

        # Initialize sub-agents
        self.news_agent = TavilyNewsIntelligenceAgent(
            tavily_api_key=tavily_api_key,
            llm=llm,
            cache=cache,
            router=router
        )

        self.sentiment_agent = TavilySentimentTrackerAgent(
            tavily_api_key=tavily_api_key,
            llm=llm,
            cache=cache
        )

        # Initialize correlator
        self.correlator = NewsSentimentCorrelator(llm=llm)

        logger.info(f"[{self.name}] Initialized with news-sentiment correlation")

    async def analyze(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Perform integrated news-sentiment analysis

        Args:
            context: {
                'symbol': str,
                'market_data': dict (optional),
                'base_recommendation': str (optional)
            }

        Returns:
            {
                'agent': str,
                'symbol': str,
                'news_analysis': dict (from NewsIntelligenceAgent),
                'social_sentiment': dict (from SentimentTrackerAgent),
                'news_sentiment_correlation': dict (NEW - the key addition),
                'unified_sentiment': dict (combined view),
                'divergence_analysis': dict (news vs social sentiment),
                'timestamp': str
            }
        """
        symbol = context.get('symbol', 'UNKNOWN')
        logger.info(f"[{self.name}] Starting integrated analysis for {symbol}")

        try:
            # Step 1: Run news and sentiment agents in parallel
            logger.info(f"[{self.name}] Fetching news and social sentiment in parallel...")

            news_task = self.news_agent.analyze(context)
            sentiment_task = self.sentiment_agent.analyze(context)

            news_result, sentiment_result = await asyncio.gather(
                news_task,
                sentiment_task,
                return_exceptions=True
            )

            # Handle failures gracefully
            if isinstance(news_result, Exception):
                logger.error(f"[{self.name}] News agent failed: {news_result}")
                news_result = self._empty_news_result(symbol)

            if isinstance(sentiment_result, Exception):
                logger.error(f"[{self.name}] Sentiment agent failed: {sentiment_result}")
                sentiment_result = self._empty_sentiment_result(symbol)

            # Step 2: Extract news articles for correlation
            news_articles = news_result.get('news_data', {}).get('sources', [])

            if not news_articles:
                logger.warning(f"[{self.name}] No news articles available for correlation")
                return self._build_result_without_correlation(
                    symbol, news_result, sentiment_result
                )

            # Step 3: Perform news-sentiment correlation
            logger.info(f"[{self.name}] Correlating {len(news_articles)} articles with sentiment...")

            correlation_result = await self.correlator.correlate(
                news_articles=news_articles,
                symbol=symbol,
                aggregate_sentiment=news_result.get('sentiment', {})
            )

            # Step 4: Analyze divergence between news and social sentiment
            divergence_analysis = self._analyze_divergence(
                news_sentiment=correlation_result.get('aggregate_sentiment', {}),
                social_sentiment=sentiment_result.get('sentiment_pulse', {})
            )

            # Step 5: Create unified sentiment view
            unified_sentiment = self._create_unified_sentiment(
                news_sentiment=correlation_result.get('aggregate_sentiment', {}),
                social_sentiment=sentiment_result.get('sentiment_pulse', {}),
                divergence=divergence_analysis
            )

            # Step 6: Build final result
            result = {
                'agent': self.name,
                'symbol': symbol,

                # Original agent outputs
                'news_analysis': {
                    'key_events': news_result.get('key_events', []),
                    'catalysts': news_result.get('catalysts', []),
                    'risks': news_result.get('risks', []),
                    'analyst_actions': news_result.get('analyst_actions', []),
                    'total_articles': len(news_articles)
                },

                'social_sentiment': {
                    'retail_sentiment': sentiment_result.get('sentiment_pulse', {}).get('retail_sentiment', 'neutral'),
                    'retail_score': sentiment_result.get('sentiment_pulse', {}).get('score', 0),
                    'social_volume': sentiment_result.get('sentiment_pulse', {}).get('volume', 'low'),
                    'trending': sentiment_result.get('sentiment_pulse', {}).get('trending', False),
                    'bull_arguments': sentiment_result.get('bull_arguments', []),
                    'bear_arguments': sentiment_result.get('bear_arguments', []),
                    'platforms': sentiment_result.get('social_data', {}).get('platforms', [])
                },

                # NEW: News-Sentiment Correlation
                'news_sentiment_correlation': {
                    'article_sentiments': correlation_result.get('article_sentiments', []),
                    'sentiment_drivers': correlation_result.get('sentiment_drivers', []),
                    'sentiment_timeline': correlation_result.get('sentiment_timeline', []),
                    'insights': correlation_result.get('insights', {}),
                    'correlation_metadata': correlation_result.get('correlation_metadata', {})
                },

                # Unified views
                'unified_sentiment': unified_sentiment,
                'divergence_analysis': divergence_analysis,

                # Metadata
                'data_lineage': {
                    'news_source': 'Tavily News Search (Premium Financial Media)',
                    'social_source': 'Tavily Social Search (Professional + Retail)',
                    'correlation_method': 'LLM-powered article-level sentiment with weighted aggregation',
                    'models_used': ['GPT-3.5 for sentiment extraction', 'GPT-3.5 for news analysis'],
                    'articles_correlated': len(news_articles),
                    'confidence_factors': [
                        'Article-level sentiment scores',
                        'Source diversity',
                        'Sentiment agreement across articles',
                        'Social vs news divergence'
                    ]
                },
                'timestamp': datetime.utcnow().isoformat()
            }

            logger.info(
                f"[{self.name}] Analysis complete - "
                f"Unified sentiment: {unified_sentiment['label']} "
                f"(news: {unified_sentiment['news_sentiment']}, "
                f"social: {unified_sentiment['social_sentiment']}, "
                f"divergence: {divergence_analysis['divergence_level']})"
            )

            return result

        except Exception as e:
            logger.error(f"[{self.name}] Analysis failed: {e}", exc_info=True)
            return self._error_result(symbol, str(e))

    def _analyze_divergence(
        self,
        news_sentiment: Dict[str, Any],
        social_sentiment: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Analyze divergence between news and social sentiment

        High divergence = interesting signal (professionals vs retail disagree)
        """
        news_score = news_sentiment.get('score', 0)
        social_score = social_sentiment.get('score', 0)

        divergence = abs(news_score - social_score)

        # Classify divergence level
        if divergence > 0.6:
            level = 'high'
            interpretation = 'Significant disagreement between professional and retail sentiment'
        elif divergence > 0.3:
            level = 'moderate'
            interpretation = 'Some disagreement between professional and retail sentiment'
        else:
            level = 'low'
            interpretation = 'Professional and retail sentiment are aligned'

        # Determine who's more bullish
        if news_score > social_score + 0.2:
            sentiment_leader = 'news'
            leader_interpretation = 'Professional media more bullish than retail'
        elif social_score > news_score + 0.2:
            sentiment_leader = 'social'
            leader_interpretation = 'Retail investors more bullish than professional media'
        else:
            sentiment_leader = 'aligned'
            leader_interpretation = 'Professional and retail sentiment are similar'

        return {
            'divergence_score': round(divergence, 3),
            'divergence_level': level,
            'interpretation': interpretation,
            'sentiment_leader': sentiment_leader,
            'leader_interpretation': leader_interpretation,
            'news_sentiment_score': news_score,
            'social_sentiment_score': social_score,
            'trading_signal': self._generate_divergence_trading_signal(
                divergence, news_score, social_score
            )
        }

    def _generate_divergence_trading_signal(
        self,
        divergence: float,
        news_score: float,
        social_score: float
    ) -> str:
        """
        Generate trading insight based on sentiment divergence

        Classic contrarian indicators:
        - High retail bullishness + low news sentiment = potential top
        - High retail bearishness + positive news = potential bottom
        """
        if divergence < 0.3:
            return "Aligned sentiment - no divergence signal"

        if social_score > 0.5 and news_score < 0.2:
            return "Contrarian signal: Retail euphoria vs cautious news (potential overvaluation)"
        elif social_score < -0.5 and news_score > -0.2:
            return "Contrarian signal: Retail pessimism vs stable news (potential opportunity)"
        elif news_score > 0.5 and social_score < 0.2:
            return "Institutional signal: Strong news sentiment not yet reflected in retail (potential early mover)"
        else:
            return f"Divergence detected - monitor for resolution"

    def _create_unified_sentiment(
        self,
        news_sentiment: Dict[str, Any],
        social_sentiment: Dict[str, Any],
        divergence: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Create unified sentiment view combining news and social

        Weighted average favoring news sentiment (more reliable)
        """
        news_score = news_sentiment.get('score', 0)
        social_score = social_sentiment.get('score', 0)
        news_confidence = news_sentiment.get('confidence', 0.5)
        social_confidence = social_sentiment.get('confidence', 0.5)

        # Weight news more heavily (70% news, 30% social)
        unified_score = (news_score * 0.7 * news_confidence) + (social_score * 0.3 * social_confidence)
        unified_confidence = (news_confidence * 0.7) + (social_confidence * 0.3)

        # Adjust confidence based on divergence (high divergence = lower confidence)
        divergence_penalty = divergence['divergence_score'] * 0.2
        unified_confidence = max(0.1, unified_confidence - divergence_penalty)

        # Determine label
        if unified_score > 0.25:
            label = 'bullish'
        elif unified_score < -0.25:
            label = 'bearish'
        else:
            label = 'neutral'

        return {
            'label': label,
            'score': round(unified_score, 3),
            'confidence': round(unified_confidence, 3),
            'news_sentiment': news_sentiment.get('label', 'neutral'),
            'social_sentiment': social_sentiment.get('retail_sentiment', 'neutral'),
            'composition': {
                'news_weight': 0.7,
                'social_weight': 0.3,
                'divergence_adjustment': round(divergence_penalty, 3)
            },
            'interpretation': self._generate_unified_interpretation(
                label, news_sentiment.get('label'), social_sentiment.get('retail_sentiment'),
                divergence['divergence_level']
            )
        }

    def _generate_unified_interpretation(
        self,
        unified: str,
        news: str,
        social: str,
        divergence: str
    ) -> str:
        """Generate human-readable interpretation"""
        if unified == news == social:
            return f"Strong {unified} consensus across news and social sentiment"

        if divergence == 'high':
            return f"Overall {unified} but with significant divergence: news is {news}, social is {social}"

        return f"{unified.capitalize()} sentiment (news: {news}, social: {social})"

    def _build_result_without_correlation(
        self,
        symbol: str,
        news_result: Dict[str, Any],
        sentiment_result: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Build result when correlation not possible (no news articles)"""
        return {
            'agent': self.name,
            'symbol': symbol,
            'news_analysis': news_result,
            'social_sentiment': sentiment_result,
            'news_sentiment_correlation': {
                'article_sentiments': [],
                'sentiment_drivers': [],
                'sentiment_timeline': [],
                'insights': {},
                'status': 'No news articles available for correlation'
            },
            'unified_sentiment': {
                'label': 'neutral',
                'score': 0,
                'confidence': 0.3,
                'status': 'Limited data'
            },
            'divergence_analysis': {
                'divergence_score': 0,
                'divergence_level': 'unknown',
                'interpretation': 'Insufficient data for divergence analysis'
            },
            'timestamp': datetime.utcnow().isoformat()
        }

    def _empty_news_result(self, symbol: str) -> Dict[str, Any]:
        """Empty news result"""
        return {
            'symbol': symbol,
            'news_data': {'sources': [], 'total_articles': 0},
            'sentiment': {'overall': 'neutral', 'score': 0, 'confidence': 0},
            'key_events': [],
            'catalysts': [],
            'risks': [],
            'analyst_actions': []
        }

    def _empty_sentiment_result(self, symbol: str) -> Dict[str, Any]:
        """Empty sentiment result"""
        return {
            'symbol': symbol,
            'social_data': {'sources': [], 'platforms': []},
            'sentiment_pulse': {
                'retail_sentiment': 'neutral',
                'score': 0,
                'volume': 'low',
                'trending': False,
                'confidence': 0
            },
            'bull_arguments': [],
            'bear_arguments': [],
            'divergence_score': 0
        }

    def _error_result(self, symbol: str, error: str) -> Dict[str, Any]:
        """Error result"""
        return {
            'agent': self.name,
            'symbol': symbol,
            'status': 'failed',
            'error': error,
            'timestamp': datetime.utcnow().isoformat()
        }
