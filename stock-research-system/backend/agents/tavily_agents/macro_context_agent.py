"""
Tavily Macro Context Agent
Uses Tavily Search to analyze market-wide factors affecting individual stocks
Provides sector trends, economic indicators, and Fed policy context
"""

import logging
from typing import Dict, Any, List
from datetime import datetime
import asyncio

from tavily import TavilyClient
from langchain_openai import ChatOpenAI
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)


class MacroOverlay(BaseModel):
    """Structured macro analysis output"""
    market_regime: str = Field(description="Current market regime: bull/bear/neutral/volatile")
    market_score: float = Field(description="Market favorability score -1 to 1", ge=-1, le=1)
    sector_trend: str = Field(description="Sector performance: outperforming/inline/underperforming")
    sector_rotation: bool = Field(description="Whether sector rotation is occurring")
    fed_policy: str = Field(description="Fed stance: hawkish/neutral/dovish")
    economic_indicators: List[str] = Field(description="Key economic factors affecting stock")
    macro_catalysts: List[str] = Field(description="Macro tailwinds")
    macro_headwinds: List[str] = Field(description="Macro risks")
    confidence: float = Field(description="Confidence 0-1", ge=0, le=1)


class MacroContextAgent:
    """
    Analyzes macro market conditions and sector trends

    Data Sources (via Tavily):
    - Federal Reserve news and policy signals
    - Sector performance and rotation patterns
    - Economic indicators (inflation, employment, GDP)
    - Market sentiment and volatility indicators
    """

    def __init__(self, tavily_api_key: str, llm: ChatOpenAI, cache=None):
        self.tavily = TavilyClient(api_key=tavily_api_key)
        self.llm = llm
        self.name = "MacroContextAgent"
        self.cache = cache  # Optional TavilyCache instance

        # Use GPT-3.5 for cost efficiency
        self.summary_llm = ChatOpenAI(
            model="gpt-3.5-turbo",
            temperature=0.2,
            max_tokens=500
        )

    async def analyze(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Analyze macro context for a symbol

        Args:
            context: {
                'symbol': str,
                'sector': str (e.g., 'Technology', 'Healthcare'),
                'market_data': dict,
                'base_recommendation': str
            }

        Returns:
            {
                'agent': str,
                'macro_data': dict,
                'market_regime': dict,
                'sector_analysis': dict,
                'context_score': float (how much macro helps/hurts the stock)
            }
        """
        symbol = context.get('symbol', 'UNKNOWN')
        sector = context.get('sector', 'General')
        logger.info(f"[{self.name}] Analyzing macro context for {symbol} ({sector})")

        try:
            # Step 1: Search for macro factors
            macro_results = await self._search_macro_factors(symbol, sector)

            if not macro_results or not macro_results.get('results'):
                logger.warning(f"[{self.name}] No macro data found for {symbol}")
                return self._empty_result(symbol)

            # Step 2: Analyze macro overlay
            macro_analysis = await self._analyze_macro_overlay(symbol, sector, macro_results)

            # Step 3: Calculate context score (macro impact on stock)
            context_score = self._calculate_macro_impact(
                macro_analysis,
                context.get('base_recommendation', 'HOLD')
            )

            result = {
                'agent': self.name,
                'symbol': symbol,
                'macro_data': {
                    'sources': macro_results.get('results', [])[:5],  # Top 5
                    'search_summary': macro_results.get('answer', ''),
                    'total_sources': len(macro_results.get('results', []))
                },
                'market_regime': {
                    'regime': macro_analysis.market_regime,
                    'score': macro_analysis.market_score,
                    'fed_policy': macro_analysis.fed_policy
                },
                'sector_analysis': {
                    'trend': macro_analysis.sector_trend,
                    'rotation': macro_analysis.sector_rotation
                },
                'economic_indicators': macro_analysis.economic_indicators,
                'catalysts': macro_analysis.macro_catalysts,
                'headwinds': macro_analysis.macro_headwinds,
                'context_score': context_score,
                'confidence': macro_analysis.confidence,
                'timestamp': datetime.utcnow().isoformat()
            }

            logger.info(
                f"[{self.name}] Analysis complete: {macro_analysis.market_regime} market, "
                f"{macro_analysis.sector_trend} sector (score: {context_score:.2f})"
            )

            return result

        except Exception as e:
            logger.error(f"[{self.name}] Error analyzing macro context: {e}", exc_info=True)
            return self._error_result(symbol, str(e))

    async def _search_macro_factors(self, symbol: str, sector: str) -> Dict[str, Any]:
        """Search Tavily for macro and sector data"""
        try:
            # Search for macro factors affecting the sector/stock
            results = await asyncio.to_thread(
                self.tavily.search,
                query=f"{sector} sector trends Federal Reserve policy inflation GDP economic indicators {symbol}",
                search_depth="advanced",
                max_results=15,
                days=14,  # Last 2 weeks for macro trends
                include_domains=[
                    "federalreserve.gov",
                    "reuters.com",
                    "bloomberg.com",
                    "cnbc.com",
                    "wsj.com",
                    "marketwatch.com",
                    "bls.gov",
                    "bea.gov"
                ],
                include_answer=True
            )

            return results

        except Exception as e:
            logger.error(f"[{self.name}] Macro search failed: {e}")
            return {}

    async def _analyze_macro_overlay(self, symbol: str, sector: str,
                                     macro_results: Dict) -> MacroOverlay:
        """Analyze macro context with GPT-3.5"""
        try:
            macro_text = self._format_macro_data(macro_results.get('results', []))

            prompt = f"""Analyze macro market conditions for ${symbol} ({sector} sector):

MACRO & SECTOR DATA:
{macro_text}

Provide comprehensive macro overlay:

1. Market Regime: Current overall market condition (bull/bear/neutral/volatile)
2. Market Score: -1 (very bearish) to 1 (very bullish) based on macro conditions
3. Sector Trend: Is {sector} sector outperforming/inline/underperforming the market?
4. Sector Rotation: Is money rotating into or out of {sector}?
5. Fed Policy: Current Federal Reserve stance (hawkish/neutral/dovish)
6. Economic Indicators: Key economic factors affecting {sector} (max 3)
7. Macro Catalysts: Positive macro factors for {sector} (max 3)
8. Macro Headwinds: Negative macro factors for {sector} (max 3)
9. Confidence: How confident in this macro analysis (0-1)

Return as JSON:
{{
    "market_regime": "bull|bear|neutral|volatile",
    "market_score": -1 to 1,
    "sector_trend": "outperforming|inline|underperforming",
    "sector_rotation": true|false,
    "fed_policy": "hawkish|neutral|dovish",
    "economic_indicators": ["indicator1", "indicator2"],
    "macro_catalysts": ["catalyst1"],
    "macro_headwinds": ["headwind1"],
    "confidence": 0 to 1
}}"""

            response = await self.summary_llm.ainvoke(prompt)

            # Parse JSON response
            import json
            try:
                data = json.loads(response.content)
                return MacroOverlay(**data)
            except json.JSONDecodeError:
                logger.warning(f"[{self.name}] JSON parse failed, using fallback")
                return self._fallback_macro_analysis(macro_text, sector)

        except Exception as e:
            logger.error(f"[{self.name}] Macro analysis failed: {e}")
            return MacroOverlay(
                market_regime="neutral",
                market_score=0,
                sector_trend="inline",
                sector_rotation=False,
                fed_policy="neutral",
                economic_indicators=[],
                macro_catalysts=[],
                macro_headwinds=[],
                confidence=0.3
            )

    def _format_macro_data(self, sources: List[Dict]) -> str:
        """Format macro sources for LLM"""
        formatted = []
        for i, source in enumerate(sources[:8], 1):  # Top 8
            formatted.append(
                f"{i}. {source.get('title', 'Untitled')}\n"
                f"   Source: {self._extract_source_name(source.get('url', ''))}\n"
                f"   Content: {source.get('content', '')[:200]}..."
            )
        return "\n\n".join(formatted)

    def _extract_source_name(self, url: str) -> str:
        """Extract source name from URL"""
        if 'federalreserve.gov' in url:
            return 'Federal Reserve'
        elif 'bls.gov' in url:
            return 'Bureau of Labor Statistics'
        elif 'bea.gov' in url:
            return 'Bureau of Economic Analysis'
        elif 'reuters.com' in url:
            return 'Reuters'
        elif 'bloomberg.com' in url:
            return 'Bloomberg'
        elif 'wsj.com' in url:
            return 'Wall Street Journal'
        else:
            return 'Financial Source'

    def _fallback_macro_analysis(self, text: str, sector: str) -> MacroOverlay:
        """Rule-based fallback if LLM fails"""
        text_lower = text.lower()

        # Market regime detection
        bull_kw = ['rally', 'growth', 'expansion', 'strong economy', 'optimistic']
        bear_kw = ['recession', 'contraction', 'downturn', 'weak', 'pessimistic']

        bull_count = sum(1 for kw in bull_kw if kw in text_lower)
        bear_count = sum(1 for kw in bear_kw if kw in text_lower)

        if bull_count > bear_count + 2:
            regime = "bull"
            score = 0.6
        elif bear_count > bull_count + 2:
            regime = "bear"
            score = -0.6
        else:
            regime = "neutral"
            score = 0.0

        # Fed policy detection
        if 'rate hike' in text_lower or 'hawkish' in text_lower:
            fed_policy = "hawkish"
        elif 'rate cut' in text_lower or 'dovish' in text_lower:
            fed_policy = "dovish"
        else:
            fed_policy = "neutral"

        return MacroOverlay(
            market_regime=regime,
            market_score=score,
            sector_trend="inline",
            sector_rotation=False,
            fed_policy=fed_policy,
            economic_indicators=["Macro data available"],
            macro_catalysts=["Economic growth"] if score > 0 else [],
            macro_headwinds=["Economic headwinds"] if score < 0 else [],
            confidence=0.4
        )

    def _calculate_macro_impact(self, macro_analysis: MacroOverlay,
                                base_recommendation: str) -> float:
        """
        Calculate how macro context affects the stock

        Returns:
            float -1 to 1:
            - Positive = macro helps the stock (tailwind)
            - Negative = macro hurts the stock (headwind)
            - 0 = macro neutral
        """
        # Map recommendations to scores
        rec_scores = {'STRONG_SELL': -1, 'SELL': -0.5, 'HOLD': 0,
                     'BUY': 0.5, 'STRONG_BUY': 1}
        base_score = rec_scores.get(base_recommendation, 0)

        # Calculate macro alignment
        macro_score = macro_analysis.market_score

        # If both positive or both negative = reinforcing (positive impact)
        # If opposing signs = conflicting (negative impact)
        if base_score * macro_score > 0:
            # Same direction = macro helps
            impact = abs(macro_score) * macro_analysis.confidence
        elif base_score * macro_score < 0:
            # Opposite direction = macro hurts
            impact = -abs(macro_score) * macro_analysis.confidence
        else:
            # Neutral
            impact = 0.0

        return round(impact, 3)

    def _empty_result(self, symbol: str) -> Dict[str, Any]:
        """Empty result when no macro data"""
        return {
            'agent': self.name,
            'symbol': symbol,
            'macro_data': {'sources': [], 'total_sources': 0},
            'market_regime': {'regime': 'neutral', 'score': 0, 'fed_policy': 'neutral'},
            'sector_analysis': {'trend': 'inline', 'rotation': False},
            'economic_indicators': [],
            'catalysts': [],
            'headwinds': [],
            'context_score': 0.0,
            'confidence': 0,
            'timestamp': datetime.utcnow().isoformat()
        }

    def _error_result(self, symbol: str, error: str) -> Dict[str, Any]:
        """Error result"""
        result = self._empty_result(symbol)
        result['error'] = error
        result['status'] = 'failed'
        return result
