"""
AI Intelligence Layer for TavilyAI Pro
Advanced multi-model orchestration, RAG, and memory systems
"""

from typing import Dict, Any, Optional
import os
import logging
from pathlib import Path

# Import all AI components
from .model_orchestrator import (
    ModelOrchestrator,
    ModelType,
    TaskType,
    TaskContext,
    ModelResponse
)

from .prompt_templates import (
    PromptTemplateEngine,
    PromptTechnique
)

from .vector_engine import (
    VectorIntelligence
)

from .rag_pipeline import (
    RAGPipeline,
    RAGContext,
    RAGResult
)

from .memory_system import (
    AdvancedMemorySystem,
    MemoryType
)

from .tool_orchestrator import (
    ToolOrchestrator
)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

__version__ = "1.0.0"
__author__ = "TavilyAI Pro Team"


class AISystem:
    """Unified AI System integrating all components."""

    def __init__(
        self,
        openai_api_key: Optional[str] = None,
        anthropic_api_key: Optional[str] = None,
        vector_persist_dir: str = "./vector_store",
        memory_persist_dir: str = "./memory_store",
        enable_cache: bool = True
    ):
        """Initialize the complete AI system."""
        # Get API keys from environment if not provided
        self.openai_api_key = openai_api_key or os.getenv("OPENAI_API_KEY")
        self.anthropic_api_key = anthropic_api_key or os.getenv("ANTHROPIC_API_KEY")

        if not self.openai_api_key:
            logger.warning("OpenAI API key not found. Some features may be limited.")
        if not self.anthropic_api_key:
            logger.warning("Anthropic API key not found. Some features may be limited.")

        # Initialize all components
        logger.info("Initializing AI System components...")

        # Model orchestration
        self.model_orchestrator = ModelOrchestrator(
            openai_api_key=self.openai_api_key,
            anthropic_api_key=self.anthropic_api_key
        )
        logger.info("✓ Model orchestrator initialized")

        # Prompt engineering
        self.prompt_engine = PromptTemplateEngine()
        logger.info("✓ Prompt template engine initialized")

        # Vector intelligence
        self.vector_engine = VectorIntelligence(
            openai_api_key=self.openai_api_key,
            persist_directory=vector_persist_dir
        )
        logger.info("✓ Vector intelligence initialized")

        # Memory system
        self.memory_system = AdvancedMemorySystem()
        logger.info("✓ Memory system initialized")

        # RAG pipeline
        self.rag_pipeline = RAGPipeline(
            vector_engine=self.vector_engine,
            model_orchestrator=self.model_orchestrator
        )
        logger.info("✓ RAG pipeline initialized")

        # Tool orchestrator
        self.tool_orchestrator = ToolOrchestrator()
        logger.info("✓ Tool orchestrator initialized")

        # System statistics
        self._stats = {
            "queries_processed": 0,
            "total_tokens": 0,
            "total_cost": 0.0,
            "cache_hits": 0,
            "cache_misses": 0
        }

        logger.info("AI System initialization complete!")

    async def process_query(
        self,
        query: str,
        task_type: TaskType = TaskType.GENERAL,
        use_rag: bool = True,
        use_memory: bool = True,
        require_citations: bool = True
    ) -> Dict[str, Any]:
        """Process a query using the full AI system."""
        try:
            # Recall relevant memories
            relevant_memories = []
            if use_memory:
                relevant_memories = self.memory_system.recall(
                    query=query,
                    max_items=5
                )

            # Build context from memories
            memory_context = "\n".join([
                f"- {mem.content}"
                for mem in relevant_memories
            ]) if relevant_memories else ""

            # Use RAG pipeline if enabled
            if use_rag:
                rag_context = RAGContext(
                    query=query,
                    max_results=10,
                    require_citations=require_citations,
                    memory_context=memory_context
                )

                rag_result = await self.rag_pipeline.process(rag_context)

                # Store important information in memory
                if use_memory and rag_result.confidence > 0.7:
                    self.memory_system.store(
                        content=rag_result.answer,
                        memory_type=MemoryType.SEMANTIC,
                        importance=rag_result.confidence,
                        metadata={
                            "query": query,
                            "sources": len(rag_result.sources)
                        }
                    )

                # Update statistics
                self._stats["queries_processed"] += 1

                return {
                    "answer": rag_result.answer,
                    "confidence": rag_result.confidence,
                    "sources": rag_result.sources,
                    "citations": rag_result.citations,
                    "metadata": rag_result.metadata,
                    "memories_used": len(relevant_memories)
                }

            else:
                # Direct model query without RAG
                context = TaskContext(
                    task_type=task_type,
                    complexity_score=0.5,
                    memory_context=memory_context
                )

                # Select optimal prompting technique
                technique = self.prompt_engine.select_optimal_technique(
                    task=query,
                    requirements={"accuracy": "high"}
                )

                # Generate enhanced prompt
                enhanced_prompt = self.prompt_engine.generate_prompt(
                    task=query,
                    technique=technique,
                    context=memory_context
                )

                # Route to optimal model
                response, metadata = await self.model_orchestrator.route_task(
                    prompt=enhanced_prompt,
                    context=context
                )

                # Store in memory if important
                if use_memory:
                    self.memory_system.store(
                        content=response.content,
                        memory_type=MemoryType.SEMANTIC,
                        importance=0.6,
                        metadata={"query": query}
                    )

                # Update statistics
                self._stats["queries_processed"] += 1
                self._stats["total_tokens"] += response.token_count
                self._stats["total_cost"] += metadata.get("cost", 0)

                return {
                    "answer": response.content,
                    "confidence": response.confidence,
                    "model_used": metadata.get("model"),
                    "technique_used": technique.value,
                    "memories_used": len(relevant_memories),
                    "metadata": metadata
                }

        except Exception as e:
            logger.error(f"Error processing query: {str(e)}")
            raise

    def get_statistics(self) -> Dict[str, Any]:
        """Get system statistics."""
        return {
            **self._stats,
            "model_stats": self.model_orchestrator.get_usage_report(),
            "memory_stats": self.memory_system.get_statistics(),
            "vector_stats": {
                "indices_loaded": len([i for i in self.vector_engine.indices.values() if i]),
                "total_documents": sum(
                    len(docs) for docs in self.vector_engine.documents.values()
                )
            }
        }

    async def optimize_performance(self) -> Dict[str, Any]:
        """Run performance optimization routines."""
        results = {}

        # Consolidate memories
        consolidated = self.memory_system.consolidate_memories()
        results["memories_consolidated"] = consolidated

        # Clean expired memories
        cleaned = self.memory_system.cleanup_expired()
        results["memories_cleaned"] = cleaned

        # Save vector indices
        if any(self.vector_engine.indices.values()):
            self.vector_engine.save_index("semantic", "semantic_index.faiss")
            results["vector_indices_saved"] = True

        return results


def initialize_ai_system(
    openai_api_key: Optional[str] = None,
    anthropic_api_key: Optional[str] = None,
    **kwargs
) -> AISystem:
    """Initialize and return a configured AI system."""
    return AISystem(
        openai_api_key=openai_api_key,
        anthropic_api_key=anthropic_api_key,
        **kwargs
    )


# Export all public classes and functions
__all__ = [
    # Model Orchestration
    'ModelOrchestrator',
    'ModelType',
    'TaskType',
    'TaskContext',
    'ModelResponse',

    # Prompt Engineering
    'PromptTemplateEngine',
    'PromptTechnique',

    # Vector Intelligence
    'VectorIntelligence',

    # RAG Pipeline
    'RAGPipeline',
    'RAGContext',
    'RAGResult',

    # Memory System
    'AdvancedMemorySystem',
    'MemoryType',

    # Tool Orchestration
    'ToolOrchestrator',

    # Unified System
    'AISystem',
    'initialize_ai_system'
]

# Module-level initialization message
logger.info(f"AI Enhancement Module v{__version__} loaded")