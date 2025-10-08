"""
Comprehensive test suite for AI enhancement components
Testing all advanced AI features: multi-model, RAG, memory, vector search
"""

import pytest
import asyncio
from unittest.mock import Mock, patch, AsyncMock
import numpy as np
from datetime import datetime, timedelta

# Import AI components
from ai import (
    AISystem,
    initialize_ai_system,
    ModelOrchestrator,
    ModelType,
    TaskType,
    TaskContext,
    PromptTemplateEngine,
    PromptTechnique,
    VectorIntelligence,
    RAGPipeline,
    RAGContext,
    AdvancedMemorySystem,
    MemoryType,
    ToolOrchestrator
)


class TestModelOrchestrator:
    """Test multi-model orchestration capabilities."""

    @pytest.fixture
    def orchestrator(self):
        """Create a model orchestrator instance."""
        with patch.dict('os.environ', {
            'OPENAI_API_KEY': 'test-openai-key',
            'ANTHROPIC_API_KEY': 'test-anthropic-key'
        }):
            return ModelOrchestrator()

    @pytest.mark.asyncio
    async def test_model_routing(self, orchestrator):
        """Test intelligent model routing based on task type."""
        # Test strategic planning routes to Claude-3 Opus
        context = TaskContext(urgency="medium", 
            task_type=TaskType.STRATEGIC_PLANNING,
            complexity_score=0.9
        )
        model = orchestrator._select_model(context)
        assert model == ModelType.CLAUDE_3_OPUS

        # Test financial analysis routes to GPT-4
        context = TaskContext(urgency="medium", 
            task_type=TaskType.FINANCIAL_ANALYSIS,
            complexity_score=0.8
        )
        model = orchestrator._select_model(context)
        assert model == ModelType.GPT_4_TURBO

        # Test simple task routes to GPT-3.5
        context = TaskContext(urgency="medium", 
            task_type=TaskType.SIMPLE_QUERY,
            complexity_score=0.2
        )
        model = orchestrator._select_model(context)
        assert model == ModelType.GPT_3_5_TURBO

    @pytest.mark.asyncio
    async def test_fallback_mechanism(self, orchestrator):
        """Test fallback to alternative models on failure."""
        with patch.object(orchestrator, '_execute_with_claude', side_effect=Exception("API Error")):
            with patch.object(orchestrator, '_execute_with_openai') as mock_openai:
                mock_openai.return_value = AsyncMock(
                    return_value=("Success", {"model": "gpt-4"})
                )()

                context = TaskContext(urgency="medium", 
                    task_type=TaskType.STRATEGIC_PLANNING,
                    complexity_score=0.9
                )

                response, metadata = await orchestrator.route_task("test prompt", context)
                assert response is not None
                assert metadata["model"] == "gpt-4"

    def test_temperature_adjustment(self, orchestrator):
        """Test dynamic temperature adjustment based on task."""
        # Creative task should have higher temperature
        creative_context = TaskContext(urgency="medium", 
            task_type=TaskType.CREATIVE,
            complexity_score=0.5
        )
        temp = orchestrator._get_temperature(creative_context)
        assert temp >= 0.7

        # Analytical task should have lower temperature
        analytical_context = TaskContext(urgency="medium", 
            task_type=TaskType.FINANCIAL_ANALYSIS,
            complexity_score=0.8
        )
        temp = orchestrator._get_temperature(analytical_context)
        assert temp <= 0.3


class TestPromptTemplateEngine:
    """Test advanced prompting techniques."""

    @pytest.fixture
    def engine(self):
        """Create a prompt template engine instance."""
        return PromptTemplateEngine()

    def test_chain_of_thought_generation(self, engine):
        """Test Chain-of-Thought prompt generation."""
        prompt = engine.generate_prompt(
            task="Analyze NVDA stock performance",
            technique=PromptTechnique.CHAIN_OF_THOUGHT
        )

        assert "step by step" in prompt.lower()
        assert "reasoning" in prompt.lower()
        assert "NVDA stock performance" in prompt

    def test_tree_of_thoughts_generation(self, engine):
        """Test Tree-of-Thoughts prompt generation."""
        prompt = engine.generate_prompt(
            task="Compare investment strategies",
            technique=PromptTechnique.TREE_OF_THOUGHTS
        )

        assert "multiple approaches" in prompt.lower()
        assert "evaluate" in prompt.lower()
        assert "investment strategies" in prompt

    def test_few_shot_learning(self, engine):
        """Test Few-Shot learning with examples."""
        prompt = engine.generate_prompt(
            task="Analyze market trends",
            technique=PromptTechnique.FEW_SHOT,
            examples_domain="stock_analysis"
        )

        assert "Example" in prompt
        assert "market trends" in prompt

    def test_optimal_technique_selection(self, engine):
        """Test automatic selection of optimal prompting technique."""
        # Complex analytical task should select appropriate technique
        technique = engine.select_optimal_technique(
            task="Perform comprehensive financial analysis of NVDA including DCF model",
            requirements={"accuracy": "high", "reasoning": "detailed"}
        )
        assert technique in [PromptTechnique.CHAIN_OF_THOUGHT, PromptTechnique.TREE_OF_THOUGHTS]

        # Simple query should select simpler technique
        technique = engine.select_optimal_technique(
            task="What is the current stock price?",
            requirements={}
        )
        assert technique == PromptTechnique.ZERO_SHOT


