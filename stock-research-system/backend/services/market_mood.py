"""
Market Mood Index Calculator
Inspired by Tickertape's Fear & Greed Index
"""

import asyncio
from typing import Dict, Any, List
import numpy as np
import logging
import yfinance as yf
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)


class MarketMoodCalculator:
    """
    Calculates market mood/sentiment based on multiple indicators
    """

    def __init__(self):
        self.indicators = {
            'vix': {'weight': 0.20, 'name': 'Volatility Index'},
            'breadth': {'weight': 0.15, 'name': 'Market Breadth'},
            'momentum': {'weight': 0.15, 'name': 'Price Momentum'},
            'volume': {'weight': 0.15, 'name': 'Volume Analysis'},
            'put_call': {'weight': 0.15, 'name': 'Put/Call Ratio'},
            'high_low': {'weight': 0.10, 'name': '52-Week Highs/Lows'},
            'safe_haven': {'weight': 0.10, 'name': 'Safe Haven Demand'}
        }

        # Mood levels
        self.mood_levels = {
            'extreme_fear': (0, 20),
            'fear': (20, 40),
            'neutral': (40, 60),
            'greed': (60, 80),
            'extreme_greed': (80, 100)
        }

    async def calculate_market_mood(self, market: str = 'US') -> Dict[str, Any]:
        """
        Calculate overall market mood index
        """
        try:
            logger.info(f"Calculating market mood for {market} market")

            # Calculate individual indicators
            indicators_data = await asyncio.gather(
                self._calculate_vix(),
                self._calculate_breadth(),
                self._calculate_momentum(),
                self._calculate_volume(),
                self._calculate_put_call_ratio(),
                self._calculate_high_low(),
                self._calculate_safe_haven()
            )

            # Combine indicators
            mood_score = 0
            components = []

            indicator_names = list(self.indicators.keys())
            for i, indicator_value in enumerate(indicators_data):
                if indicator_value is not None:
                    indicator_name = indicator_names[i]
                    weight = self.indicators[indicator_name]['weight']
                    mood_score += indicator_value * weight

                    components.append({
                        'name': self.indicators[indicator_name]['name'],
                        'value': indicator_value,
                        'weight': weight * 100,
                        'contribution': indicator_value * weight
                    })

            # Determine mood level
            mood_level = self._get_mood_level(mood_score)

            return {
                'timestamp': datetime.now().isoformat(),
                'market': market,
                'mood_score': round(mood_score, 2),
                'mood_level': mood_level,
                'mood_emoji': self._get_mood_emoji(mood_level),
                'components': components,
                'interpretation': self._interpret_mood(mood_score, mood_level),
                'historical_comparison': self._get_historical_context(mood_score)
            }

        except Exception as e:
            logger.error(f"Error calculating market mood: {e}")
            return {'error': str(e)}

    async def _calculate_vix(self) -> float:
        """
        Calculate fear based on VIX (Volatility Index)
        VIX < 15: Low fear (100), VIX > 30: High fear (0)
        """
        try:
            vix = yf.Ticker('^VIX')
            info = vix.info
            current_vix = info.get('regularMarketPrice', 20)

            # Normalize VIX to 0-100 scale (inverted - high VIX = fear)
            if current_vix <= 12:
                return 100  # Extreme greed
            elif current_vix >= 35:
                return 0    # Extreme fear
            else:
                # Linear scale between 12 and 35
                return 100 - ((current_vix - 12) / 23 * 100)

        except Exception as e:
            logger.warning(f"VIX calculation error: {e}")
            return 50  # Neutral if error

    async def _calculate_breadth(self) -> float:
        """
        Calculate market breadth (advancing vs declining stocks)
        """
        try:
            # Get S&P 500 components performance
            spy = yf.Ticker('SPY')
            hist = spy.history(period='1d')

            if not hist.empty:
                daily_change = (hist['Close'].iloc[-1] - hist['Open'].iloc[-1]) / hist['Open'].iloc[-1]

                # Simplified breadth based on SPY performance
                if daily_change > 0.01:
                    return 75  # Bullish breadth
                elif daily_change < -0.01:
                    return 25  # Bearish breadth
                else:
                    return 50  # Neutral

            return 50

        except Exception as e:
            logger.warning(f"Breadth calculation error: {e}")
            return 50

    async def _calculate_momentum(self) -> float:
        """
        Calculate price momentum (SPY vs moving averages)
        """
        try:
            spy = yf.Ticker('SPY')
            hist = spy.history(period='3mo')

            if not hist.empty:
                current_price = hist['Close'].iloc[-1]
                sma_50 = hist['Close'].rolling(window=50).mean().iloc[-1]
                sma_200 = hist['Close'].rolling(window=200).mean().iloc[-1] if len(hist) >= 200 else sma_50

                # Calculate momentum score
                above_50 = (current_price - sma_50) / sma_50
                above_200 = (current_price - sma_200) / sma_200

                # Convert to 0-100 scale
                momentum = 50 + (above_50 * 100) + (above_200 * 50)
                momentum = max(0, min(100, momentum))

                return momentum

            return 50

        except Exception as e:
            logger.warning(f"Momentum calculation error: {e}")
            return 50

    async def _calculate_volume(self) -> float:
        """
        Calculate volume sentiment (above/below average)
        """
        try:
            spy = yf.Ticker('SPY')
            hist = spy.history(period='1mo')

            if not hist.empty:
                current_volume = hist['Volume'].iloc[-1]
                avg_volume = hist['Volume'].mean()

                # High volume with price up = greed, high volume with price down = fear
                price_change = (hist['Close'].iloc[-1] - hist['Open'].iloc[-1]) / hist['Open'].iloc[-1]
                volume_ratio = current_volume / avg_volume

                if volume_ratio > 1.2:
                    # High volume
                    if price_change > 0:
                        return 75  # Greed
                    else:
                        return 25  # Fear
                else:
                    return 50  # Normal volume

            return 50

        except Exception as e:
            logger.warning(f"Volume calculation error: {e}")
            return 50

    async def _calculate_put_call_ratio(self) -> float:
        """
        Calculate put/call ratio sentiment
        (Simplified - in production would use options data)
        """
        try:
            # Simplified using VIX as proxy for put/call sentiment
            vix = yf.Ticker('^VIX')
            info = vix.info
            current_vix = info.get('regularMarketPrice', 20)

            # Lower VIX suggests lower put/call ratio (more calls = greed)
            if current_vix < 15:
                return 80  # Low put/call = greed
            elif current_vix > 25:
                return 20  # High put/call = fear
            else:
                # Linear scale
                return 80 - ((current_vix - 15) / 10 * 60)

        except Exception as e:
            logger.warning(f"Put/Call ratio error: {e}")
            return 50

    async def _calculate_high_low(self) -> float:
        """
        Calculate 52-week highs vs lows sentiment
        """
        try:
            # Check major indices proximity to 52-week highs
            indices = ['SPY', 'QQQ', 'DIA']
            scores = []

            for symbol in indices:
                ticker = yf.Ticker(symbol)
                info = ticker.info
                current = info.get('regularMarketPrice', 0)
                high_52w = info.get('fiftyTwoWeekHigh', current)
                low_52w = info.get('fiftyTwoWeekLow', current)

                if high_52w > low_52w:
                    # Calculate position in 52-week range
                    position = (current - low_52w) / (high_52w - low_52w)
                    scores.append(position * 100)

            return np.mean(scores) if scores and len(scores) > 0 else 50

        except Exception as e:
            logger.warning(f"High/Low calculation error: {e}")
            return 50

    async def _calculate_safe_haven(self) -> float:
        """
        Calculate safe haven demand (bonds, gold sentiment)
        """
        try:
            # Check bond ETF (TLT) and gold (GLD) performance
            safe_havens = ['TLT', 'GLD']
            risk_assets = ['SPY', 'QQQ']

            safe_performance = []
            risk_performance = []

            for symbol in safe_havens:
                ticker = yf.Ticker(symbol)
                hist = ticker.history(period='5d')
                if not hist.empty:
                    perf = (hist['Close'].iloc[-1] - hist['Close'].iloc[0]) / hist['Close'].iloc[0]
                    safe_performance.append(perf)

            for symbol in risk_assets:
                ticker = yf.Ticker(symbol)
                hist = ticker.history(period='5d')
                if not hist.empty:
                    perf = (hist['Close'].iloc[-1] - hist['Close'].iloc[0]) / hist['Close'].iloc[0]
                    risk_performance.append(perf)

            # If safe havens outperform = fear, if risk assets outperform = greed
            if safe_performance and risk_performance:
                safe_avg = np.mean(safe_performance)
                risk_avg = np.mean(risk_performance)

                if risk_avg > safe_avg:
                    return 50 + (risk_avg - safe_avg) * 500  # Greed
                else:
                    return 50 - (safe_avg - risk_avg) * 500  # Fear

            return 50

        except Exception as e:
            logger.warning(f"Safe haven calculation error: {e}")
            return 50

    def _get_mood_level(self, score: float) -> str:
        """
        Determine mood level based on score
        """
        for level, (min_score, max_score) in self.mood_levels.items():
            if min_score <= score < max_score:
                return level
        return 'neutral'

    def _get_mood_emoji(self, mood_level: str) -> str:
        """
        Get emoji representation of mood
        """
        emoji_map = {
            'extreme_fear': '😱',
            'fear': '😨',
            'neutral': '😐',
            'greed': '😊',
            'extreme_greed': '🤑'
        }
        return emoji_map.get(mood_level, '😐')

    def _interpret_mood(self, score: float, level: str) -> str:
        """
        Provide interpretation of current mood
        """
        interpretations = {
            'extreme_fear': "The market is experiencing extreme fear. This could be a buying opportunity for contrarian investors, but caution is warranted.",
            'fear': "Fear is prevalent in the market. Investors are risk-averse, which may create value opportunities.",
            'neutral': "The market sentiment is balanced. Neither fear nor greed dominates investor behavior.",
            'greed': "Greed is driving the market. Investors are optimistic, but be cautious of potential overvaluation.",
            'extreme_greed': "Extreme greed is present. The market may be overheated and due for a correction. Consider taking profits."
        }

        return interpretations.get(level, "Market sentiment is neutral.")

    def _get_historical_context(self, score: float) -> Dict[str, Any]:
        """
        Provide historical context for current mood
        """
        # Simplified historical context
        return {
            'current_vs_average': 'above' if score > 50 else 'below',
            'percentile': min(100, max(0, score)),
            'similar_periods': [
                'March 2020 (COVID crash): Extreme Fear (10)',
                'January 2021 (Meme stock rally): Extreme Greed (85)',
                'Current: ' + str(round(score))
            ]
        }


