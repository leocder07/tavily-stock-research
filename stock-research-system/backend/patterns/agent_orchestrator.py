"""
AI Agent Orchestration System with Advanced Design Patterns
Implements Blackboard, Coordinator, Mediator, and Observer patterns
"""

import asyncio
import logging
from typing import Dict, Any, List, Optional, Callable, Set
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
import uuid
from collections import defaultdict
import json

logger = logging.getLogger(__name__)


# ================== Core Agent Patterns ==================

class AgentMessage:
    """Message structure for inter-agent communication"""

    def __init__(self,
                 sender: str,
                 receiver: str,
                 message_type: str,
                 content: Any,
                 correlation_id: str = None,
                 priority: int = 0):
        self.sender = sender
        self.receiver = receiver
        self.message_type = message_type
        self.content = content
        self.correlation_id = correlation_id or str(uuid.uuid4())
        self.priority = priority
        self.timestamp = datetime.utcnow()


class AgentState(Enum):
    """Agent lifecycle states"""
    IDLE = "idle"
    PROCESSING = "processing"
    WAITING = "waiting"
    COMPLETED = "completed"
    FAILED = "failed"
    SUSPENDED = "suspended"


class AgentCapability(Enum):
    """Agent capabilities for dynamic discovery"""
    MARKET_DATA = "market_data"
    FUNDAMENTAL_ANALYSIS = "fundamental_analysis"
    TECHNICAL_ANALYSIS = "technical_analysis"
    SENTIMENT_ANALYSIS = "sentiment_analysis"
    RISK_ASSESSMENT = "risk_assessment"
    SYNTHESIS = "synthesis"
    VALIDATION = "validation"


@dataclass
class AgentProfile:
    """Agent metadata and capabilities"""
    agent_id: str
    name: str
    capabilities: Set[AgentCapability]
    priority: int = 0
    max_concurrent_tasks: int = 5
    timeout: int = 30
    retry_policy: Dict[str, Any] = field(default_factory=dict)


# ================== Blackboard Pattern ==================

class Blackboard:
    """
    Shared knowledge base for agent coordination
    Implements the Blackboard architectural pattern
    """

    def __init__(self):
        self._knowledge_base = {}
        self._subscribers = defaultdict(list)
        self._locks = defaultdict(asyncio.Lock)
        self._version_control = defaultdict(int)

    async def write(self, key: str, value: Any, agent_id: str):
        """Write data to blackboard with versioning"""
        async with self._locks[key]:
            old_value = self._knowledge_base.get(key)
            self._knowledge_base[key] = value
            self._version_control[key] += 1

            # Notify subscribers
            await self._notify_subscribers(key, value, old_value, agent_id)

            logger.debug(f"Agent {agent_id} wrote to blackboard: {key} (v{self._version_control[key]})")

    async def read(self, key: str) -> Any:
        """Read data from blackboard"""
        async with self._locks[key]:
            return self._knowledge_base.get(key)

    async def subscribe(self, key: str, callback: Callable):
        """Subscribe to changes for a specific key"""
        self._subscribers[key].append(callback)

    async def _notify_subscribers(self, key: str, new_value: Any, old_value: Any, agent_id: str):
        """Notify all subscribers of a key change"""
        for callback in self._subscribers[key]:
            try:
                await callback(key, new_value, old_value, agent_id)
            except Exception as e:
                logger.error(f"Error notifying subscriber for {key}: {e}")

    def get_snapshot(self) -> Dict[str, Any]:
        """Get complete snapshot of blackboard state"""
        return {
            'knowledge': dict(self._knowledge_base),
            'versions': dict(self._version_control),
            'timestamp': datetime.utcnow().isoformat()
        }


# ================== Agent Base Class ==================

