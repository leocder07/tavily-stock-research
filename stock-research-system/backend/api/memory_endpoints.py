"""
API Endpoints for Memory System and Progress Tracking
"""

from fastapi import APIRouter, HTTPException, WebSocket, WebSocketDisconnect
from typing import Dict, List, Any, Optional
from datetime import datetime
import logging

from memory.memory_persistence import MemoryPersistenceService
from memory.agent_memory import SharedMemory, MemoryEntry
from services.enhanced_progress_tracker import enhanced_progress_tracker
from services.mongodb_connection import mongodb_connection

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api", tags=["memory", "progress"])

# Initialize services lazily
memory_persistence = None
shared_memory = None

def get_services():
    """Get or initialize services"""
    global memory_persistence, shared_memory
    if memory_persistence is None:
        db = mongodb_connection.get_database(async_mode=True)
        memory_persistence = MemoryPersistenceService(db)
        shared_memory = SharedMemory()
    return memory_persistence, shared_memory


@router.get("/memory/entries")
async def get_memory_entries(
    request_id: Optional[str] = None,
    agent_name: Optional[str] = None,
    memory_type: Optional[str] = None,
    limit: int = 100
) -> Dict[str, Any]:
    """Get memory entries with filters"""
    memory_persistence, shared_memory = get_services()
    try:
        if agent_name:
            memories = await memory_persistence.load_recent_memories(
                agent_name=agent_name,
                limit=limit,
                memory_type=memory_type
            )
        else:
            # Get all memories for request
            memories = []
            for agent in await _get_active_agents():
                agent_memories = await memory_persistence.load_recent_memories(
                    agent_name=agent,
                    limit=20,
                    memory_type=memory_type
                )
                memories.extend(agent_memories)

        return {
            "memories": [
                {
                    "id": str(hash(m.content + str(m.timestamp))),
                    "agent": m.agent_name,
                    "type": m.memory_type,
                    "content": m.content,
                    "timestamp": m.timestamp.isoformat(),
                    "importance": m.importance_score,
                    "accessCount": m.access_count,
                    "context": m.context
                }
                for m in memories
            ]
        }
    except Exception as e:
        logger.error(f"Error fetching memories: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/memory/patterns")
async def get_patterns(
    min_confidence: float = 0.6,
    min_discoveries: int = 2
) -> Dict[str, Any]:
    """Get discovered patterns"""
    memory_persistence, shared_memory = get_services()
    try:
        patterns = await memory_persistence.get_reliable_patterns(
            min_discoveries=min_discoveries,
            min_confidence=min_confidence
        )

        return {
            "patterns": [
                {
                    "id": p.get("_id", ""),
                    "type": p.get("type", ""),
                    "description": p.get("description", ""),
                    "confidence": p.get("confidence", 0),
                    "discoveries": p.get("discovery_count", 0),
                    "lastSeen": p.get("last_seen", datetime.utcnow()).isoformat()
                }
                for p in patterns
            ]
        }
    except Exception as e:
        logger.error(f"Error fetching patterns: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/memory/insights/{symbol}")
async def get_symbol_insights(
    symbol: str,
    limit: int = 20,
    min_relevance: float = 0.5
) -> Dict[str, Any]:
    """Get insights for a specific symbol"""
    memory_persistence, shared_memory = get_services()
    try:
        insights = await memory_persistence.get_symbol_insights(
            symbol=symbol,
            limit=limit,
            min_relevance=min_relevance
        )

        # Also get from shared memory
        shared_insights = shared_memory.get_symbol_insights(symbol)

        combined_insights = []

        # From database
        for insight in insights:
            combined_insights.append({
                "id": insight.get("_id", ""),
                "symbol": symbol,
                "content": str(insight.get("insight", "")),
                "importance": insight.get("relevance_score", 0.5),
                "agent": insight.get("agent_name", ""),
                "timestamp": insight.get("timestamp", datetime.utcnow()).isoformat()
            })

        # From shared memory
        for idx, insight in enumerate(shared_insights[:5]):  # Limit to 5 from memory
            combined_insights.append({
                "id": f"shared_{idx}",
                "symbol": symbol,
                "content": str(insight),
                "importance": 0.7,
                "agent": "SharedMemory",
                "timestamp": datetime.utcnow().isoformat()
            })

        return {"insights": combined_insights}
    except Exception as e:
        logger.error(f"Error fetching insights for {symbol}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/memory/search")
