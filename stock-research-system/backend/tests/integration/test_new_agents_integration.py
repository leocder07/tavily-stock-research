"""
Unit tests for new agent integrations (Valuation, Macro, Insider)
Tests the integration of new agents into division leaders and data flow
"""

import pytest
import asyncio
from unittest.mock import Mock, AsyncMock, patch
from datetime import datetime
from typing import Dict, Any

# Import the agents and orchestrators
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Since we're testing integration without full imports, we'll mock the agents
# and test the integration logic directly


class TestValuationAgentIntegration:
    """Test Valuation Specialist Agent integration into Analysis Division"""

    @pytest.fixture
    def mock_llm(self):
        """Mock LLM for testing"""
        llm = Mock()
        llm.ainvoke = AsyncMock(return_value=Mock(content="Test analysis"))
        return llm

    @pytest.fixture
    def mock_memory(self):
        """Mock memory system"""
        memory = Mock()
        memory.episodic = Mock()
        memory.episodic.add_memory = Mock()
        memory.working = Mock()
        memory.working.update_context = Mock()
        return memory

    @pytest.mark.asyncio
    async def test_valuation_agent_in_analysis_division(self, mock_llm, mock_memory):
        """Test that Valuation Agent is properly integrated into Analysis Division"""
        leader = AnalysisDivisionLeader(
            llm=mock_llm,
            tavily_client=None,
            memory=mock_memory
        )

        # Verify valuation_specialist is in workers list
        assert "valuation_specialist" in leader.workers

        # Verify valuation_agent is initialized
        assert hasattr(leader, 'valuation_agent')
        assert isinstance(leader.valuation_agent, ValuationSpecialistAgent)

    @pytest.mark.asyncio
    async def test_valuation_task_creation(self, mock_llm, mock_memory):
        """Test that valuation tasks are created for analysis"""
        leader = AnalysisDivisionLeader(
            llm=mock_llm,
            tavily_client=None,
            memory=mock_memory
        )

        state = AnalysisDivisionState(
            request_id="test-123",
            query="Analyze AAPL valuation",
            symbols=["AAPL"],
            priority="high",
            context={}
        )

        # Plan analysis (creates tasks)
        result = await leader.plan_analysis(state)

        # Verify valuation tasks are created
        valuation_tasks = [t for t in result['analysis_tasks'] if 'valuation' in t.task_type.lower()]
        assert len(valuation_tasks) > 0, "No valuation tasks created"
        assert valuation_tasks[0].symbols == ["AAPL"]

    @pytest.mark.asyncio
    async def test_valuation_state_field_exists(self):
        """Test that valuation_analysis field exists in state"""
        state = AnalysisDivisionState(
            request_id="test-123",
            query="Test",
            symbols=["AAPL"],
            priority="high",
            context={}
        )

        # Verify valuation_analysis field exists and is dict
        assert hasattr(state, 'valuation_analysis')
        assert isinstance(state.valuation_analysis, dict)


class TestMacroAgentIntegration:
    """Test Macro Economics Agent integration into Research Division"""

    @pytest.fixture
    def mock_llm(self):
        llm = Mock()
        llm.ainvoke = AsyncMock(return_value=Mock(content="Test research"))
        return llm

    @pytest.mark.asyncio
    async def test_macro_agent_in_research_division(self, mock_llm):
        """Test that Macro Agent is properly integrated into Research Division"""
        leader = ResearchDivisionLeader(
            llm=mock_llm,
            tavily_client=None,
            memory=None
        )

        # Verify macro_agent is initialized
        assert hasattr(leader, 'macro_agent')
        assert isinstance(leader.macro_agent, MacroEconomicsAgent)

    @pytest.mark.asyncio
    async def test_macro_task_creation(self, mock_llm):
        """Test that macro economics tasks are created"""
        leader = ResearchDivisionLeader(
            llm=mock_llm,
            tavily_client=None,
            memory=None
        )

        state = ResearchDivisionState(
            task="Research macro trends",
            parent_query="Analyze AAPL",
            request_id="test-123",
            priority="high",
            context={"symbols": ["AAPL"]}
        )

        # Plan research
        result = await leader.plan_research(state)

        # Verify macro_analyst task is created
        tasks = result['research_tasks']
        macro_tasks = [t for t in tasks if t.worker_type == "macro_analyst"]
        assert len(macro_tasks) > 0, "No macro analyst tasks created"
        assert "fed_policy" in macro_tasks[0].focus_areas


