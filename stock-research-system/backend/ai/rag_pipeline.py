"""
RAG (Retrieval-Augmented Generation) Pipeline for TavilyAI Pro
Implements advanced retrieval, reranking, and citation tracking
"""

import asyncio
import logging
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass
from datetime import datetime
import re

from .vector_engine import VectorIntelligence, SearchResult
from .model_orchestrator import ModelOrchestrator, TaskType, TaskContext

logger = logging.getLogger(__name__)


@dataclass
class RAGContext:
    """Context for RAG pipeline execution"""
    query: str
    max_context_length: int = 4000
    num_documents: int = 5
    require_citations: bool = True
    search_type: str = "hybrid"
    confidence_threshold: float = 0.7


@dataclass
class RAGResult:
    """Result from RAG pipeline"""
    answer: str
    citations: List[Dict[str, Any]]
    confidence_score: float
    context_used: str
    search_results: List[SearchResult]
    metadata: Dict[str, Any]


class RAGPipeline:
    """
    Advanced RAG pipeline with query expansion, hybrid search,
    reranking, and citation tracking
    """

    def __init__(self,
                 vector_engine: VectorIntelligence,
                 model_orchestrator: ModelOrchestrator):

        self.vector_engine = vector_engine
        self.model_orchestrator = model_orchestrator

        # Pipeline statistics
        self.stats = {
            "queries_processed": 0,
            "avg_confidence": 0.0,
            "total_citations": 0
        }

    async def process(self, context: RAGContext) -> RAGResult:
        """
        Execute the full RAG pipeline

        Args:
            context: RAG execution context

        Returns:
            RAGResult with answer and citations
        """
        self.stats["queries_processed"] += 1

        # Step 1: Query expansion
        expanded_queries = await self._expand_query(context.query)
        logger.info(f"Expanded query to {len(expanded_queries)} variants")

        # Step 2: Retrieve relevant documents
        all_results = []
        for query_variant in expanded_queries:
            results = await self.vector_engine.search(
                query=query_variant,
                top_k=context.num_documents * 2,  # Get extra for filtering
                search_type=context.search_type,
                rerank=True
            )
            all_results.extend(results)

        # Step 3: Deduplicate and filter results
        unique_results = self._deduplicate_and_filter(all_results, context.confidence_threshold)

        # Step 4: Build context from results
        context_text, citation_map = self._build_context(
            unique_results,
            context.max_context_length
        )

        # Step 5: Generate answer with citations
        answer, metadata = await self._generate_answer_with_citations(
            context.query,
            context_text,
            citation_map,
            context.require_citations
        )

        # Step 6: Extract citations from answer
        citations = self._extract_citations(answer, citation_map)

        # Step 7: Calculate confidence
        confidence = self._calculate_confidence(unique_results, metadata)

        # Update statistics
        self.stats["total_citations"] += len(citations)
        self.stats["avg_confidence"] = (
            (self.stats["avg_confidence"] * (self.stats["queries_processed"] - 1) + confidence)
            / self.stats["queries_processed"]
        )

        return RAGResult(
            answer=answer,
            citations=citations,
            confidence_score=confidence,
            context_used=context_text,
            search_results=unique_results[:context.num_documents],
            metadata={
                "expanded_queries": expanded_queries,
                "total_results_found": len(all_results),
                "unique_results": len(unique_results),
                "model_metadata": metadata
            }
        )

    async def _expand_query(self, query: str) -> List[str]:
        """
        Expand query into multiple variants for better recall

        Args:
            query: Original query

        Returns:
            List of query variants
        """
        # Generate query variants using LLM
        expansion_prompt = f"""Generate 3 alternative phrasings of this query for better search coverage:

Original Query: {query}

Provide 3 variants that:
1. Use different keywords but same meaning
2. Add relevant context or related terms
3. Rephrase from different perspectives

Format as a numbered list."""

        context = TaskContext(
            task_type=TaskType.SIMPLE_TASK,
            complexity_score=0.3,
            urgency="medium"
        )

        response, _ = await self.model_orchestrator.route_task(
            expansion_prompt,
            context
        )

        # Parse response to extract variants
        variants = [query]  # Always include original
        lines = response.strip().split('\n')

        for line in lines:
            # Extract numbered items
            match = re.match(r'^\d+\.\s*(.+)$', line.strip())
            if match:
                variants.append(match.group(1))

        return variants[:4]  # Limit to 4 total (original + 3)

    def _deduplicate_and_filter(self,
                                results: List[SearchResult],
                                confidence_threshold: float) -> List[SearchResult]:
        """
        Deduplicate and filter search results

        Args:
            results: All search results
            confidence_threshold: Minimum confidence score

        Returns:
            Filtered and deduplicated results
        """
        # Filter by confidence
        filtered = [r for r in results if r.score >= confidence_threshold]

        # Deduplicate based on content similarity
        unique = []
        seen_content = set()

        for result in filtered:
            # Create content signature
            content_sig = result.document.content[:100].lower().strip()

            if content_sig not in seen_content:
                seen_content.add(content_sig)
                unique.append(result)

        # Sort by score
        return sorted(unique, key=lambda x: x.score, reverse=True)

    def _build_context(self,
                      results: List[SearchResult],
                      max_length: int) -> Tuple[str, Dict[int, SearchResult]]:
        """
        Build context from search results

        Args:
            results: Search results
            max_length: Maximum context length

        Returns:
            (context_text, citation_map)
        """
        context_parts = []
        citation_map = {}
        current_length = 0
        citation_id = 1

        for result in results:
            content = result.document.content
            metadata = result.document.metadata

            # Calculate space needed
            citation_marker = f"[{citation_id}]"
            source_info = f" (Source: {metadata.get('source', 'Unknown')})"
            content_with_citation = f"{citation_marker} {content}{source_info}"

            # Check if we have space
            if current_length + len(content_with_citation) > max_length:
                # Try to fit partial content
                remaining = max_length - current_length - len(citation_marker) - len(source_info)
                if remaining > 100:  # Only include if we have reasonable space
                    truncated = content[:remaining] + "..."
                    content_with_citation = f"{citation_marker} {truncated}{source_info}"
                    context_parts.append(content_with_citation)
                    citation_map[citation_id] = result
                break

            context_parts.append(content_with_citation)
            citation_map[citation_id] = result
            current_length += len(content_with_citation)
            citation_id += 1

        return "\n\n".join(context_parts), citation_map

    async def _generate_answer_with_citations(self,
                                             query: str,
                                             context: str,
                                             citation_map: Dict[int, SearchResult],
                                             require_citations: bool) -> Tuple[str, Dict]:
        """
        Generate answer using context with citations

        Args:
            query: Original query
            context: Retrieved context
            citation_map: Mapping of citation IDs to sources
            require_citations: Whether to require citations

        Returns:
            (answer, metadata)
        """
        # Build prompt with citation instructions
        citation_instruction = ""
        if require_citations:
            citation_instruction = """
IMPORTANT: You must cite sources using [1], [2], etc. format when using information from the context.
Place citations immediately after the relevant statement.
Example: "The company reported 50% growth [1]."
"""

        prompt = f"""Answer the following question using the provided context.

{citation_instruction}

Context:
{context}

Question: {query}

Provide a comprehensive answer based on the context. If the context doesn't contain sufficient information, acknowledge the limitations.

Answer:"""

        # Route to appropriate model
        task_context = TaskContext(
            task_type=TaskType.WEB_SYNTHESIS,
            complexity_score=0.7,
            urgency="medium",
            require_citations=require_citations,
            require_confidence=True
        )

        answer, metadata = await self.model_orchestrator.route_task(
            prompt,
            task_context
        )

        return answer, metadata

    def _extract_citations(self,
                          answer: str,
                          citation_map: Dict[int, SearchResult]) -> List[Dict[str, Any]]:
        """
        Extract citations from answer text

        Args:
            answer: Answer text with citation markers
            citation_map: Mapping of citation IDs to sources

        Returns:
            List of citation information
        """
        citations = []
        cited_ids = set()

        # Find all citation markers in answer
        citation_pattern = r'\[(\d+)\]'
        matches = re.findall(citation_pattern, answer)

        for match in matches:
            citation_id = int(match)
            if citation_id in citation_map and citation_id not in cited_ids:
                cited_ids.add(citation_id)
                result = citation_map[citation_id]

                citations.append({
                    "id": citation_id,
                    "content": result.document.content[:200] + "...",
                    "source": result.document.metadata.get("source", "Unknown"),
                    "url": result.document.metadata.get("url", ""),
                    "score": result.score,
                    "metadata": result.document.metadata
                })

        return citations

    def _calculate_confidence(self,
                             search_results: List[SearchResult],
                             model_metadata: Dict) -> float:
        """
        Calculate overall confidence score

        Args:
            search_results: Search results used
            model_metadata: Metadata from model

        Returns:
            Confidence score (0.0 to 1.0)
        """
        # Factors for confidence calculation
        factors = []

        # 1. Search result quality
        if search_results:
            avg_search_score = sum(r.score for r in search_results) / len(search_results)
            factors.append(avg_search_score)

        # 2. Model confidence
        model_confidence = model_metadata.get("confidence", 0.75)
        factors.append(model_confidence)

        # 3. Number of relevant documents found
        doc_coverage = min(len(search_results) / 5, 1.0)  # Normalize to max 5 docs
        factors.append(doc_coverage)

        # Calculate weighted average
        if factors:
            confidence = sum(factors) / len(factors)
        else:
            confidence = 0.5

        return min(max(confidence, 0.0), 1.0)

    async def process_with_feedback(self,
                                   context: RAGContext,
                                   max_iterations: int = 2) -> RAGResult:
        """
        Process with iterative refinement based on confidence

        Args:
            context: RAG context
            max_iterations: Maximum refinement iterations

        Returns:
            Refined RAGResult
        """
        best_result = None
        best_confidence = 0.0

        for iteration in range(max_iterations):
            logger.info(f"RAG iteration {iteration + 1}/{max_iterations}")

            # Process query
            result = await self.process(context)

            # Check if this is the best result so far
            if result.confidence_score > best_confidence:
                best_result = result
                best_confidence = result.confidence_score

            # Check if confidence is sufficient
            if result.confidence_score >= 0.85:
                logger.info(f"Achieved confidence {result.confidence_score:.2f}, stopping")
                break

            # Refine query for next iteration
            if iteration < max_iterations - 1:
                context.query = await self._refine_query_based_on_feedback(
                    context.query,
                    result
                )

        return best_result

    async def _refine_query_based_on_feedback(self,
                                             original_query: str,
                                             result: RAGResult) -> str:
        """
        Refine query based on previous result

        Args:
            original_query: Original query
            result: Previous result

        Returns:
            Refined query
        """
        # Analyze what's missing
        refinement_prompt = f"""The following query didn't get a fully confident answer:

Query: {original_query}
Confidence: {result.confidence_score:.2f}
Answer preview: {result.answer[:200]}...

Generate a refined version of the query that might get better results.
Focus on being more specific or adding clarifying context.

Refined query:"""

        context = TaskContext(
            task_type=TaskType.SIMPLE_TASK,
            complexity_score=0.4,
            urgency="medium"
        )

        refined_query, _ = await self.model_orchestrator.route_task(
            refinement_prompt,
            context
        )

        return refined_query.strip()

    def get_statistics(self) -> Dict[str, Any]:
        """Get RAG pipeline statistics"""
        return {
            **self.stats,
            "vector_store_stats": self.vector_engine.get_statistics(),
            "model_stats": self.model_orchestrator.get_usage_report()
        }

    async def add_feedback(self,
                          query: str,
                          answer: str,
                          rating: float,
                          feedback: Optional[str] = None):
        """
        Add user feedback for continuous improvement

        Args:
            query: Original query
            answer: Generated answer
            rating: User rating (0.0 to 1.0)
            feedback: Optional text feedback
        """
        # Store feedback for analysis (implement storage as needed)
        logger.info(f"Feedback received - Query: {query[:50]}..., Rating: {rating}")

        # Could implement learning from feedback here
        # For example, adjusting retrieval parameters or prompt templates
        pass