"""
Macro Economics Agent - Economic Context and Market Environment Analysis

This agent analyzes macroeconomic factors that impact stock performance:
1. Federal Reserve policy (interest rates, monetary policy)
2. GDP growth and economic indicators
3. Inflation trends (CPI, PCE)
4. Sector-specific economic factors
5. Currency and commodity impacts
6. Economic cycle positioning
"""

import asyncio
from typing import Dict, Any, List, Optional
from datetime import datetime
import logging

from services.progress_tracker import Citation, progress_tracker

logger = logging.getLogger(__name__)


class MacroEconomicsAgent:
    """
    Macro Economics Agent for analyzing economic context and market environment.

    Uses Tavily APIs to gather:
    - Current Fed policy and interest rate outlook
    - GDP growth trends and forecasts
    - Inflation data and trends
    - Sector-specific economic drivers
    - Currency and commodity price impacts
    """

    def __init__(self, tavily_client=None, memory=None, **kwargs):
        self.tavily_client = tavily_client
        self.memory = memory
        self.name = "macro_economics"
        self.description = "Analyzes macroeconomic factors and market environment"
        self.citations = []
        self.request_id = None

    async def execute(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """Execute macro economics analysis."""
        try:
            await self.send_progress("Starting macroeconomic analysis...", 0.0)

            symbol = state.get('symbol') or state.get('symbols', [''])[0]
            sector = state.get('sector', 'Technology')  # Get from state or default

            if not symbol:
                raise ValueError("No stock symbol provided for macro analysis")

            # Phase 1: Federal Reserve & Interest Rates (20%)
            await self.send_progress("Analyzing Fed policy and interest rates...", 0.05)
            fed_analysis = await self._analyze_fed_policy(symbol)
            await self.send_progress("Fed policy analysis complete", 0.2)

            # Phase 2: GDP & Economic Growth (40%)
            await self.send_progress("Analyzing GDP and economic growth...", 0.25)
            gdp_analysis = await self._analyze_gdp_trends(symbol)
            await self.send_progress("GDP analysis complete", 0.4)

            # Phase 3: Inflation Analysis (60%)
            await self.send_progress("Analyzing inflation trends...", 0.45)
            inflation_analysis = await self._analyze_inflation(symbol)
            await self.send_progress("Inflation analysis complete", 0.6)

            # Phase 4: Sector-Specific Factors (80%)
            await self.send_progress(f"Analyzing {sector} sector economics...", 0.65)
            sector_analysis = await self._analyze_sector_economics(symbol, sector)
            await self.send_progress("Sector analysis complete", 0.8)

            # Phase 5: Economic Cycle & Risk Assessment (100%)
            await self.send_progress("Assessing economic cycle positioning...", 0.85)
            cycle_analysis = await self._assess_economic_cycle(
                fed_analysis, gdp_analysis, inflation_analysis
            )
            await self.send_progress("Economic cycle assessment complete", 0.95)

            # Synthesize macro outlook
            await self.send_progress("Synthesizing macro outlook...", 0.98)
            macro_outlook = await self._synthesize_macro_outlook(
                symbol, fed_analysis, gdp_analysis, inflation_analysis,
                sector_analysis, cycle_analysis
            )
            await self.send_progress("Macroeconomic analysis complete", 1.0)

            return {
                'macro_analysis': macro_outlook,
                'citations': self.citations
            }

        except Exception as e:
            logger.error(f"Error in MacroEconomicsAgent: {e}", exc_info=True)
            await self.send_progress(f"Macro analysis failed: {str(e)}", 1.0)
            return {'macro_analysis': None, 'error': str(e)}

    async def _analyze_fed_policy(self, symbol: str) -> Dict[str, Any]:
        """Analyze Federal Reserve policy and interest rate environment."""
        fed_analysis = {
            'current_fed_rate': None,
            'rate_direction': 'NEUTRAL',
            'policy_stance': 'NEUTRAL',
            'rate_impact_on_stock': '',
            'next_fed_meeting': None,
            'market_expectations': ''
        }

        try:
            # Query 1: Current Fed funds rate
            fed_rate_query = "What is the current Federal Reserve interest rate federal funds rate?"
            fed_rate_results = await self.qna_search_tavily(fed_rate_query)

            if fed_rate_results:
                self.add_citation(
                    url=fed_rate_results.get('url', ''),
                    title="Federal Reserve Interest Rate",
                    content=fed_rate_results.get('answer', ''),
                    agent_id=self.name,
                    relevance_score=0.95
                )

                answer = fed_rate_results.get('answer', '').lower()
                fed_analysis['current_fed_rate'] = self._extract_percentage_value(answer)

            # Query 2: Fed policy outlook
            fed_outlook_query = "Federal Reserve interest rate outlook 2024 2025 monetary policy future rate cuts or hikes"
            outlook_results = await self.search_tavily(fed_outlook_query)

            if outlook_results:
                for result in outlook_results[:3]:
                    self.add_citation(
                        url=result.get('url', ''),
                        title=result.get('title', ''),
                        content=result.get('content', ''),
                        agent_id=self.name,
                        relevance_score=result.get('score', 0.85)
                    )

                content = ' '.join([r.get('content', '') for r in outlook_results[:3]]).lower()

                # Determine rate direction
                if 'rate cut' in content or 'cutting rates' in content or 'lower rates' in content:
                    fed_analysis['rate_direction'] = 'EASING'
                    fed_analysis['policy_stance'] = 'ACCOMMODATIVE'
                elif 'rate hike' in content or 'raising rates' in content or 'higher rates' in content:
                    fed_analysis['rate_direction'] = 'TIGHTENING'
                    fed_analysis['policy_stance'] = 'RESTRICTIVE'
                else:
                    fed_analysis['rate_direction'] = 'HOLDING'
                    fed_analysis['policy_stance'] = 'NEUTRAL'

                fed_analysis['market_expectations'] = outlook_results[0].get('content', '')[:300]

            # Query 3: Impact on stock
            impact_query = f"How do Federal Reserve interest rates affect {symbol} stock valuation and performance?"
            impact_results = await self.qna_search_tavily(impact_query)

            if impact_results:
                self.add_citation(
                    url=impact_results.get('url', ''),
                    title=f"Fed Policy Impact on {symbol}",
                    content=impact_results.get('answer', ''),
                    agent_id=self.name,
                    relevance_score=0.8
                )
                fed_analysis['rate_impact_on_stock'] = impact_results.get('answer', '')

        except Exception as e:
            logger.error(f"Error analyzing Fed policy: {e}")

        return fed_analysis

    async def _analyze_gdp_trends(self, symbol: str) -> Dict[str, Any]:
        """Analyze GDP growth and economic health indicators."""
        gdp_analysis = {
            'current_gdp_growth': None,
            'gdp_trend': 'STABLE',
            'economic_health': 'MODERATE',
            'unemployment_rate': None,
            'consumer_spending': '',
            'business_investment': '',
            'recession_risk': 'LOW'
        }

        try:
            # Query 1: Current GDP growth
            gdp_query = "What is the current United States GDP growth rate latest quarter?"
            gdp_results = await self.qna_search_tavily(gdp_query)

            if gdp_results:
                self.add_citation(
                    url=gdp_results.get('url', ''),
                    title="US GDP Growth Rate",
                    content=gdp_results.get('answer', ''),
                    agent_id=self.name,
                    relevance_score=0.9
                )

                answer = gdp_results.get('answer', '').lower()
                gdp_analysis['current_gdp_growth'] = self._extract_percentage_value(answer)

                # Assess GDP trend
                if gdp_analysis['current_gdp_growth']:
                    if gdp_analysis['current_gdp_growth'] > 3.0:
                        gdp_analysis['gdp_trend'] = 'ACCELERATING'
                        gdp_analysis['economic_health'] = 'STRONG'
                    elif gdp_analysis['current_gdp_growth'] > 1.5:
                        gdp_analysis['gdp_trend'] = 'STABLE'
                        gdp_analysis['economic_health'] = 'MODERATE'
                    elif gdp_analysis['current_gdp_growth'] > 0:
                        gdp_analysis['gdp_trend'] = 'SLOWING'
                        gdp_analysis['economic_health'] = 'WEAK'
                    else:
                        gdp_analysis['gdp_trend'] = 'CONTRACTING'
                        gdp_analysis['economic_health'] = 'RECESSION'
                        gdp_analysis['recession_risk'] = 'HIGH'

            # Query 2: Unemployment and labor market
            unemployment_query = "United States unemployment rate current labor market conditions"
            unemployment_results = await self.search_tavily(unemployment_query)

            if unemployment_results:
                self.add_citation(
                    url=unemployment_results[0].get('url', ''),
                    title=unemployment_results[0].get('title', ''),
                    content=unemployment_results[0].get('content', ''),
                    agent_id=self.name,
                    relevance_score=unemployment_results[0].get('score', 0.85)
                )

                content = unemployment_results[0].get('content', '').lower()
                gdp_analysis['unemployment_rate'] = self._extract_percentage_value(content)

            # Query 3: Consumer spending trends
            consumer_query = "United States consumer spending retail sales trends latest data"
            consumer_results = await self.search_tavily(consumer_query)

            if consumer_results:
                self.add_citation(
                    url=consumer_results[0].get('url', ''),
                    title=consumer_results[0].get('title', ''),
                    content=consumer_results[0].get('content', ''),
                    agent_id=self.name,
                    relevance_score=consumer_results[0].get('score', 0.8)
                )
                gdp_analysis['consumer_spending'] = consumer_results[0].get('content', '')[:250]

        except Exception as e:
            logger.error(f"Error analyzing GDP trends: {e}")

        return gdp_analysis

    async def _analyze_inflation(self, symbol: str) -> Dict[str, Any]:
        """Analyze inflation trends and impact."""
        inflation_analysis = {
            'current_cpi': None,
            'inflation_trend': 'STABLE',
            'inflation_target_vs_actual': '',
            'inflation_impact': '',
            'commodity_prices': {},
            'wage_inflation': None
        }

        try:
            # Query 1: Current CPI inflation
            cpi_query = "What is the current United States CPI inflation rate consumer price index?"
            cpi_results = await self.qna_search_tavily(cpi_query)

            if cpi_results:
                self.add_citation(
                    url=cpi_results.get('url', ''),
                    title="US CPI Inflation Rate",
                    content=cpi_results.get('answer', ''),
                    agent_id=self.name,
                    relevance_score=0.95
                )

                answer = cpi_results.get('answer', '').lower()
                inflation_analysis['current_cpi'] = self._extract_percentage_value(answer)

                # Assess vs Fed target (2%)
                if inflation_analysis['current_cpi']:
                    if inflation_analysis['current_cpi'] > 4.0:
                        inflation_analysis['inflation_trend'] = 'HIGH'
                        inflation_analysis['inflation_target_vs_actual'] = 'Well above Fed 2% target'
                    elif inflation_analysis['current_cpi'] > 2.5:
                        inflation_analysis['inflation_trend'] = 'ELEVATED'
                        inflation_analysis['inflation_target_vs_actual'] = 'Above Fed 2% target'
                    elif inflation_analysis['current_cpi'] >= 1.5:
                        inflation_analysis['inflation_trend'] = 'STABLE'
                        inflation_analysis['inflation_target_vs_actual'] = 'Near Fed 2% target'
                    else:
                        inflation_analysis['inflation_trend'] = 'LOW'
                        inflation_analysis['inflation_target_vs_actual'] = 'Below Fed 2% target'

            # Query 2: Inflation impact on company
            impact_query = f"How does inflation affect {symbol} stock profit margins pricing power cost pressures?"
            impact_results = await self.qna_search_tavily(impact_query)

            if impact_results:
                self.add_citation(
                    url=impact_results.get('url', ''),
                    title=f"Inflation Impact on {symbol}",
                    content=impact_results.get('answer', ''),
                    agent_id=self.name,
                    relevance_score=0.8
                )
                inflation_analysis['inflation_impact'] = impact_results.get('answer', '')

            # Query 3: Key commodity prices (if relevant)
            commodity_query = "oil prices natural gas copper commodity prices latest trends"
            commodity_results = await self.search_tavily(commodity_query)

            if commodity_results:
                self.add_citation(
                    url=commodity_results[0].get('url', ''),
                    title="Commodity Price Trends",
                    content=commodity_results[0].get('content', ''),
                    agent_id=self.name,
                    relevance_score=commodity_results[0].get('score', 0.7)
                )

        except Exception as e:
            logger.error(f"Error analyzing inflation: {e}")

        return inflation_analysis

    async def _analyze_sector_economics(self, symbol: str, sector: str) -> Dict[str, Any]:
        """Analyze sector-specific economic factors."""
        sector_analysis = {
            'sector': sector,
            'sector_outlook': '',
            'sector_drivers': [],
            'regulatory_environment': '',
            'competitive_dynamics': '',
            'sector_tailwinds': [],
            'sector_headwinds': []
        }

        try:
            # Query sector outlook
            sector_query = f"{sector} sector economic outlook trends 2024 2025 growth drivers challenges"
            sector_results = await self.search_tavily(sector_query)

            if sector_results:
                for result in sector_results[:3]:
                    self.add_citation(
                        url=result.get('url', ''),
                        title=result.get('title', ''),
                        content=result.get('content', ''),
                        agent_id=self.name,
                        relevance_score=result.get('score', 0.8)
                    )

                sector_analysis['sector_outlook'] = sector_results[0].get('content', '')[:300]

                # Extract tailwinds and headwinds from content
                content = ' '.join([r.get('content', '') for r in sector_results[:3]]).lower()

                # Common positive keywords
                if any(word in content for word in ['growth', 'expansion', 'demand', 'opportunity']):
                    sector_analysis['sector_tailwinds'].append('Strong demand and growth opportunities')
                if any(word in content for word in ['innovation', 'technology', 'digital']):
                    sector_analysis['sector_tailwinds'].append('Technological innovation')

                # Common negative keywords
                if any(word in content for word in ['regulation', 'compliance', 'oversight']):
                    sector_analysis['sector_headwinds'].append('Regulatory pressures')
                if any(word in content for word in ['competition', 'pricing pressure', 'commoditization']):
                    sector_analysis['sector_headwinds'].append('Competitive pressures')

            # Query regulatory environment
            regulatory_query = f"{sector} sector regulation policy government impact on {symbol}"
            regulatory_results = await self.search_tavily(regulatory_query)

            if regulatory_results:
                self.add_citation(
                    url=regulatory_results[0].get('url', ''),
                    title=regulatory_results[0].get('title', ''),
                    content=regulatory_results[0].get('content', ''),
                    agent_id=self.name,
                    relevance_score=regulatory_results[0].get('score', 0.75)
                )
                sector_analysis['regulatory_environment'] = regulatory_results[0].get('content', '')[:200]

        except Exception as e:
            logger.error(f"Error analyzing sector economics: {e}")

        return sector_analysis

    async def _assess_economic_cycle(
        self,
        fed_analysis: Dict,
        gdp_analysis: Dict,
        inflation_analysis: Dict
    ) -> Dict[str, Any]:
        """Assess where we are in the economic cycle."""
        cycle_analysis = {
            'current_phase': 'MID_CYCLE',
            'phase_description': '',
            'investment_implications': [],
            'macro_risk_level': 'MODERATE',
            'recession_probability': 'LOW'
        }

        try:
            # Determine economic cycle phase based on indicators
            gdp_growth = gdp_analysis.get('current_gdp_growth', 2.0)
            inflation = inflation_analysis.get('current_cpi', 2.5)
            fed_stance = fed_analysis.get('policy_stance', 'NEUTRAL')

            # Early Cycle: Recovering from recession, low rates, low inflation
            if gdp_growth > 2.0 and inflation < 2.5 and fed_stance == 'ACCOMMODATIVE':
                cycle_analysis['current_phase'] = 'EARLY_CYCLE'
                cycle_analysis['phase_description'] = 'Economy recovering, Fed supportive, favorable for equities'
                cycle_analysis['investment_implications'] = [
                    'Risk assets typically perform well',
                    'Growth stocks outperform',
                    'Low interest rates support valuations'
                ]
                cycle_analysis['macro_risk_level'] = 'LOW'

            # Mid Cycle: Steady growth, moderate inflation, neutral policy
            elif 1.5 < gdp_growth <= 3.0 and 1.5 < inflation < 3.5:
                cycle_analysis['current_phase'] = 'MID_CYCLE'
                cycle_analysis['phase_description'] = 'Sustained economic expansion, balanced conditions'
                cycle_analysis['investment_implications'] = [
                    'Selectivity becomes important',
                    'Focus on quality and fundamentals',
                    'Moderate returns expected'
                ]
                cycle_analysis['macro_risk_level'] = 'MODERATE'

            # Late Cycle: Slowing growth, high inflation, tight policy
            elif gdp_growth < 2.0 or inflation > 3.5 or fed_stance == 'RESTRICTIVE':
                cycle_analysis['current_phase'] = 'LATE_CYCLE'
                cycle_analysis['phase_description'] = 'Growth slowing, inflation concerns, Fed tightening'
                cycle_analysis['investment_implications'] = [
                    'Increased market volatility',
                    'Defensive sectors may outperform',
                    'Recession risk rising'
                ]
                cycle_analysis['macro_risk_level'] = 'HIGH'
                cycle_analysis['recession_probability'] = 'MODERATE'

            # Recession: Negative growth
            elif gdp_growth < 0:
                cycle_analysis['current_phase'] = 'RECESSION'
                cycle_analysis['phase_description'] = 'Economic contraction, elevated risks'
                cycle_analysis['investment_implications'] = [
                    'Focus on capital preservation',
                    'Quality and balance sheet strength critical',
                    'Fed likely to ease policy'
                ]
                cycle_analysis['macro_risk_level'] = 'VERY_HIGH'
                cycle_analysis['recession_probability'] = 'HIGH'

        except Exception as e:
            logger.error(f"Error assessing economic cycle: {e}")

        return cycle_analysis

    async def _synthesize_macro_outlook(
        self,
        symbol: str,
        fed_analysis: Dict,
        gdp_analysis: Dict,
        inflation_analysis: Dict,
        sector_analysis: Dict,
        cycle_analysis: Dict
    ) -> Dict[str, Any]:
        """Synthesize all macro analysis into actionable outlook."""

        synthesis = {
            'symbol': symbol,
            'macro_environment_rating': 'NEUTRAL',
            'key_macro_factors': {
                'fed_policy': fed_analysis,
                'gdp_growth': gdp_analysis,
                'inflation': inflation_analysis,
                'sector_economics': sector_analysis,
                'economic_cycle': cycle_analysis
            },
            'macro_tailwinds': [],
            'macro_headwinds': [],
            'overall_macro_impact': 'NEUTRAL',
            'confidence_level': 'MODERATE',
            'key_insights': []
        }

        # Assess overall macro environment
        positive_factors = 0
        negative_factors = 0

        # Fed policy assessment
        if fed_analysis.get('policy_stance') == 'ACCOMMODATIVE':
            positive_factors += 2
            synthesis['macro_tailwinds'].append('Accommodative Fed policy supports equity valuations')
        elif fed_analysis.get('policy_stance') == 'RESTRICTIVE':
            negative_factors += 2
            synthesis['macro_headwinds'].append('Restrictive Fed policy pressures valuations')

        # GDP growth assessment
        gdp_growth = gdp_analysis.get('current_gdp_growth')
        if gdp_growth and gdp_growth > 2.5:
            positive_factors += 1
            synthesis['macro_tailwinds'].append(f'Strong GDP growth of {gdp_growth:.1f}%')
        elif gdp_growth and gdp_growth < 1.0:
            negative_factors += 1
            synthesis['macro_headwinds'].append(f'Weak GDP growth of {gdp_growth:.1f}%')

        # Inflation assessment
        inflation = inflation_analysis.get('current_cpi')
        if inflation and 1.5 < inflation < 2.5:
            positive_factors += 1
            synthesis['macro_tailwinds'].append('Inflation near Fed target supports stable policy')
        elif inflation and inflation > 4.0:
            negative_factors += 1
            synthesis['macro_headwinds'].append('Elevated inflation may force Fed tightening')

        # Economic cycle assessment
        if cycle_analysis.get('current_phase') == 'EARLY_CYCLE':
            positive_factors += 2
            synthesis['macro_tailwinds'].append('Early cycle phase favorable for equities')
        elif cycle_analysis.get('current_phase') in ['LATE_CYCLE', 'RECESSION']:
            negative_factors += 2
            synthesis['macro_headwinds'].append('Late cycle/recession concerns increase risks')

        # Sector-specific factors
        if sector_analysis.get('sector_tailwinds'):
            positive_factors += len(sector_analysis['sector_tailwinds'])
            synthesis['macro_tailwinds'].extend(sector_analysis['sector_tailwinds'])

        if sector_analysis.get('sector_headwinds'):
            negative_factors += len(sector_analysis['sector_headwinds'])
            synthesis['macro_headwinds'].extend(sector_analysis['sector_headwinds'])

        # Determine overall rating
        net_score = positive_factors - negative_factors

        if net_score >= 3:
            synthesis['macro_environment_rating'] = 'VERY FAVORABLE'
            synthesis['overall_macro_impact'] = 'POSITIVE'
        elif net_score >= 1:
            synthesis['macro_environment_rating'] = 'FAVORABLE'
            synthesis['overall_macro_impact'] = 'SLIGHTLY POSITIVE'
        elif net_score <= -3:
            synthesis['macro_environment_rating'] = 'UNFAVORABLE'
            synthesis['overall_macro_impact'] = 'NEGATIVE'
        elif net_score <= -1:
            synthesis['macro_environment_rating'] = 'CAUTIOUS'
            synthesis['overall_macro_impact'] = 'SLIGHTLY NEGATIVE'
        else:
            synthesis['macro_environment_rating'] = 'NEUTRAL'
            synthesis['overall_macro_impact'] = 'NEUTRAL'

        # Add key insights
        synthesis['key_insights'].append(
            f"Economic cycle phase: {cycle_analysis.get('current_phase', 'UNKNOWN')}"
        )

        if fed_analysis.get('current_fed_rate'):
            synthesis['key_insights'].append(
                f"Fed funds rate: {fed_analysis['current_fed_rate']:.2f}% ({fed_analysis.get('rate_direction', 'HOLDING')})"
            )

        if gdp_growth:
            synthesis['key_insights'].append(
                f"GDP growth: {gdp_growth:.1f}% ({gdp_analysis.get('gdp_trend', 'STABLE')})"
            )

        if inflation:
            synthesis['key_insights'].append(
                f"CPI inflation: {inflation:.1f}% ({inflation_analysis.get('inflation_trend', 'STABLE')})"
            )

        return synthesis

    def _extract_percentage_value(self, text: str) -> Optional[float]:
        """Extract percentage value from text."""
        import re

        if not text:
            return None

        # Look for percentage pattern
        match = re.search(r'(\d+\.?\d*)%', text)
        if match:
            return float(match.group(1))

        # Look for basis points
        match = re.search(r'(\d+)\s*basis points', text)
        if match:
            return float(match.group(1)) / 100

        # Look for decimal representation
        match = re.search(r'(\d+\.\d+)', text)
        if match:
            value = float(match.group(1))
            # If it's a small decimal like 0.05, likely already a percentage
            if value < 1:
                return value * 100
            return value

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

