"""
Agent Memory System for Multi-Agent Stock Research
Implements both short-term (working) and long-term (episodic) memory
"""

from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
import json
import hashlib
from dataclasses import dataclass, asdict
from collections import deque
import numpy as np
from sentence_transformers import SentenceTransformer
import faiss
import logging

logger = logging.getLogger(__name__)


@dataclass
class MemoryEntry:
    """Single memory entry with metadata"""
    content: str
    context: Dict[str, Any]
    timestamp: datetime
    agent_name: str
    memory_type: str  # 'observation', 'decision', 'learning', 'error'
    importance_score: float
    access_count: int = 0
    last_accessed: Optional[datetime] = None
    embedding: Optional[List[float]] = None

    def to_dict(self):
        data = asdict(self)
        data['timestamp'] = self.timestamp.isoformat()
        if self.last_accessed:
            data['last_accessed'] = self.last_accessed.isoformat()
        return data


class WorkingMemory:
    """Short-term memory for active context during analysis"""

    def __init__(self, capacity: int = 100):
        self.capacity = capacity
        self.memory: deque = deque(maxlen=capacity)
        self.context_window: Dict[str, Any] = {}

    def add(self, key: str, value: Any):
        """Add item to working memory"""
        entry = {
            'key': key,
            'value': value,
            'timestamp': datetime.utcnow()
        }
        self.memory.append(entry)
        self.context_window[key] = value

    def get(self, key: str) -> Optional[Any]:
        """Retrieve from working memory"""
        return self.context_window.get(key)

    def get_recent(self, n: int = 10) -> List[Dict]:
        """Get n most recent memories"""
        return list(self.memory)[-n:]

    def clear_context(self):
        """Clear context window but preserve memory trail"""
        self.context_window.clear()

    def update_context(self, updates: Dict[str, Any]):
        """Update multiple context items at once"""
        self.context_window.update(updates)
        for key, value in updates.items():
            self.add(key, value)


class EpisodicMemory:
    """Long-term memory with semantic search capabilities"""

    def __init__(self, embedding_model: str = "all-MiniLM-L6-v2"):
        self.memories: Dict[str, MemoryEntry] = {}
        self.encoder = SentenceTransformer(embedding_model)
        self.index = None
        self.memory_ids: List[str] = []
        self._initialize_index()

    def _initialize_index(self):
        """Initialize FAISS index for semantic search"""
        dimension = 384  # dimension for all-MiniLM-L6-v2
        self.index = faiss.IndexFlatL2(dimension)

    def _generate_id(self, content: str, context: Dict) -> str:
        """Generate unique ID for memory"""
        data = f"{content}{json.dumps(context, sort_keys=True)}"
        return hashlib.md5(data.encode()).hexdigest()

    def store(self, entry: MemoryEntry) -> str:
        """Store memory with embedding"""
        # Generate embedding
        embedding = self.encoder.encode(entry.content)
        entry.embedding = embedding.tolist()

        # Generate ID
        memory_id = self._generate_id(entry.content, entry.context)

        # Store memory
        self.memories[memory_id] = entry
        self.memory_ids.append(memory_id)

        # Add to index
        self.index.add(np.array([embedding]))

        logger.debug(f"Stored memory {memory_id}: {entry.content[:50]}...")
        return memory_id

    def retrieve(self, query: str, k: int = 5) -> List[MemoryEntry]:
        """Retrieve k most similar memories"""
        if not self.memory_ids:
            return []

        # Encode query
        query_embedding = self.encoder.encode(query)

        # Search
        distances, indices = self.index.search(
            np.array([query_embedding]),
            min(k, len(self.memory_ids))
        )

        # Retrieve memories
        results = []
        for idx in indices[0]:
            if idx < len(self.memory_ids):
                memory_id = self.memory_ids[idx]
                memory = self.memories[memory_id]
                memory.access_count += 1
                memory.last_accessed = datetime.utcnow()
                results.append(memory)

        return results

    def retrieve_similar(self, query: str, k: int = 5) -> List[MemoryEntry]:
        """
        Alias for retrieve method - retrieve k most similar memories.

        IMPORTANT: Returns List[MemoryEntry] objects (dataclasses with attributes).
        Access fields using dot notation: mem.content, mem.importance_score, mem.context
        NOT dictionary subscript: mem['content'] will raise 'MemoryEntry' object is not subscriptable
        """
        return self.retrieve(query, k)

    def add_memory(self, content: str, memory_type: str = "general", importance: float = 0.5) -> str:
        """Add a memory entry (alias for store with simpler interface)"""
        entry = MemoryEntry(
            content=content,
            context={},
            timestamp=datetime.utcnow(),
            agent_name="unknown",
            memory_type=memory_type,
            importance_score=importance
        )
        return self.store(entry)

    def forget(self, threshold_days: int = 30, min_importance: float = 0.3):
        """Forget old, unimportant memories"""
        cutoff_date = datetime.utcnow() - timedelta(days=threshold_days)

        to_forget = []
        for memory_id, memory in self.memories.items():
            # Forget if old and unimportant
            if memory.timestamp < cutoff_date and memory.importance_score < min_importance:
                # Consider access patterns
                if memory.access_count < 2:
                    to_forget.append(memory_id)

        for memory_id in to_forget:
            del self.memories[memory_id]

        # Rebuild index if memories were forgotten
        if to_forget:
            self._rebuild_index()

        logger.info(f"Forgot {len(to_forget)} memories")

    def _rebuild_index(self):
        """Rebuild FAISS index after forgetting"""
        self._initialize_index()
        self.memory_ids = []

        for memory_id, memory in self.memories.items():
            self.memory_ids.append(memory_id)
            embedding = np.array(memory.embedding)
            self.index.add(np.array([embedding]))