async def search_memories(
    query: str,
    agent_name: Optional[str] = None,
    limit: int = 10
) -> Dict[str, Any]:
    """Search memories semantically"""
    memory_persistence, shared_memory = get_services()
    try:
        memories = await memory_persistence.search_memories(
            query=query,
            agent_name=agent_name,
            limit=limit
        )

        return {
            "results": [
                {
                    "content": m.content,
                    "agent": m.agent_name,
                    "type": m.memory_type,
                    "importance": m.importance_score,
                    "timestamp": m.timestamp.isoformat(),
                    "context": m.context
                }
                for m in memories
            ]
        }
    except Exception as e:
        logger.error(f"Error searching memories: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/progress/status/{request_id}")
async def get_analysis_status(request_id: str) -> Dict[str, Any]:
    """Get current analysis status"""
    try:
        status = enhanced_progress_tracker.get_analysis_status(request_id)
        if not status:
            raise HTTPException(status_code=404, detail="Analysis not found")

        return status
    except Exception as e:
        logger.error(f"Error fetching analysis status: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/progress/events/{request_id}")
async def get_progress_events(
    request_id: str,
    event_type: Optional[str] = None,
    limit: int = 100
) -> Dict[str, Any]:
    """Get progress events for analysis"""
    try:
        events = enhanced_progress_tracker.get_event_history(
            request_id=request_id,
            event_type=event_type,
            limit=limit
        )

        return {"events": events}
    except Exception as e:
        logger.error(f"Error fetching progress events: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.websocket("/ws/{request_id}")
async def websocket_endpoint(websocket: WebSocket, request_id: str):
    """WebSocket endpoint for real-time progress updates"""
    await websocket.accept()

    try:
        # Register WebSocket connection
        await enhanced_progress_tracker.register_websocket(request_id, websocket)

        # Keep connection alive
        while True:
            # Wait for any message from client (ping/pong)
            await websocket.receive_text()

    except WebSocketDisconnect:
        # Unregister on disconnect
        await enhanced_progress_tracker.unregister_websocket(request_id, websocket)
        logger.info(f"WebSocket disconnected for {request_id}")
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
        await enhanced_progress_tracker.unregister_websocket(request_id, websocket)


@router.get("/agents/performance/{agent_name}")
async def get_agent_performance(
    agent_name: str,
    days_back: int = 7
) -> Dict[str, Any]:
    """Get agent performance metrics"""
    memory_persistence, shared_memory = get_services()
    try:
        performance = await memory_persistence.get_agent_performance(
            agent_name=agent_name,
            days_back=days_back
        )

        return performance
    except Exception as e:
        logger.error(f"Error fetching agent performance: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/agents/knowledge/{agent_name}")
async def export_agent_knowledge(agent_name: str) -> Dict[str, Any]:
    """Export all knowledge for an agent"""
    memory_persistence, shared_memory = get_services()
    try:
        knowledge = await memory_persistence.export_agent_knowledge(agent_name)
        return knowledge
    except Exception as e:
        logger.error(f"Error exporting agent knowledge: {e}")
        raise HTTPException(status_code=500, detail=str(e))


async def _get_active_agents() -> List[str]:
    """Get list of active agents"""
    return [
        "CEO",
        "Research_Leader",
        "Analysis_Leader",
        "Strategy_Leader",
        "Market_Data_Specialist",
        "News_Analyst",
        "Sentiment_Researcher",
        "Technical_Analyst",
        "Fundamental_Analyst",
        "Portfolio_Strategist"
    ]