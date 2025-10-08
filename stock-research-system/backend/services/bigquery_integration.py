"""
BigQuery Integration Module (Phase 4)
Integrates BigQuery data lake with analysis workflow
"""

import logging
from typing import Dict, Any
from datetime import datetime
import asyncio

from services.bigquery_data_lake import get_bigquery_data_lake

logger = logging.getLogger(__name__)


class BigQueryIntegration:
    """
    Handles automatic storage of analysis results in BigQuery
    Also tracks agent performance and market trends
    """

    def __init__(self, data_lake=None):
        self.data_lake = data_lake or get_bigquery_data_lake()
        self.enabled = self.data_lake and self.data_lake.enabled

    async def store_analysis_result(self, analysis_id: str, result: Dict[str, Any]):
        """
        Store complete analysis result in BigQuery
        Automatically extracts and stores:
        - Main analysis record
        - Recommendations for accuracy tracking
        - Market trends data
        """
        if not self.enabled:
            logger.debug("[BigQuery] Storage disabled, skipping")
            return

        try:
            # Store main analysis
            await self.data_lake.store_analysis(analysis_id, result)

            # Store recommendations separately for accuracy tracking
            if "recommendations" in result:
                await self._store_recommendations(analysis_id, result)

            # Store market trends for ML training
            if "analysis" in result:
                await self._store_market_trends(analysis_id, result)

            logger.info(f"[BigQuery] Stored complete analysis {analysis_id}")

        except Exception as e:
            logger.error(f"[BigQuery] Failed to store analysis: {e}")

    async def _store_recommendations(self, analysis_id: str, result: Dict[str, Any]):
        """Store individual recommendations for accuracy tracking"""
        try:
            recommendations = result.get("recommendations", {})
            symbols = result.get("symbols", [])

            table_ref = f"{self.data_lake.project_id}.{self.data_lake.dataset_id}.recommendations"

            rows = []
            for symbol in symbols:
                rows.append({
                    "recommendation_id": f"{analysis_id}_{symbol}",
                    "analysis_id": analysis_id,
                    "timestamp": datetime.utcnow().isoformat(),
                    "symbol": symbol,
                    "action": recommendations.get("action", "HOLD"),
                    "confidence": recommendations.get("confidence", 0.5),
                    "predicted_price": recommendations.get("target_price", 0),
                    "entry_price": result.get("analysis", {}).get("market_data", {}).get("price", 0),
                    "target_price": recommendations.get("target_price", 0),
                    "stop_loss": recommendations.get("stop_loss", 0),
                    "time_horizon": recommendations.get("time_horizon", "short-term"),
                    "actual_return_1d": None,  # Will be updated later
                    "actual_return_7d": None,
                    "actual_return_30d": None,
                    "accuracy_score": None
                })

            errors = self.data_lake.client.insert_rows_json(table_ref, rows)
            if errors:
                logger.error(f"[BigQuery] Recommendation insert errors: {errors}")

        except Exception as e:
            logger.error(f"[BigQuery] Failed to store recommendations: {e}")

    async def _store_market_trends(self, analysis_id: str, result: Dict[str, Any]):
        """Store market trend data for ML training"""
        try:
            analysis = result.get("analysis", {})
            symbols = result.get("symbols", [])

            table_ref = f"{self.data_lake.project_id}.{self.data_lake.dataset_id}.market_trends"

            rows = []
            for symbol in symbols:
                market_data = analysis.get("market_data", {})
                sentiment_data = analysis.get("sentiment", {})

                rows.append({
                    "trend_id": f"{analysis_id}_{symbol}_{int(datetime.utcnow().timestamp())}",
                    "timestamp": datetime.utcnow().isoformat(),
                    "symbol": symbol,
                    "sector": market_data.get("sector", "Unknown"),
                    "price": market_data.get("price", 0),
                    "volume": market_data.get("volume", 0),
                    "sentiment_score": sentiment_data.get("overall_sentiment", 0),
                    "news_count": len(sentiment_data.get("news_items", [])),
                    "recommendation_distribution": {
                        "action": result.get("recommendations", {}).get("action", "HOLD"),
                        "confidence": result.get("recommendations", {}).get("confidence", 0.5)
                    },
                    "macro_indicators": analysis.get("macro_context", {})
                })

            errors = self.data_lake.client.insert_rows_json(table_ref, rows)
            if errors:
                logger.error(f"[BigQuery] Market trends insert errors: {errors}")

        except Exception as e:
            logger.error(f"[BigQuery] Failed to store market trends: {e}")

    async def store_agent_execution(
        self,
        analysis_id: str,
        agent_name: str,
        execution_time: float,
        tokens_used: int,
        cost: float,
        model_used: str,
        cache_hit: bool,
        error_occurred: bool,
        quality_score: float = 0.0
    ):
        """Store individual agent execution metrics"""
        if not self.enabled:
            return

        try:
            table_ref = f"{self.data_lake.project_id}.{self.data_lake.dataset_id}.agent_performance"

            rows = [{
                "execution_id": f"{analysis_id}_{agent_name}_{int(datetime.utcnow().timestamp())}",
                "timestamp": datetime.utcnow().isoformat(),
                "analysis_id": analysis_id,
                "agent_name": agent_name,
                "execution_time_seconds": round(execution_time, 3),
                "tokens_used": tokens_used,
                "cost_usd": round(cost, 6),
                "model_used": model_used,
                "cache_hit": cache_hit,
                "error_occurred": error_occurred,
                "output_quality_score": round(quality_score, 3)
            }]

            errors = self.data_lake.client.insert_rows_json(table_ref, rows)
            if errors:
                logger.error(f"[BigQuery] Agent performance insert errors: {errors}")
            else:
                logger.debug(f"[BigQuery] Stored agent execution for {agent_name}")

        except Exception as e:
            logger.error(f"[BigQuery] Failed to store agent execution: {e}")

    async def update_recommendation_accuracy(
        self,
        recommendation_id: str,
        actual_return_1d: float = None,
        actual_return_7d: float = None,
        actual_return_30d: float = None
    ):
        """
        Update recommendation with actual returns for accuracy tracking
        This should be called by a scheduled job (daily/weekly)
        """
        if not self.enabled:
            return

        try:
            # Calculate accuracy score based on prediction vs actual
            accuracy_score = 0.0
            if actual_return_7d is not None:
                # Simple accuracy: 1.0 if direction correct, 0.5 if neutral, 0.0 if wrong
                if abs(actual_return_7d) < 0.02:  # Within 2% = neutral
                    accuracy_score = 0.5
                elif actual_return_7d > 0:  # Positive return
                    accuracy_score = 1.0 if "BUY" in recommendation_id else 0.0
                else:  # Negative return
                    accuracy_score = 1.0 if "SELL" in recommendation_id else 0.0

            update_query = f"""
            UPDATE `{self.data_lake.project_id}.{self.data_lake.dataset_id}.recommendations`
            SET
                actual_return_1d = {actual_return_1d or 0},
                actual_return_7d = {actual_return_7d or 0},
                actual_return_30d = {actual_return_30d or 0},
                accuracy_score = {accuracy_score}
            WHERE recommendation_id = '{recommendation_id}'
            """

            query_job = self.data_lake.client.query(update_query)
            query_job.result()

            logger.info(f"[BigQuery] Updated accuracy for {recommendation_id}: {accuracy_score}")

        except Exception as e:
            logger.error(f"[BigQuery] Failed to update recommendation accuracy: {e}")

    async def get_historical_context(self, symbol: str, days: int = 30) -> Dict[str, Any]:
        """
        Get historical context for a symbol to improve analysis
        Returns recent recommendation patterns and accuracy
        """
        if not self.enabled:
            return {}

        try:
            history = await self.data_lake.get_symbol_history(symbol, days)

            if not history:
                return {"message": "No historical data available"}

            # Calculate patterns
            recommendations = [h['recommendation'] for h in history]
            recent_trend = "bullish" if recommendations[:5].count('BUY') > 2 else "bearish"

            # Calculate average confidence
            avg_confidence = sum(h['confidence'] for h in history) / len(history)

            return {
                "total_analyses": len(history),
                "recent_trend": recent_trend,
                "avg_confidence": round(avg_confidence, 3),
                "recommendation_counts": {
                    "BUY": recommendations.count('BUY'),
                    "SELL": recommendations.count('SELL'),
                    "HOLD": recommendations.count('HOLD')
                },
                "last_recommendation": history[0]['recommendation'] if history else None,
                "last_analysis_date": history[0]['timestamp'] if history else None
            }

        except Exception as e:
            logger.error(f"[BigQuery] Failed to get historical context: {e}")
            return {}


# Global integration instance
bigquery_integration = None


def get_bigquery_integration(data_lake=None):
    """Get or create BigQuery integration instance"""
    global bigquery_integration

    if bigquery_integration is None:
        bigquery_integration = BigQueryIntegration(data_lake)

    return bigquery_integration
