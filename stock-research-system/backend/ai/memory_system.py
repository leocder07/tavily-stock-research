"""
Advanced Memory System for TavilyAI Pro
Implements multi-tier memory with working, short-term, long-term, episodic, and semantic memory
"""

import json
import pickle
import asyncio
from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from collections import deque, OrderedDict
import hashlib
import logging
from enum import Enum
import numpy as np

logger = logging.getLogger(__name__)


class MemoryType(Enum):
    """Types of memory"""
    SENSORY = "sensory"       # Very short-term (5 seconds)
    WORKING = "working"        # Active memory (7±2 items)
    SHORT_TERM = "short_term"  # Hours
    LONG_TERM = "long_term"    # Persistent
    EPISODIC = "episodic"      # Event-based
    SEMANTIC = "semantic"      # Fact-based
    PROCEDURAL = "procedural"  # Skill-based


@dataclass
class MemoryItem:
    """Single memory item"""
    id: str
    content: Any
    memory_type: MemoryType
    timestamp: datetime
    access_count: int = 0
    importance_score: float = 0.5
    decay_rate: float = 0.1
    associations: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
    embedding: Optional[np.ndarray] = None


class MemoryTier:
    """Base class for memory tiers"""

    def __init__(self, capacity: Optional[int] = None, ttl_seconds: Optional[int] = None):
        self.capacity = capacity
        self.ttl_seconds = ttl_seconds
        self.memories: OrderedDict[str, MemoryItem] = OrderedDict()
        self.access_patterns: Dict[str, List[datetime]] = {}

    def add(self, item: MemoryItem) -> bool:
        """Add item to memory"""
        # Check capacity
        if self.capacity and len(self.memories) >= self.capacity:
            self._evict_least_important()

        # Add to memory
        self.memories[item.id] = item
        self._track_access(item.id)
        return True

    def get(self, item_id: str) -> Optional[MemoryItem]:
        """Retrieve item from memory"""
        if item_id in self.memories:
            item = self.memories[item_id]

            # Check TTL
            if self._is_expired(item):
                del self.memories[item_id]
                return None

            # Update access
            item.access_count += 1
            self._track_access(item_id)

            # Move to end (LRU)
            self.memories.move_to_end(item_id)

            return item
        return None

    def _evict_least_important(self):
        """Evict least important item when capacity reached"""
        if not self.memories:
            return

        # Calculate importance scores
        scores = []
        for mem_id, item in self.memories.items():
            score = self._calculate_importance(item)
            scores.append((mem_id, score))

        # Sort by importance (lowest first)
        scores.sort(key=lambda x: x[1])

        # Evict least important
        evict_id = scores[0][0]
        del self.memories[evict_id]
        logger.debug(f"Evicted memory item: {evict_id}")

    def _calculate_importance(self, item: MemoryItem) -> float:
        """Calculate importance score for memory item"""
        # Factors: base importance, recency, frequency
        recency_factor = self._calculate_recency_factor(item)
        frequency_factor = min(item.access_count / 10, 1.0)
        association_factor = min(len(item.associations) / 5, 1.0)

        importance = (
            item.importance_score * 0.4 +
            recency_factor * 0.3 +
            frequency_factor * 0.2 +
            association_factor * 0.1
        )
        return importance

    def _calculate_recency_factor(self, item: MemoryItem) -> float:
        """Calculate recency factor based on time decay"""
        age_seconds = (datetime.now() - item.timestamp).total_seconds()
        decay_factor = np.exp(-item.decay_rate * age_seconds / 3600)  # Decay per hour
        return decay_factor

    def _is_expired(self, item: MemoryItem) -> bool:
        """Check if item has expired"""
        if not self.ttl_seconds:
            return False
        age_seconds = (datetime.now() - item.timestamp).total_seconds()
        return age_seconds > self.ttl_seconds

    def _track_access(self, item_id: str):
        """Track access patterns"""
        if item_id not in self.access_patterns:
            self.access_patterns[item_id] = []
        self.access_patterns[item_id].append(datetime.now())

        # Keep only recent accesses
        cutoff = datetime.now() - timedelta(hours=24)
        self.access_patterns[item_id] = [
            t for t in self.access_patterns[item_id] if t > cutoff
        ]


