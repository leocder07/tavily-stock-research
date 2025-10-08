"""
MongoDB Persistence for Agent Memory System
Stores and retrieves agent memories, patterns, and learning
"""

from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
from motor.motor_asyncio import AsyncIOMotorDatabase
import numpy as np
import json
import logging
from bson import ObjectId

from memory.agent_memory import MemoryEntry, SharedMemory

logger = logging.getLogger(__name__)


class MemoryPersistenceService:
    """Persist agent memories to MongoDB"""

    def __init__(self, db: AsyncIOMotorDatabase):
        self.db = db
        self.memories_collection = db.agent_memories
        self.patterns_collection = db.discovered_patterns
        self.insights_collection = db.symbol_insights
        self.learning_collection = db.agent_learning

        # Create indexes
        self._create_indexes()

    def _create_indexes(self):
        """Create MongoDB indexes for efficient queries"""
        # Memory indexes
        self.memories_collection.create_index([
            ("agent_name", 1),
            ("timestamp", -1)
        ])
        self.memories_collection.create_index([
            ("memory_type", 1),
            ("importance_score", -1)
        ])
        self.memories_collection.create_index([
            ("content", "text")  # Text index for search
        ])

        # Pattern indexes
        self.patterns_collection.create_index([
            ("discovery_count", -1),
            ("confidence", -1)
        ])

        # Insight indexes
        self.insights_collection.create_index([
            ("symbol", 1),
            ("timestamp", -1)
        ])

        # Learning indexes
        self.learning_collection.create_index([
            ("agent_name", 1),
            ("success", 1),
            ("timestamp", -1)
        ])

        logger.info("Memory persistence indexes created")

    async def save_memory(self, memory: MemoryEntry, agent_name: str) -> str:
        """Save a memory entry to MongoDB"""
        try:
            memory_doc = {
                'agent_name': agent_name,
                'content': memory.content,
                'context': memory.context,
                'timestamp': memory.timestamp,
                'memory_type': memory.memory_type,
                'importance_score': memory.importance_score,
                'access_count': memory.access_count,
                'last_accessed': memory.last_accessed,
                'embedding': memory.embedding  # Store as list
            }

            result = await self.memories_collection.insert_one(memory_doc)
            logger.debug(f"Saved memory {result.inserted_id} for agent {agent_name}")
            return str(result.inserted_id)

        except Exception as e:
            logger.error(f"Error saving memory: {e}")
            return ""

    async def load_recent_memories(
        self,
        agent_name: str,
        limit: int = 100,
        memory_type: Optional[str] = None
    ) -> List[MemoryEntry]:
        """Load recent memories for an agent"""
        try:
            query = {'agent_name': agent_name}
            if memory_type:
                query['memory_type'] = memory_type

            cursor = self.memories_collection.find(query).sort(
                'timestamp', -1
            ).limit(limit)

            memories = []
            async for doc in cursor:
                memory = MemoryEntry(
                    content=doc['content'],
                    context=doc['context'],
                    timestamp=doc['timestamp'],
                    agent_name=doc['agent_name'],
                    memory_type=doc['memory_type'],
                    importance_score=doc['importance_score'],
                    access_count=doc.get('access_count', 0),
                    last_accessed=doc.get('last_accessed'),
                    embedding=doc.get('embedding')
                )
                memories.append(memory)

            logger.info(f"Loaded {len(memories)} memories for {agent_name}")
            return memories

        except Exception as e:
            logger.error(f"Error loading memories: {e}")
            return []

    async def search_memories(
        self,
        query: str,
        agent_name: Optional[str] = None,
        limit: int = 10
    ) -> List[MemoryEntry]:
        """Search memories using text search"""
        try:
            search_query = {"$text": {"$search": query}}
            if agent_name:
                search_query['agent_name'] = agent_name

            cursor = self.memories_collection.find(
                search_query,
                {"score": {"$meta": "textScore"}}
            ).sort(
                [("score", {"$meta": "textScore"})]
            ).limit(limit)

            memories = []
            async for doc in cursor:
                memory = MemoryEntry(
                    content=doc['content'],
                    context=doc['context'],
                    timestamp=doc['timestamp'],
                    agent_name=doc['agent_name'],
                    memory_type=doc['memory_type'],
                    importance_score=doc['importance_score'],
                    access_count=doc.get('access_count', 0),
                    last_accessed=doc.get('last_accessed'),
                    embedding=doc.get('embedding')
                )
                memories.append(memory)

            # Update access count
            for doc in memories:
                await self.memories_collection.update_one(
                    {'_id': doc['_id']},
                    {
                        '$inc': {'access_count': 1},
                        '$set': {'last_accessed': datetime.utcnow()}
                    }
                )

            return memories

        except Exception as e:
            logger.error(f"Error searching memories: {e}")
            return []

    async def save_pattern(self, pattern: Dict[str, Any]) -> str:
        """Save a discovered pattern"""
        try:
            pattern['discovered_at'] = datetime.utcnow()
            pattern['last_seen'] = datetime.utcnow()

            # Check if pattern exists
            existing = await self.patterns_collection.find_one({
                'type': pattern.get('type'),
                'condition': pattern.get('condition')
            })

            if existing:
                # Update existing pattern
                await self.patterns_collection.update_one(
                    {'_id': existing['_id']},
                    {
                        '$inc': {'discovery_count': 1},
                        '$set': {
                            'last_seen': datetime.utcnow(),
                            'confidence': pattern.get('confidence', existing.get('confidence', 0.5))
                        }
                    }
                )
                return str(existing['_id'])
            else:
                # Insert new pattern
                result = await self.patterns_collection.insert_one(pattern)
                return str(result.inserted_id)

        except Exception as e:
            logger.error(f"Error saving pattern: {e}")
            return ""

    async def get_reliable_patterns(
        self,
        min_discoveries: int = 3,
        min_confidence: float = 0.6
    ) -> List[Dict[str, Any]]:
        """Get reliable patterns based on discovery count and confidence"""
        try:
            cursor = self.patterns_collection.find({
                'discovery_count': {'$gte': min_discoveries},
                'confidence': {'$gte': min_confidence}
            }).sort('discovery_count', -1)

            patterns = []
            async for doc in cursor:
                doc['_id'] = str(doc['_id'])
                patterns.append(doc)

            return patterns

        except Exception as e:
            logger.error(f"Error getting patterns: {e}")
            return []

    async def save_insight(
        self,
        symbol: str,
        insight: Dict[str, Any],
        agent_name: str
    ) -> str:
        """Save an insight about a symbol"""
        try:
            insight_doc = {
                'symbol': symbol,
                'agent_name': agent_name,
                'insight': insight,
                'timestamp': datetime.utcnow(),
                'relevance_score': insight.get('confidence', 0.5)
            }

            result = await self.insights_collection.insert_one(insight_doc)
            return str(result.inserted_id)

        except Exception as e:
            logger.error(f"Error saving insight: {e}")
            return ""

    async def get_symbol_insights(
        self,
        symbol: str,
        limit: int = 20,
        min_relevance: float = 0.5
    ) -> List[Dict[str, Any]]:
        """Get insights for a specific symbol"""
        try:
            cursor = self.insights_collection.find({
                'symbol': symbol,
                'relevance_score': {'$gte': min_relevance}
            }).sort('timestamp', -1).limit(limit)

            insights = []
            async for doc in cursor:
                doc['_id'] = str(doc['_id'])
                insights.append(doc)

            return insights

        except Exception as e:
            logger.error(f"Error getting insights: {e}")
            return []

    async def save_learning(
        self,
        agent_name: str,
        decision: str,
        outcome: str,
        success: bool,
        context: Dict[str, Any]
    ) -> str:
        """Save agent learning from decisions"""
        try:
            learning_doc = {
                'agent_name': agent_name,
                'decision': decision,
                'outcome': outcome,
                'success': success,
                'context': context,
                'timestamp': datetime.utcnow()
            }

            result = await self.learning_collection.insert_one(learning_doc)

            # If this is a failure, analyze for patterns
            if not success:
                await self._analyze_failure_pattern(agent_name, decision, context)

            return str(result.inserted_id)

        except Exception as e:
            logger.error(f"Error saving learning: {e}")
            return ""

    async def get_agent_performance(
        self,
        agent_name: str,
        days_back: int = 7
    ) -> Dict[str, Any]:
        """Get agent performance metrics"""
        try:
            cutoff = datetime.utcnow() - timedelta(days=days_back)

            # Get success rate
            total = await self.learning_collection.count_documents({
                'agent_name': agent_name,
                'timestamp': {'$gte': cutoff}
            })

            successful = await self.learning_collection.count_documents({
                'agent_name': agent_name,
                'success': True,
                'timestamp': {'$gte': cutoff}
            })

            # Get common failures
            failures = await self.learning_collection.find({
                'agent_name': agent_name,
                'success': False,
                'timestamp': {'$gte': cutoff}
            }).limit(10).to_list(length=10)

            performance = {
                'agent_name': agent_name,
                'period_days': days_back,
                'total_decisions': total,
                'successful_decisions': successful,
                'success_rate': (successful / total) if total > 0 else 0,
                'recent_failures': failures
            }

            return performance

        except Exception as e:
            logger.error(f"Error getting performance: {e}")
            return {}

    async def _analyze_failure_pattern(
        self,
        agent_name: str,
        decision: str,
        context: Dict[str, Any]
    ):
        """Analyze failures for patterns"""
        try:
            # Look for similar failures
            similar_failures = await self.learning_collection.count_documents({
                'agent_name': agent_name,
                'decision': {'$regex': decision[:20], '$options': 'i'},
                'success': False
            })

            if similar_failures >= 3:
                # This is a recurring failure pattern
                pattern = {
                    'type': 'recurring_failure',
                    'agent': agent_name,
                    'decision_pattern': decision[:50],
                    'condition': context.get('condition', 'unknown'),
                    'discovery_count': similar_failures,
                    'confidence': 0.8,
                    'description': f"Agent {agent_name} repeatedly fails with: {decision[:50]}"
                }

                await self.save_pattern(pattern)
                logger.warning(f"Detected recurring failure pattern for {agent_name}")

        except Exception as e:
            logger.error(f"Error analyzing failure pattern: {e}")

    async def cleanup_old_memories(
        self,
        days: int = 30,
        importance_threshold: float = 0.3
    ):
        """Clean up old, unimportant memories"""
        try:
            cutoff = datetime.utcnow() - timedelta(days=days)

            # Delete old, unimportant, rarely accessed memories
            result = await self.memories_collection.delete_many({
                'timestamp': {'$lt': cutoff},
                'importance_score': {'$lt': importance_threshold},
                'access_count': {'$lt': 2}
            })

            logger.info(f"Cleaned up {result.deleted_count} old memories")

        except Exception as e:
            logger.error(f"Error cleaning up memories: {e}")

    async def export_agent_knowledge(self, agent_name: str) -> Dict[str, Any]:
        """Export all knowledge for an agent"""
        try:
            # Get recent memories
            memories = await self.load_recent_memories(agent_name, limit=500)

            # Get learning history
            learning_cursor = self.learning_collection.find({
                'agent_name': agent_name
            }).sort('timestamp', -1).limit(100)

            learning_history = []
            async for doc in learning_cursor:
                doc['_id'] = str(doc['_id'])
                learning_history.append(doc)

            # Get performance
            performance = await self.get_agent_performance(agent_name, days_back=30)

            knowledge = {
                'agent_name': agent_name,
                'export_date': datetime.utcnow().isoformat(),
                'memory_count': len(memories),
                'learning_entries': len(learning_history),
                'performance': performance,
                'recent_memories': [m.to_dict() for m in memories[:50]],
                'learning_history': learning_history[:50]
            }

            return knowledge

        except Exception as e:
            logger.error(f"Error exporting knowledge: {e}")
            return {}


