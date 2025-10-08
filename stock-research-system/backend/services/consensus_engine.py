"""
Consensus Recommendation Engine - Phase 4 Task 1
Intelligent system that resolves conflicting agent recommendations using weighted voting and confidence scoring
"""

import logging
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime
from dataclasses import dataclass, field
from enum import Enum
import statistics
import math

logger = logging.getLogger(__name__)


class RecommendationType(Enum):
    """Supported recommendation types"""
    STRONG_BUY = "STRONG_BUY"
    BUY = "BUY"
    HOLD = "HOLD"
    SELL = "SELL"
    STRONG_SELL = "STRONG_SELL"

    def to_numeric(self) -> float:
        """Convert recommendation to numeric score 0-1"""
        mapping = {
            'STRONG_BUY': 1.0,
            'BUY': 0.75,
            'HOLD': 0.5,
            'SELL': 0.25,
            'STRONG_SELL': 0.0
        }
        return mapping.get(self.value, 0.5)

    @classmethod
    def from_numeric(cls, score: float) -> 'RecommendationType':
        """Convert numeric score to recommendation"""
        if score >= 0.875:
            return cls.STRONG_BUY
        elif score >= 0.625:
            return cls.BUY
        elif score >= 0.375:
            return cls.HOLD
        elif score >= 0.125:
            return cls.SELL
        else:
            return cls.STRONG_SELL


@dataclass
class AgentRecommendation:
    """Individual agent recommendation with metadata"""
    agent_name: str
    recommendation: str  # BUY, SELL, HOLD, etc.
    confidence: float  # 0-1
    rationale: str
    key_metrics: Dict[str, Any] = field(default_factory=dict)
    timestamp: str = field(default_factory=lambda: datetime.utcnow().isoformat())
    historical_accuracy: float = 0.75  # Default 75% accuracy

    def to_numeric_score(self) -> float:
        """Convert recommendation to numeric score"""
        try:
            return RecommendationType[self.recommendation.replace(' ', '_').upper()].to_numeric()
        except (KeyError, AttributeError):
            # Handle signals like 'bullish', 'bearish', 'neutral'
            signal_mapping = {
                'bullish': 0.8,
                'positive': 0.7,
                'neutral': 0.5,
                'negative': 0.3,
                'bearish': 0.2
            }
            return signal_mapping.get(self.recommendation.lower(), 0.5)


@dataclass
class ConsensusResult:
    """Result of consensus calculation"""
    recommendation: str
    confidence: float
    consensus_score: float  # 0-1
    agreement_level: float  # 0-1 (1 = full agreement)
    weighted_votes: Dict[str, float]  # recommendation -> weighted vote count
    dissenting_opinions: List[Dict[str, Any]]
    reasoning: str
    metadata: Dict[str, Any] = field(default_factory=dict)
    agent_breakdown: Dict[str, Dict[str, Any]] = field(default_factory=dict)
    conflicts_resolved: List[str] = field(default_factory=list)
    timestamp: str = field(default_factory=lambda: datetime.utcnow().isoformat())


