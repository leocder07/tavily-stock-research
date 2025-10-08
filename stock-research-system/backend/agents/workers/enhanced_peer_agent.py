"""
Enhanced Peer Comparison Agent
Combines quantitative metrics (yfinance) with qualitative insights (Tavily)
CRITICAL for institutional investors
"""

import logging
from typing import Dict, Any, List, Optional
from datetime import datetime
from calculators.peer_benchmark_calculator import PeerBenchmarkCalculator

logger = logging.getLogger(__name__)


class EnhancedPeerAgent:
    """
    Enhanced peer comparison with quantitative benchmarking

    Provides:
    - Valuation multiples comparison (P/E, PEG, EV/EBITDA)
    - Profitability comparison (margins, ROE, ROIC)
    - Growth comparison (revenue, earnings)
    - Market positioning and competitive analysis
    """

    def __init__(self, tavily_client=None):
        self.name = "EnhancedPeerAgent"
        self.benchmark_calc = PeerBenchmarkCalculator()
        self.tavily_client = tavily_client

    async def execute(self, symbol: str, context: Optional[Dict] = None) -> Dict[str, Any]:
        """
        Execute comprehensive peer analysis

        Args:
            symbol: Stock symbol to analyze
            context: Optional context (custom peers, etc.)

        Returns:
            Complete peer comparison analysis
        """

        try:
            logger.info(f"[{self.name}] Starting peer analysis for {symbol}")

            # Step 1: Get quantitative peer comparison
            peer_data = self.benchmark_calc.get_peer_comparison(symbol)

            if 'error' in peer_data:
                logger.error(f"[{self.name}] Benchmark calc error: {peer_data['error']}")
                return self._fallback_analysis(symbol)

            # Step 2: Get qualitative insights from Tavily (if available)
            qualitative_insights = []
            if self.tavily_client:
                qualitative_insights = await self._get_qualitative_insights(
                    symbol,
                    peer_data.get('peers', [])
                )

            # Step 3: Combine quantitative + qualitative
            analysis = self._synthesize_analysis(symbol, peer_data, qualitative_insights)

            logger.info(f"[{self.name}] Peer analysis complete for {symbol}")
            return analysis

        except Exception as e:
            logger.error(f"[{self.name}] Peer analysis failed: {e}")
            return self._fallback_analysis(symbol, error=str(e))

    async def _get_qualitative_insights(self, symbol: str, peers: List[str]) -> List[str]:
        """Get qualitative competitive insights from Tavily"""

        insights = []

        if not self.tavily_client:
            return insights

        try:
            # Search for competitive positioning
            query = f"{symbol} vs {' '.join(peers[:2])} competitive advantage market share analysis"
            response = await self.tavily_client.search(
                query=query,
                search_depth="advanced",
                max_results=3
            )

            results = response.get('results', [])

            for result in results:
                content = result.get('content', '')

                # Extract key competitive insights
                if 'market share' in content.lower():
                    insights.append(f"Market share: {content[:200]}")
                if 'competitive advantage' in content.lower():
                    insights.append(f"Advantage: {content[:200]}")
                if 'product' in content.lower() and 'innovation' in content.lower():
                    insights.append(f"Innovation: {content[:200]}")

        except Exception as e:
            logger.warning(f"[{self.name}] Tavily search failed: {e}")

        return insights[:5]  # Top 5 insights

    def _synthesize_analysis(
        self,
        symbol: str,
        peer_data: Dict,
        qualitative_insights: List[str]
    ) -> Dict[str, Any]:
        """Synthesize quantitative + qualitative analysis"""

        valuation_comp = peer_data.get('valuation_comparison', {})
        profitability_comp = peer_data.get('profitability_comparison', {})
        growth_comp = peer_data.get('growth_comparison', {})
        rankings = peer_data.get('rankings', {})
        insights = peer_data.get('insights', [])

        # Build comprehensive analysis
        analysis = {
            'agent': self.name,
            'symbol': symbol,
            'peers_analyzed': peer_data.get('peers', []),

            # Summary metrics
            'summary': {
                'overall_grade': rankings.get('overall_grade', 'C'),
                'composite_score': rankings.get('composite_score', 50),
                'valuation_score': rankings.get('valuation_score', 50),
                'profitability_rank': rankings.get('profitability_rank', 3),
                'growth_rank': rankings.get('growth_rank', 3)
            },

            # Detailed comparisons
            'valuation': self._format_valuation(valuation_comp),
            'profitability': self._format_profitability(profitability_comp),
            'growth': self._format_growth(growth_comp),
            'size': peer_data.get('size_comparison', {}),

            # Insights
            'quantitative_insights': insights,
            'qualitative_insights': qualitative_insights,

            # Recommendation
            'recommendation': self._generate_recommendation(
                symbol,
                rankings,
                valuation_comp,
                profitability_comp,
                growth_comp
            ),

            'timestamp': datetime.utcnow().isoformat()
        }

        return analysis

    def _format_valuation(self, valuation_comp: Dict) -> Dict[str, Any]:
        """Format valuation comparison for output"""

        pe_data = valuation_comp.get('pe_ratio', {})
        peg_data = valuation_comp.get('peg_ratio', {})
        pb_data = valuation_comp.get('price_to_book', {})

        return {
            'pe_ratio': {
                'value': pe_data.get('stock_value'),
                'peer_avg': pe_data.get('peer_average'),
                'premium_pct': pe_data.get('premium_to_avg_pct'),
                'percentile': pe_data.get('percentile')
            },
            'peg_ratio': {
                'value': peg_data.get('stock_value'),
                'peer_avg': peg_data.get('peer_average'),
                'premium_pct': peg_data.get('premium_to_avg_pct')
            },
            'price_to_book': {
                'value': pb_data.get('stock_value'),
                'peer_avg': pb_data.get('peer_average'),
                'premium_pct': pb_data.get('premium_to_avg_pct')
            },
            'summary': self._valuation_summary(pe_data, peg_data)
        }

    def _format_profitability(self, profitability_comp: Dict) -> Dict[str, Any]:
        """Format profitability comparison for output"""

        profit_margin = profitability_comp.get('profit_margin', {})
        roe = profitability_comp.get('roe', {})
        roic = profitability_comp.get('roic', {})

        return {
            'profit_margin': {
                'value': profit_margin.get('stock_value'),
                'peer_avg': profit_margin.get('peer_average'),
                'outperformance': profit_margin.get('outperformance'),
                'rank': profit_margin.get('rank')
            },
            'roe': {
                'value': roe.get('stock_value'),
                'peer_avg': roe.get('peer_average'),
                'outperformance': roe.get('outperformance'),
                'rank': roe.get('rank')
            },
            'roic': {
                'value': roic.get('stock_value'),
                'peer_avg': roic.get('peer_average'),
                'outperformance': roic.get('outperformance'),
                'rank': roic.get('rank')
            },
            'summary': self._profitability_summary(profit_margin, roe)
        }

    def _format_growth(self, growth_comp: Dict) -> Dict[str, Any]:
        """Format growth comparison for output"""

        revenue_growth = growth_comp.get('revenue_growth', {})
        earnings_growth = growth_comp.get('earnings_growth', {})

        return {
            'revenue_growth': {
                'value': revenue_growth.get('stock_value'),
                'peer_avg': revenue_growth.get('peer_average'),
                'growth_premium': revenue_growth.get('growth_premium'),
                'rank': revenue_growth.get('rank')
            },
            'earnings_growth': {
                'value': earnings_growth.get('stock_value'),
                'peer_avg': earnings_growth.get('peer_average'),
                'growth_premium': earnings_growth.get('growth_premium'),
                'rank': earnings_growth.get('rank')
            },
            'summary': self._growth_summary(revenue_growth, earnings_growth)
        }

    def _valuation_summary(self, pe_data: Dict, peg_data: Dict) -> str:
        """Generate valuation summary"""

        pe_premium = pe_data.get('premium_to_avg_pct', 0)
        peg_premium = peg_data.get('premium_to_avg_pct', 0)

        if pe_premium > 20:
            valuation = "expensive vs peers"
        elif pe_premium < -20:
            valuation = "attractive discount vs peers"
        else:
            valuation = "in-line with peers"

        if peg_premium < -20:
            growth_adj = ", but justified by growth"
        elif peg_premium > 20:
            growth_adj = ", not justified by growth"
        else:
            growth_adj = ""

        return f"Valuation is {valuation}{growth_adj}"

    def _profitability_summary(self, margin_data: Dict, roe_data: Dict) -> str:
        """Generate profitability summary"""

        margin_rank = margin_data.get('rank', 3)
        roe_rank = roe_data.get('rank', 3)

        if margin_rank == 1 and roe_rank == 1:
            return "Superior profitability vs all peers"
        elif margin_rank <= 2 or roe_rank <= 2:
            return "Above-average profitability vs peers"
        elif margin_rank >= 4 or roe_rank >= 4:
            return "Below-average profitability vs peers"
        else:
            return "Average profitability vs peers"

    def _growth_summary(self, revenue_data: Dict, earnings_data: Dict) -> str:
        """Generate growth summary"""

        rev_premium = revenue_data.get('growth_premium', 0)
        earn_premium = earnings_data.get('growth_premium', 0)

        if rev_premium > 5 and earn_premium > 5:
            return "Faster growth than peers on revenue and earnings"
        elif rev_premium > 5:
            return "Faster revenue growth, but earnings lag"
        elif earn_premium > 5:
            return "Faster earnings growth, but revenue lag"
        elif rev_premium < -5 and earn_premium < -5:
            return "Slower growth than peers on both metrics"
        else:
            return "Growth in-line with peers"

    def _generate_recommendation(
        self,
        symbol: str,
        rankings: Dict,
        valuation: Dict,
        profitability: Dict,
        growth: Dict
    ) -> str:
        """Generate peer comparison recommendation"""

        composite_score = rankings.get('composite_score', 50)
        grade = rankings.get('overall_grade', 'C')

        pe_premium = valuation.get('pe_ratio', {}).get('premium_to_avg_pct', 0)
        roe_rank = rankings.get('profitability_rank', 3)
        growth_rank = rankings.get('growth_rank', 3)

        if composite_score >= 80:
            rec = f"{symbol} ranks highly vs peers (Grade: {grade})"
            if pe_premium > 15:
                rec += f", but valuation at {pe_premium:.0f}% premium limits upside"
            else:
                rec += f", valuation reasonable for quality"

        elif composite_score >= 60:
            rec = f"{symbol} is average vs peers (Grade: {grade})"
            if pe_premium < -10:
                rec += f", trading at {abs(pe_premium):.0f}% discount may offer value"
            else:
                rec += f", no clear competitive advantage"

        else:
            rec = f"{symbol} underperforms peers (Grade: {grade})"
            if pe_premium < -20:
                rec += f", but {abs(pe_premium):.0f}% discount may be warranted given weaker fundamentals"
            else:
                rec += f", valuation not compelling given competitive position"

        return rec

    def _fallback_analysis(self, symbol: str, error: str = None) -> Dict[str, Any]:
        """Fallback analysis if full comparison fails"""

        return {
            'agent': self.name,
            'symbol': symbol,
            'error': error or 'Peer comparison unavailable',
            'summary': {
                'overall_grade': 'N/A',
                'message': 'Insufficient peer data for comparison'
            },
            'timestamp': datetime.utcnow().isoformat()
        }
