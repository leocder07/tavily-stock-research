"""
Integration module for ConsensusEngine with ExpertSynthesisAgent
Shows how to integrate consensus engine into the synthesis workflow
"""

import logging
from typing import Dict, Any
from services.consensus_engine import ConsensusEngine, ConsensusResult

logger = logging.getLogger(__name__)


class ConsensusIntegration:
    """
    Integration layer between ConsensusEngine and ExpertSynthesisAgent
    """

    def __init__(self):
        self.consensus_engine = ConsensusEngine()

    async def enhance_synthesis_with_consensus(
        self,
        analyses: Dict[str, Any],
        symbol: str,
        price: float
    ) -> Dict[str, Any]:
        """
        Enhance synthesis with consensus recommendation

        This method should be called from ExpertSynthesisAgent.synthesize()
        after collecting all agent analyses but before final LLM synthesis

        Args:
            analyses: Dict of all agent analyses
            symbol: Stock symbol
            price: Current price

        Returns:
            Enhanced analysis dict with consensus data
        """
        logger.info(f"[ConsensusIntegration] Calculating consensus for {symbol}")

        # Calculate consensus
        consensus_result = self.consensus_engine.calculate_consensus(
            agent_recommendations=analyses,
            risk_adjusted=True
        )

        # Generate consensus report
        consensus_report = self.consensus_engine.get_consensus_report(consensus_result)
        logger.info(f"\n{consensus_report}")

        # Add consensus data to analyses
        enhanced_analyses = analyses.copy()
        enhanced_analyses['consensus'] = {
            'recommendation': consensus_result.recommendation,
            'confidence': consensus_result.confidence,
            'consensus_score': consensus_result.consensus_score,
            'agreement_level': consensus_result.agreement_level,
            'weighted_votes': consensus_result.weighted_votes,
            'dissenting_opinions': consensus_result.dissenting_opinions,
            'reasoning': consensus_result.reasoning,
            'metadata': consensus_result.metadata,
            'agent_breakdown': consensus_result.agent_breakdown,
            'conflicts_resolved': consensus_result.conflicts_resolved,
            'report': consensus_report
        }

        return enhanced_analyses

    def override_synthesis_with_consensus(
        self,
        llm_recommendation: Dict[str, Any],
        consensus_result: ConsensusResult,
        threshold: float = 0.7
    ) -> Dict[str, Any]:
        """
        Override LLM recommendation with consensus if confidence is high enough

        Args:
            llm_recommendation: Original LLM-generated recommendation
            consensus_result: Consensus engine result
            threshold: Confidence threshold to override (default 0.7)

        Returns:
            Final recommendation (either LLM or consensus)
        """

        # If consensus confidence is high and disagrees with LLM, use consensus
        if consensus_result.confidence >= threshold:
            llm_rec = llm_recommendation.get('action', 'HOLD')

            if llm_rec != consensus_result.recommendation:
                logger.warning(
                    f"[ConsensusIntegration] Overriding LLM recommendation "
                    f"({llm_rec}) with consensus ({consensus_result.recommendation}) "
                    f"due to high consensus confidence ({consensus_result.confidence:.1%})"
                )

                # Update recommendation
                llm_recommendation['action'] = consensus_result.recommendation
                llm_recommendation['confidence'] = consensus_result.confidence

                # Add override metadata
                llm_recommendation['override_applied'] = True
                llm_recommendation['original_llm_recommendation'] = llm_rec
                llm_recommendation['override_reason'] = (
                    f"High-confidence consensus ({consensus_result.confidence:.1%}) "
                    f"with {consensus_result.agreement_level:.1%} agent agreement"
                )

        return llm_recommendation

    def get_consensus_metrics_for_logging(
        self,
        consensus_result: ConsensusResult
    ) -> Dict[str, Any]:
        """
        Extract key metrics for logging/monitoring

        Args:
            consensus_result: Consensus calculation result

        Returns:
            Dict of metrics
        """
        return {
            'recommendation': consensus_result.recommendation,
            'confidence': consensus_result.confidence,
            'agreement_level': consensus_result.agreement_level,
            'total_agents': consensus_result.metadata.get('total_agents', 0),
            'dissenting_count': len(consensus_result.dissenting_opinions),
            'conflicts_resolved': len(consensus_result.conflicts_resolved),
            'weighted_buy_votes': consensus_result.weighted_votes.get('BUY', 0) + \
                                 consensus_result.weighted_votes.get('STRONG_BUY', 0),
            'weighted_sell_votes': consensus_result.weighted_votes.get('SELL', 0) + \
                                  consensus_result.weighted_votes.get('STRONG_SELL', 0),
            'weighted_hold_votes': consensus_result.weighted_votes.get('HOLD', 0)
        }


# Example integration with ExpertSynthesisAgent
"""
To integrate with ExpertSynthesisAgent, modify the synthesize() method:

```python
from services.consensus_integration import ConsensusIntegration

class ExpertSynthesisAgent:
    def __init__(self, llm: ChatOpenAI):
        # ... existing initialization ...
        self.consensus_integration = ConsensusIntegration()

    async def synthesize(self, analyses: Dict[str, Any]) -> Dict[str, Any]:
        # ... existing code ...

        # STEP 1: Calculate consensus BEFORE LLM synthesis
        enhanced_analyses = await self.consensus_integration.enhance_synthesis_with_consensus(
            analyses=analyses,
            symbol=symbol,
            price=price
        )

        # STEP 2: Calculate traditional consensus (existing code)
        consensus = self._calculate_consensus(enhanced_analyses)

        # STEP 3: Generate LLM recommendation (existing code)
        recommendation = await self._generate_final_recommendation(
            symbol, price, enhanced_analyses, consensus
        )

        # STEP 4: Check if consensus should override LLM
        consensus_data = enhanced_analyses.get('consensus', {})
        if consensus_data:
            consensus_result = ConsensusResult(
                recommendation=consensus_data['recommendation'],
                confidence=consensus_data['confidence'],
                consensus_score=consensus_data['consensus_score'],
                agreement_level=consensus_data['agreement_level'],
                weighted_votes=consensus_data['weighted_votes'],
                dissenting_opinions=consensus_data['dissenting_opinions'],
                reasoning=consensus_data['reasoning'],
                metadata=consensus_data['metadata'],
                agent_breakdown=consensus_data['agent_breakdown'],
                conflicts_resolved=consensus_data['conflicts_resolved']
            )

            recommendation = self.consensus_integration.override_synthesis_with_consensus(
                llm_recommendation=recommendation,
                consensus_result=consensus_result,
                threshold=0.7  # Override if consensus confidence >= 70%
            )

        # STEP 5: Build final result with consensus data
        result = {
            # ... existing fields ...
            'consensus_breakdown': consensus,
            'consensus_engine_result': consensus_data,  # NEW: Full consensus data
            'consensus_metrics': self.consensus_integration.get_consensus_metrics_for_logging(
                consensus_result
            ) if consensus_data else {},
            # ... rest of fields ...
        }

        return result
```
"""