class WorkingMemory(MemoryTier):
    """Working memory with 7±2 item capacity"""

    def __init__(self):
        super().__init__(capacity=7)
        self.focus_stack = deque(maxlen=3)  # Current focus items

    def focus_on(self, item_id: str):
        """Focus on specific item"""
        if item_id in self.memories:
            self.focus_stack.append(item_id)
            # Boost importance of focused item
            self.memories[item_id].importance_score = min(
                self.memories[item_id].importance_score + 0.1, 1.0
            )

    def get_focused_items(self) -> List[MemoryItem]:
        """Get currently focused items"""
        items = []
        for item_id in self.focus_stack:
            if item_id in self.memories:
                items.append(self.memories[item_id])
        return items


class EpisodicMemory(MemoryTier):
    """Episodic memory for event sequences"""

    def __init__(self):
        super().__init__()
        self.episodes: Dict[str, List[MemoryItem]] = {}
        self.current_episode: Optional[str] = None

    def start_episode(self, episode_id: str):
        """Start a new episode"""
        self.current_episode = episode_id
        self.episodes[episode_id] = []

    def add_to_episode(self, item: MemoryItem):
        """Add item to current episode"""
        if self.current_episode:
            self.episodes[self.current_episode].append(item)
            self.add(item)

    def get_episode(self, episode_id: str) -> List[MemoryItem]:
        """Get all items from an episode"""
        return self.episodes.get(episode_id, [])

    def find_similar_episodes(self, current_context: Dict) -> List[str]:
        """Find episodes similar to current context"""
        similar = []
        # Implementation would use embeddings for similarity
        return similar


class SemanticMemory(MemoryTier):
    """Semantic memory for facts and knowledge"""

    def __init__(self):
        super().__init__()
        self.knowledge_graph: Dict[str, List[str]] = {}  # Concept relationships
        self.concept_embeddings: Dict[str, np.ndarray] = {}

    def add_fact(self, fact: str, concepts: List[str], embedding: Optional[np.ndarray] = None):
        """Add a fact with associated concepts"""
        fact_id = hashlib.md5(fact.encode()).hexdigest()[:8]

        item = MemoryItem(
            id=fact_id,
            content=fact,
            memory_type=MemoryType.SEMANTIC,
            timestamp=datetime.now(),
            metadata={"concepts": concepts},
            embedding=embedding
        )

        self.add(item)

        # Update knowledge graph
        for concept in concepts:
            if concept not in self.knowledge_graph:
                self.knowledge_graph[concept] = []
            self.knowledge_graph[concept].append(fact_id)

            if embedding is not None:
                self.concept_embeddings[concept] = embedding

    def get_related_facts(self, concept: str) -> List[MemoryItem]:
        """Get facts related to a concept"""
        fact_ids = self.knowledge_graph.get(concept, [])
        facts = []
        for fact_id in fact_ids:
            fact = self.get(fact_id)
            if fact:
                facts.append(fact)
        return facts


class ProceduralMemory(MemoryTier):
    """Procedural memory for learned skills and patterns"""

    def __init__(self):
        super().__init__()
        self.procedures: Dict[str, Dict[str, Any]] = {}
        self.success_rates: Dict[str, float] = {}

    def add_procedure(self, name: str, steps: List[str], context: Dict, success: bool):
        """Add or update a procedure"""
        proc_id = hashlib.md5(name.encode()).hexdigest()[:8]

        if proc_id not in self.procedures:
            self.procedures[proc_id] = {
                "name": name,
                "steps": steps,
                "contexts": [],
                "success_count": 0,
                "total_count": 0
            }

        self.procedures[proc_id]["contexts"].append(context)
        self.procedures[proc_id]["total_count"] += 1
        if success:
            self.procedures[proc_id]["success_count"] += 1

        # Update success rate
        proc = self.procedures[proc_id]
        self.success_rates[proc_id] = proc["success_count"] / proc["total_count"]

        # Create memory item
        item = MemoryItem(
            id=proc_id,
            content={"name": name, "steps": steps},
            memory_type=MemoryType.PROCEDURAL,
            timestamp=datetime.now(),
            importance_score=self.success_rates[proc_id],
            metadata={"context": context, "success": success}
        )
        self.add(item)

    def get_best_procedure(self, task: str) -> Optional[Dict[str, Any]]:
        """Get best procedure for a task"""
        # Find matching procedures
        matches = []
        for proc_id, proc in self.procedures.items():
            if task.lower() in proc["name"].lower():
                success_rate = self.success_rates.get(proc_id, 0)
                matches.append((proc, success_rate))

        # Sort by success rate
        matches.sort(key=lambda x: x[1], reverse=True)

        if matches:
            return matches[0][0]
        return None


