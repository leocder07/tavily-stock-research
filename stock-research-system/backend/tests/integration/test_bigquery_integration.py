"""
Test BigQuery Data Lake Integration (Phase 4)
Tests data storage, retrieval, and analytics functionality
"""

import pytest
import asyncio
from datetime import datetime, timedelta
from unittest.mock import Mock, patch, AsyncMock

from services.bigquery_data_lake import BigQueryDataLake
from services.bigquery_integration import BigQueryIntegration


class TestBigQueryDataLake:
    """Test BigQuery data lake functionality"""

    @pytest.fixture
    def mock_bigquery_client(self):
        """Create mock BigQuery client"""
        client = Mock()
        client.create_dataset = Mock()
        client.create_table = Mock()
        client.insert_rows_json = Mock(return_value=[])  # No errors
        client.query = Mock()
        return client

    @pytest.fixture
    def data_lake(self, mock_bigquery_client):
        """Create data lake instance with mocked client"""
        with patch('services.bigquery_data_lake.bigquery.Client', return_value=mock_bigquery_client):
            lake = BigQueryDataLake(
                project_id="test-project",
                dataset_id="test_dataset"
            )
            lake.client = mock_bigquery_client
            lake.enabled = True
            return lake

    @pytest.mark.asyncio
    async def test_store_analysis(self, data_lake, mock_bigquery_client):
        """Test storing analysis in BigQuery"""
        analysis_data = {
            "query": "Analyze AAPL",
            "symbols": ["AAPL"],
            "recommendations": {
                "action": "BUY",
                "confidence": 0.85,
                "target_price": 200.0
            },
            "analysis": {
                "market_data": {"price": 180.50},
                "sentiment": {"overall_sentiment": 0.75}
            },
            "enrichment_status": "enabled",
            "execution_time": 18.5,
            "cost_usd": 0.13,
            "cache_hit": True
        }

        await data_lake.store_analysis("test-analysis-1", analysis_data)

        # Verify insert was called
        assert mock_bigquery_client.insert_rows_json.called
        call_args = mock_bigquery_client.insert_rows_json.call_args

        # Check table reference
        assert "analyses" in call_args[0][0]

        # Check inserted data
        rows = call_args[0][1]
        assert len(rows) == 1
        assert rows[0]["analysis_id"] == "test-analysis-1"
        assert rows[0]["symbols"] == ["AAPL"]
        assert rows[0]["recommendation"] == "BUY"
        assert rows[0]["confidence"] == 0.85

    @pytest.mark.asyncio
    async def test_get_symbol_history(self, data_lake, mock_bigquery_client):
        """Test retrieving symbol history"""
        # Mock query results
        mock_results = [
            Mock(
                timestamp=datetime.utcnow(),
                recommendation="BUY",
                confidence=0.85,
                target_price=200.0,
                actual_price=180.0,
                enrichment_status="enabled"
            ),
            Mock(
                timestamp=datetime.utcnow() - timedelta(days=1),
                recommendation="HOLD",
                confidence=0.65,
                target_price=185.0,
                actual_price=182.0,
                enrichment_status="enabled"
            )
        ]

        mock_job = Mock()
        mock_job.result.return_value = mock_results
        mock_bigquery_client.query.return_value = mock_job

        history = await data_lake.get_symbol_history("AAPL", days=30)

        # Verify query was called
        assert mock_bigquery_client.query.called

        # Check results
        assert len(history) == 2
        assert history[0]["recommendation"] == "BUY"
        assert history[1]["recommendation"] == "HOLD"

    @pytest.mark.asyncio
    async def test_get_recommendation_accuracy(self, data_lake, mock_bigquery_client):
        """Test calculating recommendation accuracy"""
        # Mock query results
        mock_results = [
            Mock(action="BUY", avg_accuracy=0.82, total_count=45),
            Mock(action="SELL", avg_accuracy=0.78, total_count=23),
            Mock(action="HOLD", avg_accuracy=0.71, total_count=32)
        ]

        mock_job = Mock()
        mock_job.result.return_value = mock_results
        mock_bigquery_client.query.return_value = mock_job

        accuracy = await data_lake.get_recommendation_accuracy(days=30)

        # Verify results
        assert len(accuracy) == 3
        assert accuracy["BUY"]["accuracy"] == 0.82
        assert accuracy["BUY"]["count"] == 45
        assert accuracy["SELL"]["accuracy"] == 0.78
        assert accuracy["HOLD"]["accuracy"] == 0.71

    @pytest.mark.asyncio
    async def test_graceful_degradation(self, mock_bigquery_client):
        """Test system works without BigQuery"""
        # Create data lake that fails to initialize
        with patch('services.bigquery_data_lake.bigquery.Client', side_effect=Exception("No credentials")):
            lake = BigQueryDataLake(
                project_id="test-project",
                dataset_id="test_dataset"
            )

            # Should be disabled
            assert lake.enabled is False

            # Operations should not crash
            await lake.store_analysis("test-id", {})
            history = await lake.get_symbol_history("AAPL")
            assert history == []


