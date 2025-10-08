"""
Yahoo Finance Service for fetching stock data
"""

import yfinance as yf
from typing import Dict, Any, Optional
import logging

logger = logging.getLogger(__name__)


class YahooFinanceService:
    """Service for fetching stock data from Yahoo Finance"""

    def __init__(self):
        self.name = "Yahoo Finance Service"

    async def get_stock_price(self, symbol: str) -> Dict[str, Any]:
        """Get stock price data for a symbol"""
        try:
            ticker = yf.Ticker(symbol)
            data = ticker.info

            return {
                "symbol": symbol,
                "price": data.get("currentPrice", data.get("regularMarketPrice", 0)),
                "change": data.get("regularMarketChange", 0),
                "changePercent": data.get("regularMarketChangePercent", 0),
                "volume": data.get("volume", 0),
                "marketCap": data.get("marketCap", 0),
                "dayHigh": data.get("dayHigh", 0),
                "dayLow": data.get("dayLow", 0),
                "previousClose": data.get("previousClose", 0)
            }
        except Exception as e:
            logger.error(f"Error fetching {symbol} from Yahoo Finance: {e}")
            return {
                "symbol": symbol,
                "price": 0,
                "error": str(e)
            }

    async def get_historical_data(self, symbol: str, period: str = "1mo") -> Dict[str, Any]:
        """Get historical price data"""
        try:
            ticker = yf.Ticker(symbol)
            hist = ticker.history(period=period)

            return {
                "symbol": symbol,
                "history": hist.to_dict() if not hist.empty else {},
                "period": period
            }
        except Exception as e:
            logger.error(f"Error fetching historical data for {symbol}: {e}")
            return {
                "symbol": symbol,
                "history": {},
                "error": str(e)
            }

    async def get_financials(self, symbol: str) -> Dict[str, Any]:
        """Get financial statements"""
        try:
            ticker = yf.Ticker(symbol)

            return {
                "symbol": symbol,
                "income_statement": ticker.income_stmt.to_dict() if hasattr(ticker, 'income_stmt') else {},
                "balance_sheet": ticker.balance_sheet.to_dict() if hasattr(ticker, 'balance_sheet') else {},
                "cash_flow": ticker.cash_flow.to_dict() if hasattr(ticker, 'cash_flow') else {}
            }
        except Exception as e:
            logger.error(f"Error fetching financials for {symbol}: {e}")
            return {
                "symbol": symbol,
                "error": str(e)
            }