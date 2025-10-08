"""
Chart Pattern Recognition
Detects classic technical analysis patterns in price data
CRITICAL for professional traders
"""

import logging
from typing import Dict, Any, List, Optional, Tuple
import numpy as np
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)


class PatternDetector:
    """
    Detects chart patterns in OHLCV data

    Patterns detected:
    - Head and Shoulders (bearish reversal)
    - Inverse Head and Shoulders (bullish reversal)
    - Double Top (bearish reversal)
    - Double Bottom (bullish reversal)
    - Ascending/Descending Triangles
    - Channels (ascending, descending, horizontal)
    - Cup and Handle (bullish continuation)
    - Wedges (rising, falling)
    """

    def __init__(self):
        self.name = "PatternDetector"

    def detect_patterns(self, ohlc_data: List[Dict]) -> Dict[str, Any]:
        """
        Detect all patterns in price data

        Args:
            ohlc_data: List of OHLC candles [{date, open, high, low, close, volume}]

        Returns:
            Detected patterns with confidence scores
        """

        if len(ohlc_data) < 20:
            return {'error': 'Insufficient data (need 20+ candles)'}

        try:
            # Extract arrays
            closes = np.array([c['close'] for c in ohlc_data])
            highs = np.array([c['high'] for c in ohlc_data])
            lows = np.array([c['low'] for c in ohlc_data])
            volumes = np.array([c.get('volume', 0) for c in ohlc_data])

            patterns = []

            # Reversal patterns
            patterns.extend(self._detect_head_and_shoulders(highs, lows, closes))
            patterns.extend(self._detect_double_top_bottom(highs, lows, closes))

            # Continuation patterns
            patterns.extend(self._detect_triangles(highs, lows, closes))
            patterns.extend(self._detect_channels(highs, lows, closes))
            patterns.extend(self._detect_cup_and_handle(closes, highs, lows))
            patterns.extend(self._detect_wedges(highs, lows, closes))

            # Support/Resistance levels
            support_resistance = self._detect_support_resistance(highs, lows, closes)

            return {
                'patterns_detected': len(patterns),
                'patterns': patterns,
                'support_resistance': support_resistance,
                'current_price': float(closes[-1]),
                'pattern_summary': self._generate_pattern_summary(patterns),
                'trading_signals': self._generate_trading_signals(patterns, closes[-1]),
                'timestamp': datetime.utcnow().isoformat()
            }

        except Exception as e:
            logger.error(f"[{self.name}] Pattern detection failed: {e}")
            return {'error': str(e)}

    def _detect_head_and_shoulders(self, highs: np.ndarray, lows: np.ndarray, closes: np.ndarray) -> List[Dict]:
        """Detect Head and Shoulders pattern (bearish reversal)"""

        patterns = []
        window = 20  # Look at recent 20 candles

        if len(highs) < window:
            return patterns

        recent_highs = highs[-window:]
        recent_lows = lows[-window:]

        # Find peaks (local maxima)
        peaks = []
        for i in range(2, len(recent_highs) - 2):
            if (recent_highs[i] > recent_highs[i-1] and
                recent_highs[i] > recent_highs[i-2] and
                recent_highs[i] > recent_highs[i+1] and
                recent_highs[i] > recent_highs[i+2]):
                peaks.append((i, recent_highs[i]))

        # Need 3 peaks for head and shoulders
        if len(peaks) >= 3:
            # Check if middle peak (head) is higher than shoulders
            left_shoulder = peaks[0]
            head = peaks[1]
            right_shoulder = peaks[2]

            if (head[1] > left_shoulder[1] and
                head[1] > right_shoulder[1] and
                abs(left_shoulder[1] - right_shoulder[1]) / left_shoulder[1] < 0.05):  # Shoulders similar height

                # Calculate neckline
                neckline = (recent_lows[left_shoulder[0]] + recent_lows[right_shoulder[0]]) / 2

                patterns.append({
                    'pattern': 'Head and Shoulders',
                    'type': 'bearish_reversal',
                    'confidence': 0.75,
                    'neckline': float(neckline),
                    'target': float(neckline - (head[1] - neckline)),  # Measured move
                    'invalidation': float(head[1]),
                    'description': 'Bearish reversal pattern - expect breakdown below neckline',
                    'formation_complete': float(closes[-1]) < neckline
                })

        # Inverse Head and Shoulders (bullish)
        troughs = []
        for i in range(2, len(recent_lows) - 2):
            if (recent_lows[i] < recent_lows[i-1] and
                recent_lows[i] < recent_lows[i-2] and
                recent_lows[i] < recent_lows[i+1] and
                recent_lows[i] < recent_lows[i+2]):
                troughs.append((i, recent_lows[i]))

        if len(troughs) >= 3:
            left_shoulder = troughs[0]
            head = troughs[1]
            right_shoulder = troughs[2]

            if (head[1] < left_shoulder[1] and
                head[1] < right_shoulder[1] and
                abs(left_shoulder[1] - right_shoulder[1]) / left_shoulder[1] < 0.05):

                neckline = (recent_highs[left_shoulder[0]] + recent_highs[right_shoulder[0]]) / 2

                patterns.append({
                    'pattern': 'Inverse Head and Shoulders',
                    'type': 'bullish_reversal',
                    'confidence': 0.75,
                    'neckline': float(neckline),
                    'target': float(neckline + (neckline - head[1])),
                    'invalidation': float(head[1]),
                    'description': 'Bullish reversal pattern - expect breakout above neckline',
                    'formation_complete': float(closes[-1]) > neckline
                })

        return patterns

    def _detect_double_top_bottom(self, highs: np.ndarray, lows: np.ndarray, closes: np.ndarray) -> List[Dict]:
        """Detect Double Top/Bottom patterns"""

        patterns = []
        window = 15

        if len(highs) < window:
            return patterns

        recent_highs = highs[-window:]
        recent_lows = lows[-window:]

        # Double Top (bearish)
        peaks = []
        for i in range(1, len(recent_highs) - 1):
            if recent_highs[i] > recent_highs[i-1] and recent_highs[i] > recent_highs[i+1]:
                peaks.append((i, recent_highs[i]))

        if len(peaks) >= 2:
            last_two_peaks = peaks[-2:]
            if abs(last_two_peaks[0][1] - last_two_peaks[1][1]) / last_two_peaks[0][1] < 0.03:  # Within 3%
                # Found double top
                support = float(np.min(recent_lows[last_two_peaks[0][0]:last_two_peaks[1][0]]))
                peak_level = float(last_two_peaks[1][1])

                patterns.append({
                    'pattern': 'Double Top',
                    'type': 'bearish_reversal',
                    'confidence': 0.70,
                    'resistance': peak_level,
                    'support': support,
                    'target': float(support - (peak_level - support)),
                    'invalidation': peak_level,
                    'description': 'Bearish reversal - breakdown below support confirms pattern',
                    'formation_complete': float(closes[-1]) < support
                })

        # Double Bottom (bullish)
        troughs = []
        for i in range(1, len(recent_lows) - 1):
            if recent_lows[i] < recent_lows[i-1] and recent_lows[i] < recent_lows[i+1]:
                troughs.append((i, recent_lows[i]))

        if len(troughs) >= 2:
            last_two_troughs = troughs[-2:]
            if abs(last_two_troughs[0][1] - last_two_troughs[1][1]) / last_two_troughs[0][1] < 0.03:
                resistance = float(np.max(recent_highs[last_two_troughs[0][0]:last_two_troughs[1][0]]))
                trough_level = float(last_two_troughs[1][1])

                patterns.append({
                    'pattern': 'Double Bottom',
                    'type': 'bullish_reversal',
                    'confidence': 0.70,
                    'support': trough_level,
                    'resistance': resistance,
                    'target': float(resistance + (resistance - trough_level)),
                    'invalidation': trough_level,
                    'description': 'Bullish reversal - breakout above resistance confirms pattern',
                    'formation_complete': float(closes[-1]) > resistance
                })

        return patterns

    def _detect_triangles(self, highs: np.ndarray, lows: np.ndarray, closes: np.ndarray) -> List[Dict]:
        """Detect triangle patterns (ascending, descending, symmetrical)"""

        patterns = []
        window = 20

        if len(highs) < window:
            return patterns

        recent_highs = highs[-window:]
        recent_lows = lows[-window:]

        # Fit trendlines
        x = np.arange(len(recent_highs))

        # Upper trendline (resistance)
        upper_slope, upper_intercept = np.polyfit(x, recent_highs, 1)

        # Lower trendline (support)
        lower_slope, lower_intercept = np.polyfit(x, recent_lows, 1)

        # Ascending Triangle: flat resistance, rising support
        if abs(upper_slope) < 0.1 and lower_slope > 0.1:
            apex = float(recent_highs[-1])
            patterns.append({
                'pattern': 'Ascending Triangle',
                'type': 'bullish_continuation',
                'confidence': 0.65,
                'resistance': apex,
                'support': float(lower_intercept + lower_slope * len(x)),
                'target': float(apex + (apex - recent_lows[0])),
                'description': 'Bullish continuation - breakout above resistance expected',
                'formation_complete': float(closes[-1]) > apex
            })

        # Descending Triangle: falling resistance, flat support
        if upper_slope < -0.1 and abs(lower_slope) < 0.1:
            apex = float(recent_lows[-1])
            patterns.append({
                'pattern': 'Descending Triangle',
                'type': 'bearish_continuation',
                'confidence': 0.65,
                'resistance': float(upper_intercept + upper_slope * len(x)),
                'support': apex,
                'target': float(apex - (recent_highs[0] - apex)),
                'description': 'Bearish continuation - breakdown below support expected',
                'formation_complete': float(closes[-1]) < apex
            })

        return patterns

    def _detect_channels(self, highs: np.ndarray, lows: np.ndarray, closes: np.ndarray) -> List[Dict]:
        """Detect price channels"""

        patterns = []
        window = 30

        if len(highs) < window:
            return patterns

        recent_highs = highs[-window:]
        recent_lows = lows[-window:]
        recent_closes = closes[-window:]

        x = np.arange(len(recent_highs))

        # Fit parallel trendlines
        upper_slope, upper_intercept = np.polyfit(x, recent_highs, 1)
        lower_slope, lower_intercept = np.polyfit(x, recent_lows, 1)

        # Check if slopes are similar (parallel channel)
        if abs(upper_slope - lower_slope) < 0.05:
            channel_type = 'ascending' if upper_slope > 0.1 else 'descending' if upper_slope < -0.1 else 'horizontal'

            upper_line = float(upper_intercept + upper_slope * (len(x) - 1))
            lower_line = float(lower_intercept + lower_slope * (len(x) - 1))

            patterns.append({
                'pattern': f'{channel_type.capitalize()} Channel',
                'type': 'continuation',
                'confidence': 0.60,
                'upper_bound': upper_line,
                'lower_bound': lower_line,
                'description': f'{channel_type.capitalize()} channel - trade within bounds',
                'trading_strategy': f'Buy near {lower_line:.2f}, sell near {upper_line:.2f}'
            })

        return patterns

    def _detect_cup_and_handle(self, closes: np.ndarray, highs: np.ndarray, lows: np.ndarray) -> List[Dict]:
        """Detect Cup and Handle pattern (bullish)"""

        patterns = []
        window = 40

        if len(closes) < window:
            return patterns

        recent = closes[-window:]

        # Find cup (U-shape)
        # Look for: high -> low -> high pattern
        first_third = recent[:window//3]
        middle_third = recent[window//3:2*window//3]
        last_third = recent[2*window//3:]

        if (np.mean(first_third) > np.mean(middle_third) and
            np.mean(last_third) > np.mean(middle_third) and
            np.min(middle_third) < np.min(first_third) * 0.90):  # At least 10% dip

            # Check for handle (small pullback in last third)
            if np.max(last_third) > np.mean(last_third) * 1.02:
                rim = float(np.max(first_third))
                handle_low = float(np.min(last_third[-5:]))

                patterns.append({
                    'pattern': 'Cup and Handle',
                    'type': 'bullish_continuation',
                    'confidence': 0.70,
                    'rim': rim,
                    'handle_low': handle_low,
                    'target': float(rim + (rim - np.min(middle_third))),
                    'description': 'Bullish continuation - breakout above rim expected',
                    'formation_complete': float(closes[-1]) > rim
                })

        return patterns

    def _detect_wedges(self, highs: np.ndarray, lows: np.ndarray, closes: np.ndarray) -> List[Dict]:
        """Detect wedge patterns (rising, falling)"""

        patterns = []
        window = 25

        if len(highs) < window:
            return patterns

        recent_highs = highs[-window:]
        recent_lows = lows[-window:]

        x = np.arange(len(recent_highs))

        upper_slope, _ = np.polyfit(x, recent_highs, 1)
        lower_slope, _ = np.polyfit(x, recent_lows, 1)

        # Rising Wedge: both slopes positive, converging (bearish)
        if upper_slope > 0 and lower_slope > 0 and lower_slope > upper_slope:
            patterns.append({
                'pattern': 'Rising Wedge',
                'type': 'bearish_reversal',
                'confidence': 0.65,
                'description': 'Bearish reversal - breakdown expected despite uptrend',
                'target': float(recent_lows[0])
            })

        # Falling Wedge: both slopes negative, converging (bullish)
        if upper_slope < 0 and lower_slope < 0 and upper_slope < lower_slope:
            patterns.append({
                'pattern': 'Falling Wedge',
                'type': 'bullish_reversal',
                'confidence': 0.65,
                'description': 'Bullish reversal - breakout expected despite downtrend',
                'target': float(recent_highs[0])
            })

        return patterns

    def _detect_support_resistance(self, highs: np.ndarray, lows: np.ndarray, closes: np.ndarray) -> Dict[str, Any]:
        """Detect key support and resistance levels"""

        window = 30
        recent_highs = highs[-window:]
        recent_lows = lows[-window:]
        current_price = float(closes[-1])

        # Find resistance levels (local maxima)
        resistance_levels = []
        for i in range(2, len(recent_highs) - 2):
            if (recent_highs[i] > recent_highs[i-1] and
                recent_highs[i] > recent_highs[i-2] and
                recent_highs[i] > recent_highs[i+1]):
                resistance_levels.append(float(recent_highs[i]))

        # Find support levels (local minima)
        support_levels = []
        for i in range(2, len(recent_lows) - 2):
            if (recent_lows[i] < recent_lows[i-1] and
                recent_lows[i] < recent_lows[i-2] and
                recent_lows[i] < recent_lows[i+1]):
                support_levels.append(float(recent_lows[i]))

        # Cluster nearby levels
        resistance_levels = self._cluster_levels(resistance_levels, current_price)
        support_levels = self._cluster_levels(support_levels, current_price)

        return {
            'resistance_levels': resistance_levels[:3],  # Top 3
            'support_levels': support_levels[:3],
            'nearest_resistance': min([r for r in resistance_levels if r > current_price], default=None),
            'nearest_support': max([s for s in support_levels if s < current_price], default=None)
        }

    def _cluster_levels(self, levels: List[float], current_price: float) -> List[float]:
        """Cluster nearby levels within 2% of each other"""

        if not levels:
            return []

        clustered = []
        sorted_levels = sorted(levels)

        i = 0
        while i < len(sorted_levels):
            cluster = [sorted_levels[i]]
            j = i + 1

            while j < len(sorted_levels):
                if abs(sorted_levels[j] - sorted_levels[i]) / sorted_levels[i] < 0.02:
                    cluster.append(sorted_levels[j])
                    j += 1
                else:
                    break

            # Use median of cluster
            clustered.append(np.median(cluster))
            i = j

        return clustered

    def _generate_pattern_summary(self, patterns: List[Dict]) -> str:
        """Generate human-readable pattern summary"""

        if not patterns:
            return "No significant patterns detected"

        bullish = [p for p in patterns if 'bullish' in p['type']]
        bearish = [p for p in patterns if 'bearish' in p['type']]

        summary = f"Detected {len(patterns)} pattern(s): "

        if bullish and bearish:
            summary += f"{len(bullish)} bullish, {len(bearish)} bearish - mixed signals"
        elif bullish:
            summary += f"{len(bullish)} bullish pattern(s) - upside potential"
        elif bearish:
            summary += f"{len(bearish)} bearish pattern(s) - downside risk"

        # Highest confidence pattern
        if patterns:
            top_pattern = max(patterns, key=lambda p: p.get('confidence', 0))
            summary += f". Strongest: {top_pattern['pattern']} ({top_pattern['confidence']*100:.0f}% confidence)"

        return summary

    def _generate_trading_signals(self, patterns: List[Dict], current_price: float) -> List[str]:
        """Generate actionable trading signals from patterns"""

        signals = []

        for pattern in patterns:
            if pattern.get('formation_complete'):
                if 'bullish' in pattern['type']:
                    target = pattern.get('target')
                    if target:
                        signals.append(f"{pattern['pattern']}: BUY signal - target ${target:.2f} (+{((target/current_price)-1)*100:.1f}%)")
                elif 'bearish' in pattern['type']:
                    target = pattern.get('target')
                    if target:
                        signals.append(f"{pattern['pattern']}: SELL signal - target ${target:.2f} ({((target/current_price)-1)*100:.1f}%)")
            else:
                signals.append(f"{pattern['pattern']}: Watch for confirmation (not complete)")

        return signals
