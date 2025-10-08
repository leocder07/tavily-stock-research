"""
Expert Technical Analysis Agent
Chart pattern recognition + indicator analysis with GPT-4
Combines local calculations with AI pattern recognition
"""

import logging
from typing import Dict, Any, List
from datetime import datetime
import json

from langchain_openai import ChatOpenAI
from langchain.prompts import ChatPromptTemplate
from langchain.output_parsers import PydanticOutputParser
from pydantic import BaseModel, Field

from calculators.technical_calculator import TechnicalCalculator
from calculators.pattern_detector import PatternDetector
from agents.mixins.lineage_mixin import LineageMixin
from services.data_lineage_tracker import DataSource, DataReliability

logger = logging.getLogger(__name__)


class TechnicalInsight(BaseModel):
    """Structured technical analysis output"""
    trend_analysis: str = Field(description="Overall trend assessment")
    pattern_recognition: str = Field(description="Chart patterns identified")
    support_resistance_analysis: str = Field(description="Key levels analysis")
    momentum_assessment: str = Field(description="Momentum indicators interpretation")
    volume_analysis: str = Field(description="Volume pattern analysis")
    signal: str = Field(description="BUY, SELL, or HOLD")
    confidence_score: float = Field(description="Confidence 0-1")
    entry_exit_strategy: str = Field(description="Recommended entry/exit points")


