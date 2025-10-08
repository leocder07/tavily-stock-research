"""
Risk Analysis Calculator
Quantitative risk models - VaR, CVaR, Monte Carlo, Portfolio optimization
Jim Simons & Ray Dalio methodologies
"""

from typing import List, Dict, Tuple, Optional
import numpy as np
import random
from datetime import datetime
import math


class RiskCalculator:
    """Calculate risk metrics and portfolio optimization"""

    def calculate_var(self,
                     returns: List[float],
                     confidence_level: float = 0.95,
                     portfolio_value: float = 100000) -> Dict:
        """
        Value at Risk (VaR)
        Maximum expected loss at given confidence level
        """
        if not returns:
            return {'var': None, 'error': 'No returns data'}

        sorted_returns = sorted(returns)
        index = int((1 - confidence_level) * len(sorted_returns))

        var_return = sorted_returns[index]
        var_amount = abs(var_return * portfolio_value)

        return {
            'var': round(var_amount, 2),
            'var_percent': round(var_return * 100, 2),
            'confidence_level': confidence_level,
            'interpretation': f'${var_amount:,.2f} maximum loss expected at {confidence_level*100}% confidence'
        }

    def calculate_cvar(self,
                      returns: List[float],
                      confidence_level: float = 0.95,
                      portfolio_value: float = 100000) -> Dict:
        """
        Conditional Value at Risk (CVaR) / Expected Shortfall
        Average loss in worst-case scenarios
        """
        if not returns:
            return {'cvar': None, 'error': 'No returns data'}

        sorted_returns = sorted(returns)
        index = int((1 - confidence_level) * len(sorted_returns))

        # Average of worst returns
        tail_returns = sorted_returns[:index] if index > 0 else [sorted_returns[0]]
        avg_tail_return = sum(tail_returns) / len(tail_returns)

        cvar_amount = abs(avg_tail_return * portfolio_value)

        return {
            'cvar': round(cvar_amount, 2),
            'cvar_percent': round(avg_tail_return * 100, 2),
            'var_percent': round(sorted_returns[index] * 100, 2),
            'confidence_level': confidence_level,
            'interpretation': f'${cvar_amount:,.2f} average loss in worst {(1-confidence_level)*100}% scenarios'
        }

    def calculate_sharpe_ratio(self,
                               returns: List[float],
                               risk_free_rate: float = 0.02) -> float:
        """
        Sharpe Ratio = (Expected Return - Risk-Free Rate) / Standard Deviation
        Risk-adjusted return metric
        """
        if not returns or len(returns) < 2:
            return None

        avg_return = sum(returns) / len(returns)
        std_dev = self._calculate_std_dev(returns)

        if std_dev == 0:
            return None

        annualized_return = avg_return * 252  # Trading days
        annualized_std = std_dev * math.sqrt(252)

        sharpe = (annualized_return - risk_free_rate) / annualized_std

        return round(sharpe, 2)

    def calculate_sortino_ratio(self,
                                returns: List[float],
                                risk_free_rate: float = 0.02) -> float:
        """
        Sortino Ratio - Like Sharpe but only penalizes downside volatility
        """
        if not returns or len(returns) < 2:
            return None

        avg_return = sum(returns) / len(returns)

        # Downside deviation (only negative returns)
        downside_returns = [r for r in returns if r < 0]
        if not downside_returns:
            return None

        downside_dev = self._calculate_std_dev(downside_returns)

        if downside_dev == 0:
            return None

        annualized_return = avg_return * 252
        annualized_downside = downside_dev * math.sqrt(252)

        sortino = (annualized_return - risk_free_rate) / annualized_downside

        return round(sortino, 2)

    def calculate_max_drawdown(self, prices: List[float]) -> Dict:
        """
        Maximum Drawdown - largest peak-to-trough decline
        """
        if len(prices) < 2:
            return {'max_drawdown': None}

        peak = prices[0]
        peak_index = 0  # Initialize peak_index to avoid UnboundLocalError
        max_dd = 0
        max_dd_start = 0
        max_dd_end = 0

        for i, price in enumerate(prices):
            if price > peak:
                peak = price
                peak_index = i

            drawdown = (peak - price) / peak

            if drawdown > max_dd:
                max_dd = drawdown
                max_dd_start = peak_index
                max_dd_end = i

        return {
            'max_drawdown': round(max_dd * 100, 2),
            'drawdown_period': max_dd_end - max_dd_start,
            'interpretation': f'{max_dd*100:.2f}% largest decline from peak'
        }

    def calculate_beta(self,
                      stock_returns: List[float],
                      market_returns: List[float]) -> Optional[float]:
        """
        Beta - measure of volatility relative to market
        Beta > 1: More volatile than market
        Beta < 1: Less volatile than market
        """
        if len(stock_returns) != len(market_returns) or len(stock_returns) < 2:
            return None

        # Covariance
        stock_mean = sum(stock_returns) / len(stock_returns)
        market_mean = sum(market_returns) / len(market_returns)

        covariance = sum((stock_returns[i] - stock_mean) * (market_returns[i] - market_mean)
                        for i in range(len(stock_returns))) / (len(stock_returns) - 1)

        # Market variance
        market_variance = sum((r - market_mean) ** 2 for r in market_returns) / (len(market_returns) - 1)

        if market_variance == 0:
            return None

        beta = covariance / market_variance

        return round(beta, 2)

    def monte_carlo_simulation(self,
                               current_price: float,
                               expected_return: float,
                               volatility: float,
                               days: int = 252,
                               simulations: int = 10000) -> Dict:
        """
        Monte Carlo simulation for price projections
        """
        results = []

        for _ in range(simulations):
            prices = [current_price]
            for _ in range(days):
                random_return = random.gauss(expected_return / 252, volatility / math.sqrt(252))
                new_price = prices[-1] * (1 + random_return)
                prices.append(new_price)

            results.append(prices[-1])

        # Calculate statistics
        results.sort()
        percentile_5 = results[int(0.05 * len(results))]
        percentile_50 = results[int(0.50 * len(results))]
        percentile_95 = results[int(0.95 * len(results))]

        return {
            'current_price': current_price,
            'expected_price': round(percentile_50, 2),
            'pessimistic': round(percentile_5, 2),
            'optimistic': round(percentile_95, 2),
            'expected_return': round((percentile_50 - current_price) / current_price * 100, 2),
            'downside_risk': round((percentile_5 - current_price) / current_price * 100, 2),
            'upside_potential': round((percentile_95 - current_price) / current_price * 100, 2),
            'simulations': simulations,
            'days_ahead': days
        }

    def portfolio_optimization(self,
                              assets: List[Dict],
                              target_return: Optional[float] = None) -> Dict:
        """
        Modern Portfolio Theory - Efficient Frontier
        Optimize asset allocation for risk/return

        assets = [
            {'symbol': 'AAPL', 'expected_return': 0.15, 'volatility': 0.25, 'weight': 0.3},
            ...
        ]
        """
        if not assets:
            return {'error': 'No assets provided'}

        # Extract data
        returns = [a['expected_return'] for a in assets]
        volatilities = [a['volatility'] for a in assets]
        symbols = [a['symbol'] for a in assets]

        # Simple equal-weight if no target
        if target_return is None:
            weights = [1 / len(assets) for _ in assets]
        else:
            # Optimize for target return
            weights = self._optimize_weights(returns, volatilities, target_return)

        # Calculate portfolio metrics
        portfolio_return = sum(r * w for r, w in zip(returns, weights))
        portfolio_volatility = self._portfolio_volatility(weights, volatilities)

        sharpe = (portfolio_return - 0.02) / portfolio_volatility if portfolio_volatility > 0 else 0

        allocations = [
            {
                'symbol': symbols[i],
                'weight': round(weights[i] * 100, 2),
                'expected_contribution': round(returns[i] * weights[i] * 100, 2)
            }
            for i in range(len(assets))
        ]

        return {
            'allocations': allocations,
            'expected_return': round(portfolio_return * 100, 2),
            'expected_volatility': round(portfolio_volatility * 100, 2),
            'sharpe_ratio': round(sharpe, 2),
            'diversification_score': self._diversification_score(weights)
        }

    def correlation_analysis(self,
                            returns_a: List[float],
                            returns_b: List[float]) -> Dict:
        """
        Calculate correlation between two assets
        """
        if len(returns_a) != len(returns_b) or len(returns_a) < 2:
            return {'correlation': None}

        # Calculate means
        mean_a = sum(returns_a) / len(returns_a)
        mean_b = sum(returns_b) / len(returns_b)

        # Calculate correlation
        numerator = sum((returns_a[i] - mean_a) * (returns_b[i] - mean_b)
                       for i in range(len(returns_a)))

        std_a = self._calculate_std_dev(returns_a)
        std_b = self._calculate_std_dev(returns_b)

        if std_a == 0 or std_b == 0:
            return {'correlation': None}

        correlation = numerator / ((len(returns_a) - 1) * std_a * std_b)

        # Interpretation
        if correlation > 0.7:
            interpretation = 'Strong positive correlation - moves together'
        elif correlation > 0.3:
            interpretation = 'Moderate positive correlation'
        elif correlation < -0.7:
            interpretation = 'Strong negative correlation - hedge potential'
        elif correlation < -0.3:
            interpretation = 'Moderate negative correlation'
        else:
            interpretation = 'Weak correlation - good diversification'

        return {
            'correlation': round(correlation, 2),
            'interpretation': interpretation
        }

    def _calculate_std_dev(self, values: List[float]) -> float:
        """Calculate standard deviation"""
        if len(values) < 2:
            return 0

        mean = sum(values) / len(values)
        variance = sum((x - mean) ** 2 for x in values) / (len(values) - 1)
        return math.sqrt(variance)

    def _optimize_weights(self,
                         returns: List[float],
                         volatilities: List[float],
                         target_return: float) -> List[float]:
        """Simple optimization for target return"""
        # Simplified: weight by return/risk ratio
        ratios = [r / v if v > 0 else 0 for r, v in zip(returns, volatilities)]
        total_ratio = sum(ratios)

        if total_ratio == 0:
            return [1 / len(returns) for _ in returns]

        weights = [r / total_ratio for r in ratios]

        return weights

    def _portfolio_volatility(self, weights: List[float], volatilities: List[float]) -> float:
        """Calculate portfolio volatility (simplified)"""
        # Simplified: weighted average (ignoring correlations for now)
        return sum(w * v for w, v in zip(weights, volatilities))

    def _diversification_score(self, weights: List[float]) -> float:
        """Calculate diversification score (1-10)"""
        # Entropy-based diversification
        entropy = -sum(w * math.log(w) if w > 0 else 0 for w in weights)
        max_entropy = math.log(len(weights))

        score = (entropy / max_entropy) * 10 if max_entropy > 0 else 0

        return round(score, 2)

    def risk_parity_allocation(self, assets: List[Dict]) -> Dict:
        """
        Ray Dalio's Risk Parity Strategy
        Equal risk contribution from each asset
        """
        volatilities = [a['volatility'] for a in assets]
        symbols = [a['symbol'] for a in assets]

        # Weight inversely proportional to volatility
        inv_vols = [1 / v if v > 0 else 0 for v in volatilities]
        total = sum(inv_vols)

        weights = [iv / total if total > 0 else 1 / len(assets) for iv in inv_vols]

        allocations = [
            {
                'symbol': symbols[i],
                'weight': round(weights[i] * 100, 2),
                'volatility': round(volatilities[i] * 100, 2),
                'risk_contribution': round(weights[i] * volatilities[i] * 100, 2)
            }
            for i in range(len(assets))
        ]

        return {
            'strategy': 'Risk Parity',
            'allocations': allocations,
            'philosophy': 'Equal risk contribution from each asset class'
        }
