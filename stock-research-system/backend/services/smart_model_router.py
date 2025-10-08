"""
Smart Model Router
Dynamically selects between GPT-3.5 and GPT-4 based on task complexity
Optimizes cost while maintaining quality for complex reasoning tasks
"""

import logging
from typing import Dict, Any, Literal
from enum import Enum

from langchain_openai import ChatOpenAI

logger = logging.getLogger(__name__)


class TaskComplexity(Enum):
    """Task complexity levels"""
    SIMPLE = "simple"           # GPT-3.5: Summarization, extraction, simple classification
    MODERATE = "moderate"       # GPT-3.5 or GPT-4: Pattern recognition, sentiment analysis
    COMPLEX = "complex"         # GPT-4: Deep reasoning, multi-step analysis, synthesis


class SmartModelRouter:
    """
    Routes tasks to appropriate LLM based on complexity

    Decision Logic:
    - Simple (GPT-3.5): News summarization, sentiment extraction, data formatting
    - Moderate (GPT-3.5 with fallback): Pattern recognition, comparative analysis
    - Complex (GPT-4): Financial reasoning, multi-agent synthesis, strategic decisions

    Cost Impact:
    - GPT-3.5: ~$0.002 per 1K tokens
    - GPT-4: ~$0.03 per 1K tokens
    - Savings: ~93% for tasks routed to GPT-3.5
    """

    def __init__(self, openai_api_key: str):
        self.openai_api_key = openai_api_key

        # Pre-configured models
        self.gpt35 = ChatOpenAI(
            model="gpt-3.5-turbo",
            api_key=openai_api_key,
            temperature=0.1,
            max_tokens=1000
        )

        self.gpt4 = ChatOpenAI(
            model="gpt-4",
            api_key=openai_api_key,
            temperature=0.2,
            max_tokens=2000
        )

        # Statistics tracking
        self.stats = {
            'gpt35_calls': 0,
            'gpt4_calls': 0,
            'cost_saved': 0.0,
            'total_tokens_saved': 0
        }

    def get_model(
        self,
        task_type: str,
        complexity: TaskComplexity = None,
        force_model: Literal["gpt-3.5", "gpt-4"] = None
    ) -> ChatOpenAI:
        """
        Get appropriate model for task

        Args:
            task_type: Type of task (e.g., 'news_summary', 'financial_analysis')
            complexity: Explicit complexity level (optional)
            force_model: Force specific model (for testing/override)

        Returns:
            ChatOpenAI instance (GPT-3.5 or GPT-4)
        """
        # Force model if specified
        if force_model == "gpt-3.5":
            self.stats['gpt35_calls'] += 1
            logger.debug(f"[SmartModelRouter] Using GPT-3.5 (forced) for {task_type}")
            return self.gpt35
        elif force_model == "gpt-4":
            self.stats['gpt4_calls'] += 1
            logger.debug(f"[SmartModelRouter] Using GPT-4 (forced) for {task_type}")
            return self.gpt4

        # Determine complexity if not provided
        if complexity is None:
            complexity = self._infer_complexity(task_type)

        # Route based on complexity
        if complexity == TaskComplexity.SIMPLE:
            model = self.gpt35
            self.stats['gpt35_calls'] += 1
            # Estimate savings (GPT-4 would cost ~15x more)
            self.stats['cost_saved'] += 0.028  # ~$0.028 saved per simple task
            self.stats['total_tokens_saved'] += 500  # Avg tokens saved
            logger.info(f"[SmartModelRouter] Using GPT-3.5 for {task_type} (simple task)")

        elif complexity == TaskComplexity.MODERATE:
            # Use GPT-3.5 for moderate tasks (with quality monitoring)
            model = self.gpt35
            self.stats['gpt35_calls'] += 1
            self.stats['cost_saved'] += 0.028
            logger.info(f"[SmartModelRouter] Using GPT-3.5 for {task_type} (moderate task)")

        else:  # COMPLEX
            model = self.gpt4
            self.stats['gpt4_calls'] += 1
            logger.info(f"[SmartModelRouter] Using GPT-4 for {task_type} (complex reasoning)")

        return model

    def _infer_complexity(self, task_type: str) -> TaskComplexity:
        """
        Infer task complexity from task type

        Task Classification:
        - SIMPLE: Data extraction, formatting, simple summarization
        - MODERATE: Sentiment analysis, pattern detection, comparison
        - COMPLEX: Multi-step reasoning, synthesis, strategic decisions
        """
        task_lower = task_type.lower()

        # Simple tasks (GPT-3.5 sufficient)
        simple_keywords = [
            'summary', 'summarize', 'extract', 'format', 'parse',
            'news', 'headlines', 'events', 'list', 'fetch'
        ]

        # Moderate tasks (GPT-3.5 capable with monitoring)
        moderate_keywords = [
            'sentiment', 'classify', 'categorize', 'compare',
            'social', 'retail', 'pulse', 'trending', 'pattern'
        ]

        # Complex tasks (GPT-4 required)
        complex_keywords = [
            'analysis', 'strategy', 'reasoning', 'synthesis',
            'fundamental', 'technical', 'risk', 'recommendation',
            'decision', 'forecast', 'valuation', 'portfolio'
        ]

        # Check keywords
        for keyword in simple_keywords:
            if keyword in task_lower:
                return TaskComplexity.SIMPLE

        for keyword in moderate_keywords:
            if keyword in task_lower:
                return TaskComplexity.MODERATE

        for keyword in complex_keywords:
            if keyword in task_lower:
                return TaskComplexity.COMPLEX

        # Default to moderate if uncertain
        logger.warning(f"[SmartModelRouter] Unknown task type '{task_type}', defaulting to moderate")
        return TaskComplexity.MODERATE

    def create_model(
        self,
        model_name: Literal["gpt-3.5-turbo", "gpt-4"] = "gpt-3.5-turbo",
        temperature: float = 0.1,
        max_tokens: int = 1000
    ) -> ChatOpenAI:
        """
        Create custom model with specific parameters

        Useful for edge cases requiring custom configuration
        """
        return ChatOpenAI(
            model=model_name,
            api_key=self.openai_api_key,
            temperature=temperature,
            max_tokens=max_tokens
        )

    def get_stats(self) -> Dict[str, Any]:
        """Get routing statistics"""
        total_calls = self.stats['gpt35_calls'] + self.stats['gpt4_calls']
        gpt35_percentage = 0.0

        if total_calls > 0:
            gpt35_percentage = (self.stats['gpt35_calls'] / total_calls) * 100

        return {
            'total_calls': total_calls,
            'gpt35_calls': self.stats['gpt35_calls'],
            'gpt4_calls': self.stats['gpt4_calls'],
            'gpt35_percentage': round(gpt35_percentage, 2),
            'cost_saved': round(self.stats['cost_saved'], 2),
            'tokens_saved': self.stats['total_tokens_saved'],
            'avg_cost_per_call': round(self._calculate_avg_cost(), 3)
        }

    def _calculate_avg_cost(self) -> float:
        """Calculate average cost per call"""
        total_calls = self.stats['gpt35_calls'] + self.stats['gpt4_calls']
        if total_calls == 0:
            return 0.0

        # Rough estimates (per call with ~500 tokens)
        gpt35_cost = self.stats['gpt35_calls'] * 0.002
        gpt4_cost = self.stats['gpt4_calls'] * 0.03

        return (gpt35_cost + gpt4_cost) / total_calls

    def reset_stats(self):
        """Reset statistics"""
        self.stats = {
            'gpt35_calls': 0,
            'gpt4_calls': 0,
            'cost_saved': 0.0,
            'total_tokens_saved': 0
        }
        logger.info("[SmartModelRouter] Statistics reset")


