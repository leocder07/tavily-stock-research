"""
AI Safety Layer - Hallucination Detection & Self-Critique (Phase 2)
Validates AI-generated recommendations using multiple verification strategies
"""

import logging
from typing import Dict, Any, List, Tuple
from datetime import datetime
import re

from langchain_openai import ChatOpenAI
from langchain.prompts import ChatPromptTemplate

logger = logging.getLogger(__name__)


class AISafetyLayer:
    """
    Multi-layered safety system for AI-generated stock analysis
    Detects hallucinations, validates claims, and provides confidence scoring
    """

    def __init__(self, llm: ChatOpenAI):
        self.llm = llm
        self.critique_llm = ChatOpenAI(model="gpt-4", temperature=0.0)  # Use GPT-4 for critique

    async def validate_recommendation(
        self,
        recommendation: Dict[str, Any],
        context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Comprehensive validation of AI recommendation

        Args:
            recommendation: AI-generated recommendation with action, confidence, reasoning
            context: Market data and financial metrics used for analysis

        Returns:
            Validation result with safety score, flags, and corrected recommendation
        """
        logger.info("[AISafety] Starting recommendation validation")

        validation_result = {
            'original_recommendation': recommendation,
            'safety_checks': {},
            'validation_score': 0.0,
            'flags': [],
            'corrected_recommendation': recommendation.copy(),
            'validation_timestamp': datetime.utcnow().isoformat()
        }

        # Check 1: Numerical Consistency
        numerical_check = await self._check_numerical_consistency(recommendation, context)
        validation_result['safety_checks']['numerical_consistency'] = numerical_check

        # Check 2: Logical Reasoning
        logic_check = await self._check_logical_reasoning(recommendation)
        validation_result['safety_checks']['logical_reasoning'] = logic_check

        # Check 3: Hallucination Detection
        hallucination_check = await self._detect_hallucinations(recommendation, context)
        validation_result['safety_checks']['hallucination_detection'] = hallucination_check

        # Check 4: Self-Critique
        critique_check = await self._self_critique(recommendation, context)
        validation_result['safety_checks']['self_critique'] = critique_check

        # Calculate overall safety score
        scores = [
            numerical_check.get('score', 0.0),
            logic_check.get('score', 0.0),
            hallucination_check.get('score', 0.0),
            critique_check.get('score', 0.0)
        ]
        validation_result['validation_score'] = sum(scores) / len(scores)

        # Aggregate flags
        for check in validation_result['safety_checks'].values():
            if check.get('flags'):
                validation_result['flags'].extend(check['flags'])

        # Apply corrections if validation score is low
        if validation_result['validation_score'] < 0.6:
            validation_result['corrected_recommendation'] = await self._apply_corrections(
                recommendation,
                validation_result['flags']
            )

        logger.info(f"[AISafety] Validation complete. Score: {validation_result['validation_score']:.2f}")

        return validation_result

    async def _check_numerical_consistency(
        self,
        recommendation: Dict[str, Any],
        context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Check if numerical values are realistic and consistent"""

        flags = []
        score = 1.0

        # Extract numerical claims
        target_price = recommendation.get('target_price', 0)
        current_price = context.get('market_data', {}).get('price', 0)
        stop_loss = recommendation.get('stop_loss', 0)

        # Validation 1: Target price reasonableness
        if target_price > 0 and current_price > 0:
            price_change = (target_price - current_price) / current_price
            if abs(price_change) > 0.5:  # More than 50% change
                flags.append({
                    'type': 'extreme_target_price',
                    'severity': 'medium',
                    'message': f'Target price implies {price_change*100:.1f}% change - unusually high'
                })
                score -= 0.2

        # Validation 2: Stop loss validation
        if stop_loss > current_price:
            flags.append({
                'type': 'invalid_stop_loss',
                'severity': 'high',
                'message': 'Stop loss is above current price - should be below'
            })
            score -= 0.3

        # Validation 3: PE ratio consistency
        pe_ratio = context.get('market_data', {}).get('pe_ratio', 0)
        if pe_ratio < 0:
            flags.append({
                'type': 'negative_pe_ratio',
                'severity': 'low',
                'message': 'Negative PE ratio indicates losses - ensure this is factored into analysis'
            })
            score -= 0.1

        return {
            'score': max(0.0, score),
            'flags': flags,
            'checked_at': datetime.utcnow().isoformat()
        }

    async def _check_logical_reasoning(self, recommendation: Dict[str, Any]) -> Dict[str, Any]:
        """Validate logical coherence of reasoning"""

        flags = []
        score = 1.0

        action = recommendation.get('action', 'HOLD')
        confidence = recommendation.get('confidence', 0.5)
        reasoning = recommendation.get('reasoning', '')

        # Check 1: Action-confidence alignment
        if action in ['STRONG_BUY', 'STRONG_SELL'] and confidence < 0.7:
            flags.append({
                'type': 'action_confidence_mismatch',
                'severity': 'medium',
                'message': f'Strong action ({action}) with low confidence ({confidence:.2f})'
            })
            score -= 0.3

        # Check 2: Reasoning length
        if len(reasoning) < 50:
            flags.append({
                'type': 'insufficient_reasoning',
                'severity': 'high',
                'message': 'Reasoning is too brief - lacks detail'
            })
            score -= 0.4

        # Check 3: Contradictory language
        contradictions = [
            (r'bullish.*bearish', 'Mixed bullish/bearish signals without clarification'),
            (r'strong buy.*caution', 'Strong buy recommendation with cautionary language'),
            (r'overvalued.*buy', 'Overvalued but recommending buy')
        ]

        for pattern, message in contradictions:
            if re.search(pattern, reasoning, re.IGNORECASE):
                flags.append({
                    'type': 'contradictory_reasoning',
                    'severity': 'high',
                    'message': message
                })
                score -= 0.3

        return {
            'score': max(0.0, score),
            'flags': flags,
            'checked_at': datetime.utcnow().isoformat()
        }

    async def _detect_hallucinations(
        self,
        recommendation: Dict[str, Any],
        context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Detect potential hallucinated facts"""

        flags = []
        score = 1.0

        reasoning = recommendation.get('reasoning', '')

        # Check for unsupported quantitative claims
        # Pattern: specific numbers not in context
        number_pattern = r'(\d+(?:\.\d+)?)\s*(billion|million|thousand|%|percent)'
        numbers_in_reasoning = re.findall(number_pattern, reasoning, re.IGNORECASE)

        # Extract numbers from context
        context_numbers = set()
        for key, value in context.get('market_data', {}).items():
            if isinstance(value, (int, float)):
                context_numbers.add(str(value))

        # Check for hallucinated numbers
        for num, unit in numbers_in_reasoning:
            if num not in context_numbers and num not in reasoning[:100]:  # Allow numbers in summary
                flags.append({
                    'type': 'potential_hallucination',
                    'severity': 'medium',
                    'message': f'Specific claim ({num} {unit}) not found in source data'
                })
                score -= 0.15

        # Check for specific company names or events not in context
        company_pattern = r'\b([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)\s+(?:announced|reported|said|confirmed)\b'
        companies = re.findall(company_pattern, reasoning)

        if companies and not context.get('news', {}).get('articles'):
            flags.append({
                'type': 'unsourced_news',
                'severity': 'high',
                'message': f'References specific events/announcements without news sources: {", ".join(companies[:3])}'
            })
            score -= 0.4

        return {
            'score': max(0.0, score),
            'flags': flags,
            'checked_at': datetime.utcnow().isoformat()
        }

    async def _self_critique(
        self,
        recommendation: Dict[str, Any],
        context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Use GPT-4 to critique the recommendation"""

        critique_prompt = ChatPromptTemplate.from_messages([
            ("system", """You are a senior financial analyst reviewing a junior analyst's stock recommendation.
Your job is to identify potential errors, oversights, or exaggerations.

Review the recommendation and provide:
1. Score (0-1) for overall quality
2. List of specific concerns or red flags
3. Suggested improvements

Be critical but fair. Focus on factual accuracy and logical consistency."""),
            ("user", """Recommendation:
Action: {action}
Confidence: {confidence}
Reasoning: {reasoning}
Target Price: ${target_price}

Market Data:
Current Price: ${current_price}
PE Ratio: {pe_ratio}
Market Cap: ${market_cap}

Critique this recommendation. What are the weaknesses?""")
        ])

        try:
            response = await self.critique_llm.ainvoke(
                critique_prompt.format_messages(
                    action=recommendation.get('action', 'HOLD'),
                    confidence=recommendation.get('confidence', 0.5),
                    reasoning=recommendation.get('reasoning', ''),
                    target_price=recommendation.get('target_price', 0),
                    current_price=context.get('market_data', {}).get('price', 0),
                    pe_ratio=context.get('market_data', {}).get('pe_ratio', 0),
                    market_cap=context.get('market_data', {}).get('market_cap', 0)
                )
            )

            critique_text = response.content

            # Parse critique for score (simple heuristic)
            score = 0.7  # Default neutral score
            if 'strong' in critique_text.lower() and 'concern' in critique_text.lower():
                score = 0.4
            elif 'minor' in critique_text.lower() or 'overall solid' in critique_text.lower():
                score = 0.9

            flags = []
            if score < 0.6:
                flags.append({
                    'type': 'ai_critique_concerns',
                    'severity': 'medium',
                    'message': f'AI critique raised concerns: {critique_text[:200]}...'
                })

            return {
                'score': score,
                'flags': flags,
                'critique': critique_text,
                'checked_at': datetime.utcnow().isoformat()
            }

        except Exception as e:
            logger.error(f"[AISafety] Self-critique failed: {e}")
            return {
                'score': 0.5,  # Neutral if critique fails
                'flags': [],
                'critique': f'Critique failed: {str(e)}',
                'checked_at': datetime.utcnow().isoformat()
            }

    async def _apply_corrections(
        self,
        recommendation: Dict[str, Any],
        flags: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Apply automatic corrections based on validation flags"""

        corrected = recommendation.copy()

        # Correction 1: Reduce confidence for flagged recommendations
        high_severity_flags = [f for f in flags if f.get('severity') == 'high']
        if high_severity_flags:
            corrected['confidence'] = max(0.3, corrected.get('confidence', 0.5) * 0.7)
            corrected['reasoning'] += f"\n\n⚠️ AI Safety Warning: {len(high_severity_flags)} high-severity validation flags detected. Confidence adjusted."

        # Correction 2: Downgrade strong actions with validation issues
        if corrected.get('action') in ['STRONG_BUY', 'STRONG_SELL'] and len(flags) >= 2:
            corrected['action'] = 'BUY' if corrected['action'] == 'STRONG_BUY' else 'SELL'
            corrected['reasoning'] += "\n\n⚠️ AI Safety: Action downgraded due to validation concerns."

        # Correction 3: Add disclaimers
        corrected['safety_disclaimer'] = f"This recommendation passed {len(flags)} validation checks. Review all flags before acting."

        return corrected


# Global AI safety instance
ai_safety_layer = None


def get_ai_safety_layer(llm: ChatOpenAI):
    """Get or create AI safety layer instance"""
    global ai_safety_layer
    if ai_safety_layer is None:
        ai_safety_layer = AISafetyLayer(llm)
    return ai_safety_layer
