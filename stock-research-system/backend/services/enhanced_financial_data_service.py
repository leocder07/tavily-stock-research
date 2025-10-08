"""
Enhanced Financial Data Service with Lineage Tracking
Extends the existing financial_data_service.py with comprehensive data lineage
"""

import logging
from typing import Dict, Any, Optional
from datetime import datetime

from services.financial_data_service import FinancialDataService
from services.data_lineage_tracker import (
    DataLineageTracker,
    DataSource,
    DataReliability
)
from services.lineage_integration import LineageIntegration

logger = logging.getLogger(__name__)


class EnhancedFinancialDataService(FinancialDataService):
    """
    Financial Data Service with built-in lineage tracking
    Drop-in replacement for FinancialDataService
    """

    def __init__(self):
        super().__init__()
        self.lineage_tracker = DataLineageTracker()

    async def get_stock_quote_with_lineage(self, symbol: str) -> Dict[str, Any]:
        """
        Get stock quote with complete lineage tracking

        Returns:
            {
                'symbol': 'TSLA',
                'price': 444.72,
                'change': 1.51,
                ...
                'lineage': {
                    'data_quality': {...},
                    'sources': {...},
                    'freshness': {...}
                }
            }
        """
        # Reset tracker for this request
        self.lineage_tracker = DataLineageTracker()

        # Fetch data using parent method
        quote = await self.get_stock_quote(symbol)

        # Add lineage tracking to all fields
        for key, value in quote.items():
            if value is None or key in ['data_quality', 'last_updated']:
                continue

            # Determine source and reliability
            source = DataSource.YFINANCE
            reliability = DataReliability.HIGH

            # Check if this was from fallback
            if quote.get('error'):
                source = DataSource.FALLBACK
                reliability = DataReliability.FALLBACK

            self.lineage_tracker.track(
                field_name=key,
                value=value,
                source=source,
                reliability=reliability,
                confidence=0.95 if not quote.get('error') else 0.3,
                data_timestamp=datetime.utcnow(),
                api_endpoint="yfinance.Ticker.info",
                citation=f"Yahoo Finance quote for {symbol}"
            )

        # Add lineage summary to result
        quote['lineage'] = LineageIntegration.create_lineage_summary_dict(self.lineage_tracker)

        return quote

    async def get_fundamental_data_with_lineage(self, symbol: str) -> Dict[str, Any]:
        """
        Get fundamental data with complete lineage tracking

        Returns:
            Fundamental data dict with lineage metadata
        """
        # Reset tracker
        self.lineage_tracker = DataLineageTracker()

        # Fetch fundamentals
        fundamentals = await self.get_fundamental_data(symbol)

        # Track yfinance fields
        yfinance_fields = [
            'pe_ratio', 'eps', 'forward_pe', 'peg_ratio', 'price_to_book',
            'price_to_sales', 'revenue', 'revenue_growth', 'profit_margin',
            'operating_margin', 'gross_margin', 'roe', 'roa', 'debt_to_equity',
            'current_ratio', 'quick_ratio', 'free_cash_flow', 'earnings_date',
            'dividend_yield', 'beta'
        ]

        for field in yfinance_fields:
            value = fundamentals.get(field)
            if value is not None:
                self.lineage_tracker.track(
                    field_name=field,
                    value=value,
                    source=DataSource.YFINANCE,
                    reliability=DataReliability.HIGH,
                    confidence=0.90,
                    data_timestamp=datetime.utcnow(),
                    api_endpoint="yfinance.Ticker.info",
                    citation=f"Yahoo Finance fundamentals for {symbol}"
                )

        # Track Alpha Vantage enrichment if present
        if 'alpha_vantage_enrichment' in fundamentals:
            av_data = fundamentals['alpha_vantage_enrichment']
            for key, value in av_data.items():
                if value is not None:
                    self.lineage_tracker.track(
                        field_name=f"av_{key}",
                        value=value,
                        source=DataSource.ALPHA_VANTAGE,
                        reliability=DataReliability.HIGH,
                        confidence=0.85,
                        data_timestamp=datetime.utcnow(),
                        api_endpoint="alphavantage.OVERVIEW",
                        citation=f"Alpha Vantage company overview for {symbol}"
                    )

        # Add lineage summary
        fundamentals['lineage'] = LineageIntegration.create_lineage_summary_dict(self.lineage_tracker)

        return fundamentals

    def get_lineage_tracker(self) -> DataLineageTracker:
        """Get the current lineage tracker"""
        return self.lineage_tracker


# Global instance with lineage tracking
enhanced_financial_data_service = EnhancedFinancialDataService()
