"""
Chart Analytics Agent - Professional Trading Charts & Visual Analytics

This agent generates comprehensive trading charts with:
1. Price action charts (Candlestick, OHLC, Line)
2. Technical indicators (RSI, MACD, Bollinger Bands, ATR, Volume)
3. Trend analysis with support/resistance levels
4. Pattern recognition (Head & Shoulders, Double Top/Bottom, Triangles)
5. Multi-timeframe analysis (Daily, Weekly, Monthly)
6. Expert trader visual metrics
"""

import asyncio
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
import logging
import numpy as np
import yfinance as yf

logger = logging.getLogger(__name__)


class ChartAnalyticsAgent:
    """
    Chart Analytics Agent for generating professional trading charts and visual metrics.

    Provides expert trader perspective with:
    - Multi-timeframe price charts
    - Technical indicator overlays
    - Support/Resistance levels
    - Chart pattern recognition
    - Volume profile analysis
    """

    def __init__(self, **kwargs):
        self.name = "chart_analytics"
        self.description = "Generates professional trading charts with technical indicators and visual metrics"

    async def execute(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """Execute chart analytics generation."""
        try:
            symbol = state.get('symbol') or state.get('symbols', [''])[0]
            if not symbol:
                raise ValueError("No stock symbol provided for chart analysis")

            logger.info(f"[{self.name}] Starting chart analytics for {symbol}")

            # Fetch historical data for charting
            historical_data = await self._fetch_chart_data(symbol)

            # Generate chart configurations
            price_charts = self._generate_price_charts(symbol, historical_data)
            indicator_charts = self._generate_indicator_charts(symbol, historical_data)
            pattern_analysis = self._analyze_chart_patterns(symbol, historical_data)
            support_resistance = self._calculate_support_resistance(historical_data)
            volume_profile = self._analyze_volume_profile(historical_data)

            # Multi-timeframe analysis
            mtf_analysis = self._multi_timeframe_analysis(symbol)

            result = {
                'symbol': symbol,
                'chart_data': {
                    'price_charts': price_charts,
                    'indicator_charts': indicator_charts,
                    'technical_overlays': self._generate_technical_overlays(historical_data)
                },
                'pattern_analysis': pattern_analysis,
                'support_resistance': support_resistance,
                'volume_profile': volume_profile,
                'multi_timeframe': mtf_analysis,
                'expert_insights': self._generate_expert_insights(
                    pattern_analysis, support_resistance, mtf_analysis
                ),
                'chart_metadata': {
                    'data_points': len(historical_data['close']),
                    'timeframe': 'daily',
                    'period': '6 months',
                    'last_updated': datetime.utcnow().isoformat()
                }
            }

            logger.info(f"[{self.name}] Chart analytics complete for {symbol}")
            return result  # Return unwrapped data to avoid double nesting

        except Exception as e:
            logger.error(f"Error in ChartAnalyticsAgent: {e}", exc_info=True)
            return {'error': str(e)}

    async def _fetch_chart_data(self, symbol: str, period: str = '6mo') -> Dict[str, List]:
        """Fetch historical OHLCV data for charting."""
        try:
            ticker = yf.Ticker(symbol)
            hist = ticker.history(period=period)

            return {
                'dates': hist.index.strftime('%Y-%m-%d').tolist(),
                'open': hist['Open'].tolist(),
                'high': hist['High'].tolist(),
                'low': hist['Low'].tolist(),
                'close': hist['Close'].tolist(),
                'volume': hist['Volume'].tolist()
            }
        except Exception as e:
            logger.error(f"[{self.name}] Failed to fetch chart data: {e}")
            return {'dates': [], 'open': [], 'high': [], 'low': [], 'close': [], 'volume': []}

    def _generate_price_charts(self, symbol: str, data: Dict) -> Dict[str, Any]:
        """Generate price chart configurations."""
        return {
            'candlestick': {
                'type': 'candlestick',
                'data': {
                    'dates': data['dates'],
                    'open': data['open'],
                    'high': data['high'],
                    'low': data['low'],
                    'close': data['close']
                },
                'config': {
                    'title': f'{symbol} Candlestick Chart',
                    'yaxis_title': 'Price (USD)',
                    'showgrid': True,
                    'colors': {'up': '#00C853', 'down': '#D50000'}
                }
            },
            'line': {
                'type': 'line',
                'data': {
                    'dates': data['dates'],
                    'close': data['close']
                },
                'config': {
                    'title': f'{symbol} Price Trend',
                    'yaxis_title': 'Price (USD)',
                    'line_color': '#1976D2',
                    'fill': True
                }
            },
            'ohlc': {
                'type': 'ohlc',
                'data': {
                    'dates': data['dates'],
                    'open': data['open'],
                    'high': data['high'],
                    'low': data['low'],
                    'close': data['close']
                },
                'config': {
                    'title': f'{symbol} OHLC Chart',
                    'yaxis_title': 'Price (USD)'
                }
            }
        }

    def _generate_indicator_charts(self, symbol: str, data: Dict) -> Dict[str, Any]:
        """Generate technical indicator charts."""
        close_prices = np.array(data['close'])
        high_prices = np.array(data['high'])
        low_prices = np.array(data['low'])
        volumes = np.array(data['volume'])

        # RSI (14-period)
        rsi = self._calculate_rsi(close_prices, period=14)

        # MACD
        macd_line, signal_line, histogram = self._calculate_macd(close_prices)

        # Bollinger Bands
        bb_upper, bb_middle, bb_lower = self._calculate_bollinger_bands(close_prices)

        # ATR (14-period)
        atr = self._calculate_atr(high_prices, low_prices, close_prices, period=14)

        # Moving Averages
        sma_20 = self._calculate_sma(close_prices, 20)
        sma_50 = self._calculate_sma(close_prices, 50)
        ema_12 = self._calculate_ema(close_prices, 12)
        ema_26 = self._calculate_ema(close_prices, 26)

        # ADX (14-period)
        adx = self._calculate_adx(high_prices, low_prices, close_prices, period=14)

        # Stochastic Oscillator (14, 3, 3)
        stoch_k, stoch_d = self._calculate_stochastic(high_prices, low_prices, close_prices)

        # Williams %R (14-period)
        williams_r = self._calculate_williams_r(high_prices, low_prices, close_prices, period=14)

        # MFI (Money Flow Index - 14-period)
        mfi = self._calculate_mfi(high_prices, low_prices, close_prices, volumes, period=14)

        # CCI (Commodity Channel Index - 20-period)
        cci = self._calculate_cci(high_prices, low_prices, close_prices, period=20)

        # OBV (On-Balance Volume)
        obv = self._calculate_obv(close_prices, volumes)

        return {
            'rsi': {
                'type': 'line',
                'data': {'dates': data['dates'], 'values': rsi.tolist()},
                'config': {
                    'title': 'RSI (14)',
                    'yaxis_title': 'RSI',
                    'yaxis_range': [0, 100],
                    'reference_lines': [{'value': 70, 'label': 'Overbought'}, {'value': 30, 'label': 'Oversold'}]
                }
            },
            'macd': {
                'type': 'multi_line',
                'data': {
                    'dates': data['dates'],
                    'macd': macd_line.tolist(),
                    'signal': signal_line.tolist(),
                    'histogram': histogram.tolist()
                },
                'config': {
                    'title': 'MACD',
                    'yaxis_title': 'MACD Value',
                    'colors': {'macd': '#2196F3', 'signal': '#FF9800', 'histogram': '#9E9E9E'}
                }
            },
            'bollinger_bands': {
                'type': 'bands',
                'data': {
                    'dates': data['dates'],
                    'upper': bb_upper.tolist(),
                    'middle': bb_middle.tolist(),
                    'lower': bb_lower.tolist(),
                    'price': data['close']
                },
                'config': {
                    'title': 'Bollinger Bands (20, 2)',
                    'yaxis_title': 'Price (USD)',
                    'colors': {'upper': '#F44336', 'middle': '#2196F3', 'lower': '#4CAF50'}
                }
            },
            'volume': {
                'type': 'bar',
                'data': {'dates': data['dates'], 'volume': data['volume']},
                'config': {
                    'title': 'Volume',
                    'yaxis_title': 'Volume',
                    'color_by_price_change': True
                }
            },
            'moving_averages': {
                'type': 'overlay',
                'data': {
                    'dates': data['dates'],
                    'price': data['close'],
                    'sma_20': sma_20.tolist(),
                    'sma_50': sma_50.tolist(),
                    'ema_12': ema_12.tolist(),
                    'ema_26': ema_26.tolist()
                },
                'config': {
                    'title': 'Moving Averages Overlay',
                    'legend': {'SMA 20': '#FF6B6B', 'SMA 50': '#4ECDC4', 'EMA 12': '#45B7D1', 'EMA 26': '#FFA07A'}
                }
            },
            'atr': {
                'type': 'line',
                'data': {'dates': data['dates'], 'values': atr.tolist()},
                'config': {
                    'title': 'Average True Range (14)',
                    'yaxis_title': 'ATR',
                    'color': '#9C27B0'
                }
            },
            'adx': {
                'type': 'line',
                'data': {'dates': data['dates'], 'values': adx.tolist()},
                'config': {
                    'title': 'ADX - Trend Strength (14)',
                    'yaxis_title': 'ADX',
                    'yaxis_range': [0, 100],
                    'reference_lines': [
                        {'value': 25, 'label': 'Strong Trend', 'color': '#4CAF50'},
                        {'value': 20, 'label': 'Weak Trend', 'color': '#FF9800'}
                    ],
                    'color': '#FF5722'
                }
            },
            'stochastic': {
                'type': 'multi_line',
                'data': {
                    'dates': data['dates'],
                    'k': stoch_k.tolist(),
                    'd': stoch_d.tolist()
                },
                'config': {
                    'title': 'Stochastic Oscillator (14, 3, 3)',
                    'yaxis_title': 'Stochastic',
                    'yaxis_range': [0, 100],
                    'reference_lines': [
                        {'value': 80, 'label': 'Overbought'},
                        {'value': 20, 'label': 'Oversold'}
                    ],
                    'colors': {'k': '#2196F3', 'd': '#FF9800'}
                }
            },
            'williams_r': {
                'type': 'line',
                'data': {'dates': data['dates'], 'values': williams_r.tolist()},
                'config': {
                    'title': 'Williams %R (14)',
                    'yaxis_title': 'Williams %R',
                    'yaxis_range': [-100, 0],
                    'reference_lines': [
                        {'value': -20, 'label': 'Overbought'},
                        {'value': -80, 'label': 'Oversold'}
                    ],
                    'color': '#9C27B0'
                }
            },
            'mfi': {
                'type': 'line',
                'data': {'dates': data['dates'], 'values': mfi.tolist()},
                'config': {
                    'title': 'Money Flow Index (14)',
                    'yaxis_title': 'MFI',
                    'yaxis_range': [0, 100],
                    'reference_lines': [
                        {'value': 80, 'label': 'Overbought'},
                        {'value': 20, 'label': 'Oversold'}
                    ],
                    'color': '#00BCD4'
                }
            },
            'cci': {
                'type': 'line',
                'data': {'dates': data['dates'], 'values': cci.tolist()},
                'config': {
                    'title': 'Commodity Channel Index (20)',
                    'yaxis_title': 'CCI',
                    'reference_lines': [
                        {'value': 100, 'label': 'Overbought'},
                        {'value': -100, 'label': 'Oversold'},
                        {'value': 0, 'label': 'Neutral'}
                    ],
                    'color': '#673AB7'
                }
            },
            'obv': {
                'type': 'line',
                'data': {'dates': data['dates'], 'values': obv.tolist()},
                'config': {
                    'title': 'On-Balance Volume',
                    'yaxis_title': 'OBV',
                    'color': '#607D8B'
                }
            }
        }

    def _generate_technical_overlays(self, data: Dict) -> Dict[str, Any]:
        """Generate technical overlays for main price chart."""
        close_prices = np.array(data['close'])

        return {
            'sma_20': self._calculate_sma(close_prices, 20).tolist(),
            'sma_50': self._calculate_sma(close_prices, 50).tolist(),
            'sma_200': self._calculate_sma(close_prices, 200).tolist(),
            'ema_12': self._calculate_ema(close_prices, 12).tolist(),
            'ema_26': self._calculate_ema(close_prices, 26).tolist(),
            'vwap': self._calculate_vwap(data).tolist()
        }

    def _analyze_chart_patterns(self, symbol: str, data: Dict) -> Dict[str, Any]:
        """Analyze chart patterns (Head & Shoulders, Double Top/Bottom, etc.)."""
        close_prices = np.array(data['close'])

        # Simple pattern detection (can be enhanced with ML)
        patterns_detected = []

        # Double Top/Bottom detection
        if self._detect_double_top(close_prices):
            patterns_detected.append({
                'pattern': 'Double Top',
                'type': 'bearish',
                'confidence': 0.7,
                'implication': 'Potential reversal downward'
            })

        if self._detect_double_bottom(close_prices):
            patterns_detected.append({
                'pattern': 'Double Bottom',
                'type': 'bullish',
                'confidence': 0.7,
                'implication': 'Potential reversal upward'
            })

        # Trend detection
        trend = self._detect_trend(close_prices)

        return {
            'patterns': patterns_detected,
            'current_trend': trend,
            'trend_strength': self._calculate_trend_strength(close_prices),
            'reversal_probability': self._calculate_reversal_probability(close_prices)
        }

    def _calculate_support_resistance(self, data: Dict) -> Dict[str, Any]:
        """Calculate support and resistance levels."""
        close_prices = np.array(data['close'])
        high_prices = np.array(data['high'])
        low_prices = np.array(data['low'])

        # Pivot Points
        pivot = (high_prices[-1] + low_prices[-1] + close_prices[-1]) / 3

        # Support levels
        support1 = (2 * pivot) - high_prices[-1]
        support2 = pivot - (high_prices[-1] - low_prices[-1])

        # Resistance levels
        resistance1 = (2 * pivot) - low_prices[-1]
        resistance2 = pivot + (high_prices[-1] - low_prices[-1])

        # Fibonacci retracements
        recent_high = np.max(high_prices[-60:])
        recent_low = np.min(low_prices[-60:])
        diff = recent_high - recent_low

        fib_levels = {
            '0.0%': recent_high,
            '23.6%': recent_high - (diff * 0.236),
            '38.2%': recent_high - (diff * 0.382),
            '50.0%': recent_high - (diff * 0.5),
            '61.8%': recent_high - (diff * 0.618),
            '100.0%': recent_low
        }

        return {
            'pivot_point': round(pivot, 2),
            'support_levels': [
                {'level': round(support2, 2), 'strength': 'strong', 'type': 'S2'},
                {'level': round(support1, 2), 'strength': 'moderate', 'type': 'S1'}
            ],
            'resistance_levels': [
                {'level': round(resistance1, 2), 'strength': 'moderate', 'type': 'R1'},
                {'level': round(resistance2, 2), 'strength': 'strong', 'type': 'R2'}
            ],
            'fibonacci_retracements': {k: round(v, 2) for k, v in fib_levels.items()},
            'current_price': round(close_prices[-1], 2),
            'nearest_support': round(max([s for s in [support1, support2] if s < close_prices[-1]], default=support2), 2),
            'nearest_resistance': round(min([r for r in [resistance1, resistance2] if r > close_prices[-1]], default=resistance1), 2)
        }

    def _analyze_volume_profile(self, data: Dict) -> Dict[str, Any]:
        """Analyze volume profile and distribution."""
        volumes = np.array(data['volume'])
        close_prices = np.array(data['close'])

        avg_volume = np.mean(volumes)
        volume_trend = 'increasing' if volumes[-10:].mean() > volumes[-30:-10].mean() else 'decreasing'

        # Volume-weighted average price
        vwap = np.sum(close_prices * volumes) / np.sum(volumes)

        # On-Balance Volume (OBV)
        obv = self._calculate_obv(close_prices, volumes)

        return {
            'average_volume': int(avg_volume),
            'current_volume': int(volumes[-1]),
            'volume_trend': volume_trend,
            'volume_ratio': round(volumes[-1] / avg_volume, 2),
            'vwap': round(vwap, 2),
            'obv_trend': 'bullish' if obv[-1] > obv[-10] else 'bearish',
            'high_volume_days': int(np.sum(volumes > avg_volume * 1.5)),
            'volume_spikes': self._detect_volume_spikes(volumes)
        }

    def _multi_timeframe_analysis(self, symbol: str) -> Dict[str, Any]:
        """Multi-timeframe trend analysis."""
        timeframes = {}

        for period, label in [('1mo', 'weekly'), ('3mo', 'monthly'), ('1y', 'quarterly')]:
            try:
                ticker = yf.Ticker(symbol)
                hist = ticker.history(period=period)
                close_prices = hist['Close'].values

                trend = self._detect_trend(close_prices)
                strength = self._calculate_trend_strength(close_prices)

                timeframes[label] = {
                    'trend': trend,
                    'strength': strength,
                    'alignment': 'aligned' if trend == self._detect_trend(close_prices[-10:]) else 'diverging'
                }
            except:
                timeframes[label] = {'trend': 'unknown', 'strength': 0, 'alignment': 'unknown'}

        return timeframes

    def _generate_expert_insights(self, patterns: Dict, sr: Dict, mtf: Dict) -> List[str]:
        """Generate expert trader insights from chart analysis."""
        insights = []

        # Pattern insights
        if patterns.get('patterns'):
            for pattern in patterns['patterns']:
                insights.append(f"📊 {pattern['pattern']} detected ({pattern['type']}) - {pattern['implication']}")

        # Trend insights
        if patterns.get('current_trend'):
            insights.append(f"📈 Current trend: {patterns['current_trend'].upper()} with {patterns.get('trend_strength', 'moderate')} strength")

        # Support/Resistance insights
        current_price = sr.get('current_price', 0)
        nearest_support = sr.get('nearest_support', 0)
        nearest_resistance = sr.get('nearest_resistance', 0)

        if current_price:
            support_distance = ((current_price - nearest_support) / current_price) * 100
            resistance_distance = ((nearest_resistance - current_price) / current_price) * 100

            insights.append(f"🎯 Nearest support: ${nearest_support} ({support_distance:.1f}% below)")
            insights.append(f"🚧 Nearest resistance: ${nearest_resistance} ({resistance_distance:.1f}% above)")

        # Multi-timeframe alignment
        trends = [v['trend'] for v in mtf.values() if v['trend'] != 'unknown']
        if trends and len(set(trends)) == 1:
            insights.append(f"⚡ Multi-timeframe alignment: All timeframes show {trends[0].upper()} trend")

        return insights

    # Technical Indicator Calculations
    def _calculate_rsi(self, prices: np.ndarray, period: int = 14) -> np.ndarray:
        """Calculate Relative Strength Index."""
        deltas = np.diff(prices)
        gains = np.where(deltas > 0, deltas, 0)
        losses = np.where(deltas < 0, -deltas, 0)

        avg_gains = np.convolve(gains, np.ones(period)/period, mode='valid')
        avg_losses = np.convolve(losses, np.ones(period)/period, mode='valid')

        rs = avg_gains / (avg_losses + 1e-10)
        rsi = 100 - (100 / (1 + rs))

        return np.concatenate([np.full(period, 50), rsi])  # Pad with neutral 50

    def _calculate_macd(self, prices: np.ndarray) -> tuple:
        """Calculate MACD, Signal line, and Histogram."""
        ema_12 = self._calculate_ema(prices, 12)
        ema_26 = self._calculate_ema(prices, 26)

        macd_line = ema_12 - ema_26
        signal_line = self._calculate_ema(macd_line, 9)
        histogram = macd_line - signal_line

        return macd_line, signal_line, histogram

    def _calculate_bollinger_bands(self, prices: np.ndarray, period: int = 20, std_dev: float = 2) -> tuple:
        """Calculate Bollinger Bands."""
        sma = self._calculate_sma(prices, period)
        rolling_std = np.array([np.std(prices[max(0, i-period):i+1]) for i in range(len(prices))])

        upper_band = sma + (rolling_std * std_dev)
        lower_band = sma - (rolling_std * std_dev)

        return upper_band, sma, lower_band

    def _calculate_atr(self, high: np.ndarray, low: np.ndarray, close: np.ndarray, period: int = 14) -> np.ndarray:
        """Calculate Average True Range."""
        tr1 = high - low
        tr2 = np.abs(high - np.roll(close, 1))
        tr3 = np.abs(low - np.roll(close, 1))

        tr = np.maximum(tr1, np.maximum(tr2, tr3))
        tr[0] = tr1[0]  # First value

        atr = np.convolve(tr, np.ones(period)/period, mode='same')
        return atr

    def _calculate_sma(self, prices: np.ndarray, period: int) -> np.ndarray:
        """Calculate Simple Moving Average."""
        return np.convolve(prices, np.ones(period)/period, mode='same')

    def _calculate_ema(self, prices: np.ndarray, period: int) -> np.ndarray:
        """Calculate Exponential Moving Average."""
        alpha = 2 / (period + 1)
        ema = np.zeros_like(prices)
        ema[0] = prices[0]

        for i in range(1, len(prices)):
            ema[i] = alpha * prices[i] + (1 - alpha) * ema[i-1]

        return ema

    def _calculate_vwap(self, data: Dict) -> np.ndarray:
        """Calculate Volume Weighted Average Price."""
        close = np.array(data['close'])
        volume = np.array(data['volume'])

        cumulative_pv = np.cumsum(close * volume)
        cumulative_volume = np.cumsum(volume)

        return cumulative_pv / (cumulative_volume + 1e-10)

    def _calculate_obv(self, close: np.ndarray, volume: np.ndarray) -> np.ndarray:
        """Calculate On-Balance Volume."""
        obv = np.zeros_like(close)
        obv[0] = volume[0]

        for i in range(1, len(close)):
            if close[i] > close[i-1]:
                obv[i] = obv[i-1] + volume[i]
            elif close[i] < close[i-1]:
                obv[i] = obv[i-1] - volume[i]
            else:
                obv[i] = obv[i-1]

        return obv

    def _detect_trend(self, prices: np.ndarray) -> str:
        """Detect current trend direction."""
        if len(prices) < 20:
            return 'neutral'

        recent_slope = np.polyfit(range(20), prices[-20:], 1)[0]

        if recent_slope > prices[-1] * 0.001:
            return 'bullish'
        elif recent_slope < -prices[-1] * 0.001:
            return 'bearish'
        else:
            return 'neutral'

    def _calculate_trend_strength(self, prices: np.ndarray) -> str:
        """Calculate trend strength."""
        if len(prices) < 20:
            return 'weak'

        slope = abs(np.polyfit(range(20), prices[-20:], 1)[0])
        relative_slope = slope / prices[-1]

        if relative_slope > 0.003:
            return 'strong'
        elif relative_slope > 0.001:
            return 'moderate'
        else:
            return 'weak'

    def _calculate_reversal_probability(self, prices: np.ndarray) -> float:
        """Calculate probability of trend reversal."""
        # Simple heuristic based on recent volatility and momentum
        if len(prices) < 30:
            return 0.5

        recent_std = np.std(prices[-10:])
        longer_std = np.std(prices[-30:])

        volatility_ratio = recent_std / (longer_std + 1e-10)

        if volatility_ratio > 1.5:
            return 0.7
        elif volatility_ratio > 1.2:
            return 0.5
        else:
            return 0.3

    def _detect_double_top(self, prices: np.ndarray) -> bool:
        """Detect double top pattern."""
        if len(prices) < 50:
            return False

        recent_prices = prices[-50:]
        peaks = []

        for i in range(2, len(recent_prices)-2):
            if recent_prices[i] > recent_prices[i-1] and recent_prices[i] > recent_prices[i+1]:
                peaks.append((i, recent_prices[i]))

        if len(peaks) >= 2:
            last_two_peaks = peaks[-2:]
            if abs(last_two_peaks[0][1] - last_two_peaks[1][1]) < recent_prices[-1] * 0.02:
                return True

        return False

    def _detect_double_bottom(self, prices: np.ndarray) -> bool:
        """Detect double bottom pattern."""
        if len(prices) < 50:
            return False

        recent_prices = prices[-50:]
        troughs = []

        for i in range(2, len(recent_prices)-2):
            if recent_prices[i] < recent_prices[i-1] and recent_prices[i] < recent_prices[i+1]:
                troughs.append((i, recent_prices[i]))

        if len(troughs) >= 2:
            last_two_troughs = troughs[-2:]
            if abs(last_two_troughs[0][1] - last_two_troughs[1][1]) < recent_prices[-1] * 0.02:
                return True

        return False

    def _detect_volume_spikes(self, volumes: np.ndarray) -> List[Dict]:
        """Detect significant volume spikes."""
        avg_volume = np.mean(volumes)
        spikes = []

        for i in range(len(volumes)-10, len(volumes)):
            if volumes[i] > avg_volume * 2:
                spikes.append({
                    'date_index': i,
                    'volume': int(volumes[i]),
                    'multiplier': round(volumes[i] / avg_volume, 2)
                })

        return spikes[-3:] if spikes else []  # Return last 3 spikes

    def _calculate_adx(self, high: np.ndarray, low: np.ndarray, close: np.ndarray, period: int = 14) -> np.ndarray:
        """Calculate Average Directional Index (ADX)."""
        # Calculate +DI and -DI
        plus_dm = np.diff(high)
        minus_dm = -np.diff(low)

        plus_dm = np.where((plus_dm > minus_dm) & (plus_dm > 0), plus_dm, 0)
        minus_dm = np.where((minus_dm > plus_dm) & (minus_dm > 0), minus_dm, 0)

        # True Range
        tr = np.maximum(high[1:] - low[1:],
                        np.maximum(abs(high[1:] - close[:-1]),
                                 abs(low[1:] - close[:-1])))

        # Smooth with EMA
        plus_di = 100 * np.convolve(plus_dm, np.ones(period)/period, mode='same') / (np.convolve(tr, np.ones(period)/period, mode='same') + 1e-10)
        minus_di = 100 * np.convolve(minus_dm, np.ones(period)/period, mode='same') / (np.convolve(tr, np.ones(period)/period, mode='same') + 1e-10)

        # Calculate DX and ADX
        dx = 100 * abs(plus_di - minus_di) / (plus_di + minus_di + 1e-10)
        adx = np.convolve(dx, np.ones(period)/period, mode='same')

        return np.concatenate([np.full(1, 25), adx])  # Pad to match length

    def _calculate_stochastic(self, high: np.ndarray, low: np.ndarray, close: np.ndarray, k_period: int = 14, d_period: int = 3) -> tuple:
        """Calculate Stochastic Oscillator (%K and %D)."""
        stoch_k = np.zeros_like(close)

        for i in range(k_period - 1, len(close)):
            period_high = np.max(high[i-k_period+1:i+1])
            period_low = np.min(low[i-k_period+1:i+1])

            if period_high - period_low != 0:
                stoch_k[i] = 100 * (close[i] - period_low) / (period_high - period_low)
            else:
                stoch_k[i] = 50

        # %D is SMA of %K
        stoch_d = self._calculate_sma(stoch_k, d_period)

        return stoch_k, stoch_d

    def _calculate_williams_r(self, high: np.ndarray, low: np.ndarray, close: np.ndarray, period: int = 14) -> np.ndarray:
        """Calculate Williams %R."""
        williams_r = np.zeros_like(close)

        for i in range(period - 1, len(close)):
            period_high = np.max(high[i-period+1:i+1])
            period_low = np.min(low[i-period+1:i+1])

            if period_high - period_low != 0:
                williams_r[i] = -100 * (period_high - close[i]) / (period_high - period_low)
            else:
                williams_r[i] = -50

        return williams_r

    def _calculate_mfi(self, high: np.ndarray, low: np.ndarray, close: np.ndarray, volume: np.ndarray, period: int = 14) -> np.ndarray:
        """Calculate Money Flow Index (MFI)."""
        typical_price = (high + low + close) / 3
        money_flow = typical_price * volume

        mfi = np.zeros_like(close)

        for i in range(period, len(close)):
            positive_flow = np.sum(money_flow[i-period:i][np.diff(typical_price[i-period-1:i]) > 0])
            negative_flow = np.sum(money_flow[i-period:i][np.diff(typical_price[i-period-1:i]) < 0])

            if negative_flow != 0:
                money_ratio = positive_flow / (negative_flow + 1e-10)
                mfi[i] = 100 - (100 / (1 + money_ratio))
            else:
                mfi[i] = 100

        return mfi

    def _calculate_cci(self, high: np.ndarray, low: np.ndarray, close: np.ndarray, period: int = 20) -> np.ndarray:
        """Calculate Commodity Channel Index (CCI)."""
        typical_price = (high + low + close) / 3
        sma_tp = self._calculate_sma(typical_price, period)

        cci = np.zeros_like(close)

        for i in range(period - 1, len(close)):
            mean_deviation = np.mean(np.abs(typical_price[i-period+1:i+1] - sma_tp[i]))

            if mean_deviation != 0:
                cci[i] = (typical_price[i] - sma_tp[i]) / (0.015 * mean_deviation)
            else:
                cci[i] = 0

        return cci
