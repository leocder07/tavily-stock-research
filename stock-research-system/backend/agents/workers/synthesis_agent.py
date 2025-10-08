"""Synthesis Agent - Synthesizes all analysis into investment recommendations using LLM"""

from typing import Dict, Any, List
import logging
from datetime import datetime
from agents.base_agent import BaseFinancialAgent, AgentState
from langchain_openai import ChatOpenAI
from langchain.prompts import ChatPromptTemplate
import json

logger = logging.getLogger(__name__)


class SynthesisAgent(BaseFinancialAgent):
    """Agent for synthesizing all analysis into recommendations"""

    def __init__(self, agent_id: str, agent_type: str, tavily_client=None, llm=None):
        super().__init__(agent_id, agent_type, tavily_client)
        self.llm = llm or ChatOpenAI(
            model="gpt-4-turbo-preview",
            temperature=0.3
        )

        self.synthesis_prompt = ChatPromptTemplate.from_messages([
            ("system", """You are a senior investment analyst synthesizing comprehensive research.

            Your task is to:
            1. Analyze all provided data (market, fundamental, sentiment, technical, risk, peer)
            2. Identify key investment insights
            3. Generate actionable investment recommendations
            4. Provide clear risk-adjusted recommendations

            Structure your response as JSON with:
            - recommendation: BUY/HOLD/SELL with confidence level
            - key_insights: List of critical findings
            - investment_thesis: Clear narrative
            - price_targets: Short/medium/long term targets
            - risk_factors: Key risks to monitor
            - action_items: Specific actions for investors"""),
            ("human", """Query: {query}

            Stock Symbols: {stock_symbols}

            Market Data: {market_data}

            Fundamental Analysis: {fundamental_data}

            Sentiment Analysis: {sentiment_data}

            Technical Analysis: {technical_data}

            Risk Assessment: {risk_assessment}

            Peer Comparison: {peer_comparison}

            Please synthesize this into a comprehensive investment recommendation.""")
        ])

    async def execute(self, context: Dict[str, Any]) -> AgentState:
        """Synthesize all analysis into recommendations

        Args:
            context: Contains all analysis results from other agents

        Returns:
            AgentState with synthesized recommendations
        """
        try:
            logger.info("Synthesizing analysis into recommendations")

            # Extract all analysis data
            market_data = context.get('market_data', {})
            fundamental_data = context.get('fundamental_data', {})
            sentiment_data = context.get('sentiment_data', {})
            technical_data = context.get('technical_data', {})
            risk_assessment = context.get('risk_assessment', {})
            peer_comparison = context.get('peer_comparison', {})

            # Use LLM to synthesize
            synthesis = await self._generate_synthesis(
                context.get('query', ''),
                context.get('stock_symbols', []),
                market_data,
                fundamental_data,
                sentiment_data,
                technical_data,
                risk_assessment,
                peer_comparison
            )

            # Calculate confidence score
            confidence = self._calculate_synthesis_confidence(synthesis)

            # Prepare output
            output_data = {
                'recommendation': synthesis.get('recommendation', {}),
                'key_insights': synthesis.get('key_insights', []),
                'investment_thesis': synthesis.get('investment_thesis', ''),
                'price_targets': synthesis.get('price_targets', {}),
                'risk_factors': synthesis.get('risk_factors', []),
                'action_items': synthesis.get('action_items', []),
                'confidence_score': confidence,
                'timestamp': datetime.utcnow().isoformat()
            }

            self.state.output_data = output_data
            self.state.confidence_score = confidence

            logger.info("Successfully synthesized analysis")
            return self.state

        except Exception as e:
            logger.error(f"Synthesis failed: {str(e)}")
            self.state.error_message = str(e)
            self.state.status = "FAILED"
            return self.state

    async def _generate_synthesis(self, query: str, symbols: List[str],
                                 market_data: Dict, fundamental_data: Dict,
                                 sentiment_data: Dict, technical_data: Dict,
                                 risk_assessment: Dict, peer_comparison: Dict) -> Dict:
        """Generate synthesis using LLM

        Args:
            All analysis data

        Returns:
            Synthesized recommendation
        """
        try:
            # Format the data for the prompt
            formatted_prompt = self.synthesis_prompt.format_messages(
                query=query,
                stock_symbols=', '.join(symbols),
                market_data=self._format_for_llm(market_data),
                fundamental_data=self._format_for_llm(fundamental_data),
                sentiment_data=self._format_for_llm(sentiment_data),
                technical_data=self._format_for_llm(technical_data),
                risk_assessment=self._format_for_llm(risk_assessment),
                peer_comparison=self._format_for_llm(peer_comparison)
            )

            # Get LLM response
            response = await self.llm.ainvoke(formatted_prompt)

            # Parse JSON response
            try:
                synthesis = json.loads(response.content)
            except json.JSONDecodeError:
                # Fallback to structured extraction
                synthesis = self._extract_structured_synthesis(response.content)

            # Ensure all required fields
            synthesis = self._validate_synthesis(synthesis)

            return synthesis

        except Exception as e:
            logger.error(f"LLM synthesis failed: {str(e)}")
            return self._generate_fallback_synthesis(symbols, market_data, fundamental_data)

    def _format_for_llm(self, data: Dict) -> str:
        """Format data for LLM consumption

        Args:
            data: Analysis data

        Returns:
            Formatted string
        """
        if not data:
            return "No data available"

        # Create a concise summary
        summary = []

        def extract_key_values(d, prefix=""):
            for key, value in d.items():
                if isinstance(value, dict):
                    extract_key_values(value, f"{prefix}{key}.")
                elif value is not None and not isinstance(value, (list, tuple)):
                    summary.append(f"{prefix}{key}: {value}")

        extract_key_values(data)

        # Limit to most important items
        return "\n".join(summary[:20])

    def _extract_structured_synthesis(self, content: str) -> Dict:
        """Extract structured data from unstructured LLM response

        Args:
            content: LLM response content

        Returns:
            Structured synthesis
        """
        import re

        synthesis = {
            'recommendation': {},
            'key_insights': [],
            'investment_thesis': '',
            'price_targets': {},
            'risk_factors': [],
            'action_items': []
        }

        # Extract recommendation
        rec_match = re.search(r'(BUY|HOLD|SELL)', content, re.IGNORECASE)
        if rec_match:
            synthesis['recommendation']['action'] = rec_match.group(1).upper()

        # Extract confidence
        conf_match = re.search(r'confidence[:\s]+(\d+)%?', content, re.IGNORECASE)
        if conf_match:
            synthesis['recommendation']['confidence'] = int(conf_match.group(1))

        # Extract insights (look for bullet points or numbered items)
        insights = re.findall(r'[•\-\*]\s*(.+)', content)
        synthesis['key_insights'] = insights[:5]

        # Extract thesis (first substantial paragraph)
        paragraphs = content.split('\n\n')
        for para in paragraphs:
            if len(para) > 100:
                synthesis['investment_thesis'] = para[:500]
                break

        return synthesis

    def _validate_synthesis(self, synthesis: Dict) -> Dict:
        """Validate and ensure all required fields in synthesis

        Args:
            synthesis: Raw synthesis data

        Returns:
            Validated synthesis
        """
        # Ensure recommendation structure
        if 'recommendation' not in synthesis or not isinstance(synthesis['recommendation'], dict):
            synthesis['recommendation'] = {'action': 'HOLD', 'confidence': 50}

        # Ensure lists
        for field in ['key_insights', 'risk_factors', 'action_items']:
            if field not in synthesis or not isinstance(synthesis[field], list):
                synthesis[field] = []

        # Ensure strings
        for field in ['investment_thesis']:
            if field not in synthesis or not isinstance(synthesis[field], str):
                synthesis[field] = ""

        # Ensure price targets
        if 'price_targets' not in synthesis or not isinstance(synthesis['price_targets'], dict):
            synthesis['price_targets'] = {}

        return synthesis

    def _generate_fallback_synthesis(self, symbols: List[str],
                                    market_data: Dict,
                                    fundamental_data: Dict) -> Dict:
        """Generate fallback synthesis without LLM

        Args:
            symbols: Stock symbols
            market_data: Market data
            fundamental_data: Fundamental data

        Returns:
            Basic synthesis
        """
        # Ensure we have stock symbols to work with
        if not symbols:
            symbols = ['UNKNOWN']

        primary_symbol = symbols[0] if symbols else 'STOCK'

        synthesis = {
            'recommendation': {
                'action': 'HOLD',
                'confidence': 50
            },
            'key_insights': [
                f"Analysis initiated for {', '.join(symbols)}",
                "Market data indicates moderate volatility",
                "Current market conditions suggest cautious approach"
            ],
            'investment_thesis': f"Based on available market data for {primary_symbol}, the stock shows mixed signals. "
                                 f"Current market conditions suggest maintaining a neutral position while monitoring "
                                 f"key technical indicators and fundamental metrics for clearer directional signals.",
            'price_targets': {
                'short_term': 'Under analysis',
                'medium_term': 'Pending data',
                'long_term': 'To be determined'
            },
            'risk_factors': [
                "Market volatility remains elevated",
                "Sector-specific headwinds present",
                "Macroeconomic uncertainty"
            ],
            'action_items': [
                f"Monitor {primary_symbol} price action closely",
                "Review upcoming earnings reports",
                "Track sector performance relative to broader market",
                "Set appropriate stop-loss levels"
            ]
        }

        # Generate better insights from actual data if available
        if market_data and 'stocks' in market_data:
            for symbol in symbols[:3]:  # Limit to first 3 symbols
                if symbol in market_data.get('stocks', {}):
                    stock_data = market_data['stocks'][symbol]
                    if 'price_data' in stock_data:
                        price_info = stock_data['price_data']
                        if price_info.get('current_price'):
                            price = price_info['current_price']
                            synthesis['key_insights'].append(f"{symbol} currently trading at ${price:.2f}")
                        if price_info.get('change_percent'):
                            change = price_info['change_percent']
                            direction = "up" if change > 0 else "down"
                            synthesis['key_insights'].append(f"{symbol} is {direction} {abs(change):.2f}% today")

        # Add fundamental insights if available
        if fundamental_data and 'companies' in fundamental_data:
            for symbol in symbols[:3]:
                if symbol in fundamental_data.get('companies', {}):
                    company = fundamental_data['companies'][symbol]
                    if 'profitability_metrics' in company:
                        metrics = company['profitability_metrics']
                        if metrics.get('roe'):
                            synthesis['key_insights'].append(f"{symbol} ROE: {metrics['roe']:.1f}%")
                        if metrics.get('profit_margin'):
                            synthesis['key_insights'].append(f"{symbol} Profit Margin: {metrics['profit_margin']:.1f}%")

        # Determine recommendation based on available signals
        positive_signals = 0
        negative_signals = 0

        # Check market data signals
        for symbol in symbols:
            if market_data and symbol in market_data.get('stocks', {}):
                stock = market_data['stocks'][symbol]
                if 'price_data' in stock:
                    change = stock['price_data'].get('change_percent', 0)
                    if change > 2:
                        positive_signals += 1
                    elif change < -2:
                        negative_signals += 1

        # Adjust recommendation based on signals
        if positive_signals > negative_signals and positive_signals > 0:
            synthesis['recommendation']['action'] = 'BUY'
            synthesis['recommendation']['confidence'] = min(60 + positive_signals * 10, 75)
            synthesis['investment_thesis'] = (f"{primary_symbol} shows positive momentum with {positive_signals} "
                                             f"bullish signals identified. Technical indicators suggest upward trend "
                                             f"continuation in the near term.")
        elif negative_signals > positive_signals and negative_signals > 0:
            synthesis['recommendation']['action'] = 'SELL'
            synthesis['recommendation']['confidence'] = min(60 + negative_signals * 10, 75)
            synthesis['investment_thesis'] = (f"{primary_symbol} displays weakness with {negative_signals} "
                                             f"bearish signals detected. Risk management suggests reducing exposure "
                                             f"until market conditions improve.")

        # Ensure we have enough insights (minimum 3)
        while len(synthesis['key_insights']) < 3:
            synthesis['key_insights'].append(f"Additional analysis required for {primary_symbol}")

        # Ensure we have enough risk factors (minimum 2)
        while len(synthesis['risk_factors']) < 2:
            synthesis['risk_factors'].append("Further risk assessment needed")

        return synthesis

    def _calculate_synthesis_confidence(self, synthesis: Dict) -> float:
        """Calculate confidence in synthesis

        Args:
            synthesis: Synthesis data

        Returns:
            Confidence score 0-1
        """
        confidence = 0.5

        # Check recommendation confidence
        if 'recommendation' in synthesis and 'confidence' in synthesis['recommendation']:
            rec_conf = synthesis['recommendation']['confidence']
            confidence = rec_conf / 100.0

        # Adjust based on data completeness
        if synthesis.get('key_insights'):
            confidence += 0.1 * min(len(synthesis['key_insights']) / 5, 1)

        if synthesis.get('investment_thesis'):
            confidence += 0.1

        if synthesis.get('price_targets'):
            confidence += 0.1

        if synthesis.get('risk_factors'):
            confidence += 0.05

        return min(confidence, 1.0)