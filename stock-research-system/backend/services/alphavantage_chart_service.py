"""
AlphaVantage Chart Data Service
Provides historical OHLCV data and technical indicators for chart visualization
Uses MCP AlphaVantage tools for data retrieval
"""

import logging
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
import asyncio

logger = logging.getLogger(__name__)


class AlphaVantageChartService:
    """
    Service for fetching chart data from AlphaVantage API
    Supports multiple timeframes and technical indicators
    """

    def __init__(self):
        self.name = "AlphaVantageChartService"
        # AlphaVantage API key from environment
        self.api_key = "05MCZYK21W0DNY16"

        # Timeframe mapping
        self.timeframe_map = {
            '1min': '1min',
            '5min': '5min',
            '15min': '15min',
            '30min': '30min',
            '1h': '60min',
            '1D': 'daily',
            '1W': 'weekly',
            '1M': 'monthly'
        }

    async def get_historical_data(
        self,
        symbol: str,
        timeframe: str = '1D',
        outputsize: str = 'compact'
    ) -> Dict[str, Any]:
        """
        Fetch historical OHLCV data for given symbol and timeframe

        Args:
            symbol: Stock ticker (e.g., 'AAPL')
            timeframe: '1min', '5min', '15min', '30min', '1h', '1D', '1W', '1M'
            outputsize: 'compact' (100 points) or 'full' (20+ years for daily)

        Returns:
            {
                'symbol': str,
                'timeframe': str,
                'data': [
                    {
                        'timestamp': str,
                        'open': float,
                        'high': float,
                        'low': float,
                        'close': float,
                        'volume': int
                    }
                ],
                'metadata': dict
            }
        """
        try:
            interval = self.timeframe_map.get(timeframe, '1D')

            # Intraday data (1min - 60min)
            if interval in ['1min', '5min', '15min', '30min', '60min']:
                return await self._get_intraday_data(symbol, interval, outputsize)

            # Daily data
            elif interval == 'daily':
                return await self._get_daily_data(symbol, outputsize)

            # Weekly data
            elif interval == 'weekly':
                return await self._get_weekly_data(symbol)

            # Monthly data
            elif interval == 'monthly':
                return await self._get_monthly_data(symbol)

            else:
                raise ValueError(f"Unsupported timeframe: {timeframe}")

        except Exception as e:
            logger.error(f"[{self.name}] Error fetching historical data for {symbol}: {e}")
            return self._error_result(f"Failed to fetch historical data: {str(e)}")

    async def _get_intraday_data(
        self,
        symbol: str,
        interval: str,
        outputsize: str
    ) -> Dict[str, Any]:
        """Fetch intraday OHLCV data using TIME_SERIES_INTRADAY"""
        try:
            # Use MCP AlphaVantage tool (would be called via MCP in production)
            # For now, return structure that will be populated by MCP call

            logger.info(f"[{self.name}] Fetching intraday data for {symbol} at {interval} interval")

            # This will be replaced with actual MCP tool call:
            # result = await mcp.call_tool('mcp__alphavantage__TIME_SERIES_INTRADAY', {
            #     'symbol': symbol,
            #     'interval': interval,
            #     'outputsize': outputsize,
            #     'datatype': 'json'
            # })

            return {
                'symbol': symbol,
                'timeframe': interval,
                'interval': interval,
                'outputsize': outputsize,
                'data': [],  # Will be populated by MCP call
                'metadata': {
                    'source': 'AlphaVantage',
                    'api': 'TIME_SERIES_INTRADAY',
                    'last_refreshed': datetime.now().isoformat()
                }
            }

        except Exception as e:
            logger.error(f"[{self.name}] Intraday data error: {e}")
            return self._error_result(str(e))

    async def _get_daily_data(
        self,
        symbol: str,
        outputsize: str = 'full'
    ) -> Dict[str, Any]:
        """Fetch daily OHLCV data using TIME_SERIES_DAILY"""
        try:
            logger.info(f"[{self.name}] Fetching daily data for {symbol}")

            # MCP call structure:
            # result = await mcp.call_tool('mcp__alphavantage__TIME_SERIES_DAILY', {
            #     'symbol': symbol,
            #     'outputsize': outputsize,
            #     'datatype': 'json'
            # })

            return {
                'symbol': symbol,
                'timeframe': 'daily',
                'outputsize': outputsize,
                'data': [],  # Will be populated by MCP call
                'metadata': {
                    'source': 'AlphaVantage',
                    'api': 'TIME_SERIES_DAILY',
                    'last_refreshed': datetime.now().isoformat(),
                    'historical_range': '20+ years' if outputsize == 'full' else '100 days'
                }
            }

        except Exception as e:
            logger.error(f"[{self.name}] Daily data error: {e}")
            return self._error_result(str(e))

    async def _get_weekly_data(self, symbol: str) -> Dict[str, Any]:
        """Fetch weekly OHLCV data using TIME_SERIES_WEEKLY"""
        try:
            logger.info(f"[{self.name}] Fetching weekly data for {symbol}")

            # MCP call:
            # result = await mcp.call_tool('mcp__alphavantage__TIME_SERIES_WEEKLY', {
            #     'symbol': symbol,
            #     'datatype': 'json'
            # })

            return {
                'symbol': symbol,
                'timeframe': 'weekly',
                'data': [],
                'metadata': {
                    'source': 'AlphaVantage',
                    'api': 'TIME_SERIES_WEEKLY',
                    'last_refreshed': datetime.now().isoformat()
                }
            }

        except Exception as e:
            logger.error(f"[{self.name}] Weekly data error: {e}")
            return self._error_result(str(e))

    async def _get_monthly_data(self, symbol: str) -> Dict[str, Any]:
        """Fetch monthly OHLCV data using TIME_SERIES_MONTHLY"""
        try:
            logger.info(f"[{self.name}] Fetching monthly data for {symbol}")

            # MCP call:
            # result = await mcp.call_tool('mcp__alphavantage__TIME_SERIES_MONTHLY', {
            #     'symbol': symbol,
            #     'datatype': 'json'
            # })

            return {
                'symbol': symbol,
                'timeframe': 'monthly',
                'data': [],
                'metadata': {
                    'source': 'AlphaVantage',
                    'api': 'TIME_SERIES_MONTHLY',
                    'last_refreshed': datetime.now().isoformat()
                }
            }

        except Exception as e:
            logger.error(f"[{self.name}] Monthly data error: {e}")
            return self._error_result(str(e))

    async def get_technical_indicator(
        self,
        symbol: str,
        indicator: str,
        interval: str = 'daily',
        time_period: int = 14,
        series_type: str = 'close'
    ) -> Dict[str, Any]:
        """
        Fetch technical indicator data

        Args:
            symbol: Stock ticker
            indicator: 'RSI', 'MACD', 'BBANDS', 'ADX', 'STOCH', etc.
            interval: Time interval for calculation
            time_period: Lookback period
            series_type: 'close', 'open', 'high', 'low'

        Returns:
            {
                'symbol': str,
                'indicator': str,
                'data': [
                    {
                        'timestamp': str,
                        'value': float or dict (for multi-value indicators)
                    }
                ],
                'metadata': dict
            }
        """
        try:
            indicator_upper = indicator.upper()
            logger.info(f"[{self.name}] Fetching {indicator_upper} for {symbol}")

            # Map indicator to MCP tool
            indicator_tools = {
                'RSI': 'mcp__alphavantage__RSI',
                'MACD': 'mcp__alphavantage__MACD',
                'BBANDS': 'mcp__alphavantage__BBANDS',
                'ADX': 'mcp__alphavantage__ADX',
                'STOCH': 'mcp__alphavantage__STOCH',
                'STOCHF': 'mcp__alphavantage__STOCHF',
                'STOCHRSI': 'mcp__alphavantage__STOCHRSI',
                'WILLR': 'mcp__alphavantage__WILLR',
                'CCI': 'mcp__alphavantage__CCI',
                'MFI': 'mcp__alphavantage__MFI',
                'OBV': 'mcp__alphavantage__OBV',
                'ATR': 'mcp__alphavantage__ATR',
                'AROON': 'mcp__alphavantage__AROON',
                'AROONOSC': 'mcp__alphavantage__AROONOSC',
                'SMA': 'mcp__alphavantage__SMA',
                'EMA': 'mcp__alphavantage__EMA',
                'VWAP': 'mcp__alphavantage__VWAP'
            }

            if indicator_upper not in indicator_tools:
                raise ValueError(f"Unsupported indicator: {indicator}")

            # MCP call structure (will be implemented):
            # tool_name = indicator_tools[indicator_upper]
            # result = await mcp.call_tool(tool_name, {
            #     'symbol': symbol,
            #     'interval': interval,
            #     'time_period': time_period,
            #     'series_type': series_type,
            #     'datatype': 'json'
            # })

            return {
                'symbol': symbol,
                'indicator': indicator_upper,
                'interval': interval,
                'time_period': time_period,
                'data': [],  # Will be populated by MCP call
                'metadata': {
                    'source': 'AlphaVantage',
                    'api': indicator_tools[indicator_upper],
                    'series_type': series_type,
                    'last_refreshed': datetime.now().isoformat()
                }
            }

        except Exception as e:
            logger.error(f"[{self.name}] Indicator error: {e}")
            return self._error_result(str(e))

    async def get_multiple_indicators(
        self,
        symbol: str,
        indicators: List[str],
        interval: str = 'daily',
        time_period: int = 14
    ) -> Dict[str, Any]:
        """
        Fetch multiple technical indicators in parallel

        Args:
            symbol: Stock ticker
            indicators: List of indicator names ['RSI', 'MACD', 'BBANDS', ...]
            interval: Time interval
            time_period: Lookback period

        Returns:
            {
                'symbol': str,
                'indicators': {
                    'RSI': {...},
                    'MACD': {...},
                    ...
                }
            }
        """
        try:
            logger.info(f"[{self.name}] Fetching {len(indicators)} indicators for {symbol}")

            # Fetch all indicators in parallel
            tasks = [
                self.get_technical_indicator(symbol, ind, interval, time_period)
                for ind in indicators
            ]

            results = await asyncio.gather(*tasks, return_exceptions=True)

            # Organize results
            indicator_data = {}
            for ind, result in zip(indicators, results):
                if isinstance(result, Exception):
                    logger.error(f"[{self.name}] Error fetching {ind}: {result}")
                    indicator_data[ind] = {'error': str(result)}
                else:
                    indicator_data[ind] = result

            return {
                'symbol': symbol,
                'interval': interval,
                'indicators': indicator_data,
                'metadata': {
                    'total_indicators': len(indicators),
                    'successful': len([r for r in results if not isinstance(r, Exception)]),
                    'failed': len([r for r in results if isinstance(r, Exception)])
                }
            }

        except Exception as e:
            logger.error(f"[{self.name}] Multiple indicators error: {e}")
            return self._error_result(str(e))

    async def get_company_overview(self, symbol: str) -> Dict[str, Any]:
        """
        Fetch company fundamentals using COMPANY_OVERVIEW
        Includes EPS, Revenue, Market Cap, etc.

        Returns:
            {
                'symbol': str,
                'eps': float,
                'revenue': float,
                'market_cap': float,
                'pe_ratio': float,
                'beta': float,
                ...
            }
        """
        try:
            logger.info(f"[{self.name}] Fetching company overview for {symbol}")

            # MCP call:
            # result = await mcp.call_tool('mcp__alphavantage__COMPANY_OVERVIEW', {
            #     'symbol': symbol
            # })

            return {
                'symbol': symbol,
                'data': {},  # Will be populated by MCP call
                'metadata': {
                    'source': 'AlphaVantage',
                    'api': 'COMPANY_OVERVIEW',
                    'last_refreshed': datetime.now().isoformat()
                }
            }

        except Exception as e:
            logger.error(f"[{self.name}] Company overview error: {e}")
            return self._error_result(str(e))

    async def get_earnings(self, symbol: str) -> Dict[str, Any]:
        """Fetch earnings data using EARNINGS API"""
        try:
            logger.info(f"[{self.name}] Fetching earnings for {symbol}")

            # MCP call:
            # result = await mcp.call_tool('mcp__alphavantage__EARNINGS', {
            #     'symbol': symbol
            # })

            return {
                'symbol': symbol,
                'data': {},
                'metadata': {
                    'source': 'AlphaVantage',
                    'api': 'EARNINGS',
                    'last_refreshed': datetime.now().isoformat()
                }
            }

        except Exception as e:
            logger.error(f"[{self.name}] Earnings error: {e}")
            return self._error_result(str(e))

    async def get_cash_flow(self, symbol: str) -> Dict[str, Any]:
        """Fetch cash flow statement using CASH_FLOW API"""
        try:
            logger.info(f"[{self.name}] Fetching cash flow for {symbol}")

            # MCP call:
            # result = await mcp.call_tool('mcp__alphavantage__CASH_FLOW', {
            #     'symbol': symbol
            # })

            return {
                'symbol': symbol,
                'data': {},
                'metadata': {
                    'source': 'AlphaVantage',
                    'api': 'CASH_FLOW',
                    'last_refreshed': datetime.now().isoformat()
                }
            }

        except Exception as e:
            logger.error(f"[{self.name}] Cash flow error: {e}")
            return self._error_result(str(e))

    async def get_balance_sheet(self, symbol: str) -> Dict[str, Any]:
        """Fetch balance sheet using BALANCE_SHEET API"""
        try:
            logger.info(f"[{self.name}] Fetching balance sheet for {symbol}")

            # MCP call:
            # result = await mcp.call_tool('mcp__alphavantage__BALANCE_SHEET', {
            #     'symbol': symbol
            # })

            return {
                'symbol': symbol,
                'data': {},
                'metadata': {
                    'source': 'AlphaVantage',
                    'api': 'BALANCE_SHEET',
                    'last_refreshed': datetime.now().isoformat()
                }
            }

        except Exception as e:
            logger.error(f"[{self.name}] Balance sheet error: {e}")
            return self._error_result(str(e))

    def _error_result(self, error_msg: str) -> Dict[str, Any]:
        """Return error result structure"""
        return {
            'error': error_msg,
            'success': False,
            'timestamp': datetime.now().isoformat()
        }


# Singleton instance
alphavantage_chart_service = AlphaVantageChartService()
