"""
Simple integration tests for new agents
Tests configuration and basic functionality without complex dependencies
"""

import pytest
from unittest.mock import Mock, AsyncMock
from datetime import datetime


class TestMongoDBSchema:
    """Test MongoDB schema includes new fields"""

    def test_analysis_result_document_fields(self):
        """Test that AnalysisResultDocument has valuation, macro, and insider fields"""
        import sys
        import os
        sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

        from models.database import AnalysisResultDocument

        # Create document with new fields
        doc = AnalysisResultDocument(
            analysis_id="test-123",
            query="Test query",
            symbols=["AAPL"],
            recommendations={},
            executive_summary="Test summary",
            investment_thesis="Test thesis",
            confidence_score=0.8,
            execution_time=10.5,
            valuation_analysis={"AAPL": {"intrinsic_value": 180.0}},
            macro_analysis={"fed_policy": "NEUTRAL"},
            insider_analysis={"AAPL": {"smart_money_score": 7.5}}
        )

        # Verify new fields exist
        assert hasattr(doc, 'valuation_analysis')
        assert hasattr(doc, 'macro_analysis')
        assert hasattr(doc, 'insider_analysis')

        # Verify data
        assert doc.valuation_analysis["AAPL"]["intrinsic_value"] == 180.0
        assert doc.insider_analysis["AAPL"]["smart_money_score"] == 7.5


class TestTavilyService:
    """Test Tavily service enhancements"""

    def test_extract_content_method_exists(self):
        """Test that extract_content method is added"""
        import sys
        import os
        sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

        from services.tavily_service import TavilyMarketService

        service = TavilyMarketService(api_key="test-key")

        # Verify new methods exist
        assert hasattr(service, 'extract_content')
        assert callable(service.extract_content)

    def test_get_search_context_method_exists(self):
        """Test that get_search_context method is added"""
        import sys
        import os
        sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

        from services.tavily_service import TavilyMarketService

        service = TavilyMarketService(api_key="test-key")

        # Verify Context API method exists
        assert hasattr(service, 'get_search_context')
        assert callable(service.get_search_context)


class TestAgentFailureRecovery:
    """Test enhanced agent failure handling"""

    @pytest.mark.asyncio
    async def test_partial_results_status(self):
        """Test that agent returns COMPLETED_WITH_ERRORS for partial results"""
        import sys
        import os
        sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

        from agents.base_agent import BaseFinancialAgent, AgentState

        class TestAgent(BaseFinancialAgent):
            async def execute(self, context):
                # Simulate partial data collection
                self.state.output_data = {
                    'metric1': 100,
                    'metric2': 200
                }
                # Simulate failure
                raise Exception("API timeout after partial data")

        agent = TestAgent(agent_id="test-1", agent_type="test")
        result = await agent.run({"test": "data"})

        # Should complete with errors, not fail completely
        assert result.status == "COMPLETED_WITH_ERRORS"
        assert result.metadata.get('partial_results') is True
        assert 'metric1' in result.output_data

    @pytest.mark.asyncio
    async def test_complete_failure_no_partial_data(self):
        """Test that agent fails completely when no partial data"""
        import sys
        import os
        sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

        from agents.base_agent import BaseFinancialAgent, AgentState

        class TestAgent(BaseFinancialAgent):
            async def execute(self, context):
                # No partial data before failure
                raise Exception("Complete failure")

        agent = TestAgent(agent_id="test-2", agent_type="test")
        result = await agent.run({"test": "data"})

        # Should fail completely
        assert result.status == "FAILED"
        assert result.error_message is not None


class TestDivisionLeaderConfiguration:
    """Test that division leaders have new agents configured"""

    def test_analysis_leader_has_valuation_field(self):
        """Test Analysis Division State has valuation_analysis field"""
        import sys
        import os
        sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

        # Check if valuation is in analysis_leader.py
        with open(os.path.join(os.path.dirname(__file__), '../agents/orchestrators/analysis_leader.py'), 'r') as f:
            content = f.read()
            assert 'valuation_analysis' in content
            assert 'ValuationSpecialistAgent' in content
            assert '"valuation_specialist"' in content

    def test_research_leader_has_macro_field(self):
        """Test Research Division has macro economics configuration"""
        import sys
        import os
        sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

        # Check if macro is in research_leader.py
        with open(os.path.join(os.path.dirname(__file__), '../agents/orchestrators/research_leader.py'), 'r') as f:
            content = f.read()
            assert 'MacroEconomicsAgent' in content
            assert '"macro_analyst"' in content

    def test_strategy_leader_has_insider_field(self):
        """Test Strategy Division has insider activity configuration"""
        import sys
        import os
        sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

        # Check if insider is in strategy_leader.py
        with open(os.path.join(os.path.dirname(__file__), '../agents/orchestrators/strategy_leader.py'), 'r') as f:
            content = f.read()
            assert 'InsiderActivityAgent' in content
            assert '"insider_analyst"' in content
            assert 'insider_analysis' in content


# Run tests
if __name__ == "__main__":
    pytest.main([__file__, "-v"])
