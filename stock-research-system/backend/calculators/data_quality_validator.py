"""
Data Quality Validation Framework
Timestamp freshness, source reliability, anomaly detection, and data completeness checks
"""

import numpy as np
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
from dataclasses import dataclass
import logging

logger = logging.getLogger(__name__)


@dataclass
class DataQualityReport:
    """Container for data quality metrics"""
    overall_score: float  # 0-100
    quality_grade: str  # A-F
    freshness_score: float
    reliability_score: float
    completeness_score: float
    anomaly_score: float
    issues: List[str]
    warnings: List[str]
    metadata: Dict[str, Any]


class DataQualityValidator:
    """
    Comprehensive data quality validation

    Features:
    - Timestamp freshness checking
    - Source reliability scoring
    - Anomaly detection (price, volume, metrics)
    - Data completeness validation
    - Cross-source verification
    """

    def __init__(self):
        self.name = "DataQualityValidator"

        # Source reliability scores (0-10)
        self.source_reliability = {
            'yfinance': 8.5,
            'alpha_vantage': 9.0,
            'finnhub': 8.0,
            'tavily': 7.5,
            'openai': 9.5,
            'internal_calculation': 9.0,
            'user_input': 5.0,
            'unknown': 3.0
        }

        # Freshness thresholds (in hours)
        self.freshness_thresholds = {
            'realtime': 0.25,  # 15 minutes
            'intraday': 1,  # 1 hour
            'daily': 24,  # 1 day
            'weekly': 168,  # 1 week
            'monthly': 720  # 30 days
        }

    def validate_data_quality(
        self,
        data: Dict[str, Any],
        data_type: str = 'general',
        expected_freshness: str = 'daily'
    ) -> DataQualityReport:
        """
        Comprehensive data quality validation

        Args:
            data: Data to validate
            data_type: Type of data (price, news, fundamental, etc.)
            expected_freshness: Expected freshness level

        Returns:
            DataQualityReport with scores and issues
        """
        logger.info(f"[{self.name}] Validating data quality for {data_type}")

        issues = []
        warnings = []

        # 1. Timestamp freshness check
        freshness_result = self._check_timestamp_freshness(
            data, expected_freshness
        )
        freshness_score = freshness_result['score']
        if freshness_result['issues']:
            issues.extend(freshness_result['issues'])
        if freshness_result['warnings']:
            warnings.extend(freshness_result['warnings'])

        # 2. Source reliability check
        reliability_result = self._check_source_reliability(data)
        reliability_score = reliability_result['score']
        if reliability_result['issues']:
            issues.extend(reliability_result['issues'])

        # 3. Data completeness check
        completeness_result = self._check_data_completeness(data, data_type)
        completeness_score = completeness_result['score']
        if completeness_result['issues']:
            issues.extend(completeness_result['issues'])

        # 4. Anomaly detection
        anomaly_result = self._detect_anomalies(data, data_type)
        anomaly_score = anomaly_result['score']
        if anomaly_result['issues']:
            issues.extend(anomaly_result['issues'])
        if anomaly_result['warnings']:
            warnings.extend(anomaly_result['warnings'])

        # Calculate overall score (weighted average)
        overall_score = (
            freshness_score * 0.3 +
            reliability_score * 0.25 +
            completeness_score * 0.25 +
            anomaly_score * 0.20
        )

        # Determine quality grade
        quality_grade = self._calculate_quality_grade(overall_score)

        logger.info(
            f"[{self.name}] Data quality: {quality_grade} "
            f"({overall_score:.1f}/100)"
        )

        return DataQualityReport(
            overall_score=overall_score,
            quality_grade=quality_grade,
            freshness_score=freshness_score,
            reliability_score=reliability_score,
            completeness_score=completeness_score,
            anomaly_score=anomaly_score,
            issues=issues,
            warnings=warnings,
            metadata={
                'data_type': data_type,
                'expected_freshness': expected_freshness,
                'validation_timestamp': datetime.utcnow().isoformat()
            }
        )

    def _check_timestamp_freshness(
        self,
        data: Dict[str, Any],
        expected_freshness: str
    ) -> Dict[str, Any]:
        """Check if data timestamps are fresh enough"""

        issues = []
        warnings = []
        score = 100

        # Extract timestamp (try multiple fields)
        timestamp = None
        for field in ['timestamp', 'date', 'updated_at', 'last_update', 'time']:
            if field in data:
                timestamp = data[field]
                break

        if not timestamp:
            issues.append("No timestamp found in data")
            score = 30
            return {'score': score, 'issues': issues, 'warnings': warnings}

        # Parse timestamp
        try:
            if isinstance(timestamp, str):
                # Try multiple formats
                for fmt in ['%Y-%m-%d %H:%M:%S', '%Y-%m-%dT%H:%M:%S', '%Y-%m-%d']:
                    try:
                        data_time = datetime.strptime(timestamp, fmt)
                        break
                    except ValueError:
                        continue
                else:
                    # If no format works, try ISO format
                    data_time = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
            elif isinstance(timestamp, datetime):
                data_time = timestamp
            else:
                issues.append(f"Invalid timestamp format: {type(timestamp)}")
                score = 40
                return {'score': score, 'issues': issues, 'warnings': warnings}

        except Exception as e:
            issues.append(f"Failed to parse timestamp: {e}")
            score = 40
            return {'score': score, 'issues': issues, 'warnings': warnings}

        # Calculate age
        now = datetime.utcnow()
        if data_time.tzinfo is None:
            # Make timezone-naive
            now = now.replace(tzinfo=None)

        age_hours = (now - data_time).total_seconds() / 3600

        # Check against threshold
        threshold_hours = self.freshness_thresholds.get(expected_freshness, 24)

        if age_hours > threshold_hours * 2:
            issues.append(
                f"Data is stale: {age_hours:.1f} hours old "
                f"(expected <{threshold_hours} hours)"
            )
            score = 20
        elif age_hours > threshold_hours:
            warnings.append(
                f"Data is older than expected: {age_hours:.1f} hours old "
                f"(expected <{threshold_hours} hours)"
            )
            score = 60
        else:
            # Score degrades linearly with age
            score = 100 - (age_hours / threshold_hours) * 20

        return {'score': max(score, 0), 'issues': issues, 'warnings': warnings}

    def _check_source_reliability(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Check reliability of data source"""

        issues = []
        score = 100

        # Extract source
        source = data.get('source', data.get('data_source', 'unknown')).lower()

        # Get reliability score
        reliability = self.source_reliability.get(source, 3.0)

        # Convert 0-10 scale to 0-100 scale
        score = reliability * 10

        if reliability < 5:
            issues.append(f"Low reliability source: {source} ({reliability}/10)")
        elif reliability < 7:
            issues.append(f"Medium reliability source: {source} ({reliability}/10)")

        return {'score': score, 'issues': issues}

    def _check_data_completeness(
        self,
        data: Dict[str, Any],
        data_type: str
    ) -> Dict[str, Any]:
        """Check if all expected fields are present"""

        issues = []
        score = 100

        # Define expected fields by data type
        expected_fields = {
            'price': ['symbol', 'price', 'volume', 'timestamp'],
            'fundamental': ['symbol', 'pe_ratio', 'market_cap', 'revenue'],
            'news': ['title', 'content', 'timestamp', 'source'],
            'technical': ['rsi', 'macd', 'trend', 'support_levels'],
            'general': []
        }

        fields = expected_fields.get(data_type, [])

        if fields:
            missing_fields = [f for f in fields if f not in data or data[f] is None]

            if missing_fields:
                issues.append(f"Missing fields: {', '.join(missing_fields)}")
                score = max(0, 100 - (len(missing_fields) / len(fields)) * 100)

        # Check for None values in present fields
        none_count = sum(1 for v in data.values() if v is None)
        if none_count > 0:
            total_fields = len(data)
            score = max(0, score - (none_count / total_fields) * 30)

        return {'score': score, 'issues': issues}

    def _detect_anomalies(
        self,
        data: Dict[str, Any],
        data_type: str
    ) -> Dict[str, Any]:
        """Detect anomalous values in data"""

        issues = []
        warnings = []
        score = 100

        # Price anomalies
        if 'price' in data or 'current_price' in data:
            price = data.get('price', data.get('current_price'))

            if price is not None:
                # Check for unrealistic prices
                if price <= 0:
                    issues.append(f"Invalid price: ${price}")
                    score -= 50
                elif price > 100000:
                    warnings.append(f"Unusually high price: ${price}")
                    score -= 10

        # P/E ratio anomalies
        if 'pe_ratio' in data:
            pe = data.get('pe_ratio')

            if pe is not None:
                if pe < 0:
                    issues.append(f"Negative P/E ratio: {pe}")
                    score -= 30
                elif pe > 500:
                    warnings.append(f"Extremely high P/E ratio: {pe}")
                    score -= 20

        # Market cap anomalies
        if 'market_cap' in data:
            mcap = data.get('market_cap')

            if mcap is not None:
                if mcap <= 0:
                    issues.append(f"Invalid market cap: ${mcap}")
                    score -= 40

        # Volume anomalies
        if 'volume' in data:
            volume = data.get('volume')

            if volume is not None:
                if volume < 0:
                    issues.append(f"Negative volume: {volume}")
                    score -= 30
                elif volume == 0:
                    warnings.append("Zero trading volume detected")
                    score -= 10

        # RSI anomalies
        if 'rsi' in data:
            rsi = data.get('rsi')

            if rsi is not None:
                if isinstance(rsi, dict):
                    rsi = rsi.get('value', rsi.get('rsi'))

                if rsi is not None:
                    if rsi < 0 or rsi > 100:
                        issues.append(f"RSI out of range: {rsi} (should be 0-100)")
                        score -= 40

        # Confidence anomalies
        if 'confidence' in data:
            conf = data.get('confidence')

            if conf is not None:
                if conf < 0 or conf > 1:
                    issues.append(f"Confidence out of range: {conf} (should be 0-1)")
                    score -= 30

        return {
            'score': max(score, 0),
            'issues': issues,
            'warnings': warnings
        }

    def _calculate_quality_grade(self, score: float) -> str:
        """Convert score to letter grade"""

        if score >= 90:
            return 'A'
        elif score >= 80:
            return 'B'
        elif score >= 70:
            return 'C'
        elif score >= 60:
            return 'D'
        else:
            return 'F'

    def validate_time_series(
        self,
        timestamps: List[datetime],
        values: List[float],
        expected_interval: str = 'daily'
    ) -> Dict[str, Any]:
        """
        Validate time series data for gaps, irregularities

        Args:
            timestamps: List of timestamps
            values: List of values
            expected_interval: Expected interval (daily, hourly, etc.)

        Returns:
            Validation report with gap detection
        """
        issues = []
        warnings = []

        if len(timestamps) != len(values):
            issues.append(
                f"Timestamp/value mismatch: {len(timestamps)} timestamps, "
                f"{len(values)} values"
            )

        if len(timestamps) < 2:
            return {
                'has_gaps': False,
                'gap_count': 0,
                'issues': issues,
                'warnings': warnings
            }

        # Calculate expected interval in seconds
        interval_map = {
            'minute': 60,
            'hourly': 3600,
            'daily': 86400,
            'weekly': 604800
        }
        expected_seconds = interval_map.get(expected_interval, 86400)

        # Check for gaps
        gaps = []
        for i in range(1, len(timestamps)):
            diff = (timestamps[i] - timestamps[i-1]).total_seconds()

            if diff > expected_seconds * 1.5:
                gaps.append({
                    'start': timestamps[i-1],
                    'end': timestamps[i],
                    'duration_hours': diff / 3600
                })

        if gaps:
            warnings.append(f"Found {len(gaps)} gaps in time series")

        # Check for duplicate timestamps
        unique_timestamps = len(set(timestamps))
        if unique_timestamps < len(timestamps):
            duplicates = len(timestamps) - unique_timestamps
            issues.append(f"Found {duplicates} duplicate timestamps")

        return {
            'has_gaps': len(gaps) > 0,
            'gap_count': len(gaps),
            'gaps': gaps[:5],  # First 5 gaps
            'duplicate_count': len(timestamps) - unique_timestamps,
            'issues': issues,
            'warnings': warnings
        }

    def cross_validate_sources(
        self,
        data_sources: List[Dict[str, Any]],
        field: str
    ) -> Dict[str, Any]:
        """
        Cross-validate data from multiple sources

        Args:
            data_sources: List of data from different sources
            field: Field to validate

        Returns:
            Validation report with consensus and outliers
        """
        if not data_sources or len(data_sources) < 2:
            return {
                'consensus_value': None,
                'variance': 0,
                'outliers': [],
                'agreement': 0
            }

        values = []
        for source in data_sources:
            if field in source and source[field] is not None:
                values.append({
                    'value': source[field],
                    'source': source.get('source', 'unknown')
                })

        if not values:
            return {
                'consensus_value': None,
                'variance': 0,
                'outliers': [],
                'agreement': 0
            }

        # Calculate consensus (median)
        numeric_values = [v['value'] for v in values]
        consensus = np.median(numeric_values)

        # Calculate variance
        variance = np.std(numeric_values) if len(numeric_values) > 1 else 0

        # Find outliers (> 2 std dev from median)
        outliers = []
        if variance > 0:
            for v in values:
                z_score = abs(v['value'] - consensus) / variance
                if z_score > 2:
                    outliers.append({
                        'source': v['source'],
                        'value': v['value'],
                        'deviation': (v['value'] - consensus) / consensus * 100
                    })

        # Calculate agreement (% within 5% of consensus)
        agreement_count = sum(
            1 for v in numeric_values
            if abs(v - consensus) / consensus < 0.05
        )
        agreement = agreement_count / len(numeric_values) * 100

        return {
            'consensus_value': float(consensus),
            'variance': float(variance),
            'outliers': outliers,
            'agreement': agreement,
            'sources_count': len(values)
        }

    def validate_price_data(
        self,
        price: float,
        symbol: str,
        price_type: str = 'current'
    ) -> Dict[str, Any]:
        """
        Validate stock price data for anomalies

        Args:
            price: Price value to validate
            symbol: Stock symbol for logging
            price_type: Type of price (current, target, stop_loss, etc.)

        Returns:
            Validation result with is_valid flag and reason
        """
        issues = []
        is_valid = True

        # Check for None or invalid types
        if price is None:
            return {
                'is_valid': True,  # None is acceptable (missing data)
                'validated_price': None,
                'issues': []
            }

        try:
            price = float(price)
        except (ValueError, TypeError):
            return {
                'is_valid': False,
                'validated_price': None,
                'issues': [f"Invalid price type for {symbol}: {type(price)}"]
            }

        # Range validation (0.01 to 100,000)
        if price < 0.01:
            issues.append(f"Price too low for {symbol} {price_type}: ${price:.2f} (min: $0.01)")
            is_valid = False
        elif price > 100000:
            issues.append(f"Anomalous price for {symbol} {price_type}: ${price:,.2f} (max: $100,000)")
            logger.warning(f"[DataQualityValidator] {issues[-1]}")
            is_valid = False

        # Additional validation for target prices (shouldn't be extreme outliers)
        if price_type == 'target' and is_valid:
            # Flag if target price is suspiciously high (likely data error)
            if price > 10000:
                issues.append(f"Suspicious target price for {symbol}: ${price:,.2f} (unusual for most stocks)")
                logger.warning(f"[DataQualityValidator] {issues[-1]}")

        return {
            'is_valid': is_valid,
            'validated_price': price if is_valid else None,
            'issues': issues
        }
