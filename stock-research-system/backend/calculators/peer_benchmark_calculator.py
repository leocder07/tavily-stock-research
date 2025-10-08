"""
Peer Benchmarking Calculator
Compares company metrics against competitors and sector averages
CRITICAL for institutional investors to assess relative valuation
"""

import logging
from typing import Dict, Any, List, Optional
import yfinance as yf
from datetime import datetime

logger = logging.getLogger(__name__)


class PeerBenchmarkCalculator:
    """
    Calculates comprehensive peer benchmarking metrics

    Compares:
    - Valuation multiples (P/E, PEG, P/B, EV/EBITDA)
    - Profitability (margins, ROE, ROIC)
    - Growth rates (revenue, earnings)
    - Market position (market cap, market share)
    """

    def __init__(self):
        self.name = "PeerBenchmarkCalculator"

        # Industry peer mappings (can be expanded)
        self.peer_map = {
            'AAPL': ['MSFT', 'GOOGL', 'META', 'NVDA'],
            'MSFT': ['AAPL', 'GOOGL', 'META', 'ORCL'],
            'GOOGL': ['META', 'MSFT', 'AAPL', 'AMZN'],
            'META': ['GOOGL', 'SNAP', 'PINS', 'TWTR'],
            'TSLA': ['F', 'GM', 'RIVN', 'LCID'],
            'NVDA': ['AMD', 'INTC', 'QCOM', 'AVGO'],
            # Add more as needed
        }

    def get_peer_comparison(
        self,
        symbol: str,
        peer_symbols: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        Get comprehensive peer comparison

        Args:
            symbol: Primary stock symbol
            peer_symbols: Optional list of peers (auto-detected if None)

        Returns:
            Complete peer benchmarking analysis
        """

        # Get peers (provided or auto-detect)
        peers = peer_symbols or self.peer_map.get(symbol, [])

        if not peers:
            return {
                'error': f'No peers defined for {symbol}',
                'symbol': symbol
            }

        try:
            # Fetch data for all symbols
            stock_data = self._fetch_stock_metrics(symbol)
            peer_data = {}

            for peer in peers:
                try:
                    peer_data[peer] = self._fetch_stock_metrics(peer)
                except Exception as e:
                    logger.warning(f"Failed to fetch {peer}: {e}")
                    continue

            # Calculate comparisons
            valuation_comparison = self._compare_valuation(stock_data, peer_data)
            profitability_comparison = self._compare_profitability(stock_data, peer_data)
            growth_comparison = self._compare_growth(stock_data, peer_data)
            size_comparison = self._compare_size(stock_data, peer_data)

            # Calculate relative rankings
            rankings = self._calculate_rankings(
                symbol,
                stock_data,
                peer_data,
                valuation_comparison,
                profitability_comparison,
                growth_comparison
            )

            # Generate insights
            insights = self._generate_insights(
                symbol,
                stock_data,
                peer_data,
                valuation_comparison,
                profitability_comparison,
                growth_comparison
            )

            return {
                'symbol': symbol,
                'peers': list(peer_data.keys()),
                'stock_metrics': stock_data,
                'peer_metrics': peer_data,
                'valuation_comparison': valuation_comparison,
                'profitability_comparison': profitability_comparison,
                'growth_comparison': growth_comparison,
                'size_comparison': size_comparison,
                'rankings': rankings,
                'insights': insights,
                'timestamp': datetime.utcnow().isoformat()
            }

        except Exception as e:
            logger.error(f"[{self.name}] Peer comparison failed: {e}")
            return {
                'error': str(e),
                'symbol': symbol
            }

    def _fetch_stock_metrics(self, symbol: str) -> Dict[str, Any]:
        """Fetch key metrics for a stock"""

        ticker = yf.Ticker(symbol)
        info = ticker.info

        metrics = {
            'symbol': symbol,
            # Valuation metrics
            'pe_ratio': info.get('trailingPE'),
            'forward_pe': info.get('forwardPE'),
            'peg_ratio': info.get('pegRatio'),
            'price_to_book': info.get('priceToBook'),
            'ev_to_ebitda': info.get('enterpriseToEbitda'),
            'price_to_sales': info.get('priceToSalesTrailing12Months'),

            # Profitability metrics
            'profit_margin': info.get('profitMargins'),
            'operating_margin': info.get('operatingMargins'),
            'gross_margin': info.get('grossMargins'),
            'roe': info.get('returnOnEquity'),
            'roa': info.get('returnOnAssets'),
            'roic': info.get('returnOnCapital'),

            # Growth metrics
            'revenue_growth': info.get('revenueGrowth'),
            'earnings_growth': info.get('earningsGrowth'),
            'earnings_quarterly_growth': info.get('earningsQuarterlyGrowth'),

            # Size metrics
            'market_cap': info.get('marketCap'),
            'enterprise_value': info.get('enterpriseValue'),
            'revenue': info.get('totalRevenue'),

            # Other
            'beta': info.get('beta'),
            'dividend_yield': info.get('dividendYield'),
            'debt_to_equity': info.get('debtToEquity')
        }

        return metrics

    def _compare_valuation(self, stock: Dict, peers: Dict[str, Dict]) -> Dict[str, Any]:
        """Compare valuation multiples"""

        metrics = ['pe_ratio', 'forward_pe', 'peg_ratio', 'price_to_book', 'ev_to_ebitda', 'price_to_sales']
        comparison = {}

        for metric in metrics:
            stock_value = stock.get(metric)
            peer_values = [p.get(metric) for p in peers.values() if p.get(metric) is not None]

            if stock_value is not None and peer_values:
                peer_avg = sum(peer_values) / len(peer_values)
                peer_median = sorted(peer_values)[len(peer_values) // 2]
                peer_min = min(peer_values)
                peer_max = max(peer_values)

                # Calculate premium/discount
                premium_to_avg = ((stock_value - peer_avg) / peer_avg) * 100 if peer_avg > 0 else 0
                premium_to_median = ((stock_value - peer_median) / peer_median) * 100 if peer_median > 0 else 0

                comparison[metric] = {
                    'stock_value': round(stock_value, 2),
                    'peer_average': round(peer_avg, 2),
                    'peer_median': round(peer_median, 2),
                    'peer_range': [round(peer_min, 2), round(peer_max, 2)],
                    'premium_to_avg_pct': round(premium_to_avg, 1),
                    'premium_to_median_pct': round(premium_to_median, 1),
                    'percentile': self._calculate_percentile(stock_value, peer_values)
                }

        return comparison

    def _compare_profitability(self, stock: Dict, peers: Dict[str, Dict]) -> Dict[str, Any]:
        """Compare profitability metrics"""

        metrics = ['profit_margin', 'operating_margin', 'gross_margin', 'roe', 'roa', 'roic']
        comparison = {}

        for metric in metrics:
            stock_value = stock.get(metric)
            peer_values = [p.get(metric) for p in peers.values() if p.get(metric) is not None]

            if stock_value is not None and peer_values:
                peer_avg = sum(peer_values) / len(peer_values)
                peer_median = sorted(peer_values)[len(peer_values) // 2]

                # Convert to percentage if needed
                if metric in ['profit_margin', 'operating_margin', 'gross_margin', 'roe', 'roa', 'roic']:
                    stock_value = stock_value * 100
                    peer_avg = peer_avg * 100
                    peer_median = peer_median * 100

                outperformance = stock_value - peer_avg

                comparison[metric] = {
                    'stock_value': round(stock_value, 2),
                    'peer_average': round(peer_avg, 2),
                    'peer_median': round(peer_median, 2),
                    'outperformance': round(outperformance, 2),
                    'rank': self._calculate_rank(stock_value, peer_values, higher_is_better=True)
                }

        return comparison

    def _compare_growth(self, stock: Dict, peers: Dict[str, Dict]) -> Dict[str, Any]:
        """Compare growth metrics"""

        metrics = ['revenue_growth', 'earnings_growth', 'earnings_quarterly_growth']
        comparison = {}

        for metric in metrics:
            stock_value = stock.get(metric)
            peer_values = [p.get(metric) for p in peers.values() if p.get(metric) is not None]

            if stock_value is not None and peer_values:
                peer_avg = sum(peer_values) / len(peer_values)

                # Convert to percentage
                stock_value_pct = stock_value * 100
                peer_avg_pct = peer_avg * 100

                comparison[metric] = {
                    'stock_value': round(stock_value_pct, 2),
                    'peer_average': round(peer_avg_pct, 2),
                    'growth_premium': round(stock_value_pct - peer_avg_pct, 2),
                    'rank': self._calculate_rank(stock_value, peer_values, higher_is_better=True)
                }

        return comparison

    def _compare_size(self, stock: Dict, peers: Dict[str, Dict]) -> Dict[str, Any]:
        """Compare company size metrics"""

        market_cap = stock.get('market_cap', 0)
        revenue = stock.get('revenue', 0)

        peer_market_caps = [p.get('market_cap', 0) for p in peers.values()]
        peer_revenues = [p.get('revenue', 0) for p in peers.values()]

        total_market_cap = market_cap + sum(peer_market_caps)
        market_share_by_cap = (market_cap / total_market_cap * 100) if total_market_cap > 0 else 0

        return {
            'market_cap': market_cap,
            'market_cap_billions': round(market_cap / 1e9, 2),
            'revenue': revenue,
            'revenue_billions': round(revenue / 1e9, 2),
            'market_share_by_cap': round(market_share_by_cap, 1),
            'size_rank': self._calculate_rank(market_cap, peer_market_caps, higher_is_better=True)
        }

    def _calculate_percentile(self, value: float, peer_values: List[float]) -> int:
        """Calculate percentile rank (0-100)"""
        if not peer_values:
            return 50

        all_values = sorted(peer_values + [value])
        rank = all_values.index(value)
        percentile = int((rank / len(all_values)) * 100)
        return percentile

    def _calculate_rank(self, value: float, peer_values: List[float], higher_is_better: bool = True) -> int:
        """Calculate rank (1 = best)"""
        if not peer_values:
            return 1

        all_values = sorted(peer_values + [value], reverse=higher_is_better)
        return all_values.index(value) + 1

    def _calculate_rankings(
        self,
        symbol: str,
        stock: Dict,
        peers: Dict,
        valuation: Dict,
        profitability: Dict,
        growth: Dict
    ) -> Dict[str, Any]:
        """Calculate overall rankings"""

        # Valuation rank (lower P/E = better)
        pe_rank = valuation.get('pe_ratio', {}).get('percentile', 50)
        valuation_score = 100 - pe_rank  # Invert (lower P/E = higher score)

        # Profitability rank
        roe = profitability.get('roe', {})
        profitability_rank = roe.get('rank', 3)

        # Growth rank
        revenue_growth = growth.get('revenue_growth', {})
        growth_rank = revenue_growth.get('rank', 3)

        # Overall composite score (weighted)
        composite_score = (
            valuation_score * 0.3 +
            (100 - (profitability_rank * 20)) * 0.4 +
            (100 - (growth_rank * 20)) * 0.3
        )

        return {
            'valuation_score': round(valuation_score, 1),
            'profitability_rank': profitability_rank,
            'growth_rank': growth_rank,
            'composite_score': round(composite_score, 1),
            'overall_grade': self._score_to_grade(composite_score)
        }

    def _score_to_grade(self, score: float) -> str:
        """Convert score to letter grade"""
        if score >= 90:
            return 'A+'
        elif score >= 85:
            return 'A'
        elif score >= 80:
            return 'A-'
        elif score >= 75:
            return 'B+'
        elif score >= 70:
            return 'B'
        elif score >= 65:
            return 'B-'
        elif score >= 60:
            return 'C+'
        elif score >= 55:
            return 'C'
        else:
            return 'C-'

    def _generate_insights(
        self,
        symbol: str,
        stock: Dict,
        peers: Dict,
        valuation: Dict,
        profitability: Dict,
        growth: Dict
    ) -> List[str]:
        """Generate actionable insights from comparison"""

        insights = []

        # Valuation insights
        pe_data = valuation.get('pe_ratio', {})
        if pe_data:
            premium = pe_data.get('premium_to_avg_pct', 0)
            if premium > 20:
                insights.append(f"{symbol} trades at {premium:.0f}% premium to peers - expensive valuation")
            elif premium < -20:
                insights.append(f"{symbol} trades at {abs(premium):.0f}% discount to peers - potential value opportunity")
            else:
                insights.append(f"{symbol} valuation in-line with peers ({premium:+.0f}% vs avg)")

        # Profitability insights
        roe_data = profitability.get('roe', {})
        if roe_data:
            stock_roe = roe_data.get('stock_value', 0)
            peer_roe = roe_data.get('peer_average', 0)
            if stock_roe > peer_roe * 1.2:
                insights.append(f"Superior profitability: ROE {stock_roe:.1f}% vs peer avg {peer_roe:.1f}%")
            elif stock_roe < peer_roe * 0.8:
                insights.append(f"Weaker profitability: ROE {stock_roe:.1f}% vs peer avg {peer_roe:.1f}%")

        # Growth insights
        rev_growth_data = growth.get('revenue_growth', {})
        if rev_growth_data:
            stock_growth = rev_growth_data.get('stock_value', 0)
            peer_growth = rev_growth_data.get('peer_average', 0)
            if stock_growth > peer_growth + 5:
                insights.append(f"Faster growth: {stock_growth:.1f}% revenue growth vs {peer_growth:.1f}% peer avg")
            elif stock_growth < peer_growth - 5:
                insights.append(f"Slower growth: {stock_growth:.1f}% revenue growth vs {peer_growth:.1f}% peer avg")

        # Margin expansion/contraction
        op_margin_data = profitability.get('operating_margin', {})
        if op_margin_data:
            outperformance = op_margin_data.get('outperformance', 0)
            if outperformance > 5:
                insights.append(f"Margin advantage: Operating margin {outperformance:+.1f}pp vs peers")
            elif outperformance < -5:
                insights.append(f"Margin disadvantage: Operating margin {outperformance:.1f}pp vs peers")

        return insights