class TestInsiderAgentIntegration:
    """Test Insider Activity Agent integration into Strategy Division"""

    @pytest.fixture
    def mock_llm(self):
        llm = Mock()
        llm.ainvoke = AsyncMock(return_value=Mock(content="Test strategy"))
        return llm

    @pytest.fixture
    def mock_memory(self):
        memory = Mock()
        memory.episodic = Mock()
        memory.episodic.add_memory = Mock()
        memory.episodic.retrieve_similar = Mock(return_value=[])
        memory.working = Mock()
        memory.working.update_context = Mock()
        memory.shared = Mock()
        return memory

    @pytest.mark.asyncio
    async def test_insider_agent_in_strategy_division(self, mock_llm, mock_memory):
        """Test that Insider Agent is properly integrated into Strategy Division"""
        leader = StrategyDivisionLeader(
            memory_system=mock_memory,
            llm=mock_llm
        )

        # Verify insider_analyst is in workers list
        assert "insider_analyst" in leader.workers

        # Verify insider_agent is initialized
        assert hasattr(leader, 'insider_agent')
        assert isinstance(leader.insider_agent, InsiderActivityAgent)

    @pytest.mark.asyncio
    async def test_insider_state_field_exists(self):
        """Test that insider_analysis field exists in state"""
        state = StrategyDivisionState(
            request_id="test-123",
            query="Test strategy",
            symbols=["AAPL"],
            research_findings={},
            analysis_results={}
        )

        # Verify insider_analysis field exists
        assert hasattr(state, 'insider_analysis')
        assert isinstance(state.insider_analysis, dict)


class TestMongoDBSchemaUpdate:
    """Test MongoDB schema includes new agent fields"""

    def test_analysis_result_has_new_fields(self):
        """Test that AnalysisResultDocument has valuation, macro, and insider fields"""
        # Create a document with all fields
        doc = AnalysisResultDocument(
            analysis_id="test-123",
            query="Test query",
            symbols=["AAPL"],
            recommendations={},
            executive_summary="Test",
            investment_thesis="Test",
            confidence_score=0.8,
            execution_time=10.5,
            valuation_analysis={"AAPL": {"intrinsic_value": 180.0}},
            macro_analysis={"fed_policy": {"stance": "NEUTRAL"}},
            insider_analysis={"AAPL": {"smart_money_score": 7.5}}
        )

        # Verify fields exist and are populated
        assert hasattr(doc, 'valuation_analysis')
        assert hasattr(doc, 'macro_analysis')
        assert hasattr(doc, 'insider_analysis')
        assert doc.valuation_analysis["AAPL"]["intrinsic_value"] == 180.0
        assert doc.macro_analysis["fed_policy"]["stance"] == "NEUTRAL"
        assert doc.insider_analysis["AAPL"]["smart_money_score"] == 7.5


class TestTavilyAPIEnhancements:
    """Test Tavily API service enhancements"""

    @pytest.mark.asyncio
    async def test_extract_content_method_exists(self):
        """Test that extract_content method exists in TavilyMarketService"""
        from services.tavily_service import TavilyMarketService

        service = TavilyMarketService(api_key="test-key")
        assert hasattr(service, 'extract_content')
        assert callable(service.extract_content)

    @pytest.mark.asyncio
    async def test_get_search_context_method_exists(self):
        """Test that get_search_context method exists"""
        from services.tavily_service import TavilyMarketService

        service = TavilyMarketService(api_key="test-key")
        assert hasattr(service, 'get_search_context')
        assert callable(service.get_search_context)

    @pytest.mark.asyncio
    async def test_no_mock_data_fallback(self):
        """Test that service returns unavailable status instead of mock data"""
        from services.tavily_service import TavilyMarketService

        service = TavilyMarketService(api_key="invalid-key")

        # Mock both Yahoo Finance and Tavily to fail
        with patch('yfinance.Ticker', side_effect=Exception("Network error")):
            with patch.object(service.client, 'qna_search', side_effect=Exception("API error")):
                result = await service.get_stock_price("AAPL")

                # Should return unavailable, not mock data
                assert result['data_quality'] == 'unavailable'
                assert result['source'] == 'unavailable'
                assert 'error' in result
                assert result['price'] == 0  # Not a random mock price


class TestAgentFailureRecovery:
    """Test agent failure recovery with partial results"""

    @pytest.mark.asyncio
    async def test_partial_results_on_failure(self):
        """Test that agents return partial results when available"""
        from agents.base_agent import BaseFinancialAgent, AgentState

        class TestAgent(BaseFinancialAgent):
            async def execute(self, context: Dict[str, Any]) -> AgentState:
                # Simulate partial results before failure
                self.state.output_data = {
                    'partial_metric_1': 100,
                    'partial_metric_2': 200
                }
                # Simulate failure
                raise Exception("API timeout")

        agent = TestAgent(agent_id="test-agent", agent_type="test")
        result = await agent.run({"test": "data"})

        # Should complete with errors, not fail completely
        assert result.status == "COMPLETED_WITH_ERRORS"
        assert result.metadata.get('partial_results') is True
        assert 'partial_metric_1' in result.output_data
        assert result.output_data['partial_metric_1'] == 100

    @pytest.mark.asyncio
    async def test_complete_failure_without_partial_results(self):
        """Test that agents fail completely when no partial results"""
        from agents.base_agent import BaseFinancialAgent, AgentState

        class TestAgent(BaseFinancialAgent):
            async def execute(self, context: Dict[str, Any]) -> AgentState:
                # No partial results
                raise Exception("Complete failure")

        agent = TestAgent(agent_id="test-agent", agent_type="test")
        result = await agent.run({"test": "data"})

        # Should fail completely
        assert result.status == "FAILED"
        assert result.error_message is not None


# Run tests
if __name__ == "__main__":
    pytest.main([__file__, "-v", "--asyncio-mode=auto"])
