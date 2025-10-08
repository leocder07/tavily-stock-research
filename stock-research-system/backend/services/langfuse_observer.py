"""
Langfuse LLM Observability Integration (Phase 3)
Tracks all LLM calls, costs, latency, and quality metrics
"""

import logging
import os
from typing import Dict, Any, Optional
from datetime import datetime
from contextlib import asynccontextmanager

from langfuse import Langfuse
from langfuse.decorators import observe, langfuse_context

logger = logging.getLogger(__name__)


class LangfuseObserver:
    """
    Centralized LLM observability using Langfuse
    Tracks costs, latency, token usage, and trace relationships
    """

    def __init__(self):
        self.enabled = False
        self.langfuse = None

        # Initialize Langfuse if API keys provided
        langfuse_public_key = os.getenv("LANGFUSE_PUBLIC_KEY")
        langfuse_secret_key = os.getenv("LANGFUSE_SECRET_KEY")
        langfuse_host = os.getenv("LANGFUSE_HOST", "https://cloud.langfuse.com")

        if langfuse_public_key and langfuse_secret_key:
            try:
                self.langfuse = Langfuse(
                    public_key=langfuse_public_key,
                    secret_key=langfuse_secret_key,
                    host=langfuse_host
                )
                self.enabled = True
                logger.info("[Langfuse] Observability enabled")
            except Exception as e:
                logger.warning(f"[Langfuse] Initialization failed: {e}")
        else:
            logger.info("[Langfuse] Observability disabled (no API keys)")

    @asynccontextmanager
    async def trace_analysis(self, analysis_id: str, query: str, symbols: list):
        """
        Create a trace for entire analysis workflow

        Args:
            analysis_id: Analysis document ID
            query: User query
            symbols: Stock symbols

        Usage:
            async with observer.trace_analysis(id, query, symbols) as trace:
                # Your analysis code
                pass
        """
        if not self.enabled:
            yield None
            return

        trace = self.langfuse.trace(
            name="stock_analysis",
            user_id=analysis_id,
            metadata={
                "analysis_id": analysis_id,
                "query": query,
                "symbols": symbols,
                "timestamp": datetime.utcnow().isoformat()
            },
            tags=["production", "stock-analysis"]
        )

        try:
            yield trace
        finally:
            # Finalize trace
            trace.update(
                output={"status": "completed"},
                level="DEFAULT"
            )

    @asynccontextmanager
    async def trace_agent(
        self,
        agent_name: str,
        trace_id: Optional[str] = None,
        metadata: Dict[str, Any] = None
    ):
        """
        Create a span for individual agent execution

        Args:
            agent_name: Name of the agent
            trace_id: Parent trace ID
            metadata: Additional metadata

        Usage:
            async with observer.trace_agent("FundamentalAgent", trace_id) as span:
                result = await agent.analyze()
        """
        if not self.enabled:
            yield None
            return

        span = self.langfuse.span(
            trace_id=trace_id,
            name=agent_name,
            metadata=metadata or {},
            start_time=datetime.utcnow()
        )

        start_time = datetime.utcnow()

        try:
            yield span
            # Success
            span.update(
                end_time=datetime.utcnow(),
                level="DEFAULT",
                status_message="success"
            )
        except Exception as e:
            # Error
            span.update(
                end_time=datetime.utcnow(),
                level="ERROR",
                status_message=str(e)
            )
            raise

    async def track_llm_call(
        self,
        model: str,
        prompt: str,
        completion: str,
        trace_id: Optional[str] = None,
        metadata: Dict[str, Any] = None
    ):
        """
        Track individual LLM API call

        Args:
            model: Model name (gpt-4, gpt-3.5-turbo)
            prompt: Input prompt
            completion: Model output
            trace_id: Parent trace ID
            metadata: Additional metadata (tokens, cost, etc.)
        """
        if not self.enabled:
            return

        try:
            self.langfuse.generation(
                trace_id=trace_id,
                name=f"llm_call_{model}",
                model=model,
                model_parameters={
                    "temperature": metadata.get("temperature", 0.3),
                    "max_tokens": metadata.get("max_tokens", 2000)
                },
                input=prompt,
                output=completion,
                metadata=metadata or {},
                usage={
                    "input": metadata.get("prompt_tokens", 0),
                    "output": metadata.get("completion_tokens", 0),
                    "total": metadata.get("total_tokens", 0),
                    "unit": "TOKENS"
                },
                level="DEFAULT"
            )

            # Calculate cost
            cost = self._calculate_cost(
                model,
                metadata.get("prompt_tokens", 0),
                metadata.get("completion_tokens", 0)
            )

            # Track cost separately
            if cost > 0:
                self.langfuse.score(
                    trace_id=trace_id,
                    name="cost",
                    value=cost,
                    data_type="NUMERIC"
                )

        except Exception as e:
            logger.error(f"[Langfuse] Failed to track LLM call: {e}")

    def _calculate_cost(self, model: str, prompt_tokens: int, completion_tokens: int) -> float:
        """Calculate cost based on model and token usage"""

        # OpenAI pricing (per 1K tokens)
        pricing = {
            "gpt-4": {"input": 0.03, "output": 0.06},
            "gpt-4-turbo": {"input": 0.01, "output": 0.03},
            "gpt-3.5-turbo": {"input": 0.0015, "output": 0.002}
        }

        model_key = "gpt-4" if "gpt-4" in model else "gpt-3.5-turbo"
        rates = pricing.get(model_key, {"input": 0, "output": 0})

        cost = (prompt_tokens / 1000 * rates["input"]) + \
               (completion_tokens / 1000 * rates["output"])

        return round(cost, 4)

    async def track_cache_hit(self, trace_id: Optional[str] = None):
        """Track cache hit event"""
        if not self.enabled:
            return

        self.langfuse.event(
            trace_id=trace_id,
            name="cache_hit",
            metadata={"source": "redis", "saved_cost": 0.01}
        )

    async def track_tavily_call(
        self,
        query: str,
        results_count: int,
        trace_id: Optional[str] = None,
        cached: bool = False
    ):
        """Track Tavily API call"""
        if not self.enabled:
            return

        self.langfuse.event(
            trace_id=trace_id,
            name="tavily_search",
            metadata={
                "query": query,
                "results_count": results_count,
                "cached": cached,
                "cost": 0 if cached else 0.01
            }
        )

    async def track_recommendation_quality(
        self,
        trace_id: str,
        recommendation: Dict[str, Any],
        validation_score: float
    ):
        """Track recommendation quality score"""
        if not self.enabled:
            return

        # Track validation score
        self.langfuse.score(
            trace_id=trace_id,
            name="ai_safety_score",
            value=validation_score,
            data_type="NUMERIC",
            comment=f"Action: {recommendation.get('action')}, Confidence: {recommendation.get('confidence')}"
        )

    async def flush(self):
        """Flush pending events to Langfuse"""
        if self.enabled and self.langfuse:
            try:
                self.langfuse.flush()
            except Exception as e:
                logger.error(f"[Langfuse] Flush failed: {e}")


# Global Langfuse observer
langfuse_observer = None


def get_langfuse_observer():
    """Get or create Langfuse observer instance"""
    global langfuse_observer
    if langfuse_observer is None:
        langfuse_observer = LangfuseObserver()
    return langfuse_observer


# Decorator for observing functions
def observe_llm(name: str = None):
    """
    Decorator to automatically observe LLM function calls

    Usage:
        @observe_llm(name="fundamental_analysis")
        async def analyze_fundamentals(data):
            # Your code
            pass
    """
    def decorator(func):
        async def wrapper(*args, **kwargs):
            observer = get_langfuse_observer()

            if not observer.enabled:
                return await func(*args, **kwargs)

            async with observer.trace_agent(name or func.__name__):
                return await func(*args, **kwargs)

        return wrapper
    return decorator
