"""Portfolio API endpoints"""

from fastapi import APIRouter, HTTPException, Depends, Header, Body
from typing import Optional, Dict, Any, List
from datetime import datetime
from pydantic import BaseModel, Field
import logging
import yfinance as yf

from services.mongodb_connection import mongodb_connection

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/portfolio", tags=["portfolio"])


# Pydantic models for request validation
class HoldingCreate(BaseModel):
    symbol: str = Field(..., description="Stock symbol (e.g., AAPL)")
    shares: float = Field(..., gt=0, description="Number of shares")
    purchase_price: float = Field(..., gt=0, description="Purchase price per share")
    purchase_date: str = Field(..., description="Purchase date in YYYY-MM-DD format")
    notes: Optional[str] = Field(None, description="Optional notes")


class HoldingUpdate(BaseModel):
    shares: Optional[float] = Field(None, gt=0, description="Number of shares")
    purchase_price: Optional[float] = Field(None, gt=0, description="Purchase price per share")
    purchase_date: Optional[str] = Field(None, description="Purchase date in YYYY-MM-DD format")
    notes: Optional[str] = Field(None, description="Optional notes")


@router.get("")
async def get_portfolio(user_id: Optional[str] = None):
    """
    Get portfolio data for the current user.
    Returns empty portfolio structure if no portfolio exists.

    Args:
        user_id: Optional user ID from query params (supports both user_id and user_email)

    Returns:
        Portfolio data with metrics
    """
    try:
        # If no user_id provided or no portfolio exists, return empty structure
        if not user_id:
            logger.info("No user_id provided, returning empty portfolio")
            return {
                "total_value": 0,
                "day_change": 0,
                "day_change_percent": 0,
                "total_return_percent": 0,
                "win_rate": 0,
                "sharpe_ratio": 0,
                "holdings": []
            }

        db = mongodb_connection.get_database()
        portfolios_collection = db['portfolios']

        # Try to find portfolio by user_id first, then by user_email (for backwards compatibility)
        portfolio = await portfolios_collection.find_one(
            {"user_id": user_id},
            {"_id": 0}
        )

        # If not found by user_id, try user_email
        if not portfolio:
            portfolio = await portfolios_collection.find_one(
                {"user_email": user_id},
                {"_id": 0}
            )

        if not portfolio:
            logger.info(f"No portfolio found for user_id/email: {user_id}, returning empty portfolio")
            return {
                "total_value": 0,
                "day_change": 0,
                "day_change_percent": 0,
                "total_return_percent": 0,
                "win_rate": 0,
                "sharpe_ratio": 0,
                "holdings": []
            }

        logger.info(f"Found portfolio for user: {user_id}")
        logger.info(f"Portfolio value: ${portfolio.get('current_value', 0):,.2f}")

        # Return portfolio metrics in snake_case (frontend will transform)
        return {
            "total_value": portfolio.get("current_value", 0),
            "day_change": portfolio.get("day_change", 0),
            "day_change_percent": portfolio.get("day_change_percent", 0),
            "total_return": portfolio.get("current_value", 0) - portfolio.get("total_invested", 0),
            "total_return_percent": portfolio.get("total_return_percent", 0),
            "win_rate": portfolio.get("win_rate", 0),
            "sharpe_ratio": portfolio.get("sharpe_ratio", 0),
            "profitable_positions": 0,  # Calculate from holdings if needed
            "total_positions": len(portfolio.get("holdings", [])),
            "holdings": portfolio.get("holdings", [])
        }

    except Exception as e:
        logger.error(f"Error fetching portfolio: {e}")
        import traceback
        logger.error(traceback.format_exc())
        # Return empty portfolio on error instead of failing
        return {
            "total_value": 0,
            "day_change": 0,
            "day_change_percent": 0,
            "total_return_percent": 0,
            "win_rate": 0,
            "sharpe_ratio": 0,
            "holdings": []
        }