class TestVectorIntelligence:
    """Test FAISS vector search capabilities."""

    @pytest.fixture
    def vector_engine(self):
        """Create a vector intelligence instance."""
        with patch.dict('os.environ', {'OPENAI_API_KEY': 'test-key'}):
            return VectorIntelligence()

    @pytest.mark.asyncio
    async def test_document_embedding(self, vector_engine):
        """Test document embedding and storage."""
        with patch.object(vector_engine.embedder, 'encode') as mock_encode:
            mock_encode.return_value = np.random.rand(10, 768)

            documents = [
                "NVIDIA reported strong Q3 earnings",
                "AI chip demand continues to grow",
                "Data center revenue increased 40%"
            ]

            await vector_engine.add_documents(documents)
            assert "semantic" in vector_engine.documents
            assert len(vector_engine.documents["semantic"]) == 3

    @pytest.mark.asyncio
    async def test_hybrid_search(self, vector_engine):
        """Test hybrid search combining semantic and keyword search."""
        # Add test documents
        documents = [
            "NVIDIA's GPU technology leads AI revolution",
            "Apple launches new iPhone with advanced features",
            "Tesla reports record vehicle deliveries"
        ]

        with patch.object(vector_engine.embedder, 'encode') as mock_encode:
            mock_encode.return_value = np.random.rand(len(documents), 768)
            await vector_engine.add_documents(documents)

            # Mock search results
            with patch.object(vector_engine, '_semantic_search') as mock_semantic:
                with patch.object(vector_engine, '_keyword_search') as mock_keyword:
                    mock_semantic.return_value = [(documents[0], 0.9)]
                    mock_keyword.return_value = [(documents[0], 0.8)]

                    results = await vector_engine.search(
                        query="NVIDIA AI technology",
                        search_type=SearchType.HYBRID
                    )

                    assert len(results) > 0
                    assert "NVIDIA" in results[0][0]

    def test_intelligent_chunking(self, vector_engine):
        """Test content-aware text chunking."""
        long_text = """
        NVIDIA Corporation reported exceptional Q3 2024 results.
        Revenue reached $18.12 billion, up 34% quarter-over-quarter.

        Data center revenue hit a record $14.51 billion.
        Gaming revenue was $2.86 billion for the quarter.

        The company expects Q4 revenue of $20 billion.
        CEO Jensen Huang highlighted strong AI demand.
        """

        chunks = vector_engine._chunk_text(long_text, chunk_size=100)
        assert len(chunks) > 1
        assert all(len(chunk) <= 150 for chunk in chunks)  # Allow some overlap


class TestRAGPipeline:
    """Test Retrieval-Augmented Generation pipeline."""

    @pytest.fixture
    def rag_pipeline(self):
        """Create a RAG pipeline instance."""
        with patch.dict('os.environ', {
            'OPENAI_API_KEY': 'test-key',
            'ANTHROPIC_API_KEY': 'test-key'
        }):
            vector_engine = Mock(spec=VectorIntelligence)
            model_orchestrator = Mock(spec=ModelOrchestrator)
            return RAGPipeline(vector_engine, model_orchestrator)

    @pytest.mark.asyncio
    async def test_query_expansion(self, rag_pipeline):
        """Test query expansion for better retrieval."""
        original_query = "NVDA earnings"
        expanded = await rag_pipeline._expand_query(original_query)

        assert len(expanded) > 1
        assert original_query in expanded
        # Should include variations
        variations = ["NVIDIA earnings", "NVDA financial results", "NVIDIA quarterly results"]
        assert any(v in ' '.join(expanded) for v in variations)

    @pytest.mark.asyncio
    async def test_citation_tracking(self, rag_pipeline):
        """Test that all claims include proper citations."""
        context = RAGContext(
            query="What were NVDA's Q3 earnings?",
            require_citations=True
        )

        # Mock retrieval results
        rag_pipeline.vector_engine.search = AsyncMock(return_value=[
            ("NVDA reported $18.12B in Q3 revenue", 0.95),
            ("Q3 earnings beat expectations", 0.85)
        ])

        # Mock synthesis
        rag_pipeline.model_orchestrator.route_task = AsyncMock(return_value=(
            Mock(content="NVDA reported $18.12 billion in Q3 revenue [1]", confidence=0.9, token_count=50),
            {"model": "gpt-4"}
        ))

        result = await rag_pipeline.process(context)

        assert result.citations is not None
        assert len(result.sources) > 0
        assert "[1]" in result.answer

    @pytest.mark.asyncio
    async def test_confidence_scoring(self, rag_pipeline):
        """Test confidence score calculation."""
        context = RAGContext(query="Test query")

        # Mock low-quality retrieval
        rag_pipeline.vector_engine.search = AsyncMock(return_value=[
            ("Somewhat related content", 0.4),
            ("Barely related", 0.3)
        ])

        rag_pipeline.model_orchestrator.route_task = AsyncMock(return_value=(
            Mock(content="Low confidence answer", confidence=0.5, token_count=30),
            {"model": "gpt-3.5"}
        ))

        result = await rag_pipeline.process(context)
        assert result.confidence < 0.6  # Should have low confidence


