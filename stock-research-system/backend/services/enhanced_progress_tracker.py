"""
Enhanced Progress Tracking with WebSocket Support
Real-time agent activity, citations, and memory events
"""

from typing import Dict, List, Any, Optional
from datetime import datetime
from dataclasses import dataclass, asdict
import asyncio
import json
import logging
from enum import Enum

logger = logging.getLogger(__name__)


class AgentStatus(Enum):
    """Agent status states"""
    IDLE = "idle"
    ACTIVE = "active"
    THINKING = "thinking"
    SEARCHING = "searching"
    ANALYZING = "analyzing"
    COMPLETED = "completed"
    ERROR = "error"


class EventType(Enum):
    """Progress event types"""
    AGENT_STATUS = "agent_status"
    CITATION_ADDED = "citation_added"
    MEMORY_RECALLED = "memory_recalled"
    PATTERN_DETECTED = "pattern_detected"
    INSIGHT_GENERATED = "insight_generated"
    DELEGATION = "delegation"
    TOOL_CALL = "tool_call"
    DECISION_MADE = "decision_made"
    ERROR = "error"


@dataclass
class ProgressEvent:
    """Single progress event"""
    event_type: EventType
    agent_name: str
    message: str
    timestamp: datetime
    metadata: Dict[str, Any]
    request_id: str


@dataclass
class AgentActivity:
    """Agent activity tracking"""
    agent_name: str
    status: AgentStatus
    current_task: str
    start_time: datetime
    end_time: Optional[datetime] = None
    sub_tasks: List[str] = None
    citations: List[Dict] = None
    confidence: float = 0.5


