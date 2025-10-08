"""Risk Assessment Agent - Evaluates investment risks using Tavily"""

from typing import Dict, Any, List
import logging
from datetime import datetime
from agents.base_agent import BaseFinancialAgent, AgentState

logger = logging.getLogger(__name__)


class RiskAgent(BaseFinancialAgent):
    """Agent for assessing investment risks"""

    def __init__(self, agent_id: str, agent_type: str, tavily_client=None):
        super().__init__(agent_id, agent_type, tavily_client)

    async def execute(self, context: Dict[str, Any]) -> AgentState:
        """Assess risks for specified stocks

        Args:
            context: Contains 'stock_symbols' and 'market_data'

        Returns:
            AgentState with risk assessment
        """
        try:
            symbols = context.get('stock_symbols', [])
            market_data = context.get('market_data', {})

            if not symbols:
                raise ValueError("No stock symbols provided")

            logger.info(f"Assessing risks for {symbols}")

            risk_data = {}

            for symbol in symbols:
                assessment = await self._assess_stock_risk(symbol, market_data)
                risk_data[symbol] = assessment

            output_data = {
                'stocks': risk_data,
                'overall_risk_level': self._calculate_overall_risk(risk_data),
                'main_risks': self._identify_main_risks(risk_data),
                'mitigation_strategies': self._suggest_mitigations(risk_data),
                'timestamp': datetime.utcnow().isoformat()
            }

            self.state.output_data = output_data
            self.state.confidence_score = 0.75

            logger.info("Risk assessment complete")
            return self.state

        except Exception as e:
            logger.error(f"Risk assessment failed: {str(e)}")
            self.state.error_message = str(e)
            self.state.status = "FAILED"
            return self.state

    async def _assess_stock_risk(self, symbol: str, market_data: Dict) -> Dict:
        """Assess risks for a single stock"""
        
        # Search for risk factors
        query = f"{symbol} stock risks volatility debt bankruptcy lawsuit regulatory competition"
        results = await self.search_tavily(query, search_depth="advanced", max_results=4)
        
        assessment = {
            'risk_level': 'medium',
            'volatility_risk': 'medium',
            'market_risk': 'medium',
            'business_risk': 'medium',
            'financial_risk': 'medium',
            'regulatory_risk': 'low',
            'specific_risks': []
        }
        
        if results:
            self.state.citations.extend(self.extract_citations(results))
            # Extract risk information
            for result in results:
                content = result.get('content', '').lower()
                if 'high risk' in content or 'significant risk' in content:
                    assessment['risk_level'] = 'high'
                if 'volatility' in content or 'volatile' in content:
                    assessment['volatility_risk'] = 'high'
                if 'lawsuit' in content or 'litigation' in content:
                    assessment['specific_risks'].append('Legal/litigation risk')
                if 'regulatory' in content or 'regulation' in content:
                    assessment['regulatory_risk'] = 'medium'
        
        return assessment

    def _calculate_overall_risk(self, risk_data: Dict) -> str:
        """Calculate overall portfolio risk level"""
        risk_scores = {'low': 1, 'medium': 2, 'high': 3}
        total_score = 0
        count = 0
        
        for symbol, assessment in risk_data.items():
            if isinstance(assessment, dict) and 'risk_level' in assessment:
                total_score += risk_scores.get(assessment['risk_level'], 2)
                count += 1
        
        avg_score = total_score / count if count > 0 else 2
        
        if avg_score <= 1.5:
            return 'low'
        elif avg_score <= 2.5:
            return 'medium'
        else:
            return 'high'

    def _identify_main_risks(self, risk_data: Dict) -> List[str]:
        """Identify main portfolio risks"""
        main_risks = set()
        
        for symbol, assessment in risk_data.items():
            if isinstance(assessment, dict):
                if assessment.get('volatility_risk') == 'high':
                    main_risks.add('High market volatility')
                if assessment.get('financial_risk') == 'high':
                    main_risks.add('Financial stability concerns')
                for risk in assessment.get('specific_risks', []):
                    main_risks.add(risk)
        
        return list(main_risks)[:5]

    def _suggest_mitigations(self, risk_data: Dict) -> List[str]:
        """Suggest risk mitigation strategies"""
        strategies = []
        
        overall_risk = self._calculate_overall_risk(risk_data)
        
        if overall_risk == 'high':
            strategies.append('Consider diversifying portfolio')
            strategies.append('Use stop-loss orders')
            strategies.append('Reduce position sizes')
        elif overall_risk == 'medium':
            strategies.append('Monitor positions regularly')
            strategies.append('Set price alerts')
        
        strategies.append('Review risk tolerance periodically')
        
        return strategies