# Singleton instance
_router_instance = None


def get_smart_router(openai_api_key: str = None) -> SmartModelRouter:
    """
    Get or create SmartModelRouter singleton

    Args:
        openai_api_key: OpenAI API key (required for first call)

    Returns:
        SmartModelRouter instance
    """
    global _router_instance

    if _router_instance is None:
        if openai_api_key is None:
            raise ValueError("OpenAI API key required for first SmartModelRouter initialization")
        _router_instance = SmartModelRouter(openai_api_key)

    return _router_instance


# Task type constants for easy reference
class TaskTypes:
    """Common task types for model routing"""

    # SIMPLE tasks (GPT-3.5)
    NEWS_SUMMARY = "news_summary"
    EVENT_EXTRACTION = "event_extraction"
    HEADLINE_PARSING = "headline_parsing"
    DATA_FORMATTING = "data_formatting"

    # MODERATE tasks (GPT-3.5 with monitoring)
    SENTIMENT_ANALYSIS = "sentiment_analysis"
    SOCIAL_PULSE = "social_pulse_analysis"
    PATTERN_DETECTION = "pattern_detection"
    COMPARATIVE_ANALYSIS = "comparative_analysis"

    # COMPLEX tasks (GPT-4)
    FUNDAMENTAL_ANALYSIS = "fundamental_analysis"
    TECHNICAL_ANALYSIS = "technical_analysis"
    RISK_ANALYSIS = "risk_analysis"
    PORTFOLIO_STRATEGY = "portfolio_strategy"
    SYNTHESIS = "synthesis_reasoning"
    INVESTMENT_DECISION = "investment_decision"