class EnhancedProgressTracker:
    """Enhanced progress tracking with WebSocket broadcasting"""

    def __init__(self):
        self.active_analyses: Dict[str, Dict] = {}
        self.websocket_connections: Dict[str, Any] = {}
        self.event_history: Dict[str, List[ProgressEvent]] = {}
        self.agent_activities: Dict[str, Dict[str, AgentActivity]] = {}

    async def start_analysis(
        self,
        request_id: str,
        query: str,
        user_id: Optional[str] = None
    ):
        """Start tracking a new analysis"""
        self.active_analyses[request_id] = {
            'query': query,
            'user_id': user_id,
            'start_time': datetime.utcnow(),
            'status': 'active',
            'agents': {}
        }

        self.event_history[request_id] = []
        self.agent_activities[request_id] = {}

        # Broadcast start event
        await self._broadcast_event(
            request_id,
            ProgressEvent(
                event_type=EventType.AGENT_STATUS,
                agent_name="System",
                message=f"Starting analysis: {query[:100]}",
                timestamp=datetime.utcnow(),
                metadata={'query': query},
                request_id=request_id
            )
        )

        logger.info(f"Started tracking analysis {request_id}")

    async def update_agent_status(
        self,
        request_id: str,
        agent_name: str,
        task: str,
        status: str,
        metadata: Optional[Dict] = None
    ):
        """Update agent status and broadcast"""
        if request_id not in self.active_analyses:
            return

        # Update or create agent activity
        if request_id not in self.agent_activities:
            self.agent_activities[request_id] = {}

        if agent_name not in self.agent_activities[request_id]:
            self.agent_activities[request_id][agent_name] = AgentActivity(
                agent_name=agent_name,
                status=AgentStatus(status),
                current_task=task,
                start_time=datetime.utcnow()
            )
        else:
            activity = self.agent_activities[request_id][agent_name]
            activity.status = AgentStatus(status)
            activity.current_task = task

            if status == "completed":
                activity.end_time = datetime.utcnow()

        # Create and broadcast event
        event = ProgressEvent(
            event_type=EventType.AGENT_STATUS,
            agent_name=agent_name,
            message=f"{agent_name}: {task}",
            timestamp=datetime.utcnow(),
            metadata=metadata or {},
            request_id=request_id
        )

        await self._broadcast_event(request_id, event)

    async def add_citation(
        self,
        request_id: str,
        agent_name: str,
        source: str,
        url: str,
        content: str,
        confidence: float = 0.8
    ):
        """Add and broadcast citation"""
        citation = {
            'source': source,
            'url': url,
            'content': content[:200],  # Truncate for display
            'confidence': confidence,
            'timestamp': datetime.utcnow().isoformat(),
            'agent': agent_name
        }

        # Store citation with agent
        if request_id in self.agent_activities and agent_name in self.agent_activities[request_id]:
            activity = self.agent_activities[request_id][agent_name]
            if activity.citations is None:
                activity.citations = []
            activity.citations.append(citation)

        # Broadcast citation event
        event = ProgressEvent(
            event_type=EventType.CITATION_ADDED,
            agent_name=agent_name,
            message=f"Citation from {source}",
            timestamp=datetime.utcnow(),
            metadata=citation,
            request_id=request_id
        )

        await self._broadcast_event(request_id, event)

    async def memory_recalled(
        self,
        request_id: str,
        agent_name: str,
        memory_content: str,
        relevance: float
    ):
        """Broadcast memory recall event"""
        event = ProgressEvent(
            event_type=EventType.MEMORY_RECALLED,
            agent_name=agent_name,
            message=f"Recalled: {memory_content[:100]}...",
            timestamp=datetime.utcnow(),
            metadata={
                'memory': memory_content,
                'relevance': relevance
            },
            request_id=request_id
        )

        await self._broadcast_event(request_id, event)

    async def pattern_detected(
        self,
        request_id: str,
        pattern_type: str,
        description: str,
        confidence: float
    ):
        """Broadcast pattern detection"""
        event = ProgressEvent(
            event_type=EventType.PATTERN_DETECTED,
            agent_name="Pattern Recognition",
            message=f"Pattern detected: {pattern_type}",
            timestamp=datetime.utcnow(),
            metadata={
                'pattern_type': pattern_type,
                'description': description,
                'confidence': confidence
            },
            request_id=request_id
        )

        await self._broadcast_event(request_id, event)

    async def insight_generated(
        self,
        request_id: str,
        agent_name: str,
        insight: str,
        importance: float = 0.5
    ):
        """Broadcast insight generation"""
        event = ProgressEvent(
            event_type=EventType.INSIGHT_GENERATED,
            agent_name=agent_name,
            message=insight[:200],
            timestamp=datetime.utcnow(),
            metadata={
                'insight': insight,
                'importance': importance
            },
            request_id=request_id
        )

        await self._broadcast_event(request_id, event)

    async def delegation_event(
        self,
        request_id: str,
        from_agent: str,
        to_agent: str,
        task: str
    ):
        """Broadcast delegation event"""
        event = ProgressEvent(
            event_type=EventType.DELEGATION,
            agent_name=from_agent,
            message=f"{from_agent} → {to_agent}: {task}",
            timestamp=datetime.utcnow(),
            metadata={
                'from': from_agent,
                'to': to_agent,
                'task': task
            },
            request_id=request_id
        )

        await self._broadcast_event(request_id, event)

    async def tool_call(
        self,
        request_id: str,
        agent_name: str,
        tool_name: str,
        parameters: Dict
    ):
        """Broadcast tool usage"""
        event = ProgressEvent(
            event_type=EventType.TOOL_CALL,
            agent_name=agent_name,
            message=f"{agent_name} using {tool_name}",
            timestamp=datetime.utcnow(),
            metadata={
                'tool': tool_name,
                'parameters': parameters
            },
            request_id=request_id
        )

        await self._broadcast_event(request_id, event)

    async def decision_made(
        self,
        request_id: str,
        agent_name: str,
        decision: str,
        reasoning: str
    ):
        """Broadcast decision event"""
        event = ProgressEvent(
            event_type=EventType.DECISION_MADE,
            agent_name=agent_name,
            message=f"Decision: {decision[:100]}",
            timestamp=datetime.utcnow(),
            metadata={
                'decision': decision,
                'reasoning': reasoning
            },
            request_id=request_id
        )

        await self._broadcast_event(request_id, event)

    async def error_event(
        self,
        request_id: str,
        agent_name: str,
        error: str,
        recoverable: bool = True
    ):
        """Broadcast error event"""
        event = ProgressEvent(
            event_type=EventType.ERROR,
            agent_name=agent_name,
            message=f"Error: {error[:100]}",
            timestamp=datetime.utcnow(),
            metadata={
                'error': error,
                'recoverable': recoverable
            },
            request_id=request_id
        )

        await self._broadcast_event(request_id, event)

    async def complete_analysis(
        self,
        request_id: str,
        final_report: Dict
    ):
        """Complete analysis tracking"""
        if request_id not in self.active_analyses:
            return

        analysis = self.active_analyses[request_id]
        analysis['status'] = 'completed'
        analysis['end_time'] = datetime.utcnow()
        analysis['duration'] = (analysis['end_time'] - analysis['start_time']).total_seconds()
        analysis['final_report'] = final_report

        # Broadcast completion
        event = ProgressEvent(
            event_type=EventType.AGENT_STATUS,
            agent_name="System",
            message="Analysis completed",
            timestamp=datetime.utcnow(),
            metadata={
                'duration': analysis['duration'],
                'confidence': final_report.get('confidence_score', 0)
            },
            request_id=request_id
        )

        await self._broadcast_event(request_id, event)

        # Clean up after delay
        asyncio.create_task(self._cleanup_analysis(request_id))

    async def _cleanup_analysis(self, request_id: str, delay: int = 300):
        """Clean up analysis data after delay"""
        await asyncio.sleep(delay)

        if request_id in self.active_analyses:
            del self.active_analyses[request_id]
        if request_id in self.event_history:
            del self.event_history[request_id]
        if request_id in self.agent_activities:
            del self.agent_activities[request_id]

        logger.info(f"Cleaned up analysis {request_id}")

    async def register_websocket(self, request_id: str, websocket):
        """Register WebSocket connection for updates"""
        if request_id not in self.websocket_connections:
            self.websocket_connections[request_id] = []

        self.websocket_connections[request_id].append(websocket)
        logger.info(f"Registered WebSocket for {request_id}")

        # Send current state
        await self._send_current_state(request_id, websocket)

    async def unregister_websocket(self, request_id: str, websocket):
        """Unregister WebSocket connection"""
        if request_id in self.websocket_connections:
            if websocket in self.websocket_connections[request_id]:
                self.websocket_connections[request_id].remove(websocket)

            if not self.websocket_connections[request_id]:
                del self.websocket_connections[request_id]

        logger.info(f"Unregistered WebSocket for {request_id}")

    async def _send_current_state(self, request_id: str, websocket):
        """Send current state to newly connected WebSocket"""
        if request_id not in self.active_analyses:
            return

        # Send analysis info
        analysis = self.active_analyses[request_id]
        await self._send_to_websocket(websocket, {
            'type': 'state_sync',
            'analysis': {
                'query': analysis['query'],
                'status': analysis['status'],
                'start_time': analysis['start_time'].isoformat()
            }
        })

        # Send agent activities
        if request_id in self.agent_activities:
            activities = []
            for agent_name, activity in self.agent_activities[request_id].items():
                activities.append({
                    'agent': agent_name,
                    'status': activity.status.value,
                    'task': activity.current_task,
                    'citations': len(activity.citations) if activity.citations else 0
                })

            await self._send_to_websocket(websocket, {
                'type': 'agents_update',
                'agents': activities
            })

        # Send recent events
        if request_id in self.event_history:
            recent_events = self.event_history[request_id][-20:]  # Last 20 events
            for event in recent_events:
                await self._send_to_websocket(websocket, self._event_to_dict(event))

    async def _broadcast_event(self, request_id: str, event: ProgressEvent):
        """Broadcast event to all connected WebSockets"""
        # Store in history
        if request_id not in self.event_history:
            self.event_history[request_id] = []
        self.event_history[request_id].append(event)

        # Broadcast to WebSockets
        if request_id in self.websocket_connections:
            event_dict = self._event_to_dict(event)

            # Send to all connections
            disconnected = []
            for websocket in self.websocket_connections[request_id]:
                try:
                    await self._send_to_websocket(websocket, event_dict)
                except Exception as e:
                    logger.error(f"WebSocket send error: {e}")
                    disconnected.append(websocket)

            # Clean up disconnected
            for ws in disconnected:
                await self.unregister_websocket(request_id, ws)

    async def _send_to_websocket(self, websocket, data: Dict):
        """Send data to WebSocket"""
        try:
            await websocket.send_json(data)
        except Exception as e:
            logger.error(f"Failed to send to WebSocket: {e}")
            raise

    def _event_to_dict(self, event: ProgressEvent) -> Dict:
        """Convert event to dictionary for WebSocket"""
        return {
            'type': event.event_type.value,
            'agent': event.agent_name,
            'message': event.message,
            'timestamp': event.timestamp.isoformat(),
            'metadata': event.metadata
        }

    def get_analysis_status(self, request_id: str) -> Optional[Dict]:
        """Get current analysis status"""
        if request_id not in self.active_analyses:
            return None

        analysis = self.active_analyses[request_id]
        agents = []

        if request_id in self.agent_activities:
            for agent_name, activity in self.agent_activities[request_id].items():
                agents.append({
                    'name': agent_name,
                    'status': activity.status.value,
                    'task': activity.current_task,
                    'duration': (
                        (activity.end_time or datetime.utcnow()) - activity.start_time
                    ).total_seconds()
                })

        return {
            'query': analysis['query'],
            'status': analysis['status'],
            'start_time': analysis['start_time'].isoformat(),
            'agents': agents,
            'event_count': len(self.event_history.get(request_id, []))
        }

    def get_event_history(
        self,
        request_id: str,
        event_type: Optional[EventType] = None,
        limit: int = 100
    ) -> List[Dict]:
        """Get event history for analysis"""
        if request_id not in self.event_history:
            return []

        events = self.event_history[request_id]

        if event_type:
            events = [e for e in events if e.event_type == event_type]

        # Return last N events
        return [self._event_to_dict(e) for e in events[-limit:]]


# Global instance
enhanced_progress_tracker = EnhancedProgressTracker()