"""
Memory Consolidation Service
Periodically consolidates, compresses, and extracts patterns from agent memories
"""

from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
import asyncio
import logging
from collections import Counter, defaultdict
import numpy as np
from sklearn.cluster import DBSCAN
from sentence_transformers import SentenceTransformer

from memory.agent_memory import AgentMemorySystem, SharedMemory, MemoryEntry
from memory.memory_persistence import MemoryPersistenceService

logger = logging.getLogger(__name__)


class MemoryConsolidationService:
    """Service for consolidating and extracting patterns from memories"""

    def __init__(
        self,
        persistence: MemoryPersistenceService,
        shared_memory: SharedMemory,
        embedding_model: str = "all-MiniLM-L6-v2"
    ):
        self.persistence = persistence
        self.shared_memory = shared_memory
        self.encoder = SentenceTransformer(embedding_model)
        self.consolidation_interval = 3600  # 1 hour
        self.is_running = False

    async def start(self):
        """Start the consolidation service"""
        if self.is_running:
            logger.warning("Consolidation service already running")
            return

        self.is_running = True
        logger.info("Starting memory consolidation service")

        while self.is_running:
            try:
                await self._consolidation_cycle()
                await asyncio.sleep(self.consolidation_interval)
            except Exception as e:
                logger.error(f"Consolidation cycle error: {e}")
                await asyncio.sleep(60)  # Wait before retry

    async def stop(self):
        """Stop the consolidation service"""
        self.is_running = False
        logger.info("Stopping memory consolidation service")

    async def _consolidation_cycle(self):
        """Run one consolidation cycle"""
        logger.info("Starting memory consolidation cycle")

        # 1. Extract patterns from recent memories
        await self._extract_patterns()

        # 2. Consolidate similar memories
        await self._consolidate_similar_memories()

        # 3. Update agent performance metrics
        await self._update_performance_metrics()

        # 4. Clean up old memories
        await self._cleanup_old_memories()

        # 5. Generate insights
        await self._generate_insights()

        logger.info("Consolidation cycle completed")

    async def _extract_patterns(self):
        """Extract patterns from recent memories"""
        try:
            # Get recent decisions and outcomes
            learning_data = await self._get_recent_learning_data()

            # Analyze for patterns
            patterns = self._analyze_patterns(learning_data)

            # Save discovered patterns
            for pattern in patterns:
                await self.persistence.save_pattern(pattern)

            logger.info(f"Extracted {len(patterns)} patterns")

        except Exception as e:
            logger.error(f"Pattern extraction error: {e}")

    async def _consolidate_similar_memories(self):
        """Consolidate similar memories to reduce redundancy"""
        try:
            # Get all recent memories
            memories = await self.persistence.load_recent_memories(
                agent_name=None,  # All agents
                limit=1000
            )

            if len(memories) < 10:
                return

            # Extract embeddings
            embeddings = []
            valid_memories = []

            for memory in memories:
                if memory.embedding:
                    embeddings.append(memory.embedding)
                    valid_memories.append(memory)

            if len(embeddings) < 10:
                return

            # Cluster similar memories
            embeddings_array = np.array(embeddings)
            clustering = DBSCAN(eps=0.3, min_samples=3, metric='cosine')
            labels = clustering.fit_predict(embeddings_array)

            # Consolidate clusters
            clusters = defaultdict(list)
            for idx, label in enumerate(labels):
                if label != -1:  # Not noise
                    clusters[label].append(valid_memories[idx])

            # Create consolidated memories for each cluster
            for cluster_id, cluster_memories in clusters.items():
                await self._create_consolidated_memory(cluster_memories)

            logger.info(f"Consolidated {len(clusters)} memory clusters")

        except Exception as e:
            logger.error(f"Memory consolidation error: {e}")

    async def _create_consolidated_memory(self, memories: List[MemoryEntry]):
        """Create a single consolidated memory from a cluster"""
        if not memories:
            return

        # Find most important memory in cluster
        most_important = max(memories, key=lambda m: m.importance_score)

        # Aggregate information
        all_contexts = [m.context for m in memories]
        all_agents = list(set(m.agent_name for m in memories))

        # Create consolidated memory
        consolidated = MemoryEntry(
            content=f"Consolidated: {most_important.content}",
            context={
                'original_count': len(memories),
                'agents_involved': all_agents,
                'consolidated_contexts': all_contexts[:3],  # Keep top 3
                'consolidation_date': datetime.utcnow().isoformat()
            },
            timestamp=datetime.utcnow(),
            agent_name="System",
            memory_type="consolidated",
            importance_score=min(most_important.importance_score * 1.2, 1.0),
            embedding=most_important.embedding
        )

        # Save consolidated memory
        await self.persistence.save_memory(consolidated, "System")

        # Mark originals for cleanup (lower importance)
        for memory in memories:
            memory.importance_score *= 0.7

    async def _update_performance_metrics(self):
        """Update performance metrics for all agents"""
        try:
            # Get list of active agents
            agents = await self._get_active_agents()

            for agent in agents:
                performance = await self.persistence.get_agent_performance(
                    agent,
                    days_back=7
                )

                # Store performance in shared memory
                self.shared_memory.add_insight(
                    "_performance",
                    {
                        'agent': agent,
                        'metrics': performance,
                        'timestamp': datetime.utcnow().isoformat()
                    }
                )

                # If performance is declining, flag for attention
                if performance.get('success_rate', 0) < 0.5:
                    logger.warning(f"Agent {agent} performance below threshold: {performance['success_rate']}")

        except Exception as e:
            logger.error(f"Performance update error: {e}")

    async def _cleanup_old_memories(self):
        """Clean up old, unimportant memories"""
        try:
            await self.persistence.cleanup_old_memories(
                days=30,
                importance_threshold=0.3
            )
        except Exception as e:
            logger.error(f"Cleanup error: {e}")

    async def _generate_insights(self):
        """Generate high-level insights from memories"""
        try:
            # Get recent patterns
            patterns = await self.persistence.get_reliable_patterns()

            # Analyze for meta-patterns
            insights = []

            # Market behavior patterns
            market_patterns = [p for p in patterns if p.get('type') == 'market_behavior']
            if market_patterns:
                insight = {
                    'type': 'market_insight',
                    'content': f"Identified {len(market_patterns)} recurring market patterns",
                    'patterns': market_patterns[:3],
                    'confidence': 0.7
                }
                insights.append(insight)

            # Agent collaboration patterns
            failure_patterns = [p for p in patterns if p.get('type') == 'recurring_failure']
            if failure_patterns:
                insight = {
                    'type': 'process_improvement',
                    'content': f"Found {len(failure_patterns)} areas for improvement",
                    'patterns': failure_patterns[:3],
                    'confidence': 0.8
                }
                insights.append(insight)

            # Save insights
            for insight in insights:
                await self.persistence.save_insight(
                    "_system",
                    insight,
                    "ConsolidationService"
                )

            logger.info(f"Generated {len(insights)} insights")

        except Exception as e:
            logger.error(f"Insight generation error: {e}")

    async def _get_recent_learning_data(self) -> List[Dict[str, Any]]:
        """Get recent learning data from all agents"""
        # In production, query from MongoDB
        return []

    def _analyze_patterns(self, learning_data: List[Dict]) -> List[Dict]:
        """Analyze learning data for patterns"""
        patterns = []

        if not learning_data:
            return patterns

        # Group by decision type
        decision_groups = defaultdict(list)
        for entry in learning_data:
            decision_type = self._classify_decision(entry['decision'])
            decision_groups[decision_type].append(entry)

        # Analyze each group
        for decision_type, entries in decision_groups.items():
            success_rate = sum(1 for e in entries if e['success']) / len(entries)

            if len(entries) >= 5:  # Minimum sample size
                if success_rate > 0.8:
                    patterns.append({
                        'type': 'successful_strategy',
                        'condition': decision_type,
                        'success_rate': success_rate,
                        'sample_size': len(entries),
                        'confidence': min(success_rate, 0.9),
                        'description': f"Strategy '{decision_type}' succeeds {success_rate:.0%} of the time"
                    })
                elif success_rate < 0.3:
                    patterns.append({
                        'type': 'failure_pattern',
                        'condition': decision_type,
                        'success_rate': success_rate,
                        'sample_size': len(entries),
                        'confidence': 0.8,
                        'description': f"Strategy '{decision_type}' fails {(1-success_rate):.0%} of the time"
                    })

        return patterns

    def _classify_decision(self, decision: str) -> str:
        """Classify decision into categories"""
        decision_lower = decision.lower()

        if 'buy' in decision_lower or 'long' in decision_lower:
            return 'bullish_position'
        elif 'sell' in decision_lower or 'short' in decision_lower:
            return 'bearish_position'
        elif 'hold' in decision_lower or 'wait' in decision_lower:
            return 'neutral_position'
        elif 'research' in decision_lower:
            return 'research_task'
        elif 'analyze' in decision_lower:
            return 'analysis_task'
        else:
            return 'other'

    async def _get_active_agents(self) -> List[str]:
        """Get list of active agents"""
        # In production, query from database
        return [
            "CEO",
            "Research_Leader",
            "Analysis_Leader",
            "Strategy_Leader",
            "Market_Data_Specialist",
            "News_Analyst",
            "Sentiment_Researcher"
        ]


