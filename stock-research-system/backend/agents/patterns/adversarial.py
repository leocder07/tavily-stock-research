"""
Adversarial Collaboration Pattern for Multi-Agent System
Enables bull vs bear debates for balanced analysis
"""

import logging
import asyncio
from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass
from enum import Enum
from datetime import datetime

logger = logging.getLogger(__name__)


class DebatePosition(Enum):
    """Positions in adversarial debate."""
    BULLISH = "bullish"
    BEARISH = "bearish"
    NEUTRAL = "neutral"


class ArgumentStrength(Enum):
    """Strength levels for arguments."""
    WEAK = 1
    MODERATE = 2
    STRONG = 3
    COMPELLING = 4


@dataclass
class Argument:
    """Single argument in debate."""
    position: DebatePosition
    claim: str
    evidence: List[Dict[str, Any]]
    strength: ArgumentStrength
    confidence: float
    counter_arguments: List[str] = None


@dataclass
class DebateResult:
    """Result of adversarial debate."""
    topic: str
    bull_arguments: List[Argument]
    bear_arguments: List[Argument]
    consensus: Dict[str, Any]
    winner: Optional[DebatePosition]
    confidence_delta: float
    synthesis: str
    key_insights: List[str]


class AdversarialCollaborationAgent:
    """Agent that facilitates adversarial collaboration between bull and bear perspectives."""

    def __init__(self, llm=None):
        self.llm = llm
        self.debate_history = []

    async def conduct_debate(
        self,
        topic: str,
        context: Dict[str, Any],
        rounds: int = 3
    ) -> DebateResult:
        """
        Conduct adversarial debate on a topic.

        Args:
            topic: The topic to debate
            context: Context information including data and analysis
            rounds: Number of debate rounds

        Returns:
            DebateResult with arguments, consensus, and synthesis
        """
        logger.info(f"Starting adversarial debate on: {topic}")

        # Initialize debate positions
        bull_agent = BullAgent(self.llm)
        bear_agent = BearAgent(self.llm)

        bull_arguments = []
        bear_arguments = []

        # Conduct debate rounds
        for round_num in range(rounds):
            logger.info(f"Debate round {round_num + 1}/{rounds}")

            # Bull makes argument
            bull_arg = await bull_agent.make_argument(
                topic=topic,
                context=context,
                previous_arguments=bear_arguments,
                round_num=round_num
            )
            bull_arguments.append(bull_arg)

            # Bear counters
            bear_arg = await bear_agent.make_argument(
                topic=topic,
                context=context,
                previous_arguments=bull_arguments,
                round_num=round_num
            )
            bear_arguments.append(bear_arg)

            # Exchange rebuttals
            if round_num < rounds - 1:
                bull_arg.counter_arguments = await bull_agent.generate_rebuttals(bear_arg)
                bear_arg.counter_arguments = await bear_agent.generate_rebuttals(bull_arg)

        # Find consensus
        consensus = await self._find_consensus(bull_arguments, bear_arguments, context)

        # Determine winner (if any)
        winner = await self._determine_winner(bull_arguments, bear_arguments, consensus)

        # Calculate confidence delta
        confidence_delta = await self._calculate_confidence_delta(bull_arguments, bear_arguments)

        # Synthesize insights
        synthesis = await self._synthesize_debate(bull_arguments, bear_arguments, consensus)

        # Extract key insights
        key_insights = await self._extract_key_insights(bull_arguments, bear_arguments, synthesis)

        result = DebateResult(
            topic=topic,
            bull_arguments=bull_arguments,
            bear_arguments=bear_arguments,
            consensus=consensus,
            winner=winner,
            confidence_delta=confidence_delta,
            synthesis=synthesis,
            key_insights=key_insights
        )

        # Store in history
        self.debate_history.append(result)

        return result

    async def _find_consensus(
        self,
        bull_arguments: List[Argument],
        bear_arguments: List[Argument],
        context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Find areas of consensus between opposing views."""
        consensus = {
            "agreed_facts": [],
            "agreed_risks": [],
            "agreed_opportunities": [],
            "divergence_points": [],
            "uncertainty_areas": []
        }

        # Extract all claims
        bull_claims = [arg.claim for arg in bull_arguments]
        bear_claims = [arg.claim for arg in bear_arguments]

        # Find agreed facts
        for bull_claim in bull_claims:
            for bear_claim in bear_claims:
                if self._claims_agree(bull_claim, bear_claim):
                    consensus["agreed_facts"].append({
                        "fact": self._extract_common_fact(bull_claim, bear_claim),
                        "confidence": 0.8
                    })

        # Identify agreed risks
        bull_risks = self._extract_risks(bull_arguments)
        bear_risks = self._extract_risks(bear_arguments)
        consensus["agreed_risks"] = list(set(bull_risks) & set(bear_risks))

        # Identify divergence points
        for i, bull_arg in enumerate(bull_arguments):
            for j, bear_arg in enumerate(bear_arguments):
                if self._claims_conflict(bull_arg.claim, bear_arg.claim):
                    consensus["divergence_points"].append({
                        "bull_position": bull_arg.claim,
                        "bear_position": bear_arg.claim,
                        "importance": max(bull_arg.strength.value, bear_arg.strength.value)
                    })

        # Identify uncertainty areas
        low_confidence_topics = []
        for arg in bull_arguments + bear_arguments:
            if arg.confidence < 0.6:
                low_confidence_topics.append(arg.claim)
        consensus["uncertainty_areas"] = list(set(low_confidence_topics))

        return consensus

    async def _determine_winner(
        self,
        bull_arguments: List[Argument],
        bear_arguments: List[Argument],
        consensus: Dict[str, Any]
    ) -> Optional[DebatePosition]:
        """Determine debate winner based on argument strength and evidence."""
        bull_score = 0
        bear_score = 0

        # Score based on argument strength
        for arg in bull_arguments:
            bull_score += arg.strength.value * arg.confidence

        for arg in bear_arguments:
            bear_score += arg.strength.value * arg.confidence

        # Score based on evidence quality
        bull_score += len([e for arg in bull_arguments for e in arg.evidence]) * 0.5
        bear_score += len([e for arg in bear_arguments for e in arg.evidence]) * 0.5

        # Adjust for consensus agreement
        if len(consensus["agreed_facts"]) > 5:
            # Many agreed facts suggest neutral outcome
            diff = abs(bull_score - bear_score)
            if diff < 2:
                return DebatePosition.NEUTRAL

        if bull_score > bear_score * 1.2:
            return DebatePosition.BULLISH
        elif bear_score > bull_score * 1.2:
            return DebatePosition.BEARISH
        else:
            return DebatePosition.NEUTRAL

    async def _calculate_confidence_delta(
        self,
        bull_arguments: List[Argument],
        bear_arguments: List[Argument]
    ) -> float:
        """Calculate the confidence differential between positions."""
        bull_confidence = sum(arg.confidence for arg in bull_arguments) / len(bull_arguments)
        bear_confidence = sum(arg.confidence for arg in bear_arguments) / len(bear_arguments)
        return bull_confidence - bear_confidence

    async def _synthesize_debate(
        self,
        bull_arguments: List[Argument],
        bear_arguments: List[Argument],
        consensus: Dict[str, Any]
    ) -> str:
        """Synthesize debate into balanced conclusion."""
        synthesis = f"After thorough adversarial analysis, the following synthesis emerges:\n\n"

        # Summarize strongest arguments from each side
        strongest_bull = max(bull_arguments, key=lambda x: x.strength.value * x.confidence)
        strongest_bear = max(bear_arguments, key=lambda x: x.strength.value * x.confidence)

        synthesis += f"BULL CASE: {strongest_bull.claim}\n"
        synthesis += f"BEAR CASE: {strongest_bear.claim}\n\n"

        # Include consensus findings
        if consensus["agreed_facts"]:
            synthesis += f"AGREED FACTS: {len(consensus['agreed_facts'])} points of agreement found\n"

        if consensus["agreed_risks"]:
            synthesis += f"AGREED RISKS: {', '.join(consensus['agreed_risks'][:3])}\n"

        if consensus["divergence_points"]:
            synthesis += f"KEY DIVERGENCES: {len(consensus['divergence_points'])} major points of disagreement\n"

        # Provide balanced recommendation
        synthesis += "\nBALANCED PERSPECTIVE: "
        if len(bull_arguments) > len(bear_arguments):
            synthesis += "While bullish arguments dominate, bear concerns warrant careful consideration."
        elif len(bear_arguments) > len(bull_arguments):
            synthesis += "Despite bearish headwinds, bullish catalysts remain relevant."
        else:
            synthesis += "The debate reveals a genuinely balanced risk-reward profile."

        return synthesis

    async def _extract_key_insights(
        self,
        bull_arguments: List[Argument],
        bear_arguments: List[Argument],
        synthesis: str
    ) -> List[str]:
        """Extract key actionable insights from debate."""
        insights = []

        # Insight from strongest arguments
        strongest_bull = max(bull_arguments, key=lambda x: x.strength.value)
        strongest_bear = max(bear_arguments, key=lambda x: x.strength.value)

        insights.append(f"Primary upside driver: {self._simplify_claim(strongest_bull.claim)}")
        insights.append(f"Primary downside risk: {self._simplify_claim(strongest_bear.claim)}")

        # Insight from confidence levels
        avg_bull_confidence = sum(arg.confidence for arg in bull_arguments) / len(bull_arguments)
        avg_bear_confidence = sum(arg.confidence for arg in bear_arguments) / len(bear_arguments)

        if avg_bull_confidence > 0.7 and avg_bear_confidence < 0.5:
            insights.append("High conviction bullish opportunity identified")
        elif avg_bear_confidence > 0.7 and avg_bull_confidence < 0.5:
            insights.append("High conviction bearish signal detected")
        else:
            insights.append("Mixed signals suggest cautious approach")

        # Timing insight
        if any("short-term" in arg.claim.lower() for arg in bull_arguments):
            insights.append("Bullish catalysts appear near-term")
        if any("long-term" in arg.claim.lower() for arg in bear_arguments):
            insights.append("Bearish risks may materialize over longer timeframe")

        return insights

    def _claims_agree(self, claim1: str, claim2: str) -> bool:
        """Check if two claims agree."""
        # Simplified agreement detection
        claim1_lower = claim1.lower()
        claim2_lower = claim2.lower()

        agreement_terms = ["agree", "confirm", "support", "consistent"]
        disagreement_terms = ["disagree", "contrary", "oppose", "conflict"]

        for term in agreement_terms:
            if term in claim1_lower and term in claim2_lower:
                return True

        # Check for same sentiment
        positive_terms = ["growth", "increase", "improve", "strong", "bullish"]
        negative_terms = ["decline", "decrease", "weaken", "weak", "bearish"]

        claim1_positive = any(term in claim1_lower for term in positive_terms)
        claim2_positive = any(term in claim2_lower for term in positive_terms)

        return claim1_positive == claim2_positive

    def _claims_conflict(self, claim1: str, claim2: str) -> bool:
        """Check if two claims conflict."""
        return not self._claims_agree(claim1, claim2) and \
               any(term in claim1.lower() or term in claim2.lower()
                   for term in ["however", "but", "contrary", "despite", "although"])

    def _extract_common_fact(self, claim1: str, claim2: str) -> str:
        """Extract common fact from agreeing claims."""
        # Find common words (simplified)
        words1 = set(claim1.lower().split())
        words2 = set(claim2.lower().split())
        common = words1 & words2

        if len(common) > 3:
            return f"Both sides agree on: {' '.join(list(common)[:10])}"
        return "General agreement on market conditions"

    def _extract_risks(self, arguments: List[Argument]) -> List[str]:
        """Extract risk mentions from arguments."""
        risks = []
        risk_keywords = ["risk", "concern", "threat", "danger", "vulnerability", "exposure"]

        for arg in arguments:
            claim_lower = arg.claim.lower()
            for keyword in risk_keywords:
                if keyword in claim_lower:
                    # Extract the risk phrase
                    words = claim_lower.split()
                    idx = words.index(keyword)
                    start = max(0, idx - 2)
                    end = min(len(words), idx + 3)
                    risk_phrase = " ".join(words[start:end])
                    risks.append(risk_phrase)

        return list(set(risks))

    def _simplify_claim(self, claim: str) -> str:
        """Simplify claim to key message."""
        # Remove filler words
        filler = ["the", "a", "an", "and", "or", "but", "in", "on", "at", "to", "for"]
        words = claim.split()
        simplified = [w for w in words if w.lower() not in filler]
        return " ".join(simplified[:10])


class BullAgent:
    """Agent that argues bullish perspective."""

    def __init__(self, llm=None):
        self.llm = llm
        self.position = DebatePosition.BULLISH

    async def make_argument(
        self,
        topic: str,
        context: Dict[str, Any],
        previous_arguments: List[Argument],
        round_num: int
    ) -> Argument:
        """Make a bullish argument."""
        # Generate bullish argument based on context
        claim = await self._generate_bullish_claim(topic, context, round_num)
        evidence = await self._gather_bullish_evidence(context)
        strength = await self._assess_argument_strength(claim, evidence)
        confidence = await self._calculate_confidence(evidence, context)

        return Argument(
            position=self.position,
            claim=claim,
            evidence=evidence,
            strength=strength,
            confidence=confidence
        )

    async def generate_rebuttals(self, opposing_argument: Argument) -> List[str]:
        """Generate rebuttals to opposing argument."""
        rebuttals = []

        # Challenge evidence
        if opposing_argument.confidence < 0.6:
            rebuttals.append(f"The bearish view lacks strong evidence (confidence: {opposing_argument.confidence:.2f})")

        # Provide counter-evidence
        rebuttals.append("Historical data shows resilience in similar conditions")

        # Question assumptions
        rebuttals.append("This pessimistic view underestimates growth potential")

        return rebuttals

    async def _generate_bullish_claim(self, topic: str, context: Dict[str, Any], round_num: int) -> str:
        """Generate a bullish claim."""
        claims = [
            f"{topic} presents strong growth opportunity based on market dynamics",
            f"Technical indicators suggest upward momentum for {topic}",
            f"Fundamental strength supports bullish outlook on {topic}",
            f"Market positioning favors continued appreciation in {topic}",
            f"Risk-reward profile tilts positively for {topic}"
        ]

        # Vary claim by round
        if round_num < len(claims):
            return claims[round_num]
        return claims[0]

    async def _gather_bullish_evidence(self, context: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Gather evidence supporting bullish view."""
        evidence = []

        # Extract positive indicators from context
        if context.get("price_trend") == "up":
            evidence.append({
                "type": "price_action",
                "data": "Positive price trend observed",
                "weight": 0.8
            })

        if context.get("earnings_growth", 0) > 0:
            evidence.append({
                "type": "fundamental",
                "data": f"Earnings growth: {context.get('earnings_growth', 0)}%",
                "weight": 0.9
            })

        if context.get("sentiment_score", 0) > 0.5:
            evidence.append({
                "type": "sentiment",
                "data": f"Positive market sentiment: {context.get('sentiment_score', 0):.2f}",
                "weight": 0.7
            })

        return evidence

    async def _assess_argument_strength(self, claim: str, evidence: List[Dict]) -> ArgumentStrength:
        """Assess strength of argument."""
        if len(evidence) >= 3:
            return ArgumentStrength.STRONG
        elif len(evidence) >= 2:
            return ArgumentStrength.MODERATE
        else:
            return ArgumentStrength.WEAK

    async def _calculate_confidence(self, evidence: List[Dict], context: Dict[str, Any]) -> float:
        """Calculate confidence in argument."""
        if not evidence:
            return 0.3

        # Base confidence on evidence weight
        weights = [e.get("weight", 0.5) for e in evidence]
        return min(sum(weights) / len(weights), 1.0)


class BearAgent:
    """Agent that argues bearish perspective."""

    def __init__(self, llm=None):
        self.llm = llm
        self.position = DebatePosition.BEARISH

    async def make_argument(
        self,
        topic: str,
        context: Dict[str, Any],
        previous_arguments: List[Argument],
        round_num: int
    ) -> Argument:
        """Make a bearish argument."""
        claim = await self._generate_bearish_claim(topic, context, round_num)
        evidence = await self._gather_bearish_evidence(context)
        strength = await self._assess_argument_strength(claim, evidence)
        confidence = await self._calculate_confidence(evidence, context)

        return Argument(
            position=self.position,
            claim=claim,
            evidence=evidence,
            strength=strength,
            confidence=confidence
        )

    async def generate_rebuttals(self, opposing_argument: Argument) -> List[str]:
        """Generate rebuttals to opposing argument."""
        rebuttals = []

        # Point out risks ignored
        rebuttals.append("The bullish view overlooks significant downside risks")

        # Historical precedent
        rebuttals.append("Similar optimism preceded previous market corrections")

        # Valuation concerns
        rebuttals.append("Current valuations leave little room for error")

        return rebuttals

    async def _generate_bearish_claim(self, topic: str, context: Dict[str, Any], round_num: int) -> str:
        """Generate a bearish claim."""
        claims = [
            f"{topic} faces significant headwinds that limit upside potential",
            f"Technical breakdown signals caution for {topic}",
            f"Fundamental deterioration undermines {topic} investment case",
            f"Risk factors outweigh potential rewards for {topic}",
            f"Market conditions suggest defensive positioning on {topic}"
        ]

        if round_num < len(claims):
            return claims[round_num]
        return claims[0]

    async def _gather_bearish_evidence(self, context: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Gather evidence supporting bearish view."""
        evidence = []

        if context.get("price_trend") == "down":
            evidence.append({
                "type": "price_action",
                "data": "Negative price trend observed",
                "weight": 0.8
            })

        if context.get("debt_ratio", 0) > 0.6:
            evidence.append({
                "type": "fundamental",
                "data": f"High debt ratio: {context.get('debt_ratio', 0):.2f}",
                "weight": 0.7
            })

        if context.get("volatility", 0) > 0.3:
            evidence.append({
                "type": "risk",
                "data": f"Elevated volatility: {context.get('volatility', 0):.2f}",
                "weight": 0.6
            })

        return evidence

    async def _assess_argument_strength(self, claim: str, evidence: List[Dict]) -> ArgumentStrength:
        """Assess strength of argument."""
        if len(evidence) >= 3 and any(e.get("weight", 0) > 0.8 for e in evidence):
            return ArgumentStrength.COMPELLING
        elif len(evidence) >= 2:
            return ArgumentStrength.MODERATE
        else:
            return ArgumentStrength.WEAK

    async def _calculate_confidence(self, evidence: List[Dict], context: Dict[str, Any]) -> float:
        """Calculate confidence in argument."""
        if not evidence:
            return 0.3

        weights = [e.get("weight", 0.5) for e in evidence]
        base_confidence = sum(weights) / len(weights)

        # Adjust for market conditions
        if context.get("market_condition") == "bear_market":
            base_confidence *= 1.2

        return min(base_confidence, 1.0)