class ConsensusEngine:
    """
    Intelligent consensus engine that resolves conflicting agent recommendations
    using weighted voting, confidence scoring, and historical accuracy
    """

    def __init__(self):
        self.name = "ConsensusEngine"

        # Base weights for different agent types (can be overridden)
        self.base_weights = {
            'fundamental': 0.35,
            'technical': 0.25,
            'risk': 0.20,
            'sentiment': 0.10,
            'news': 0.15,
            'market': 0.05,
            'macro': 0.10,
            'peer_comparison': 0.08,
            'insider_activity': 0.07,
            'valuation': 0.30
        }

        # Historical accuracy tracking (in production, load from database)
        self.historical_accuracy = {}

        # Conflict resolution strategies
        self.conflict_resolution_threshold = 0.3  # If agreement < 30%, flag as low confidence

    def calculate_consensus(
        self,
        agent_recommendations: Dict[str, Any],
        override_weights: Optional[Dict[str, float]] = None,
        risk_adjusted: bool = True
    ) -> ConsensusResult:
        """
        Calculate consensus recommendation from multiple agent outputs

        Args:
            agent_recommendations: Dict of agent_name -> agent analysis output
            override_weights: Optional custom weights for agents
            risk_adjusted: Whether to apply risk adjustments to consensus

        Returns:
            ConsensusResult with final recommendation and metadata
        """
        logger.info(f"[{self.name}] Calculating consensus from {len(agent_recommendations)} agents")

        # Step 1: Extract and normalize agent recommendations
        normalized_recommendations = self._extract_recommendations(agent_recommendations)

        if not normalized_recommendations:
            logger.warning(f"[{self.name}] No valid recommendations found")
            return self._create_fallback_consensus()

        # Step 2: Calculate agent weights
        weights = override_weights or self.base_weights
        agent_weights = self._calculate_agent_weights(normalized_recommendations, weights)

        # Step 3: Calculate weighted votes
        weighted_votes = self._calculate_weighted_votes(
            normalized_recommendations,
            agent_weights
        )

        # Step 4: Determine consensus recommendation
        consensus_recommendation, consensus_score = self._determine_consensus(weighted_votes)

        # Step 5: Apply risk adjustments if enabled
        if risk_adjusted:
            consensus_recommendation, consensus_score = self._apply_risk_adjustments(
                consensus_recommendation,
                consensus_score,
                agent_recommendations
            )

        # Step 6: Calculate agreement level
        agreement_level = self._calculate_agreement_level(
            normalized_recommendations,
            consensus_recommendation
        )

        # Step 7: Identify dissenting opinions
        dissenting_opinions = self._identify_dissenters(
            normalized_recommendations,
            consensus_recommendation,
            agent_weights
        )

        # Step 8: Generate reasoning
        reasoning = self._generate_consensus_reasoning(
            normalized_recommendations,
            agent_weights,
            weighted_votes,
            consensus_recommendation,
            agreement_level,
            dissenting_opinions
        )

        # Step 9: Calculate final confidence
        final_confidence = self._calculate_consensus_confidence(
            agreement_level,
            consensus_score,
            normalized_recommendations,
            agent_weights
        )

        # Step 10: Build agent breakdown
        agent_breakdown = self._build_agent_breakdown(
            normalized_recommendations,
            agent_weights,
            weighted_votes
        )

        # Step 11: Track conflicts resolved
        conflicts_resolved = self._identify_conflicts_resolved(
            normalized_recommendations,
            consensus_recommendation
        )

        result = ConsensusResult(
            recommendation=consensus_recommendation,
            confidence=final_confidence,
            consensus_score=consensus_score,
            agreement_level=agreement_level,
            weighted_votes=weighted_votes,
            dissenting_opinions=dissenting_opinions,
            reasoning=reasoning,
            metadata={
                'total_agents': len(normalized_recommendations),
                'agents_consulted': [r.agent_name for r in normalized_recommendations],
                'risk_adjusted': risk_adjusted,
                'average_confidence': statistics.mean([r.confidence for r in normalized_recommendations]),
                'confidence_stdev': statistics.stdev([r.confidence for r in normalized_recommendations]) if len(normalized_recommendations) > 1 else 0.0,
                'minority_views': len(dissenting_opinions),
                'conflict_resolution_applied': len(conflicts_resolved) > 0
            },
            agent_breakdown=agent_breakdown,
            conflicts_resolved=conflicts_resolved
        )

        logger.info(
            f"[{self.name}] Consensus: {result.recommendation} "
            f"(confidence: {result.confidence:.1%}, agreement: {result.agreement_level:.1%})"
        )

        return result

    def _extract_recommendations(
        self,
        agent_recommendations: Dict[str, Any]
    ) -> List[AgentRecommendation]:
        """Extract and normalize recommendations from agent outputs"""
        normalized = []

        for agent_name, analysis in agent_recommendations.items():
            if not analysis or not isinstance(analysis, dict):
                continue

            # Extract recommendation (varies by agent type)
            recommendation = None
            confidence = 0.5
            rationale = ""
            key_metrics = {}

            # Fundamental agent
            if agent_name == 'fundamental':
                recommendation = analysis.get('recommendation', 'HOLD')
                confidence = analysis.get('confidence', 0.5)
                rationale = analysis.get('summary', '')
                key_metrics = {
                    'pe_ratio': analysis.get('pe_ratio'),
                    'roe': analysis.get('roe'),
                    'analyst_target': analysis.get('analyst_target_price')
                }

            # Technical agent
            elif agent_name == 'technical':
                recommendation = analysis.get('signal', 'HOLD')
                confidence = analysis.get('confidence', 0.5)
                rationale = analysis.get('analysis_summary', '')
                key_metrics = {
                    'trend': analysis.get('trend'),
                    'rsi': analysis.get('rsi', {}).get('value') if isinstance(analysis.get('rsi'), dict) else analysis.get('rsi'),
                    'momentum': analysis.get('momentum')
                }

            # Risk agent
            elif agent_name == 'risk':
                risk_level = analysis.get('risk_level', 'medium')
                # Convert risk level to recommendation
                risk_mapping = {
                    'low': 'BUY',
                    'medium': 'HOLD',
                    'high': 'SELL',
                    'very_high': 'STRONG_SELL'
                }
                recommendation = risk_mapping.get(risk_level.lower(), 'HOLD')
                confidence = analysis.get('confidence', 0.6)
                rationale = f"Risk level: {risk_level}"
                key_metrics = {
                    'sharpe_ratio': analysis.get('sharpe_ratio'),
                    'max_drawdown': analysis.get('max_drawdown'),
                    'var_95': analysis.get('var_95')
                }

            # Sentiment agent
            elif agent_name == 'sentiment':
                sentiment = analysis.get('overall_sentiment', 'neutral')
                sentiment_mapping = {
                    'bullish': 'BUY',
                    'positive': 'BUY',
                    'neutral': 'HOLD',
                    'negative': 'SELL',
                    'bearish': 'SELL'
                }
                recommendation = sentiment_mapping.get(sentiment.lower(), 'HOLD')
                confidence = analysis.get('confidence', 0.4)
                rationale = f"Sentiment: {sentiment}"
                key_metrics = {
                    'sentiment_score': analysis.get('sentiment_score'),
                    'volume': analysis.get('total_mentions')
                }

            # News agent
            elif agent_name == 'news':
                news_sentiment = analysis.get('sentiment', {})
                if isinstance(news_sentiment, dict):
                    score = news_sentiment.get('score', 0)
                    # Convert -1 to 1 scale to recommendation
                    if score > 0.3:
                        recommendation = 'BUY'
                    elif score < -0.3:
                        recommendation = 'SELL'
                    else:
                        recommendation = 'HOLD'
                    confidence = news_sentiment.get('confidence', 0.6)
                    rationale = news_sentiment.get('overall', 'neutral')
                    key_metrics = {
                        'sentiment_score': score,
                        'article_count': len(analysis.get('articles', []))
                    }
                else:
                    continue

            # Market agent
            elif agent_name == 'market':
                # Infer from price movement
                price_data = analysis.get('price_data', {})
                change_pct = price_data.get('change_percent', 0)
                if change_pct > 2:
                    recommendation = 'BUY'
                elif change_pct < -2:
                    recommendation = 'SELL'
                else:
                    recommendation = 'HOLD'
                confidence = 0.5
                rationale = f"Price change: {change_pct:.2f}%"
                key_metrics = {
                    'current_price': price_data.get('current_price'),
                    'volume': price_data.get('volume')
                }

            # Add to normalized list if we got a recommendation
            if recommendation:
                normalized.append(AgentRecommendation(
                    agent_name=agent_name,
                    recommendation=recommendation,
                    confidence=confidence,
                    rationale=rationale,
                    key_metrics=key_metrics,
                    historical_accuracy=self.historical_accuracy.get(agent_name, 0.75)
                ))

        logger.info(f"[{self.name}] Extracted {len(normalized)} valid recommendations")
        return normalized

    def _calculate_agent_weights(
        self,
        recommendations: List[AgentRecommendation],
        base_weights: Dict[str, float]
    ) -> Dict[str, float]:
        """
        Calculate final weights for each agent based on:
        - Base weight
        - Confidence score
        - Historical accuracy
        """
        agent_weights = {}

        for rec in recommendations:
            # Base weight
            base_weight = base_weights.get(rec.agent_name, 0.1)

            # Weight formula: base_weight * confidence * historical_accuracy
            final_weight = base_weight * rec.confidence * rec.historical_accuracy

            agent_weights[rec.agent_name] = final_weight

            logger.debug(
                f"[{self.name}] {rec.agent_name}: base={base_weight:.2f}, "
                f"confidence={rec.confidence:.2f}, accuracy={rec.historical_accuracy:.2f}, "
                f"final_weight={final_weight:.3f}"
            )

        # Normalize weights to sum to 1.0
        total_weight = sum(agent_weights.values())
        if total_weight > 0:
            agent_weights = {k: v/total_weight for k, v in agent_weights.items()}

        return agent_weights

    def _calculate_weighted_votes(
        self,
        recommendations: List[AgentRecommendation],
        agent_weights: Dict[str, float]
    ) -> Dict[str, float]:
        """Calculate weighted votes for each recommendation type"""
        weighted_votes = {
            'STRONG_BUY': 0.0,
            'BUY': 0.0,
            'HOLD': 0.0,
            'SELL': 0.0,
            'STRONG_SELL': 0.0
        }

        for rec in recommendations:
            weight = agent_weights.get(rec.agent_name, 0.0)

            # Normalize recommendation to standard format
            normalized_rec = rec.recommendation.replace(' ', '_').upper()

            # Handle non-standard recommendations
            if normalized_rec not in weighted_votes:
                # Map to closest standard recommendation
                if 'BUY' in normalized_rec:
                    normalized_rec = 'BUY'
                elif 'SELL' in normalized_rec:
                    normalized_rec = 'SELL'
                else:
                    normalized_rec = 'HOLD'

            weighted_votes[normalized_rec] += weight

        return weighted_votes

    def _determine_consensus(
        self,
        weighted_votes: Dict[str, float]
    ) -> Tuple[str, float]:
        """
        Determine consensus recommendation from weighted votes

        Returns:
            (recommendation, consensus_score)
        """
        # Find recommendation with highest weighted vote
        consensus_rec = max(weighted_votes.items(), key=lambda x: x[1])[0]

        # Calculate consensus score (0-1) using weighted average approach
        # Convert votes to numeric scores and calculate weighted average
        total_weight = sum(weighted_votes.values())

        if total_weight == 0:
            return 'HOLD', 0.5

        weighted_score = 0.0
        for rec, vote in weighted_votes.items():
            try:
                numeric_score = RecommendationType[rec].to_numeric()
                weighted_score += numeric_score * vote
            except KeyError:
                continue

        consensus_score = weighted_score / total_weight if total_weight > 0 else 0.5

        # Verify consensus recommendation matches score
        derived_rec = RecommendationType.from_numeric(consensus_score).value

        logger.info(
            f"[{self.name}] Consensus: {consensus_rec} (score: {consensus_score:.3f}), "
            f"votes: {weighted_votes}"
        )

        return consensus_rec, consensus_score

    def _apply_risk_adjustments(
        self,
        recommendation: str,
        score: float,
        agent_recommendations: Dict[str, Any]
    ) -> Tuple[str, float]:
        """
        Apply risk-based adjustments to consensus recommendation
        Critical: Downgrade BUY if risk metrics are unfavorable
        """
        risk_data = agent_recommendations.get('risk', {})

        if not risk_data:
            return recommendation, score

        # Extract risk metrics
        sharpe_ratio = risk_data.get('sharpe_ratio', 0.5)
        risk_level = risk_data.get('risk_level', 'medium').upper()
        max_drawdown = risk_data.get('max_drawdown', 0)

        original_recommendation = recommendation

        # Risk adjustment rules
        if 'BUY' in recommendation:
            # Rule 1: Poor risk-adjusted returns
            if sharpe_ratio < 0.5 and risk_level in ['HIGH', 'VERY_HIGH']:
                recommendation = 'HOLD'
                score = 0.5  # Neutral score
                logger.warning(
                    f"[{self.name}] Risk adjustment: Downgraded {original_recommendation} -> HOLD "
                    f"(Sharpe: {sharpe_ratio:.2f}, Risk: {risk_level})"
                )

            # Rule 2: Excessive drawdown risk
            elif max_drawdown > 30 and risk_level in ['HIGH', 'VERY_HIGH']:
                recommendation = 'HOLD'
                score = max(score - 0.2, 0.5)
                logger.warning(
                    f"[{self.name}] Risk adjustment: Downgraded {original_recommendation} -> HOLD "
                    f"(Max Drawdown: {max_drawdown:.1f}%, Risk: {risk_level})"
                )

            # Rule 3: Moderate risk - reduce confidence
            elif risk_level == 'HIGH':
                score = score * 0.8  # Reduce score by 20%
                logger.info(
                    f"[{self.name}] Risk adjustment: Reduced confidence for {recommendation} "
                    f"due to HIGH risk"
                )

        return recommendation, score

    def _calculate_agreement_level(
        self,
        recommendations: List[AgentRecommendation],
        consensus: str
    ) -> float:
        """
        Calculate how much agents agree with consensus
        Returns value 0-1 (1 = full agreement)
        """
        if not recommendations:
            return 0.5

        # Count agents that agree with consensus
        agreements = 0
        total = len(recommendations)

        for rec in recommendations:
            normalized_rec = rec.recommendation.replace(' ', '_').upper()

            # Exact match
            if normalized_rec == consensus:
                agreements += 1
            # Partial match (BUY variants)
            elif 'BUY' in normalized_rec and 'BUY' in consensus:
                agreements += 0.5
            # Partial match (SELL variants)
            elif 'SELL' in normalized_rec and 'SELL' in consensus:
                agreements += 0.5

        agreement_level = agreements / total if total > 0 else 0.5

        return agreement_level

    def _identify_dissenters(
        self,
        recommendations: List[AgentRecommendation],
        consensus: str,
        agent_weights: Dict[str, float]
    ) -> List[Dict[str, Any]]:
        """Identify agents that significantly disagree with consensus"""
        dissenters = []

        consensus_numeric = RecommendationType[consensus].to_numeric()

        for rec in recommendations:
            rec_numeric = rec.to_numeric_score()

            # Dissenter if recommendation differs by more than 0.3 on 0-1 scale
            if abs(rec_numeric - consensus_numeric) > 0.3:
                dissenters.append({
                    'agent': rec.agent_name,
                    'recommendation': rec.recommendation,
                    'confidence': rec.confidence,
                    'rationale': rec.rationale,
                    'weight': agent_weights.get(rec.agent_name, 0.0),
                    'divergence': abs(rec_numeric - consensus_numeric)
                })

        # Sort by weight (most important dissenters first)
        dissenters.sort(key=lambda x: x['weight'], reverse=True)

        return dissenters

    def _generate_consensus_reasoning(
        self,
        recommendations: List[AgentRecommendation],
        agent_weights: Dict[str, float],
        weighted_votes: Dict[str, float],
        consensus: str,
        agreement_level: float,
        dissenters: List[Dict[str, Any]]
    ) -> str:
        """Generate human-readable explanation of consensus decision"""

        # Count agent opinions
        buy_count = sum(1 for r in recommendations if 'BUY' in r.recommendation.upper())
        sell_count = sum(1 for r in recommendations if 'SELL' in r.recommendation.upper())
        hold_count = len(recommendations) - buy_count - sell_count

        # Build reasoning
        reasoning_parts = []

        # 1. Overall consensus
        reasoning_parts.append(
            f"Consensus recommendation: {consensus} based on analysis from "
            f"{len(recommendations)} specialized agents."
        )

        # 2. Vote breakdown
        reasoning_parts.append(
            f"Agent opinions: {buy_count} bullish, {hold_count} neutral, {sell_count} bearish. "
            f"Weighted votes: BUY={weighted_votes.get('BUY', 0):.2f}, "
            f"HOLD={weighted_votes.get('HOLD', 0):.2f}, "
            f"SELL={weighted_votes.get('SELL', 0):.2f}."
        )

        # 3. Agreement level
        if agreement_level > 0.7:
            reasoning_parts.append(
                f"Strong consensus achieved ({agreement_level:.0%} agreement among agents)."
            )
        elif agreement_level > 0.5:
            reasoning_parts.append(
                f"Moderate consensus ({agreement_level:.0%} agreement). "
                f"Some conflicting signals present."
            )
        else:
            reasoning_parts.append(
                f"Low consensus ({agreement_level:.0%} agreement). "
                f"Significant divergence in agent opinions - exercise caution."
            )

        # 4. Key supporting agents
        top_supporters = sorted(
            [r for r in recommendations if consensus in r.recommendation.upper()],
            key=lambda r: agent_weights.get(r.agent_name, 0),
            reverse=True
        )[:3]

        if top_supporters:
            supporter_names = [r.agent_name for r in top_supporters]
            reasoning_parts.append(
                f"Primary support from: {', '.join(supporter_names)}."
            )

        # 5. Dissenting opinions
        if dissenters:
            if len(dissenters) == 1:
                d = dissenters[0]
                reasoning_parts.append(
                    f"Minority view: {d['agent']} recommends {d['recommendation']} "
                    f"({d['rationale']})."
                )
            else:
                dissenter_summary = ', '.join([
                    f"{d['agent']} ({d['recommendation']})"
                    for d in dissenters[:2]
                ])
                reasoning_parts.append(
                    f"Minority views from {len(dissenters)} agents: {dissenter_summary}."
                )

        # 6. Confidence assessment
        avg_confidence = statistics.mean([r.confidence for r in recommendations])
        if avg_confidence > 0.7:
            reasoning_parts.append("Agents demonstrate high confidence in their analyses.")
        elif avg_confidence < 0.5:
            reasoning_parts.append("Agent confidence levels are moderate - monitor closely.")

        return " ".join(reasoning_parts)

    def _calculate_consensus_confidence(
        self,
        agreement_level: float,
        consensus_score: float,
        recommendations: List[AgentRecommendation],
        agent_weights: Dict[str, float]
    ) -> float:
        """
        Calculate final confidence in consensus recommendation

        Factors:
        - Agreement level (how many agents agree)
        - Individual agent confidence levels
        - Agent weights
        - Consensus strength
        """

        # Factor 1: Agreement level (0-1)
        agreement_factor = agreement_level

        # Factor 2: Weighted average of agent confidences
        weighted_confidence = sum(
            r.confidence * agent_weights.get(r.agent_name, 0)
            for r in recommendations
        )

        # Factor 3: Consensus strength (how decisive is the consensus score)
        # Scores near 0.5 are weak, scores near 0 or 1 are strong
        consensus_strength = abs(consensus_score - 0.5) * 2  # Maps 0.5->0, 0/1->1

        # Combine factors with weights
        final_confidence = (
            agreement_factor * 0.4 +
            weighted_confidence * 0.4 +
            consensus_strength * 0.2
        )

        # Adjust for low agreement
        if agreement_level < 0.3:
            final_confidence *= 0.7  # Reduce confidence by 30%
            logger.warning(
                f"[{self.name}] Low agreement detected ({agreement_level:.1%}) - "
                f"reducing confidence"
            )

        # Cap between 0.1 and 0.95
        final_confidence = max(0.1, min(0.95, final_confidence))

        return final_confidence

    def _build_agent_breakdown(
        self,
        recommendations: List[AgentRecommendation],
        agent_weights: Dict[str, float],
        weighted_votes: Dict[str, float]
    ) -> Dict[str, Dict[str, Any]]:
        """Build detailed breakdown of each agent's contribution"""
        breakdown = {}

        for rec in recommendations:
            breakdown[rec.agent_name] = {
                'recommendation': rec.recommendation,
                'confidence': rec.confidence,
                'weight': agent_weights.get(rec.agent_name, 0.0),
                'rationale': rec.rationale,
                'key_metrics': rec.key_metrics,
                'historical_accuracy': rec.historical_accuracy,
                'contribution': agent_weights.get(rec.agent_name, 0.0) * rec.confidence
            }

        return breakdown

    def _identify_conflicts_resolved(
        self,
        recommendations: List[AgentRecommendation],
        consensus: str
    ) -> List[str]:
        """Identify specific conflicts that were resolved"""
        conflicts = []

        # Check for BUY vs SELL conflicts
        buy_agents = [r.agent_name for r in recommendations if 'BUY' in r.recommendation.upper()]
        sell_agents = [r.agent_name for r in recommendations if 'SELL' in r.recommendation.upper()]

        if buy_agents and sell_agents:
            conflicts.append(
                f"Resolved BUY ({', '.join(buy_agents)}) vs "
                f"SELL ({', '.join(sell_agents)}) conflict -> {consensus}"
            )

        # Check for high vs low risk conflicts
        risk_rec = next((r for r in recommendations if r.agent_name == 'risk'), None)
        fundamental_rec = next((r for r in recommendations if r.agent_name == 'fundamental'), None)

        if risk_rec and fundamental_rec:
            if ('BUY' in fundamental_rec.recommendation.upper() and
                'SELL' in risk_rec.recommendation.upper()):
                conflicts.append(
                    f"Resolved fundamental bullishness vs risk bearishness -> {consensus}"
                )

        # Check for technical vs fundamental divergence
        technical_rec = next((r for r in recommendations if r.agent_name == 'technical'), None)
        if technical_rec and fundamental_rec:
            if technical_rec.recommendation.upper() != fundamental_rec.recommendation.upper():
                if 'BUY' in technical_rec.recommendation.upper() or 'SELL' in technical_rec.recommendation.upper():
                    if 'BUY' in fundamental_rec.recommendation.upper() or 'SELL' in fundamental_rec.recommendation.upper():
                        conflicts.append(
                            f"Resolved technical ({technical_rec.recommendation}) vs "
                            f"fundamental ({fundamental_rec.recommendation}) divergence -> {consensus}"
                        )

        return conflicts

    def _create_fallback_consensus(self) -> ConsensusResult:
        """Create fallback consensus when no valid recommendations available"""
        return ConsensusResult(
            recommendation='HOLD',
            confidence=0.3,
            consensus_score=0.5,
            agreement_level=0.0,
            weighted_votes={'HOLD': 1.0},
            dissenting_opinions=[],
            reasoning="Insufficient agent data for consensus calculation. Default to HOLD.",
            metadata={'error': 'No valid agent recommendations available'},
            agent_breakdown={},
            conflicts_resolved=[]
        )

    def update_historical_accuracy(
        self,
        agent_name: str,
        accuracy: float
    ):
        """
        Update historical accuracy for an agent

        Args:
            agent_name: Name of agent
            accuracy: Accuracy score 0-1
        """
        self.historical_accuracy[agent_name] = max(0.1, min(1.0, accuracy))
        logger.info(
            f"[{self.name}] Updated {agent_name} historical accuracy: "
            f"{self.historical_accuracy[agent_name]:.2%}"
        )

    def get_consensus_report(self, result: ConsensusResult) -> str:
        """
        Generate human-readable consensus report

        Args:
            result: ConsensusResult to format

        Returns:
            Formatted report string
        """
        report_lines = [
            "=" * 80,
            "CONSENSUS RECOMMENDATION REPORT",
            "=" * 80,
            "",
            f"FINAL RECOMMENDATION: {result.recommendation}",
            f"CONFIDENCE: {result.confidence:.1%}",
            f"CONSENSUS SCORE: {result.consensus_score:.3f}",
            f"AGREEMENT LEVEL: {result.agreement_level:.1%}",
            "",
            "WEIGHTED VOTES:",
        ]

        for rec, votes in sorted(result.weighted_votes.items(), key=lambda x: x[1], reverse=True):
            report_lines.append(f"  {rec:15s}: {votes:.3f}")

        report_lines.extend([
            "",
            "REASONING:",
            f"  {result.reasoning}",
            ""
        ])

        if result.conflicts_resolved:
            report_lines.extend([
                "CONFLICTS RESOLVED:",
                *[f"  - {conflict}" for conflict in result.conflicts_resolved],
                ""
            ])

        if result.dissenting_opinions:
            report_lines.extend([
                f"DISSENTING OPINIONS ({len(result.dissenting_opinions)}):",
                *[
                    f"  - {d['agent']}: {d['recommendation']} "
                    f"(confidence: {d['confidence']:.1%}, weight: {d['weight']:.3f})"
                    for d in result.dissenting_opinions[:3]
                ],
                ""
            ])

        report_lines.extend([
            "AGENT BREAKDOWN:",
            *[
                f"  {agent:20s}: {data['recommendation']:12s} "
                f"(confidence: {data['confidence']:.1%}, weight: {data['weight']:.3f})"
                for agent, data in result.agent_breakdown.items()
            ],
            "",
            "METADATA:",
            f"  Total Agents: {result.metadata.get('total_agents', 0)}",
            f"  Average Confidence: {result.metadata.get('average_confidence', 0):.1%}",
            f"  Confidence StdDev: {result.metadata.get('confidence_stdev', 0):.3f}",
            f"  Minority Views: {result.metadata.get('minority_views', 0)}",
            f"  Risk Adjusted: {result.metadata.get('risk_adjusted', False)}",
            "",
            "=" * 80
        ])

        return "\n".join(report_lines)