class ExpertTechnicalAgent(LineageMixin):
    """
    Technical analysis expert using local calculations + GPT-4 pattern recognition
    """

    def __init__(self, llm: ChatOpenAI):
        self.name = "ExpertTechnicalAgent"
        self.llm = llm
        self.calculator = TechnicalCalculator()
        self.pattern_detector = PatternDetector()
        self.output_parser = PydanticOutputParser(pydantic_object=TechnicalInsight)
        self.init_lineage_tracking()  # Initialize lineage tracking

    async def analyze(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Perform comprehensive technical analysis

        Args:
            context: {
                'symbol': str,
                'price': float,
                'prices': List[float],  # Historical prices
                'volumes': List[float],
                'highs': List[float],
                'lows': List[float]
            }
        """
        logger.info(f"[{self.name}] Starting technical analysis for {context.get('symbol')}")

        symbol = context.get('symbol', 'UNKNOWN')
        # CRITICAL FIX: Get price from market_data if not at root level
        price = context.get('price') or context.get('market_data', {}).get('price', 0)
        prices = context.get('prices', [price] * 200)  # Generate dummy if not available

        try:
            # Step 1: Calculate all technical indicators locally
            indicators = await self._calculate_indicators(prices, context)

            # Step 2: Detect chart patterns
            patterns = await self._detect_chart_patterns(context)

            # Step 3: Use GPT-4 as chart pattern expert (with pattern data)
            insights = await self._generate_expert_insights(symbol, price, indicators, patterns, context)

            # Step 3.5: Track data lineage
            self._track_technical_lineage(symbol, price, indicators, patterns)

            # Safety check: ensure insights is a dict
            if not isinstance(insights, dict):
                logger.error(f"[{self.name}] insights is not a dict, type: {type(insights)}, value: {insights}")
                insights = self._rule_based_insights(indicators)

            # Step 4: Combine calculations with LLM insights
            result = {
                'agent': self.name,
                'symbol': symbol,
                'indicators': indicators,
                'patterns': patterns,
                'insights': insights,
                'summary': insights.get('trend_analysis', 'Neutral trend'),
                'signal': insights.get('signal', 'HOLD'),
                'rsi': indicators.get('rsi'),
                'macd': indicators.get('macd'),
                'bollinger_bands': indicators.get('bollinger_bands'),
                'golden_cross': indicators.get('golden_cross'),
                'support_levels': patterns.get('support_resistance', {}).get('support', []),
                'resistance_levels': patterns.get('support_resistance', {}).get('resistance', []),
                'chart_patterns': patterns.get('patterns', []),
                'pattern_signals': patterns.get('trading_signals', []),
                'trend': self._determine_trend(indicators),
                'confidence': insights.get('confidence_score', 0.5),
                'timestamp': datetime.utcnow().isoformat()
            }

            logger.info(f"[{self.name}] Completed analysis: {result['signal']} signal with {result['confidence']*100}% confidence")

            # Add lineage to output
            result = self.add_lineage_to_output(result)
            return result

        except Exception as e:
            logger.error(f"[{self.name}] Error in technical analysis: {e}")
            return self._fallback_analysis(symbol, price)

    async def _calculate_indicators(self, prices: List[float], context: Dict) -> Dict[str, Any]:
        """Calculate all technical indicators using local calculator"""

        volumes = context.get('volumes', [100000] * len(prices))
        highs = context.get('highs', [p * 1.02 for p in prices])
        lows = context.get('lows', [p * 0.98 for p in prices])

        indicators = {
            'rsi': self.calculator.calculate_rsi(prices),
            'macd': self.calculator.calculate_macd(prices),
            'bollinger_bands': self.calculator.calculate_bollinger_bands(prices),
            'golden_cross': self.calculator.detect_golden_cross(prices),
            'support_resistance': self.calculator.calculate_support_resistance(prices),
            'sma_50': self.calculator.calculate_sma(prices, 50)[-1] if len(prices) >= 50 else None,
            'sma_200': self.calculator.calculate_sma(prices, 200)[-1] if len(prices) >= 200 else None,
            'ema_12': self.calculator.calculate_ema(prices, 12)[-1] if len(prices) >= 12 else None,
            'ema_26': self.calculator.calculate_ema(prices, 26)[-1] if len(prices) >= 26 else None,
            'atr': self.calculator.calculate_atr(highs, lows, prices),
            'volume_analysis': self.calculator.analyze_volume(volumes, prices)
        }

        return indicators

    async def _detect_chart_patterns(self, context: Dict) -> Dict[str, Any]:
        """Detect chart patterns using PatternDetector"""

        # Build OHLC data from context
        prices = context.get('prices', [])
        highs = context.get('highs', [])
        lows = context.get('lows', [])
        volumes = context.get('volumes', [])

        if not prices or len(prices) < 20:
            logger.warning(f"[{self.name}] Insufficient price data for pattern detection")
            return {
                'patterns_detected': 0,
                'patterns': [],
                'support_resistance': {'support': [], 'resistance': []},
                'pattern_summary': 'Insufficient data',
                'trading_signals': []
            }

        # Convert to OHLC format
        ohlc_data = []
        for i in range(len(prices)):
            ohlc_data.append({
                'open': prices[i-1] if i > 0 else prices[i],
                'high': highs[i] if i < len(highs) else prices[i] * 1.01,
                'low': lows[i] if i < len(lows) else prices[i] * 0.99,
                'close': prices[i],
                'volume': volumes[i] if i < len(volumes) else 1000000
            })

        try:
            patterns = self.pattern_detector.detect_patterns(ohlc_data)
            logger.info(f"[{self.name}] Detected {patterns.get('patterns_detected', 0)} chart patterns")
            return patterns
        except Exception as e:
            logger.error(f"[{self.name}] Pattern detection failed: {e}")
            return {
                'patterns_detected': 0,
                'patterns': [],
                'support_resistance': {'support': [], 'resistance': []},
                'pattern_summary': 'Pattern detection failed',
                'trading_signals': []
            }

    async def _generate_expert_insights(self,
                                       symbol: str,
                                       price: float,
                                       indicators: Dict,
                                       patterns: Dict,
                                       context: Dict) -> Dict:
        """Use GPT-4 as technical analysis expert"""

        prompt = ChatPromptTemplate.from_messages([
            ("system", """You are a master technical analyst and chart pattern expert. Analyze price action,
indicators, and patterns with expertise in:
1. Trend identification (uptrend, downtrend, sideways)
2. Chart pattern recognition (head & shoulders, triangles, flags, etc.)
3. Support/resistance analysis
4. Momentum indicators (RSI, MACD)
5. Volume confirmation
6. Entry/exit timing

IMPORTANT: You MUST respond with ONLY valid JSON matching the exact schema provided.
Do NOT include markdown code blocks, explanations, or any text outside the JSON.
Your entire response must be parseable as JSON."""),
            ("human", """Analyze {symbol} at ${price}:

Technical Indicators:
- RSI: {rsi_value} ({rsi_signal})
- MACD: {macd_value} (Trend: {macd_trend})
- Bollinger Bands: Price at {bb_position}
- Golden/Death Cross: {cross_signal}
- SMA 50: ${sma_50}
- SMA 200: ${sma_200}
- ATR (Volatility): {atr}

Chart Patterns Detected:
{chart_patterns}

Pattern Signals:
{pattern_signals}

Support Levels: {support}
Resistance Levels: {resistance}

Volume Analysis: {volume_analysis}

{format_instructions}

RESPOND WITH ONLY THE JSON OBJECT. No markdown, no explanation, just the JSON.""")
        ])

        try:
            rsi_data = indicators.get('rsi', {})
            macd_data = indicators.get('macd', {})
            bb_data = indicators.get('bollinger_bands', {})
            gc_data = indicators.get('golden_cross', {})
            sr_data = patterns.get('support_resistance', {})
            vol_data = indicators.get('volume_analysis', {})

            # Format detected patterns for prompt
            pattern_list = patterns.get('patterns', []) if isinstance(patterns, dict) else []
            chart_patterns_text = self._format_patterns_for_prompt(pattern_list) if pattern_list else "No patterns detected"

            pattern_signals = patterns.get('trading_signals', []) if isinstance(patterns, dict) else []
            signals_text = "\n".join([f"- {s.get('signal', 'HOLD')} at ${s.get('price_target', 'N/A')}: {s.get('reasoning', '')}"
                                     for s in pattern_signals[:3] if isinstance(s, dict)]) if pattern_signals else "No signals generated"

            # Ensure sr_data is dict
            sr_data_dict = sr_data if isinstance(sr_data, dict) else {}

            formatted_prompt = prompt.format_messages(
                symbol=symbol,
                price=price,
                rsi_value=rsi_data.get('value', 'N/A') if isinstance(rsi_data, dict) else 'N/A',
                rsi_signal=rsi_data.get('signal', 'neutral') if isinstance(rsi_data, dict) else 'neutral',
                macd_value=macd_data.get('macd', 'N/A') if isinstance(macd_data, dict) else 'N/A',
                macd_trend=macd_data.get('trend', 'neutral') if isinstance(macd_data, dict) else 'neutral',
                bb_position=bb_data.get('position', 'within_bands') if isinstance(bb_data, dict) else 'within_bands',
                cross_signal=gc_data.get('type', 'none') if isinstance(gc_data, dict) else 'none',
                sma_50=indicators.get('sma_50', 'N/A'),
                sma_200=indicators.get('sma_200', 'N/A'),
                atr=indicators.get('atr', 'N/A'),
                chart_patterns=chart_patterns_text,
                pattern_signals=signals_text,
                support=sr_data_dict.get('support', []),
                resistance=sr_data_dict.get('resistance', []),
                volume_analysis=vol_data.get('interpretation', 'Normal volume') if isinstance(vol_data, dict) else 'Normal volume',
                format_instructions=self.output_parser.get_format_instructions()
            )

            response = await self.llm.ainvoke(formatted_prompt)

            # Robust parsing with multiple fallbacks
            try:
                parsed = self.output_parser.parse(response.content)

                # Handle case where parser returns string instead of Pydantic model
                if isinstance(parsed, str):
                    logger.warning(f"[{self.name}] Parser returned string, attempting JSON parse")
                    # Try to parse as JSON
                    try:
                        parsed_json = json.loads(parsed)
                        # Convert JSON dict to expected format
                        return {
                            'trend_analysis': parsed_json.get('trend_analysis', 'N/A'),
                            'pattern_recognition': parsed_json.get('pattern_recognition', 'N/A'),
                            'support_resistance_analysis': parsed_json.get('support_resistance_analysis', 'N/A'),
                            'momentum_assessment': parsed_json.get('momentum_assessment', 'N/A'),
                            'volume_analysis': parsed_json.get('volume_analysis', 'N/A'),
                            'signal': parsed_json.get('signal', 'HOLD'),
                            'confidence_score': float(parsed_json.get('confidence_score', 0.5)),
                            'entry_exit_strategy': parsed_json.get('entry_exit_strategy', 'N/A')
                        }
                    except (json.JSONDecodeError, ValueError) as json_err:
                        logger.warning(f"[{self.name}] JSON parse failed: {json_err}, using rule-based fallback")
                        return self._rule_based_insights(indicators)

                # Handle case where parsed is a dict (unexpected but possible)
                if isinstance(parsed, dict):
                    logger.warning(f"[{self.name}] Parser returned dict instead of Pydantic model")
                    return {
                        'trend_analysis': parsed.get('trend_analysis', 'N/A'),
                        'pattern_recognition': parsed.get('pattern_recognition', 'N/A'),
                        'support_resistance_analysis': parsed.get('support_resistance_analysis', 'N/A'),
                        'momentum_assessment': parsed.get('momentum_assessment', 'N/A'),
                        'volume_analysis': parsed.get('volume_analysis', 'N/A'),
                        'signal': parsed.get('signal', 'HOLD'),
                        'confidence_score': float(parsed.get('confidence_score', 0.5)),
                        'entry_exit_strategy': parsed.get('entry_exit_strategy', 'N/A')
                    }

                # Expected case: Pydantic model - safely extract attributes
                return {
                    'trend_analysis': getattr(parsed, 'trend_analysis', 'N/A'),
                    'pattern_recognition': getattr(parsed, 'pattern_recognition', 'N/A'),
                    'support_resistance_analysis': getattr(parsed, 'support_resistance_analysis', 'N/A'),
                    'momentum_assessment': getattr(parsed, 'momentum_assessment', 'N/A'),
                    'volume_analysis': getattr(parsed, 'volume_analysis', 'N/A'),
                    'signal': getattr(parsed, 'signal', 'HOLD'),
                    'confidence_score': getattr(parsed, 'confidence_score', 0.5),
                    'entry_exit_strategy': getattr(parsed, 'entry_exit_strategy', 'N/A')
                }

            except Exception as parse_error:
                logger.error(f"[{self.name}] Parse error: {parse_error}, attempting raw JSON extraction")
                # Last resort: try to extract JSON from response.content directly
                try:
                    # Sometimes LLM wraps JSON in markdown code blocks
                    content = response.content.strip()
                    if content.startswith('```'):
                        # Extract JSON from markdown code block
                        content = content.split('```')[1]
                        if content.startswith('json'):
                            content = content[4:]
                        content = content.strip()

                    parsed_json = json.loads(content)
                    return {
                        'trend_analysis': parsed_json.get('trend_analysis', 'N/A'),
                        'pattern_recognition': parsed_json.get('pattern_recognition', 'N/A'),
                        'support_resistance_analysis': parsed_json.get('support_resistance_analysis', 'N/A'),
                        'momentum_assessment': parsed_json.get('momentum_assessment', 'N/A'),
                        'volume_analysis': parsed_json.get('volume_analysis', 'N/A'),
                        'signal': parsed_json.get('signal', 'HOLD'),
                        'confidence_score': float(parsed_json.get('confidence_score', 0.5)),
                        'entry_exit_strategy': parsed_json.get('entry_exit_strategy', 'N/A')
                    }
                except Exception as final_error:
                    logger.error(f"[{self.name}] All parsing attempts failed: {final_error}")
                    return self._rule_based_insights(indicators)

        except Exception as e:
            logger.error(f"[{self.name}] LLM analysis failed: {e}", exc_info=True)
            return self._rule_based_insights(indicators)

    def _format_patterns_for_prompt(self, patterns: List[Dict]) -> str:
        """Format detected patterns for LLM prompt"""
        if not patterns:
            return "No patterns detected"

        formatted = []
        for i, p in enumerate(patterns[:5], 1):  # Top 5 patterns
            pattern_type = p.get('pattern', 'Unknown')
            pattern_category = p.get('type', 'neutral')
            confidence = p.get('confidence', 0) * 100
            target = p.get('target', 'N/A')
            description = p.get('description', '')

            formatted.append(
                f"{i}. {pattern_type} ({pattern_category}) - Confidence: {confidence:.0f}%\n"
                f"   Target: ${target if isinstance(target, str) else f'{target:.2f}'}\n"
                f"   {description}"
            )

        return "\n\n".join(formatted)

    def _rule_based_insights(self, indicators: Dict) -> Dict:
        """Fallback rule-based analysis if LLM fails"""

        rsi = indicators.get('rsi', {})
        macd = indicators.get('macd', {})
        gc = indicators.get('golden_cross', {})

        # Simple technical rules
        signals = []
        confidence = 0.5

        # RSI signals
        if rsi.get('signal') == 'oversold':
            signals.append('BUY')
            confidence += 0.1
        elif rsi.get('signal') == 'overbought':
            signals.append('SELL')
            confidence += 0.1

        # MACD signals
        if macd.get('trend') == 'bullish':
            signals.append('BUY')
            confidence += 0.15
        elif macd.get('trend') == 'bearish':
            signals.append('SELL')
            confidence += 0.15

        # Golden/Death cross
        if gc.get('type') == 'golden_cross':
            signals.append('BUY')
            confidence += 0.2
        elif gc.get('type') == 'death_cross':
            signals.append('SELL')
            confidence += 0.2

        # Determine final signal
        buy_count = signals.count('BUY')
        sell_count = signals.count('SELL')

        if buy_count > sell_count:
            signal = 'BUY'
        elif sell_count > buy_count:
            signal = 'SELL'
        else:
            signal = 'HOLD'

        return {
            'trend_analysis': f'{macd.get("trend", "neutral").title()} trend detected',
            'pattern_recognition': 'Pattern analysis via technical indicators',
            'support_resistance_analysis': f'Key levels identified',
            'momentum_assessment': f'RSI: {rsi.get("signal", "neutral")}, MACD: {macd.get("trend", "neutral")}',
            'volume_analysis': indicators.get('volume_analysis', {}).get('interpretation', 'Normal'),
            'signal': signal,
            'confidence_score': min(confidence, 1.0),
            'entry_exit_strategy': 'Based on technical indicator confluence'
        }

    def _determine_trend(self, indicators: Dict) -> str:
        """Determine overall trend from indicators"""

        macd_trend = indicators.get('macd', {}).get('trend', 'neutral')
        gc_type = indicators.get('golden_cross', {}).get('type')
        rsi_signal = indicators.get('rsi', {}).get('signal', 'neutral')

        # Combine signals
        if macd_trend == 'bullish' or gc_type == 'golden_cross':
            return 'strong_bullish'
        elif macd_trend == 'bearish' or gc_type == 'death_cross':
            return 'strong_bearish'
        elif rsi_signal == 'overbought':
            return 'bearish'
        elif rsi_signal == 'oversold':
            return 'bullish'
        else:
            return 'neutral'

    def _track_technical_lineage(self, symbol: str, price: float, indicators: Dict, patterns: Dict):
        """Track data lineage for technical metrics"""

        # Track price data (same source as fundamental)
        self.track_data(
            field_name='price',
            value=price,
            source=DataSource.YFINANCE,
            reliability=DataReliability.HIGH,
            confidence=0.95,
            citation=f"Current market price from Yahoo Finance for {symbol}"
        )

        # Track RSI indicator
        rsi_data = indicators.get('rsi', {})
        if isinstance(rsi_data, dict) and rsi_data.get('value'):
            self.track_calculated(
                field_name='rsi',
                value=rsi_data['value'],
                formula='RSI(14): 100 - (100 / (1 + RS)) where RS = avg_gain / avg_loss',
                input_fields=['price_history'],
                confidence=0.92
            )

        # Track MACD indicator
        macd_data = indicators.get('macd', {})
        if isinstance(macd_data, dict) and macd_data.get('macd'):
            self.track_calculated(
                field_name='macd',
                value=macd_data['macd'],
                formula='MACD: EMA(12) - EMA(26)',
                input_fields=['price_history'],
                confidence=0.92
            )

        # Track Bollinger Bands
        bb_data = indicators.get('bollinger_bands', {})
        if isinstance(bb_data, dict) and bb_data.get('middle'):
            self.track_calculated(
                field_name='bollinger_bands',
                value=bb_data,
                formula='BB: SMA(20) ± 2*StdDev(20)',
                input_fields=['price_history'],
                confidence=0.90
            )

        # Track ATR (volatility measure)
        atr_value = indicators.get('atr')
        if atr_value:
            self.track_calculated(
                field_name='atr',
                value=atr_value,
                formula='ATR(14): Average True Range over 14 periods',
                input_fields=['high', 'low', 'close'],
                confidence=0.93
            )

        # Track chart patterns (pattern detector output)
        pattern_count = patterns.get('patterns_detected', 0)
        if pattern_count > 0:
            self.track_data(
                field_name='chart_patterns',
                value=patterns.get('patterns', []),
                source=DataSource.CALCULATED,
                reliability=DataReliability.MEDIUM,
                confidence=0.75,
                citation=f"Detected {pattern_count} chart patterns via technical pattern recognition"
            )

        # Track support/resistance levels
        sr_data = patterns.get('support_resistance', {})
        if isinstance(sr_data, dict):
            if sr_data.get('support'):
                self.track_calculated(
                    field_name='support_levels',
                    value=sr_data['support'],
                    formula='Local minima in price history',
                    input_fields=['price_history'],
                    confidence=0.80
                )
            if sr_data.get('resistance'):
                self.track_calculated(
                    field_name='resistance_levels',
                    value=sr_data['resistance'],
                    formula='Local maxima in price history',
                    input_fields=['price_history'],
                    confidence=0.80
                )

        logger.info(f"[{self.name}] Tracked lineage for {len(self.lineage_tracker.records)} technical data points")

    def _fallback_analysis(self, symbol: str, price: float) -> Dict:
        """Fallback analysis if everything fails"""

        return {
            'agent': self.name,
            'symbol': symbol,
            'summary': 'Technical analysis unavailable',
            'signal': 'neutral',
            'rsi': {'value': None, 'signal': 'neutral'},
            'macd': {'macd': None, 'signal': None, 'trend': 'neutral'},
            'trend': 'neutral',
            'confidence': 0.3,
            'support_levels': [],
            'resistance_levels': [],
            'data_source': 'fallback',
            'timestamp': datetime.utcnow().isoformat()
        }
