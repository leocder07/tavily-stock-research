"""
Financial Data Service
Provides accurate financial data from multiple sources (yfinance, Alpha Vantage, FMP)
with validation, fallback mechanisms, and intelligent rate limiting.
"""

import os
import logging
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
import yfinance as yf
import httpx
from decimal import Decimal, InvalidOperation

# Import rate limiter
try:
    from services.rate_limiter import rate_limiter
except ImportError:
    # Fallback if rate_limiter not available
    class DummyRateLimiter:
        async def execute_with_limit(self, *args, **kwargs):
            func = kwargs.get('func') or args[1]
            func_args = args[2:] if len(args) > 2 else []
            return await func(*func_args)
    rate_limiter = DummyRateLimiter()

logger = logging.getLogger(__name__)


class FinancialDataService:
    """Service for fetching and validating financial data"""

    def __init__(self):
        self.alpha_vantage_key = os.getenv("ALPHA_VANTAGE_API_KEY", "")
        self.fmp_key = os.getenv("FMP_API_KEY", "")
        self.timeout = 30.0
        self.alpha_vantage_base_url = "https://www.alphavantage.co/query"

    async def get_stock_quote(self, symbol: str) -> Dict[str, Any]:
        """
        Get real-time stock quote with validation and rate limiting

        Returns:
            {
                'symbol': 'TSLA',
                'price': 444.72,
                'change': 1.51,
                'change_percent': 0.34,
                'volume': 73340000,
                'market_cap': 1478760000000,
                'day_high': 448.50,
                'day_low': 441.20,
                'open': 443.00,
                'previous_close': 443.21,
                '52_week_high': 488.54,
                '52_week_low': 138.80,
                'data_quality': 95,
                'last_updated': '2025-10-01T12:00:00Z'
            }
        """
        async def _fetch_quote():
            ticker = yf.Ticker(symbol)
            info = ticker.info

            # Get current price
            current_price = info.get('currentPrice') or info.get('regularMarketPrice')
            previous_close = info.get('previousClose')

            if not current_price or not previous_close:
                logger.warning(f"Missing price data for {symbol}")
                return self._get_fallback_quote(symbol)

            # Calculate changes
            change = current_price - previous_close
            change_percent = (change / previous_close) * 100 if previous_close else 0

            quote = {
                'symbol': symbol.upper(),
                'price': round(current_price, 2),
                'change': round(change, 2),
                'change_percent': round(change_percent, 4),
                'volume': info.get('volume', 0),
                'market_cap': info.get('marketCap', 0),
                'day_high': info.get('dayHigh') or info.get('regularMarketDayHigh'),
                'day_low': info.get('dayLow') or info.get('regularMarketDayLow'),
                'open': info.get('open') or info.get('regularMarketOpen'),
                'previous_close': previous_close,
                '52_week_high': info.get('fiftyTwoWeekHigh'),
                '52_week_low': info.get('fiftyTwoWeekLow'),
                'data_quality': self._calculate_data_quality(info),
                'last_updated': datetime.utcnow().isoformat() + 'Z'
            }

            return quote

        try:
            # Use rate limiter with caching for stock prices
            return await rate_limiter.execute_with_limit(
                api_name='yahoo_finance',
                func=_fetch_quote,
                cache_key=f'quote:{symbol}',
                cache_type='stock_price',
                priority='real_time_price'
            )
        except Exception as e:
            logger.error(f"Error fetching quote for {symbol}: {e}")
            return self._get_fallback_quote(symbol)

    async def get_alpha_vantage_overview(self, symbol: str) -> Optional[Dict[str, Any]]:
        """Get company overview from Alpha Vantage with rate limiting"""
        if not self.alpha_vantage_key:
            return None

        async def _fetch_overview():
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                params = {
                    'function': 'OVERVIEW',
                    'symbol': symbol,
                    'apikey': self.alpha_vantage_key
                }
                response = await client.get(self.alpha_vantage_base_url, params=params)
                response.raise_for_status()
                data = response.json()

                # Alpha Vantage returns empty dict or error message if rate limited
                if not data or 'Error Message' in data or 'Note' in data:
                    logger.warning(f"Alpha Vantage rate limit or error for {symbol}")
                    return None

                return data

        try:
            # Use rate limiter with both daily and minute limits
            return await rate_limiter.execute_with_limit(
                api_name='alpha_vantage_minute',  # 5 calls/minute limit
                func=_fetch_overview,
                cache_key=f'av_overview:{symbol}',
                cache_type='fundamental',
                priority='fundamental_data'
            )
        except Exception as e:
            logger.error(f"Alpha Vantage overview error for {symbol}: {e}")
            return None

    async def get_fundamental_data(self, symbol: str) -> Dict[str, Any]:
        """
        Get comprehensive fundamental data with validation
        Uses yfinance as primary source with Alpha Vantage enrichment

        Returns:
            {
                'symbol': 'TSLA',
                'pe_ratio': 65.5,
                'eps': 6.79,
                'forward_pe': 58.2,
                'peg_ratio': 2.1,
                'price_to_book': 12.5,
                'price_to_sales': 8.2,
                'revenue': 96773000000,
                'revenue_growth': 0.187,
                'profit_margin': 0.096,
                'operating_margin': 0.122,
                'gross_margin': 0.189,
                'roe': 0.215,
                'roa': 0.087,
                'debt_to_equity': 0.15,
                'current_ratio': 1.73,
                'quick_ratio': 1.18,
                'free_cash_flow': 4423000000,
                'earnings_date': '2025-01-24',
                'dividend_yield': 0.0,
                'beta': 2.31,
                'data_quality': 92,
                'last_updated': '2025-10-01T12:00:00Z'
            }
        """
        try:
            ticker = yf.Ticker(symbol)
            info = ticker.info

            # Get earnings per share
            eps = self._get_valid_eps(info)
            current_price = info.get('currentPrice') or info.get('regularMarketPrice', 0)

            # Calculate P/E ratio with validation
            pe_ratio = self._calculate_pe_ratio(current_price, eps)

            fundamentals = {
                'symbol': symbol.upper(),
                'pe_ratio': pe_ratio,
                'eps': eps,
                'forward_pe': self._validate_ratio(info.get('forwardPE'), 'forward_pe'),
                'peg_ratio': self._validate_ratio(info.get('pegRatio'), 'peg'),
                'price_to_book': self._validate_ratio(info.get('priceToBook'), 'pb'),
                'price_to_sales': self._validate_ratio(info.get('priceToSalesTrailing12Months'), 'ps'),
                'revenue': info.get('totalRevenue', 0),
                'revenue_growth': self._validate_percentage(info.get('revenueGrowth')),
                'profit_margin': self._validate_percentage(info.get('profitMargins')),
                'operating_margin': self._validate_percentage(info.get('operatingMargins')),
                'gross_margin': self._validate_percentage(info.get('grossMargins')),
                'roe': self._validate_percentage(info.get('returnOnEquity')),
                'roa': self._validate_percentage(info.get('returnOnAssets')),
                'debt_to_equity': self._validate_ratio(info.get('debtToEquity'), 'de', max_val=500),
                'current_ratio': self._validate_ratio(info.get('currentRatio'), 'current'),
                'quick_ratio': self._validate_ratio(info.get('quickRatio'), 'quick'),
                'free_cash_flow': info.get('freeCashflow', 0),
                'earnings_date': self._get_next_earnings_date(ticker),
                'dividend_yield': self._validate_percentage(info.get('dividendYield')),
                'beta': self._validate_ratio(info.get('beta'), 'beta', min_val=-5, max_val=10),
                'data_quality': self._calculate_fundamental_quality(info, eps, pe_ratio),
                'last_updated': datetime.utcnow().isoformat() + 'Z'
            }

            # Enrich with Alpha Vantage data if available
            av_data = await self.get_alpha_vantage_overview(symbol)
            if av_data:
                fundamentals['alpha_vantage_enrichment'] = {
                    'description': av_data.get('Description'),
                    'sector': av_data.get('Sector'),
                    'industry': av_data.get('Industry'),
                    'analyst_target_price': self._validate_ratio(
                        float(av_data.get('AnalystTargetPrice', 0)) if av_data.get('AnalystTargetPrice') else None,
                        'target_price'
                    ),
                    '52_week_high_av': self._validate_ratio(
                        float(av_data.get('52WeekHigh', 0)) if av_data.get('52WeekHigh') else None,
                        '52w_high'
                    ),
                    '52_week_low_av': self._validate_ratio(
                        float(av_data.get('52WeekLow', 0)) if av_data.get('52WeekLow') else None,
                        '52w_low'
                    )
                }
                logger.info(f"Enriched {symbol} with Alpha Vantage data")

            return fundamentals

        except Exception as e:
            logger.error(f"Error fetching fundamentals for {symbol}: {e}")
            return self._get_fallback_fundamentals(symbol)

    async def get_historical_data(self, symbol: str, period: str = "1y", interval: str = "1d") -> List[Dict[str, Any]]:
        """
        Get historical OHLCV data

        Args:
            symbol: Stock symbol
            period: Time period (1d, 5d, 1mo, 3mo, 6mo, 1y, 2y, 5y, 10y, ytd, max)
            interval: Data interval (1m, 2m, 5m, 15m, 30m, 60m, 90m, 1h, 1d, 5d, 1wk, 1mo, 3mo)

        Returns:
            List of OHLCV data points:
            [
                {
                    'timestamp': '2024-10-01T00:00:00Z',
                    'open': 443.00,
                    'high': 448.50,
                    'low': 441.20,
                    'close': 444.72,
                    'volume': 73340000
                },
                ...
            ]
        """
        try:
            ticker = yf.Ticker(symbol)
            hist = ticker.history(period=period, interval=interval)

            if hist.empty:
                logger.warning(f"No historical data for {symbol}")
                return []

            # Convert to list of dictionaries
            historical_data = []
            for index, row in hist.iterrows():
                data_point = {
                    'timestamp': index.isoformat() + 'Z',
                    'open': round(float(row['Open']), 2),
                    'high': round(float(row['High']), 2),
                    'low': round(float(row['Low']), 2),
                    'close': round(float(row['Close']), 2),
                    'volume': int(row['Volume'])
                }
                historical_data.append(data_point)

            return historical_data

        except Exception as e:
            logger.error(f"Error fetching historical data for {symbol}: {e}")
            return []

    def _get_valid_eps(self, info: Dict) -> Optional[float]:
        """Extract and validate EPS"""
        eps = info.get('trailingEps') or info.get('forwardEps')

        if eps is None or eps == 0:
            return None

        try:
            eps_val = float(eps)
            # EPS should be reasonable (-100 to 1000 for most stocks)
            if -100 <= eps_val <= 1000:
                return round(eps_val, 2)
            else:
                logger.warning(f"EPS out of range: {eps_val}")
                return None
        except (ValueError, TypeError):
            return None

    def _calculate_pe_ratio(self, price: float, eps: Optional[float]) -> Optional[float]:
        """Calculate P/E ratio with validation"""
        if not price or not eps or eps == 0:
            return None

        try:
            pe = price / eps
            # P/E ratio should be reasonable (-100 to 1000)
            if -100 <= pe <= 1000:
                return round(pe, 2)
            else:
                logger.warning(f"P/E ratio out of range: {pe}")
                return None
        except (ZeroDivisionError, TypeError):
            return None

    def _validate_ratio(self, value: Any, ratio_type: str, min_val: float = -100, max_val: float = 1000) -> Optional[float]:
        """Validate financial ratios"""
        if value is None:
            return None

        try:
            val = float(value)
            if min_val <= val <= max_val:
                return round(val, 2)
            else:
                logger.warning(f"{ratio_type} ratio out of range: {val}")
                return None
        except (ValueError, TypeError):
            return None

    def _validate_percentage(self, value: Any) -> Optional[float]:
        """Validate percentage values"""
        if value is None:
            return None

        try:
            val = float(value)
            # Percentages should be between -1 (100% loss) and 10 (1000% gain)
            if -1 <= val <= 10:
                return round(val, 4)
            else:
                logger.warning(f"Percentage out of range: {val}")
                return None
        except (ValueError, TypeError):
            return None

    def _calculate_data_quality(self, info: Dict) -> int:
        """Calculate data quality score (0-100)"""
        required_fields = ['currentPrice', 'volume', 'marketCap', 'previousClose']
        present_fields = sum(1 for field in required_fields if info.get(field))

        quality = (present_fields / len(required_fields)) * 100
        return int(quality)

    def _calculate_fundamental_quality(self, info: Dict, eps: Optional[float], pe: Optional[float]) -> int:
        """Calculate fundamental data quality score (0-100)"""
        key_metrics = [
            'trailingEps' in info or eps is not None,
            'forwardPE' in info or pe is not None,
            'totalRevenue' in info,
            'profitMargins' in info,
            'debtToEquity' in info,
            'returnOnEquity' in info,
            'beta' in info
        ]

        quality = (sum(key_metrics) / len(key_metrics)) * 100
        return int(quality)

    def _get_next_earnings_date(self, ticker) -> Optional[str]:
        """Get next earnings date"""
        try:
            calendar = ticker.calendar
            if calendar is not None and 'Earnings Date' in calendar:
                earnings_date = calendar['Earnings Date'][0]
                return earnings_date.strftime('%Y-%m-%d')
        except Exception as e:
            logger.debug(f"Could not fetch earnings date: {e}")

        return None

    def _get_fallback_quote(self, symbol: str) -> Dict[str, Any]:
        """Fallback quote data when primary source fails"""
        return {
            'symbol': symbol.upper(),
            'price': None,
            'change': None,
            'change_percent': None,
            'volume': 0,
            'market_cap': 0,
            'day_high': None,
            'day_low': None,
            'open': None,
            'previous_close': None,
            '52_week_high': None,
            '52_week_low': None,
            'data_quality': 0,
            'last_updated': datetime.utcnow().isoformat() + 'Z',
            'error': 'Failed to fetch quote data'
        }

    def _get_fallback_fundamentals(self, symbol: str) -> Dict[str, Any]:
        """Fallback fundamental data when primary source fails"""
        return {
            'symbol': symbol.upper(),
            'pe_ratio': None,
            'eps': None,
            'forward_pe': None,
            'peg_ratio': None,
            'price_to_book': None,
            'price_to_sales': None,
            'revenue': 0,
            'revenue_growth': None,
            'profit_margin': None,
            'operating_margin': None,
            'gross_margin': None,
            'roe': None,
            'roa': None,
            'debt_to_equity': None,
            'current_ratio': None,
            'quick_ratio': None,
            'free_cash_flow': 0,
            'earnings_date': None,
            'dividend_yield': None,
            'beta': None,
            'data_quality': 0,
            'last_updated': datetime.utcnow().isoformat() + 'Z',
            'error': 'Failed to fetch fundamental data'
        }


# Global instance
financial_data_service = FinancialDataService()
