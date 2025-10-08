"""
Enhanced Tavily Service with Lineage Tracking
Extends tavily_service.py with comprehensive data lineage tracking
"""

import logging
from typing import Dict, Any, List, Optional
from datetime import datetime

from services.tavily_service import TavilyMarketService
from services.data_lineage_tracker import (
    DataLineageTracker,
    DataSource,
    DataReliability
)
from services.lineage_integration import LineageIntegration

logger = logging.getLogger(__name__)


class EnhancedTavilyService(TavilyMarketService):
    """
    Tavily Market Service with built-in lineage tracking
    Drop-in replacement for TavilyMarketService
    """

    def __init__(self, api_key: str, cache_ttl: int = 60):
        super().__init__(api_key, cache_ttl)
        self.lineage_tracker = DataLineageTracker()

    async def get_stock_price_with_lineage(self, symbol: str) -> Dict[str, Any]:
        """
        Get stock price with complete lineage tracking

        Returns stock data with lineage metadata showing:
        - Primary source (yfinance vs tavily)
        - Data freshness
        - Reliability score
        - Cache status
        """
        # Reset tracker
        self.lineage_tracker = DataLineageTracker()

        # Check if from cache first
        cache_key = f"price:{symbol}"
        cached_data = self._get_from_cache(cache_key)
        is_cached = cached_data is not None

        # Fetch data
        stock_data = await self.get_stock_price(symbol)

        # Determine source
        source_map = {
            'yahoo_finance': DataSource.YFINANCE,
            'tavily_search': DataSource.TAVILY_SEARCH,
            'tavily_qa': DataSource.TAVILY_QNA,
            'unavailable': DataSource.FALLBACK
        }

        source = source_map.get(stock_data.get('source', 'unavailable'), DataSource.FALLBACK)

        # Determine reliability
        reliability_map = {
            'real-time': DataReliability.HIGH,
            'estimated': DataReliability.LOW,
            'unavailable': DataReliability.FALLBACK
        }

        reliability = reliability_map.get(stock_data.get('data_quality', 'unavailable'), DataReliability.HIGH)

        # Track all fields
        for key, value in stock_data.items():
            if value is None or key in ['source', 'data_quality', 'timestamp', 'error']:
                continue

            self.lineage_tracker.track(
                field_name=key,
                value=value,
                source=source,
                reliability=reliability,
                confidence=0.95 if source == DataSource.YFINANCE else 0.70,
                data_timestamp=datetime.fromisoformat(stock_data['timestamp'].replace('Z', '+00:00')),
                cache_hit=is_cached,
                api_endpoint=f"yfinance.Ticker({symbol})" if source == DataSource.YFINANCE else "tavily.search",
                citation=f"{'Yahoo Finance' if source == DataSource.YFINANCE else 'Tavily Search'} for {symbol}"
            )

        # Add lineage summary
        stock_data['lineage'] = LineageIntegration.create_lineage_summary_dict(self.lineage_tracker)

        return stock_data

    async def get_market_news_with_lineage(
        self,
        symbols: List[str],
        limit: int = 10
    ) -> Dict[str, Any]:
        """
        Get market news with lineage tracking

        Returns:
            {
                'news': [...],
                'lineage': {...}
            }
        """
        self.lineage_tracker = DataLineageTracker()

        # Fetch news
        news_items = await self.get_market_news(symbols, limit)

        # Track each news item
        for idx, news_item in enumerate(news_items):
            for key, value in news_item.items():
                if value is None:
                    continue

                self.lineage_tracker.track(
                    field_name=f"news_{idx}_{key}",
                    value=value,
                    source=DataSource.TAVILY_SEARCH,
                    reliability=DataReliability.MEDIUM,
                    confidence=news_item.get('relevance_score', 0.7),
                    data_timestamp=datetime.fromisoformat(
                        news_item.get('published', datetime.utcnow().isoformat()).replace('Z', '+00:00')
                    ) if 'published' in news_item else datetime.utcnow(),
                    source_url=news_item.get('url'),
                    citation=f"{news_item.get('source', 'Unknown')} - {news_item.get('title', '')[:50]}"
                )

        return {
            'news': news_items,
            'count': len(news_items),
            'symbols': symbols,
            'lineage': LineageIntegration.create_lineage_summary_dict(self.lineage_tracker),
            'timestamp': datetime.utcnow().isoformat()
        }

    async def get_market_sentiment_with_lineage(self, symbol: str) -> Dict[str, Any]:
        """
        Get market sentiment with lineage tracking

        Returns sentiment data with complete source attribution
        """
        self.lineage_tracker = DataLineageTracker()

        # Fetch sentiment
        sentiment_data = await self.get_market_sentiment(symbol)

        # Track sentiment fields
        for key, value in sentiment_data.items():
            if value is None or key in ['data_quality', 'error']:
                continue

            self.lineage_tracker.track(
                field_name=key,
                value=value,
                source=DataSource.TAVILY_SEARCH,
                reliability=DataReliability.MEDIUM,
                confidence=0.60,  # Sentiment analysis is inherently uncertain
                data_timestamp=datetime.utcnow(),
                api_endpoint="tavily.search",
                citation=f"Tavily sentiment analysis for {symbol}"
            )

        # Add lineage summary
        sentiment_data['lineage'] = LineageIntegration.create_lineage_summary_dict(self.lineage_tracker)

        return sentiment_data

    def get_lineage_tracker(self) -> DataLineageTracker:
        """Get the current lineage tracker"""
        return self.lineage_tracker
