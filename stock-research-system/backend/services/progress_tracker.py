"""Progress Tracker for Real-time Analysis Updates with Citations"""

import asyncio
from typing import Dict, Any, Optional, List, Callable
from datetime import datetime
import logging
from dataclasses import dataclass, field

logger = logging.getLogger(__name__)


@dataclass
class Citation:
    """Represents a citation from Tavily API."""
    title: str
    url: str
    content: str
    published_date: Optional[str] = None
    source: Optional[str] = None
    relevance_score: float = 0.0


@dataclass
class ProgressUpdate:
    """Represents a progress update during analysis."""
    stage: str
    agent: str
    status: str  # 'starting', 'in_progress', 'completed', 'failed'
    message: str
    progress_percentage: float
    citations: List[Citation] = field(default_factory=list)
    details: Dict[str, Any] = field(default_factory=dict)
    timestamp: str = field(default_factory=lambda: datetime.utcnow().isoformat())


class ProgressTracker:
    """Tracks and broadcasts analysis progress with citations."""

    def __init__(self):
        self.current_analysis: Dict[str, Any] = {}
        self.progress_callbacks: List[Callable] = []
        self.citations: Dict[str, List[Citation]] = {}
        self.agent_status: Dict[str, str] = {}
        self.agent_sub_progress: Dict[str, float] = {}  # Sub-progress within each agent (0-1)

    async def register_callback(self, callback: Callable):
        """Register a callback for progress updates."""
        self.progress_callbacks.append(callback)

    async def start_analysis(self, request_id: str, query: str, symbols: List[str]):
        """Initialize tracking for a new analysis."""
        self.current_analysis[request_id] = {
            'query': query,
            'symbols': symbols,
            'start_time': datetime.utcnow(),
            'stages': {},
            'citations': []
        }

        await self.emit_progress(ProgressUpdate(
            stage='initialization',
            agent='system',
            status='starting',
            message=f'Starting analysis for {", ".join(symbols)}',
            progress_percentage=0,
            details={'query': query, 'symbols': symbols}
        ), request_id)

    async def update_agent_progress(self, request_id: str, agent_name: str,
                                   status: str, message: str,
                                   citations: List[Citation] = None,
                                   details: Dict[str, Any] = None,
                                   sub_progress: float = None):
        """Update progress for a specific agent with optional sub-progress.

        Args:
            request_id: ID of the analysis request
            agent_name: Name of the agent
            status: Agent status ('starting', 'in_progress', 'completed', 'failed')
            message: Progress message
            citations: List of citations found
            details: Additional details
            sub_progress: Sub-progress within agent (0.0 to 1.0), e.g., 0.5 = 50% through agent's work
        """
        if request_id not in self.current_analysis:
            return

        # Calculate progress based on agent completion with hierarchical weights
        # Phase 1: Planning (5%)
        # Phase 2: Research (30%)
        # Phase 3: Analysis (40%)
        # Phase 4: Strategy (20%)
        # Phase 5: Synthesis (5%)
        agent_weights = {
            # Phase 1: Planning
            'ceo_planning': 5,
            'query_parser': 0,  # Included in CEO planning

            # Phase 2: Research
            'market_data': 10,
            'news_analysis': 8,
            'sentiment': 7,
            'macro_economics': 5,

            # Phase 3: Analysis
            'fundamental': 12,
            'technical': 10,
            'valuation': 10,
            'risk': 8,

            # Phase 4: Strategy
            'insider_activity': 7,
            'peer': 6,
            'portfolio_fit': 7,

            # Phase 5: Synthesis
            'synthesis': 3,
            'critique': 2
        }

        # Update agent status and sub-progress
        self.agent_status[agent_name] = status
        if sub_progress is not None:
            self.agent_sub_progress[agent_name] = sub_progress
        elif status == 'starting':
            self.agent_sub_progress[agent_name] = 0.0
        elif status == 'completed':
            self.agent_sub_progress[agent_name] = 1.0
        elif status == 'in_progress' and agent_name not in self.agent_sub_progress:
            self.agent_sub_progress[agent_name] = 0.5  # Default to 50% if not specified

        # Calculate overall progress with sub-progress
        total_progress = 0.0
        for agent, weight in agent_weights.items():
            if self.agent_status.get(agent) == 'completed':
                # Agent completed: add full weight
                total_progress += weight
            elif self.agent_status.get(agent) in ['starting', 'in_progress']:
                # Agent in progress: add partial weight based on sub-progress
                sub_prog = self.agent_sub_progress.get(agent, 0.0)
                total_progress += weight * sub_prog

        progress = min(total_progress, 100.0)  # Cap at 100%

        # Store citations if provided and emit individual citation updates
        if citations:
            if request_id not in self.citations:
                self.citations[request_id] = []
            self.citations[request_id].extend(citations)

            # Emit individual citation updates for real-time display
            for citation in citations:
                await self.emit_citation_update(request_id, agent_name, citation)

        await self.emit_progress(ProgressUpdate(
            stage='analysis',
            agent=agent_name,
            status=status,
            message=message,
            progress_percentage=progress,
            citations=citations or [],
            details=details or {}
        ), request_id)

    async def emit_citation_update(self, request_id: str, agent_name: str, citation: Citation):
        """Emit individual citation update for real-time display."""
        for callback in self.progress_callbacks:
            try:
                await callback({
                    'request_id': request_id,
                    'type': 'citation_update',
                    'agent_id': agent_name,
                    'agent_name': agent_name,
                    'title': citation.title,
                    'url': citation.url,
                    'content': citation.content,
                    'published_date': citation.published_date,
                    'source': citation.source,
                    'relevance_score': citation.relevance_score,
                    'timestamp': datetime.utcnow().isoformat()
                })
            except Exception as e:
                logger.error(f"Error emitting citation: {e}")

    async def emit_progress(self, update: ProgressUpdate, request_id: str):
        """Emit progress update to all registered callbacks."""
        for callback in self.progress_callbacks:
            try:
                await callback({
                    'request_id': request_id,
                    'type': 'agent_progress',
                    'agent_id': update.agent,
                    'agent_name': update.agent,
                    'status': update.status,
                    'data': {
                        'stage': update.stage,
                        'agent': update.agent,
                        'status': update.status,
                        'message': update.message,
                        'progress': update.progress_percentage,
                        'citations': [
                            {
                                'title': c.title,
                                'url': c.url,
                                'content': c.content[:200],  # Truncate for display
                                'source': c.source,
                                'relevance': c.relevance_score
                            } for c in update.citations
                        ],
                        'details': update.details,
                        'timestamp': update.timestamp
                    }
                })
            except Exception as e:
                logger.error(f"Error emitting progress: {e}")

    async def complete_analysis(self, request_id: str, results: Dict[str, Any]):
        """Mark analysis as complete and provide final citations."""
        if request_id not in self.current_analysis:
            return

        all_citations = self.citations.get(request_id, [])

        # Sort citations by relevance
        all_citations.sort(key=lambda x: x.relevance_score, reverse=True)

        await self.emit_progress(ProgressUpdate(
            stage='completion',
            agent='system',
            status='completed',
            message='Analysis complete',
            progress_percentage=100,
            citations=all_citations[:10],  # Top 10 citations
            details={'total_citations': len(all_citations)}
        ), request_id)

        # Clean up
        if request_id in self.current_analysis:
            del self.current_analysis[request_id]
        if request_id in self.citations:
            del self.citations[request_id]

    def extract_tavily_citations(self, tavily_response: Dict) -> List[Citation]:
        """Extract citations from Tavily API response."""
        citations = []

        if 'results' in tavily_response:
            for result in tavily_response.get('results', []):
                citation = Citation(
                    title=result.get('title', 'Untitled'),
                    url=result.get('url', ''),
                    content=result.get('content', result.get('snippet', '')),
                    published_date=result.get('published_date'),
                    source=result.get('source', 'Unknown'),
                    relevance_score=result.get('relevance_score', 0.5)
                )
                citations.append(citation)

        return citations


# Global progress tracker instance
progress_tracker = ProgressTracker()