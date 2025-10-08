"""
Server-Sent Events (SSE) Endpoints for Real-time Analysis Progress
Provides streaming updates without WebSocket complexity
"""

import asyncio
import logging
from typing import AsyncGenerator
from datetime import datetime
from fastapi import APIRouter, Request
from fastapi.responses import StreamingResponse
from sse_starlette.sse import EventSourceResponse
import json

from services.mongodb_connection import mongodb_connection

logger = logging.getLogger(__name__)
router = APIRouter()


class SSEProgressTracker:
    """
    Manages SSE connections for real-time progress updates
    """

    def __init__(self, database):
        self.database = database
        self.active_connections = {}

    async def stream_progress(self, analysis_id: str) -> AsyncGenerator[dict, None]:
        """
        Stream progress updates for a specific analysis

        Args:
            analysis_id: Analysis document ID

        Yields:
            SSE events with progress updates
        """
        try:
            last_update_time = None
            completed = False

            while not completed:
                # Fetch latest progress from MongoDB
                analysis = await self.database['analyses'].find_one({"id": analysis_id})

                if not analysis:
                    yield {
                        "event": "error",
                        "data": json.dumps({
                            "error": "Analysis not found",
                            "analysis_id": analysis_id
                        })
                    }
                    break

                # Get progress data
                progress = analysis.get('progress', {})
                status = analysis.get('status', 'pending')
                active_agent = analysis.get('active_agent')
                agent_executions = analysis.get('agent_executions', [])

                # Check if we have new data
                current_update = progress.get('updated_at')

                if current_update != last_update_time:
                    # Send progress update
                    yield {
                        "event": "progress",
                        "data": json.dumps({
                            "analysis_id": analysis_id,
                            "percentage": progress.get('percentage', 0),
                            "message": progress.get('message', 'Processing...'),
                            "status": status,
                            "active_agent": active_agent,
                            "completed_agents": len([e for e in agent_executions if e.get('status') == 'COMPLETED']),
                            "total_agents": len(agent_executions),
                            "timestamp": current_update or datetime.utcnow().isoformat()
                        })
                    }

                    last_update_time = current_update

                # Send agent execution updates
                for execution in agent_executions:
                    if execution.get('status') == 'COMPLETED' and not execution.get('sent_sse'):
                        yield {
                            "event": "agent_complete",
                            "data": json.dumps({
                                "analysis_id": analysis_id,
                                "agent": execution.get('agent'),
                                "duration": (execution.get('end_time') - execution.get('start_time')).total_seconds() if execution.get('end_time') and execution.get('start_time') else 0,
                                "timestamp": execution.get('end_time', datetime.utcnow()).isoformat()
                            })
                        }

                        # Mark as sent to avoid duplicates
                        await self.database['analyses'].update_one(
                            {"id": analysis_id, "agent_executions.agent": execution['agent']},
                            {"$set": {"agent_executions.$.sent_sse": True}}
                        )

                # Check if completed
                if status in ['completed', 'failed']:
                    # Send final result
                    result = await self.database['analysis_results'].find_one({"analysis_id": analysis_id})

                    yield {
                        "event": "complete" if status == 'completed' else "error",
                        "data": json.dumps({
                            "analysis_id": analysis_id,
                            "status": status,
                            "recommendation": result.get('recommendations', {}).get('action') if result else None,
                            "confidence": result.get('recommendations', {}).get('confidence') if result else None,
                            "timestamp": datetime.utcnow().isoformat()
                        })
                    }

                    completed = True
                    break

                # Poll every 500ms
                await asyncio.sleep(0.5)

        except Exception as e:
            logger.error(f"[SSEProgressTracker] Error streaming progress: {e}", exc_info=True)
            yield {
                "event": "error",
                "data": json.dumps({
                    "error": str(e),
                    "analysis_id": analysis_id
                })
            }


# Global SSE tracker instance
sse_tracker = None


def get_sse_tracker(database):
    """Get or create SSE tracker instance"""
    global sse_tracker
    if sse_tracker is None:
        sse_tracker = SSEProgressTracker(database)
    return sse_tracker


@router.get("/api/v1/analysis/{analysis_id}/stream")
async def stream_analysis_progress(analysis_id: str, request: Request):
    """
    Stream real-time progress updates for an analysis using SSE

    Args:
        analysis_id: Analysis document ID
        request: FastAPI request object (for client disconnect detection)

    Returns:
        StreamingResponse with SSE events

    Events:
        - progress: Progress percentage and status updates
        - agent_complete: Individual agent completion notifications
        - complete: Final analysis completion
        - error: Error notifications
    """
    database = await get_database()
    tracker = get_sse_tracker(database)

    async def event_generator():
        """Generate SSE events"""
        try:
            async for event in tracker.stream_progress(analysis_id):
                # Check if client disconnected
                if await request.is_disconnected():
                    logger.info(f"[SSE] Client disconnected for analysis {analysis_id}")
                    break

                yield event
        except Exception as e:
            logger.error(f"[SSE] Error in event generator: {e}", exc_info=True)
            yield {
                "event": "error",
                "data": json.dumps({"error": str(e)})
            }

    return EventSourceResponse(event_generator())