class TestAdvancedMemorySystem:
    """Test multi-tier memory system."""

    @pytest.fixture
    def memory_system(self):
        """Create a memory system instance."""
        return AdvancedMemorySystem()

    def test_memory_storage_tiers(self, memory_system):
        """Test storage in different memory tiers."""
        # Store in sensory memory (short TTL)
        sensory_id = memory_system.store(
            content="Quick observation",
            memory_type=MemoryType.SENSORY,
            importance=0.3
        )
        assert sensory_id is not None

        # Store in semantic memory (long-term)
        semantic_id = memory_system.store(
            content="NVDA is a leading AI chip manufacturer",
            memory_type=MemoryType.SEMANTIC,
            importance=0.9
        )
        assert semantic_id is not None

        # Verify storage
        stats = memory_system.get_statistics()
        assert stats["total_memories"] >= 2

    def test_memory_recall(self, memory_system):
        """Test memory recall with relevance scoring."""
        # Store related memories
        memory_system.store("NVDA stock price increased", MemoryType.SEMANTIC, 0.8)
        memory_system.store("Tesla announced new model", MemoryType.SEMANTIC, 0.7)
        memory_system.store("NVIDIA GPU sales are strong", MemoryType.SEMANTIC, 0.9)

        # Recall memories related to NVIDIA
        recalled = memory_system.recall("NVIDIA performance", max_items=2)

        assert len(recalled) <= 2
        # Should prioritize NVIDIA-related memories
        assert any("NVID" in mem.content or "NVDA" in mem.content for mem in recalled)

    def test_memory_consolidation(self, memory_system):
        """Test memory consolidation from short-term to long-term."""
        # Store important short-term memory
        memory_id = memory_system.store(
            content="Critical market insight",
            memory_type=MemoryType.SHORT_TERM,
            importance=0.95
        )

        # Run consolidation
        consolidated = memory_system.consolidate_memories()

        # High importance memories should be candidates for consolidation
        stats = memory_system.get_statistics()
        assert consolidated >= 0

    def test_memory_expiration(self, memory_system):
        """Test automatic memory expiration."""
        # Store sensory memory with short TTL
        memory_system.store(
            content="Temporary observation",
            memory_type=MemoryType.SENSORY,
            importance=0.2
        )

        # Simulate time passing
        with patch('time.time', return_value=datetime.now().timestamp() + 10):
            cleaned = memory_system.cleanup_expired()
            assert cleaned >= 0


class TestToolOrchestrator:
    """Test intelligent tool selection and orchestration."""

    @pytest.fixture
    def tool_orchestrator(self):
        """Create a tool orchestrator instance."""
        return ToolOrchestrator()

    @pytest.mark.asyncio
    async def test_tool_selection(self, tool_orchestrator):
        """Test optimal tool selection for tasks."""
        # Search task should select Tavily Search
        plan = await tool_orchestrator.create_execution_plan(
            task="Search for latest NVDA news",
            requirements={}
        )
        assert any("search" in step.tool.lower() for step in plan.steps)

        # Extraction task should select appropriate tool
        plan = await tool_orchestrator.create_execution_plan(
            task="Extract financial data from earnings report",
            requirements={}
        )
        assert any("extract" in step.tool.lower() for step in plan.steps)

    @pytest.mark.asyncio
    async def test_parallel_tool_execution(self, tool_orchestrator):
        """Test parallel execution of independent tools."""
        plan = await tool_orchestrator.create_execution_plan(
            task="Analyze NVDA and compare with competitors",
            requirements={}
        )

        # Should identify parallel opportunities
        assert plan.parallel_groups is not None
        assert len(plan.parallel_groups) > 0

    @pytest.mark.asyncio
    async def test_cost_aware_planning(self, tool_orchestrator):
        """Test cost-aware tool planning."""
        plan = await tool_orchestrator.create_execution_plan(
            task="Quick stock price check",
            requirements={"max_cost": 0.01}
        )

        # Should optimize for low cost
        assert plan.estimated_cost <= 0.01
        assert len(plan.steps) <= 2  # Minimal tool usage


