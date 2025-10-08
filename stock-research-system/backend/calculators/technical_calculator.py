"""
Technical Analysis Calculator
Pure mathematical implementations of all technical indicators
No external API dependencies - all calculations done locally
"""

from typing import List, Dict, Tuple, Optional
import numpy as np
from datetime import datetime, timedelta


class TechnicalCalculator:
    """Calculate technical indicators using pure mathematics"""

    def calculate_sma(self, prices: List[float], period: int) -> List[float]:
        """Simple Moving Average"""
        if len(prices) < period:
            return []

        sma = []
        for i in range(period - 1, len(prices)):
            window = prices[i - period + 1:i + 1]
            sma.append(sum(window) / period)

        return sma

    def calculate_ema(self, prices: List[float], period: int) -> List[float]:
        """Exponential Moving Average"""
        if len(prices) < period:
            return []

        multiplier = 2 / (period + 1)
        ema = [sum(prices[:period]) / period]  # Start with SMA

        for price in prices[period:]:
            ema_value = (price - ema[-1]) * multiplier + ema[-1]
            ema.append(ema_value)

        return ema

    def calculate_rsi(self, prices: List[float], period: int = 14) -> Dict:
        """Relative Strength Index"""
        if len(prices) < period + 1:
            return {'value': None, 'signal': 'neutral', 'interpretation': 'Insufficient data'}

        # Calculate price changes
        changes = [prices[i] - prices[i-1] for i in range(1, len(prices))]

        gains = [change if change > 0 else 0 for change in changes]
        losses = [-change if change < 0 else 0 for change in changes]

        # Calculate average gains and losses
        avg_gain = sum(gains[:period]) / period
        avg_loss = sum(losses[:period]) / period

        # Calculate RSI for the period
        for i in range(period, len(gains)):
            avg_gain = (avg_gain * (period - 1) + gains[i]) / period
            avg_loss = (avg_loss * (period - 1) + losses[i]) / period

        if avg_loss == 0:
            rsi_value = 100
        else:
            rs = avg_gain / avg_loss
            rsi_value = 100 - (100 / (1 + rs))

        # Determine signal
        if rsi_value > 70:
            signal = 'overbought'
            interpretation = 'Potentially overbought - consider taking profits'
        elif rsi_value < 30:
            signal = 'oversold'
            interpretation = 'Potentially oversold - buying opportunity'
        else:
            signal = 'neutral'
            interpretation = 'Neutral momentum'

        return {
            'value': round(rsi_value, 2),
            'signal': signal,
            'interpretation': interpretation,
            'date': datetime.now().isoformat()
        }

    def calculate_macd(self, prices: List[float],
                       fast_period: int = 12,
                       slow_period: int = 26,
                       signal_period: int = 9) -> Dict:
        """Moving Average Convergence Divergence"""
        if len(prices) < slow_period:
            return {
                'macd': None,
                'signal': None,
                'histogram': None,
                'trend': 'neutral'
            }

        # Calculate EMAs
        ema_fast = self.calculate_ema(prices, fast_period)
        ema_slow = self.calculate_ema(prices, slow_period)

        # Align arrays
        offset = len(ema_fast) - len(ema_slow)
        if offset > 0:
            ema_fast = ema_fast[offset:]

        # Calculate MACD line
        macd_line = [ema_fast[i] - ema_slow[i] for i in range(len(ema_slow))]

        # Calculate signal line
        signal_line = self.calculate_ema(macd_line, signal_period)

        # Calculate histogram
        offset = len(macd_line) - len(signal_line)
        histogram = [macd_line[i + offset] - signal_line[i] for i in range(len(signal_line))]

        # Determine trend
        current_macd = macd_line[-1] if macd_line else 0
        current_signal = signal_line[-1] if signal_line else 0
        current_hist = histogram[-1] if histogram else 0

        if current_macd > current_signal and current_hist > 0:
            trend = 'bullish'
        elif current_macd < current_signal and current_hist < 0:
            trend = 'bearish'
        else:
            trend = 'neutral'

        return {
            'macd': round(current_macd, 2) if current_macd else None,
            'signal': round(current_signal, 2) if current_signal else None,
            'histogram': round(current_hist, 2) if current_hist else None,
            'trend': trend
        }

    def calculate_bollinger_bands(self, prices: List[float],
                                  period: int = 20,
                                  std_dev: float = 2.0) -> Dict:
        """Bollinger Bands"""
        if len(prices) < period:
            return {'upper': None, 'middle': None, 'lower': None}

        sma = self.calculate_sma(prices, period)

        # Calculate standard deviation
        std_devs = []
        for i in range(period - 1, len(prices)):
            window = prices[i - period + 1:i + 1]
            mean = sum(window) / period
            variance = sum((x - mean) ** 2 for x in window) / period
            std_devs.append(variance ** 0.5)

        # Calculate bands
        upper_band = [sma[i] + (std_devs[i] * std_dev) for i in range(len(sma))]
        lower_band = [sma[i] - (std_devs[i] * std_dev) for i in range(len(sma))]

        current_price = prices[-1]
        current_upper = upper_band[-1]
        current_middle = sma[-1]
        current_lower = lower_band[-1]

        # Position analysis
        if current_price > current_upper:
            position = 'above_upper'
            signal = 'overbought'
        elif current_price < current_lower:
            position = 'below_lower'
            signal = 'oversold'
        else:
            position = 'within_bands'
            signal = 'neutral'

        return {
            'upper': round(current_upper, 2),
            'middle': round(current_middle, 2),
            'lower': round(current_lower, 2),
            'current_price': round(current_price, 2),
            'position': position,
            'signal': signal
        }

    def detect_golden_cross(self, prices: List[float]) -> Dict:
        """Detect Golden Cross (SMA50 crosses above SMA200)"""
        if len(prices) < 200:
            return {'detected': False, 'signal': None}

        sma_50 = self.calculate_sma(prices, 50)
        sma_200 = self.calculate_sma(prices, 200)

        # Align arrays
        offset = len(sma_50) - len(sma_200)
        if offset > 0:
            sma_50 = sma_50[offset:]

        # Check for cross
        if len(sma_50) < 2 or len(sma_200) < 2:
            return {'detected': False, 'signal': None}

        current_50 = sma_50[-1]
        previous_50 = sma_50[-2]
        current_200 = sma_200[-1]
        previous_200 = sma_200[-2]

        golden_cross = previous_50 <= previous_200 and current_50 > current_200
        death_cross = previous_50 >= previous_200 and current_50 < current_200

        if golden_cross:
            return {
                'detected': True,
                'type': 'golden_cross',
                'signal': 'strong_buy',
                'sma_50': round(current_50, 2),
                'sma_200': round(current_200, 2)
            }
        elif death_cross:
            return {
                'detected': True,
                'type': 'death_cross',
                'signal': 'strong_sell',
                'sma_50': round(current_50, 2),
                'sma_200': round(current_200, 2)
            }
        else:
            return {
                'detected': False,
                'type': None,
                'signal': 'neutral',
                'sma_50': round(current_50, 2),
                'sma_200': round(current_200, 2)
            }

    def calculate_support_resistance(self, prices: List[float],
                                     window: int = 20) -> Dict:
        """Calculate support and resistance levels"""
        if len(prices) < window:
            return {'support': [], 'resistance': []}

        # Find local minima (support) and maxima (resistance)
        support_levels = []
        resistance_levels = []

        for i in range(window, len(prices) - window):
            # Check if local minimum
            if prices[i] == min(prices[i-window:i+window+1]):
                support_levels.append(prices[i])

            # Check if local maximum
            if prices[i] == max(prices[i-window:i+window+1]):
                resistance_levels.append(prices[i])

        # Cluster nearby levels
        support_levels = self._cluster_levels(support_levels)
        resistance_levels = self._cluster_levels(resistance_levels)

        return {
            'support': sorted(support_levels)[-3:],  # Top 3 support
            'resistance': sorted(resistance_levels)[:3]  # Top 3 resistance
        }

    def _cluster_levels(self, levels: List[float], threshold: float = 0.02) -> List[float]:
        """Cluster nearby price levels"""
        if not levels:
            return []

        clustered = []
        current_cluster = [levels[0]]

        for level in levels[1:]:
            cluster_mean = sum(current_cluster) / len(current_cluster)
            # Prevent division by zero
            if level == 0:
                continue
            if abs(level - cluster_mean) / level < threshold:
                current_cluster.append(level)
            else:
                clustered.append(sum(current_cluster) / len(current_cluster))
                current_cluster = [level]

        if current_cluster:
            clustered.append(sum(current_cluster) / len(current_cluster))

        return clustered

    def calculate_atr(self, highs: List[float], lows: List[float],
                     closes: List[float], period: int = 14) -> float:
        """Average True Range - volatility indicator"""
        if len(highs) < period or len(lows) < period or len(closes) < period:
            return None

        true_ranges = []
        for i in range(1, len(highs)):
            high_low = highs[i] - lows[i]
            high_close = abs(highs[i] - closes[i-1])
            low_close = abs(lows[i] - closes[i-1])
            true_ranges.append(max(high_low, high_close, low_close))

        # Calculate ATR
        atr = sum(true_ranges[:period]) / period
        for i in range(period, len(true_ranges)):
            atr = (atr * (period - 1) + true_ranges[i]) / period

        return round(atr, 2)

    def analyze_volume(self, volumes: List[float], prices: List[float]) -> Dict:
        """Volume analysis"""
        if len(volumes) < 20 or len(prices) < 20:
            return {'trend': 'neutral', 'signal': 'insufficient_data'}

        avg_volume = sum(volumes[-20:]) / 20
        current_volume = volumes[-1]

        # Prevent division by zero in price change calculation
        price_change = (prices[-1] - prices[-2]) / prices[-2] if len(prices) > 1 and prices[-2] != 0 else 0

        # Volume spike analysis
        if current_volume > avg_volume * 1.5:
            if price_change > 0:
                signal = 'accumulation'
                interpretation = 'High volume with price increase - strong buying'
            else:
                signal = 'distribution'
                interpretation = 'High volume with price decrease - strong selling'
        else:
            signal = 'normal'
            interpretation = 'Normal trading volume'

        return {
            'current_volume': int(current_volume),
            'average_volume': int(avg_volume),
            'volume_ratio': round(current_volume / avg_volume, 2) if avg_volume > 0 else 0,
            'signal': signal,
            'interpretation': interpretation
        }
