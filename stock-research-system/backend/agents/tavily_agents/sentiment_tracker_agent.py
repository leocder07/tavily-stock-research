"""
Tavily Sentiment Tracker Agent
Uses Tavily Search + Extract to analyze social media and retail sentiment
Complements professional news with retail investor pulse
"""

import logging
from typing import Dict, Any, List
from datetime import datetime
import asyncio

from tavily import TavilyClient
from langchain_openai import ChatOpenAI
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)


class SentimentPulse(BaseModel):
    """Structured sentiment output"""
    retail_sentiment: str = Field(description="Retail investor sentiment: bullish/neutral/bearish")
    retail_score: float = Field(description="Retail sentiment score -1 to 1", ge=-1, le=1)
    social_volume: str = Field(description="Discussion volume: high/medium/low")
    trending: bool = Field(description="Whether stock is trending on social media")
    bull_arguments: List[str] = Field(description="Main bullish arguments from retail")
    bear_arguments: List[str] = Field(description="Main bearish arguments from retail")
    confidence: float = Field(description="Confidence 0-1", ge=0, le=1)


class TavilySentimentTrackerAgent:
    """
    Tracks retail sentiment from social media and forums

    Data Sources (via Tavily):
    - Reddit (r/wallstreetbets, r/stocks, r/investing)
    - StockTwits
    - Twitter/X
    - Seeking Alpha comments
    """

    def __init__(self, tavily_api_key: str, llm: ChatOpenAI, cache=None):
        self.tavily = TavilyClient(api_key=tavily_api_key)
        self.llm = llm
        self.name = "TavilySentimentTrackerAgent"
        self.cache = cache  # Optional TavilyCache instance

        # Use GPT-3.5 for cost efficiency
        self.summary_llm = ChatOpenAI(
            model="gpt-3.5-turbo",
            temperature=0.2,
            max_tokens=400
        )

    async def track(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Track social sentiment (alias for analyze method to match workflow expectations)

        Args:
            context: Analysis context dict

        Returns:
            Sentiment analysis results
        """
        return await self.analyze(context)

    async def analyze(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Analyze retail/social sentiment

        Args:
            context: {
                'symbol': str,
                'market_data': dict,
                'news_sentiment': dict (from NewsIntelligenceAgent if available)
            }

        Returns:
            {
                'agent': str,
                'social_data': dict,
                'sentiment_pulse': dict,
                'divergence_score': float (vs professional sentiment)
            }
        """
        symbol = context.get('symbol', 'UNKNOWN')
        logger.info(f"[{self.name}] Tracking social sentiment for {symbol}")

        try:
            # Step 1: Search social platforms
            social_results = await self._search_social_media(symbol)

            if not social_results or not social_results.get('results'):
                logger.warning(f"[{self.name}] No social data found for {symbol}")
                return self._empty_result(symbol)

            # Step 2: Analyze sentiment
            sentiment_pulse = await self._analyze_social_sentiment(symbol, social_results)

            # Step 3: Check divergence with professional sentiment
            divergence = self._calculate_sentiment_divergence(
                retail_sentiment=sentiment_pulse.retail_score,
                news_sentiment=context.get('news_sentiment', {}).get('score', 0)
            )

            result = {
                'agent': self.name,
                'symbol': symbol,
                'social_data': {
                    'sources': social_results.get('results', [])[:10],
                    'total_mentions': len(social_results.get('results', [])),
                    'platforms': self._extract_platforms(social_results.get('results', []))
                },
                'sentiment_pulse': {
                    'retail_sentiment': sentiment_pulse.retail_sentiment,
                    'score': sentiment_pulse.retail_score,
                    'volume': sentiment_pulse.social_volume,
                    'trending': sentiment_pulse.trending,
                    'confidence': sentiment_pulse.confidence
                },
                'bull_arguments': sentiment_pulse.bull_arguments,
                'bear_arguments': sentiment_pulse.bear_arguments,
                'divergence_score': divergence,
                'data_lineage': {
                    'source_type': 'Professional Financial Media + Social Platforms',
                    'search_api': 'Tavily Advanced Search',
                    'query': f"${symbol} stock sentiment analysis latest today discussion opinion 2025",
                    'time_range': 'Last 24 hours',
                    'domains_searched': ['seekingalpha.com', 'benzinga.com', 'marketwatch.com', 'barrons.com', 'investors.com', 'fool.com', 'investing.com', 'stocktwits.com', 'twitter.com'],
                    'results_retrieved': len(social_results.get('results', [])),
                    'quality_tier': 'Professional (no Reddit)',
                    'model': 'GPT-3.5 for sentiment analysis'
                },
                'timestamp': datetime.utcnow().isoformat()
            }

            logger.info(
                f"[{self.name}] Sentiment tracked: {sentiment_pulse.retail_sentiment} "
                f"(score: {sentiment_pulse.retail_score:.2f}, volume: {sentiment_pulse.social_volume})"
            )

            return result

        except Exception as e:
            logger.error(f"[{self.name}] Error tracking sentiment: {e}", exc_info=True)
            return self._error_result(symbol, str(e))

    async def _search_social_media(self, symbol: str) -> Dict[str, Any]:
        """Search social platforms via Tavily - UPDATED with fresh professional sources"""
        try:
            # UPDATED: Use recency-focused query with professional sources
            # CRITICAL FIX: Changed from 3 days to 1 day, added professional sources
            results = await asyncio.to_thread(
                self.tavily.search,
                query=f"${symbol} stock sentiment analysis latest today discussion opinion 2025",
                search_depth="advanced",
                max_results=25,
                days=1,  # CRITICAL: Only last 24 hours for freshness (was 3 days)
                include_domains=[
                    # Professional financial sources (prioritized over Reddit)
                    "seekingalpha.com",
                    "benzinga.com",
                    "marketwatch.com",
                    "barrons.com",
                    "investors.com",
                    "fool.com",
                    "investing.com",
                    # Social/Retail sources (secondary)
                    "stocktwits.com",
                    "twitter.com",
                    "x.com",
                    # Reddit removed from primary sources (too stale/low quality)
                ],
                include_answer=True
            )

            logger.info(f"[{self.name}] Retrieved {len(results.get('results', []))} recent sentiment sources (last 24h)")
            return results

        except Exception as e:
            logger.error(f"[{self.name}] Social media search failed: {e}")
            return {}

    async def _analyze_social_sentiment(self, symbol: str, social_results: Dict) -> SentimentPulse:
        """Analyze social sentiment with GPT-3.5"""
        try:
            discussions_text = self._format_discussions(social_results.get('results', []))

            prompt = f"""Analyze retail investor sentiment for ${symbol} from social media:

SOCIAL DISCUSSIONS:
{discussions_text}

Provide:
1. Retail sentiment (bullish/neutral/bearish)
2. Sentiment score (-1=very bearish, 0=neutral, 1=very bullish)
3. Social volume (high/medium/low based on discussion frequency)
4. Trending (true if unusually high activity)
5. Top 2-3 bullish arguments retail investors are making
6. Top 2-3 bearish arguments retail investors are making
7. Confidence (0-1)

Return as JSON:
{{
    "retail_sentiment": "bullish|neutral|bearish",
    "retail_score": -1 to 1,
    "social_volume": "high|medium|low",
    "trending": true|false,
    "bull_arguments": ["arg1", "arg2"],
    "bear_arguments": ["arg1", "arg2"],
    "confidence": 0 to 1
}}"""

            response = await self.summary_llm.ainvoke(prompt)

            # Parse response
            import json
            try:
                data = json.loads(response.content)
                return SentimentPulse(**data)
            except json.JSONDecodeError:
                logger.warning(f"[{self.name}] JSON parse failed, using fallback")
                return self._fallback_sentiment(discussions_text, len(social_results.get('results', [])))

        except Exception as e:
            logger.error(f"[{self.name}] Sentiment analysis failed: {e}")
            return SentimentPulse(
                retail_sentiment="neutral",
                retail_score=0,
                social_volume="low",
                trending=False,
                bull_arguments=[],
                bear_arguments=[],
                confidence=0.3
            )

    def _format_discussions(self, discussions: List[Dict]) -> str:
        """Format social discussions for LLM"""
        formatted = []
        for i, post in enumerate(discussions[:8], 1):  # Top 8
            formatted.append(
                f"{i}. {post.get('title', 'Untitled')}\n"
                f"   Platform: {self._extract_platform_name(post.get('url', ''))}\n"
                f"   Content: {post.get('content', '')[:150]}..."
            )
        return "\n\n".join(formatted)

    def _extract_platform_name(self, url: str) -> str:
        """Extract platform name from URL - UPDATED with professional sources"""
        # Professional financial platforms (prioritized display)
        if 'seekingalpha.com' in url:
            return 'Seeking Alpha'
        elif 'benzinga.com' in url:
            return 'Benzinga'
        elif 'marketwatch.com' in url:
            return 'MarketWatch'
        elif 'barrons.com' in url:
            return "Barron's"
        elif 'investors.com' in url:
            return "Investor's Business Daily"
        elif 'fool.com' in url:
            return 'Motley Fool'
        elif 'investing.com' in url:
            return 'Investing.com'
        # Social/Retail platforms
        elif 'stocktwits.com' in url:
            return 'StockTwits'
        elif 'twitter.com' in url or 'x.com' in url:
            return 'Twitter/X'
        elif 'reddit.com' in url:
            return 'Reddit'
        else:
            return 'Financial Media'

    def _extract_platforms(self, results: List[Dict]) -> List[str]:
        """Get list of platforms where discussion found"""
        platforms = set()
        for result in results:
            platform = self._extract_platform_name(result.get('url', ''))
            platforms.add(platform)
        return list(platforms)

    def _fallback_sentiment(self, text: str, result_count: int) -> SentimentPulse:
        """Rule-based fallback"""
        text_lower = text.lower()

        # Keyword counting
        bullish_kw = ['buy', 'moon', 'rocket', 'bull', 'calls', 'long', 'yolo']
        bearish_kw = ['sell', 'puts', 'short', 'bearish', 'crash', 'dump']

        bull_count = sum(1 for kw in bullish_kw if kw in text_lower)
        bear_count = sum(1 for kw in bearish_kw if kw in text_lower)

        if bull_count > bear_count + 3:
            sentiment = "bullish"
            score = 0.7
        elif bear_count > bull_count + 3:
            sentiment = "bearish"
            score = -0.7
        else:
            sentiment = "neutral"
            score = 0.0

        # Volume based on result count
        if result_count > 15:
            volume = "high"
            trending = True
        elif result_count > 5:
            volume = "medium"
            trending = False
        else:
            volume = "low"
            trending = False

        return SentimentPulse(
            retail_sentiment=sentiment,
            retail_score=score,
            social_volume=volume,
            trending=trending,
            bull_arguments=["Active retail discussion"] if bull_count > 0 else [],
            bear_arguments=["Retail caution detected"] if bear_count > 0 else [],
            confidence=0.5
        )

    def _calculate_sentiment_divergence(self, retail_sentiment: float, news_sentiment: float) -> float:
        """
        Calculate divergence between retail and professional sentiment

        High divergence = interesting signal (retail vs Wall Street disagree)

        Returns:
            float 0-1: divergence score
        """
        divergence = abs(retail_sentiment - news_sentiment)
        return round(min(1.0, divergence), 3)

    def _empty_result(self, symbol: str) -> Dict[str, Any]:
        """Empty result when no social data"""
        return {
            'agent': self.name,
            'symbol': symbol,
            'social_data': {'sources': [], 'total_mentions': 0, 'platforms': []},
            'sentiment_pulse': {
                'retail_sentiment': 'neutral',
                'score': 0,
                'volume': 'low',
                'trending': False,
                'confidence': 0
            },
            'bull_arguments': [],
            'bear_arguments': [],
            'divergence_score': 0.0,
            'timestamp': datetime.utcnow().isoformat()
        }

    def _error_result(self, symbol: str, error: str) -> Dict[str, Any]:
        """Error result"""
        result = self._empty_result(symbol)
        result['error'] = error
        result['status'] = 'failed'
        return result
