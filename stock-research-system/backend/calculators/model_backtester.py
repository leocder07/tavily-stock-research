"""
Model Backtesting Framework
Out-of-sample testing, walk-forward analysis, and performance metrics
"""

import numpy as np
from typing import Dict, Any, List, Tuple, Optional
from datetime import datetime, timedelta
from dataclasses import dataclass
import logging

logger = logging.getLogger(__name__)


@dataclass
class BacktestResult:
    """Container for backtest results"""
    total_predictions: int
    correct_predictions: int
    accuracy: float
    sharpe_ratio: float
    sortino_ratio: float
    max_drawdown: float
    win_rate: float
    avg_return: float
    total_return: float
    predictions: List[Dict]
    performance_by_period: Dict[str, Any]
    validation_passed: bool = True
    validation_errors: List[str] = None

    def __post_init__(self):
        if self.validation_errors is None:
            self.validation_errors = []


@dataclass
class WalkForwardResult:
    """Walk-forward analysis result"""
    window_start: datetime
    window_end: datetime
    train_accuracy: float
    test_accuracy: float
    predictions: int
    returns: float


class ModelBacktester:
    """
    Backtesting framework for predictive models

    Features:
    - Out-of-sample testing (train/test split)
    - Walk-forward analysis (rolling windows)
    - Performance metrics (Sharpe, Sortino, max DD)
    - Win rate and return analysis
    """

    def __init__(self):
        self.name = "ModelBacktester"
        self.transaction_cost = 0.001  # 0.1% per trade
        self.slippage = 0.0005  # 0.05% slippage on market orders

    def backtest_predictions(
        self,
        predictions: List[Dict],
        actual_prices: List[float],
        timestamps: List[datetime],
        initial_capital: float = 100000
    ) -> BacktestResult:
        """
        Backtest model predictions against actual outcomes

        Args:
            predictions: List of {prediction, confidence, timestamp}
            actual_prices: Actual price movements
            timestamps: Datetime for each prediction
            initial_capital: Starting portfolio value

        Returns:
            BacktestResult with comprehensive metrics
        """
        logger.info(f"[{self.name}] Starting backtest with {len(predictions)} predictions")

        if not predictions or not actual_prices:
            return self._empty_result()

        # Align predictions with actual outcomes
        results = []
        portfolio_values = [initial_capital]
        returns = []

        for i, pred in enumerate(predictions):
            if i >= len(actual_prices) - 1:
                break

            predicted_direction = pred.get('direction', 'neutral')
            predicted_return = pred.get('predicted_return', 0)
            confidence = pred.get('confidence', 0.5)

            # Actual return (next day)
            current_price = actual_prices[i]
            next_price = actual_prices[i + 1]
            actual_return = (next_price - current_price) / current_price

            # Determine if prediction was correct
            correct = False
            if predicted_direction == 'up' and actual_return > 0:
                correct = True
            elif predicted_direction == 'down' and actual_return < 0:
                correct = True
            elif predicted_direction == 'neutral' and abs(actual_return) < 0.01:
                correct = True

            # Calculate portfolio impact (size position by confidence)
            position_size = confidence  # Use confidence as position sizing
            trade_return = 0

            if predicted_direction != 'neutral':
                # Apply actual return to position
                gross_return = actual_return * position_size

                # Reverse if predicted down
                if predicted_direction == 'down':
                    gross_return = -gross_return

                # Apply transaction costs and slippage
                # Transaction costs apply on entry and exit (2x)
                total_costs = (self.transaction_cost * 2) + self.slippage
                trade_return = gross_return - total_costs * position_size

                # Additional costs for shorting (borrow fees ~3% annualized = 0.012% daily)
                if predicted_direction == 'down':
                    short_cost = 0.00012 * position_size  # Daily borrow cost
                    trade_return -= short_cost

            portfolio_value = portfolio_values[-1] * (1 + trade_return)
            portfolio_values.append(portfolio_value)
            returns.append(trade_return)

            results.append({
                'timestamp': timestamps[i] if i < len(timestamps) else None,
                'predicted_direction': predicted_direction,
                'actual_return': actual_return,
                'correct': correct,
                'confidence': confidence,
                'trade_return': trade_return,
                'portfolio_value': portfolio_value
            })

        # Calculate metrics
        correct_count = sum(1 for r in results if r['correct'])
        accuracy = correct_count / len(results) if results else 0

        # Returns-based metrics
        returns_array = np.array(returns)
        avg_return = np.mean(returns_array) if len(returns_array) > 0 else 0
        std_return = np.std(returns_array) if len(returns_array) > 0 else 1

        # Sharpe Ratio (annualized)
        sharpe_ratio = (avg_return / std_return) * np.sqrt(252) if std_return > 0 else 0

        # Sortino Ratio (downside deviation)
        downside_returns = returns_array[returns_array < 0]
        downside_std = np.std(downside_returns) if len(downside_returns) > 0 else 1
        sortino_ratio = (avg_return / downside_std) * np.sqrt(252) if downside_std > 0 else 0

        # Maximum Drawdown
        portfolio_array = np.array(portfolio_values)
        running_max = np.maximum.accumulate(portfolio_array)
        drawdown = (portfolio_array - running_max) / running_max
        max_drawdown = np.min(drawdown) if len(drawdown) > 0 else 0

        # Win Rate
        winning_trades = sum(1 for r in returns if r > 0)
        win_rate = winning_trades / len(returns) if returns else 0

        # Total Return
        total_return = (portfolio_values[-1] - initial_capital) / initial_capital if portfolio_values else 0

        # VALIDATION: Check for impossible metric combinations
        validation_failed = False
        validation_errors = []

        # Rule 1: Unrealistic accuracy (> 70% is world-class, > 80% is suspicious)
        if accuracy > 0.70:
            validation_errors.append(f"SUSPICIOUS: {accuracy*100:.1f}% accuracy (>70% is rare in real markets)")
            validation_failed = True
            logger.warning(f"[{self.name}] Validation FAILED: Accuracy {accuracy*100:.1f}% exceeds realistic threshold")

        # Rule 2: Unrealistic Sharpe ratios (> 3 is world-class, > 4 is impossible in equities)
        if sharpe_ratio > 4.0:
            validation_errors.append(f"IMPOSSIBLE: Sharpe ratio {sharpe_ratio:.2f} > 4.0 (world's best funds: 2-3)")
            validation_failed = True
            logger.warning(f"[{self.name}] Validation FAILED: Sharpe ratio {sharpe_ratio:.2f} unrealistic")

        # Rule 3: High accuracy should correlate with reasonable win rate
        # Note: Accuracy (direction) and win rate (profitable trades) differ due to costs
        # If accuracy > 65%, win rate should be > 40% (with costs, neutral signals)
        if accuracy > 0.65 and win_rate < 0.40:
            validation_errors.append(f"INCONSISTENT: {accuracy*100:.1f}% accuracy with {win_rate*100:.1f}% win rate")
            validation_failed = True
            logger.warning(f"[{self.name}] Validation failed: High accuracy ({accuracy*100:.1f}%) with very low win rate ({win_rate*100:.1f}%)")

        # Rule 4: Max drawdown should never be exactly 0 (always some volatility)
        if max_drawdown == 0.0 and len(portfolio_values) > 10:
            validation_errors.append(f"IMPOSSIBLE: Max drawdown exactly 0% over {len(portfolio_values)} periods")
            validation_failed = True
            logger.warning(f"[{self.name}] Validation FAILED: Max drawdown is exactly 0%")

        # Rule 5: Unrealistic win rate (> 65% is world-class)
        if win_rate > 0.65:
            validation_errors.append(f"SUSPICIOUS: {win_rate*100:.1f}% win rate (>65% is rare in real markets)")
            validation_failed = True
            logger.warning(f"[{self.name}] Validation FAILED: Win rate {win_rate*100:.1f}% exceeds realistic threshold")

        # Rule 6: Sharpe and Sortino must be correlated (both measure risk-adjusted returns)
        # If Sharpe > 2, Sortino should be >= 50% of Sharpe and <= 200% of Sharpe
        if sharpe_ratio > 2.0 and (sortino_ratio < sharpe_ratio * 0.5 or sortino_ratio > sharpe_ratio * 2.0):
            validation_errors.append(f"INCONSISTENT: Sharpe {sharpe_ratio:.2f} with Sortino {sortino_ratio:.2f}")
            validation_failed = True
            logger.warning(f"[{self.name}] Validation failed: Sharpe ({sharpe_ratio:.2f}) and Sortino ({sortino_ratio:.2f}) misaligned")

        # Rule 7: Total return should be reasonable for the period
        # If more than 100% return with less than 100 trades, likely unrealistic
        if total_return > 1.0 and len(results) < 100:
            validation_errors.append(f"SUSPICIOUS: {total_return*100:.1f}% return in {len(results)} trades")
            validation_failed = True
            logger.warning(f"[{self.name}] Validation FAILED: Return {total_return*100:.1f}% too high for {len(results)} trades")

        # Performance by period
        performance_by_period = self._calculate_period_performance(results, timestamps)

        if validation_failed:
            logger.error(f"[{self.name}] ⚠️  BACKTEST VALIDATION FAILED ⚠️")
            logger.error(f"[{self.name}] Errors: {', '.join(validation_errors)}")
            logger.error(f"[{self.name}] These results indicate look-ahead bias, overfitting, or unrealistic assumptions")
        else:
            logger.info(f"[{self.name}] ✅ Backtest validation passed")
            logger.info(f"[{self.name}] Backtest complete: {accuracy*100:.1f}% accuracy, {sharpe_ratio:.2f} Sharpe")

        return BacktestResult(
            total_predictions=len(results),
            correct_predictions=correct_count,
            accuracy=accuracy,
            sharpe_ratio=sharpe_ratio,
            sortino_ratio=sortino_ratio,
            max_drawdown=max_drawdown,
            win_rate=win_rate,
            avg_return=avg_return,
            total_return=total_return,
            predictions=results,
            performance_by_period=performance_by_period,
            validation_passed=not validation_failed,
            validation_errors=validation_errors
        )

    def walk_forward_analysis(
        self,
        data: List[Dict],
        window_size: int = 60,
        test_size: int = 20,
        step_size: int = 20
    ) -> List[WalkForwardResult]:
        """
        Walk-forward analysis with rolling windows

        Args:
            data: Historical data with prices and predictions
            window_size: Training window size (days)
            test_size: Test window size (days)
            step_size: Step size between windows

        Returns:
            List of WalkForwardResult for each window
        """
        logger.info(f"[{self.name}] Starting walk-forward analysis")

        if len(data) < window_size + test_size:
            logger.warning(f"[{self.name}] Insufficient data for walk-forward analysis")
            return []

        results = []

        for start_idx in range(0, len(data) - window_size - test_size, step_size):
            # Define windows
            train_end = start_idx + window_size
            test_end = train_end + test_size

            train_data = data[start_idx:train_end]
            test_data = data[train_end:test_end]

            # Calculate accuracy on training set
            train_correct = sum(1 for d in train_data if d.get('correct', False))
            train_accuracy = train_correct / len(train_data) if train_data else 0

            # Calculate accuracy on test set
            test_correct = sum(1 for d in test_data if d.get('correct', False))
            test_accuracy = test_correct / len(test_data) if test_data else 0

            # Calculate returns on test set
            test_returns = sum(d.get('trade_return', 0) for d in test_data)

            results.append(WalkForwardResult(
                window_start=train_data[0].get('timestamp') if train_data else datetime.now(),
                window_end=test_data[-1].get('timestamp') if test_data else datetime.now(),
                train_accuracy=train_accuracy,
                test_accuracy=test_accuracy,
                predictions=len(test_data),
                returns=test_returns
            ))

        # Log summary
        if results:
            avg_test_accuracy = np.mean([r.test_accuracy for r in results])
            logger.info(f"[{self.name}] Walk-forward complete: {len(results)} windows, {avg_test_accuracy*100:.1f}% avg test accuracy")

        return results

    def out_of_sample_test(
        self,
        predictions: List[Dict],
        actual_prices: List[float],
        timestamps: List[datetime],
        train_ratio: float = 0.7
    ) -> Dict[str, BacktestResult]:
        """
        Out-of-sample testing with train/test split

        Args:
            predictions: Model predictions
            actual_prices: Actual outcomes
            timestamps: Timestamps
            train_ratio: Ratio of data for training (0.7 = 70% train, 30% test)

        Returns:
            Dict with 'train' and 'test' BacktestResults
        """
        logger.info(f"[{self.name}] Out-of-sample test with {train_ratio*100:.0f}% train split")

        split_idx = int(len(predictions) * train_ratio)

        # Train set
        train_predictions = predictions[:split_idx]
        train_prices = actual_prices[:split_idx]
        train_timestamps = timestamps[:split_idx]

        # Test set
        test_predictions = predictions[split_idx:]
        test_prices = actual_prices[split_idx:]
        test_timestamps = timestamps[split_idx:]

        # Backtest both
        train_result = self.backtest_predictions(
            train_predictions, train_prices, train_timestamps
        )

        test_result = self.backtest_predictions(
            test_predictions, test_prices, test_timestamps
        )

        logger.info(
            f"[{self.name}] Train accuracy: {train_result.accuracy*100:.1f}%, "
            f"Test accuracy: {test_result.accuracy*100:.1f}%"
        )

        # Check for overfitting
        overfitting_gap = train_result.accuracy - test_result.accuracy
        if overfitting_gap > 0.15:
            logger.warning(f"[{self.name}] Possible overfitting detected! Gap: {overfitting_gap*100:.1f}%")

        return {
            'train': train_result,
            'test': test_result,
            'overfitting_gap': overfitting_gap
        }

    def calculate_prediction_confidence_calibration(
        self,
        predictions: List[Dict]
    ) -> Dict[str, Any]:
        """
        Analyze if confidence scores are well-calibrated
        (e.g., 70% confidence predictions should be correct 70% of the time)

        Args:
            predictions: List of predictions with confidence and correctness

        Returns:
            Calibration analysis
        """
        confidence_buckets = {
            '0-20%': [],
            '20-40%': [],
            '40-60%': [],
            '60-80%': [],
            '80-100%': []
        }

        for pred in predictions:
            confidence = pred.get('confidence', 0.5)
            correct = pred.get('correct', False)

            if confidence < 0.2:
                confidence_buckets['0-20%'].append(correct)
            elif confidence < 0.4:
                confidence_buckets['20-40%'].append(correct)
            elif confidence < 0.6:
                confidence_buckets['40-60%'].append(correct)
            elif confidence < 0.8:
                confidence_buckets['60-80%'].append(correct)
            else:
                confidence_buckets['80-100%'].append(correct)

        calibration = {}
        for bucket, results in confidence_buckets.items():
            if results:
                actual_accuracy = sum(results) / len(results)
                calibration[bucket] = {
                    'predictions': len(results),
                    'actual_accuracy': actual_accuracy,
                    'expected_accuracy': self._bucket_midpoint(bucket)
                }

        return calibration

    def _calculate_period_performance(
        self,
        results: List[Dict],
        timestamps: List[datetime]
    ) -> Dict[str, Any]:
        """Calculate performance by time period (daily, weekly, monthly)"""

        if not results or not timestamps:
            return {}

        # Group by month
        monthly_performance = {}
        for i, result in enumerate(results):
            if i >= len(timestamps):
                continue

            month_key = timestamps[i].strftime('%Y-%m')
            if month_key not in monthly_performance:
                monthly_performance[month_key] = {
                    'correct': 0,
                    'total': 0,
                    'returns': []
                }

            monthly_performance[month_key]['total'] += 1
            if result['correct']:
                monthly_performance[month_key]['correct'] += 1
            monthly_performance[month_key]['returns'].append(result['trade_return'])

        # Calculate monthly stats
        for month in monthly_performance:
            data = monthly_performance[month]
            data['accuracy'] = data['correct'] / data['total'] if data['total'] > 0 else 0
            data['avg_return'] = np.mean(data['returns']) if data['returns'] else 0
            data['total_return'] = sum(data['returns'])

        return {
            'monthly': monthly_performance,
            'best_month': max(monthly_performance.items(), key=lambda x: x[1]['accuracy'])[0] if monthly_performance else None,
            'worst_month': min(monthly_performance.items(), key=lambda x: x[1]['accuracy'])[0] if monthly_performance else None
        }

    def _bucket_midpoint(self, bucket: str) -> float:
        """Get midpoint of confidence bucket"""
        midpoints = {
            '0-20%': 0.1,
            '20-40%': 0.3,
            '40-60%': 0.5,
            '60-80%': 0.7,
            '80-100%': 0.9
        }
        return midpoints.get(bucket, 0.5)

    def _empty_result(self) -> BacktestResult:
        """Return empty backtest result"""
        return BacktestResult(
            total_predictions=0,
            correct_predictions=0,
            accuracy=0,
            sharpe_ratio=0,
            sortino_ratio=0,
            max_drawdown=0,
            win_rate=0,
            avg_return=0,
            total_return=0,
            predictions=[],
            performance_by_period={}
        )

    def generate_backtest_report(
        self,
        backtest_result: BacktestResult,
        walk_forward_results: Optional[List[WalkForwardResult]] = None
    ) -> Dict[str, Any]:
        """
        Generate comprehensive backtest report

        Args:
            backtest_result: Main backtest result
            walk_forward_results: Optional walk-forward results

        Returns:
            Formatted report dict
        """
        report = {
            'summary': {
                'total_predictions': backtest_result.total_predictions,
                'accuracy': f"{backtest_result.accuracy * 100:.1f}%",
                'win_rate': f"{backtest_result.win_rate * 100:.1f}%",
                'sharpe_ratio': f"{backtest_result.sharpe_ratio:.2f}",
                'sortino_ratio': f"{backtest_result.sortino_ratio:.2f}",
                'max_drawdown': f"{backtest_result.max_drawdown * 100:.1f}%",
                'total_return': f"{backtest_result.total_return * 100:.1f}%",
                'avg_return_per_trade': f"{backtest_result.avg_return * 100:.2f}%"
            },
            'performance_grade': self._calculate_grade(backtest_result),
            'period_performance': backtest_result.performance_by_period
        }

        if walk_forward_results:
            report['walk_forward'] = {
                'windows_tested': len(walk_forward_results),
                'avg_test_accuracy': f"{np.mean([r.test_accuracy for r in walk_forward_results]) * 100:.1f}%",
                'consistency': self._calculate_consistency(walk_forward_results)
            }

        return report

    def _calculate_grade(self, result: BacktestResult) -> str:
        """Calculate performance grade A-F"""
        score = 0

        # Accuracy (40 points)
        if result.accuracy >= 0.65:
            score += 40
        elif result.accuracy >= 0.55:
            score += 30
        elif result.accuracy >= 0.50:
            score += 20
        else:
            score += 10

        # Sharpe Ratio (30 points)
        if result.sharpe_ratio >= 2.0:
            score += 30
        elif result.sharpe_ratio >= 1.0:
            score += 20
        elif result.sharpe_ratio >= 0.5:
            score += 10

        # Max Drawdown (20 points)
        if abs(result.max_drawdown) < 0.10:
            score += 20
        elif abs(result.max_drawdown) < 0.20:
            score += 10

        # Total Return (10 points)
        if result.total_return > 0.20:
            score += 10
        elif result.total_return > 0:
            score += 5

        # Grade mapping
        if score >= 85:
            return 'A'
        elif score >= 70:
            return 'B'
        elif score >= 55:
            return 'C'
        elif score >= 40:
            return 'D'
        else:
            return 'F'

    def _calculate_consistency(self, walk_forward_results: List[WalkForwardResult]) -> str:
        """Calculate model consistency across windows"""
        test_accuracies = [r.test_accuracy for r in walk_forward_results]
        std_accuracy = np.std(test_accuracies)

        if std_accuracy < 0.05:
            return 'Very High'
        elif std_accuracy < 0.10:
            return 'High'
        elif std_accuracy < 0.15:
            return 'Moderate'
        else:
            return 'Low'
