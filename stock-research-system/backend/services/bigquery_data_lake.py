"""
BigQuery Data Lake Integration (Phase 4)
Stores 100M+ analyses for historical trends and pattern analysis
"""

import logging
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
import json

from google.cloud import bigquery
from google.oauth2 import service_account

logger = logging.getLogger(__name__)


class BigQueryDataLake:
    """
    BigQuery data lake for stock analysis history
    Supports petabyte-scale analytics and ML model training
    """

    def __init__(self, project_id: str, dataset_id: str = "stock_research", credentials_path: str = None):
        self.project_id = project_id
        self.dataset_id = dataset_id

        # Initialize BigQuery client
        if credentials_path:
            credentials = service_account.Credentials.from_service_account_file(credentials_path)
            self.client = bigquery.Client(credentials=credentials, project=project_id)
        else:
            self.client = bigquery.Client(project=project_id)

        self.enabled = False
        self._initialize_dataset()

    def _initialize_dataset(self):
        """Create dataset and tables if they don't exist"""
        try:
            # Create dataset
            dataset_ref = f"{self.project_id}.{self.dataset_id}"
            dataset = bigquery.Dataset(dataset_ref)
            dataset.location = "US"

            try:
                self.client.create_dataset(dataset, exists_ok=True)
                logger.info(f"[BigQuery] Dataset {self.dataset_id} ready")
            except Exception as e:
                logger.warning(f"[BigQuery] Dataset creation skipped: {e}")

            # Create tables
            self._create_analyses_table()
            self._create_recommendations_table()
            self._create_agent_performance_table()
            self._create_market_trends_table()

            self.enabled = True
            logger.info("[BigQuery] Data lake initialized successfully")

        except Exception as e:
            logger.error(f"[BigQuery] Initialization failed: {e}")
            self.enabled = False

    def _create_analyses_table(self):
        """Create analyses table for storing all analysis history"""
        schema = [
            bigquery.SchemaField("analysis_id", "STRING", mode="REQUIRED"),
            bigquery.SchemaField("timestamp", "TIMESTAMP", mode="REQUIRED"),
            bigquery.SchemaField("user_id", "STRING"),
            bigquery.SchemaField("query", "STRING"),
            bigquery.SchemaField("symbols", "STRING", mode="REPEATED"),
            bigquery.SchemaField("recommendation", "STRING"),
            bigquery.SchemaField("confidence", "FLOAT64"),
            bigquery.SchemaField("target_price", "FLOAT64"),
            bigquery.SchemaField("actual_price", "FLOAT64"),
            bigquery.SchemaField("enrichment_status", "STRING"),
            bigquery.SchemaField("execution_time_seconds", "FLOAT64"),
            bigquery.SchemaField("cost_usd", "FLOAT64"),
            bigquery.SchemaField("cache_hit", "BOOLEAN"),
            bigquery.SchemaField("agent_results", "JSON"),
        ]

        table_ref = f"{self.project_id}.{self.dataset_id}.analyses"
        table = bigquery.Table(table_ref, schema=schema)

        # Partition by date for better performance
        table.time_partitioning = bigquery.TimePartitioning(
            type_=bigquery.TimePartitioningType.DAY,
            field="timestamp"
        )

        # Cluster for better query performance
        table.clustering_fields = ["symbols", "recommendation"]

        self.client.create_table(table, exists_ok=True)
        logger.info("[BigQuery] Analyses table created")

    def _create_recommendations_table(self):
        """Create recommendations table for tracking accuracy"""
        schema = [
            bigquery.SchemaField("recommendation_id", "STRING", mode="REQUIRED"),
            bigquery.SchemaField("analysis_id", "STRING", mode="REQUIRED"),
            bigquery.SchemaField("timestamp", "TIMESTAMP", mode="REQUIRED"),
            bigquery.SchemaField("symbol", "STRING", mode="REQUIRED"),
            bigquery.SchemaField("action", "STRING"),
            bigquery.SchemaField("confidence", "FLOAT64"),
            bigquery.SchemaField("predicted_price", "FLOAT64"),
            bigquery.SchemaField("entry_price", "FLOAT64"),
            bigquery.SchemaField("target_price", "FLOAT64"),
            bigquery.SchemaField("stop_loss", "FLOAT64"),
            bigquery.SchemaField("time_horizon", "STRING"),
            bigquery.SchemaField("actual_return_1d", "FLOAT64"),
            bigquery.SchemaField("actual_return_7d", "FLOAT64"),
            bigquery.SchemaField("actual_return_30d", "FLOAT64"),
            bigquery.SchemaField("accuracy_score", "FLOAT64"),
        ]

        table_ref = f"{self.project_id}.{self.dataset_id}.recommendations"
        table = bigquery.Table(table_ref, schema=schema)
        table.time_partitioning = bigquery.TimePartitioning(
            type_=bigquery.TimePartitioningType.DAY,
            field="timestamp"
        )
        table.clustering_fields = ["symbol", "action"]

        self.client.create_table(table, exists_ok=True)
        logger.info("[BigQuery] Recommendations table created")

    def _create_agent_performance_table(self):
        """Create agent performance table for optimization"""
        schema = [
            bigquery.SchemaField("execution_id", "STRING", mode="REQUIRED"),
            bigquery.SchemaField("timestamp", "TIMESTAMP", mode="REQUIRED"),
            bigquery.SchemaField("analysis_id", "STRING"),
            bigquery.SchemaField("agent_name", "STRING", mode="REQUIRED"),
            bigquery.SchemaField("execution_time_seconds", "FLOAT64"),
            bigquery.SchemaField("tokens_used", "INT64"),
            bigquery.SchemaField("cost_usd", "FLOAT64"),
            bigquery.SchemaField("model_used", "STRING"),
            bigquery.SchemaField("cache_hit", "BOOLEAN"),
            bigquery.SchemaField("error_occurred", "BOOLEAN"),
            bigquery.SchemaField("output_quality_score", "FLOAT64"),
        ]

        table_ref = f"{self.project_id}.{self.dataset_id}.agent_performance"
        table = bigquery.Table(table_ref, schema=schema)
        table.time_partitioning = bigquery.TimePartitioning(
            type_=bigquery.TimePartitioningType.DAY,
            field="timestamp"
        )
        table.clustering_fields = ["agent_name", "model_used"]

        self.client.create_table(table, exists_ok=True)
        logger.info("[BigQuery] Agent performance table created")

    def _create_market_trends_table(self):
        """Create market trends table for ML training"""
        schema = [
            bigquery.SchemaField("trend_id", "STRING", mode="REQUIRED"),
            bigquery.SchemaField("timestamp", "TIMESTAMP", mode="REQUIRED"),
            bigquery.SchemaField("symbol", "STRING", mode="REQUIRED"),
            bigquery.SchemaField("sector", "STRING"),
            bigquery.SchemaField("price", "FLOAT64"),
            bigquery.SchemaField("volume", "INT64"),
            bigquery.SchemaField("sentiment_score", "FLOAT64"),
            bigquery.SchemaField("news_count", "INT64"),
            bigquery.SchemaField("recommendation_distribution", "JSON"),
            bigquery.SchemaField("macro_indicators", "JSON"),
        ]

        table_ref = f"{self.project_id}.{self.dataset_id}.market_trends"
        table = bigquery.Table(table_ref, schema=schema)
        table.time_partitioning = bigquery.TimePartitioning(
            type_=bigquery.TimePartitioningType.DAY,
            field="timestamp"
        )
        table.clustering_fields = ["symbol", "sector"]

        self.client.create_table(table, exists_ok=True)
        logger.info("[BigQuery] Market trends table created")

    async def store_analysis(self, analysis_id: str, analysis_data: Dict[str, Any]):
        """Store analysis in BigQuery data lake"""
        if not self.enabled:
            return

        try:
            table_ref = f"{self.project_id}.{self.dataset_id}.analyses"

            rows_to_insert = [{
                "analysis_id": analysis_id,
                "timestamp": datetime.utcnow().isoformat(),
                "user_id": analysis_data.get("user_id", "anonymous"),
                "query": analysis_data.get("query", ""),
                "symbols": analysis_data.get("symbols", []),
                "recommendation": analysis_data.get("recommendations", {}).get("action", "HOLD"),
                "confidence": analysis_data.get("recommendations", {}).get("confidence", 0.5),
                "target_price": analysis_data.get("recommendations", {}).get("target_price", 0),
                "actual_price": analysis_data.get("analysis", {}).get("market_data", {}).get("price", 0),
                "enrichment_status": analysis_data.get("enrichment_status", "disabled"),
                "execution_time_seconds": analysis_data.get("execution_time", 0),
                "cost_usd": analysis_data.get("cost_usd", 0),
                "cache_hit": analysis_data.get("cache_hit", False),
                "agent_results": json.dumps(analysis_data.get("analysis", {}))
            }]

            errors = self.client.insert_rows_json(table_ref, rows_to_insert)
            if errors:
                logger.error(f"[BigQuery] Insert errors: {errors}")
            else:
                logger.info(f"[BigQuery] Stored analysis {analysis_id}")

        except Exception as e:
            logger.error(f"[BigQuery] Failed to store analysis: {e}")

    async def get_symbol_history(self, symbol: str, days: int = 30) -> List[Dict]:
        """Get historical analyses for a symbol"""
        if not self.enabled:
            return []

        query = f"""
        SELECT
            timestamp,
            recommendation,
            confidence,
            target_price,
            actual_price,
            enrichment_status
        FROM `{self.project_id}.{self.dataset_id}.analyses`
        WHERE '{symbol}' IN UNNEST(symbols)
          AND timestamp >= TIMESTAMP_SUB(CURRENT_TIMESTAMP(), INTERVAL {days} DAY)
        ORDER BY timestamp DESC
        LIMIT 100
        """

        try:
            query_job = self.client.query(query)
            results = query_job.result()

            history = []
            for row in results:
                history.append({
                    "timestamp": row.timestamp.isoformat(),
                    "recommendation": row.recommendation,
                    "confidence": row.confidence,
                    "target_price": row.target_price,
                    "actual_price": row.actual_price,
                    "enrichment_status": row.enrichment_status
                })

            return history

        except Exception as e:
            logger.error(f"[BigQuery] Failed to query history: {e}")
            return []

    async def get_recommendation_accuracy(self, days: int = 30) -> Dict[str, float]:
        """Calculate recommendation accuracy over time"""
        if not self.enabled:
            return {}

        query = f"""
        SELECT
            action,
            AVG(accuracy_score) as avg_accuracy,
            COUNT(*) as total_count
        FROM `{self.project_id}.{self.dataset_id}.recommendations`
        WHERE timestamp >= TIMESTAMP_SUB(CURRENT_TIMESTAMP(), INTERVAL {days} DAY)
          AND accuracy_score IS NOT NULL
        GROUP BY action
        """

        try:
            query_job = self.client.query(query)
            results = query_job.result()

            accuracy = {}
            for row in results:
                accuracy[row.action] = {
                    "accuracy": round(row.avg_accuracy, 3),
                    "count": row.total_count
                }

            return accuracy

        except Exception as e:
            logger.error(f"[BigQuery] Failed to calculate accuracy: {e}")
            return {}

    async def get_agent_performance_stats(self, days: int = 7) -> Dict[str, Any]:
        """Get agent performance statistics"""
        if not self.enabled:
            return {}

        query = f"""
        SELECT
            agent_name,
            model_used,
            AVG(execution_time_seconds) as avg_time,
            AVG(cost_usd) as avg_cost,
            SUM(cache_hit) / COUNT(*) as cache_hit_rate,
            AVG(output_quality_score) as avg_quality
        FROM `{self.project_id}.{self.dataset_id}.agent_performance`
        WHERE timestamp >= TIMESTAMP_SUB(CURRENT_TIMESTAMP(), INTERVAL {days} DAY)
        GROUP BY agent_name, model_used
        ORDER BY avg_cost DESC
        """

        try:
            query_job = self.client.query(query)
            results = query_job.result()

            stats = {}
            for row in results:
                key = f"{row.agent_name}_{row.model_used}"
                stats[key] = {
                    "agent": row.agent_name,
                    "model": row.model_used,
                    "avg_time": round(row.avg_time, 2),
                    "avg_cost": round(row.avg_cost, 4),
                    "cache_hit_rate": round(row.cache_hit_rate or 0, 3),
                    "avg_quality": round(row.avg_quality or 0, 3)
                }

            return stats

        except Exception as e:
            logger.error(f"[BigQuery] Failed to get agent stats: {e}")
            return {}

    async def export_training_data(self, symbol: str, destination_uri: str):
        """Export data for ML model training"""
        if not self.enabled:
            return

        query = f"""
        SELECT
            a.symbols,
            a.recommendation,
            a.confidence,
            a.target_price,
            a.actual_price,
            a.agent_results,
            r.actual_return_7d,
            r.actual_return_30d,
            t.sentiment_score,
            t.news_count,
            t.macro_indicators
        FROM `{self.project_id}.{self.dataset_id}.analyses` a
        LEFT JOIN `{self.project_id}.{self.dataset_id}.recommendations` r
          ON a.analysis_id = r.analysis_id
        LEFT JOIN `{self.project_id}.{self.dataset_id}.market_trends` t
          ON a.symbols[0] = t.symbol
          AND DATE(a.timestamp) = DATE(t.timestamp)
        WHERE '{symbol}' IN UNNEST(a.symbols)
          AND a.timestamp >= TIMESTAMP_SUB(CURRENT_TIMESTAMP(), INTERVAL 365 DAY)
        """

        try:
            job_config = bigquery.QueryJobConfig(
                destination=destination_uri,
                write_disposition="WRITE_TRUNCATE"
            )

            query_job = self.client.query(query, job_config=job_config)
            query_job.result()

            logger.info(f"[BigQuery] Exported training data to {destination_uri}")

        except Exception as e:
            logger.error(f"[BigQuery] Export failed: {e}")


# Global BigQuery instance
bigquery_data_lake = None


def get_bigquery_data_lake(project_id: str = None, credentials_path: str = None):
    """Get or create BigQuery data lake instance"""
    global bigquery_data_lake

    if bigquery_data_lake is None and project_id:
        bigquery_data_lake = BigQueryDataLake(project_id, credentials_path=credentials_path)

    return bigquery_data_lake
