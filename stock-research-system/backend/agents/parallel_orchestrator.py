"""
Parallel Agent Orchestrator for TavilyAI Pro
Enables true parallel execution of agents with intelligent coordination
"""

import asyncio
import logging
from typing import Dict, Any, List, Optional, Callable, Set, Tuple
from dataclasses import dataclass, field
from datetime import datetime
from concurrent.futures import ProcessPoolExecutor, ThreadPoolExecutor
from enum import Enum
import json
import hashlib

from langgraph.graph import StateGraph, END
from langgraph.checkpoint import MemorySaver

logger = logging.getLogger(__name__)


class AgentStatus(Enum):
    """Agent execution status"""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    BLOCKED = "blocked"


@dataclass
class AgentTask:
    """Definition of an agent task"""
    id: str
    agent_name: str
    task: str
    dependencies: List[str] = field(default_factory=list)
    priority: int = 5  # 1-10, higher is more important
    timeout: float = 60.0  # seconds
    retry_count: int = 0
    max_retries: int = 3
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class AgentResult:
    """Result from agent execution"""
    task_id: str
    agent_name: str
    status: AgentStatus
    output: Any
    error: Optional[str] = None
    execution_time: float = 0.0
    confidence: float = 0.0
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ExecutionState:
    """State for the execution graph"""
    tasks: Dict[str, AgentTask]
    results: Dict[str, AgentResult]
    running_agents: Set[str]
    completed_agents: Set[str]
    failed_agents: Set[str]
    shared_context: Dict[str, Any]
    execution_plan: List[List[str]]  # Groups of tasks for parallel execution


