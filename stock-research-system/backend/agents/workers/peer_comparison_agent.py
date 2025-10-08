"""Peer Comparison Agent - Compares stocks with industry peers using Tavily"""

from typing import Dict, Any, List
import logging
from datetime import datetime
from agents.base_agent import BaseFinancialAgent, AgentState

logger = logging.getLogger(__name__)


class PeerComparisonAgent(BaseFinancialAgent):
    """Agent for comparing stocks with industry peers"""

    def __init__(self, agent_id: str, agent_type: str, tavily_client=None):
        super().__init__(agent_id, agent_type, tavily_client)

    async def execute(self, context: Dict[str, Any]) -> AgentState:
        """Compare stocks with their industry peers

        Args:
            context: Contains 'stock_symbols' and 'markets'

        Returns:
            AgentState with peer comparison
        """
        try:
            symbols = context.get('stock_symbols', [])
            markets = context.get('markets', ['US'])

            if not symbols:
                raise ValueError("No stock symbols provided")

            logger.info(f"Comparing {symbols} with industry peers")

            comparison_data = {}

            for symbol in symbols:
                peer_analysis = await self._compare_with_peers(symbol, markets)
                comparison_data[symbol] = peer_analysis

            output_data = {
                'stocks': comparison_data,
                'relative_position': self._determine_relative_position(comparison_data),
                'competitive_advantages': self._identify_advantages(comparison_data),
                'competitive_risks': self._identify_competitive_risks(comparison_data),
                'timestamp': datetime.utcnow().isoformat()
            }

            self.state.output_data = output_data
            self.state.confidence_score = 0.7

            logger.info("Peer comparison complete")
            return self.state

        except Exception as e:
            logger.error(f"Peer comparison failed: {str(e)}")
            self.state.error_message = str(e)
            self.state.status = "FAILED"
            return self.state

    def _get_default_peers(self, symbol: str) -> List[str]:
        """Sector-based peer fallback mapping"""
        peer_map = {
            # Tech Giants
            'AAPL': ['MSFT', 'GOOGL', 'META', 'NVDA', 'AMZN'],
            'MSFT': ['AAPL', 'GOOGL', 'ORCL', 'IBM', 'ADBE'],
            'GOOGL': ['META', 'AAPL', 'MSFT', 'AMZN'],
            'META': ['GOOGL', 'SNAP', 'PINS', 'TWTR'],
            'AMZN': ['WMT', 'TGT', 'EBAY', 'SHOP'],

            # Semiconductors
            'NVDA': ['AMD', 'INTC', 'QCOM', 'AVGO', 'TSM'],
            'AMD': ['NVDA', 'INTC', 'QCOM', 'MU'],
            'INTC': ['AMD', 'NVDA', 'QCOM', 'TXN'],

            # Automotive
            'TSLA': ['GM', 'F', 'NIO', 'RIVN', 'LCID'],
            'GM': ['F', 'TSLA', 'STLA', 'TM'],
            'F': ['GM', 'TSLA', 'STLA', 'TM'],

            # Finance
            'JPM': ['BAC', 'WFC', 'C', 'GS', 'MS'],
            'BAC': ['JPM', 'WFC', 'C', 'USB'],

            # Retail
            'WMT': ['TGT', 'COST', 'AMZN', 'DG'],
            'TGT': ['WMT', 'COST', 'DG', 'KSS'],
        }
        return peer_map.get(symbol.upper(), [])

    async def _compare_with_peers(self, symbol: str, markets: List[str]) -> Dict:
        """Compare a stock with its peers"""

        # Search for peer comparison data
        query = f"{symbol} competitors peers industry comparison market share valuation"
        results = await self.search_tavily(query, search_depth="advanced", max_results=4)

        # Also search for industry performance
        industry_query = f"{symbol} sector industry performance leaders laggards"
        industry_results = await self.search_tavily(industry_query, search_depth="basic", max_results=2)

        comparison = {
            'identified_peers': [],
            'market_position': 'average',
            'valuation_vs_peers': 'inline',
            'growth_vs_peers': 'inline',
            'profitability_vs_peers': 'inline',
            'key_differentiators': [],
            'peer_metrics': {}
        }

        if results:
            self.state.citations.extend(self.extract_citations(results))
            # Extract peer information
            for result in results:
                content = result.get('content', '').lower()

                # Extract peer names (simplified)
                import re
                peer_pattern = r'competitors?:?\s*([\w\s,]+)'
                peer_match = re.search(peer_pattern, content)
                if peer_match:
                    peers = peer_match.group(1).split(',')
                    comparison['identified_peers'].extend([p.strip() for p in peers[:3]])
                
                # Determine market position
                if 'market leader' in content or 'leading' in content:
                    comparison['market_position'] = 'leader'
                elif 'laggard' in content or 'underperform' in content:
                    comparison['market_position'] = 'laggard'
                
                # Valuation comparison
                if 'undervalued' in content:
                    comparison['valuation_vs_peers'] = 'discount'
                elif 'overvalued' in content or 'premium' in content:
                    comparison['valuation_vs_peers'] = 'premium'
        
        if industry_results:
            self.state.citations.extend(self.extract_citations(industry_results))
        
        # Get additional peer comparison context
        peer_context_query = f"{symbol} peer comparison competitive analysis market share"
        peer_context = await self.get_search_context_tavily(peer_context_query)
        if peer_context:
            comparison['peer_data_available'] = True

        # Fallback: Use default sector-based peers if extraction failed
        if not comparison['identified_peers']:
            default_peers = self._get_default_peers(symbol)
            comparison['identified_peers'] = default_peers
            logger.info(f"Using fallback peers for {symbol}: {default_peers}")

        return comparison

    def _determine_relative_position(self, comparison_data: Dict) -> Dict:
        """Determine relative position in industry"""
        positions = {
            'overall': 'average',
            'by_metric': {}
        }
        
        leader_count = 0
        laggard_count = 0
        
        for symbol, data in comparison_data.items():
            if isinstance(data, dict):
                if data.get('market_position') == 'leader':
                    leader_count += 1
                elif data.get('market_position') == 'laggard':
                    laggard_count += 1
        
        if leader_count > laggard_count:
            positions['overall'] = 'strong'
        elif laggard_count > leader_count:
            positions['overall'] = 'weak'
        
        return positions

    def _identify_advantages(self, comparison_data: Dict) -> List[str]:
        """Identify competitive advantages"""
        advantages = []

        for symbol, data in comparison_data.items():
            if isinstance(data, dict):
                if data.get('market_position') == 'leader':
                    advantages.append(f"{symbol}: Market leadership position")
                if data.get('valuation_vs_peers') == 'discount':
                    advantages.append(f"{symbol}: Attractive valuation vs peers")
                if data.get('growth_vs_peers') == 'outperform':
                    advantages.append(f"{symbol}: Superior growth metrics")

                # Generic advantages based on peer presence
                peers = data.get('identified_peers', [])
                if len(peers) > 0:
                    advantages.append(f"{symbol}: Established competitive position in sector with peers {', '.join(peers[:3])}")

        return advantages[:5] if advantages else [f"Analysis complete with identified peer set"]

    def _identify_competitive_risks(self, comparison_data: Dict) -> List[str]:
        """Identify competitive risks"""
        risks = []

        for symbol, data in comparison_data.items():
            if isinstance(data, dict):
                if data.get('market_position') == 'laggard':
                    risks.append(f"{symbol}: Weak competitive position")
                if data.get('valuation_vs_peers') == 'premium':
                    risks.append(f"{symbol}: Premium valuation may limit upside")

                peers = data.get('identified_peers', [])
                if len(peers) > 3:
                    risks.append(f"{symbol}: Intense competition from {len(peers)} identified peers")
                elif len(peers) > 0:
                    risks.append(f"{symbol}: Competitive pressure from {', '.join(peers[:2])} and others")

        return risks[:5] if risks else [f"Standard competitive risks apply in sector"]
