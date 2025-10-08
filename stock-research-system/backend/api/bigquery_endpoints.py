"""
BigQuery Data Lake API Endpoints (Phase 4)
Provides access to historical analysis data and ML training exports
"""

from fastapi import APIRouter, HTTPException, Query
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
import logging

from services.bigquery_data_lake import get_bigquery_data_lake

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/bigquery", tags=["bigquery"])


@router.get("/history/{symbol}")
async def get_symbol_history(
    symbol: str,
    days: int = Query(default=30, ge=1, le=365, description="Number of days of history")
) -> Dict[str, Any]:
    """
    Get historical analyses for a specific symbol

    Returns:
    - List of past recommendations with confidence and outcomes
    - Trend analysis
    """
    data_lake = get_bigquery_data_lake()

    if not data_lake or not data_lake.enabled:
        raise HTTPException(
            status_code=503,
            detail="BigQuery data lake not available. Check configuration."
        )

    try:
        history = await data_lake.get_symbol_history(symbol.upper(), days)

        # Calculate statistics
        if history:
            recommendations = [h['recommendation'] for h in history]
            buy_count = recommendations.count('BUY')
            sell_count = recommendations.count('SELL')
            hold_count = recommendations.count('HOLD')

            avg_confidence = sum(h['confidence'] for h in history) / len(history)

            stats = {
                "symbol": symbol.upper(),
                "period_days": days,
                "total_analyses": len(history),
                "recommendation_distribution": {
                    "BUY": buy_count,
                    "SELL": sell_count,
                    "HOLD": hold_count
                },
                "avg_confidence": round(avg_confidence, 3)
            }
        else:
            stats = {
                "symbol": symbol.upper(),
                "period_days": days,
                "total_analyses": 0,
                "recommendation_distribution": {"BUY": 0, "SELL": 0, "HOLD": 0},
                "avg_confidence": 0.0
            }

        return {
            "stats": stats,
            "history": history[:50]  # Limit to 50 most recent
        }

    except Exception as e:
        logger.error(f"Failed to get symbol history: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/accuracy")
async def get_recommendation_accuracy(
    days: int = Query(default=30, ge=1, le=365, description="Number of days to analyze")
) -> Dict[str, Any]:
    """
    Get recommendation accuracy metrics

    Returns:
    - Accuracy by action type (BUY/SELL/HOLD)
    - Overall performance statistics
    """
    data_lake = get_bigquery_data_lake()

    if not data_lake or not data_lake.enabled:
        raise HTTPException(
            status_code=503,
            detail="BigQuery data lake not available"
        )

    try:
        accuracy = await data_lake.get_recommendation_accuracy(days)

        # Calculate overall accuracy
        if accuracy:
            total_count = sum(a['count'] for a in accuracy.values())
            weighted_accuracy = sum(
                a['accuracy'] * a['count'] for a in accuracy.values()
            ) / total_count if total_count > 0 else 0

            return {
                "period_days": days,
                "overall_accuracy": round(weighted_accuracy, 3),
                "total_recommendations": total_count,
                "by_action": accuracy
            }
        else:
            return {
                "period_days": days,
                "overall_accuracy": 0.0,
                "total_recommendations": 0,
                "by_action": {}
            }

    except Exception as e:
        logger.error(f"Failed to get accuracy metrics: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/agent-performance")
async def get_agent_performance(
    days: int = Query(default=7, ge=1, le=30, description="Number of days to analyze")
) -> Dict[str, Any]:
    """
    Get agent performance statistics

    Returns:
    - Execution time, cost, and quality metrics per agent
    - Cache hit rates
    - Model usage distribution
    """
    data_lake = get_bigquery_data_lake()

    if not data_lake or not data_lake.enabled:
        raise HTTPException(
            status_code=503,
            detail="BigQuery data lake not available"
        )

    try:
        stats = await data_lake.get_agent_performance_stats(days)

        if stats:
            # Calculate totals
            total_cost = sum(s['avg_cost'] for s in stats.values())
            total_time = sum(s['avg_time'] for s in stats.values())
            avg_cache_rate = sum(s['cache_hit_rate'] for s in stats.values()) / len(stats)

            # Find most expensive agent
            most_expensive = max(stats.values(), key=lambda x: x['avg_cost'])

            summary = {
                "period_days": days,
                "total_agents": len(stats),
                "avg_total_cost": round(total_cost, 4),
                "avg_total_time": round(total_time, 2),
                "avg_cache_hit_rate": round(avg_cache_rate, 3),
                "most_expensive_agent": most_expensive['agent']
            }
        else:
            summary = {
                "period_days": days,
                "total_agents": 0,
                "avg_total_cost": 0.0,
                "avg_total_time": 0.0,
                "avg_cache_hit_rate": 0.0,
                "most_expensive_agent": None
            }

        return {
            "summary": summary,
            "agent_stats": stats
        }

    except Exception as e:
        logger.error(f"Failed to get agent performance: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/export-training-data/{symbol}")
