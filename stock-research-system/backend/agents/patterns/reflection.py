"""
Reflection Pattern for Multi-Agent System
Enables agents to review and improve their own outputs
"""

import logging
from typing import Dict, Any, Optional, List, Tuple
from dataclasses import dataclass
from enum import Enum
import asyncio

logger = logging.getLogger(__name__)


class ReflectionType(Enum):
    """Types of reflection patterns."""
    SELF_CRITIQUE = "self_critique"
    PEER_REVIEW = "peer_review"
    ITERATIVE_REFINEMENT = "iterative_refinement"
    CONFIDENCE_ASSESSMENT = "confidence_assessment"


@dataclass
class ReflectionResult:
    """Result of reflection process."""
    original_output: Any
    refined_output: Any
    confidence_before: float
    confidence_after: float
    improvements: List[str]
    issues_found: List[str]
    reflection_type: ReflectionType
    iterations: int


class ReflectionMixin:
    """Mixin class to add reflection capabilities to any agent."""

    async def reflect_on_output(
        self,
        output: Any,
        context: Dict[str, Any],
        reflection_type: ReflectionType = ReflectionType.SELF_CRITIQUE,
        max_iterations: int = 3
    ) -> ReflectionResult:
        """
        Reflect on and potentially improve an output.

        Args:
            output: The output to reflect on
            context: Context information for reflection
            reflection_type: Type of reflection to perform
            max_iterations: Maximum refinement iterations

        Returns:
            ReflectionResult with refined output and metadata
        """
        original_output = output
        confidence_before = await self._assess_confidence(output, context)

        issues_found = []
        improvements = []
        iterations = 0

        if reflection_type == ReflectionType.SELF_CRITIQUE:
            output, issues, improvements = await self._self_critique(output, context)
            iterations = 1

        elif reflection_type == ReflectionType.ITERATIVE_REFINEMENT:
            for i in range(max_iterations):
                new_output, found_issues = await self._refine_iteration(output, context)
                if found_issues:
                    issues_found.extend(found_issues)
                    output = new_output
                    iterations += 1
                    improvements.append(f"Iteration {i+1} improvements applied")
                else:
                    break

        elif reflection_type == ReflectionType.CONFIDENCE_ASSESSMENT:
            output, confidence_details = await self._assess_with_confidence(output, context)
            improvements = confidence_details

        confidence_after = await self._assess_confidence(output, context)

        return ReflectionResult(
            original_output=original_output,
            refined_output=output,
            confidence_before=confidence_before,
            confidence_after=confidence_after,
            improvements=improvements,
            issues_found=issues_found,
            reflection_type=reflection_type,
            iterations=iterations
        )

    async def _self_critique(
        self,
        output: Any,
        context: Dict[str, Any]
    ) -> Tuple[Any, List[str], List[str]]:
        """
        Perform self-critique on the output.

        Returns:
            Tuple of (refined_output, issues_found, improvements_made)
        """
        issues = []
        improvements = []

        # Check for completeness
        if isinstance(output, dict):
            if "analysis" in output and len(output.get("analysis", "")) < 100:
                issues.append("Analysis is too brief")
                output["analysis"] = await self._expand_analysis(output["analysis"], context)
                improvements.append("Expanded analysis with more detail")

            if "recommendations" in output and not output.get("recommendations"):
                issues.append("Missing recommendations")
                output["recommendations"] = await self._generate_recommendations(context)
                improvements.append("Added actionable recommendations")

            if "confidence" not in output:
                issues.append("Missing confidence score")
                output["confidence"] = await self._assess_confidence(output, context)
                improvements.append("Added confidence assessment")

        # Check for accuracy and consistency
        inconsistencies = await self._check_consistency(output, context)
        if inconsistencies:
            issues.extend(inconsistencies)
            output = await self._fix_inconsistencies(output, inconsistencies, context)
            improvements.append(f"Fixed {len(inconsistencies)} inconsistencies")

        return output, issues, improvements

    async def _refine_iteration(
        self,
        output: Any,
        context: Dict[str, Any]
    ) -> Tuple[Any, List[str]]:
        """
        Single iteration of refinement.

        Returns:
            Tuple of (refined_output, issues_found)
        """
        issues = []

        # Check quality metrics
        quality_score = await self._assess_quality(output, context)

        if quality_score < 0.7:
            issues.append(f"Quality score below threshold: {quality_score}")

            # Identify specific improvements
            if "clarity" in context.get("requirements", []):
                output = await self._improve_clarity(output, context)

            if "depth" in context.get("requirements", []):
                output = await self._add_depth(output, context)

            if "evidence" in context.get("requirements", []):
                output = await self._add_evidence(output, context)

        return output, issues

    async def _assess_confidence(
        self,
        output: Any,
        context: Dict[str, Any]
    ) -> float:
        """Assess confidence in the output."""
        confidence = 0.5  # Base confidence

        # Adjust based on data quality
        if context.get("data_sources"):
            confidence += 0.1 * min(len(context["data_sources"]), 3)

        # Adjust based on consistency
        if not await self._check_consistency(output, context):
            confidence += 0.2

        # Adjust based on completeness
        if isinstance(output, dict):
            required_fields = ["analysis", "recommendations", "risks", "confidence"]
            present_fields = sum(1 for field in required_fields if field in output)
            confidence += 0.1 * (present_fields / len(required_fields))

        return min(confidence, 1.0)

    async def _check_consistency(
        self,
        output: Any,
        context: Dict[str, Any]
    ) -> List[str]:
        """Check for inconsistencies in the output."""
        inconsistencies = []

        if isinstance(output, dict):
            # Check numerical consistency
            if "metrics" in output:
                metrics = output["metrics"]
                if isinstance(metrics, dict):
                    # Example: Check if percentages add up correctly
                    if "allocation" in metrics:
                        total = sum(metrics["allocation"].values())
                        if abs(total - 100) > 0.01:
                            inconsistencies.append(f"Allocation percentages sum to {total}, not 100%")

            # Check logical consistency
            if "recommendation" in output and "risks" in output:
                rec = output["recommendation"].lower()
                risks = output["risks"]
                if "buy" in rec and len(risks) > 5:
                    inconsistencies.append("Strong buy recommendation despite numerous risks")

        return inconsistencies

    async def _fix_inconsistencies(
        self,
        output: Any,
        inconsistencies: List[str],
        context: Dict[str, Any]
    ) -> Any:
        """Fix identified inconsistencies."""
        for issue in inconsistencies:
            if "Allocation percentages" in issue:
                # Normalize allocations
                if "metrics" in output and "allocation" in output["metrics"]:
                    total = sum(output["metrics"]["allocation"].values())
                    if total > 0:
                        output["metrics"]["allocation"] = {
                            k: (v / total) * 100
                            for k, v in output["metrics"]["allocation"].items()
                        }

            elif "recommendation despite" in issue:
                # Adjust recommendation based on risks
                if len(output.get("risks", [])) > 5:
                    output["recommendation"] = output.get("recommendation", "").replace(
                        "Strong Buy", "Hold with Caution"
                    )

        return output

    async def _assess_quality(
        self,
        output: Any,
        context: Dict[str, Any]
    ) -> float:
        """Assess overall quality of the output."""
        quality_score = 0.0
        weights = {
            "completeness": 0.3,
            "accuracy": 0.3,
            "clarity": 0.2,
            "relevance": 0.2
        }

        # Completeness check
        if isinstance(output, dict):
            expected_keys = context.get("expected_output_keys", ["analysis", "recommendations"])
            completeness = sum(1 for k in expected_keys if k in output) / len(expected_keys)
            quality_score += weights["completeness"] * completeness

        # Clarity check (simplified - check for structure)
        if isinstance(output, str):
            has_structure = any(marker in output for marker in ["1.", "•", "-", "\n\n"])
            quality_score += weights["clarity"] * (1.0 if has_structure else 0.5)

        # Relevance check
        if context.get("query"):
            query_terms = context["query"].lower().split()
            output_str = str(output).lower()
            relevance = sum(1 for term in query_terms if term in output_str) / len(query_terms)
            quality_score += weights["relevance"] * relevance

        # Accuracy (simplified - no errors detected)
        quality_score += weights["accuracy"] * 0.8  # Base accuracy

        return quality_score

    async def _improve_clarity(self, output: Any, context: Dict[str, Any]) -> Any:
        """Improve clarity of the output."""
        if isinstance(output, str):
            # Add structure
            lines = output.split(". ")
            if len(lines) > 3:
                structured = "Key Points:\n"
                for i, line in enumerate(lines[:5], 1):
                    structured += f"{i}. {line}.\n"
                if len(lines) > 5:
                    structured += f"\nAdditional Details:\n{'. '.join(lines[5:])}"
                output = structured

        elif isinstance(output, dict):
            # Ensure clear structure
            if "summary" not in output and "analysis" in output:
                output["summary"] = output["analysis"][:200] + "..."

        return output

    async def _add_depth(self, output: Any, context: Dict[str, Any]) -> Any:
        """Add more depth to the analysis."""
        if isinstance(output, dict):
            if "analysis" in output:
                # Add more analytical dimensions
                if "technical_analysis" not in output:
                    output["technical_analysis"] = "Technical indicators suggest..."
                if "fundamental_analysis" not in output:
                    output["fundamental_analysis"] = "Fundamental metrics indicate..."
                if "market_context" not in output:
                    output["market_context"] = "In the context of current market conditions..."

        return output

    async def _add_evidence(self, output: Any, context: Dict[str, Any]) -> Any:
        """Add supporting evidence to claims."""
        if isinstance(output, dict):
            if "claims" in output or "analysis" in output:
                if "evidence" not in output:
                    output["evidence"] = []

                # Add data points as evidence
                if context.get("data_sources"):
                    for source in context["data_sources"][:3]:
                        output["evidence"].append({
                            "source": source.get("name", "Unknown"),
                            "data": source.get("data", {}),
                            "relevance": "Supports primary analysis"
                        })

        return output

    async def _expand_analysis(self, analysis: str, context: Dict[str, Any]) -> str:
        """Expand brief analysis with more detail."""
        if len(analysis) < 100:
            expansion = f"{analysis}\n\nFurther analysis reveals several key factors:\n"

            # Add contextual expansions
            if context.get("symbol"):
                expansion += f"1. Market position of {context['symbol']} remains strong.\n"
            if context.get("timeframe"):
                expansion += f"2. Over the {context['timeframe']} timeframe, trends indicate positive momentum.\n"
            if context.get("sector"):
                expansion += f"3. Within the {context['sector']} sector, comparative performance is favorable.\n"

            return expansion
        return analysis

    async def _generate_recommendations(self, context: Dict[str, Any]) -> List[str]:
        """Generate recommendations based on context."""
        recommendations = []

        if context.get("risk_level") == "low":
            recommendations.append("Consider increasing position size given low risk profile")
        elif context.get("risk_level") == "high":
            recommendations.append("Implement stop-loss orders to manage downside risk")

        if context.get("trend") == "bullish":
            recommendations.append("Monitor for continuation patterns in technical indicators")
        elif context.get("trend") == "bearish":
            recommendations.append("Wait for reversal confirmation before entering positions")

        if not recommendations:
            recommendations.append("Continue monitoring for optimal entry points")

        return recommendations

    async def _assess_with_confidence(
        self,
        output: Any,
        context: Dict[str, Any]
    ) -> Tuple[Any, List[str]]:
        """Assess output and provide confidence details."""
        confidence_details = []

        # Assess different aspects
        data_confidence = await self._assess_data_confidence(context)
        confidence_details.append(f"Data confidence: {data_confidence:.2f}")

        analysis_confidence = await self._assess_analysis_confidence(output, context)
        confidence_details.append(f"Analysis confidence: {analysis_confidence:.2f}")

        prediction_confidence = await self._assess_prediction_confidence(output, context)
        confidence_details.append(f"Prediction confidence: {prediction_confidence:.2f}")

        # Add confidence breakdown to output
        if isinstance(output, dict):
            output["confidence_breakdown"] = {
                "data": data_confidence,
                "analysis": analysis_confidence,
                "prediction": prediction_confidence,
                "overall": (data_confidence + analysis_confidence + prediction_confidence) / 3
            }

        return output, confidence_details

    async def _assess_data_confidence(self, context: Dict[str, Any]) -> float:
        """Assess confidence in data quality."""
        confidence = 0.5

        if context.get("data_sources"):
            # More sources = higher confidence
            confidence += min(len(context["data_sources"]) * 0.1, 0.3)

        if context.get("data_freshness"):
            # Fresher data = higher confidence
            from datetime import datetime, timedelta
            if isinstance(context["data_freshness"], datetime):
                age = datetime.now() - context["data_freshness"]
                if age < timedelta(hours=1):
                    confidence += 0.2
                elif age < timedelta(days=1):
                    confidence += 0.1

        return min(confidence, 1.0)

    async def _assess_analysis_confidence(self, output: Any, context: Dict[str, Any]) -> float:
        """Assess confidence in analysis quality."""
        confidence = 0.6

        if isinstance(output, dict):
            # Check for multiple analytical perspectives
            perspectives = ["technical", "fundamental", "sentiment", "quantitative"]
            present = sum(1 for p in perspectives if p in str(output).lower())
            confidence += present * 0.1

            # Check for supporting evidence
            if "evidence" in output or "sources" in output:
                confidence += 0.1

        return min(confidence, 1.0)

    async def _assess_prediction_confidence(self, output: Any, context: Dict[str, Any]) -> float:
        """Assess confidence in predictions."""
        confidence = 0.4  # Predictions inherently uncertain

        if isinstance(output, dict):
            # Check for risk acknowledgment
            if "risks" in output and len(output["risks"]) > 0:
                confidence += 0.2  # Acknowledging risks = more realistic

            # Check for probability ranges
            if "probability" in output or "confidence_interval" in output:
                confidence += 0.2

            # Check for scenario analysis
            if "scenarios" in output or "sensitivity" in output:
                confidence += 0.1

        return min(confidence, 1.0)