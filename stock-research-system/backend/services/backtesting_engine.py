"""
Backtesting Engine (Phase 4)
Test AI recommendations against historical data to validate strategy effectiveness
"""

import logging
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
from dataclasses import dataclass
import pandas as pd
import numpy as np
import yfinance as yf

logger = logging.getLogger(__name__)


@dataclass
class BacktestResult:
    """Backtest performance results"""
    total_return: float
    annual_return: float
    sharpe_ratio: float
    max_drawdown: float
    win_rate: float
    total_trades: int
    profitable_trades: int
    avg_profit: float
    avg_loss: float
    profit_factor: float


class BacktestingEngine:
    """
    Backtest AI trading strategies against historical data
    Validates recommendation accuracy and risk-adjusted returns
    """

    def __init__(self):
        self.results_cache = {}

    async def backtest_strategy(
        self,
        symbol: str,
        start_date: datetime,
        end_date: datetime,
        initial_capital: float = 100000,
        strategy_params: Dict[str, Any] = None
    ) -> BacktestResult:
        """
        Run backtest for a trading strategy

        Args:
            symbol: Stock symbol
            start_date: Backtest start date
            end_date: Backtest end date
            initial_capital: Starting capital
            strategy_params: Strategy parameters (confidence threshold, etc.)
        """
        logger.info(f"[Backtest] Running backtest for {symbol} from {start_date} to {end_date}")

        # Download historical data
        data = await self._get_historical_data(symbol, start_date, end_date)
        if data is None or data.empty:
            logger.error(f"[Backtest] No data available for {symbol}")
            return None

        # Apply strategy
        signals = await self._generate_signals(data, strategy_params or {})

        # Execute trades
        trades = await self._execute_backtest_trades(data, signals, initial_capital)

        # Calculate metrics
        result = await self._calculate_metrics(trades, initial_capital)

        return result

    async def _get_historical_data(
        self,
        symbol: str,
        start_date: datetime,
        end_date: datetime
    ) -> Optional[pd.DataFrame]:
        """Download historical price data"""
        try:
            ticker = yf.Ticker(symbol)
            data = ticker.history(start=start_date, end=end_date)

            if data.empty:
                return None

            # Add technical indicators
            data['SMA_20'] = data['Close'].rolling(window=20).mean()
            data['SMA_50'] = data['Close'].rolling(window=50).mean()
            data['RSI'] = self._calculate_rsi(data['Close'])
            data['Volatility'] = data['Close'].pct_change().rolling(window=20).std()

            return data

        except Exception as e:
            logger.error(f"[Backtest] Failed to get historical data: {e}")
            return None

    async def _generate_signals(
        self,
        data: pd.DataFrame,
        params: Dict[str, Any]
    ) -> pd.DataFrame:
        """
        Generate buy/sell signals based on strategy

        Default strategy:
        - BUY when SMA_20 crosses above SMA_50 and RSI < 70
        - SELL when SMA_20 crosses below SMA_50 or RSI > 80
        """
        signals = pd.DataFrame(index=data.index)
        signals['signal'] = 0

        confidence_threshold = params.get('confidence_threshold', 0.7)

        for i in range(1, len(data)):
            # Golden Cross (BUY signal)
            if (data['SMA_20'].iloc[i] > data['SMA_50'].iloc[i] and
                data['SMA_20'].iloc[i-1] <= data['SMA_50'].iloc[i-1] and
                data['RSI'].iloc[i] < 70):
                signals['signal'].iloc[i] = 1  # BUY

            # Death Cross (SELL signal)
            elif (data['SMA_20'].iloc[i] < data['SMA_50'].iloc[i] and
                  data['SMA_20'].iloc[i-1] >= data['SMA_50'].iloc[i-1]):
                signals['signal'].iloc[i] = -1  # SELL

            # Overbought (SELL signal)
            elif data['RSI'].iloc[i] > 80:
                signals['signal'].iloc[i] = -1  # SELL

        signals['price'] = data['Close']
        signals['position'] = signals['signal'].replace(to_replace=0, method='ffill')

        return signals

    async def _execute_backtest_trades(
        self,
        data: pd.DataFrame,
        signals: pd.DataFrame,
        initial_capital: float
    ) -> List[Dict[str, Any]]:
        """Execute trades based on signals"""
        trades = []
        cash = initial_capital
        position = 0
        position_price = 0

        for i in range(len(signals)):
            signal = signals['signal'].iloc[i]
            price = signals['price'].iloc[i]

            if signal == 1 and position == 0:  # BUY
                shares = int(cash / price)
                if shares > 0:
                    position = shares
                    position_price = price
                    cash -= shares * price

                    trades.append({
                        'date': signals.index[i],
                        'action': 'BUY',
                        'price': price,
                        'shares': shares,
                        'cash': cash,
                        'portfolio_value': cash + (position * price)
                    })

            elif signal == -1 and position > 0:  # SELL
                cash += position * price
                profit = (price - position_price) * position
                profit_pct = ((price - position_price) / position_price) * 100

                trades.append({
                    'date': signals.index[i],
                    'action': 'SELL',
                    'price': price,
                    'shares': position,
                    'profit': profit,
                    'profit_pct': profit_pct,
                    'cash': cash,
                    'portfolio_value': cash
                })

                position = 0
                position_price = 0

        # Close any open position at end
        if position > 0:
            final_price = signals['price'].iloc[-1]
            cash += position * final_price
            profit = (final_price - position_price) * position

            trades.append({
                'date': signals.index[-1],
                'action': 'SELL (final)',
                'price': final_price,
                'shares': position,
                'profit': profit,
                'cash': cash,
                'portfolio_value': cash
            })

        return trades

    async def _calculate_metrics(
        self,
        trades: List[Dict[str, Any]],
        initial_capital: float
    ) -> BacktestResult:
        """Calculate performance metrics"""
        if not trades:
            return BacktestResult(
                total_return=0, annual_return=0, sharpe_ratio=0,
                max_drawdown=0, win_rate=0, total_trades=0,
                profitable_trades=0, avg_profit=0, avg_loss=0, profit_factor=0
            )

        # Extract trades with profit/loss
        completed_trades = [t for t in trades if 'profit' in t]

        if not completed_trades:
            return BacktestResult(
                total_return=0, annual_return=0, sharpe_ratio=0,
                max_drawdown=0, win_rate=0, total_trades=0,
                profitable_trades=0, avg_profit=0, avg_loss=0, profit_factor=0
            )

        # Total return
        final_value = trades[-1]['portfolio_value']
        total_return = ((final_value - initial_capital) / initial_capital) * 100

        # Annualized return
        days = (trades[-1]['date'] - trades[0]['date']).days
        years = days / 365.25
        annual_return = ((final_value / initial_capital) ** (1 / max(years, 0.1)) - 1) * 100

        # Win rate
        profitable_trades = [t for t in completed_trades if t['profit'] > 0]
        win_rate = len(profitable_trades) / len(completed_trades) if completed_trades else 0

        # Average profit/loss
        profits = [t['profit'] for t in profitable_trades]
        losses = [abs(t['profit']) for t in completed_trades if t['profit'] < 0]

        avg_profit = np.mean(profits) if profits else 0
        avg_loss = np.mean(losses) if losses else 0

        # Profit factor
        total_profit = sum(profits) if profits else 0
        total_loss = sum(losses) if losses else 0.01  # Avoid division by zero
        profit_factor = total_profit / total_loss

        # Sharpe ratio (simplified)
        returns = [t['profit_pct'] for t in completed_trades]
        sharpe_ratio = (np.mean(returns) / np.std(returns)) * np.sqrt(252) if len(returns) > 1 else 0

        # Max drawdown
        portfolio_values = [t['portfolio_value'] for t in trades]
        max_drawdown = self._calculate_max_drawdown(portfolio_values)

        return BacktestResult(
            total_return=round(total_return, 2),
            annual_return=round(annual_return, 2),
            sharpe_ratio=round(sharpe_ratio, 2),
            max_drawdown=round(max_drawdown, 2),
            win_rate=round(win_rate, 3),
            total_trades=len(completed_trades),
            profitable_trades=len(profitable_trades),
            avg_profit=round(avg_profit, 2),
            avg_loss=round(avg_loss, 2),
            profit_factor=round(profit_factor, 2)
        )

    def _calculate_rsi(self, prices: pd.Series, period: int = 14) -> pd.Series:
        """Calculate Relative Strength Index"""
        delta = prices.diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()

        rs = gain / loss
        rsi = 100 - (100 / (1 + rs))

        return rsi

    def _calculate_max_drawdown(self, portfolio_values: List[float]) -> float:
        """Calculate maximum drawdown percentage"""
        peak = portfolio_values[0]
        max_dd = 0

        for value in portfolio_values:
            if value > peak:
                peak = value
            dd = ((peak - value) / peak) * 100
            if dd > max_dd:
                max_dd = dd

        return max_dd

    async def compare_strategies(
        self,
        symbol: str,
        strategies: List[Dict[str, Any]],
        start_date: datetime,
        end_date: datetime
    ) -> Dict[str, BacktestResult]:
        """Compare multiple strategies"""
        results = {}

        for strategy in strategies:
            name = strategy.get('name', 'Unnamed')
            params = strategy.get('params', {})

            result = await self.backtest_strategy(
                symbol, start_date, end_date,
                strategy_params=params
            )

            results[name] = result

        return results


# Global backtesting engine
backtesting_engine = None


def get_backtesting_engine():
    """Get or create backtesting engine instance"""
    global backtesting_engine
    if backtesting_engine is None:
        backtesting_engine = BacktestingEngine()
    return backtesting_engine