class BaseAgent(ABC):
    """
    Abstract base class for all agents
    Implements Strategy pattern for agent behaviors
    """

    def __init__(self, profile: AgentProfile, blackboard: Blackboard):
        self.profile = profile
        self.blackboard = blackboard
        self.state = AgentState.IDLE
        self.current_tasks = []
        self.message_queue = asyncio.Queue()
        self._execution_strategy = None

    @abstractmethod
    async def process(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """Process a task - must be implemented by subclasses"""
        pass

    async def execute(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """Execute task with state management"""
        try:
            self.state = AgentState.PROCESSING
            result = await self.process(task)
            self.state = AgentState.COMPLETED
            return result
        except Exception as e:
            self.state = AgentState.FAILED
            logger.error(f"Agent {self.profile.agent_id} failed: {e}")
            raise

    async def receive_message(self, message: AgentMessage):
        """Receive message from other agents"""
        await self.message_queue.put(message)

    async def send_message(self, receiver: str, message_type: str, content: Any):
        """Send message to another agent"""
        message = AgentMessage(
            sender=self.profile.agent_id,
            receiver=receiver,
            message_type=message_type,
            content=content
        )
        return message


# ================== Mediator Pattern ==================

class AgentMediator:
    """
    Mediates communication between agents
    Implements the Mediator pattern for decoupled communication
    """

    def __init__(self):
        self.agents: Dict[str, BaseAgent] = {}
        self.message_log = []
        self.routing_rules = {}

    def register_agent(self, agent: BaseAgent):
        """Register an agent with the mediator"""
        self.agents[agent.profile.agent_id] = agent
        logger.info(f"Registered agent: {agent.profile.name}")

    async def send_message(self, message: AgentMessage):
        """Route message between agents"""
        self.message_log.append(message)

        if message.receiver in self.agents:
            await self.agents[message.receiver].receive_message(message)
        elif message.receiver == "broadcast":
            # Broadcast to all agents
            for agent in self.agents.values():
                if agent.profile.agent_id != message.sender:
                    await agent.receive_message(message)
        else:
            logger.warning(f"Unknown receiver: {message.receiver}")

    def add_routing_rule(self, pattern: str, handler: Callable):
        """Add custom routing rule"""
        self.routing_rules[pattern] = handler


# ================== Coordinator Pattern ==================

class AgentCoordinator:
    """
    Coordinates agent execution using various strategies
    Implements the Coordinator pattern for agent orchestration
    """

    def __init__(self, blackboard: Blackboard, mediator: AgentMediator):
        self.blackboard = blackboard
        self.mediator = mediator
        self.agents = {}
        self.workflows = {}
        self.execution_plans = []

    def register_agent(self, agent: BaseAgent):
        """Register agent with coordinator"""
        self.agents[agent.profile.agent_id] = agent
        self.mediator.register_agent(agent)

    async def execute_parallel(self,
                              tasks: List[Dict[str, Any]],
                              agents: List[str] = None) -> List[Dict[str, Any]]:
        """Execute tasks in parallel across agents"""
        if agents is None:
            agents = list(self.agents.keys())

        # Distribute tasks among agents
        agent_tasks = self._distribute_tasks(tasks, agents)

        # Execute in parallel
        coroutines = []
        for agent_id, agent_task_list in agent_tasks.items():
            agent = self.agents[agent_id]
            for task in agent_task_list:
                coroutines.append(agent.execute(task))

        results = await asyncio.gather(*coroutines, return_exceptions=True)

        # Process results
        processed_results = []
        for result in results:
            if isinstance(result, Exception):
                processed_results.append({
                    'status': 'failed',
                    'error': str(result)
                })
            else:
                processed_results.append(result)

        return processed_results

    async def execute_sequential(self,
                                tasks: List[Dict[str, Any]],
                                agents: List[str]) -> List[Dict[str, Any]]:
        """Execute tasks sequentially with data passing"""
        results = []
        context = {}

        for task, agent_id in zip(tasks, agents):
            agent = self.agents[agent_id]

            # Pass context from previous executions
            task['context'] = context

            result = await agent.execute(task)
            results.append(result)

            # Update context for next agent
            context.update(result)

        return results

    async def execute_pipeline(self,
                              stages: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Execute multi-stage pipeline with dependencies"""
        pipeline_state = {}

        for stage in stages:
            stage_name = stage['name']
            dependencies = stage.get('dependencies', [])
            agent_id = stage['agent']
            task = stage['task']

            # Wait for dependencies
            for dep in dependencies:
                while dep not in pipeline_state:
                    await asyncio.sleep(0.1)

            # Add dependency results to task
            task['dependencies'] = {
                dep: pipeline_state[dep]
                for dep in dependencies
            }

            # Execute stage
            agent = self.agents[agent_id]
            result = await agent.execute(task)
            pipeline_state[stage_name] = result

        return pipeline_state

    def _distribute_tasks(self,
                         tasks: List[Dict[str, Any]],
                         agents: List[str]) -> Dict[str, List]:
        """Distribute tasks among agents based on load"""
        agent_tasks = defaultdict(list)

        # Simple round-robin distribution
        for i, task in enumerate(tasks):
            agent_id = agents[i % len(agents)]
            agent_tasks[agent_id].append(task)

        return agent_tasks


# ================== Observer Pattern ==================

class EventType(Enum):
    """Event types for observer pattern"""
    AGENT_STARTED = "agent_started"
    AGENT_COMPLETED = "agent_completed"
    AGENT_FAILED = "agent_failed"
    DATA_UPDATED = "data_updated"
    WORKFLOW_STARTED = "workflow_started"
    WORKFLOW_COMPLETED = "workflow_completed"


class EventBus:
    """
    Event bus for publish-subscribe pattern
    Implements Observer pattern for loose coupling
    """

    def __init__(self):
        self.subscribers = defaultdict(list)
        self.event_log = []

    def subscribe(self, event_type: EventType, callback: Callable):
        """Subscribe to an event type"""
        self.subscribers[event_type].append(callback)

    async def publish(self, event_type: EventType, data: Any):
        """Publish an event to all subscribers"""
        event = {
            'type': event_type,
            'data': data,
            'timestamp': datetime.utcnow()
        }
        self.event_log.append(event)

        # Notify all subscribers
        for callback in self.subscribers[event_type]:
            try:
                await callback(event)
            except Exception as e:
                logger.error(f"Error in event handler: {e}")


# ================== Chain of Responsibility ==================

class RequestHandler(ABC):
    """
    Abstract handler for chain of responsibility
    """

    def __init__(self):
        self.next_handler = None

    def set_next(self, handler):
        """Set the next handler in the chain"""
        self.next_handler = handler
        return handler

    @abstractmethod
    async def handle(self, request: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Handle the request or pass to next handler"""
        pass


class ValidationHandler(RequestHandler):
    """Validates incoming requests"""

    async def handle(self, request: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        # Validation logic
        if not request.get('symbols'):
            return {'error': 'No symbols provided'}

        if self.next_handler:
            return await self.next_handler.handle(request)
        return request


class AuthorizationHandler(RequestHandler):
    """Handles authorization checks"""

    async def handle(self, request: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        # Authorization logic
        if not request.get('user_id'):
            request['user_id'] = 'anonymous'

        if self.next_handler:
            return await self.next_handler.handle(request)
        return request


class RateLimitHandler(RequestHandler):
    """Handles rate limiting"""

    def __init__(self):
        super().__init__()
        self.request_counts = defaultdict(int)
        self.limit = 100

    async def handle(self, request: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        user_id = request.get('user_id', 'anonymous')
        self.request_counts[user_id] += 1

        if self.request_counts[user_id] > self.limit:
            return {'error': 'Rate limit exceeded'}

        if self.next_handler:
            return await self.next_handler.handle(request)
        return request


# ================== Main Orchestrator ==================

class StockResearchOrchestrator:
    """
    Main orchestrator combining all patterns
    Production-ready AI agent orchestration system
    """

    def __init__(self):
        # Core components
        self.blackboard = Blackboard()
        self.mediator = AgentMediator()
        self.coordinator = AgentCoordinator(self.blackboard, self.mediator)
        self.event_bus = EventBus()

        # Request handling chain
        self.request_chain = ValidationHandler()
        self.request_chain.set_next(AuthorizationHandler()).set_next(RateLimitHandler())

        # Metrics
        self.metrics = {
            'total_workflows': 0,
            'successful_workflows': 0,
            'failed_workflows': 0,
            'average_execution_time': 0
        }

    async def process_request(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process a stock research request through the entire system
        """
        start_time = datetime.utcnow()

        try:
            # Validate and authorize request
            validated_request = await self.request_chain.handle(request)
            if validated_request.get('error'):
                return validated_request

            # Publish workflow start event
            await self.event_bus.publish(
                EventType.WORKFLOW_STARTED,
                {'request': validated_request}
            )

            # Create execution plan based on request
            execution_plan = self._create_execution_plan(validated_request)

            # Execute plan
            result = await self.coordinator.execute_pipeline(execution_plan)

            # Update metrics
            self.metrics['successful_workflows'] += 1
            execution_time = (datetime.utcnow() - start_time).total_seconds()
            self._update_average_execution_time(execution_time)

            # Publish completion event
            await self.event_bus.publish(
                EventType.WORKFLOW_COMPLETED,
                {'result': result, 'execution_time': execution_time}
            )

            return {
                'status': 'success',
                'result': result,
                'execution_time': execution_time
            }

        except Exception as e:
            self.metrics['failed_workflows'] += 1
            logger.error(f"Workflow failed: {e}")

            await self.event_bus.publish(
                EventType.WORKFLOW_COMPLETED,
                {'error': str(e)}
            )

            return {
                'status': 'failed',
                'error': str(e)
            }
        finally:
            self.metrics['total_workflows'] += 1

    def _create_execution_plan(self, request: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Create execution plan based on request type"""
        symbols = request.get('symbols', [])
        analysis_type = request.get('analysis_type', 'comprehensive')

        if analysis_type == 'comprehensive':
            return [
                {
                    'name': 'market_data',
                    'agent': 'market_agent',
                    'task': {'type': 'fetch_market_data', 'symbols': symbols},
                    'dependencies': []
                },
                {
                    'name': 'fundamental',
                    'agent': 'fundamental_agent',
                    'task': {'type': 'analyze_fundamentals', 'symbols': symbols},
                    'dependencies': ['market_data']
                },
                {
                    'name': 'technical',
                    'agent': 'technical_agent',
                    'task': {'type': 'technical_analysis', 'symbols': symbols},
                    'dependencies': ['market_data']
                },
                {
                    'name': 'sentiment',
                    'agent': 'sentiment_agent',
                    'task': {'type': 'sentiment_analysis', 'symbols': symbols},
                    'dependencies': []
                },
                {
                    'name': 'synthesis',
                    'agent': 'synthesis_agent',
                    'task': {'type': 'synthesize_results'},
                    'dependencies': ['fundamental', 'technical', 'sentiment']
                }
            ]
        else:
            # Simplified plan for quick analysis
            return [
                {
                    'name': 'quick_analysis',
                    'agent': 'market_agent',
                    'task': {'type': 'quick_analysis', 'symbols': symbols},
                    'dependencies': []
                }
            ]

    def _update_average_execution_time(self, new_time: float):
        """Update rolling average execution time"""
        n = self.metrics['successful_workflows']
        if n == 1:
            self.metrics['average_execution_time'] = new_time
        else:
            avg = self.metrics['average_execution_time']
            self.metrics['average_execution_time'] = (avg * (n - 1) + new_time) / n

    def get_system_status(self) -> Dict[str, Any]:
        """Get complete system status"""
        return {
            'blackboard': self.blackboard.get_snapshot(),
            'agents': {
                agent_id: agent.state.value
                for agent_id, agent in self.coordinator.agents.items()
            },
            'metrics': self.metrics,
            'timestamp': datetime.utcnow().isoformat()
        }