@router.get("/{user_email}")
async def get_user_portfolio(user_email: str, update_prices: bool = True):
    """
    Get portfolio data for a specific user with full metrics.

    Args:
        user_email: User's email address
        update_prices: If True, fetch live prices before returning (default: True)

    Returns:
        Portfolio data including holdings, metrics, and performance
    """
    try:
        db = mongodb_connection.get_database()
        portfolios_collection = db['portfolios']

        # Find portfolio for this user
        portfolio = await portfolios_collection.find_one(
            {"user_email": user_email},
            {"_id": 0}  # Exclude MongoDB ID from response
        )

        if not portfolio:
            raise HTTPException(status_code=404, detail=f"Portfolio not found for user {user_email}")

        # Calculate current values for all holdings with live prices
        holdings_with_metrics = []
        total_value = 0
        total_cost = 0

        for h in portfolio.get('holdings', []):
            # Get both current and previous close
            current_price, previous_close = await get_current_and_previous_price(h['symbol'])

            if current_price:
                holding_metrics = await calculate_holding_metrics(h, current_price, previous_close)
                holdings_with_metrics.append(holding_metrics)
                total_value += holding_metrics['current_value']
                total_cost += holding_metrics['cost_basis']

        # Calculate allocation percentage for each holding
        for holding_metrics in holdings_with_metrics:
            allocation = (holding_metrics['current_value'] / total_value * 100) if total_value > 0 else 0
            holding_metrics['allocation'] = round(allocation, 2)

        # Calculate portfolio-level metrics
        portfolio_metrics = calculate_portfolio_metrics(holdings_with_metrics, total_value, total_cost)

        return {
            "status": "success",
            "data": {
                "holdings": holdings_with_metrics,
                "user_email": user_email,
                **portfolio_metrics  # Spread all portfolio metrics
            }
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching portfolio for {user_email}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to fetch portfolio: {str(e)}")


@router.get("/{user_email}/holdings")
async def get_user_holdings(user_email: str):
    """
    Get just the holdings for a user's portfolio.

    Args:
        user_email: User's email address

    Returns:
        List of holdings with details
    """
    try:
        db = mongodb_connection.get_database()
        portfolios_collection = db['portfolios']

        portfolio = await portfolios_collection.find_one(
            {"user_email": user_email},
            {"holdings": 1, "_id": 0}
        )

        if not portfolio:
            raise HTTPException(status_code=404, detail=f"Portfolio not found for user {user_email}")

        return {
            "status": "success",
            "data": {
                "holdings": portfolio.get("holdings", [])
            }
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching holdings for {user_email}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to fetch holdings: {str(e)}")


@router.get("/{user_email}/metrics")
async def get_portfolio_metrics(user_email: str):
    """
    Get portfolio performance metrics.

    Args:
        user_email: User's email address

    Returns:
        Portfolio metrics including total value, returns, etc.
    """
    try:
        db = mongodb_connection.get_database()
        portfolios_collection = db['portfolios']

        portfolio = await portfolios_collection.find_one(
            {"user_email": user_email},
            {
                "total_invested": 1,
                "current_value": 1,
                "total_return": 1,
                "total_return_percent": 1,
                "_id": 0
            }
        )

        if not portfolio:
            raise HTTPException(status_code=404, detail=f"Portfolio not found for user {user_email}")

        # Calculate additional metrics
        holdings = await portfolios_collection.find_one(
            {"user_email": user_email},
            {"holdings": 1, "_id": 0}
        )

        # Calculate day change from holdings
        day_change = 0
        day_change_percent = 0

        if holdings and "holdings" in holdings:
            total_value = portfolio.get("current_value", 0)
            day_change = sum(
                h.get("day_change", 0) * h.get("shares", 0)
                for h in holdings["holdings"]
            )
            day_change_percent = (day_change / total_value * 100) if total_value > 0 else 0

        return {
            "status": "success",
            "data": {
                "totalValue": portfolio.get("current_value", 0),
                "dayChange": round(day_change, 2),
                "dayChangePercent": round(day_change_percent, 2),
                "totalReturn": portfolio.get("total_return_percent", 0),
                "winRate": 75,  # Placeholder - can be calculated from trade history
                "sharpeRatio": 1.85,  # Placeholder - needs historical data
            }
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching metrics for {user_email}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to fetch metrics: {str(e)}")


# Helper function to get current stock price
async def get_current_price(symbol: str) -> Optional[float]:
    """Get current stock price from Yahoo Finance"""
    try:
        ticker = yf.Ticker(symbol)
        data = ticker.history(period="1d")
        if not data.empty:
            return float(data['Close'].iloc[-1])
        return None
    except Exception as e:
        logger.error(f"Failed to get price for {symbol}: {e}")
        return None


# Helper function to get current and previous close prices
async def get_current_and_previous_price(symbol: str) -> tuple[Optional[float], Optional[float]]:
    """Get current price and previous close from Yahoo Finance"""
    try:
        ticker = yf.Ticker(symbol)
        data = ticker.history(period="2d")  # Get last 2 days
        if len(data) >= 2:
            current = float(data['Close'].iloc[-1])
            previous = float(data['Close'].iloc[-2])
            return current, previous
        elif len(data) == 1:
            current = float(data['Close'].iloc[-1])
            return current, current  # No previous data
        return None, None
    except Exception as e:
        logger.error(f"Failed to get prices for {symbol}: {e}")
        return None, None


# Helper function to calculate holding metrics
async def calculate_holding_metrics(holding: Dict[str, Any], current_price: float, previous_close: float = None) -> Dict[str, Any]:
    """Calculate current value, gain/loss, and return % for a holding"""
    purchase_price = holding.get('purchase_price', 0)
    shares = holding.get('shares', 0)

    cost_basis = purchase_price * shares
    current_value = current_price * shares
    gain_loss = current_value - cost_basis
    gain_loss_percent = (gain_loss / cost_basis * 100) if cost_basis > 0 else 0

    # Calculate day change if previous close available
    if previous_close and previous_close > 0:
        previous_value = previous_close * shares
        day_change_value = current_value - previous_value
        day_change_percent = (day_change_value / previous_value * 100)
    else:
        day_change_value = 0
        day_change_percent = 0

    return {
        **holding,
        'avg_cost': round(purchase_price, 2),
        'current_price': round(current_price, 2),
        'previous_close': round(previous_close, 2) if previous_close else None,
        'value': round(current_value, 2),
        'current_value': round(current_value, 2),
        'cost_basis': round(cost_basis, 2),
        'gain_loss': round(gain_loss, 2),
        'gain_loss_percent': round(gain_loss_percent, 2),
        'total_return_percent': round(gain_loss_percent, 2),
        'day_change_value': round(day_change_value, 2),
        'day_change_percent': round(day_change_percent, 2),
        'allocation': 0  # Calculated at portfolio level
    }


def calculate_portfolio_metrics(holdings_with_metrics: List[Dict[str, Any]], total_value: float, total_cost: float) -> Dict[str, Any]:
    """Calculate portfolio-level metrics"""

    # Total day change (sum of all holdings' day changes)
    total_day_change = sum(h.get('day_change_value', 0) for h in holdings_with_metrics)
    day_change_percent = (total_day_change / (total_value - total_day_change) * 100) if (total_value - total_day_change) > 0 else 0

    # Win rate (% of profitable positions)
    profitable = sum(1 for h in holdings_with_metrics if h.get('gain_loss', 0) > 0)
    total_positions = len(holdings_with_metrics)
    win_rate = (profitable / total_positions * 100) if total_positions > 0 else 0

    # Sharpe ratio (simplified calculation)
    # Formula: (Average Return - Risk Free Rate) / Standard Deviation of Returns
    returns = [h.get('total_return_percent', 0) for h in holdings_with_metrics]
    if returns and len(returns) > 1:
        avg_return = sum(returns) / len(returns)
        variance = sum((r - avg_return) ** 2 for r in returns) / len(returns)
        std_dev = variance ** 0.5
        risk_free_rate = 4.5  # Assume 4.5% risk-free rate (US Treasury)
        sharpe_ratio = (avg_return - risk_free_rate) / std_dev if std_dev > 0 else 0
    else:
        sharpe_ratio = 0

    return {
        'total_value': round(total_value, 2),
        'total_cost': round(total_cost, 2),
        'total_return': round(total_value - total_cost, 2),
        'total_return_percent': round((total_value - total_cost) / total_cost * 100, 2) if total_cost > 0 else 0,
        'day_change': round(total_day_change, 2),
        'day_change_percent': round(day_change_percent, 2),
        'win_rate': round(win_rate, 2),
        'sharpe_ratio': round(sharpe_ratio, 2),
        'profitable_positions': profitable,
        'total_positions': total_positions
    }


@router.post("/{user_email}/holdings")
async def add_holding(user_email: str, holding: HoldingCreate):
    """
    Add a new holding to user's portfolio.

    Args:
        user_email: User's email address
        holding: Holding details (symbol, shares, purchase_price, purchase_date)

    Returns:
        Updated portfolio with new holding
    """
    try:
        db = mongodb_connection.get_database()
        portfolios_collection = db['portfolios']

        # Validate symbol by getting current price
        current_price = await get_current_price(holding.symbol.upper())
        if current_price is None:
            raise HTTPException(status_code=400, detail=f"Invalid symbol: {holding.symbol}")

        # Parse purchase date
        try:
            purchase_date = datetime.strptime(holding.purchase_date, "%Y-%m-%d")
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid date format. Use YYYY-MM-DD")

        # Create holding document
        new_holding = {
            "symbol": holding.symbol.upper(),
            "shares": holding.shares,
            "purchase_price": holding.purchase_price,
            "purchase_date": purchase_date.isoformat(),
            "notes": holding.notes,
            "added_at": datetime.utcnow().isoformat()
        }

        # Find portfolio or create if doesn't exist
        portfolio = await portfolios_collection.find_one({"user_email": user_email})

        if not portfolio:
            # Create new portfolio
            portfolio = {
                "user_email": user_email,
                "holdings": [new_holding],
                "created_at": datetime.utcnow().isoformat(),
                "updated_at": datetime.utcnow().isoformat()
            }
            await portfolios_collection.insert_one(portfolio)
            logger.info(f"Created new portfolio for {user_email}")
        else:
            # Add holding to existing portfolio
            await portfolios_collection.update_one(
                {"user_email": user_email},
                {
                    "$push": {"holdings": new_holding},
                    "$set": {"updated_at": datetime.utcnow().isoformat()}
                }
            )
            logger.info(f"Added {holding.symbol} to portfolio for {user_email}")

        # Calculate updated portfolio metrics
        updated_portfolio = await portfolios_collection.find_one({"user_email": user_email}, {"_id": 0})

        # Calculate current values for all holdings
        holdings_with_metrics = []
        total_value = 0
        total_cost = 0

        for h in updated_portfolio.get('holdings', []):
            price = await get_current_price(h['symbol'])
            if price:
                holding_metrics = await calculate_holding_metrics(h, price)
                holdings_with_metrics.append(holding_metrics)
                total_value += holding_metrics['current_value']
                total_cost += holding_metrics['cost_basis']

        # Calculate allocation percentage for each holding
        for holding_metrics in holdings_with_metrics:
            allocation = (holding_metrics['current_value'] / total_value * 100) if total_value > 0 else 0
            holding_metrics['allocation'] = round(allocation, 2)

        total_return = total_value - total_cost
        total_return_percent = (total_return / total_cost * 100) if total_cost > 0 else 0

        return {
            "status": "success",
            "message": f"Added {holding.shares} shares of {holding.symbol}",
            "data": {
                "holdings": holdings_with_metrics,
                "total_value": round(total_value, 2),
                "total_cost": round(total_cost, 2),
                "total_return": round(total_return, 2),
                "total_return_percent": round(total_return_percent, 2)
            }
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error adding holding for {user_email}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to add holding: {str(e)}")


@router.put("/{user_email}/holdings/{symbol}")
async def update_holding(user_email: str, symbol: str, updates: HoldingUpdate):
    """
    Update an existing holding in user's portfolio.

    Args:
        user_email: User's email address
        symbol: Stock symbol to update
        updates: Fields to update (shares, purchase_price, purchase_date, notes)

    Returns:
        Updated holding details
    """
    try:
        db = mongodb_connection.get_database()
        portfolios_collection = db['portfolios']

        portfolio = await portfolios_collection.find_one({"user_email": user_email})
        if not portfolio:
            raise HTTPException(status_code=404, detail=f"Portfolio not found for {user_email}")

        # Find holding index
        holdings = portfolio.get('holdings', [])
        holding_index = next((i for i, h in enumerate(holdings) if h['symbol'].upper() == symbol.upper()), None)

        if holding_index is None:
            raise HTTPException(status_code=404, detail=f"Holding {symbol} not found in portfolio")

        # Build update dict
        update_fields = {}
        if updates.shares is not None:
            update_fields[f"holdings.{holding_index}.shares"] = updates.shares
        if updates.purchase_price is not None:
            update_fields[f"holdings.{holding_index}.purchase_price"] = updates.purchase_price
        if updates.purchase_date is not None:
            try:
                purchase_date = datetime.strptime(updates.purchase_date, "%Y-%m-%d")
                update_fields[f"holdings.{holding_index}.purchase_date"] = purchase_date.isoformat()
            except ValueError:
                raise HTTPException(status_code=400, detail="Invalid date format. Use YYYY-MM-DD")
        if updates.notes is not None:
            update_fields[f"holdings.{holding_index}.notes"] = updates.notes

        update_fields["updated_at"] = datetime.utcnow().isoformat()

        # Update holding
        await portfolios_collection.update_one(
            {"user_email": user_email},
            {"$set": update_fields}
        )

        # Get updated holding with current price
        updated_portfolio = await portfolios_collection.find_one({"user_email": user_email}, {"_id": 0})
        updated_holding = updated_portfolio['holdings'][holding_index]

        current_price = await get_current_price(symbol.upper())
        if current_price:
            holding_with_metrics = await calculate_holding_metrics(updated_holding, current_price)
        else:
            holding_with_metrics = updated_holding

        logger.info(f"Updated {symbol} holding for {user_email}")

        return {
            "status": "success",
            "message": f"Updated {symbol} holding",
            "data": holding_with_metrics
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating holding {symbol} for {user_email}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to update holding: {str(e)}")


@router.delete("/{user_email}/holdings/{symbol}")
async def delete_holding(user_email: str, symbol: str):
    """
    Remove a holding from user's portfolio.

    Args:
        user_email: User's email address
        symbol: Stock symbol to remove

    Returns:
        Confirmation message
    """
    try:
        db = mongodb_connection.get_database()
        portfolios_collection = db['portfolios']

        portfolio = await portfolios_collection.find_one({"user_email": user_email})
        if not portfolio:
            raise HTTPException(status_code=404, detail=f"Portfolio not found for {user_email}")

        # Remove holding
        result = await portfolios_collection.update_one(
            {"user_email": user_email},
            {
                "$pull": {"holdings": {"symbol": symbol.upper()}},
                "$set": {"updated_at": datetime.utcnow().isoformat()}
            }
        )

        if result.modified_count == 0:
            raise HTTPException(status_code=404, detail=f"Holding {symbol} not found in portfolio")

        logger.info(f"Deleted {symbol} holding for {user_email}")

        return {
            "status": "success",
            "message": f"Removed {symbol} from portfolio"
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting holding {symbol} for {user_email}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to delete holding: {str(e)}")
