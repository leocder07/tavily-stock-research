"""
Expert Risk Assessment Agent
Quantitative risk analysis with GPT-4 interpretation
VaR, CVaR, Monte Carlo, Portfolio optimization
"""

import logging
from typing import Dict, Any, List
from datetime import datetime

from langchain_openai import ChatOpenAI
from langchain.prompts import ChatPromptTemplate
from langchain.output_parsers import PydanticOutputParser
from pydantic import BaseModel, Field

from calculators.risk_calculator import RiskCalculator
from agents.mixins.lineage_mixin import LineageMixin
from services.data_lineage_tracker import DataSource, DataReliability

logger = logging.getLogger(__name__)


class RiskInsight(BaseModel):
    """Structured risk analysis output"""
    risk_assessment: str = Field(description="Overall risk evaluation")
    downside_analysis: str = Field(description="Downside risk interpretation")
    portfolio_impact: str = Field(description="Impact on portfolio")
    risk_mitigation: str = Field(description="Risk mitigation strategies")
    optimal_position_size: str = Field(description="Recommended position sizing")
    risk_level: str = Field(description="LOW, MEDIUM, or HIGH")
    confidence_score: float = Field(description="Confidence 0-1")


class ExpertRiskAgent(LineageMixin):
    """
    Ray Dalio-inspired risk assessment agent
    Quantitative risk models + AI interpretation
    """

    def __init__(self, llm: ChatOpenAI):
        self.name = "ExpertRiskAgent"
        self.llm = llm
        self.calculator = RiskCalculator()
        self.output_parser = PydanticOutputParser(pydantic_object=RiskInsight)
        self.init_lineage_tracking()  # Initialize lineage tracking

    async def analyze(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Perform comprehensive risk assessment

        Args:
            context: {
                'symbol': str,
                'price': float,
                'returns': List[float],  # Historical returns
                'portfolio_value': float,
                'beta': float,
                'volatility': float
            }
        """
        logger.info(f"[{self.name}] Starting risk analysis for {context.get('symbol')}")

        symbol = context.get('symbol', 'UNKNOWN')
        # CRITICAL FIX: Get price from market_data if not at root level
        price = context.get('price') or context.get('market_data', {}).get('price', 0)

        try:
            # Step 1: Calculate risk metrics locally
            risk_metrics = await self._calculate_risk_metrics(context)

            # Step 2: Use GPT-4 for risk interpretation
            insights = await self._generate_expert_insights(symbol, price, risk_metrics, context)

            # Step 2.5: Track data lineage
            self._track_risk_lineage(symbol, price, risk_metrics, context)

            # Step 3: Combine calculations with insights
            result = {
                'agent': self.name,
                'symbol': symbol,
                'risk_metrics': risk_metrics,
                'insights': insights,
                'summary': insights.get('risk_assessment', 'Moderate risk'),
                'risk_level': insights.get('risk_level', 'medium'),
                'risk_score': risk_metrics.get('risk_score', 50),
                'var_95': risk_metrics.get('var', {}).get('var'),
                'cvar_95': risk_metrics.get('cvar', {}).get('cvar'),
                'sharpe_ratio': risk_metrics.get('sharpe_ratio'),
                'sortino_ratio': risk_metrics.get('sortino_ratio'),
                'max_drawdown': risk_metrics.get('max_drawdown', {}).get('max_drawdown'),
                'beta': risk_metrics.get('beta'),
                'volatility': risk_metrics.get('volatility'),
                'downside_risk': risk_metrics.get('cvar', {}).get('cvar_percent'),
                'monte_carlo': risk_metrics.get('monte_carlo'),
                'confidence': insights.get('confidence_score', 0.6),
                'timestamp': datetime.utcnow().isoformat()
            }

            logger.info(f"[{self.name}] Completed risk analysis: {result['risk_level'].upper()} risk")

            # Add lineage to output
            result = self.add_lineage_to_output(result)
            return result

        except Exception as e:
            logger.error(f"[{self.name}] Error in risk analysis: {e}")
            return self._fallback_analysis(symbol)

    async def _calculate_risk_metrics(self, context: Dict) -> Dict[str, Any]:
        """Calculate all risk metrics using local calculator"""

        # CRITICAL FIX: Get price from market_data if not at root level
        price = context.get('price') or context.get('market_data', {}).get('price', 100)
        returns = context.get('returns', self._generate_dummy_returns(price))
        portfolio_value = context.get('portfolio_value', 100000)
        prices = context.get('prices', [price] * 100)

        metrics = {
            'var': self.calculator.calculate_var(returns, 0.95, portfolio_value),
            'cvar': self.calculator.calculate_cvar(returns, 0.95, portfolio_value),
            'sharpe_ratio': self.calculator.calculate_sharpe_ratio(returns),
            'sortino_ratio': self.calculator.calculate_sortino_ratio(returns),
            'max_drawdown': self.calculator.calculate_max_drawdown(prices),
            'beta': context.get('beta', 1.0),  # From market data or estimate
            'volatility': self._calculate_volatility(returns)
        }

        # Monte Carlo simulation
        if prices:
            current_price = prices[-1]
            expected_return = sum(returns) / len(returns) if returns else 0
            volatility = metrics['volatility'] or 0.20

            metrics['monte_carlo'] = self.calculator.monte_carlo_simulation(
                current_price,
                expected_return,
                volatility,
                days=252,  # 1 year
                simulations=10000
            )

        # Calculate overall risk score
        metrics['risk_score'] = self._calculate_risk_score(metrics)

        return metrics

    def _calculate_volatility(self, returns: List[float]) -> float:
        """Calculate annualized volatility"""
        if not returns or len(returns) < 2:
            return 0.20  # Default 20% volatility

        mean = sum(returns) / len(returns)
        variance = sum((r - mean) ** 2 for r in returns) / (len(returns) - 1)
        std_dev = variance ** 0.5

        # Annualize (252 trading days)
        annualized_vol = std_dev * (252 ** 0.5)

        return round(annualized_vol, 4)

    def _calculate_risk_score(self, metrics: Dict) -> int:
        """Calculate composite risk score 0-100 (higher = more risk)"""

        score = 50  # Start neutral

        # Sharpe ratio (lower = more risk)
        sharpe = metrics.get('sharpe_ratio', 0)
        if sharpe and sharpe < 0:
            score += 15
        elif sharpe and sharpe < 1:
            score += 5
        elif sharpe and sharpe > 2:
            score -= 10

        # Sortino ratio
        sortino = metrics.get('sortino_ratio', 0)
        if sortino and sortino < 0:
            score += 10
        elif sortino and sortino > 2:
            score -= 5

        # Max drawdown (higher = more risk)
        max_dd = metrics.get('max_drawdown', {}).get('max_drawdown', 0)
        if max_dd > 30:
            score += 20
        elif max_dd > 20:
            score += 10
        elif max_dd < 10:
            score -= 5

        # Beta (higher = more risk)
        beta = metrics.get('beta', 1.0)
        if beta > 1.5:
            score += 10
        elif beta < 0.5:
            score -= 10

        # Volatility
        volatility = metrics.get('volatility', 0.20)
        if volatility > 0.40:
            score += 15
        elif volatility < 0.15:
            score -= 5

        return max(0, min(100, score))

    async def _generate_expert_insights(self,
                                       symbol: str,
                                       price: float,
                                       metrics: Dict,
                                       context: Dict) -> Dict:
        """Use GPT-4 as risk management expert"""

        prompt = ChatPromptTemplate.from_messages([
            ("system", """You are Ray Dalio, legendary risk manager and founder of Bridgewater Associates.
Analyze risk with your principles:
1. Understand that losses are the price of admission
2. Diversification is the only free lunch
3. Risk parity - balance risk contributions
4. Prepare for what you don't expect
5. Know your downside scenarios

Provide expert risk analysis in the specified JSON format."""),
            ("human", """Analyze risk for {symbol} at ${price}:

Risk Metrics:
- Value at Risk (95%): ${var} ({var_pct}%)
- Conditional VaR (95%): ${cvar} ({cvar_pct}%)
- Sharpe Ratio: {sharpe}
- Sortino Ratio: {sortino}
- Maximum Drawdown: {max_dd}%
- Beta: {beta}
- Volatility: {volatility}%

Monte Carlo Projections (1 year):
- Expected: ${mc_expected}
- Pessimistic (5%): ${mc_pessimistic}
- Optimistic (95%): ${mc_optimistic}

Risk Score: {risk_score}/100

{format_instructions}

Provide risk assessment with position sizing recommendations.""")
        ])

        try:
            mc_data = metrics.get('monte_carlo', {})

            formatted_prompt = prompt.format_messages(
                symbol=symbol,
                price=price,
                var=metrics.get('var', {}).get('var', 'N/A'),
                var_pct=metrics.get('var', {}).get('var_percent', 'N/A'),
                cvar=metrics.get('cvar', {}).get('cvar', 'N/A'),
                cvar_pct=metrics.get('cvar', {}).get('cvar_percent', 'N/A'),
                sharpe=metrics.get('sharpe_ratio', 'N/A'),
                sortino=metrics.get('sortino_ratio', 'N/A'),
                max_dd=metrics.get('max_drawdown', {}).get('max_drawdown', 'N/A'),
                beta=metrics.get('beta', 'N/A'),
                volatility=round(metrics.get('volatility', 0) * 100, 2),
                mc_expected=mc_data.get('expected_price', 'N/A'),
                mc_pessimistic=mc_data.get('pessimistic', 'N/A'),
                mc_optimistic=mc_data.get('optimistic', 'N/A'),
                risk_score=metrics.get('risk_score', 50),
                format_instructions=self.output_parser.get_format_instructions()
            )

            response = await self.llm.ainvoke(formatted_prompt)
            parsed = self.output_parser.parse(response.content)

            return {
                'risk_assessment': parsed.risk_assessment,
                'downside_analysis': parsed.downside_analysis,
                'portfolio_impact': parsed.portfolio_impact,
                'risk_mitigation': parsed.risk_mitigation,
                'optimal_position_size': parsed.optimal_position_size,
                'risk_level': parsed.risk_level,
                'confidence_score': parsed.confidence_score
            }

        except Exception as e:
            logger.error(f"[{self.name}] LLM analysis failed: {e}")
            return self._rule_based_insights(metrics)

    def _rule_based_insights(self, metrics: Dict) -> Dict:
        """Fallback rule-based risk analysis"""

        risk_score = metrics.get('risk_score', 50)

        if risk_score > 70:
            risk_level = 'HIGH'
            assessment = 'High volatility and significant downside risk detected'
            position_size = 'Conservative: 2-5% of portfolio'
        elif risk_score > 50:
            risk_level = 'MEDIUM'
            assessment = 'Moderate risk with acceptable risk/reward'
            position_size = 'Moderate: 5-10% of portfolio'
        else:
            risk_level = 'LOW'
            assessment = 'Lower risk profile with stable characteristics'
            position_size = 'Standard: 10-15% of portfolio'

        return {
            'risk_assessment': assessment,
            'downside_analysis': f'VaR shows potential loss scenarios',
            'portfolio_impact': f'Risk score: {risk_score}/100',
            'risk_mitigation': 'Diversification and position sizing recommended',
            'optimal_position_size': position_size,
            'risk_level': risk_level,
            'confidence_score': 0.65
        }

    def _generate_dummy_returns(self, price: float) -> List[float]:
        """Generate dummy returns for fallback"""
        import random
        returns = []
        for _ in range(100):
            returns.append(random.gauss(0.0005, 0.02))  # Small positive drift with volatility
        return returns

    def _track_risk_lineage(self, symbol: str, price: float, risk_metrics: Dict, context: Dict):
        """Track data lineage for risk metrics"""

        # Track historical returns (source data)
        returns = context.get('returns', [])
        if returns:
            self.track_data(
                field_name='historical_returns',
                value=returns,
                source=DataSource.YFINANCE,
                reliability=DataReliability.HIGH,
                confidence=0.95,
                citation=f"Historical price returns calculated from Yahoo Finance data for {symbol}"
            )

        # Track VaR (Value at Risk)
        var_data = risk_metrics.get('var', {})
        if var_data.get('var'):
            self.track_calculated(
                field_name='var_95',
                value=var_data['var'],
                formula='VaR(95%): 5th percentile of return distribution',
                input_fields=['historical_returns'],
                confidence=0.85
            )

        # Track CVaR (Conditional VaR)
        cvar_data = risk_metrics.get('cvar', {})
        if cvar_data.get('cvar'):
            self.track_calculated(
                field_name='cvar_95',
                value=cvar_data['cvar'],
                formula='CVaR(95%): Expected loss beyond VaR threshold',
                input_fields=['historical_returns', 'var_95'],
                confidence=0.85
            )

        # Track Sharpe Ratio
        sharpe = risk_metrics.get('sharpe_ratio')
        if sharpe is not None:
            self.track_calculated(
                field_name='sharpe_ratio',
                value=sharpe,
                formula='Sharpe: (Mean Return - Risk Free Rate) / StdDev',
                input_fields=['historical_returns'],
                confidence=0.90
            )

        # Track Sortino Ratio
        sortino = risk_metrics.get('sortino_ratio')
        if sortino is not None:
            self.track_calculated(
                field_name='sortino_ratio',
                value=sortino,
                formula='Sortino: (Mean Return - Risk Free Rate) / Downside Deviation',
                input_fields=['historical_returns'],
                confidence=0.90
            )

        # Track Max Drawdown
        mdd_data = risk_metrics.get('max_drawdown', {})
        if mdd_data.get('max_drawdown'):
            self.track_calculated(
                field_name='max_drawdown',
                value=mdd_data['max_drawdown'],
                formula='Max Drawdown: Largest peak-to-trough decline',
                input_fields=['price_history'],
                confidence=0.92
            )

        # Track Beta
        beta = risk_metrics.get('beta')
        if beta is not None:
            self.track_data(
                field_name='beta',
                value=beta,
                source=DataSource.YFINANCE,
                reliability=DataReliability.HIGH,
                confidence=0.88,
                citation=f"Beta (market sensitivity) from Yahoo Finance for {symbol}"
            )

        # Track Volatility
        volatility = risk_metrics.get('volatility')
        if volatility is not None:
            self.track_calculated(
                field_name='volatility',
                value=volatility,
                formula='Annualized Volatility: StdDev(returns) * sqrt(252)',
                input_fields=['historical_returns'],
                confidence=0.93
            )

        # Track Monte Carlo simulation
        mc_data = risk_metrics.get('monte_carlo', {})
        if mc_data:
            self.track_calculated(
                field_name='monte_carlo_simulation',
                value=mc_data,
                formula='Monte Carlo: 10,000 simulated price paths over 252 days',
                input_fields=['price', 'expected_return', 'volatility'],
                confidence=0.70
            )

        logger.info(f"[{self.name}] Tracked lineage for {len(self.lineage_tracker.records)} risk data points")

    def _fallback_analysis(self, symbol: str) -> Dict:
        """Fallback analysis if everything fails"""

        return {
            'agent': self.name,
            'symbol': symbol,
            'summary': 'Risk analysis unavailable',
            'risk_level': 'medium',
            'risk_score': 50,
            'var_95': None,
            'sharpe_ratio': None,
            'beta': None,
            'volatility': None,
            'confidence': 0.3,
            'data_source': 'fallback',
            'timestamp': datetime.utcnow().isoformat()
        }
