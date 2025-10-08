"""
Personality-Driven Analysis System
Customizes agent behavior based on selected AI personality
"""

import logging
from typing import Dict, Any, List, Optional
from dataclasses import dataclass
from enum import Enum
from agents.base_agent import BaseAgent

logger = logging.getLogger(__name__)


class PersonalityType(Enum):
    """Available AI personality types."""
    BUFFETT = "buffett"  # Conservative Sage
    WOOD = "wood"  # Growth Innovator
    QUANT = "quant"  # Data Scientist
    DALIO = "dalio"  # Balanced Strategist
    LYNCH = "lynch"  # Opportunity Hunter


@dataclass
class PersonalityProfile:
    """Profile for each AI personality."""
    name: str
    style: str
    risk_preference: float  # 0.0 (conservative) to 1.0 (aggressive)
    time_horizon: str
    key_metrics: List[str]
    analysis_focus: List[str]
    communication_style: str
    decision_framework: Dict[str, Any]


class PersonalityDrivenAgent(BaseAgent):
    """Agent that adapts its analysis based on selected personality."""

    # Define personality profiles
    PERSONALITIES = {
        PersonalityType.BUFFETT: PersonalityProfile(
            name="Conservative Sage",
            style="Value investing with margin of safety",
            risk_preference=0.3,
            time_horizon="long-term",
            key_metrics=["P/E", "P/B", "ROE", "Debt/Equity", "FCF"],
            analysis_focus=["fundamentals", "moat", "management", "intrinsic_value"],
            communication_style="wise and measured",
            decision_framework={
                "buy_criteria": ["undervalued", "strong_fundamentals", "competitive_advantage"],
                "sell_criteria": ["overvalued", "deteriorating_fundamentals", "lost_moat"],
                "hold_criteria": ["fair_value", "stable_business", "good_management"]
            }
        ),

        PersonalityType.WOOD: PersonalityProfile(
            name="Growth Innovator",
            style="Disruptive innovation and exponential growth",
            risk_preference=0.8,
            time_horizon="medium-to-long-term",
            key_metrics=["Revenue Growth", "TAM", "Innovation Score", "R&D Spend", "Market Share"],
            analysis_focus=["innovation", "disruption", "scalability", "technology"],
            communication_style="visionary and bold",
            decision_framework={
                "buy_criteria": ["disruptive_technology", "massive_TAM", "exponential_growth"],
                "sell_criteria": ["innovation_stagnation", "competition_catching_up", "market_saturation"],
                "hold_criteria": ["continued_innovation", "market_expansion", "execution_on_track"]
            }
        ),

        PersonalityType.QUANT: PersonalityProfile(
            name="Data Scientist",
            style="Quantitative analysis and algorithmic patterns",
            risk_preference=0.5,
            time_horizon="varies",
            key_metrics=["Sharpe Ratio", "Beta", "Alpha", "Correlation", "Volatility"],
            analysis_focus=["statistical_patterns", "technical_indicators", "risk_metrics", "backtesting"],
            communication_style="analytical and precise",
            decision_framework={
                "buy_criteria": ["positive_signals", "risk_reward_favorable", "momentum_confirmed"],
                "sell_criteria": ["signal_reversal", "risk_exceeded", "pattern_breakdown"],
                "hold_criteria": ["neutral_signals", "within_parameters", "trend_continuation"]
            }
        ),

        PersonalityType.DALIO: PersonalityProfile(
            name="Balanced Strategist",
            style="Principles-based investing with risk parity",
            risk_preference=0.5,
            time_horizon="all-weather",
            key_metrics=["Correlation", "Risk Parity", "Economic Indicators", "Debt Cycles", "Portfolio Balance"],
            analysis_focus=["macroeconomics", "diversification", "risk_management", "cycles"],
            communication_style="systematic and educational",
            decision_framework={
                "buy_criteria": ["portfolio_balance_needed", "cycle_positioning", "risk_parity"],
                "sell_criteria": ["overweight_position", "cycle_turning", "correlation_breakdown"],
                "hold_criteria": ["balanced_allocation", "cycle_stable", "diversification_intact"]
            }
        ),

        PersonalityType.LYNCH: PersonalityProfile(
            name="Opportunity Hunter",
            style="Finding hidden gems before the crowd",
            risk_preference=0.6,
            time_horizon="medium-term",
            key_metrics=["PEG Ratio", "Earnings Growth", "Insider Buying", "Market Neglect", "Local Knowledge"],
            analysis_focus=["undiscovered_opportunities", "growth_at_reasonable_price", "company_visits", "scuttlebutt"],
            communication_style="practical and enthusiastic",
            decision_framework={
                "buy_criteria": ["undiscovered_gem", "peg_under_1", "strong_story", "insider_buying"],
                "sell_criteria": ["overvalued_peg", "story_changed", "too_popular", "fundamentals_deteriorating"],
                "hold_criteria": ["story_intact", "reasonable_valuation", "growth_continuing"]
            }
        )
    }

    def __init__(self, personality_type: PersonalityType):
        """Initialize with specific personality."""
        super().__init__(name=f"PersonalityAgent_{personality_type.value}")
        self.personality_type = personality_type
        self.profile = self.PERSONALITIES[personality_type]
        logger.info(f"Initialized {self.profile.name} personality agent")

    async def execute(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """Execute analysis with personality-driven approach."""
        query = state.get("query", "")
        symbol = state.get("symbol", "")
        market_data = state.get("market_data", {})

        # Perform personality-specific analysis
        analysis = await self.analyze_with_personality(symbol, market_data, query)

        # Apply decision framework
        recommendation = await self.make_recommendation(analysis, market_data)

        # Generate personality-specific insights
        insights = await self.generate_insights(analysis, recommendation)

        # Format response in personality style
        response = await self.format_response(analysis, recommendation, insights)

        return {
            "personality": self.personality_type.value,
            "analysis": analysis,
            "recommendation": recommendation,
            "insights": insights,
            "response": response,
            "confidence": analysis.get("confidence", 0.5),
            "risk_assessment": analysis.get("risk_assessment", {})
        }

    async def analyze_with_personality(
        self,
        symbol: str,
        market_data: Dict[str, Any],
        query: str
    ) -> Dict[str, Any]:
        """Perform analysis based on personality focus areas."""
        analysis = {
            "symbol": symbol,
            "personality_perspective": self.profile.name,
            "key_findings": [],
            "metrics_analysis": {},
            "confidence": 0.5
        }

        # Analyze key metrics based on personality
        for metric in self.profile.key_metrics:
            if metric in market_data:
                analysis["metrics_analysis"][metric] = await self.evaluate_metric(
                    metric,
                    market_data[metric]
                )

        # Focus on personality-specific areas
        for focus_area in self.profile.analysis_focus:
            finding = await self.analyze_focus_area(focus_area, market_data, symbol)
            if finding:
                analysis["key_findings"].append(finding)

        # Adjust confidence based on personality risk preference
        analysis["confidence"] = await self.calculate_confidence(
            market_data,
            self.profile.risk_preference
        )

        # Add risk assessment from personality perspective
        analysis["risk_assessment"] = await self.assess_risk_personality(
            market_data,
            self.profile.risk_preference
        )

        return analysis

    async def evaluate_metric(self, metric: str, value: Any) -> Dict[str, Any]:
        """Evaluate a metric from personality perspective."""
        evaluation = {
            "value": value,
            "assessment": "",
            "importance": "medium"
        }

        # Personality-specific metric evaluation
        if self.personality_type == PersonalityType.BUFFETT:
            if metric == "P/E" and isinstance(value, (int, float)):
                if value < 15:
                    evaluation["assessment"] = "Attractive valuation"
                    evaluation["importance"] = "high"
                elif value > 25:
                    evaluation["assessment"] = "Potentially overvalued"
                    evaluation["importance"] = "high"
                else:
                    evaluation["assessment"] = "Fair valuation"

        elif self.personality_type == PersonalityType.WOOD:
            if metric == "Revenue Growth" and isinstance(value, (int, float)):
                if value > 40:
                    evaluation["assessment"] = "Exceptional growth"
                    evaluation["importance"] = "high"
                elif value > 20:
                    evaluation["assessment"] = "Strong growth"
                else:
                    evaluation["assessment"] = "Moderate growth"

        elif self.personality_type == PersonalityType.QUANT:
            if metric == "Sharpe Ratio" and isinstance(value, (int, float)):
                if value > 2:
                    evaluation["assessment"] = "Excellent risk-adjusted returns"
                    evaluation["importance"] = "high"
                elif value > 1:
                    evaluation["assessment"] = "Good risk-adjusted returns"
                else:
                    evaluation["assessment"] = "Suboptimal risk-adjusted returns"

        elif self.personality_type == PersonalityType.DALIO:
            if metric == "Correlation" and isinstance(value, (int, float)):
                if abs(value) < 0.3:
                    evaluation["assessment"] = "Good diversification potential"
                    evaluation["importance"] = "high"
                else:
                    evaluation["assessment"] = "High correlation, limited diversification"

        elif self.personality_type == PersonalityType.LYNCH:
            if metric == "PEG Ratio" and isinstance(value, (int, float)):
                if value < 1:
                    evaluation["assessment"] = "Growth at a reasonable price"
                    evaluation["importance"] = "high"
                elif value > 2:
                    evaluation["assessment"] = "Expensive relative to growth"
                else:
                    evaluation["assessment"] = "Fair value for growth"

        return evaluation

    async def analyze_focus_area(
        self,
        focus_area: str,
        market_data: Dict[str, Any],
        symbol: str
    ) -> Optional[Dict[str, Any]]:
        """Analyze specific focus area based on personality."""
        finding = {
            "area": focus_area,
            "observation": "",
            "significance": "medium"
        }

        if self.personality_type == PersonalityType.BUFFETT:
            if focus_area == "moat":
                # Analyze competitive advantage
                if market_data.get("market_share", 0) > 30:
                    finding["observation"] = f"{symbol} demonstrates strong competitive moat with significant market share"
                    finding["significance"] = "high"
                    return finding

            elif focus_area == "intrinsic_value":
                # Calculate intrinsic value (simplified)
                pe = market_data.get("P/E", 20)
                growth = market_data.get("earnings_growth", 5)
                if pe < 15 and growth > 10:
                    finding["observation"] = "Trading below intrinsic value with strong growth"
                    finding["significance"] = "high"
                    return finding

        elif self.personality_type == PersonalityType.WOOD:
            if focus_area == "innovation":
                rd_ratio = market_data.get("rd_revenue_ratio", 0)
                if rd_ratio > 0.15:
                    finding["observation"] = f"High R&D investment ({rd_ratio:.1%}) indicates strong innovation focus"
                    finding["significance"] = "high"
                    return finding

            elif focus_area == "disruption":
                if market_data.get("disruptive_score", 0) > 7:
                    finding["observation"] = "Company positioned as industry disruptor"
                    finding["significance"] = "high"
                    return finding

        elif self.personality_type == PersonalityType.QUANT:
            if focus_area == "statistical_patterns":
                rsi = market_data.get("rsi", 50)
                if rsi < 30:
                    finding["observation"] = "Oversold condition detected (RSI < 30)"
                    finding["significance"] = "high"
                    return finding
                elif rsi > 70:
                    finding["observation"] = "Overbought condition detected (RSI > 70)"
                    finding["significance"] = "high"
                    return finding

        elif self.personality_type == PersonalityType.DALIO:
            if focus_area == "macroeconomics":
                if market_data.get("economic_sensitivity", 0) > 0.7:
                    finding["observation"] = "High sensitivity to macroeconomic cycles"
                    finding["significance"] = "high"
                    return finding

        elif self.personality_type == PersonalityType.LYNCH:
            if focus_area == "undiscovered_opportunities":
                analyst_coverage = market_data.get("analyst_coverage", 10)
                if analyst_coverage < 3:
                    finding["observation"] = "Limited analyst coverage suggests undiscovered opportunity"
                    finding["significance"] = "high"
                    return finding

        return None

    async def make_recommendation(
        self,
        analysis: Dict[str, Any],
        market_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Make recommendation based on personality decision framework."""
        framework = self.profile.decision_framework
        recommendation = {
            "action": "hold",
            "confidence": 0.5,
            "reasoning": [],
            "time_horizon": self.profile.time_horizon
        }

        buy_signals = 0
        sell_signals = 0
        total_criteria = 0

        # Check buy criteria
        for criterion in framework["buy_criteria"]:
            total_criteria += 1
            if await self.check_criterion(criterion, analysis, market_data):
                buy_signals += 1
                recommendation["reasoning"].append(f"Buy signal: {criterion}")

        # Check sell criteria
        for criterion in framework["sell_criteria"]:
            total_criteria += 1
            if await self.check_criterion(criterion, analysis, market_data):
                sell_signals += 1
                recommendation["reasoning"].append(f"Sell signal: {criterion}")

        # Determine recommendation
        buy_strength = buy_signals / len(framework["buy_criteria"]) if framework["buy_criteria"] else 0
        sell_strength = sell_signals / len(framework["sell_criteria"]) if framework["sell_criteria"] else 0

        if buy_strength > 0.6 and sell_strength < 0.3:
            recommendation["action"] = "buy"
            recommendation["confidence"] = buy_strength
        elif sell_strength > 0.6 and buy_strength < 0.3:
            recommendation["action"] = "sell"
            recommendation["confidence"] = sell_strength
        else:
            recommendation["action"] = "hold"
            recommendation["confidence"] = 1 - abs(buy_strength - sell_strength)

        # Add personality-specific context
        recommendation["personality_context"] = f"{self.profile.name} perspective on {self.profile.style}"

        return recommendation

    async def check_criterion(
        self,
        criterion: str,
        analysis: Dict[str, Any],
        market_data: Dict[str, Any]
    ) -> bool:
        """Check if a specific criterion is met."""
        # Simplified criterion checking
        if criterion == "undervalued":
            return market_data.get("P/E", 20) < 15

        elif criterion == "strong_fundamentals":
            return market_data.get("roe", 0) > 15 and market_data.get("debt_equity", 1) < 0.5

        elif criterion == "disruptive_technology":
            return market_data.get("innovation_score", 0) > 7

        elif criterion == "massive_TAM":
            return market_data.get("tam_billions", 0) > 100

        elif criterion == "positive_signals":
            return market_data.get("technical_score", 0) > 7

        elif criterion == "portfolio_balance_needed":
            return market_data.get("portfolio_weight", 0) < 5

        elif criterion == "undiscovered_gem":
            return market_data.get("analyst_coverage", 10) < 3 and market_data.get("peg", 2) < 1

        return False

    async def generate_insights(
        self,
        analysis: Dict[str, Any],
        recommendation: Dict[str, Any]
    ) -> List[str]:
        """Generate personality-specific insights."""
        insights = []

        # Add personality signature insight
        if self.personality_type == PersonalityType.BUFFETT:
            insights.append("Focus on long-term value creation over short-term volatility")
            if recommendation["action"] == "buy":
                insights.append("Margin of safety present at current levels")

        elif self.personality_type == PersonalityType.WOOD:
            insights.append("Innovation potential outweighs traditional valuation concerns")
            if analysis.get("key_findings"):
                insights.append("Disruptive technology adoption accelerating")

        elif self.personality_type == PersonalityType.QUANT:
            insights.append("Statistical models indicate clear directional bias")
            confidence = analysis.get("confidence", 0.5)
            insights.append(f"Model confidence: {confidence:.1%}")

        elif self.personality_type == PersonalityType.DALIO:
            insights.append("Position aligns with all-weather portfolio principles")
            insights.append("Consider correlation with existing holdings")

        elif self.personality_type == PersonalityType.LYNCH:
            insights.append("Story remains intact with room for multiple expansion")
            if recommendation["action"] == "buy":
                insights.append("Classic 'ten-bagger' potential identified")

        # Add risk-adjusted insight
        risk_level = analysis.get("risk_assessment", {}).get("level", "medium")
        insights.append(f"Risk assessment: {risk_level} (adjusted for {self.profile.name} approach)")

        return insights

    async def format_response(
        self,
        analysis: Dict[str, Any],
        recommendation: Dict[str, Any],
        insights: List[str]
    ) -> str:
        """Format response in personality's communication style."""
        response = f"**{self.profile.name} Analysis**\n\n"

        # Opening statement in personality style
        if self.personality_type == PersonalityType.BUFFETT:
            response += "As I always say, 'Be fearful when others are greedy, and greedy when others are fearful.'\n\n"

        elif self.personality_type == PersonalityType.WOOD:
            response += "Innovation is the key to exponential growth. Let's look at the disruptive potential.\n\n"

        elif self.personality_type == PersonalityType.QUANT:
            response += "The data reveals patterns that human intuition might miss. Here's what the numbers say.\n\n"

        elif self.personality_type == PersonalityType.DALIO:
            response += "Principles-based analysis reveals the following systematic observations.\n\n"

        elif self.personality_type == PersonalityType.LYNCH:
            response += "The best opportunities are often hiding in plain sight. Here's what I found.\n\n"

        # Add analysis summary
        response += f"**Key Findings:**\n"
        for finding in analysis.get("key_findings", [])[:3]:
            if finding:
                response += f"• {finding.get('observation', '')}\n"

        # Add recommendation
        action = recommendation["action"].upper()
        confidence = recommendation["confidence"]
        response += f"\n**Recommendation:** {action} (Confidence: {confidence:.1%})\n"

        # Add reasoning
        if recommendation.get("reasoning"):
            response += "\n**Reasoning:**\n"
            for reason in recommendation["reasoning"][:3]:
                response += f"• {reason}\n"

        # Add insights
        response += "\n**Key Insights:**\n"
        for insight in insights:
            response += f"• {insight}\n"

        # Closing statement
        response += f"\n*Analysis conducted with {self.profile.time_horizon} perspective using {self.profile.style}.*"

        return response

    async def calculate_confidence(
        self,
        market_data: Dict[str, Any],
        risk_preference: float
    ) -> float:
        """Calculate confidence based on personality risk preference."""
        base_confidence = 0.5

        # Adjust based on data quality
        if market_data:
            base_confidence += 0.1

        # Adjust based on personality risk preference
        if risk_preference > 0.7:  # Aggressive personalities are more confident
            base_confidence *= 1.2
        elif risk_preference < 0.3:  # Conservative personalities are more cautious
            base_confidence *= 0.8

        # Cap between 0 and 1
        return min(max(base_confidence, 0.1), 0.95)

    async def assess_risk_personality(
        self,
        market_data: Dict[str, Any],
        risk_preference: float
    ) -> Dict[str, Any]:
        """Assess risk from personality perspective."""
        volatility = market_data.get("volatility", 0.2)
        beta = market_data.get("beta", 1.0)

        # Base risk assessment
        risk_score = (volatility + abs(beta - 1)) / 2

        # Adjust perception based on personality
        if risk_preference > 0.7:
            # Aggressive personalities downplay risk
            risk_score *= 0.7
        elif risk_preference < 0.3:
            # Conservative personalities emphasize risk
            risk_score *= 1.3

        # Determine risk level
        if risk_score < 0.3:
            level = "low"
        elif risk_score < 0.6:
            level = "medium"
        else:
            level = "high"

        return {
            "score": risk_score,
            "level": level,
            "volatility": volatility,
            "beta": beta,
            "personality_adjustment": f"Risk viewed through {self.profile.name} lens"
        }