class MemorySearchService:
    """Advanced memory search using embeddings"""

    def __init__(self, persistence: MemoryPersistenceService):
        self.persistence = persistence

    async def semantic_search(
        self,
        query: str,
        agent_name: Optional[str] = None,
        k: int = 10
    ) -> List[Dict[str, Any]]:
        """Semantic search across memories using embeddings"""
        # This would use FAISS or similar for vector search
        # For now, fallback to text search
        memories = await self.persistence.search_memories(query, agent_name, k)

        results = []
        for memory in memories:
            results.append({
                'content': memory.content,
                'context': memory.context,
                'agent': memory.agent_name,
                'type': memory.memory_type,
                'importance': memory.importance_score,
                'timestamp': memory.timestamp.isoformat()
            })

        return results

    async def find_similar_scenarios(
        self,
        scenario: Dict[str, Any],
        limit: int = 5
    ) -> List[Dict[str, Any]]:
        """Find similar past scenarios"""
        # Build search query from scenario
        search_terms = []
        if scenario.get('symbols'):
            search_terms.extend(scenario['symbols'])
        if scenario.get('query'):
            search_terms.append(scenario['query'])

        query = ' '.join(search_terms)

        memories = await self.persistence.search_memories(query, limit=limit)

        similar = []
        for memory in memories:
            similar.append({
                'memory': memory.content,
                'context': memory.context,
                'similarity': 0.8,  # Would be calculated by embedding similarity
                'timestamp': memory.timestamp.isoformat()
            })

        return similar