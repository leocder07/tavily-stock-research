"""Critique Agent - Reviews and validates synthesis quality using LLM"""

from typing import Dict, Any, List
import logging
from datetime import datetime
from agents.base_agent import BaseFinancialAgent, AgentState
from langchain_openai import ChatOpenAI
from langchain.prompts import ChatPromptTemplate
import json

logger = logging.getLogger(__name__)


class CritiqueAgent(BaseFinancialAgent):
    """Agent for critiquing and validating synthesis quality"""

    def __init__(self, agent_id: str, agent_type: str, tavily_client=None, llm=None):
        super().__init__(agent_id, agent_type, tavily_client)
        self.llm = llm or ChatOpenAI(
            model="gpt-4-turbo-preview",
            temperature=0.2  # Low temperature for consistent critique
        )

        self.critique_prompt = ChatPromptTemplate.from_messages([
            ("system", """You are a senior investment review committee member.

            Your role is to critically evaluate investment recommendations for:
            1. Completeness - Are all important factors considered?
            2. Accuracy - Is the analysis factually correct?
            3. Logic - Is the reasoning sound?
            4. Actionability - Are recommendations clear and executable?
            5. Risk Assessment - Are risks properly identified and weighted?

            Return JSON with:
            - quality_pass: boolean (true if meets standards)
            - confidence_adjustment: float (-0.3 to 0.3)
            - critical_issues: list of major problems
            - missing_analysis: list of missing components
            - strengths: list of strong points
            - improvement_suggestions: specific improvements needed
            - revision_priority: HIGH/MEDIUM/LOW/NONE"""),
            ("human", """Please critique this investment analysis:

            SYNTHESIS:
            {synthesis}

            CONFIDENCE SCORE: {confidence_score}

            SUPPORTING DATA QUALITY:
            Market Data: {market_data_quality}
            Fundamental Data: {fundamental_data_quality}
            Sentiment Data: {sentiment_data_quality}
            Technical Data: {technical_data_quality}
            Risk Data: {risk_data_quality}

            Provide a thorough critique.""")
        ])

    async def execute(self, context: Dict[str, Any]) -> AgentState:
        """Critique the synthesis quality

        Args:
            context: Contains synthesis and all agent results

        Returns:
            AgentState with critique
        """
        try:
            logger.info("Critiquing synthesis quality")

            synthesis = context.get('synthesis', {})
            confidence_score = context.get('confidence_score', 0.5)
            agent_results = context.get('agent_results', {})

            # Log the synthesis data for debugging
            logger.info(f"Synthesis data keys: {list(synthesis.keys()) if synthesis else 'empty'}")
            logger.info(f"Synthesis recommendation: {synthesis.get('recommendation', 'missing')}")
            logger.info(f"Synthesis confidence: {confidence_score}")

            # Evaluate data quality from each agent
            data_quality = self._evaluate_data_quality(agent_results)

            # Generate critique using LLM
            critique = await self._generate_critique(
                synthesis,
                confidence_score,
                data_quality
            )

            # Determine if revision is needed
            quality_pass = critique.get('quality_pass', False)
            critical_issues = critique.get('critical_issues', [])

            # Prepare output
            output_data = {
                'quality_pass': quality_pass,
                'confidence_adjustment': critique.get('confidence_adjustment', 0),
                'critical_issues': critical_issues,
                'missing_analysis': critique.get('missing_analysis', []),
                'strengths': critique.get('strengths', []),
                'improvement_suggestions': critique.get('improvement_suggestions', []),
                'revision_priority': critique.get('revision_priority', 'NONE'),
                'overall_assessment': self._generate_assessment_summary(critique),
                'timestamp': datetime.utcnow().isoformat()
            }

            self.state.output_data = output_data
            self.state.confidence_score = self._calculate_critique_confidence(critique)

            logger.info(f"Critique complete - Quality Pass: {quality_pass}")
            return self.state

        except Exception as e:
            logger.error(f"Critique failed: {str(e)}")
            self.state.error_message = str(e)
            self.state.status = "FAILED"
            return self.state

    async def _generate_critique(self, synthesis: Dict, confidence: float,
                                data_quality: Dict) -> Dict:
        """Generate critique using LLM

        Args:
            synthesis: Synthesis to critique
            confidence: Current confidence score
            data_quality: Quality metrics for each data source

        Returns:
            Critique results
        """
        try:
            # Format the critique prompt
            formatted_prompt = self.critique_prompt.format_messages(
                synthesis=json.dumps(synthesis, indent=2)[:2000],  # Limit size
                confidence_score=confidence,
                market_data_quality=data_quality.get('market_data', 'unknown'),
                fundamental_data_quality=data_quality.get('fundamental', 'unknown'),
                sentiment_data_quality=data_quality.get('sentiment', 'unknown'),
                technical_data_quality=data_quality.get('technical', 'unknown'),
                risk_data_quality=data_quality.get('risk', 'unknown')
            )

            # Get LLM critique
            response = await self.llm.ainvoke(formatted_prompt)

            # Parse JSON response
            try:
                critique = json.loads(response.content)
            except json.JSONDecodeError:
                # Fallback to rule-based critique
                critique = self._generate_rule_based_critique(synthesis, confidence, data_quality)

            # Validate critique structure
            critique = self._validate_critique(critique)

            return critique

        except Exception as e:
            logger.error(f"LLM critique failed: {str(e)}")
            return self._generate_rule_based_critique(synthesis, confidence, data_quality)

    def _generate_rule_based_critique(self, synthesis: Dict, confidence: float,
                                     data_quality: Dict) -> Dict:
        """Generate critique using rules when LLM fails

        Args:
            synthesis: Synthesis to critique
            confidence: Current confidence score
            data_quality: Quality metrics

        Returns:
            Rule-based critique
        """
        critique = {
            'quality_pass': True,
            'confidence_adjustment': 0,
            'critical_issues': [],
            'missing_analysis': [],
            'strengths': [],
            'improvement_suggestions': [],
            'revision_priority': 'NONE'
        }

        # Check for critical missing components with proper validation
        recommendation = synthesis.get('recommendation', {})
        if not recommendation or (isinstance(recommendation, dict) and not recommendation.get('action')):
            critique['critical_issues'].append("No clear recommendation provided")
            critique['quality_pass'] = False
            critique['revision_priority'] = 'HIGH'

        # Check key_insights - must have at least 2 insights
        key_insights = synthesis.get('key_insights', [])
        if not key_insights or len(key_insights) < 2:
            critique['missing_analysis'].append("Insufficient key insights identified")
            critique['confidence_adjustment'] -= 0.1

        # Check risk_factors - at least 1 risk factor required
        risk_factors = synthesis.get('risk_factors', [])
        if not risk_factors:
            critique['missing_analysis'].append("Risk factors not identified")
            critique['confidence_adjustment'] -= 0.1

        # Check confidence level - be more lenient
        if confidence < 0.3:  # Lowered from 0.5
            critique['critical_issues'].append("Very low confidence in analysis")
            critique['quality_pass'] = False
            critique['revision_priority'] = 'MEDIUM'

        # Check data quality - be more lenient
        low_quality_sources = [k for k, v in data_quality.items() if v == 'low']
        if len(low_quality_sources) > 3:  # Increased from 2
            critique['critical_issues'].append(f"Poor data quality from: {', '.join(low_quality_sources)}")
            critique['confidence_adjustment'] -= 0.2
            critique['quality_pass'] = False

        # Identify strengths
        if synthesis.get('investment_thesis'):
            critique['strengths'].append("Clear investment thesis provided")

        if synthesis.get('price_targets'):
            critique['strengths'].append("Price targets established")

        if len(key_insights) >= 3:
            critique['strengths'].append("Comprehensive insights identified")

        if len(risk_factors) >= 2:
            critique['strengths'].append("Risk factors well documented")

        # Generate improvement suggestions
        if confidence < 0.7:
            critique['improvement_suggestions'].append("Gather additional data to improve confidence")

        action_items = synthesis.get('action_items', [])
        if not action_items:
            critique['improvement_suggestions'].append("Add specific action items for investors")

        # Be more lenient with quality pass
        # Only fail if there are critical issues
        if len(critique['critical_issues']) == 0:
            critique['quality_pass'] = True

        # Determine final revision priority
        if len(critique['critical_issues']) > 2:
            critique['revision_priority'] = 'HIGH'
        elif len(critique['critical_issues']) > 0:
            critique['revision_priority'] = 'MEDIUM'
        elif len(critique['improvement_suggestions']) > 2:
            critique['revision_priority'] = 'LOW'
        else:
            critique['revision_priority'] = 'NONE'

        return critique

    def _evaluate_data_quality(self, agent_results: Dict[str, Any]) -> Dict[str, str]:
        """Evaluate quality of data from each agent

        Args:
            agent_results: Results from all agents

        Returns:
            Quality assessment for each data source
        """
        quality = {}

        quality_thresholds = {
            'high': 0.7,
            'medium': 0.5,
            'low': 0.3
        }

        # Evaluate each agent's data quality
        for agent_name, agent_state in agent_results.items():
            if hasattr(agent_state, 'confidence_score'):
                score = agent_state.confidence_score
            elif isinstance(agent_state, dict) and 'confidence_score' in agent_state:
                score = agent_state['confidence_score']
            else:
                score = 0.5

            if score >= quality_thresholds['high']:
                quality[agent_name] = 'high'
            elif score >= quality_thresholds['medium']:
                quality[agent_name] = 'medium'
            else:
                quality[agent_name] = 'low'

        return quality

    def _validate_critique(self, critique: Dict) -> Dict:
        """Validate critique structure

        Args:
            critique: Raw critique

        Returns:
            Validated critique
        """
        # Ensure boolean fields
        if 'quality_pass' not in critique or not isinstance(critique['quality_pass'], bool):
            critique['quality_pass'] = True

        # Ensure numeric fields
        if 'confidence_adjustment' not in critique or not isinstance(critique['confidence_adjustment'], (int, float)):
            critique['confidence_adjustment'] = 0
        else:
            # Clamp to valid range
            critique['confidence_adjustment'] = max(-0.3, min(0.3, critique['confidence_adjustment']))

        # Ensure list fields
        list_fields = ['critical_issues', 'missing_analysis', 'strengths', 'improvement_suggestions']
        for field in list_fields:
            if field not in critique or not isinstance(critique[field], list):
                critique[field] = []

        # Ensure revision priority
        valid_priorities = ['HIGH', 'MEDIUM', 'LOW', 'NONE']
        if 'revision_priority' not in critique or critique['revision_priority'] not in valid_priorities:
            critique['revision_priority'] = 'NONE'

        return critique

    def _generate_assessment_summary(self, critique: Dict) -> str:
        """Generate summary of the critique

        Args:
            critique: Critique results

        Returns:
            Summary string
        """
        if critique.get('quality_pass'):
            if len(critique.get('strengths', [])) > 3:
                return "Excellent analysis with strong supporting evidence"
            else:
                return "Analysis meets quality standards"
        else:
            issues = len(critique.get('critical_issues', []))
            if issues > 2:
                return "Significant issues require immediate revision"
            elif issues > 0:
                return "Critical issues identified - revision recommended"
            else:
                return "Quality standards not met - improvements needed"

    def _calculate_critique_confidence(self, critique: Dict) -> float:
        """Calculate confidence in the critique

        Args:
            critique: Critique results

        Returns:
            Confidence score 0-1
        """
        confidence = 0.7  # Base confidence in critique

        # Adjust based on critique completeness
        if critique.get('critical_issues'):
            confidence += 0.05 * min(len(critique['critical_issues']), 3)

        if critique.get('strengths'):
            confidence += 0.05 * min(len(critique['strengths']), 3)

        if critique.get('improvement_suggestions'):
            confidence += 0.05

        # Reduce confidence if quality fails
        if not critique.get('quality_pass'):
            confidence -= 0.1

        return max(0.3, min(1.0, confidence))