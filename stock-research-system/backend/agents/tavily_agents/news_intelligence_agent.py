"""
Tavily News Intelligence Agent
Uses Tavily Search API to fetch real-time breaking news and market events
Runs AFTER base analysis to enrich with latest market intelligence
"""

import logging
from typing import Dict, Any, List, Optional
from datetime import datetime
import asyncio

from tavily import TavilyClient
from langchain_openai import ChatOpenAI
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)


class NewsInsight(BaseModel):
    """Structured news analysis output"""
    sentiment: str = Field(description="Overall news sentiment: bullish/neutral/bearish")
    sentiment_score: float = Field(description="Sentiment score -1 to 1", ge=-1, le=1)
    key_events: List[str] = Field(description="Major events affecting the stock")
    catalysts: List[str] = Field(description="Positive catalysts identified")
    risks: List[str] = Field(description="Risk factors from news")
    analyst_actions: List[str] = Field(description="Recent analyst upgrades/downgrades")
    confidence: float = Field(description="Confidence in analysis 0-1", ge=0, le=1)


class TavilyNewsIntelligenceAgent:
    """
    Tavily-powered news intelligence agent

    Architecture:
    1. Search Tavily for breaking news (last 7 days)
    2. Extract structured data from top financial sources
    3. Use GPT-3.5 to analyze sentiment and extract events
    4. Return enrichment data (does NOT replace base analysis)
    """

    def __init__(self, tavily_api_key: str, llm: ChatOpenAI, cache=None, router=None):
        self.tavily = TavilyClient(api_key=tavily_api_key)
        self.llm = llm
        self.name = "TavilyNewsIntelligenceAgent"
        self.cache = cache  # Optional TavilyCache instance
        self.router = router  # Optional SmartModelRouter


        # Use router if available for smart model selection
        if router:
            self.summary_llm = router.get_model('news_summary')
        else:
            self.summary_llm = ChatOpenAI(
                model="gpt-3.5-turbo",
                temperature=0.1,
                max_tokens=500
            )

    async def analyze(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Analyze breaking news for a symbol

        Args:
            context: {
                'symbol': str,
                'market_data': dict (from base analysis),
                'base_recommendation': str (from existing agents)
            }

        Returns:
            {
                'agent': str,
                'news_data': dict,
                'sentiment': dict,
                'enrichment_score': float (0-1, how much this changes base analysis)
            }
        """
        symbol = context.get('symbol', 'UNKNOWN')
        logger.info(f"[{self.name}] Starting news intelligence for {symbol}")

        try:
            # Step 1: Search Tavily for recent news
            news_results = await self._search_breaking_news(symbol)

            if not news_results or not news_results.get('results'):
                logger.warning(f"[{self.name}] No news found for {symbol}")
                return self._empty_result(symbol)

            # Step 2: Analyze news with GPT-3.5
            news_analysis = await self._analyze_news_sentiment(symbol, news_results)

            # Step 3: Calculate enrichment score
            enrichment_score = self._calculate_enrichment_impact(
                news_analysis,
                context.get('base_recommendation', 'HOLD')
            )

            result = {
                'agent': self.name,
                'symbol': symbol,
                'news_data': {
                    'sources': news_results.get('results', [])[:5],  # Top 5 articles
                    'search_summary': news_results.get('answer', ''),
                    'total_articles': len(news_results.get('results', []))
                },
                'sentiment': {
                    'overall': news_analysis.sentiment,
                    'score': news_analysis.sentiment_score,
                    'confidence': news_analysis.confidence
                },
                'key_events': news_analysis.key_events,
                'catalysts': news_analysis.catalysts,
                'risks': news_analysis.risks,
                'analyst_actions': news_analysis.analyst_actions,
                'enrichment_score': enrichment_score,
                'data_lineage': {
                    'source_type': 'Premium Financial News',
                    'search_api': 'Tavily News Search',
                    'query': f"${symbol} stock news latest earnings analyst upgrades downgrades",
                    'time_range': 'Last 7 days',
                    'domains_searched': ['bloomberg.com', 'reuters.com', 'wsj.com', 'ft.com', 'cnbc.com', 'marketwatch.com', 'seekingalpha.com', 'benzinga.com'],
                    'articles_analyzed': len(news_results.get('results', [])),
                    'quality_tier': 'Premium',
                    'analysis_model': 'GPT-3.5 Turbo'
                },
                'timestamp': datetime.utcnow().isoformat()
            }

            logger.info(
                f"[{self.name}] Analysis complete: {news_analysis.sentiment} "
                f"sentiment (score: {news_analysis.sentiment_score:.2f})"
            )

            return result

        except Exception as e:
            logger.error(f"[{self.name}] Error analyzing news: {e}", exc_info=True)
            return self._error_result(symbol, str(e))

    async def _search_breaking_news(self, symbol: str) -> Dict[str, Any]:
        """Search Tavily for breaking news (with caching)"""
        try:
            # Prepare search params
            search_params = {
                'query': f"{symbol} stock news earnings announcement analyst upgrade downgrade",
                'search_depth': 'advanced',
                'max_results': 15,
                'days': 7,
                'domains': ['reuters.com', 'bloomberg.com', 'cnbc.com', 'wsj.com',
                           'marketwatch.com', 'seekingalpha.com']
            }

            # Try cache first
            if self.cache:
                cached = await self.cache.get('news', symbol, search_params)
                if cached:
                    logger.info(f"[{self.name}] Using cached news for {symbol}")
                    return cached

            # Cache miss - call Tavily API
            results = await asyncio.to_thread(
                self.tavily.search,
                query=search_params['query'],
                search_depth=search_params['search_depth'],
                max_results=search_params['max_results'],
                days=search_params['days'],
                include_domains=search_params['domains'],
                include_answer=True,
                include_raw_content=False
            )

            # Store in cache (24h TTL for news)
            if self.cache and results:
                await self.cache.set('news', symbol, search_params, results, ttl_hours=24)

            return results

        except Exception as e:
            logger.error(f"[{self.name}] Tavily search failed: {e}")
            return {}

    async def _analyze_news_sentiment(self, symbol: str, news_results: Dict) -> NewsInsight:
        """Analyze news sentiment using GPT-3.5"""
        try:
            articles_text = self._format_articles(news_results.get('results', []))

            prompt = f"""Analyze this financial news for {symbol} and provide structured insights:

NEWS ARTICLES:
{articles_text}

Analyze and return:
1. Overall sentiment (bullish/neutral/bearish)
2. Sentiment score (-1 to 1, where -1=very bearish, 0=neutral, 1=very bullish)
3. Key events (max 3 most important)
4. Positive catalysts (bullish factors)
5. Risk factors (bearish factors)
6. Analyst actions (upgrades/downgrades mentioned)
7. Confidence in your analysis (0-1)

Be concise and focus on market-moving events only.

Return as JSON with this schema:
{{
    "sentiment": "bullish|neutral|bearish",
    "sentiment_score": -1 to 1,
    "key_events": ["event1", "event2"],
    "catalysts": ["catalyst1"],
    "risks": ["risk1"],
    "analyst_actions": ["action1"],
    "confidence": 0 to 1
}}"""

            response = await self.summary_llm.ainvoke(prompt)

            # Parse JSON response
            import json
            try:
                data = json.loads(response.content)
                return NewsInsight(**data)
            except json.JSONDecodeError:
                # Fallback parsing
                logger.warning(f"[{self.name}] Failed to parse JSON, using fallback")
                return self._fallback_sentiment_analysis(articles_text)

        except Exception as e:
            logger.error(f"[{self.name}] Sentiment analysis failed: {e}")
            return NewsInsight(
                sentiment="neutral",
                sentiment_score=0,
                key_events=[],
                catalysts=[],
                risks=[],
                analyst_actions=[],
                confidence=0.3
            )

    def _format_articles(self, articles: List[Dict]) -> str:
        """Format articles for LLM analysis"""
        formatted = []
        for i, article in enumerate(articles[:5], 1):  # Top 5 only
            formatted.append(
                f"{i}. {article.get('title', 'Untitled')}\n"
                f"   Source: {article.get('url', 'N/A')}\n"
                f"   Content: {article.get('content', '')[:200]}..."
            )
        return "\n\n".join(formatted)

    def _fallback_sentiment_analysis(self, articles_text: str) -> NewsInsight:
        """Simple rule-based fallback if LLM parsing fails"""
        text_lower = articles_text.lower()

        # Simple keyword-based sentiment
        bullish_keywords = ['upgrade', 'beat', 'surge', 'rally', 'growth', 'buy', 'positive']
        bearish_keywords = ['downgrade', 'miss', 'plunge', 'decline', 'sell', 'negative', 'warning']

        bullish_count = sum(1 for kw in bullish_keywords if kw in text_lower)
        bearish_count = sum(1 for kw in bearish_keywords if kw in text_lower)

        if bullish_count > bearish_count + 2:
            sentiment = "bullish"
            score = 0.6
        elif bearish_count > bullish_count + 2:
            sentiment = "bearish"
            score = -0.6
        else:
            sentiment = "neutral"
            score = 0.0

        return NewsInsight(
            sentiment=sentiment,
            sentiment_score=score,
            key_events=["News analysis available"],
            catalysts=[] if score <= 0 else ["Positive news detected"],
            risks=[] if score >= 0 else ["Negative news detected"],
            analyst_actions=[],
            confidence=0.4  # Lower confidence for fallback
        )

    def _calculate_enrichment_impact(self, news_analysis: NewsInsight, base_recommendation: str) -> float:
        """
        Calculate how much this news changes the base recommendation

        Returns:
            float 0-1: enrichment score
            - 0.0 = news confirms base analysis (no change)
            - 0.5 = news adds new information
            - 1.0 = news contradicts base analysis (significant change)
        """
        # Map recommendations to scores
        rec_scores = {'STRONG_SELL': -1, 'SELL': -0.5, 'HOLD': 0, 'BUY': 0.5, 'STRONG_BUY': 1}
        base_score = rec_scores.get(base_recommendation, 0)

        # Compare with news sentiment
        news_score = news_analysis.sentiment_score

        # Calculate divergence
        divergence = abs(base_score - news_score)

        # Higher divergence = more impact
        enrichment = min(1.0, divergence * news_analysis.confidence)

        return round(enrichment, 3)

    def _empty_result(self, symbol: str) -> Dict[str, Any]:
        """Return empty result when no news found"""
        return {
            'agent': self.name,
            'symbol': symbol,
            'news_data': {'sources': [], 'total_articles': 0},
            'sentiment': {'overall': 'neutral', 'score': 0, 'confidence': 0},
            'key_events': [],
            'catalysts': [],
            'risks': [],
            'analyst_actions': [],
            'enrichment_score': 0.0,
            'timestamp': datetime.utcnow().isoformat()
        }

    def _error_result(self, symbol: str, error: str) -> Dict[str, Any]:
        """Return error result"""
        result = self._empty_result(symbol)
        result['error'] = error
        result['status'] = 'failed'
        return result