class SharedMemory:
    """Shared memory across all agents for collaborative learning"""

    def __init__(self):
        self.insights: Dict[str, List[Dict]] = {}  # Symbol -> Insights
        self.patterns: List[Dict] = []  # Discovered patterns
        self.errors: List[Dict] = []  # Common errors to avoid

    def add_insight(self, symbol: str, insight: Dict):
        """Add insight about a symbol"""
        if symbol not in self.insights:
            self.insights[symbol] = []

        insight['timestamp'] = datetime.utcnow().isoformat()
        self.insights[symbol].append(insight)

        # Keep only recent insights (last 100)
        self.insights[symbol] = self.insights[symbol][-100:]

    def add_pattern(self, pattern: Dict):
        """Add discovered market pattern"""
        pattern['timestamp'] = datetime.utcnow().isoformat()
        pattern['discovery_count'] = 1

        # Check if pattern exists
        for existing in self.patterns:
            if existing.get('type') == pattern.get('type') and \
               existing.get('condition') == pattern.get('condition'):
                existing['discovery_count'] += 1
                return

        self.patterns.append(pattern)

    def add_error(self, error: Dict):
        """Learn from errors"""
        error['timestamp'] = datetime.utcnow().isoformat()
        self.errors.append(error)

        # Keep only recent errors (last 50)
        self.errors = self.errors[-50:]

    def get_relevant_insights(self, symbol: str) -> List[Dict]:
        """Get insights for a symbol"""
        return self.insights.get(symbol, [])

    def get_patterns(self, min_discoveries: int = 2) -> List[Dict]:
        """Get reliable patterns"""
        return [p for p in self.patterns if p['discovery_count'] >= min_discoveries]


class AgentMemorySystem:
    """Complete memory system for an agent"""

    def __init__(self, agent_name: str, shared_memory: Optional[SharedMemory] = None):
        self.agent_name = agent_name
        self.working = WorkingMemory()
        self.episodic = EpisodicMemory()
        self.shared = shared_memory or SharedMemory()

    def remember_observation(self, content: str, context: Dict, importance: float = 0.5):
        """Remember an observation"""
        entry = MemoryEntry(
            content=content,
            context=context,
            timestamp=datetime.utcnow(),
            agent_name=self.agent_name,
            memory_type='observation',
            importance_score=importance
        )

        # Store in episodic memory
        self.episodic.store(entry)

        # Also add to working memory if important
        if importance > 0.7:
            self.working.add(f"observation_{datetime.utcnow().timestamp()}", content)

    def remember_decision(self, decision: str, reasoning: str, context: Dict):
        """Remember a decision and its reasoning"""
        entry = MemoryEntry(
            content=f"Decision: {decision}. Reasoning: {reasoning}",
            context=context,
            timestamp=datetime.utcnow(),
            agent_name=self.agent_name,
            memory_type='decision',
            importance_score=0.8
        )

        self.episodic.store(entry)
        self.working.add('last_decision', {'decision': decision, 'reasoning': reasoning})

    def recall_similar(self, query: str, k: int = 5) -> List[MemoryEntry]:
        """Recall similar past experiences"""
        return self.episodic.retrieve(query, k)

    def learn_from_outcome(self, decision: str, outcome: str, success: bool):
        """Learn from decision outcomes"""
        learning = {
            'decision': decision,
            'outcome': outcome,
            'success': success,
            'agent': self.agent_name
        }

        if not success:
            # Remember errors
            self.shared.add_error(learning)

        entry = MemoryEntry(
            content=f"Learned: {decision} led to {outcome} ({'success' if success else 'failure'})",
            context=learning,
            timestamp=datetime.utcnow(),
            agent_name=self.agent_name,
            memory_type='learning',
            importance_score=0.9 if not success else 0.6
        )

        self.episodic.store(entry)

    def consolidate_memories(self):
        """Consolidate and compress memories"""
        # Forget old, unimportant memories
        self.episodic.forget(threshold_days=7, min_importance=0.4)

        # Clear working memory context
        self.working.clear_context()

        logger.info(f"Agent {self.agent_name} consolidated memories")