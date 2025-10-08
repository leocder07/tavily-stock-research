"""
Position Sizing Calculator
Calculates optimal position sizes based on risk management principles
Uses Kelly Criterion and Fixed Fractional methods
"""

import logging
from typing import Dict, Any, Optional, Union
from enum import Enum

# Import value extraction utilities
try:
    from utils.value_extractors import extract_numeric_value, calculate_risk_reward_ratio
except ImportError:
    # Fallback inline definitions if import fails
    def extract_numeric_value(data: Any, field_name: str = "value", default: float = 0.0) -> float:
        """Extract numeric value from dict or direct number"""
        if data is None:
            return default
        if isinstance(data, (int, float)):
            return float(data)
        if isinstance(data, dict) and 'value' in data:
            value = data['value']
            if isinstance(value, (int, float)):
                return float(value)
        return default

    def calculate_risk_reward_ratio(
        entry_price: Union[float, Any],
        target_price: Union[float, Any],
        stop_loss: Union[float, Any],
        field_prefix: str = "position"
    ) -> Optional[float]:
        """Calculate risk/reward ratio"""
        entry = extract_numeric_value(entry_price, f"{field_prefix}_entry_price")
        target = extract_numeric_value(target_price, f"{field_prefix}_target_price")
        stop = extract_numeric_value(stop_loss, f"{field_prefix}_stop_loss")

        if entry is None or target is None or stop is None or entry <= 0 or stop >= entry or target <= entry:
            return None

        risk_reward_ratio = (target - entry) / (entry - stop)
        return round(risk_reward_ratio, 2)

logger = logging.getLogger(__name__)


class PositionSizeMethod(str, Enum):
    """Position sizing methods"""
    FIXED_FRACTIONAL = "fixed_fractional"  # Fixed % of capital at risk
    KELLY_CRITERION = "kelly_criterion"    # Kelly formula for optimal sizing
    VOLATILITY_ADJUSTED = "volatility_adjusted"  # Adjust for stock volatility


