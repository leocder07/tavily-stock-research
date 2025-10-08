"""
Valuation Specialist Agent - DCF Model, Intrinsic Value, Scenario Analysis

This agent focuses on company valuation using multiple methods:
1. Discounted Cash Flow (DCF) analysis
2. Relative valuation (P/E, PEG, EV/EBITDA multiples)
3. Scenario analysis (bull/base/bear cases)
4. Intrinsic value calculation
5. Margin of safety assessment
"""

import asyncio
from typing import Dict, Any, List, Optional
from datetime import datetime
import logging

from services.progress_tracker import Citation, progress_tracker

logger = logging.getLogger(__name__)


class ValuationSpecialistAgent:
    """
    Valuation Specialist Agent for comprehensive company valuation.

    Uses Tavily APIs to gather:
    - Free cash flow projections
    - WACC (Weighted Average Cost of Capital)
    - Terminal growth rates
    - Analyst price targets
    - Fair value estimates
    """

    def __init__(self, tavily_client=None, memory=None, **kwargs):
        self.tavily_client = tavily_client
        self.memory = memory
        self.name = "valuation_specialist"
        self.description = "Performs DCF analysis and intrinsic value calculation"
        self.citations = []
        self.request_id = None

    async def execute(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """Execute valuation analysis."""
        try:
            await self.send_progress("Starting comprehensive valuation analysis...", 0.0)

            symbol = state.get('symbol') or state.get('symbols', [''])[0]
            if not symbol:
                raise ValueError("No stock symbol provided for valuation")

            # Phase 1: Gather financial data (25%)
            await self.send_progress(f"Gathering financial data for {symbol}...", 0.1)
            financial_data = await self._gather_financial_data(symbol)
            await self.send_progress("Financial data gathered", 0.25)

            # Phase 2: Calculate DCF valuation (50%)
            await self.send_progress("Calculating DCF valuation...", 0.3)
            dcf_result = await self._calculate_dcf_valuation(symbol, financial_data)
            await self.send_progress("DCF valuation complete", 0.5)

            # Phase 3: Relative valuation (70%)
            await self.send_progress("Analyzing relative valuation...", 0.55)
            relative_val = await self._analyze_relative_valuation(symbol, financial_data)
            await self.send_progress("Relative valuation complete", 0.7)

            # Phase 4: Scenario analysis (90%)
            await self.send_progress("Running scenario analysis...", 0.75)
            scenarios = await self._scenario_analysis(symbol, dcf_result, relative_val)
            await self.send_progress("Scenario analysis complete", 0.9)

            # Phase 5: Synthesize results (100%)
            await self.send_progress("Synthesizing valuation results...", 0.95)
            final_valuation = await self._synthesize_valuation(
                symbol, dcf_result, relative_val, scenarios, financial_data
            )
            await self.send_progress("Valuation analysis complete", 1.0)

            return {
                'valuation_analysis': final_valuation,
                'citations': self.citations
            }

        except Exception as e:
            logger.error(f"Error in ValuationSpecialistAgent: {e}", exc_info=True)
            await self.send_progress(f"Valuation analysis failed: {str(e)}", 1.0)
            return {'valuation_analysis': None, 'error': str(e)}

    async def _gather_financial_data(self, symbol: str) -> Dict[str, Any]:
        """Gather financial data needed for valuation."""
        financial_data = {
            'free_cash_flow': None,
            'revenue': None,
            'operating_margin': None,
            'wacc': None,
            'terminal_growth_rate': None,
            'shares_outstanding': None,
            'current_price': None,
            'market_cap': None
        }

        try:
            # Query 1: Free cash flow and revenue
            fcf_query = f"What is {symbol} stock's latest annual free cash flow FCF and revenue in dollars?"
            fcf_results = await self.qna_search_tavily(fcf_query)

            if fcf_results:
                self.add_citation(
                    url=fcf_results.get('url', ''),
                    title=f"{symbol} Free Cash Flow Data",
                    content=fcf_results.get('answer', ''),
                    agent_id=self.name,
                    relevance_score=0.9
                )

                # Extract FCF and revenue (in millions/billions)
                financial_data['free_cash_flow'] = self._extract_number(
                    fcf_results.get('answer', ''),
                    ['free cash flow', 'fcf']
                )
                financial_data['revenue'] = self._extract_number(
                    fcf_results.get('answer', ''),
                    ['revenue', 'sales']
                )

            # Query 2: WACC and cost of capital
            wacc_query = f"What is {symbol} stock's weighted average cost of capital WACC or discount rate?"
            wacc_results = await self.qna_search_tavily(wacc_query)

            if wacc_results:
                self.add_citation(
                    url=wacc_results.get('url', ''),
                    title=f"{symbol} WACC Data",
                    content=wacc_results.get('answer', ''),
                    agent_id=self.name,
                    relevance_score=0.85
                )
                financial_data['wacc'] = self._extract_percentage(
                    wacc_results.get('answer', ''),
                    ['wacc', 'discount rate', 'cost of capital']
                )

            # Query 3: Market data
            market_query = f"{symbol} stock current price shares outstanding market capitalization"
            market_results = await self.search_tavily(market_query)

            if market_results:
                for result in market_results[:2]:
                    self.add_citation(
                        url=result.get('url', ''),
                        title=result.get('title', ''),
                        content=result.get('content', ''),
                        agent_id=self.name,
                        relevance_score=result.get('score', 0.7)
                    )

                # Extract from first result
                content = market_results[0].get('content', '')
                financial_data['current_price'] = self._extract_number(content, ['price', 'trading at', '$'])
                financial_data['shares_outstanding'] = self._extract_number(
                    content,
                    ['shares outstanding', 'shares']
                )
                financial_data['market_cap'] = self._extract_number(content, ['market cap', 'capitalization'])

            # Set defaults for missing values
            if not financial_data['wacc']:
                financial_data['wacc'] = 10.0  # Default WACC estimate
            if not financial_data['terminal_growth_rate']:
                financial_data['terminal_growth_rate'] = 2.5  # GDP growth assumption

            logger.info(f"Gathered financial data for {symbol}: {financial_data}")

        except Exception as e:
            logger.error(f"Error gathering financial data: {e}")

        return financial_data

    async def _calculate_dcf_valuation(self, symbol: str, financial_data: Dict[str, Any]) -> Dict[str, Any]:
        """Calculate DCF (Discounted Cash Flow) valuation."""
        dcf_result = {
            'intrinsic_value_per_share': None,
            'current_price': financial_data.get('current_price'),
            'upside_downside': None,
            'margin_of_safety': None,
            'npv_fcf': None,
            'terminal_value': None,
            'enterprise_value': None,
            'assumptions': {},
            'explanation': ''
        }

        try:
            # Query for growth projections
            growth_query = f"What is the expected revenue growth rate for {symbol} stock over the next 5 years?"
            growth_results = await self.qna_search_tavily(growth_query)

            if growth_results:
                self.add_citation(
                    url=growth_results.get('url', ''),
                    title=f"{symbol} Growth Projections",
                    content=growth_results.get('answer', ''),
                    agent_id=self.name,
                    relevance_score=0.85
                )

            growth_rate = self._extract_percentage(
                growth_results.get('answer', '') if growth_results else '',
                ['growth', 'cagr', 'compound annual']
            ) or 8.0  # Default growth assumption

            # DCF Assumptions
            fcf = financial_data.get('free_cash_flow') or 0
            wacc = financial_data.get('wacc', 10.0) / 100  # Convert to decimal
            terminal_growth = financial_data.get('terminal_growth_rate', 2.5) / 100
            shares = financial_data.get('shares_outstanding') or 0

            dcf_result['assumptions'] = {
                'base_fcf': fcf,
                'growth_rate_years_1_5': growth_rate,
                'wacc': wacc * 100,
                'terminal_growth_rate': terminal_growth * 100,
                'projection_years': 5
            }

            # Only calculate if we have FCF and shares
            if fcf and shares and fcf > 0 and shares > 0:
                # Project 5 years of FCF
                projected_fcf = []
                for year in range(1, 6):
                    projected = fcf * ((1 + growth_rate/100) ** year)
                    projected_fcf.append(projected)

                # Calculate NPV of projected FCF
                npv_fcf = sum(
                    cf / ((1 + wacc) ** (year + 1))
                    for year, cf in enumerate(projected_fcf)
                )

                # Calculate terminal value
                terminal_fcf = projected_fcf[-1] * (1 + terminal_growth)
                terminal_value = terminal_fcf / (wacc - terminal_growth)
                pv_terminal_value = terminal_value / ((1 + wacc) ** 5)

                # Enterprise value = NPV of FCF + PV of Terminal Value
                enterprise_value = npv_fcf + pv_terminal_value

                # Intrinsic value per share
                intrinsic_value = enterprise_value / shares

                dcf_result['npv_fcf'] = npv_fcf
                dcf_result['terminal_value'] = terminal_value
                dcf_result['enterprise_value'] = enterprise_value
                dcf_result['intrinsic_value_per_share'] = intrinsic_value

                # Calculate upside/downside
                current_price = financial_data.get('current_price')
                if current_price and current_price > 0:
                    upside = ((intrinsic_value - current_price) / current_price) * 100
                    dcf_result['upside_downside'] = upside
                    dcf_result['margin_of_safety'] = ((intrinsic_value - current_price) / intrinsic_value) * 100

                dcf_result['explanation'] = (
                    f"DCF Analysis: Projected {symbol}'s FCF over 5 years at {growth_rate}% growth, "
                    f"discounted at {wacc*100:.1f}% WACC. Terminal value assumes {terminal_growth*100:.1f}% "
                    f"perpetual growth. Intrinsic value: ${intrinsic_value:.2f} per share."
                )
            else:
                dcf_result['explanation'] = "Insufficient data for DCF calculation. Missing FCF or shares outstanding."

        except Exception as e:
            logger.error(f"Error calculating DCF: {e}")
            dcf_result['explanation'] = f"DCF calculation failed: {str(e)}"

        return dcf_result

    async def _analyze_relative_valuation(self, symbol: str, financial_data: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze relative valuation using multiples."""
        relative_val = {
            'pe_ratio': None,
            'peg_ratio': None,
            'ev_ebitda': None,
            'price_to_book': None,
            'peer_pe_average': None,
            'peer_ev_ebitda_average': None,
            'valuation_vs_peers': '',
            'fair_value_pe': None,
            'fair_value_ev_ebitda': None
        }

        try:
            # Query multiples
            multiples_query = f"{symbol} stock PE ratio PEG ratio EV/EBITDA price to book valuation multiples"
            multiples_results = await self.search_tavily(multiples_query)

            if multiples_results:
                for result in multiples_results[:3]:
                    self.add_citation(
                        url=result.get('url', ''),
                        title=result.get('title', ''),
                        content=result.get('content', ''),
                        agent_id=self.name,
                        relevance_score=result.get('score', 0.8)
                    )

                content = ' '.join([r.get('content', '') for r in multiples_results[:3]])
                relative_val['pe_ratio'] = self._extract_number(content, ['p/e', 'pe ratio', 'price to earnings'])
                relative_val['peg_ratio'] = self._extract_number(content, ['peg', 'peg ratio'])
                relative_val['ev_ebitda'] = self._extract_number(content, ['ev/ebitda', 'ev to ebitda'])
                relative_val['price_to_book'] = self._extract_number(content, ['p/b', 'price to book'])

            # Query peer valuation
            peer_query = f"{symbol} stock sector peer companies average PE ratio valuation comparison"
            peer_results = await self.search_tavily(peer_query)

            if peer_results:
                self.add_citation(
                    url=peer_results[0].get('url', ''),
                    title=peer_results[0].get('title', ''),
                    content=peer_results[0].get('content', ''),
                    agent_id=self.name,
                    relevance_score=peer_results[0].get('score', 0.75)
                )

                content = peer_results[0].get('content', '')
                relative_val['peer_pe_average'] = self._extract_number(content, ['average pe', 'peer pe', 'sector pe'])

            # Assess valuation vs peers
            if relative_val['pe_ratio'] and relative_val['peer_pe_average']:
                if relative_val['pe_ratio'] < relative_val['peer_pe_average']:
                    relative_val['valuation_vs_peers'] = 'UNDERVALUED vs peers'
                elif relative_val['pe_ratio'] > relative_val['peer_pe_average'] * 1.2:
                    relative_val['valuation_vs_peers'] = 'OVERVALUED vs peers'
                else:
                    relative_val['valuation_vs_peers'] = 'FAIRLY VALUED vs peers'

        except Exception as e:
            logger.error(f"Error analyzing relative valuation: {e}")

        return relative_val

    async def _scenario_analysis(self, symbol: str, dcf: Dict, relative: Dict) -> Dict[str, Any]:
        """Perform bull/base/bear scenario analysis."""
        scenarios = {
            'bull_case': {},
            'base_case': {},
            'bear_case': {},
            'probability_weighted_value': None
        }

        try:
            # Base case is the DCF result
            base_intrinsic = dcf.get('intrinsic_value_per_share')

            if base_intrinsic:
                # Bull case: 20% higher growth, lower WACC
                scenarios['bull_case'] = {
                    'intrinsic_value': base_intrinsic * 1.35,
                    'assumptions': 'Higher growth (+20%), market expansion',
                    'probability': 25
                }

                # Base case
                scenarios['base_case'] = {
                    'intrinsic_value': base_intrinsic,
                    'assumptions': 'Current projections maintained',
                    'probability': 50
                }

                # Bear case: Lower growth, higher WACC
                scenarios['bear_case'] = {
                    'intrinsic_value': base_intrinsic * 0.70,
                    'assumptions': 'Growth slowdown, higher rates',
                    'probability': 25
                }

                # Probability-weighted value
                weighted_value = (
                    scenarios['bull_case']['intrinsic_value'] * 0.25 +
                    scenarios['base_case']['intrinsic_value'] * 0.50 +
                    scenarios['bear_case']['intrinsic_value'] * 0.25
                )
                scenarios['probability_weighted_value'] = weighted_value

        except Exception as e:
            logger.error(f"Error in scenario analysis: {e}")

        return scenarios

    async def _synthesize_valuation(
        self,
        symbol: str,
        dcf: Dict,
        relative: Dict,
        scenarios: Dict,
        financial_data: Dict
    ) -> Dict[str, Any]:
        """Synthesize all valuation methods into final recommendation."""

        current_price = financial_data.get('current_price')
        intrinsic_value = dcf.get('intrinsic_value_per_share')
        weighted_value = scenarios.get('probability_weighted_value')

        synthesis = {
            'symbol': symbol,
            'current_price': current_price,
            'valuation_methods': {
                'dcf': dcf,
                'relative': relative,
                'scenarios': scenarios
            },
            'recommended_fair_value': weighted_value or intrinsic_value,
            'margin_of_safety': dcf.get('margin_of_safety'),
            'valuation_rating': '',
            'investment_recommendation': '',
            'confidence_level': 'MODERATE',
            'key_insights': []
        }

        # Determine valuation rating
        if current_price and intrinsic_value:
            discount = ((intrinsic_value - current_price) / intrinsic_value) * 100

            if discount > 30:
                synthesis['valuation_rating'] = 'SIGNIFICANTLY UNDERVALUED'
                synthesis['investment_recommendation'] = 'STRONG BUY'
                synthesis['confidence_level'] = 'HIGH'
            elif discount > 15:
                synthesis['valuation_rating'] = 'UNDERVALUED'
                synthesis['investment_recommendation'] = 'BUY'
                synthesis['confidence_level'] = 'MODERATE'
            elif discount > -10:
                synthesis['valuation_rating'] = 'FAIRLY VALUED'
                synthesis['investment_recommendation'] = 'HOLD'
                synthesis['confidence_level'] = 'MODERATE'
            else:
                synthesis['valuation_rating'] = 'OVERVALUED'
                synthesis['investment_recommendation'] = 'AVOID'
                synthesis['confidence_level'] = 'HIGH'

            synthesis['key_insights'].append(
                f"DCF intrinsic value of ${intrinsic_value:.2f} implies {discount:.1f}% margin of safety"
            )

        # Add relative valuation insight
        if relative.get('valuation_vs_peers'):
            synthesis['key_insights'].append(
                f"Relative valuation: {relative['valuation_vs_peers']}"
            )

        # Add scenario analysis insight
        if scenarios.get('probability_weighted_value'):
            synthesis['key_insights'].append(
                f"Probability-weighted fair value: ${scenarios['probability_weighted_value']:.2f}"
            )

        return synthesis

    def _extract_number(self, text: str, keywords: List[str]) -> Optional[float]:
        """Extract a number from text near keywords."""
        import re

        if not text:
            return None

        text_lower = text.lower()

        # Find keyword positions
        for keyword in keywords:
            if keyword in text_lower:
                # Look for numbers near keyword (within 50 chars)
                keyword_pos = text_lower.find(keyword)
                snippet = text[max(0, keyword_pos-20):min(len(text), keyword_pos+100)]

                # Extract number with units (million, billion, trillion)
                patterns = [
                    r'(\d+\.?\d*)\s*trillion',
                    r'(\d+\.?\d*)\s*billion',
                    r'(\d+\.?\d*)\s*million',
                    r'\$(\d+\.?\d*)',
                    r'(\d+\.?\d*)'
                ]

                for pattern in patterns:
                    match = re.search(pattern, snippet, re.IGNORECASE)
                    if match:
                        value = float(match.group(1))

                        # Adjust for units
                        if 'trillion' in snippet.lower():
                            value *= 1_000_000
                        elif 'billion' in snippet.lower():
                            value *= 1_000
                        # millions remain as-is

                        return value

        return None

    def _extract_percentage(self, text: str, keywords: List[str]) -> Optional[float]:
        """Extract a percentage from text near keywords."""
        import re

        if not text:
            return None

        text_lower = text.lower()

        for keyword in keywords:
            if keyword in text_lower:
                keyword_pos = text_lower.find(keyword)
                snippet = text[max(0, keyword_pos-20):min(len(text), keyword_pos+50)]

                # Look for percentage
                match = re.search(r'(\d+\.?\d*)%', snippet)
                if match:
                    return float(match.group(1))

                # Look for decimal (0.xx)
                match = re.search(r'0\.(\d+)', snippet)
                if match:
                    return float(f"0.{match.group(1)}") * 100

        return None

    async def send_progress(self, message: str, progress: float):
        """Send progress update."""
        if self.request_id:
            await progress_tracker.send_update(self.request_id, {
                'agent': self.name,
                'message': message,
                'progress': progress
            })

    async def search_tavily(self, query: str) -> List[Dict]:
        """Search using Tavily API."""
        if not self.tavily_client:
            return []
        try:
            results = await self.tavily_client.search(query)
            return results.get('results', [])
        except Exception as e:
            logger.error(f"Tavily search error: {e}")
            return []

    async def qna_search_tavily(self, query: str) -> Dict:
        """QnA search using Tavily API."""
        if not self.tavily_client:
            return {}
        try:
            result = await self.tavily_client.qna_search(query)
            return result
        except Exception as e:
            logger.error(f"Tavily QnA search error: {e}")
            return {}

    def add_citation(self, url: str, title: str, content: str, agent_id: str, relevance_score: float):
        """Add a citation."""
        self.citations.append(Citation(
            url=url,
            title=title,
            content=content,
            agent_id=agent_id,
            relevance_score=relevance_score,
            timestamp=datetime.utcnow()
        ))
