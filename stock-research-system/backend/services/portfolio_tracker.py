"""
Portfolio Tracking System (Phase 4)
Track user portfolios, calculate ROI, and measure recommendation accuracy
"""

import logging
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
from dataclasses import dataclass
import yfinance as yf

logger = logging.getLogger(__name__)


@dataclass
class Position:
    """Individual stock position"""
    symbol: str
    quantity: float
    entry_price: float
    entry_date: datetime
    recommendation_id: str
    target_price: float
    stop_loss: float


@dataclass
class PortfolioMetrics:
    """Portfolio performance metrics"""
    total_value: float
    total_cost: float
    total_return: float
    return_percentage: float
    winning_positions: int
    losing_positions: int
    win_rate: float
    best_performer: Dict[str, Any]
    worst_performer: Dict[str, Any]


class PortfolioTracker:
    """
    Track user portfolios and measure ROI
    Validates AI recommendation accuracy in real-world trading
    """

    def __init__(self, database):
        self.database = database
        self.positions_collection = database['portfolio_positions']
        self.portfolios_collection = database['user_portfolios']
        self.trades_collection = database['trade_history']

    async def create_portfolio(self, user_id: str, name: str = "Default Portfolio") -> str:
        """Create new portfolio for user"""
        portfolio = {
            "user_id": user_id,
            "name": name,
            "created_at": datetime.utcnow(),
            "cash_balance": 100000.0,  # Start with $100K virtual cash
            "total_value": 100000.0,
            "metrics": {
                "total_return": 0.0,
                "win_rate": 0.0,
                "trades_count": 0
            }
        }

        result = await self.portfolios_collection.insert_one(portfolio)
        portfolio_id = str(result.inserted_id)

        logger.info(f"[Portfolio] Created portfolio {portfolio_id} for user {user_id}")
        return portfolio_id

    async def execute_trade(
        self,
        portfolio_id: str,
        symbol: str,
        action: str,
        quantity: float,
        recommendation_id: str = None,
        target_price: float = None,
        stop_loss: float = None
    ) -> Dict[str, Any]:
        """
        Execute trade based on AI recommendation

        Args:
            portfolio_id: Portfolio ID
            symbol: Stock symbol
            action: BUY or SELL
            quantity: Number of shares
            recommendation_id: AI recommendation ID
            target_price: Target price from recommendation
            stop_loss: Stop loss from recommendation
        """
        # Get current price
        current_price = await self._get_current_price(symbol)
        if not current_price:
            return {"success": False, "error": "Failed to get current price"}

        # Get portfolio
        portfolio = await self.portfolios_collection.find_one({"_id": portfolio_id})
        if not portfolio:
            return {"success": False, "error": "Portfolio not found"}

        trade_value = current_price * quantity

        if action == "BUY":
            # Check if enough cash
            if portfolio['cash_balance'] < trade_value:
                return {"success": False, "error": "Insufficient funds"}

            # Create position
            position = {
                "portfolio_id": portfolio_id,
                "symbol": symbol,
                "quantity": quantity,
                "entry_price": current_price,
                "entry_date": datetime.utcnow(),
                "recommendation_id": recommendation_id,
                "target_price": target_price,
                "stop_loss": stop_loss,
                "status": "open"
            }

            await self.positions_collection.insert_one(position)

            # Update portfolio
            await self.portfolios_collection.update_one(
                {"_id": portfolio_id},
                {
                    "$inc": {"cash_balance": -trade_value},
                    "$set": {"updated_at": datetime.utcnow()}
                }
            )

        elif action == "SELL":
            # Find position
            position = await self.positions_collection.find_one({
                "portfolio_id": portfolio_id,
                "symbol": symbol,
                "status": "open"
            })

            if not position:
                return {"success": False, "error": "No open position found"}

            # Calculate profit/loss
            entry_value = position['entry_price'] * position['quantity']
            exit_value = current_price * quantity
            profit_loss = exit_value - entry_value
            return_pct = (profit_loss / entry_value) * 100

            # Close position
            await self.positions_collection.update_one(
                {"_id": position['_id']},
                {
                    "$set": {
                        "status": "closed",
                        "exit_price": current_price,
                        "exit_date": datetime.utcnow(),
                        "profit_loss": profit_loss,
                        "return_percentage": return_pct
                    }
                }
            )

            # Update portfolio
            await self.portfolios_collection.update_one(
                {"_id": portfolio_id},
                {
                    "$inc": {
                        "cash_balance": exit_value,
                        "metrics.trades_count": 1
                    },
                    "$set": {"updated_at": datetime.utcnow()}
                }
            )

        # Record trade
        trade = {
            "portfolio_id": portfolio_id,
            "symbol": symbol,
            "action": action,
            "quantity": quantity,
            "price": current_price,
            "timestamp": datetime.utcnow(),
            "recommendation_id": recommendation_id
        }
        await self.trades_collection.insert_one(trade)

        return {
            "success": True,
            "price": current_price,
            "value": trade_value,
            "action": action
        }

    async def get_portfolio_metrics(self, portfolio_id: str) -> PortfolioMetrics:
        """Calculate comprehensive portfolio metrics"""

        # Get portfolio
        portfolio = await self.portfolios_collection.find_one({"_id": portfolio_id})
        if not portfolio:
            return None

        # Get all positions
        positions = await self.positions_collection.find({"portfolio_id": portfolio_id}).to_list(None)

        # Calculate current values
        total_position_value = 0.0
        total_cost = 0.0
        winning_count = 0
        losing_count = 0
        best_return = -float('inf')
        worst_return = float('inf')
        best_position = None
        worst_position = None

        for pos in positions:
            if pos['status'] == 'open':
                current_price = await self._get_current_price(pos['symbol'])
                position_value = current_price * pos['quantity']
                position_cost = pos['entry_price'] * pos['quantity']
                position_return = ((current_price - pos['entry_price']) / pos['entry_price']) * 100

                total_position_value += position_value
                total_cost += position_cost

                if position_return > 0:
                    winning_count += 1
                else:
                    losing_count += 1

                if position_return > best_return:
                    best_return = position_return
                    best_position = {
                        "symbol": pos['symbol'],
                        "return": position_return,
                        "value": position_value
                    }

                if position_return < worst_return:
                    worst_return = position_return
                    worst_position = {
                        "symbol": pos['symbol'],
                        "return": position_return,
                        "value": position_value
                    }

        total_value = portfolio['cash_balance'] + total_position_value
        initial_value = 100000.0  # Starting cash
        total_return = total_value - initial_value
        return_pct = (total_return / initial_value) * 100
        win_rate = winning_count / max(winning_count + losing_count, 1)

        return PortfolioMetrics(
            total_value=total_value,
            total_cost=total_cost,
            total_return=total_return,
            return_percentage=return_pct,
            winning_positions=winning_count,
            losing_positions=losing_count,
            win_rate=win_rate,
            best_performer=best_position or {},
            worst_performer=worst_position or {}
        )

    async def check_stop_loss_targets(self, portfolio_id: str) -> List[Dict]:
        """Check if any positions hit stop loss or target price"""
        alerts = []

        positions = await self.positions_collection.find({
            "portfolio_id": portfolio_id,
            "status": "open"
        }).to_list(None)

        for pos in positions:
            current_price = await self._get_current_price(pos['symbol'])

            # Check stop loss
            if pos.get('stop_loss') and current_price <= pos['stop_loss']:
                alerts.append({
                    "type": "stop_loss_hit",
                    "symbol": pos['symbol'],
                    "current_price": current_price,
                    "stop_loss": pos['stop_loss'],
                    "action": "SELL",
                    "message": f"{pos['symbol']} hit stop loss at ${current_price:.2f}"
                })

            # Check target price
            if pos.get('target_price') and current_price >= pos['target_price']:
                alerts.append({
                    "type": "target_price_hit",
                    "symbol": pos['symbol'],
                    "current_price": current_price,
                    "target_price": pos['target_price'],
                    "action": "SELL",
                    "message": f"{pos['symbol']} hit target price at ${current_price:.2f}"
                })

        return alerts

    async def get_recommendation_accuracy(self, user_id: str) -> Dict[str, Any]:
        """Calculate accuracy of AI recommendations for this user"""

        # Get all closed positions with recommendations
        positions = await self.positions_collection.find({
            "status": "closed",
            "recommendation_id": {"$exists": True}
        }).to_list(None)

        if not positions:
            return {"total": 0, "accuracy": 0, "avg_return": 0}

        total = len(positions)
        profitable = sum(1 for p in positions if p.get('profit_loss', 0) > 0)
        avg_return = sum(p.get('return_percentage', 0) for p in positions) / total

        return {
            "total_recommendations": total,
            "accuracy": profitable / total,
            "avg_return": avg_return,
            "profitable_count": profitable,
            "unprofitable_count": total - profitable
        }

    async def _get_current_price(self, symbol: str) -> Optional[float]:
        """Get current stock price from Yahoo Finance"""
        try:
            ticker = yf.Ticker(symbol)
            data = ticker.history(period="1d")
            if not data.empty:
                return float(data['Close'].iloc[-1])
            return None
        except Exception as e:
            logger.error(f"[Portfolio] Failed to get price for {symbol}: {e}")
            return None


# Global portfolio tracker
portfolio_tracker = None


def get_portfolio_tracker(database):
    """Get or create portfolio tracker instance"""
    global portfolio_tracker
    if portfolio_tracker is None:
        portfolio_tracker = PortfolioTracker(database)
    return portfolio_tracker
