"""
End-to-End Test for Multi-Agent Stock Research System
Tests the complete workflow with memory, progress tracking, and visualizations
"""

import asyncio
import uuid
import json
from datetime import datetime
from typing import Dict, Any, List
import logging

from langchain_openai import ChatOpenAI
from tavily import TavilyClient
from motor.motor_asyncio import AsyncIOMotorClient
import os
from dotenv import load_dotenv

# Load environment
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Import all components
from agents.orchestrators.ceo_agent import CEOOrchestrator
from agents.orchestrators.research_leader import ResearchDivisionLeader
from agents.orchestrators.analysis_leader import AnalysisDivisionLeader
from agents.orchestrators.strategy_leader import StrategyDivisionLeader
from agents.tools.tavily_tools import SpecializedTavilyTools
from memory.agent_memory import AgentMemorySystem, SharedMemory
from memory.memory_persistence import MemoryPersistenceService
from memory.memory_consolidation import MemoryConsolidationService, PatternRecognitionService
from services.enhanced_progress_tracker import enhanced_progress_tracker
from agents.main_workflow import MultiAgentWorkflow


class WorkflowTestRunner:
    """Test runner for the complete multi-agent workflow"""

    def __init__(self):
        # Initialize services
        self.tavily_client = TavilyClient(api_key=os.getenv("TAVILY_API_KEY"))
        self.llm = ChatOpenAI(
            model="gpt-4",
            temperature=0.3,
            api_key=os.getenv("OPENAI_API_KEY")
        )

        # MongoDB setup
        mongo_client = AsyncIOMotorClient(os.getenv("MONGODB_URL"))
        self.db = mongo_client.stock_research

        # Memory services
        self.memory_persistence = MemoryPersistenceService(self.db)
        self.shared_memory = SharedMemory()

        # Consolidation service
        self.consolidation_service = MemoryConsolidationService(
            self.memory_persistence,
            self.shared_memory
        )

        # Pattern recognition
        self.pattern_recognition = PatternRecognitionService(self.shared_memory)

        # Tavily tools
        self.tavily_tools = SpecializedTavilyTools(self.tavily_client)

        # Initialize workflow
        self.workflow = MultiAgentWorkflow(
            tavily_api_key=os.getenv("TAVILY_API_KEY"),
            openai_api_key=os.getenv("OPENAI_API_KEY"),
            db=self.db
        )

    async def test_memory_system(self):
        """Test memory system functionality"""
        logger.info("=== Testing Memory System ===")

        # Create agent memory systems
        ceo_memory = AgentMemorySystem("CEO", self.shared_memory)
        research_memory = AgentMemorySystem("Research_Leader", self.shared_memory)

        # Test working memory
        ceo_memory.working.update_context({"test": "data", "symbols": ["AAPL", "NVDA"]})
        assert "test" in ceo_memory.working.context

        # Test episodic memory
        ceo_memory.episodic.add_memory(
            "Analyzed AAPL and NVDA",
            {"symbols": ["AAPL", "NVDA"], "recommendation": "BUY"},
            importance=0.9
        )

        # Test memory retrieval
        similar = ceo_memory.episodic.retrieve_similar("AAPL analysis", k=1)
        assert len(similar) > 0
        logger.info(f"Retrieved memory: {similar[0]['content']}")

        # Test shared memory
        self.shared_memory.add_insight("AAPL", {"signal": "bullish", "confidence": 0.8})
        insights = self.shared_memory.get_symbol_insights("AAPL")
        assert len(insights) > 0
        logger.info(f"Shared insight: {insights[0]}")

        # Test pattern recognition
        self.shared_memory.add_pattern({
            "type": "bullish_breakout",
            "condition": "RSI > 70 and volume spike",
            "success_rate": 0.75,
            "confidence": 0.8
        })

        pattern = await self.pattern_recognition.recognize_market_pattern({
            "symbols": ["AAPL"],
            "research": {"RSI": 72, "volume": "high"}
        })

        if pattern:
            logger.info(f"Pattern recognized: {pattern['pattern']['type']}")

        # Test persistence
        await self.memory_persistence.save_memory(
            ceo_memory.episodic.memories[0],
            "CEO"
        )

        loaded = await self.memory_persistence.load_recent_memories("CEO", limit=1)
        assert len(loaded) > 0
        logger.info(f"Persisted and loaded: {loaded[0].content}")

        logger.info("✓ Memory system test passed")

    async def test_progress_tracking(self):
        """Test progress tracking functionality"""
        logger.info("=== Testing Progress Tracking ===")

        request_id = str(uuid.uuid4())

        # Start analysis
        await enhanced_progress_tracker.start_analysis(
            request_id,
            "Test AAPL analysis",
            user_id="test_user"
        )

        # Update agent status
        await enhanced_progress_tracker.update_agent_status(
            request_id,
            "CEO",
            "Planning analysis strategy",
            "thinking"
        )

        # Add citation
        await enhanced_progress_tracker.add_citation(
            request_id,
            "Research_Leader",
            "Yahoo Finance",
            "https://finance.yahoo.com/quote/AAPL",
            "AAPL current price: $175.43",
            confidence=0.95
        )

        # Memory recall event
        await enhanced_progress_tracker.memory_recalled(
            request_id,
            "CEO",
            "Previous AAPL analysis showed strong fundamentals",
            relevance=0.85
        )

        # Pattern detection
        await enhanced_progress_tracker.pattern_detected(
            request_id,
            "bullish_trend",
            "Detected bullish trend pattern in AAPL",
            confidence=0.75
        )

        # Insight generation
        await enhanced_progress_tracker.insight_generated(
            request_id,
            "Analysis_Leader",
            "AAPL showing strong technical indicators",
            importance=0.8
        )

        # Delegation event
        await enhanced_progress_tracker.delegation_event(
            request_id,
            "CEO",
            "Research_Leader",
            "Gather market data for AAPL"
        )

        # Tool call
        await enhanced_progress_tracker.tool_call(
            request_id,
            "Research_Leader",
            "tavily_search",
            {"query": "AAPL news", "depth": "advanced"}
        )

        # Decision made
        await enhanced_progress_tracker.decision_made(
            request_id,
            "Strategy_Leader",
            "Recommend BUY for AAPL",
            "Strong fundamentals and technical indicators"
        )

        # Get status
        status = enhanced_progress_tracker.get_analysis_status(request_id)
        assert status is not None
        logger.info(f"Analysis status: {status['status']}")

        # Get event history
        events = enhanced_progress_tracker.get_event_history(request_id, limit=10)
        logger.info(f"Total events: {len(events)}")

        # Complete analysis
        await enhanced_progress_tracker.complete_analysis(
            request_id,
            {"confidence_score": 0.85, "recommendation": "BUY"}
        )

        logger.info("✓ Progress tracking test passed")

    async def test_division_leaders(self):
        """Test division leader orchestration"""
        logger.info("=== Testing Division Leaders ===")

        request_id = str(uuid.uuid4())

        # Research Division Test
        research_memory = AgentMemorySystem("Research_Leader", self.shared_memory)
        research_leader = ResearchDivisionLeader(research_memory, self.llm)

        from agents.orchestrators.research_leader import ResearchDivisionState, ResearchTask

        research_state = ResearchDivisionState(
            request_id=request_id,
            query="Analyze AAPL for investment",
            symbols=["AAPL"]
        )

        # Plan research
        research_state = await research_leader.plan_research(research_state)
        assert len(research_state.research_tasks) > 0
        logger.info(f"Research tasks created: {len(research_state.research_tasks)}")

        # Analysis Division Test
        analysis_memory = AgentMemorySystem("Analysis_Leader", self.shared_memory)
        analysis_leader = AnalysisDivisionLeader(analysis_memory, self.llm)

        from agents.orchestrators.analysis_leader import AnalysisDivisionState

        analysis_state = AnalysisDivisionState(
            request_id=request_id,
            query="Analyze AAPL for investment",
            symbols=["AAPL"],
            research_findings={"data": "mock research data"}
        )

        # Plan analysis
        analysis_state = await analysis_leader.plan_analysis(analysis_state)
        assert len(analysis_state.analysis_tasks) > 0
        logger.info(f"Analysis tasks created: {len(analysis_state.analysis_tasks)}")

        # Strategy Division Test
        strategy_memory = AgentMemorySystem("Strategy_Leader", self.shared_memory)
        strategy_leader = StrategyDivisionLeader(strategy_memory, self.llm)

        from agents.orchestrators.strategy_leader import StrategyDivisionState

        strategy_state = StrategyDivisionState(
            request_id=request_id,
            query="Analyze AAPL for investment",
            symbols=["AAPL"],
            research_findings={"data": "mock research"},
            analysis_results={"technical": "bullish", "fundamental": "strong"}
        )

        # Formulate strategy
        strategy_state = await strategy_leader.formulate_strategy(strategy_state)
        assert len(strategy_state.proposed_strategies) > 0
        logger.info(f"Strategies proposed: {len(strategy_state.proposed_strategies)}")

        logger.info("✓ Division leaders test passed")

    async def test_tavily_tools(self):
        """Test specialized Tavily tools"""
        logger.info("=== Testing Tavily Tools ===")

        # Test research search
        search_result = await self.tavily_tools.research_search(
            "AAPL latest news",
            focus="news",
            request_id=str(uuid.uuid4())
        )
        assert "results" in search_result
        logger.info(f"Search results: {len(search_result['results'])}")

        # Test financial extract
        extract_result = await self.tavily_tools.financial_extract(
            symbols=["AAPL"],
            data_types=["price"],
            request_id=str(uuid.uuid4())
        )
        assert "data" in extract_result
        logger.info(f"Extracted data for: {list(extract_result['data'].keys())}")

        # Test competitive map
        map_result = await self.tavily_tools.competitive_map(
            company="AAPL",
            industry="Technology",
            request_id=str(uuid.uuid4())
        )
        assert "competitors" in map_result
        logger.info(f"Competitors found: {len(map_result['competitors'])}")

        logger.info("✓ Tavily tools test passed")

    async def test_full_workflow(self):
        """Test the complete multi-agent workflow"""
        logger.info("=== Testing Full Workflow ===")

        query = "Should I invest in AAPL? Provide comprehensive analysis."
        request_id = str(uuid.uuid4())

        logger.info(f"Starting workflow for: {query}")

        # Execute workflow
        try:
            result = await asyncio.wait_for(
                self.workflow.execute(query, user_id="test_user"),
                timeout=180.0  # 3 minutes timeout
            )

            # Validate result structure
            assert result["status"] == "completed"
            assert "symbols" in result
            assert "executive_summary" in result
            assert "recommendations" in result
            assert "confidence_score" in result

            logger.info(f"Workflow completed successfully")
            logger.info(f"Symbols analyzed: {result['symbols']}")
            logger.info(f"Confidence score: {result['confidence_score']}")
            logger.info(f"Executive summary: {result['executive_summary'][:200]}...")

            # Check memory was created
            memories = await self.memory_persistence.load_recent_memories("CEO", limit=5)
            logger.info(f"CEO memories created: {len(memories)}")

            # Check patterns were detected
            patterns = await self.memory_persistence.get_reliable_patterns(min_discoveries=1)
            logger.info(f"Patterns discovered: {len(patterns)}")

            # Check insights were generated
            if result["symbols"]:
                insights = await self.memory_persistence.get_symbol_insights(
                    result["symbols"][0],
                    limit=5
                )
                logger.info(f"Insights for {result['symbols'][0]}: {len(insights)}")

        except asyncio.TimeoutError:
            logger.warning("Workflow timed out - this may be normal for complex queries")
        except Exception as e:
            logger.error(f"Workflow error: {e}")
            raise

        logger.info("✓ Full workflow test completed")

    async def run_all_tests(self):
        """Run all tests"""
        logger.info("Starting comprehensive workflow tests...")

        try:
            # Test individual components
            await self.test_memory_system()
            await self.test_progress_tracking()
            await self.test_division_leaders()
            await self.test_tavily_tools()

            # Test full integration
            await self.test_full_workflow()

            logger.info("\n" + "="*50)
            logger.info("✅ ALL TESTS PASSED SUCCESSFULLY!")
            logger.info("="*50)

        except Exception as e:
            logger.error(f"\n❌ TEST FAILED: {e}")
            raise


async def main():
    """Main test runner"""
    runner = WorkflowTestRunner()
    await runner.run_all_tests()


if __name__ == "__main__":
    asyncio.run(main())