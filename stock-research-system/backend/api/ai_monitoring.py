"""
AI Performance Monitoring Dashboard API Endpoints
Real-time metrics and statistics for AI enhancement components
"""

from fastapi import APIRouter, HTTPException, Depends
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
import asyncio
from pydantic import BaseModel, Field

router = APIRouter(prefix="/api/ai-monitoring", tags=["AI Monitoring"])


class AIMetricsRequest(BaseModel):
    """Request model for AI metrics."""
    time_range: str = Field("1h", pattern="^(1h|24h|7d|30d)$")
    metric_types: Optional[List[str]] = None


class AIMetricsResponse(BaseModel):
    """Response model for AI metrics."""
    timestamp: str
    time_range: str
    metrics: Dict[str, Any]
    performance: Dict[str, Any]
    cost_analysis: Dict[str, Any]
    model_distribution: Dict[str, Any]


class ModelUsageStats(BaseModel):
    """Model usage statistics."""
    model: str
    calls: int
    tokens_used: int
    total_cost: float
    avg_latency: float
    success_rate: float


class MemoryStats(BaseModel):
    """Memory system statistics."""
    total_memories: int
    by_tier: Dict[str, int]
    consolidation_rate: float
    recall_performance: Dict[str, float]


class RAGPerformance(BaseModel):
    """RAG pipeline performance metrics."""
    queries_processed: int
    avg_confidence: float
    citation_coverage: float
    retrieval_time: float
    synthesis_time: float


class ParallelExecutionStats(BaseModel):
    """Parallel execution statistics."""
    total_tasks: int
    parallel_ratio: float
    time_saved: float
    success_rate: float


def get_ai_system():
    """Dependency to get AI system instance."""
    from main import ai_system, ENABLE_AI_ENHANCEMENTS

    if not ENABLE_AI_ENHANCEMENTS or ai_system is None:
        raise HTTPException(
            status_code=503,
            detail="AI enhancement system is not available"
        )
    return ai_system


