"""
Consensus Recommendation Engine
Aggregates recommendations from multiple expert agents using weighted voting
"""

from typing import Dict, List, Any, Optional
from dataclasses import dataclass
import logging
import numpy as np

logger = logging.getLogger(__name__)


@dataclass
class AgentRecommendation:
    """Single agent's recommendation with metadata"""
    agent_name: str
    recommendation: str  # BUY, SELL, HOLD
    confidence: float  # 0-100
    reasoning: str
    weight: float = 1.0  # Agent importance weight


class ConsensusRecommendationEngine:
    """
    Aggregates recommendations from multiple expert agents using weighted voting.

    Features:
    - Weighted voting based on agent expertise and confidence
    - Consensus strength calculation
    - Dissent detection and reporting
    - Confidence-weighted final recommendation
    """

    def __init__(self):
        self.name = "ConsensusRecommendationEngine"

        # Agent weights (higher = more influential)
        # Based on professional trading hierarchy
        self.agent_weights = {
            'ExpertFundamentalAgent': 1.5,  # Highest weight (Warren Buffett style)
            'ExpertTechnicalAgent': 1.3,     # Technical patterns
            'ExpertRiskAgent': 1.4,          # Risk management critical
            'SentimentTrackerAgent': 1.0,   # Market psychology
            'PredictiveAgent': 1.2,          # ML predictions
            'EnhancedPeerAgent': 0.9,        # Peer comparison context
            'InsiderActivityAgent': 1.1,     # Insider signals
            'CatalystTrackerAgent': 0.8,     # Event-driven
            'default': 1.0
        }

    def calculate_consensus(
        self,
        agent_recommendations: List[Dict[str, Any]],
        symbol: str = "UNKNOWN"
    ) -> Dict[str, Any]:
        """
        Calculate consensus recommendation from multiple agents.

        Args:
            agent_recommendations: List of agent outputs with recommendation/confidence
            symbol: Stock symbol for logging

        Returns:
            Consensus result with final recommendation, strength, and dissent info
        """
        if not agent_recommendations:
            logger.warning(f"[{self.name}] No agent recommendations for {symbol}")
            return {
                'consensus_recommendation': 'HOLD',
                'consensus_strength': 0.0,
                'consensus_confidence': 0.0,
                'agent_agreement': 0.0,
                'dissenting_agents': [],
                'reasoning': 'No agent recommendations available'
            }

        # Extract and structure recommendations
        recommendations = []
        for agent_data in agent_recommendations:
            agent_name = agent_data.get('agent_name', agent_data.get('agent', 'Unknown'))
            rec = agent_data.get('recommendation', 'HOLD')
            conf = agent_data.get('confidence', 50.0)

            # Normalize confidence to 0-100 range
            if conf > 1.0 and conf <= 100:
                conf_normalized = conf
            elif conf <= 1.0:
                conf_normalized = conf * 100
            else:
                conf_normalized = 50.0

            reasoning = agent_data.get('reasoning', agent_data.get('summary', ''))
            weight = self.agent_weights.get(agent_name, self.agent_weights['default'])

            recommendations.append(AgentRecommendation(
                agent_name=agent_name,
                recommendation=rec.upper(),
                confidence=conf_normalized,
                reasoning=reasoning,
                weight=weight
            ))

        # Calculate weighted votes
        vote_scores = {'BUY': 0.0, 'SELL': 0.0, 'HOLD': 0.0}
        total_weight = 0.0

        for rec in recommendations:
            # Weight by both agent importance and confidence
            # Confidence acts as a multiplier (0-1 scale)
            vote_weight = rec.weight * (rec.confidence / 100.0)

            # Add to appropriate bucket
            if rec.recommendation in vote_scores:
                vote_scores[rec.recommendation] += vote_weight
            else:
                # Unknown recommendation defaults to HOLD
                vote_scores['HOLD'] += vote_weight

            total_weight += rec.weight

        # Determine consensus (highest weighted score)
        consensus_rec = max(vote_scores, key=vote_scores.get)
        consensus_score = vote_scores[consensus_rec]

        # Consensus strength (0-100%) - how much of total weight agrees
        if total_weight > 0:
            consensus_strength = (consensus_score / total_weight) * 100
        else:
            consensus_strength = 0.0

        # Calculate agent agreement (simple count %)
        consensus_count = sum(1 for r in recommendations if r.recommendation == consensus_rec)
        agent_agreement = (consensus_count / len(recommendations)) * 100

        # Detect dissenting agents
        dissenting = [
            {
                'agent': r.agent_name,
                'recommendation': r.recommendation,
                'confidence': round(r.confidence, 1),
                'reasoning': r.reasoning[:200] if r.reasoning else None  # Truncate
            }
            for r in recommendations
            if r.recommendation != consensus_rec
        ]

        # Calculate average confidence of agreeing agents
        agreeing_agents = [r for r in recommendations if r.recommendation == consensus_rec]
        if agreeing_agents:
            avg_confidence = sum(r.confidence for r in agreeing_agents) / len(agreeing_agents)
        else:
            avg_confidence = 50.0

        # Build detailed reasoning
        reasoning_parts = [
            f"{consensus_count}/{len(recommendations)} agents recommend {consensus_rec}",
            f"Weighted consensus: {consensus_strength:.1f}%",
            f"Avg confidence: {avg_confidence:.1f}%"
        ]

        if dissenting:
            dissent_summary = ", ".join([
                f"{d['agent']}: {d['recommendation']}"
                for d in dissenting[:3]  # Top 3 dissenters
            ])
            reasoning_parts.append(f"Dissent: {dissent_summary}")

        # Determine confidence level (color coding for UI)
        if consensus_strength >= 80 and avg_confidence >= 70:
            confidence_level = "high"
        elif consensus_strength >= 60 and avg_confidence >= 50:
            confidence_level = "medium"
        else:
            confidence_level = "low"

        result = {
            'consensus_recommendation': consensus_rec,
            'consensus_strength': round(consensus_strength, 2),
            'consensus_confidence': round(avg_confidence, 2),
            'confidence_level': confidence_level,
            'agent_agreement': round(agent_agreement, 2),
            'vote_breakdown': {
                'BUY': round(vote_scores['BUY'], 3),
                'SELL': round(vote_scores['SELL'], 3),
                'HOLD': round(vote_scores['HOLD'], 3)
            },
            'total_agents': len(recommendations),
            'agreeing_agents': consensus_count,
            'dissenting_agents': dissenting,
            'reasoning': ' | '.join(reasoning_parts)
        }

        logger.info(
            f"[{self.name}] {symbol} Consensus: {consensus_rec} "
            f"(strength: {consensus_strength:.1f}%, "
            f"agreement: {agent_agreement:.1f}%, "
            f"confidence: {avg_confidence:.1f}%)"
        )

        # Log dissent if significant
        if len(dissenting) > len(recommendations) * 0.3:  # >30% dissent
            logger.warning(
                f"[{self.name}] {symbol} has significant dissent: "
                f"{len(dissenting)}/{len(recommendations)} agents disagree"
            )

        return result

    def get_recommendation_summary(self, consensus_result: Dict[str, Any]) -> str:
        """Generate human-readable summary"""
        rec = consensus_result['consensus_recommendation']
        strength = consensus_result['consensus_strength']
        conf = consensus_result['consensus_confidence']

        # Strength descriptors
        if strength >= 90:
            strength_desc = "Strong"
        elif strength >= 75:
            strength_desc = "Moderate"
        elif strength >= 60:
            strength_desc = "Weak"
        else:
            strength_desc = "Mixed"

        # Confidence descriptors
        if conf >= 80:
            conf_desc = "high confidence"
        elif conf >= 60:
            conf_desc = "moderate confidence"
        else:
            conf_desc = "low confidence"

        return f"{strength_desc} {rec} ({conf_desc})"