@router.get("/api/v1/analysis/{analysis_id}/cost-stream")
async def stream_cost_metrics(analysis_id: str, request: Request):
    """
    Stream real-time cost optimization metrics during analysis

    Args:
        analysis_id: Analysis document ID
        request: FastAPI request object

    Returns:
        StreamingResponse with cost metric events
    """
    from services.tavily_cache import get_tavily_cache
    from services.smart_model_router import get_smart_router

    async def cost_event_generator():
        """Generate cost metric events"""
        try:
            cache = get_tavily_cache()
            router = get_smart_router()

            last_cache_hits = 0
            last_gpt35_calls = 0

            while True:
                # Check if analysis completed
                database = await get_database()
                analysis = await database['analyses'].find_one({"id": analysis_id})

                if not analysis:
                    break

                status = analysis.get('status', 'pending')

                # Get current metrics
                cache_stats = await cache.get_stats() if cache else {}
                router_stats = router.get_stats() if router else {}

                # Calculate incremental changes
                current_cache_hits = cache_stats.get('hits', 0)
                current_gpt35_calls = router_stats.get('gpt35_calls', 0)

                if current_cache_hits != last_cache_hits or current_gpt35_calls != last_gpt35_calls:
                    yield {
                        "event": "cost_update",
                        "data": json.dumps({
                            "analysis_id": analysis_id,
                            "cache_hits": current_cache_hits,
                            "cache_hit_rate": cache_stats.get('hit_rate', 0),
                            "cost_saved": cache_stats.get('cost_saved', 0) + router_stats.get('cost_saved', 0),
                            "gpt35_usage": router_stats.get('gpt35_calls', 0) / max(router_stats.get('total_calls', 1), 1),
                            "timestamp": datetime.utcnow().isoformat()
                        })
                    }

                    last_cache_hits = current_cache_hits
                    last_gpt35_calls = current_gpt35_calls

                # Check if analysis completed
                if status in ['completed', 'failed']:
                    yield {
                        "event": "cost_final",
                        "data": json.dumps({
                            "analysis_id": analysis_id,
                            "total_saved": cache_stats.get('cost_saved', 0) + router_stats.get('cost_saved', 0),
                            "cache_hit_rate": cache_stats.get('hit_rate', 0),
                            "gpt35_usage": router_stats.get('gpt35_calls', 0) / max(router_stats.get('total_calls', 1), 1),
                            "timestamp": datetime.utcnow().isoformat()
                        })
                    }
                    break

                # Check for client disconnect
                if await request.is_disconnected():
                    logger.info(f"[SSE Cost] Client disconnected for analysis {analysis_id}")
                    break

                # Poll every second
                await asyncio.sleep(1)

        except Exception as e:
            logger.error(f"[SSE Cost] Error in cost stream: {e}", exc_info=True)
            yield {
                "event": "error",
                "data": json.dumps({"error": str(e)})
            }

    return EventSourceResponse(cost_event_generator())


@router.get("/api/v1/analysis/{analysis_id}/agent-dag")
async def get_agent_dag(analysis_id: str):
    """
    Get agent execution DAG for visualization

    Args:
        analysis_id: Analysis document ID

    Returns:
        DAG structure with nodes (agents) and edges (dependencies)
    """
    database = await get_database()
    analysis = await database['analyses'].find_one({"id": analysis_id})

    if not analysis:
        return {"error": "Analysis not found"}

    agent_executions = analysis.get('agent_executions', [])

    # Build DAG structure
    nodes = []
    edges = []

    # Define agent hierarchy
    agent_hierarchy = {
        'ExpertFundamentalAgent': {'level': 1, 'group': 'base_analysis'},
        'ExpertTechnicalAgent': {'level': 1, 'group': 'base_analysis'},
        'ExpertRiskAgent': {'level': 1, 'group': 'base_analysis'},
        'ExpertSynthesisAgent': {'level': 2, 'group': 'base_analysis'},
        'TavilyNewsIntelligenceAgent': {'level': 3, 'group': 'intelligence'},
        'TavilySentimentTrackerAgent': {'level': 3, 'group': 'intelligence'},
        'MacroContextAgent': {'level': 3, 'group': 'intelligence'},
        'HybridOrchestrator': {'level': 4, 'group': 'synthesis'}
    }

    for execution in agent_executions:
        agent_name = execution.get('agent')
        status = execution.get('status', 'PENDING')

        hierarchy = agent_hierarchy.get(agent_name, {'level': 0, 'group': 'unknown'})

        nodes.append({
            'id': agent_name,
            'label': agent_name,
            'status': status,
            'level': hierarchy['level'],
            'group': hierarchy['group'],
            'start_time': execution.get('start_time', datetime.utcnow()).isoformat() if execution.get('start_time') else None,
            'end_time': execution.get('end_time', datetime.utcnow()).isoformat() if execution.get('end_time') else None,
            'duration': (execution.get('end_time') - execution.get('start_time')).total_seconds() if execution.get('end_time') and execution.get('start_time') else None
        })

    # Define edges (dependencies)
    # Fundamental, Technical, Risk → Synthesis
    for agent in ['ExpertFundamentalAgent', 'ExpertTechnicalAgent', 'ExpertRiskAgent']:
        edges.append({
            'from': agent,
            'to': 'ExpertSynthesisAgent',
            'type': 'sequential'
        })

    # Synthesis → Intelligence agents
    for agent in ['TavilyNewsIntelligenceAgent', 'TavilySentimentTrackerAgent', 'MacroContextAgent']:
        edges.append({
            'from': 'ExpertSynthesisAgent',
            'to': agent,
            'type': 'parallel'
        })

    # Intelligence agents → Hybrid Orchestrator
    for agent in ['TavilyNewsIntelligenceAgent', 'TavilySentimentTrackerAgent', 'MacroContextAgent']:
        edges.append({
            'from': agent,
            'to': 'HybridOrchestrator',
            'type': 'convergence'
        })

    return {
        "analysis_id": analysis_id,
        "dag": {
            "nodes": nodes,
            "edges": edges
        },
        "metadata": {
            "total_agents": len(nodes),
            "completed": len([n for n in nodes if n['status'] == 'COMPLETED']),
            "failed": len([n for n in nodes if n['status'] == 'FAILED']),
            "running": len([n for n in nodes if n['status'] == 'RUNNING'])
        }
    }