class ParallelOrchestrator:
    """
    Orchestrates parallel execution of multiple agents with dependency management
    """

    def __init__(self, max_workers: int = 10):
        self.max_workers = max_workers
        self.thread_executor = ThreadPoolExecutor(max_workers=max_workers)
        self.process_executor = ProcessPoolExecutor(max_workers=max_workers // 2)

        # Agent registry
        self.agents: Dict[str, Callable] = {}

        # Execution tracking
        self.current_execution: Optional[ExecutionState] = None
        self.execution_history: List[Dict] = []

        # State management
        self.state_graph = self._build_state_graph()
        self.checkpointer = MemorySaver()

        # Statistics
        self.stats = {
            "total_executions": 0,
            "parallel_executions": 0,
            "avg_parallelism": 0.0,
            "total_agent_calls": 0,
            "success_rate": 1.0
        }

    def _build_state_graph(self) -> StateGraph:
        """Build the state graph for execution management"""
        graph = StateGraph(ExecutionState)

        # Add nodes
        graph.add_node("analyze", self._analyze_dependencies)
        graph.add_node("plan", self._create_execution_plan)
        graph.add_node("execute", self._execute_parallel_wave)
        graph.add_node("merge", self._merge_results)
        graph.add_node("validate", self._validate_results)

        # Add edges
        graph.add_edge("analyze", "plan")
        graph.add_edge("plan", "execute")
        graph.add_edge("execute", "merge")
        graph.add_edge("merge", "validate")

        # Conditional edge back to execute if more waves
        graph.add_conditional_edges(
            "validate",
            self._should_continue,
            {
                "continue": "execute",
                "complete": END
            }
        )

        graph.set_entry_point("analyze")

        return graph.compile(checkpointer=self.checkpointer)

    def register_agent(self, name: str, agent_func: Callable):
        """Register an agent for orchestration"""
        self.agents[name] = agent_func
        logger.info(f"Registered agent: {name}")

    async def execute_tasks(self,
                           tasks: List[AgentTask],
                           shared_context: Optional[Dict] = None) -> Dict[str, Any]:
        """
        Execute multiple agent tasks with parallel optimization

        Args:
            tasks: List of agent tasks to execute
            shared_context: Shared context for all agents

        Returns:
            Execution results and metadata
        """
        self.stats["total_executions"] += 1

        # Initialize execution state
        task_dict = {task.id: task for task in tasks}
        self.current_execution = ExecutionState(
            tasks=task_dict,
            results={},
            running_agents=set(),
            completed_agents=set(),
            failed_agents=set(),
            shared_context=shared_context or {},
            execution_plan=[]
        )

        start_time = datetime.now()

        try:
            # Execute the state graph
            final_state = await self.state_graph.ainvoke(
                self.current_execution,
                {"recursion_limit": 10}
            )

            execution_time = (datetime.now() - start_time).total_seconds()

            # Calculate statistics
            parallelism = self._calculate_parallelism(final_state.execution_plan)
            self.stats["avg_parallelism"] = (
                (self.stats["avg_parallelism"] * (self.stats["total_executions"] - 1) + parallelism)
                / self.stats["total_executions"]
            )

            # Prepare results
            results = {
                "results": final_state.results,
                "execution_time": execution_time,
                "parallelism_achieved": parallelism,
                "success_rate": len(final_state.completed_agents) / len(tasks) if tasks else 0,
                "execution_plan": final_state.execution_plan,
                "shared_context": final_state.shared_context
            }

            # Add to history
            self.execution_history.append({
                "timestamp": datetime.now().isoformat(),
                "task_count": len(tasks),
                "success_rate": results["success_rate"],
                "execution_time": execution_time
            })

            return results

        except Exception as e:
            logger.error(f"Execution failed: {e}")
            return {
                "error": str(e),
                "results": self.current_execution.results if self.current_execution else {},
                "execution_time": (datetime.now() - start_time).total_seconds()
            }

    async def _analyze_dependencies(self, state: ExecutionState) -> ExecutionState:
        """Analyze task dependencies"""
        logger.info("Analyzing task dependencies")

        # Build dependency graph
        dependency_graph = {}
        for task_id, task in state.tasks.items():
            dependency_graph[task_id] = set(task.dependencies)

        # Validate no circular dependencies
        if self._has_circular_dependencies(dependency_graph):
            raise ValueError("Circular dependencies detected")

        # Store in metadata
        state.shared_context["dependency_graph"] = dependency_graph

        return state

    def _has_circular_dependencies(self, graph: Dict[str, Set[str]]) -> bool:
        """Check for circular dependencies using DFS"""
        visited = set()
        rec_stack = set()

        def has_cycle(node):
            visited.add(node)
            rec_stack.add(node)

            for neighbor in graph.get(node, set()):
                if neighbor not in visited:
                    if has_cycle(neighbor):
                        return True
                elif neighbor in rec_stack:
                    return True

            rec_stack.remove(node)
            return False

        for node in graph:
            if node not in visited:
                if has_cycle(node):
                    return True

        return False

    async def _create_execution_plan(self, state: ExecutionState) -> ExecutionState:
        """Create parallel execution plan based on dependencies"""
        logger.info("Creating parallel execution plan")

        dependency_graph = state.shared_context.get("dependency_graph", {})

        # Topological sort with level-based grouping
        levels = self._topological_levels(dependency_graph)

        # Create execution waves
        execution_plan = []
        for level_tasks in levels:
            # Sort within level by priority
            sorted_tasks = sorted(
                level_tasks,
                key=lambda tid: state.tasks[tid].priority,
                reverse=True
            )
            execution_plan.append(sorted_tasks)

        state.execution_plan = execution_plan

        logger.info(f"Created execution plan with {len(execution_plan)} parallel waves")
        return state

    def _topological_levels(self, dependency_graph: Dict[str, Set[str]]) -> List[List[str]]:
        """Group tasks into levels for parallel execution"""
        # Calculate in-degree for each node
        in_degree = {node: 0 for node in dependency_graph}
        for deps in dependency_graph.values():
            for dep in deps:
                if dep in in_degree:
                    in_degree[dep] += 1

        # BFS to create levels
        levels = []
        current_level = [node for node, degree in in_degree.items() if degree == 0]

        while current_level:
            levels.append(current_level)
            next_level = []

            for node in current_level:
                # Reduce in-degree for dependent nodes
                for check_node, deps in dependency_graph.items():
                    if node in deps:
                        in_degree[check_node] -= 1
                        if in_degree[check_node] == 0:
                            next_level.append(check_node)

            current_level = next_level

        return levels

    async def _execute_parallel_wave(self, state: ExecutionState) -> ExecutionState:
        """Execute a wave of parallel tasks"""
        if not state.execution_plan:
            return state

        # Get next wave
        current_wave = []
        for wave_idx, wave in enumerate(state.execution_plan):
            # Find first wave with pending tasks
            pending_in_wave = [
                task_id for task_id in wave
                if task_id not in state.completed_agents and task_id not in state.failed_agents
            ]
            if pending_in_wave:
                current_wave = pending_in_wave
                logger.info(f"Executing wave {wave_idx + 1} with {len(current_wave)} tasks")
                break

        if not current_wave:
            return state  # All tasks completed

        # Mark agents as running
        for task_id in current_wave:
            state.running_agents.add(task_id)

        # Execute tasks in parallel
        tasks = []
        for task_id in current_wave:
            task = state.tasks[task_id]
            agent_func = self.agents.get(task.agent_name)

            if agent_func:
                # Prepare context for agent
                agent_context = self._prepare_agent_context(task, state)

                # Create execution coroutine
                coro = self._execute_agent(task, agent_func, agent_context)
                tasks.append(coro)
            else:
                logger.error(f"Agent {task.agent_name} not found")
                state.failed_agents.add(task_id)
                state.running_agents.discard(task_id)

        # Wait for all tasks to complete
        if tasks:
            results = await asyncio.gather(*tasks, return_exceptions=True)

            # Process results
            for task_id, result in zip(current_wave, results):
                state.running_agents.discard(task_id)

                if isinstance(result, Exception):
                    # Handle failure
                    state.failed_agents.add(task_id)
                    state.results[task_id] = AgentResult(
                        task_id=task_id,
                        agent_name=state.tasks[task_id].agent_name,
                        status=AgentStatus.FAILED,
                        output=None,
                        error=str(result)
                    )
                    logger.error(f"Task {task_id} failed: {result}")
                else:
                    # Handle success
                    state.completed_agents.add(task_id)
                    state.results[task_id] = result

                    # Update shared context if needed
                    if result.output and isinstance(result.output, dict):
                        if "shared_data" in result.output:
                            state.shared_context.update(result.output["shared_data"])

        self.stats["parallel_executions"] += 1
        self.stats["total_agent_calls"] += len(current_wave)

        return state

    async def _execute_agent(self,
                            task: AgentTask,
                            agent_func: Callable,
                            context: Dict) -> AgentResult:
        """Execute a single agent task"""
        start_time = datetime.now()

        try:
            # Apply timeout
            if asyncio.iscoroutinefunction(agent_func):
                output = await asyncio.wait_for(
                    agent_func(task.task, context),
                    timeout=task.timeout
                )
            else:
                # Run in thread executor for sync functions
                output = await asyncio.wait_for(
                    asyncio.get_event_loop().run_in_executor(
                        self.thread_executor,
                        agent_func,
                        task.task,
                        context
                    ),
                    timeout=task.timeout
                )

            execution_time = (datetime.now() - start_time).total_seconds()

            # Extract confidence if available
            confidence = 0.75  # Default
            if isinstance(output, dict) and "confidence" in output:
                confidence = output["confidence"]

            return AgentResult(
                task_id=task.id,
                agent_name=task.agent_name,
                status=AgentStatus.COMPLETED,
                output=output,
                execution_time=execution_time,
                confidence=confidence,
                metadata=task.metadata
            )

        except asyncio.TimeoutError:
            logger.error(f"Agent {task.agent_name} timed out after {task.timeout}s")

            # Check if we should retry
            if task.retry_count < task.max_retries:
                task.retry_count += 1
                logger.info(f"Retrying task {task.id} (attempt {task.retry_count})")
                return await self._execute_agent(task, agent_func, context)

            return AgentResult(
                task_id=task.id,
                agent_name=task.agent_name,
                status=AgentStatus.FAILED,
                output=None,
                error=f"Timeout after {task.timeout}s",
                execution_time=(datetime.now() - start_time).total_seconds()
            )

        except Exception as e:
            logger.error(f"Agent {task.agent_name} failed: {e}")

            # Check if we should retry
            if task.retry_count < task.max_retries:
                task.retry_count += 1
                logger.info(f"Retrying task {task.id} (attempt {task.retry_count})")
                return await self._execute_agent(task, agent_func, context)

            return AgentResult(
                task_id=task.id,
                agent_name=task.agent_name,
                status=AgentStatus.FAILED,
                output=None,
                error=str(e),
                execution_time=(datetime.now() - start_time).total_seconds()
            )

    def _prepare_agent_context(self, task: AgentTask, state: ExecutionState) -> Dict:
        """Prepare context for agent execution"""
        context = {
            "shared_context": state.shared_context,
            "task_metadata": task.metadata,
            "dependencies": {}
        }

        # Add results from dependencies
        for dep_id in task.dependencies:
            if dep_id in state.results:
                context["dependencies"][dep_id] = state.results[dep_id].output

        return context

    async def _merge_results(self, state: ExecutionState) -> ExecutionState:
        """Merge results from parallel execution"""
        logger.info("Merging results from parallel execution")

        # Aggregate results by status
        status_counts = {
            "completed": len(state.completed_agents),
            "failed": len(state.failed_agents),
            "pending": len(state.tasks) - len(state.completed_agents) - len(state.failed_agents)
        }

        state.shared_context["status_summary"] = status_counts

        # Update success rate
        if state.tasks:
            success_rate = len(state.completed_agents) / len(state.tasks)
            self.stats["success_rate"] = (
                (self.stats["success_rate"] * self.stats["total_agent_calls"] + success_rate)
                / (self.stats["total_agent_calls"] + 1)
            )

        return state

    async def _validate_results(self, state: ExecutionState) -> ExecutionState:
        """Validate execution results"""
        logger.info("Validating execution results")

        # Check for critical failures
        critical_failures = [
            task_id for task_id, task in state.tasks.items()
            if task.priority >= 8 and task_id in state.failed_agents
        ]

        if critical_failures:
            logger.warning(f"Critical tasks failed: {critical_failures}")
            state.shared_context["critical_failures"] = critical_failures

        # Calculate overall confidence
        if state.results:
            avg_confidence = sum(
                r.confidence for r in state.results.values()
                if r.status == AgentStatus.COMPLETED
            ) / len([r for r in state.results.values() if r.status == AgentStatus.COMPLETED])

            state.shared_context["overall_confidence"] = avg_confidence

        return state

    def _should_continue(self, state: ExecutionState) -> str:
        """Determine if execution should continue"""
        # Check if there are pending tasks
        pending_tasks = [
            task_id for task_id in state.tasks
            if task_id not in state.completed_agents and task_id not in state.failed_agents
        ]

        if pending_tasks:
            return "continue"
        else:
            return "complete"

    def _calculate_parallelism(self, execution_plan: List[List[str]]) -> float:
        """Calculate achieved parallelism"""
        if not execution_plan:
            return 0.0

        total_tasks = sum(len(wave) for wave in execution_plan)
        if total_tasks == 0:
            return 0.0

        # Perfect parallelism would be all tasks in one wave
        # Actual parallelism is average tasks per wave
        avg_tasks_per_wave = total_tasks / len(execution_plan)
        max_possible_parallelism = total_tasks

        return avg_tasks_per_wave / max_possible_parallelism

    def get_statistics(self) -> Dict[str, Any]:
        """Get orchestrator statistics"""
        return {
            **self.stats,
            "registered_agents": list(self.agents.keys()),
            "execution_history_size": len(self.execution_history),
            "max_workers": self.max_workers
        }

    async def shutdown(self):
        """Shutdown executors"""
        self.thread_executor.shutdown(wait=True)
        self.process_executor.shutdown(wait=True)