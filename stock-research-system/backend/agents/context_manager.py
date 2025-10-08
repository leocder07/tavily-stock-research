"""
Context Manager for Enhanced LLM Analysis
Provides rich, structured context to LLMs for better stock analysis
"""

import json
from typing import Dict, Any, List, Optional
from enum import Enum
import logging

logger = logging.getLogger(__name__)


class AnalysisPersona(Enum):
    """Different investment analysis personas"""
    WARREN_BUFFETT = "value_investor"
    JIM_SIMONS = "quantitative_analyst"
    PETER_LYNCH = "growth_investor"
    RAY_DALIO = "macro_strategist"
    CATHIE_WOOD = "innovation_focused"
    DEFAULT = "balanced_analyst"


class ContextManager:
    """Manages and structures context for LLM analysis"""

    def __init__(self, max_tokens: int = 3000):
        self.max_tokens = max_tokens
        self.persona_prompts = self._initialize_personas()

    def _initialize_personas(self) -> Dict[str, str]:
        """Initialize persona-specific system prompts"""
        return {
            AnalysisPersona.WARREN_BUFFETT: """
You are analyzing stocks through the lens of Warren Buffett's value investing philosophy.
Focus on: intrinsic value, economic moats, management quality, long-term competitive advantages,
margin of safety, and businesses you can understand. Emphasize DCF analysis, book value,
and sustainable earnings power. Be skeptical of high valuations without strong fundamentals.
            """,

            AnalysisPersona.JIM_SIMONS: """
You are analyzing stocks using quantitative and technical analysis like Jim Simons.
Focus on: statistical patterns, technical indicators, momentum signals, mean reversion,
volatility patterns, and mathematical models. Use RSI, MACD, Bollinger Bands, and
pattern recognition. Identify entry/exit points based on technical signals.
            """,

            AnalysisPersona.PETER_LYNCH: """
You are analyzing stocks with Peter Lynch's growth at a reasonable price (GARP) approach.
Focus on: PEG ratios, earnings growth, market opportunity, competitive position,
and finding tenbaggers. Look for companies growing faster than their P/E suggests.
Balance growth potential with reasonable valuation.
            """,

            AnalysisPersona.RAY_DALIO: """
You are analyzing stocks through Ray Dalio's macro and risk-parity lens.
Focus on: economic cycles, debt cycles, currency impacts, correlation with other assets,
systematic risks, and portfolio diversification benefits. Consider global macro trends
and how they affect the company.
            """,

            AnalysisPersona.CATHIE_WOOD: """
You are analyzing stocks focusing on disruptive innovation like Cathie Wood.
Focus on: technological disruption potential, total addressable market expansion,
innovation trajectory, network effects, and exponential growth opportunities.
Look for companies reshaping industries through innovation.
            """,

            AnalysisPersona.DEFAULT: """
You are a balanced financial analyst providing comprehensive stock analysis.
Consider both fundamental and technical factors, short and long-term perspectives,
risks and opportunities. Provide actionable insights based on data.
            """
        }

    def build_context(
        self,
        symbol: str,
        market_data: Dict[str, Any],
        valuation: Optional[Dict[str, Any]] = None,
        technical: Optional[Dict[str, Any]] = None,
        competitive: Optional[Dict[str, Any]] = None,
        news: Optional[List[Dict]] = None,
        persona: AnalysisPersona = AnalysisPersona.DEFAULT
    ) -> Dict[str, Any]:
        """Build structured context for LLM analysis"""

        context = {
            "symbol": symbol,
            "persona": persona.value,
            "system_prompt": self.persona_prompts.get(persona, self.persona_prompts[AnalysisPersona.DEFAULT]),
            "structured_data": {}
        }

        # Add market data
        if market_data:
            context["structured_data"]["market_metrics"] = self._structure_market_data(market_data)

        # Add valuation analysis
        if valuation:
            context["structured_data"]["valuation_analysis"] = self._structure_valuation(valuation)

        # Add technical analysis
        if technical:
            context["structured_data"]["technical_analysis"] = self._structure_technical(technical)

        # Add competitive analysis
        if competitive:
            context["structured_data"]["competitive_position"] = self._structure_competitive(competitive)

        # Add news sentiment
        if news:
            context["structured_data"]["news_sentiment"] = self._structure_news(news)

        # Generate persona-specific prompt
        context["analysis_prompt"] = self._generate_analysis_prompt(context, persona)

        return context

    def _structure_market_data(self, market_data: Dict) -> Dict:
        """Structure market data for LLM consumption"""
        return {
            "current_price": market_data.get('price', 0),
            "daily_change": {
                "amount": market_data.get('change', 0),
                "percentage": market_data.get('changePercent', 0)
            },
            "volume": {
                "current": market_data.get('volume', 0),
                "average": market_data.get('avgVolume', 0),
                "relative": "above_average" if market_data.get('volume', 0) > market_data.get('avgVolume', 1) else "below_average"
            },
            "market_cap": market_data.get('marketCap', 0),
            "52_week": {
                "high": market_data.get('52WeekHigh', 0),
                "low": market_data.get('52WeekLow', 0),
                "current_position": self._calculate_52_week_position(market_data)
            },
            "key_ratios": {
                "pe_ratio": market_data.get('pe_ratio', 0),
                "peg_ratio": market_data.get('pegRatio', 0),
                "price_to_book": market_data.get('priceToBook', 0),
                "dividend_yield": market_data.get('dividendYield', 0)
            }
        }

    def _structure_valuation(self, valuation: Dict) -> Dict:
        """Structure valuation data for LLM consumption"""
        return {
            "price_targets": {
                "dcf_fair_value": valuation.get('dcf_valuation', {}).get('dcf_price', 0),
                "analyst_consensus": valuation.get('analyst_targets', {}).get('target_mean', 0),
                "weighted_target": valuation.get('price_target', {}).get('price_target', 0),
                "upside_potential": valuation.get('price_target', {}).get('upside', 0),
                "confidence_level": valuation.get('price_target', {}).get('confidence', 0)
            },
            "valuation_methods": {
                "dcf_analysis": {
                    "fair_value": valuation.get('dcf_valuation', {}).get('dcf_price', 0),
                    "wacc": valuation.get('dcf_valuation', {}).get('wacc', 0),
                    "terminal_growth": valuation.get('dcf_valuation', {}).get('terminal_growth_rate', 0)
                },
                "comparative_valuation": {
                    "pe_vs_peers": valuation.get('comparative_valuation', {}).get('pe_ratio', 0),
                    "valuation_rating": valuation.get('comparative_valuation', {}).get('valuation_rating', ''),
                    "comparative_price": valuation.get('comparative_valuation', {}).get('comparative_price', 0)
                }
            },
            "analyst_sentiment": {
                "consensus": valuation.get('analyst_targets', {}).get('analyst_consensus', ''),
                "number_of_analysts": valuation.get('analyst_targets', {}).get('number_of_analysts', 0),
                "target_range": {
                    "high": valuation.get('analyst_targets', {}).get('target_high', 0),
                    "low": valuation.get('analyst_targets', {}).get('target_low', 0)
                }
            }
        }

    def _structure_technical(self, technical: Dict) -> Dict:
        """Structure technical analysis for LLM consumption"""
        indicators = technical.get('indicators', {})
        patterns = technical.get('patterns', {})
        signals = technical.get('signals', {})

        return {
            "trend_analysis": {
                "primary_trend": signals.get('trend', 'NEUTRAL'),
                "trend_strength": signals.get('trend_strength', 'MODERATE'),
                "support_levels": technical.get('support_resistance', {}).get('support', []),
                "resistance_levels": technical.get('support_resistance', {}).get('resistance', [])
            },
            "momentum_indicators": {
                "rsi": {
                    "value": indicators.get('momentum', {}).get('rsi', 50),
                    "signal": self._interpret_rsi(indicators.get('momentum', {}).get('rsi', 50))
                },
                "macd": {
                    "histogram": indicators.get('trend', {}).get('macd', {}).get('histogram', 0),
                    "signal": indicators.get('trend', {}).get('macd', {}).get('signal_line', 0),
                    "crossover": indicators.get('trend', {}).get('macd', {}).get('crossover', False)
                },
                "stochastic": indicators.get('momentum', {}).get('stochastic', {})
            },
            "volatility_analysis": {
                "bollinger_bands": {
                    "upper": indicators.get('volatility', {}).get('bollinger', {}).get('upper', 0),
                    "lower": indicators.get('volatility', {}).get('bollinger', {}).get('lower', 0),
                    "position": indicators.get('volatility', {}).get('bollinger', {}).get('position', '')
                },
                "atr": indicators.get('volatility', {}).get('atr', 0)
            },
            "chart_patterns": {
                "identified_patterns": patterns.get('detected', []),
                "pattern_confidence": patterns.get('confidence', {}),
                "key_levels": patterns.get('key_levels', {})
            },
            "overall_signal": {
                "recommendation": signals.get('overall', 'NEUTRAL'),
                "buy_signals": signals.get('buy_signals', 0),
                "sell_signals": signals.get('sell_signals', 0),
                "signal_strength": signals.get('strength', 0)
            }
        }

    def _structure_competitive(self, competitive: Dict) -> Dict:
        """Structure competitive analysis for LLM consumption"""
        return {
            "market_position": {
                "market_share": competitive.get('market_analysis', {}).get('market_share', {}),
                "revenue_rank": competitive.get('market_analysis', {}).get('market_position', {}).get('revenue_rank', ''),
                "growth_rank": competitive.get('market_analysis', {}).get('market_position', {}).get('growth_rank', ''),
                "strategic_position": competitive.get('competitive_assessment', {}).get('strategic_position', '')
            },
            "competitive_advantages": {
                "moat_rating": competitive.get('competitive_assessment', {}).get('moat_analysis', {}).get('moat_rating', ''),
                "moat_factors": competitive.get('competitive_assessment', {}).get('moat_analysis', {}).get('moat_factors', []),
                "key_advantages": competitive.get('competitive_assessment', {}).get('competitive_advantages', [])
            },
            "peer_comparison": {
                "valuation_vs_peers": competitive.get('comparative_metrics', {}).get('valuation_vs_peers', {}),
                "operational_efficiency": competitive.get('comparative_metrics', {}).get('operational_efficiency', {}),
                "growth_comparison": competitive.get('comparative_metrics', {}).get('growth_comparison', {}),
                "composite_score": competitive.get('comparative_metrics', {}).get('composite_score', {})
            },
            "competitive_risks": competitive.get('competitive_assessment', {}).get('competitive_risks', [])
        }

    def _structure_news(self, news: List[Dict]) -> Dict:
        """Structure news data for LLM consumption"""
        if not news:
            return {"articles_analyzed": 0, "key_themes": [], "sentiment": "neutral"}

        return {
            "articles_analyzed": len(news),
            "recent_headlines": [article.get('title', '') for article in news[:3]],
            "key_themes": self._extract_news_themes(news),
            "sentiment": self._analyze_news_sentiment(news),
            "sources": list(set(article.get('source', 'unknown') for article in news if article.get('source')))
        }

    def _calculate_52_week_position(self, market_data: Dict) -> str:
        """Calculate where price sits in 52-week range"""
        current = market_data.get('price', 0)
        high = market_data.get('52WeekHigh', current)
        low = market_data.get('52WeekLow', current)

        if high == low:
            return "middle"

        position = (current - low) / (high - low)

        if position > 0.8:
            return "near_high"
        elif position < 0.2:
            return "near_low"
        else:
            return "middle_range"

    def _interpret_rsi(self, rsi: float) -> str:
        """Interpret RSI value"""
        if rsi > 70:
            return "overbought"
        elif rsi < 30:
            return "oversold"
        else:
            return "neutral"

    def _extract_news_themes(self, news: List[Dict]) -> List[str]:
        """Extract key themes from news articles"""
        themes = []
        keywords = ['earnings', 'growth', 'acquisition', 'partnership', 'innovation',
                   'regulation', 'competition', 'market share', 'product launch']

        for article in news:
            content = (article.get('title', '') + ' ' + article.get('content', '')).lower()
            for keyword in keywords:
                if keyword in content and keyword not in themes:
                    themes.append(keyword)

        return themes[:5]  # Return top 5 themes

    def _analyze_news_sentiment(self, news: List[Dict]) -> str:
        """Simple sentiment analysis based on keywords"""
        positive_words = ['growth', 'profit', 'beat', 'exceed', 'strong', 'gain', 'surge', 'rally']
        negative_words = ['loss', 'decline', 'miss', 'weak', 'fall', 'drop', 'concern', 'risk']

        positive_count = 0
        negative_count = 0

        for article in news:
            content = (article.get('title', '') + ' ' + article.get('content', '')).lower()
            positive_count += sum(1 for word in positive_words if word in content)
            negative_count += sum(1 for word in negative_words if word in content)

        if positive_count > negative_count * 1.5:
            return "positive"
        elif negative_count > positive_count * 1.5:
            return "negative"
        else:
            return "neutral"

    def _generate_analysis_prompt(self, context: Dict, persona: AnalysisPersona) -> str:
        """Generate persona-specific analysis prompt"""
        data = context["structured_data"]
        symbol = context["symbol"]

        base_prompt = f"""
Analyze {symbol} stock using the comprehensive data provided below.
{context['system_prompt']}

CURRENT MARKET DATA:
{json.dumps(data.get('market_metrics', {}), indent=2)}

VALUATION ANALYSIS:
{json.dumps(data.get('valuation_analysis', {}), indent=2)}

TECHNICAL INDICATORS:
{json.dumps(data.get('technical_analysis', {}), indent=2)}

COMPETITIVE POSITION:
{json.dumps(data.get('competitive_position', {}), indent=2)}

NEWS & SENTIMENT:
{json.dumps(data.get('news_sentiment', {}), indent=2)}

Based on this comprehensive data and your investment philosophy, provide:
1. Investment thesis (3-4 sentences)
2. Key opportunities (top 3)
3. Critical risks (top 3)
4. Price target and timeline
5. Actionable recommendation with confidence level
6. Specific entry/exit strategies if applicable
"""

        # Add persona-specific questions
        persona_specific = {
            AnalysisPersona.WARREN_BUFFETT: "\n\nSpecifically address: Is there a margin of safety? What is the intrinsic value? Does the company have a sustainable moat?",
            AnalysisPersona.JIM_SIMONS: "\n\nSpecifically address: What do the technical patterns suggest? Are there statistical arbitrage opportunities? What are the key support/resistance levels?",
            AnalysisPersona.PETER_LYNCH: "\n\nSpecifically address: Is this a potential tenbagger? How does the PEG ratio compare to growth rate? Is the story still intact?",
            AnalysisPersona.RAY_DALIO: "\n\nSpecifically address: How does this fit in the current economic cycle? What are the systematic risks? How would this perform in different economic scenarios?",
            AnalysisPersona.CATHIE_WOOD: "\n\nSpecifically address: What is the disruptive potential? How large could the TAM become? Is this riding a major innovation trend?"
        }

        if persona in persona_specific:
            base_prompt += persona_specific[persona]

        return base_prompt

    def get_token_estimate(self, context: Dict) -> int:
        """Estimate token count for context"""
        # Rough estimation: 1 token ≈ 4 characters
        context_str = json.dumps(context)
        return len(context_str) // 4

    def optimize_context(self, context: Dict, max_tokens: Optional[int] = None) -> Dict:
        """Optimize context to fit within token limits"""
        max_tokens = max_tokens or self.max_tokens

        current_tokens = self.get_token_estimate(context)
        if current_tokens <= max_tokens:
            return context

        # Progressive reduction strategy
        optimized = context.copy()

        # Level 1: Remove detailed patterns and indicators
        if current_tokens > max_tokens:
            if 'technical_analysis' in optimized.get('structured_data', {}):
                optimized['structured_data']['technical_analysis'] = {
                    'overall_signal': optimized['structured_data']['technical_analysis'].get('overall_signal', {}),
                    'trend_analysis': optimized['structured_data']['technical_analysis'].get('trend_analysis', {})
                }

        # Level 2: Summarize competitive data
        if self.get_token_estimate(optimized) > max_tokens:
            if 'competitive_position' in optimized.get('structured_data', {}):
                optimized['structured_data']['competitive_position'] = {
                    'market_position': optimized['structured_data']['competitive_position'].get('market_position', {}),
                    'competitive_advantages': {
                        'moat_rating': optimized['structured_data']['competitive_position'].get('competitive_advantages', {}).get('moat_rating', '')
                    }
                }

        # Level 3: Reduce news to sentiment only
        if self.get_token_estimate(optimized) > max_tokens:
            if 'news_sentiment' in optimized.get('structured_data', {}):
                optimized['structured_data']['news_sentiment'] = {
                    'sentiment': optimized['structured_data']['news_sentiment'].get('sentiment', 'neutral'),
                    'articles_analyzed': optimized['structured_data']['news_sentiment'].get('articles_analyzed', 0)
                }

        return optimized