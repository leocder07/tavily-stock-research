"""Service to fetch live stock prices using yfinance"""

import yfinance as yf
from datetime import datetime
from typing import Dict, List, Optional
import logging

logger = logging.getLogger(__name__)


class LivePriceService:
    """Service for fetching real-time stock prices"""

    @staticmethod
    def get_live_price(symbol: str) -> Optional[Dict]:
        """
        Fetch live price for a single stock symbol.

        Args:
            symbol: Stock ticker symbol (e.g., 'AAPL')

        Returns:
            Dict with price data or None if failed
        """
        try:
            ticker = yf.Ticker(symbol)
            info = ticker.info

            # Get latest data
            hist = ticker.history(period="1d")
            if hist.empty:
                logger.warning(f"No price data available for {symbol}")
                return None

            current_price = hist['Close'].iloc[-1]
            prev_close = info.get('previousClose', current_price)
            day_change = current_price - prev_close
            day_change_percent = (day_change / prev_close * 100) if prev_close else 0

            return {
                "symbol": symbol,
                "current_price": round(float(current_price), 2),
                "previous_close": round(float(prev_close), 2),
                "day_change": round(float(day_change), 2),
                "day_change_percent": round(float(day_change_percent), 2),
                "timestamp": datetime.utcnow().isoformat(),
                "market_cap": info.get('marketCap'),
                "volume": info.get('volume'),
                "name": info.get('longName', symbol)
            }

        except Exception as e:
            logger.error(f"Error fetching price for {symbol}: {e}")
            return None

    @staticmethod
    def get_multiple_prices(symbols: List[str]) -> Dict[str, Dict]:
        """
        Fetch live prices for multiple stocks.

        Args:
            symbols: List of stock ticker symbols

        Returns:
            Dict mapping symbols to their price data
        """
        prices = {}
        for symbol in symbols:
            price_data = LivePriceService.get_live_price(symbol)
            if price_data:
                prices[symbol] = price_data

        return prices


    @staticmethod
    async def update_portfolio_prices(db, user_email: str) -> bool:
        """
        Update portfolio with live prices.

        Args:
            db: MongoDB database instance
            user_email: User's email

        Returns:
            True if successful, False otherwise
        """
        try:
            portfolios_collection = db['portfolios']

            # Get user's portfolio
            portfolio = await portfolios_collection.find_one({"user_email": user_email})
            if not portfolio:
                logger.error(f"Portfolio not found for {user_email}")
                return False

            # Get all symbols
            symbols = [h['symbol'] for h in portfolio['holdings']]

            # Fetch live prices
            live_prices = LivePriceService.get_multiple_prices(symbols)

            # Update holdings with live prices
            updated_holdings = []
            total_value = 0

            for holding in portfolio['holdings']:
                symbol = holding['symbol']
                if symbol in live_prices:
                    price_data = live_prices[symbol]

                    # Update current price
                    holding['current_price'] = price_data['current_price']
                    holding['day_change'] = price_data['day_change']
                    holding['day_change_percent'] = price_data['day_change_percent']

                    # Recalculate values
                    holding['value'] = round(holding['shares'] * holding['current_price'], 2)
                    holding['cost_basis'] = round(holding['shares'] * holding['avg_cost'], 2)
                    holding['total_return'] = round(holding['value'] - holding['cost_basis'], 2)
                    holding['total_return_percent'] = round(
                        (holding['total_return'] / holding['cost_basis']) * 100, 2
                    )

                    total_value += holding['value']

                updated_holdings.append(holding)

            # Update allocations
            for holding in updated_holdings:
                holding['allocation'] = round((holding['value'] / total_value) * 100, 2) if total_value > 0 else 0

            # Calculate portfolio totals
            total_invested = sum(h['cost_basis'] for h in updated_holdings)
            total_return = total_value - total_invested
            total_return_percent = (total_return / total_invested) * 100 if total_invested > 0 else 0

            # Update database
            await portfolios_collection.update_one(
                {"user_email": user_email},
                {
                    "$set": {
                        "holdings": updated_holdings,
                        "current_value": round(total_value, 2),
                        "total_return": round(total_return, 2),
                        "total_return_percent": round(total_return_percent, 2),
                        "updated_at": datetime.utcnow()
                    }
                }
            )

            logger.info(f"Portfolio updated with live prices for {user_email}")
            return True

        except Exception as e:
            logger.error(f"Error updating portfolio prices: {e}")
            return False