class SectorRotationAnalyzer:
    """
    Analyzes sector rotation and performance
    """

    def __init__(self):
        self.sectors = {
            'XLK': 'Technology',
            'XLF': 'Financials',
            'XLV': 'Healthcare',
            'XLE': 'Energy',
            'XLI': 'Industrials',
            'XLY': 'Consumer Discretionary',
            'XLP': 'Consumer Staples',
            'XLU': 'Utilities',
            'XLRE': 'Real Estate',
            'XLB': 'Materials',
            'XLC': 'Communication Services'
        }

    async def analyze_sector_rotation(self) -> Dict[str, Any]:
        """
        Analyze sector rotation and performance
        """
        try:
            sector_data = []

            for symbol, name in self.sectors.items():
                ticker = yf.Ticker(symbol)
                hist = ticker.history(period='1mo')

                if not hist.empty:
                    # Calculate performance metrics
                    perf_1d = (hist['Close'].iloc[-1] - hist['Close'].iloc[-2]) / hist['Close'].iloc[-2] * 100
                    perf_1w = (hist['Close'].iloc[-1] - hist['Close'].iloc[-5]) / hist['Close'].iloc[-5] * 100
                    perf_1m = (hist['Close'].iloc[-1] - hist['Close'].iloc[0]) / hist['Close'].iloc[0] * 100

                    # Determine signal
                    if perf_1w > 2:
                        signal = 'BUY'
                    elif perf_1w < -2:
                        signal = 'SELL'
                    else:
                        signal = 'HOLD'

                    sector_data.append({
                        'name': name,
                        'symbol': symbol,
                        'performance_1d': round(perf_1d, 2),
                        'performance_1w': round(perf_1w, 2),
                        'performance_1m': round(perf_1m, 2),
                        'signal': signal,
                        'momentum': 'positive' if perf_1w > 0 else 'negative'
                    })

            # Sort by weekly performance
            sector_data.sort(key=lambda x: x['performance_1w'], reverse=True)

            # Identify rotation
            leaders = sector_data[:3]
            laggards = sector_data[-3:]

            return {
                'timestamp': datetime.now().isoformat(),
                'sectors': sector_data,
                'leaders': leaders,
                'laggards': laggards,
                'rotation_signal': self._identify_rotation_pattern(sector_data)
            }

        except Exception as e:
            logger.error(f"Sector rotation analysis error: {e}")
            return {'error': str(e)}

    def _identify_rotation_pattern(self, sector_data: List[Dict]) -> str:
        """
        Identify the current rotation pattern
        """
        # Simplified pattern recognition
        tech_perf = next((s['performance_1w'] for s in sector_data if s['name'] == 'Technology'), 0)
        utilities_perf = next((s['performance_1w'] for s in sector_data if s['name'] == 'Utilities'), 0)
        financials_perf = next((s['performance_1w'] for s in sector_data if s['name'] == 'Financials'), 0)

        if tech_perf > 2 and financials_perf > 1:
            return "Risk-On Rotation: Growth sectors leading"
        elif utilities_perf > 1 and tech_perf < 0:
            return "Risk-Off Rotation: Defensive sectors leading"
        else:
            return "Mixed Rotation: No clear pattern"