@router.get("/status", response_model=Dict[str, Any])
async def get_ai_system_status(ai_system=Depends(get_ai_system)):
    """Get current AI system status and health check."""
    try:
        # Get system statistics
        stats = ai_system.get_statistics()

        # Check component health
        health_checks = {
            "model_orchestrator": ai_system.model_orchestrator is not None,
            "vector_engine": ai_system.vector_engine is not None,
            "memory_system": ai_system.memory_system is not None,
            "rag_pipeline": ai_system.rag_pipeline is not None,
            "tool_orchestrator": ai_system.tool_orchestrator is not None
        }

        # Calculate overall health
        healthy_components = sum(health_checks.values())
        total_components = len(health_checks)
        health_score = (healthy_components / total_components) * 100

        return {
            "status": "healthy" if health_score == 100 else "degraded",
            "health_score": health_score,
            "components": health_checks,
            "uptime": datetime.utcnow().isoformat(),
            "queries_processed": stats.get("queries_processed", 0),
            "version": "1.0.0"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/metrics", response_model=AIMetricsResponse)
async def get_ai_metrics(
    request: AIMetricsRequest = AIMetricsRequest(),
    ai_system=Depends(get_ai_system)
):
    """Get comprehensive AI system metrics."""
    try:
        # Get base statistics
        stats = ai_system.get_statistics()

        # Calculate time range
        time_ranges = {
            "1h": timedelta(hours=1),
            "24h": timedelta(days=1),
            "7d": timedelta(days=7),
            "30d": timedelta(days=30)
        }

        # Model usage statistics
        model_stats = stats.get("model_stats", {})
        model_distribution = {}
        total_calls = 0

        for model, usage in model_stats.items():
            calls = usage.get("calls", 0)
            total_calls += calls
            model_distribution[model] = {
                "calls": calls,
                "percentage": 0,  # Will calculate after
                "tokens": usage.get("total_tokens", 0),
                "cost": usage.get("total_cost", 0.0)
            }

        # Calculate percentages
        if total_calls > 0:
            for model in model_distribution:
                model_distribution[model]["percentage"] = \
                    (model_distribution[model]["calls"] / total_calls) * 100

        # Memory statistics
        memory_stats = stats.get("memory_stats", {})

        # Performance metrics
        performance = {
            "avg_response_time": 2.5,  # Would calculate from actual logs
            "cache_hit_rate": stats.get("cache_hits", 0) / max(stats.get("cache_hits", 0) + stats.get("cache_misses", 1), 1),
            "parallel_execution_rate": 0.75,  # Would calculate from parallel orchestrator
            "error_rate": 0.02  # Would calculate from error logs
        }

        # Cost analysis
        total_cost = sum(m.get("cost", 0) for m in model_distribution.values())
        cost_analysis = {
            "total_cost": total_cost,
            "cost_per_query": total_cost / max(stats.get("queries_processed", 1), 1),
            "cost_breakdown": {
                model: data["cost"]
                for model, data in model_distribution.items()
            },
            "projected_monthly_cost": total_cost * 30  # Simplified projection
        }

        return AIMetricsResponse(
            timestamp=datetime.utcnow().isoformat(),
            time_range=request.time_range,
            metrics=stats,
            performance=performance,
            cost_analysis=cost_analysis,
            model_distribution=model_distribution
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/model-usage", response_model=List[ModelUsageStats])
async def get_model_usage_stats(ai_system=Depends(get_ai_system)):
    """Get detailed model usage statistics."""
    try:
        stats = ai_system.get_statistics()
        model_stats = stats.get("model_stats", {})

        usage_list = []
        for model_name, usage_data in model_stats.items():
            usage_list.append(ModelUsageStats(
                model=model_name,
                calls=usage_data.get("calls", 0),
                tokens_used=usage_data.get("total_tokens", 0),
                total_cost=usage_data.get("total_cost", 0.0),
                avg_latency=usage_data.get("avg_latency", 0.0),
                success_rate=usage_data.get("success_rate", 1.0)
            ))

        # Sort by usage (calls)
        usage_list.sort(key=lambda x: x.calls, reverse=True)

        return usage_list
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/memory-stats", response_model=MemoryStats)
async def get_memory_statistics(ai_system=Depends(get_ai_system)):
    """Get memory system statistics."""
    try:
        memory_stats = ai_system.memory_system.get_statistics()

        # Calculate tier distribution
        by_tier = {}
        for tier_name, tier_data in memory_stats.get("by_tier", {}).items():
            by_tier[tier_name] = tier_data.get("count", 0)

        return MemoryStats(
            total_memories=memory_stats.get("total_memories", 0),
            by_tier=by_tier,
            consolidation_rate=memory_stats.get("consolidation_rate", 0.0),
            recall_performance={
                "avg_recall_time": memory_stats.get("avg_recall_time", 0.0),
                "relevance_score": memory_stats.get("avg_relevance", 0.0)
            }
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/rag-performance", response_model=RAGPerformance)
async def get_rag_performance(ai_system=Depends(get_ai_system)):
    """Get RAG pipeline performance metrics."""
    try:
        # Get RAG statistics (would be tracked in production)
        rag_stats = ai_system.rag_pipeline.get_statistics() if hasattr(ai_system.rag_pipeline, 'get_statistics') else {}

        return RAGPerformance(
            queries_processed=rag_stats.get("queries_processed", 0),
            avg_confidence=rag_stats.get("avg_confidence", 0.85),
            citation_coverage=rag_stats.get("citation_coverage", 0.95),
            retrieval_time=rag_stats.get("avg_retrieval_time", 0.5),
            synthesis_time=rag_stats.get("avg_synthesis_time", 1.0)
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/parallel-execution", response_model=ParallelExecutionStats)
async def get_parallel_execution_stats():
    """Get parallel execution statistics."""
    from main import parallel_orchestrator

    if parallel_orchestrator is None:
        raise HTTPException(
            status_code=503,
            detail="Parallel orchestrator is not available"
        )

    try:
        stats = parallel_orchestrator.get_statistics()

        return ParallelExecutionStats(
            total_tasks=stats.get("total_tasks", 0),
            parallel_ratio=stats.get("parallelism_achieved", 0.0),
            time_saved=stats.get("time_saved_seconds", 0.0),
            success_rate=stats.get("success_rate", 1.0)
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/optimize")
async def optimize_ai_performance(ai_system=Depends(get_ai_system)):
    """Trigger AI system optimization routines."""
    try:
        # Run optimization
        results = await ai_system.optimize_performance()

        return {
            "status": "success",
            "optimizations": results,
            "timestamp": datetime.utcnow().isoformat()
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/cost-projection")
async def get_cost_projection(
    days: int = 30,
    ai_system=Depends(get_ai_system)
):
    """Get cost projection for specified number of days."""
    try:
        stats = ai_system.get_statistics()
        model_stats = stats.get("model_stats", {})

        # Calculate current daily cost
        total_cost = sum(
            usage.get("total_cost", 0)
            for usage in model_stats.values()
        )

        queries_processed = stats.get("queries_processed", 0)
        cost_per_query = total_cost / max(queries_processed, 1)

        # Project based on average usage
        avg_daily_queries = 100  # Would calculate from historical data
        projected_daily_cost = cost_per_query * avg_daily_queries

        return {
            "current_total_cost": total_cost,
            "cost_per_query": cost_per_query,
            "projected_daily_cost": projected_daily_cost,
            "projected_cost": projected_daily_cost * days,
            "projection_days": days,
            "confidence": 0.75  # Would calculate based on data variance
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/performance-history")
async def get_performance_history(
    metric: str = "response_time",
    hours: int = 24
):
    """Get historical performance data."""
    try:
        # In production, this would query from a time-series database
        # For now, return simulated data

        data_points = []
        base_time = datetime.utcnow() - timedelta(hours=hours)

        for i in range(hours):
            timestamp = base_time + timedelta(hours=i)

            # Simulate different metrics
            if metric == "response_time":
                value = 2.0 + (0.5 * (i % 4))  # Varies between 2-3.5s
            elif metric == "confidence":
                value = 0.85 + (0.05 * ((i % 6) - 3) / 3)  # Varies 0.80-0.90
            elif metric == "parallelism":
                value = 0.7 + (0.1 * ((i % 8) - 4) / 4)  # Varies 0.65-0.75
            else:
                value = 0.0

            data_points.append({
                "timestamp": timestamp.isoformat(),
                "value": value
            })

        return {
            "metric": metric,
            "time_range_hours": hours,
            "data_points": data_points
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# Export router
__all__ = ["router"]