class PositionSizer:
    """
    Position sizing calculator for risk management

    Critical for converting recommendations into actionable trades
    Tells traders HOW MANY shares to buy, not just BUY/SELL
    """

    def __init__(self):
        self.name = "PositionSizer"

    def calculate_position_size(
        self,
        account_value: float,
        entry_price: float,
        stop_loss_price: float,
        risk_per_trade_pct: float = 1.0,
        method: PositionSizeMethod = PositionSizeMethod.FIXED_FRACTIONAL,
        win_rate: Optional[float] = None,
        avg_win_loss_ratio: Optional[float] = None,
        volatility: Optional[float] = None
    ) -> Dict[str, Any]:
        """
        Calculate position size based on risk parameters

        Args:
            account_value: Total account value ($)
            entry_price: Entry price per share ($)
            stop_loss_price: Stop loss price ($)
            risk_per_trade_pct: % of account to risk (default 1%)
            method: Position sizing method
            win_rate: Win rate for Kelly (0-1)
            avg_win_loss_ratio: Average win/loss ratio for Kelly
            volatility: Annualized volatility for volatility-adjusted method

        Returns:
            {
                'shares': int,
                'position_value': float,
                'capital_at_risk': float,
                'position_pct': float,
                'method': str,
                'risk_reward_ratio': float
            }
        """

        # Extract numeric values safely (handle dict/float types)
        entry_val = extract_numeric_value(entry_price, "entry_price", 0.0)
        stop_val = extract_numeric_value(stop_loss_price, "stop_loss", 0.0)

        if entry_val <= 0 or stop_val <= 0:
            return self._error_result("Invalid prices")

        if account_value <= 0:
            return self._error_result("Invalid account value")

        # Calculate risk per share
        risk_per_share = abs(entry_val - stop_val)

        if risk_per_share == 0:
            return self._error_result("Entry and stop loss cannot be the same")

        try:
            if method == PositionSizeMethod.FIXED_FRACTIONAL:
                result = self._fixed_fractional(
                    account_value,
                    entry_val,
                    risk_per_share,
                    risk_per_trade_pct
                )

            elif method == PositionSizeMethod.KELLY_CRITERION:
                result = self._kelly_criterion(
                    account_value,
                    entry_val,
                    risk_per_share,
                    win_rate,
                    avg_win_loss_ratio
                )

            elif method == PositionSizeMethod.VOLATILITY_ADJUSTED:
                result = self._volatility_adjusted(
                    account_value,
                    entry_val,
                    risk_per_share,
                    risk_per_trade_pct,
                    volatility
                )

            else:
                result = self._fixed_fractional(
                    account_value,
                    entry_price,
                    risk_per_share,
                    risk_per_trade_pct
                )

            result['method'] = method.value
            return result

        except Exception as e:
            logger.error(f"[{self.name}] Position sizing failed: {e}")
            return self._error_result(str(e))

    def _fixed_fractional(
        self,
        account_value: float,
        entry_price: float,
        risk_per_share: float,
        risk_pct: float
    ) -> Dict[str, Any]:
        """
        Fixed Fractional Position Sizing
        Risk a fixed % of account on each trade

        Formula: Shares = (Account Value * Risk %) / Risk per Share
        """

        # Capital at risk
        capital_at_risk = account_value * (risk_pct / 100)

        # Number of shares
        shares = int(capital_at_risk / risk_per_share)

        # Ensure at least 1 share if affordable
        if shares == 0 and entry_price <= capital_at_risk:
            shares = 1

        # Position value
        position_value = shares * entry_price

        # Position as % of account
        position_pct = (position_value / account_value) * 100

        return {
            'shares': shares,
            'position_value': round(position_value, 2),
            'capital_at_risk': round(capital_at_risk, 2),
            'position_pct': round(position_pct, 2),
            'risk_per_trade_pct': risk_pct,
            'risk_reward_ratio': None  # Set by caller
        }

    def _kelly_criterion(
        self,
        account_value: float,
        entry_price: float,
        risk_per_share: float,
        win_rate: Optional[float],
        avg_win_loss_ratio: Optional[float]
    ) -> Dict[str, Any]:
        """
        Kelly Criterion Position Sizing
        Mathematically optimal sizing based on edge

        Formula: Kelly % = W - [(1-W) / R]
        Where: W = win rate, R = avg win/loss ratio

        Note: Use fractional Kelly (25-50%) to reduce volatility
        """

        # Default to conservative values if not provided
        W = win_rate if win_rate is not None else 0.50  # 50% win rate
        R = avg_win_loss_ratio if avg_win_loss_ratio is not None else 2.0  # 2:1 win/loss

        # Calculate Kelly %
        kelly_pct = W - ((1 - W) / R)

        # Use fractional Kelly (25%) for safety
        fractional_kelly = kelly_pct * 0.25

        # Ensure kelly % is reasonable (max 5% of account)
        kelly_pct_capped = max(0, min(fractional_kelly * 100, 5.0))

        # Use fixed fractional with Kelly %
        return self._fixed_fractional(
            account_value,
            entry_price,
            risk_per_share,
            kelly_pct_capped
        )

    def _volatility_adjusted(
        self,
        account_value: float,
        entry_price: float,
        risk_per_share: float,
        base_risk_pct: float,
        volatility: Optional[float]
    ) -> Dict[str, Any]:
        """
        Volatility-Adjusted Position Sizing
        Reduce position size for high volatility stocks

        Lower volatility = larger position
        Higher volatility = smaller position
        """

        # Default to market average volatility if not provided
        vol = volatility if volatility is not None else 0.20  # 20%

        # Adjust risk % based on volatility
        # Base volatility = 0.20 (20%)
        # If stock vol = 0.40 (40%), reduce position by 50%
        # If stock vol = 0.10 (10%), increase position by 100%

        base_volatility = 0.20
        vol_adjustment = base_volatility / vol

        # Cap adjustment between 0.5x and 2x
        vol_adjustment = max(0.5, min(vol_adjustment, 2.0))

        adjusted_risk_pct = base_risk_pct * vol_adjustment

        # Cap at 3% max
        adjusted_risk_pct = min(adjusted_risk_pct, 3.0)

        result = self._fixed_fractional(
            account_value,
            entry_price,
            risk_per_share,
            adjusted_risk_pct
        )

        result['volatility_adjustment'] = round(vol_adjustment, 2)
        result['original_risk_pct'] = base_risk_pct
        result['adjusted_risk_pct'] = round(adjusted_risk_pct, 2)

        return result

    def calculate_multiple_scenarios(
        self,
        account_value: float,
        entry_price: float,
        stop_loss_price: float,
        target_price: Optional[float] = None,
        volatility: Optional[float] = None,
        win_rate: Optional[float] = None
    ) -> Dict[str, Any]:
        """
        Calculate position size using multiple methods for comparison

        Returns:
            {
                'conservative': Dict,  # 1% fixed fractional
                'moderate': Dict,      # 2% fixed fractional
                'aggressive': Dict,    # Kelly criterion
                'volatility_adjusted': Dict,
                'recommended': Dict    # Best choice based on risk profile
            }
        """

        # Calculate risk/reward ratio with safe extraction
        # Handle dict/float type mismatches
        entry = extract_numeric_value(entry_price, "entry_price", 0.0)
        stop = extract_numeric_value(stop_loss_price, "stop_loss", 0.0)
        target = extract_numeric_value(target_price, "target_price", 0.0) if target_price else 0.0

        # Use safe calculation if all values are valid
        if entry > 0 and stop > 0 and target > 0:
            risk_reward_ratio = calculate_risk_reward_ratio(entry, target, stop, "position_sizing")
            if risk_reward_ratio is None:
                risk_reward_ratio = 0.0
        else:
            # Fallback calculation
            risk_per_share = abs(entry - stop) if entry > 0 and stop > 0 else 0
            reward_per_share = abs(target - entry) if target > 0 and entry > 0 else risk_per_share * 2
            risk_reward_ratio = reward_per_share / risk_per_share if risk_per_share > 0 else 0

        # Conservative: 1% risk
        conservative = self.calculate_position_size(
            account_value,
            entry_price,
            stop_loss_price,
            risk_per_trade_pct=1.0,
            method=PositionSizeMethod.FIXED_FRACTIONAL
        )
        conservative['risk_reward_ratio'] = round(risk_reward_ratio, 2)

        # Moderate: 2% risk
        moderate = self.calculate_position_size(
            account_value,
            entry_price,
            stop_loss_price,
            risk_per_trade_pct=2.0,
            method=PositionSizeMethod.FIXED_FRACTIONAL
        )
        moderate['risk_reward_ratio'] = round(risk_reward_ratio, 2)

        # Aggressive: Kelly criterion
        aggressive = self.calculate_position_size(
            account_value,
            entry_price,
            stop_loss_price,
            method=PositionSizeMethod.KELLY_CRITERION,
            win_rate=win_rate,
            avg_win_loss_ratio=risk_reward_ratio if risk_reward_ratio > 0 else 2.0
        )
        aggressive['risk_reward_ratio'] = round(risk_reward_ratio, 2)

        # Volatility adjusted
        volatility_adjusted = self.calculate_position_size(
            account_value,
            entry_price,
            stop_loss_price,
            risk_per_trade_pct=1.5,
            method=PositionSizeMethod.VOLATILITY_ADJUSTED,
            volatility=volatility
        )
        volatility_adjusted['risk_reward_ratio'] = round(risk_reward_ratio, 2)

        # Recommended: Choose based on risk/reward
        if risk_reward_ratio >= 3.0:
            recommended = moderate  # Good R/R allows moderate sizing
        elif risk_reward_ratio >= 2.0:
            recommended = conservative  # Decent R/R, be conservative
        else:
            recommended = {**conservative, 'shares': int(conservative['shares'] * 0.5)}  # Poor R/R, very conservative

        return {
            'conservative': conservative,
            'moderate': moderate,
            'aggressive': aggressive,
            'volatility_adjusted': volatility_adjusted,
            'recommended': recommended,
            'risk_reward_ratio': round(risk_reward_ratio, 2)
        }

    def _error_result(self, error_msg: str) -> Dict[str, Any]:
        """Return error result"""
        return {
            'shares': 0,
            'position_value': 0,
            'capital_at_risk': 0,
            'position_pct': 0,
            'method': 'error',
            'error': error_msg
        }