async def export_training_data(
    symbol: str,
    destination_bucket: str = Query(..., description="GCS bucket path (gs://bucket/path)")
) -> Dict[str, str]:
    """
    Export training data for ML models

    Exports 1 year of data including:
    - Recommendations and outcomes
    - Sentiment scores
    - Market indicators
    """
    data_lake = get_bigquery_data_lake()

    if not data_lake or not data_lake.enabled:
        raise HTTPException(
            status_code=503,
            detail="BigQuery data lake not available"
        )

    # Validate GCS path
    if not destination_bucket.startswith("gs://"):
        raise HTTPException(
            status_code=400,
            detail="Destination must be a GCS path (gs://bucket/path)"
        )

    try:
        destination_uri = f"{destination_bucket}/{symbol}_training_data.json"
        await data_lake.export_training_data(symbol.upper(), destination_uri)

        return {
            "status": "success",
            "symbol": symbol.upper(),
            "destination": destination_uri,
            "message": "Training data exported successfully"
        }

    except Exception as e:
        logger.error(f"Failed to export training data: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/market-trends/{symbol}")
async def get_market_trends(
    symbol: str,
    days: int = Query(default=30, ge=1, le=90, description="Number of days to analyze")
) -> Dict[str, Any]:
    """
    Get market trend analysis for a symbol

    Returns:
    - Sentiment trends over time
    - Recommendation patterns
    - Price movement correlation
    """
    data_lake = get_bigquery_data_lake()

    if not data_lake or not data_lake.enabled:
        raise HTTPException(
            status_code=503,
            detail="BigQuery data lake not available"
        )

    try:
        # Query market trends
        query = f"""
        SELECT
            DATE(timestamp) as date,
            AVG(sentiment_score) as avg_sentiment,
            SUM(news_count) as total_news,
            AVG(price) as avg_price
        FROM `{data_lake.project_id}.{data_lake.dataset_id}.market_trends`
        WHERE symbol = '{symbol.upper()}'
          AND timestamp >= TIMESTAMP_SUB(CURRENT_TIMESTAMP(), INTERVAL {days} DAY)
        GROUP BY date
        ORDER BY date DESC
        """

        query_job = data_lake.client.query(query)
        results = query_job.result()

        trends = []
        for row in results:
            trends.append({
                "date": row.date.isoformat(),
                "sentiment": round(row.avg_sentiment or 0, 3),
                "news_count": int(row.total_news or 0),
                "price": round(row.avg_price or 0, 2)
            })

        # Calculate trend direction
        if len(trends) >= 2:
            recent_sentiment = trends[0]['sentiment']
            older_sentiment = trends[-1]['sentiment']
            trend_direction = "bullish" if recent_sentiment > older_sentiment else "bearish"
        else:
            trend_direction = "neutral"

        return {
            "symbol": symbol.upper(),
            "period_days": days,
            "trend_direction": trend_direction,
            "data_points": len(trends),
            "trends": trends[:30]  # Limit to 30 data points
        }

    except Exception as e:
        logger.error(f"Failed to get market trends: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/status")
async def get_bigquery_status() -> Dict[str, Any]:
    """
    Get BigQuery data lake status and configuration
    """
    data_lake = get_bigquery_data_lake()

    if not data_lake:
        return {
            "enabled": False,
            "message": "BigQuery not configured"
        }

    return {
        "enabled": data_lake.enabled,
        "project_id": data_lake.project_id,
        "dataset_id": data_lake.dataset_id,
        "message": "BigQuery data lake operational" if data_lake.enabled else "BigQuery initialization failed"
    }
