"""
API Endpoints for Cost Optimization Monitoring
Provides statistics for Tavily caching and smart model routing
"""

from fastapi import APIRouter, HTTPException
from typing import Dict, Any

router = APIRouter(prefix="/api/optimization", tags=["optimization"])


@router.get("/cache/stats")
async def get_cache_stats() -> Dict[str, Any]:
    """
    Get Tavily cache statistics

    Returns:
        - enabled: Whether caching is active
        - hits: Number of cache hits
        - misses: Number of cache misses
        - hit_rate: Percentage of cache hits
        - cost_saved: Estimated cost saved (USD)
        - total_requests: Total Tavily requests
    """
    try:
        from services.tavily_cache import get_tavily_cache
        cache = get_tavily_cache()
        return await cache.get_stats()
    except Exception as e:
        return {
            "enabled": False,
            "error": str(e),
            "message": "Cache statistics unavailable"
        }


@router.get("/router/stats")
async def get_router_stats() -> Dict[str, Any]:
    """
    Get SmartModelRouter statistics

    Returns:
        - total_calls: Total LLM calls
        - gpt35_calls: Calls routed to GPT-3.5
        - gpt4_calls: Calls routed to GPT-4
        - gpt35_percentage: Percentage routed to GPT-3.5
        - cost_saved: Estimated cost saved vs all GPT-4
        - tokens_saved: Tokens saved by using GPT-3.5
        - avg_cost_per_call: Average cost per LLM call
    """
    try:
        from services.smart_model_router import get_smart_router
        router = get_smart_router()
        return router.get_stats()
    except Exception as e:
        return {
            "error": str(e),
            "message": "Router statistics unavailable"
        }


@router.get("/cost-analysis")
async def get_cost_analysis() -> Dict[str, Any]:
    """
    Get comprehensive cost analysis

    Combines cache and router statistics for total cost savings
    """
    try:
        from services.tavily_cache import get_tavily_cache
        from services.smart_model_router import get_smart_router

        cache = get_tavily_cache()
        router = get_smart_router()

        cache_stats = await cache.get_stats()
        router_stats = router.get_stats()

        # Calculate total savings
        total_saved = cache_stats.get('cost_saved', 0) + router_stats.get('cost_saved', 0)

        # Estimate what cost would be without optimization
        without_optimization_cost = total_saved + (router_stats.get('avg_cost_per_call', 0) * router_stats.get('total_calls', 0))

        return {
            "cache": cache_stats,
            "router": router_stats,
            "total_savings": {
                "amount": round(total_saved, 2),
                "currency": "USD",
                "optimization_rate": round((total_saved / without_optimization_cost * 100) if without_optimization_cost > 0 else 0, 2)
            },
            "projections": {
                "daily_savings": round(total_saved * 24, 2),  # Rough estimate
                "monthly_savings": round(total_saved * 720, 2),
                "annual_savings": round(total_saved * 8760, 2)
            }
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/cache/invalidate/{symbol}")
async def invalidate_cache(symbol: str) -> Dict[str, str]:
    """
    Invalidate all cached data for a specific symbol

    Use when you need fresh data (e.g., after major news event)

    Args:
        symbol: Stock symbol (e.g., TSLA)

    Returns:
        Success message
    """
    try:
        from services.tavily_cache import invalidate_symbol_cache
        await invalidate_symbol_cache(symbol)

        return {
            "status": "success",
            "message": f"Cache invalidated for {symbol}",
            "symbol": symbol
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/stats/reset")
async def reset_statistics() -> Dict[str, str]:
    """
    Reset all optimization statistics

    Useful for testing or monthly reporting
    """
    try:
        from services.tavily_cache import get_tavily_cache
        from services.smart_model_router import get_smart_router

        cache = get_tavily_cache()
        router = get_smart_router()

        await cache.reset_stats()
        router.reset_stats()

        return {
            "status": "success",
            "message": "All optimization statistics reset"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
