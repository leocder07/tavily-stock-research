#!/usr/bin/env python3
"""Consolidated integration tests for Stock Research System"""

import pytest
import asyncio
import json
from unittest.mock import Mock, patch
import httpx
import websockets
from datetime import datetime

# Configuration
API_BASE_URL = "http://localhost:8000"
WS_BASE_URL = "ws://localhost:8000"


class TestAPIEndpoints:
    """Test REST API endpoints"""

    @pytest.mark.asyncio
    async def test_health_check(self):
        """Test health endpoint"""
        async with httpx.AsyncClient() as client:
            response = await client.get(f"{API_BASE_URL}/health")
            assert response.status_code == 200
            data = response.json()
            assert data["status"] == "healthy"

    @pytest.mark.asyncio
    async def test_stock_price_endpoint(self):
        """Test stock price endpoint"""
        async with httpx.AsyncClient() as client:
            response = await client.get(f"{API_BASE_URL}/api/v1/market/price/AAPL")
            assert response.status_code == 200
            data = response.json()
            assert "symbol" in data
            assert "price" in data
            assert data["symbol"] == "AAPL"

    @pytest.mark.asyncio
    async def test_market_sectors(self):
        """Test sector performance endpoint"""
        async with httpx.AsyncClient() as client:
            response = await client.get(f"{API_BASE_URL}/api/v1/market/sectors")
            assert response.status_code == 200
            data = response.json()
            assert "sectors" in data

    @pytest.mark.asyncio
    async def test_analysis_request(self):
        """Test stock analysis request"""
        async with httpx.AsyncClient() as client:
            payload = {
                "query": "Analyze AAPL stock",
                "priority": "normal"
            }
            response = await client.post(
                f"{API_BASE_URL}/api/v1/analyze",
                json=payload
            )
            assert response.status_code == 200
            data = response.json()
            assert "analysis_id" in data
            assert "status" in data


class TestWebSocketEndpoints:
    """Test WebSocket endpoints"""

    @pytest.mark.asyncio
    async def test_chat_websocket(self):
        """Test chat WebSocket connection and messaging"""
        uri = f"{WS_BASE_URL}/ws/chat"

        async with websockets.connect(uri) as websocket:
            # Receive welcome message
            welcome = await websocket.recv()
            welcome_data = json.loads(welcome)
            assert welcome_data["type"] == "connection_established"

            # Send test message
            message = {
                "type": "chat_message",
                "message": "Hello, can you help me?"
            }
            await websocket.send(json.dumps(message))

            # Receive response
            response = await asyncio.wait_for(websocket.recv(), timeout=5.0)
            response_data = json.loads(response)
            assert response_data["type"] in ["chat_response", "chat_started"]

    @pytest.mark.asyncio
    async def test_analysis_websocket(self):
        """Test analysis progress WebSocket"""
        analysis_id = "test-123"
        uri = f"{WS_BASE_URL}/ws/analysis/{analysis_id}"

        try:
            async with websockets.connect(uri) as websocket:
                # Connection should be established
                assert websocket.open
        except Exception as e:
            # Connection might fail if analysis doesn't exist
            assert "404" in str(e) or "not found" in str(e).lower()


class TestMongoDBIntegration:
    """Test MongoDB integration"""

    @pytest.mark.asyncio
    async def test_mongodb_connection(self):
        """Test MongoDB connection through API"""
        from services.mongodb_connection import mongodb_connection

        # Get database instance
        db = mongodb_connection.get_database(async_mode=True)

        # Test ping
        result = await db.command("ping")
        assert result["ok"] == 1

    @pytest.mark.asyncio
    async def test_database_operations(self):
        """Test basic database operations"""
        from services.mongodb_connection import mongodb_connection

        db = mongodb_connection.get_database(async_mode=True)

        # Insert test document
        test_doc = {
            "_id": f"test_{datetime.utcnow().isoformat()}",
            "test": True,
            "timestamp": datetime.utcnow()
        }

        await db.test_collection.insert_one(test_doc)

        # Find document
        found = await db.test_collection.find_one({"_id": test_doc["_id"]})
        assert found is not None
        assert found["test"] is True

        # Clean up
        await db.test_collection.delete_one({"_id": test_doc["_id"]})


class TestTavilyIntegration:
    """Test Tavily service integration"""

    @pytest.mark.asyncio
    async def test_tavily_search(self):
        """Test Tavily search functionality"""
        from services.tavily_service import TavilyMarketService
        import os

        api_key = os.getenv("TAVILY_API_KEY")
        if not api_key:
            pytest.skip("Tavily API key not configured")

        service = TavilyMarketService(api_key=api_key)

        # Test stock price fetch
        result = await service.get_stock_price("AAPL")
        assert "symbol" in result
        assert "price" in result
        assert result["symbol"] == "AAPL"

    @pytest.mark.asyncio
    async def test_tavily_news(self):
        """Test Tavily news fetch"""
        from services.tavily_service import TavilyMarketService
        import os

        api_key = os.getenv("TAVILY_API_KEY")
        if not api_key:
            pytest.skip("Tavily API key not configured")

        service = TavilyMarketService(api_key=api_key)

        # Test news fetch
        news = await service.get_market_news(["AAPL"], limit=5)
        assert isinstance(news, list)
        assert len(news) <= 5


class TestLangGraphWorkflow:
    """Test LangGraph workflow integration"""

    @pytest.mark.asyncio
    async def test_workflow_initialization(self):
        """Test workflow initialization"""
        from agents.workflow import StockResearchWorkflow
        import os

        tavily_key = os.getenv("TAVILY_API_KEY")
        openai_key = os.getenv("OPENAI_API_KEY")

        if not tavily_key or not openai_key:
            pytest.skip("API keys not configured")

        workflow = StockResearchWorkflow(
            tavily_api_key=tavily_key,
            openai_api_key=openai_key
        )

        assert workflow.workflow is not None
        assert workflow.agents is not None

    @pytest.mark.asyncio
    async def test_workflow_execution(self):
        """Test basic workflow execution"""
        from agents.workflow import StockResearchWorkflow
        import os

        tavily_key = os.getenv("TAVILY_API_KEY")
        openai_key = os.getenv("OPENAI_API_KEY")

        if not tavily_key or not openai_key:
            pytest.skip("API keys not configured")

        workflow = StockResearchWorkflow(
            tavily_api_key=tavily_key,
            openai_api_key=openai_key
        )

        # Test with simple query
        result = await workflow.run(
            query="What is AAPL stock price?",
            request_id="test-request"
        )

        assert result is not None
        assert "symbols" in result


if __name__ == "__main__":
    # Run tests
    pytest.main([__file__, "-v", "--asyncio-mode=auto"])