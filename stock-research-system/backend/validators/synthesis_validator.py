"""
Synthesis Validator - Guardrails & Sanity Checks
Validates synthesis outputs to prevent impossible metrics and recommendations
"""

import logging
from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass
from utils.value_extractors import extract_numeric_value, extract_price_value

logger = logging.getLogger(__name__)


@dataclass
class ValidationResult:
    """Result of validation checks"""
    is_valid: bool
    errors: List[str]
    warnings: List[str]
    corrected_values: Dict[str, Any]


class SynthesisValidator:
    """
    Validates synthesis agent outputs for data integrity

    Checks:
    - Metric validity (P/E, margins, Sharpe, etc.)
    - Logical consistency (recommendation vs metrics)
    - Risk/Reward requirements
    - Price target sanity
    """

    def __init__(self):
        self.name = "SynthesisValidator"

    def validate(self, synthesis: Dict[str, Any], current_price: float) -> ValidationResult:
        """
        Main validation entry point

        Args:
            synthesis: Synthesis agent output
            current_price: Current stock price

        Returns:
            ValidationResult with errors, warnings, and corrections
        """
        errors = []
        warnings = []
        corrected = {}

        # 1. Validate recommendation
        rec_errors, rec_warnings, rec_corrected = self._validate_recommendation(synthesis, current_price)
        errors.extend(rec_errors)
        warnings.extend(rec_warnings)
        corrected.update(rec_corrected)

        # 2. Validate fundamental metrics
        fund_errors, fund_warnings = self._validate_fundamentals(synthesis)
        errors.extend(fund_errors)
        warnings.extend(fund_warnings)

        # 3. Validate risk metrics
        risk_errors, risk_warnings = self._validate_risk_metrics(synthesis)
        errors.extend(risk_errors)
        warnings.extend(risk_warnings)

        # 4. Validate price targets
        price_errors, price_warnings, price_corrected = self._validate_price_targets(
            synthesis, current_price
        )
        errors.extend(price_errors)
        warnings.extend(price_warnings)
        corrected.update(price_corrected)

        # 5. Validate risk/reward ratio
        rr_errors, rr_warnings = self._validate_risk_reward(synthesis)
        errors.extend(rr_errors)
        warnings.extend(rr_warnings)

        is_valid = len(errors) == 0

        return ValidationResult(
            is_valid=is_valid,
            errors=errors,
            warnings=warnings,
            corrected_values=corrected
        )

    def _validate_recommendation(
        self, synthesis: Dict, current_price: float
    ) -> Tuple[List[str], List[str], Dict]:
        """Validate recommendation consistency"""
        errors = []
        warnings = []
        corrected = {}

        action = synthesis.get('action', '').upper()
        confidence = synthesis.get('confidence', 0)
        target_price = synthesis.get('target_price')

        # Check action is valid
        valid_actions = ['STRONG_BUY', 'BUY', 'HOLD', 'SELL', 'STRONG_SELL']
        if action not in valid_actions:
            errors.append(f"Invalid action '{action}', must be one of {valid_actions}")

        # Check confidence range
        if not (0 <= confidence <= 1):
            errors.append(f"Confidence {confidence} must be between 0 and 1")
            corrected['confidence'] = max(0, min(1, confidence))

        # BUY/SELL direction must match target price
        if action in ['BUY', 'STRONG_BUY'] and target_price:
            if target_price < current_price:
                errors.append(
                    f"{action} recommendation but target ${target_price:.2f} < current ${current_price:.2f}"
                )

        if action in ['SELL', 'STRONG_SELL'] and target_price:
            if target_price > current_price:
                errors.append(
                    f"{action} recommendation but target ${target_price:.2f} > current ${current_price:.2f}"
                )

        # High confidence BUY requires positive risk/reward
        if action in ['BUY', 'STRONG_BUY'] and confidence > 0.7:
            rr_ratio = synthesis.get('risk_reward_ratio', 0)
            if rr_ratio and rr_ratio < 2.0:
                warnings.append(
                    f"High confidence {action} (conf: {confidence:.0%}) but low R/R: {rr_ratio:.2f} < 2.0"
                )

        return errors, warnings, corrected

    def _validate_fundamentals(self, synthesis: Dict) -> Tuple[List[str], List[str]]:
        """Validate fundamental metrics"""
        errors = []
        warnings = []

        pe_ratio = synthesis.get('pe_ratio')
        if pe_ratio is not None:
            if pe_ratio < 0:
                errors.append(f"P/E ratio {pe_ratio} cannot be negative")
            elif pe_ratio > 1000:
                warnings.append(f"P/E ratio {pe_ratio} is extremely high (> 1000)")

        # ROE validation
        roe = synthesis.get('roe')
        if roe is not None:
            if roe < -100:
                errors.append(f"ROE {roe}% < -100% is impossible")
            elif roe > 200:
                warnings.append(f"ROE {roe}% > 200% is extremely high")

        # Margin of safety
        mos = synthesis.get('margin_of_safety')
        if mos is not None:
            if mos > 100:
                errors.append(f"Margin of safety {mos}% > 100% is impossible (would be free)")
            elif mos < -100:
                errors.append(f"Margin of safety {mos}% < -100% is impossible")

        # Profit margin
        margin = synthesis.get('profit_margin')
        if margin is not None:
            if margin < -100:
                errors.append(f"Profit margin {margin}% < -100% is impossible")
            elif margin > 100:
                errors.append(f"Profit margin {margin}% > 100% is impossible")

        return errors, warnings

    def _validate_risk_metrics(self, synthesis: Dict) -> Tuple[List[str], List[str]]:
        """Validate risk metrics"""
        errors = []
        warnings = []

        sharpe = synthesis.get('sharpe_ratio')
        if sharpe is not None:
            if sharpe > 10:
                errors.append(f"Sharpe ratio {sharpe:.2f} > 10 is impossible in real markets")
            elif sharpe > 5:
                warnings.append(f"Sharpe ratio {sharpe:.2f} > 5 is extremely rare")

        sortino = synthesis.get('sortino_ratio')
        if sortino is not None and sharpe is not None:
            # Sortino should be similar to or higher than Sharpe
            if sortino < sharpe * 0.3 and sharpe > 1:
                warnings.append(
                    f"Sortino {sortino:.2f} << Sharpe {sharpe:.2f} (unusual, check calculation)"
                )

        max_dd = synthesis.get('max_drawdown')
        if max_dd is not None:
            if max_dd > 100:
                errors.append(f"Max drawdown {max_dd}% > 100% is impossible")
            elif max_dd < 0:
                errors.append(f"Max drawdown {max_dd}% cannot be negative")
            elif max_dd == 0 and synthesis.get('backtest_periods', 0) > 10:
                warnings.append("Max drawdown = 0% over 10+ periods is highly unusual")

        return errors, warnings

    def _validate_price_targets(
        self, synthesis: Dict, current_price: float
    ) -> Tuple[List[str], List[str], Dict]:
        """Validate price targets and stops"""
        errors = []
        warnings = []
        corrected = {}

        target_data = synthesis.get('target_price')
        stop_data = synthesis.get('stop_loss')

        # Extract numeric values safely
        target = extract_price_value(target_data, 'target_price')
        stop = extract_price_value(stop_data, 'stop_loss')

        if target is not None:
            # Target should be within ±100% of current (sanity check)
            if target > current_price * 3:
                warnings.append(
                    f"Target ${target:.2f} is 3x current price ${current_price:.2f} (aggressive)"
                )
            elif target < current_price * 0.5:
                warnings.append(
                    f"Target ${target:.2f} is 50% below current ${current_price:.2f} (aggressive)"
                )

        if stop is not None:
            # Stop must be a price, not a percentage or dollar amount
            if stop < 1:
                errors.append(f"Stop loss ${stop:.2f} < $1, likely a percentage not price")
                # Attempt to correct: assume it's a percentage
                corrected['stop_loss'] = current_price * (1 - stop)

            # Stop should be below current price for longs
            action = synthesis.get('action', '').upper()
            if action in ['BUY', 'STRONG_BUY', 'HOLD']:
                if stop > current_price:
                    errors.append(
                        f"Stop ${stop:.2f} > current ${current_price:.2f} for {action} (should be below)"
                    )

        return errors, warnings, corrected

    def _validate_risk_reward(self, synthesis: Dict) -> Tuple[List[str], List[str]]:
        """Validate risk/reward ratio"""
        errors = []
        warnings = []

        rr_ratio = synthesis.get('risk_reward_ratio')
        action = synthesis.get('action', '').upper()

        if rr_ratio is not None:
            if rr_ratio <= 0:
                errors.append(f"Risk/Reward ratio {rr_ratio:.2f} must be > 0")

            # BUY recommendations should have R/R >= 2.0
            if action in ['BUY', 'STRONG_BUY']:
                if rr_ratio < 2.0:
                    warnings.append(
                        f"{action} with R/R {rr_ratio:.2f} < 2.0 (should be >= 2.0 for BUY)"
                    )

            # Extremely high R/R is suspicious
            if rr_ratio > 10:
                warnings.append(f"Risk/Reward {rr_ratio:.2f} > 10 is very optimistic")

        return errors, warnings

    def apply_corrections(
        self, synthesis: Dict, validation: ValidationResult
    ) -> Dict[str, Any]:
        """Apply corrected values to synthesis output"""
        corrected_synthesis = synthesis.copy()

        for key, value in validation.corrected_values.items():
            logger.info(
                f"[{self.name}] Correcting {key}: {synthesis.get(key)} -> {value}"
            )
            corrected_synthesis[key] = value

        # Add validation metadata
        corrected_synthesis['validation'] = {
            'is_valid': validation.is_valid,
            'errors': validation.errors,
            'warnings': validation.warnings,
            'corrections_applied': len(validation.corrected_values)
        }

        return corrected_synthesis