class TestBigQueryIntegration:
    """Test BigQuery integration with workflow"""

    @pytest.fixture
    def mock_data_lake(self):
        """Create mock data lake"""
        lake = Mock()
        lake.enabled = True
        lake.project_id = "test-project"
        lake.dataset_id = "test_dataset"
        lake.client = Mock()
        lake.client.insert_rows_json = Mock(return_value=[])
        lake.store_analysis = AsyncMock()
        lake.get_symbol_history = AsyncMock(return_value=[])
        return lake

    @pytest.fixture
    def integration(self, mock_data_lake):
        """Create integration instance"""
        return BigQueryIntegration(mock_data_lake)

    @pytest.mark.asyncio
    async def test_store_analysis_result(self, integration, mock_data_lake):
        """Test storing complete analysis result"""
        result = {
            "analysis_id": "test-123",
            "query": "Analyze TSLA",
            "symbols": ["TSLA"],
            "recommendations": {
                "action": "BUY",
                "confidence": 0.9,
                "target_price": 300.0,
                "stop_loss": 250.0,
                "time_horizon": "medium-term"
            },
            "analysis": {
                "market_data": {"price": 280.0, "volume": 1000000, "sector": "Automotive"},
                "sentiment": {
                    "overall_sentiment": 0.8,
                    "news_items": [{"title": "News 1"}, {"title": "News 2"}]
                },
                "macro_context": {"gdp_growth": 2.5, "inflation": 3.2}
            },
            "cost_usd": 0.15,
            "execution_time": 22.3
        }

        await integration.store_analysis_result("test-123", result)

        # Verify main analysis was stored
        assert mock_data_lake.store_analysis.called

        # Verify recommendations table insert
        assert mock_data_lake.client.insert_rows_json.call_count >= 1

        # Check recommendations data
        calls = mock_data_lake.client.insert_rows_json.call_args_list
        rec_call = next(c for c in calls if "recommendations" in c[0][0])
        rec_rows = rec_call[0][1]

        assert len(rec_rows) == 1
        assert rec_rows[0]["symbol"] == "TSLA"
        assert rec_rows[0]["action"] == "BUY"
        assert rec_rows[0]["confidence"] == 0.9

    @pytest.mark.asyncio
    async def test_store_agent_execution(self, integration, mock_data_lake):
        """Test storing agent execution metrics"""
        await integration.store_agent_execution(
            analysis_id="test-456",
            agent_name="FundamentalAgent",
            execution_time=5.2,
            tokens_used=1500,
            cost=0.045,
            model_used="gpt-4",
            cache_hit=False,
            error_occurred=False,
            quality_score=0.92
        )

        # Verify agent performance insert
        assert mock_data_lake.client.insert_rows_json.called

        call_args = mock_data_lake.client.insert_rows_json.call_args
        assert "agent_performance" in call_args[0][0]

        rows = call_args[0][1]
        assert rows[0]["agent_name"] == "FundamentalAgent"
        assert rows[0]["execution_time_seconds"] == 5.2
        assert rows[0]["tokens_used"] == 1500
        assert rows[0]["cost_usd"] == 0.045
        assert rows[0]["model_used"] == "gpt-4"

    @pytest.mark.asyncio
    async def test_update_recommendation_accuracy(self, integration, mock_data_lake):
        """Test updating recommendation with actual returns"""
        mock_job = Mock()
        mock_job.result = Mock()
        mock_data_lake.client.query.return_value = mock_job

        await integration.update_recommendation_accuracy(
            recommendation_id="rec-123-AAPL",
            actual_return_1d=2.5,
            actual_return_7d=5.8,
            actual_return_30d=12.3
        )

        # Verify UPDATE query was executed
        assert mock_data_lake.client.query.called

        query = mock_data_lake.client.query.call_args[0][0]
        assert "UPDATE" in query
        assert "recommendations" in query
        assert "actual_return_1d = 2.5" in query
        assert "actual_return_7d = 5.8" in query
        assert "accuracy_score" in query

    @pytest.mark.asyncio
    async def test_get_historical_context(self, integration, mock_data_lake):
        """Test getting historical context for symbol"""
        # Mock historical data
        mock_data_lake.get_symbol_history.return_value = [
            {"recommendation": "BUY", "confidence": 0.85, "timestamp": datetime.utcnow().isoformat()},
            {"recommendation": "BUY", "confidence": 0.80, "timestamp": datetime.utcnow().isoformat()},
            {"recommendation": "HOLD", "confidence": 0.70, "timestamp": datetime.utcnow().isoformat()},
            {"recommendation": "BUY", "confidence": 0.75, "timestamp": datetime.utcnow().isoformat()},
            {"recommendation": "SELL", "confidence": 0.65, "timestamp": datetime.utcnow().isoformat()}
        ]

        context = await integration.get_historical_context("AAPL", days=30)

        # Verify context calculation
        assert context["total_analyses"] == 5
        assert context["recent_trend"] == "bullish"  # 3 out of 5 recent are BUY
        assert context["recommendation_counts"]["BUY"] == 3
        assert context["recommendation_counts"]["SELL"] == 1
        assert context["recommendation_counts"]["HOLD"] == 1
        assert 0.7 <= context["avg_confidence"] <= 0.8

    @pytest.mark.asyncio
    async def test_disabled_integration(self, mock_data_lake):
        """Test integration when BigQuery is disabled"""
        mock_data_lake.enabled = False
        integration = BigQueryIntegration(mock_data_lake)

        # All operations should be no-ops
        await integration.store_analysis_result("test", {})
        await integration.store_agent_execution("test", "agent", 1.0, 100, 0.01, "gpt-4", False, False)

        # No calls should have been made
        assert not mock_data_lake.store_analysis.called
        assert not mock_data_lake.client.insert_rows_json.called