class PatternRecognitionService:
    """Service for recognizing and learning patterns"""

    def __init__(self, shared_memory: SharedMemory):
        self.shared_memory = shared_memory
        self.pattern_threshold = 0.7

    async def recognize_market_pattern(
        self,
        current_data: Dict[str, Any]
    ) -> Optional[Dict[str, Any]]:
        """Recognize if current data matches known patterns"""
        known_patterns = self.shared_memory.get_patterns(min_discoveries=3)

        for pattern in known_patterns:
            similarity = self._calculate_similarity(current_data, pattern)
            if similarity > self.pattern_threshold:
                return {
                    'pattern': pattern,
                    'similarity': similarity,
                    'recommendation': self._get_pattern_recommendation(pattern)
                }

        return None

    def _calculate_similarity(
        self,
        current_data: Dict,
        pattern: Dict
    ) -> float:
        """Calculate similarity between current data and pattern"""
        # Simplified similarity calculation
        # In production, use more sophisticated matching

        similarity_scores = []

        # Check condition match
        if pattern.get('condition'):
            condition_match = pattern['condition'] in str(current_data)
            similarity_scores.append(1.0 if condition_match else 0.0)

        # Check context similarity
        if pattern.get('context') and current_data.get('context'):
            context_similarity = self._context_similarity(
                pattern['context'],
                current_data['context']
            )
            similarity_scores.append(context_similarity)

        return np.mean(similarity_scores) if similarity_scores else 0.0

    def _context_similarity(self, context1: Dict, context2: Dict) -> float:
        """Calculate context similarity"""
        common_keys = set(context1.keys()) & set(context2.keys())
        if not common_keys:
            return 0.0

        matches = sum(
            1 for k in common_keys
            if str(context1[k]) == str(context2[k])
        )

        return matches / len(common_keys)

    def _get_pattern_recommendation(self, pattern: Dict) -> str:
        """Get recommendation based on pattern"""
        if pattern.get('type') == 'successful_strategy':
            return f"Consider applying strategy: {pattern.get('description')}"
        elif pattern.get('type') == 'failure_pattern':
            return f"Avoid: {pattern.get('description')}"
        else:
            return "Pattern recognized, proceed with caution"


# Singleton instance for the consolidation service
consolidation_service = None


def get_consolidation_service(
    persistence: MemoryPersistenceService,
    shared_memory: SharedMemory
) -> MemoryConsolidationService:
    """Get or create consolidation service singleton"""
    global consolidation_service
    if consolidation_service is None:
        consolidation_service = MemoryConsolidationService(
            persistence,
            shared_memory
        )
    return consolidation_service