class AdvancedMemorySystem:
    """
    Advanced memory system with multiple tiers and consolidation
    """

    def __init__(self, persist_path: Optional[str] = "./memory_store"):
        self.persist_path = persist_path

        # Initialize memory tiers
        self.tiers = {
            MemoryType.SENSORY: MemoryTier(capacity=20, ttl_seconds=5),
            MemoryType.WORKING: WorkingMemory(),
            MemoryType.SHORT_TERM: MemoryTier(capacity=100, ttl_seconds=3600),
            MemoryType.LONG_TERM: MemoryTier(),  # No capacity limit
            MemoryType.EPISODIC: EpisodicMemory(),
            MemoryType.SEMANTIC: SemanticMemory(),
            MemoryType.PROCEDURAL: ProceduralMemory()
        }

        # Consolidation queue
        self.consolidation_queue: deque = deque(maxlen=50)

        # Load persisted memories
        self._load_memories()

        # Start background consolidation
        self._start_consolidation_task()

    def store(self,
             content: Any,
             memory_type: MemoryType,
             importance: float = 0.5,
             associations: Optional[List[str]] = None,
             metadata: Optional[Dict] = None) -> str:
        """
        Store content in appropriate memory tier

        Args:
            content: Content to store
            memory_type: Type of memory
            importance: Importance score (0-1)
            associations: Associated memory IDs
            metadata: Additional metadata

        Returns:
            Memory item ID
        """
        # Generate ID
        content_str = str(content)
        item_id = hashlib.md5(f"{content_str}{datetime.now()}".encode()).hexdigest()[:16]

        # Create memory item
        item = MemoryItem(
            id=item_id,
            content=content,
            memory_type=memory_type,
            timestamp=datetime.now(),
            importance_score=importance,
            associations=associations or [],
            metadata=metadata or {}
        )

        # Add to appropriate tier
        tier = self.tiers[memory_type]
        success = tier.add(item)

        if success:
            # Add to consolidation queue if important
            if importance > 0.7:
                self.consolidation_queue.append(item_id)

            logger.debug(f"Stored memory {item_id} in {memory_type.value}")

        return item_id

    def recall(self,
              query: str,
              memory_types: Optional[List[MemoryType]] = None,
              max_items: int = 5) -> List[MemoryItem]:
        """
        Recall relevant memories

        Args:
            query: Query for recall
            memory_types: Types to search (None = all)
            max_items: Maximum items to return

        Returns:
            List of relevant memory items
        """
        if not memory_types:
            memory_types = list(MemoryType)

        all_items = []

        # Search each requested tier
        for mem_type in memory_types:
            tier = self.tiers[mem_type]

            # Get all items from tier
            for item_id, item in tier.memories.items():
                # Simple relevance check (can be enhanced with embeddings)
                if self._is_relevant(item, query):
                    all_items.append(item)

        # Sort by relevance and importance
        all_items.sort(key=lambda x: x.importance_score, reverse=True)

        return all_items[:max_items]

    def _is_relevant(self, item: MemoryItem, query: str) -> bool:
        """Check if memory item is relevant to query"""
        # Simple keyword matching (enhance with embeddings)
        query_lower = query.lower()
        content_str = str(item.content).lower()

        # Check content
        for word in query_lower.split():
            if word in content_str:
                return True

        # Check metadata
        metadata_str = str(item.metadata).lower()
        for word in query_lower.split():
            if word in metadata_str:
                return True

        return False

    async def consolidate_memories(self):
        """Consolidate memories from short-term to long-term"""
        while self.consolidation_queue:
            item_id = self.consolidation_queue.popleft()

            # Try to find in short-term
            short_term = self.tiers[MemoryType.SHORT_TERM]
            item = short_term.get(item_id)

            if item and item.importance_score > 0.6:
                # Check if should move to long-term
                if item.access_count > 3 or item.importance_score > 0.8:
                    # Move to long-term
                    self.tiers[MemoryType.LONG_TERM].add(item)
                    logger.debug(f"Consolidated {item_id} to long-term memory")

                # Check for semantic extraction
                if isinstance(item.content, str) and len(item.content) > 100:
                    # Extract facts for semantic memory
                    facts = self._extract_facts(item.content)
                    for fact in facts:
                        semantic_mem = self.tiers[MemoryType.SEMANTIC]
                        if isinstance(semantic_mem, SemanticMemory):
                            semantic_mem.add_fact(fact, [], None)

    def _extract_facts(self, content: str) -> List[str]:
        """Extract facts from content (simplified)"""
        # Split into sentences
        import re
        sentences = re.split(r'[.!?]+', content)

        # Filter for fact-like sentences
        facts = []
        for sent in sentences:
            sent = sent.strip()
            if len(sent) > 20 and len(sent) < 200:
                # Simple heuristic: sentences with "is", "are", "was", etc.
                if any(word in sent.lower() for word in ['is', 'are', 'was', 'were', 'has', 'have']):
                    facts.append(sent)

        return facts[:5]  # Limit to 5 facts

    def _start_consolidation_task(self):
        """Start background consolidation task"""
        async def consolidation_loop():
            while True:
                await asyncio.sleep(60)  # Run every minute
                await self.consolidate_memories()

        # Start in background (would use asyncio.create_task in real app)
        pass

    def create_associations(self, item_id1: str, item_id2: str, strength: float = 0.5):
        """Create association between memories"""
        for tier in self.tiers.values():
            item1 = tier.get(item_id1)
            item2 = tier.get(item_id2)

            if item1:
                item1.associations.append(item_id2)
            if item2:
                item2.associations.append(item_id1)

            if item1 and item2:
                logger.debug(f"Created association between {item_id1} and {item_id2}")
                break

    def get_associative_memories(self, item_id: str, depth: int = 2) -> List[MemoryItem]:
        """Get memories associated with an item"""
        visited = set()
        to_visit = deque([(item_id, 0)])
        associated = []

        while to_visit:
            current_id, current_depth = to_visit.popleft()

            if current_id in visited or current_depth > depth:
                continue

            visited.add(current_id)

            # Find item in any tier
            for tier in self.tiers.values():
                item = tier.get(current_id)
                if item:
                    associated.append(item)

                    # Add associations to queue
                    for assoc_id in item.associations:
                        if assoc_id not in visited:
                            to_visit.append((assoc_id, current_depth + 1))
                    break

        return associated

    def forget(self, decay_factor: float = 0.1):
        """Apply forgetting curve to memories"""
        for tier_type, tier in self.tiers.items():
            if tier_type in [MemoryType.LONG_TERM, MemoryType.SEMANTIC]:
                continue  # Don't forget long-term and semantic

            items_to_remove = []
            for item_id, item in tier.memories.items():
                # Apply decay
                item.importance_score *= (1 - decay_factor)

                # Remove if importance too low
                if item.importance_score < 0.1:
                    items_to_remove.append(item_id)

            # Remove forgotten items
            for item_id in items_to_remove:
                del tier.memories[item_id]
                logger.debug(f"Forgot memory item: {item_id}")

    def _save_memories(self):
        """Save memories to disk"""
        if not self.persist_path:
            return

        import os
        os.makedirs(self.persist_path, exist_ok=True)

        # Save long-term and semantic memories
        for mem_type in [MemoryType.LONG_TERM, MemoryType.SEMANTIC]:
            tier = self.tiers[mem_type]
            path = os.path.join(self.persist_path, f"{mem_type.value}.pkl")

            try:
                with open(path, 'wb') as f:
                    pickle.dump(tier.memories, f)
                logger.info(f"Saved {len(tier.memories)} {mem_type.value} memories")
            except Exception as e:
                logger.error(f"Error saving {mem_type.value} memories: {e}")

    def _load_memories(self):
        """Load memories from disk"""
        if not self.persist_path:
            return

        import os

        for mem_type in [MemoryType.LONG_TERM, MemoryType.SEMANTIC]:
            path = os.path.join(self.persist_path, f"{mem_type.value}.pkl")

            if os.path.exists(path):
                try:
                    with open(path, 'rb') as f:
                        memories = pickle.load(f)
                        self.tiers[mem_type].memories = memories
                    logger.info(f"Loaded {len(memories)} {mem_type.value} memories")
                except Exception as e:
                    logger.error(f"Error loading {mem_type.value} memories: {e}")

    def get_statistics(self) -> Dict[str, Any]:
        """Get memory system statistics"""
        stats = {}
        for mem_type, tier in self.tiers.items():
            stats[mem_type.value] = {
                "count": len(tier.memories),
                "capacity": tier.capacity,
                "oldest": min([m.timestamp for m in tier.memories.values()]) if tier.memories else None,
                "newest": max([m.timestamp for m in tier.memories.values()]) if tier.memories else None
            }
        return stats