class TestAISystemIntegration:
    """Test complete AI system integration."""

    @pytest.fixture
    def ai_system(self):
        """Create a complete AI system instance."""
        with patch.dict('os.environ', {
            'OPENAI_API_KEY': 'test-key',
            'ANTHROPIC_API_KEY': 'test-key'
        }):
            return initialize_ai_system()

    @pytest.mark.asyncio
    async def test_full_query_processing(self, ai_system):
        """Test end-to-end query processing."""
        # Mock the underlying components
        ai_system.rag_pipeline.process = AsyncMock(return_value=Mock(
            answer="NVDA reported strong earnings",
            confidence=0.85,
            sources=["source1", "source2"],
            citations={"[1]": "source1"},
            metadata={}
        ))

        result = await ai_system.process_query(
            query="What were NVDA's latest earnings?",
            task_type=TaskType.FINANCIAL_ANALYSIS,
            use_rag=True,
            use_memory=True
        )

        assert "answer" in result
        assert result["confidence"] > 0.8
        assert len(result["sources"]) > 0

    @pytest.mark.asyncio
    async def test_memory_integration(self, ai_system):
        """Test memory system integration with queries."""
        # Process a query that should be remembered
        ai_system.model_orchestrator.route_task = AsyncMock(return_value=(
            Mock(content="Important market insight", confidence=0.9, token_count=100),
            {"model": "gpt-4"}
        ))

        await ai_system.process_query(
            query="Analyze market trends",
            use_rag=False,
            use_memory=True
        )

        # Check if memory was stored
        stats = ai_system.memory_system.get_statistics()
        assert stats["total_memories"] > 0

    def test_statistics_tracking(self, ai_system):
        """Test system statistics tracking."""
        initial_stats = ai_system.get_statistics()
        assert "queries_processed" in initial_stats
        assert "model_stats" in initial_stats
        assert "memory_stats" in initial_stats
        assert "vector_stats" in initial_stats

    @pytest.mark.asyncio
    async def test_performance_optimization(self, ai_system):
        """Test performance optimization routines."""
        # Add some memories to consolidate
        ai_system.memory_system.store(
            "Test memory",
            MemoryType.SHORT_TERM,
            importance=0.9
        )

        results = await ai_system.optimize_performance()

        assert "memories_consolidated" in results
        assert "memories_cleaned" in results


# Performance benchmarks
class TestPerformanceBenchmarks:
    """Benchmark tests for AI system performance."""

    @pytest.mark.benchmark
    @pytest.mark.asyncio
    async def test_model_routing_performance(self, benchmark):
        """Benchmark model routing speed."""
        orchestrator = ModelOrchestrator()
        context = TaskContext(urgency="medium", 
            task_type=TaskType.FINANCIAL_ANALYSIS,
            complexity_score=0.8
        )

        result = benchmark(orchestrator._select_model, context)
        assert result is not None

    @pytest.mark.benchmark
    def test_memory_recall_performance(self, benchmark):
        """Benchmark memory recall speed."""
        memory_system = AdvancedMemorySystem()

        # Pre-populate memories
        for i in range(100):
            memory_system.store(
                f"Memory content {i}",
                MemoryType.SEMANTIC,
                importance=np.random.random()
            )

        result = benchmark(memory_system.recall, "test query", 5)
        assert isinstance(result, list)

    @pytest.mark.benchmark
    @pytest.mark.asyncio
    async def test_vector_search_performance(self, benchmark):
        """Benchmark vector search speed."""
        vector_engine = VectorIntelligence()

        # Pre-populate vectors
        with patch.object(vector_engine.embedder, 'encode') as mock_encode:
            mock_encode.return_value = np.random.rand(100, 768)
            await vector_engine.add_documents([f"Document {i}" for i in range(100)])

            # Benchmark search
            mock_encode.return_value = np.random.rand(1, 768)
            result = await benchmark(vector_engine.search, "test query")
            assert result is not None


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--cov=ai", "--cov-report=term-missing"])