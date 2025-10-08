"""
Lineage Integration Helpers
Provides easy-to-use wrappers for adding lineage tracking to existing services
"""

import logging
from typing import Dict, Any, Optional, Callable
from datetime import datetime, timedelta
from functools import wraps

from services.data_lineage_tracker import (
    DataLineageTracker,
    DataSource,
    DataReliability,
    DataFreshness
)

logger = logging.getLogger(__name__)


class LineageIntegration:
    """Helper class for integrating lineage tracking into existing services"""

    @staticmethod
    def add_yfinance_lineage(
        tracker: DataLineageTracker,
        data: Dict[str, Any],
        symbol: str,
        prefix: str = ""
    ) -> Dict[str, Any]:
        """
        Add lineage tracking to yfinance data

        Args:
            tracker: DataLineageTracker instance
            data: Data dictionary from yfinance
            symbol: Stock symbol
            prefix: Prefix for field names

        Returns:
            Original data with lineage metadata added
        """
        for key, value in data.items():
            if value is None:
                continue

            field_name = f"{prefix}{key}" if prefix else key

            # Determine confidence based on field type
            confidence = 0.95  # yfinance is highly reliable

            tracker.track(
                field_name=field_name,
                value=value,
                source=DataSource.YFINANCE,
                reliability=DataReliability.HIGH,
                confidence=confidence,
                data_timestamp=datetime.utcnow(),  # yfinance provides current data
                api_endpoint=f"yfinance.Ticker('{symbol}').info",
                citation=f"Yahoo Finance API for {symbol}"
            )

        return data

    @staticmethod
    def add_alpha_vantage_lineage(
        tracker: DataLineageTracker,
        data: Dict[str, Any],
        symbol: str,
        api_function: str,
        prefix: str = ""
    ) -> Dict[str, Any]:
        """
        Add lineage tracking to Alpha Vantage data

        Args:
            tracker: DataLineageTracker instance
            data: Data dictionary from Alpha Vantage
            symbol: Stock symbol
            api_function: Alpha Vantage function used
            prefix: Prefix for field names

        Returns:
            Original data with lineage metadata added
        """
        for key, value in data.items():
            if value is None:
                continue

            field_name = f"{prefix}{key}" if prefix else key

            tracker.track(
                field_name=field_name,
                value=value,
                source=DataSource.ALPHA_VANTAGE,
                reliability=DataReliability.HIGH,
                confidence=0.90,
                data_timestamp=datetime.utcnow(),
                api_endpoint=f"alphavantage.{api_function}",
                citation=f"Alpha Vantage {api_function} for {symbol}"
            )

        return data

    @staticmethod
    def add_tavily_lineage(
        tracker: DataLineageTracker,
        data: Dict[str, Any],
        query: str,
        api_type: str,  # "search", "qna", "extract", "context"
        prefix: str = "",
        source_url: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Add lineage tracking to Tavily API data

        Args:
            tracker: DataLineageTracker instance
            data: Data from Tavily
            query: Query used
            api_type: Type of Tavily API
            prefix: Prefix for field names
            source_url: URL of source if available

        Returns:
            Original data with lineage metadata added
        """
        source_map = {
            "search": DataSource.TAVILY_SEARCH,
            "qna": DataSource.TAVILY_QNA,
            "extract": DataSource.TAVILY_EXTRACT,
            "context": DataSource.TAVILY_CONTEXT
        }

        source = source_map.get(api_type, DataSource.TAVILY_SEARCH)

        # Reliability varies by API type
        reliability = DataReliability.MEDIUM if api_type in ["search", "extract"] else DataReliability.LOW

        for key, value in data.items():
            if value is None:
                continue

            field_name = f"{prefix}{key}" if prefix else key

            tracker.track(
                field_name=field_name,
                value=value,
                source=source,
                reliability=reliability,
                confidence=0.70,
                data_timestamp=datetime.utcnow(),
                api_endpoint=f"tavily.{api_type}",
                source_url=source_url,
                citation=f"Tavily {api_type.upper()} API: {query[:50]}"
            )

        return data

    @staticmethod
    def add_calculated_lineage(
        tracker: DataLineageTracker,
        field_name: str,
        value: Any,
        formula: str,
        input_fields: Dict[str, Any]
    ) -> Any:
        """
        Add lineage for calculated fields

        Args:
            tracker: DataLineageTracker instance
            field_name: Name of calculated field
            value: Calculated value
            formula: Formula description
            input_fields: Dictionary of input field names and values

        Returns:
            Original value
        """
        # Calculate confidence based on input data quality
        input_confidences = []
        for input_field in input_fields.keys():
            lineage = tracker.get_lineage(input_field)
            if lineage:
                input_confidences.append(lineage.metadata.confidence)

        avg_confidence = sum(input_confidences) / len(input_confidences) if input_confidences else 0.8

        tracker.track_calculated(
            field_name=field_name,
            value=value,
            formula=formula,
            upstream_fields=list(input_fields.keys()),
            confidence=avg_confidence
        )

        return value

    @staticmethod
    def track_cache_hit(
        tracker: DataLineageTracker,
        field_name: str,
        value: Any,
        original_source: DataSource,
        cache_age: float,  # seconds
        reliability: DataReliability = DataReliability.HIGH
    ):
        """
        Track a cache hit

        Args:
            tracker: DataLineageTracker instance
            field_name: Field name
            value: Cached value
            original_source: Original data source
            cache_age: Age of cached data in seconds
            reliability: Reliability of cached data
        """
        cache_timestamp = datetime.utcnow() - timedelta(seconds=cache_age)

        tracker.track(
            field_name=field_name,
            value=value,
            source=original_source,
            reliability=reliability,
            confidence=0.95,  # Cached data maintains confidence
            data_timestamp=cache_timestamp,
            cache_hit=True,
            citation=f"Cached from {original_source.value} ({cache_age:.0f}s old)"
        )

    @staticmethod
    def create_lineage_summary_dict(tracker: DataLineageTracker) -> Dict[str, Any]:
        """
        Create a frontend-friendly summary of lineage

        Args:
            tracker: DataLineageTracker instance

        Returns:
            Dictionary suitable for JSON serialization
        """
        summary = tracker.generate_summary()

        return {
            'data_quality': {
                'overall_score': summary.data_quality_score,
                'total_fields': summary.total_fields,
                'average_confidence': summary.average_confidence,
                'cache_hit_rate': summary.cache_hit_rate
            },
            'sources': {
                'breakdown': summary.source_breakdown,
                'primary_source': max(summary.source_breakdown.items(), key=lambda x: x[1])[0] if summary.source_breakdown else 'unknown'
            },
            'freshness': {
                'breakdown': summary.freshness_breakdown,
                'oldest_age_seconds': summary.oldest_data_age.total_seconds() if summary.oldest_data_age else None,
                'newest_age_seconds': summary.newest_data_age.total_seconds() if summary.newest_data_age else None
            },
            'reliability': {
                'breakdown': summary.reliability_breakdown,
                'high_reliability_pct': (summary.reliability_breakdown.get('high', 0) / summary.total_fields * 100) if summary.total_fields > 0 else 0
            },
            'citations': tracker.get_citations()
        }


def with_lineage_tracking(source: DataSource, reliability: DataReliability):
    """
    Decorator to automatically track lineage for function returns

    Usage:
        @with_lineage_tracking(DataSource.YFINANCE, DataReliability.HIGH)
        async def fetch_price(symbol: str) -> Dict[str, Any]:
            return {"price": 150.0}
    """
    def decorator(func: Callable):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # Execute function
            result = await func(*args, **kwargs)

            # Extract tracker from context if available
            tracker = kwargs.get('lineage_tracker')
            if tracker and isinstance(result, dict):
                for key, value in result.items():
                    if value is not None:
                        tracker.track(
                            field_name=key,
                            value=value,
                            source=source,
                            reliability=reliability,
                            confidence=0.9,
                            data_timestamp=datetime.utcnow()
                        )

            return result

        return wrapper
    return decorator


# Example usage helper
class LineageExample:
    """Example of how to use lineage tracking in an agent"""

    @staticmethod
    async def example_market_data_with_lineage(symbol: str) -> Dict[str, Any]:
        """
        Example: Fetch market data with complete lineage tracking

        Args:
            symbol: Stock symbol

        Returns:
            Market data with lineage
        """
        # Initialize tracker
        tracker = DataLineageTracker()

        # Fetch from yfinance
        import yfinance as yf
        ticker = yf.Ticker(symbol)
        info = ticker.info

        price = info.get('currentPrice', 0)
        volume = info.get('volume', 0)
        market_cap = info.get('marketCap', 0)

        # Track each field
        tracker.track(
            field_name='price',
            value=price,
            source=DataSource.YFINANCE,
            reliability=DataReliability.HIGH,
            confidence=0.95,
            data_timestamp=datetime.utcnow(),
            api_endpoint="yfinance.Ticker.info",
            citation=f"Yahoo Finance API for {symbol}"
        )

        tracker.track(
            field_name='volume',
            value=volume,
            source=DataSource.YFINANCE,
            reliability=DataReliability.HIGH,
            confidence=0.95,
            data_timestamp=datetime.utcnow(),
            api_endpoint="yfinance.Ticker.info",
            citation=f"Yahoo Finance API for {symbol}"
        )

        # Calculate derived metric
        if price > 0 and market_cap > 0:
            shares_outstanding = market_cap / price

            tracker.track_calculated(
                field_name='shares_outstanding',
                value=shares_outstanding,
                formula='market_cap / price',
                upstream_fields=['market_cap', 'price'],
                confidence=0.90
            )

        # Generate summary
        lineage_summary = LineageIntegration.create_lineage_summary_dict(tracker)

        return {
            'symbol': symbol,
            'price': price,
            'volume': volume,
            'market_cap': market_cap,
            'lineage': lineage_summary,
            'raw_lineage': tracker.export_lineage_report()
        }