@pytest.mark.asyncio
async def test_end_to_end_workflow():
    """Test complete workflow with BigQuery integration"""
    # This would be an integration test with real BigQuery (mocked here)

    with patch('services.bigquery_data_lake.bigquery.Client') as mock_client:
        # Setup
        mock_client.return_value.insert_rows_json.return_value = []

        # Create instances
        data_lake = BigQueryDataLake("test-project", "test_dataset")
        data_lake.enabled = True
        integration = BigQueryIntegration(data_lake)

        # Simulate analysis workflow
        analysis_result = {
            "analysis_id": "workflow-test-789",
            "symbols": ["NVDA"],
            "query": "Should I buy NVDA?",
            "recommendations": {"action": "BUY", "confidence": 0.88},
            "analysis": {
                "market_data": {"price": 500.0},
                "sentiment": {"overall_sentiment": 0.85}
            }
        }

        # Store result
        await integration.store_analysis_result("workflow-test-789", analysis_result)

        # Store agent executions
        await integration.store_agent_execution(
            "workflow-test-789", "FundamentalAgent", 4.5, 1200, 0.036, "gpt-4", False, False, 0.91
        )
        await integration.store_agent_execution(
            "workflow-test-789", "TechnicalAgent", 3.2, 800, 0.024, "gpt-3.5-turbo", True, False, 0.88
        )

        # Verify all data was stored
        assert mock_client.return_value.insert_rows_json.call_count >= 3


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
