"""
Data Validation Service
Validates financial data for accuracy and completeness
"""

import logging
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime

logger = logging.getLogger(__name__)


class DataValidator:
    """Service for validating financial data quality"""

    # Validation ranges for different metrics
    VALIDATION_RULES = {
        'pe_ratio': {'min': -100, 'max': 1000, 'critical': True},
        'eps': {'min': -100, 'max': 1000, 'critical': True},
        'price': {'min': 0.01, 'max': 1000000, 'critical': True},
        'volume': {'min': 0, 'max': 10000000000, 'critical': False},
        'market_cap': {'min': 0, 'max': 10000000000000, 'critical': False},
        'beta': {'min': -5, 'max': 10, 'critical': False},
        'debt_to_equity': {'min': 0, 'max': 500, 'critical': False},
        'profit_margin': {'min': -1, 'max': 1, 'critical': False},
        'revenue_growth': {'min': -1, 'max': 10, 'critical': False},
    }

    @staticmethod
    def validate_quote_data(quote: Dict[str, Any]) -> Tuple[bool, List[str], int]:
        """
        Validate stock quote data

        Returns:
            (is_valid, warnings, quality_score)
        """
        warnings = []
        quality_score = 100
        is_valid = True

        # Check critical fields
        if not quote.get('price'):
            warnings.append('Missing or invalid price data')
            quality_score -= 50
            is_valid = False

        if not quote.get('volume') or quote['volume'] <= 0:
            warnings.append('Missing or invalid volume data')
            quality_score -= 10

        if not quote.get('market_cap') or quote['market_cap'] <= 0:
            warnings.append('Missing or invalid market cap')
            quality_score -= 15

        # Validate price range
        price = quote.get('price')
        if price:
            rule = DataValidator.VALIDATION_RULES['price']
            if not (rule['min'] <= price <= rule['max']):
                warnings.append(f'Price out of expected range: ${price}')
                quality_score -= 30
                is_valid = False

        # Validate volume
        volume = quote.get('volume', 0)
        if volume:
            rule = DataValidator.VALIDATION_RULES['volume']
            if not (rule['min'] <= volume <= rule['max']):
                warnings.append(f'Volume out of expected range: {volume:,}')
                quality_score -= 10

        # Check data freshness
        last_updated = quote.get('last_updated')
        if last_updated:
            try:
                updated_time = datetime.fromisoformat(last_updated.replace('Z', '+00:00'))
                age_minutes = (datetime.now(updated_time.tzinfo) - updated_time).total_seconds() / 60

                if age_minutes > 60:
                    warnings.append(f'Data is stale ({int(age_minutes)} minutes old)')
                    quality_score -= 20
            except Exception as e:
                logger.warning(f'Could not parse timestamp: {e}')

        return is_valid, warnings, max(0, quality_score)

    @staticmethod
    def validate_fundamental_data(fundamentals: Dict[str, Any]) -> Tuple[bool, List[str], int]:
        """
        Validate fundamental data

        Returns:
            (is_valid, warnings, quality_score)
        """
        warnings = []
        quality_score = 100
        is_valid = True

        # Validate P/E ratio
        pe_ratio = fundamentals.get('pe_ratio')
        if pe_ratio is not None:
            rule = DataValidator.VALIDATION_RULES['pe_ratio']
            if not (rule['min'] <= pe_ratio <= rule['max']):
                warnings.append(f'P/E ratio out of range: {pe_ratio} (expected {rule["min"]} to {rule["max"]})')
                quality_score -= 25
                if rule['critical']:
                    is_valid = False
        else:
            warnings.append('P/E ratio not available')
            quality_score -= 15

        # Validate EPS
        eps = fundamentals.get('eps')
        if eps is not None:
            rule = DataValidator.VALIDATION_RULES['eps']
            if not (rule['min'] <= eps <= rule['max']):
                warnings.append(f'EPS out of range: {eps}')
                quality_score -= 20
                if rule['critical']:
                    is_valid = False
        else:
            warnings.append('EPS not available')
            quality_score -= 15

        # Validate profit margin
        profit_margin = fundamentals.get('profit_margin')
        if profit_margin is not None:
            rule = DataValidator.VALIDATION_RULES['profit_margin']
            if not (rule['min'] <= profit_margin <= rule['max']):
                warnings.append(f'Profit margin out of range: {profit_margin*100:.2f}%')
                quality_score -= 10

        # Validate beta
        beta = fundamentals.get('beta')
        if beta is not None:
            rule = DataValidator.VALIDATION_RULES['beta']
            if not (rule['min'] <= beta <= rule['max']):
                warnings.append(f'Beta out of range: {beta}')
                quality_score -= 10

        # Check for missing critical metrics
        critical_metrics = ['revenue', 'profit_margin', 'roe']
        missing_critical = [m for m in critical_metrics if fundamentals.get(m) is None]

        if missing_critical:
            warnings.append(f'Missing critical metrics: {", ".join(missing_critical)}')
            quality_score -= len(missing_critical) * 10

        return is_valid, warnings, max(0, quality_score)

    @staticmethod
    def validate_recommendation(recommendation: Dict[str, Any]) -> Tuple[bool, List[str]]:
        """
        Validate trading recommendation logic

        Returns:
            (is_valid, warnings)
        """
        warnings = []
        is_valid = True

        action = recommendation.get('action', '').upper()
        entry_price = recommendation.get('entry_price')
        target_price = recommendation.get('target_price')
        stop_loss = recommendation.get('stop_loss')

        if not all([entry_price, target_price, stop_loss]):
            warnings.append('Missing price targets')
            return False, warnings

        # Validate BUY recommendation
        if action == 'BUY':
            if target_price <= entry_price:
                warnings.append(f'BUY recommendation has target (${target_price}) <= entry (${entry_price}) - should be higher for profit')
                is_valid = False

            if stop_loss >= entry_price:
                warnings.append(f'BUY recommendation has stop loss (${stop_loss}) >= entry (${entry_price}) - should be lower')
                is_valid = False

        # Validate SELL recommendation
        elif action == 'SELL':
            if target_price >= entry_price:
                warnings.append(f'SELL recommendation has target (${target_price}) >= entry (${entry_price}) - should be lower for short profit')
                is_valid = False

            if stop_loss <= entry_price:
                warnings.append(f'SELL recommendation has stop loss (${stop_loss}) <= entry (${entry_price}) - should be higher for short')
                is_valid = False

        # Validate HOLD recommendation
        elif action == 'HOLD':
            # For HOLD, target should be within ±5% of entry
            target_diff_pct = abs((target_price - entry_price) / entry_price) * 100

            if target_diff_pct > 5:
                warnings.append(f'HOLD recommendation has target {target_diff_pct:.1f}% away from entry - should be within ±5%')
                is_valid = False

        # Validate confidence score
        confidence = recommendation.get('confidence')
        if confidence is not None:
            if not (0 <= confidence <= 100):
                warnings.append(f'Confidence score out of range: {confidence}% (should be 0-100%)')
                is_valid = False

        return is_valid, warnings

    @staticmethod
    def calculate_overall_quality(quote_quality: int, fundamental_quality: int, sentiment_quality: int = 50) -> Tuple[int, str]:
        """
        Calculate overall data quality score

        Returns:
            (score, grade)
        """
        # Weighted average (quote: 40%, fundamentals: 40%, sentiment: 20%)
        overall = (quote_quality * 0.4) + (fundamental_quality * 0.4) + (sentiment_quality * 0.2)

        score = int(overall)

        if score >= 90:
            grade = 'A'
        elif score >= 80:
            grade = 'B'
        elif score >= 70:
            grade = 'C'
        elif score >= 60:
            grade = 'D'
        else:
            grade = 'F'

        return score, grade

    @staticmethod
    def get_data_freshness_indicator(last_updated: str) -> Dict[str, Any]:
        """
        Get data freshness indicator

        Returns:
            {
                'status': 'real-time' | 'recent' | 'stale',
                'color': 'green' | 'yellow' | 'red',
                'age_minutes': 5
            }
        """
        try:
            updated_time = datetime.fromisoformat(last_updated.replace('Z', '+00:00'))
            age_minutes = (datetime.now(updated_time.tzinfo) - updated_time).total_seconds() / 60

            if age_minutes < 5:
                return {'status': 'real-time', 'color': 'green', 'age_minutes': int(age_minutes)}
            elif age_minutes < 60:
                return {'status': 'recent', 'color': 'yellow', 'age_minutes': int(age_minutes)}
            else:
                return {'status': 'stale', 'color': 'red', 'age_minutes': int(age_minutes)}

        except Exception as e:
            logger.warning(f'Could not parse timestamp: {e}')
            return {'status': 'unknown', 'color': 'gray', 'age_minutes': None}


# Global instance
data_validator = DataValidator()
