"""
Tool Orchestrator for TavilyAI Pro
Intelligent tool selection and execution with parallel processing
"""

import asyncio
import logging
from typing import Dict, Any, List, Optional, Callable, Tuple
from dataclasses import dataclass
from enum import Enum
from datetime import datetime
import json

logger = logging.getLogger(__name__)


class ToolCategory(Enum):
    """Tool categories for organization"""
    SEARCH = "search"
    EXTRACTION = "extraction"
    ANALYSIS = "analysis"
    SYNTHESIS = "synthesis"
    VALIDATION = "validation"


@dataclass
class Tool:
    """Tool definition"""
    name: str
    category: ToolCategory
    function: Callable
    cost: float  # Relative cost (0-1)
    speed: float  # Relative speed (0-1, higher is faster)
    accuracy: float  # Accuracy rating (0-1)
    capabilities: List[str]
    required_params: List[str]
    optional_params: List[str]
    metadata: Dict[str, Any]


@dataclass
class ToolExecutionPlan:
    """Plan for tool execution"""
    tools: List[Tool]
    execution_order: List[List[str]]  # Groups for parallel execution
    dependencies: Dict[str, List[str]]  # Tool dependencies
    estimated_cost: float
    estimated_time: float
    confidence: float


@dataclass
class ToolResult:
    """Result from tool execution"""
    tool_name: str
    success: bool
    output: Any
    error: Optional[str]
    execution_time: float
    cost: float
    metadata: Dict[str, Any]


class ToolOrchestrator:
    """
    Orchestrates tool selection and execution for optimal results
    """

    def __init__(self):
        self.tools: Dict[str, Tool] = {}
        self.execution_history: List[Dict] = []
        self.tool_performance: Dict[str, Dict] = {}  # Performance metrics

        # Initialize default tools
        self._initialize_default_tools()

    def _initialize_default_tools(self):
        """Initialize with default Tavily tools"""
        # Tavily Search
        self.register_tool(Tool(
            name="tavily_search",
            category=ToolCategory.SEARCH,
            function=None,  # Will be set by actual implementation
            cost=0.3,
            speed=0.8,
            accuracy=0.9,
            capabilities=["web_search", "news", "real_time"],
            required_params=["query"],
            optional_params=["search_depth", "include_domains", "exclude_domains"],
            metadata={"api": "tavily", "rate_limit": 100}
        ))

        # Tavily Extract
        self.register_tool(Tool(
            name="tavily_extract",
            category=ToolCategory.EXTRACTION,
            function=None,
            cost=0.4,
            speed=0.7,
            accuracy=0.85,
            capabilities=["document_extraction", "structured_data"],
            required_params=["urls"],
            optional_params=["data_types", "include_raw"],
            metadata={"api": "tavily", "rate_limit": 50}
        ))

        # Tavily Crawl
        self.register_tool(Tool(
            name="tavily_crawl",
            category=ToolCategory.EXTRACTION,
            function=None,
            cost=0.6,
            speed=0.4,
            accuracy=0.9,
            capabilities=["website_crawl", "deep_extraction"],
            required_params=["url"],
            optional_params=["max_depth", "max_pages"],
            metadata={"api": "tavily", "rate_limit": 20}
        ))

        # Tavily Map
        self.register_tool(Tool(
            name="tavily_map",
            category=ToolCategory.ANALYSIS,
            function=None,
            cost=0.5,
            speed=0.6,
            accuracy=0.85,
            capabilities=["competitive_analysis", "market_mapping"],
            required_params=["domain"],
            optional_params=["analysis_depth", "max_results"],
            metadata={"api": "tavily", "rate_limit": 30}
        ))

        # Financial Analysis
        self.register_tool(Tool(
            name="financial_analyzer",
            category=ToolCategory.ANALYSIS,
            function=None,
            cost=0.2,
            speed=0.9,
            accuracy=0.95,
            capabilities=["financial_metrics", "ratios", "trends"],
            required_params=["symbol"],
            optional_params=["period", "metrics"],
            metadata={"type": "internal"}
        ))

        # Technical Indicators
        self.register_tool(Tool(
            name="technical_indicators",
            category=ToolCategory.ANALYSIS,
            function=None,
            cost=0.1,
            speed=0.95,
            accuracy=0.9,
            capabilities=["technical_analysis", "indicators", "signals"],
            required_params=["symbol"],
            optional_params=["indicators", "timeframe"],
            metadata={"type": "internal"}
        ))

    def register_tool(self, tool: Tool):
        """Register a new tool"""
        self.tools[tool.name] = tool
        self.tool_performance[tool.name] = {
            "total_executions": 0,
            "success_rate": 1.0,
            "avg_execution_time": 0.0,
            "total_cost": 0.0
        }
        logger.info(f"Registered tool: {tool.name}")

    async def create_execution_plan(self,
                                   task: str,
                                   requirements: Dict[str, Any]) -> ToolExecutionPlan:
        """
        Create an optimal execution plan for a task

        Args:
            task: Task description
            requirements: Task requirements (data needed, constraints, etc.)

        Returns:
            ToolExecutionPlan
        """
        # Analyze task to determine needed capabilities
        needed_capabilities = self._analyze_task_requirements(task, requirements)

        # Score and select tools
        selected_tools = self._select_optimal_tools(needed_capabilities, requirements)

        # Create execution order with parallelization
        execution_order = self._create_execution_order(selected_tools, task)

        # Calculate estimates
        estimated_cost = sum(tool.cost for tool in selected_tools)
        estimated_time = self._estimate_execution_time(execution_order, selected_tools)

        # Build dependencies
        dependencies = self._identify_dependencies(selected_tools, task)

        plan = ToolExecutionPlan(
            tools=selected_tools,
            execution_order=execution_order,
            dependencies=dependencies,
            estimated_cost=estimated_cost,
            estimated_time=estimated_time,
            confidence=self._calculate_plan_confidence(selected_tools)
        )

        logger.info(f"Created execution plan with {len(selected_tools)} tools")
        return plan

    def _analyze_task_requirements(self, task: str, requirements: Dict) -> List[str]:
        """Analyze task to determine needed capabilities"""
        capabilities = []
        task_lower = task.lower()

        # Search capabilities
        if any(word in task_lower for word in ["search", "find", "latest", "news"]):
            capabilities.extend(["web_search", "real_time"])

        # Extraction capabilities
        if any(word in task_lower for word in ["extract", "scrape", "crawl", "website"]):
            capabilities.extend(["document_extraction", "website_crawl"])

        # Analysis capabilities
        if any(word in task_lower for word in ["analyze", "compare", "evaluate"]):
            capabilities.extend(["financial_metrics", "competitive_analysis"])

        # Technical analysis
        if any(word in task_lower for word in ["technical", "indicator", "rsi", "macd"]):
            capabilities.extend(["technical_analysis", "indicators"])

        # Market analysis
        if any(word in task_lower for word in ["market", "competitor", "landscape"]):
            capabilities.extend(["market_mapping", "competitive_analysis"])

        # Add from explicit requirements
        if "capabilities" in requirements:
            capabilities.extend(requirements["capabilities"])

        return list(set(capabilities))  # Remove duplicates

    def _select_optimal_tools(self,
                             needed_capabilities: List[str],
                             requirements: Dict) -> List[Tool]:
        """Select optimal tools for capabilities"""
        selected = []
        covered_capabilities = set()

        # Get budget constraints
        max_cost = requirements.get("max_cost", 1.0)
        min_accuracy = requirements.get("min_accuracy", 0.7)
        max_time = requirements.get("max_time", float('inf'))

        # Score all tools
        tool_scores = []
        for tool_name, tool in self.tools.items():
            # Check if tool provides needed capabilities
            tool_caps = set(tool.capabilities)
            needed_caps = set(needed_capabilities)
            overlap = tool_caps.intersection(needed_caps)

            if overlap:
                # Calculate score
                coverage = len(overlap) / len(needed_caps) if needed_caps else 0
                performance = self.tool_performance[tool_name]["success_rate"]

                score = (
                    coverage * 0.4 +          # Capability coverage
                    tool.accuracy * 0.3 +      # Accuracy
                    tool.speed * 0.2 +         # Speed
                    performance * 0.1          # Historical performance
                )

                # Apply constraints
                if tool.accuracy >= min_accuracy and tool.cost <= max_cost:
                    tool_scores.append((tool, score, overlap))

        # Sort by score
        tool_scores.sort(key=lambda x: x[1], reverse=True)

        # Select tools to cover all capabilities
        total_cost = 0
        for tool, score, overlap in tool_scores:
            # Check if tool adds new capabilities
            new_caps = overlap - covered_capabilities

            if new_caps and total_cost + tool.cost <= max_cost:
                selected.append(tool)
                covered_capabilities.update(overlap)
                total_cost += tool.cost

                # Check if all capabilities covered
                if covered_capabilities >= set(needed_capabilities):
                    break

        return selected

    def _create_execution_order(self, tools: List[Tool], task: str) -> List[List[str]]:
        """Create execution order with parallelization"""
        # Group tools by category for logical ordering
        groups = {
            ToolCategory.SEARCH: [],
            ToolCategory.EXTRACTION: [],
            ToolCategory.ANALYSIS: [],
            ToolCategory.SYNTHESIS: [],
            ToolCategory.VALIDATION: []
        }

        for tool in tools:
            groups[tool.category].append(tool.name)

        # Create execution order
        # Search and extraction can run in parallel
        # Analysis depends on search/extraction
        # Synthesis depends on analysis
        execution_order = []

        # First wave: Search and initial extraction
        first_wave = groups[ToolCategory.SEARCH] + groups[ToolCategory.EXTRACTION][:1]
        if first_wave:
            execution_order.append(first_wave)

        # Second wave: Remaining extraction
        if len(groups[ToolCategory.EXTRACTION]) > 1:
            execution_order.append(groups[ToolCategory.EXTRACTION][1:])

        # Third wave: Analysis
        if groups[ToolCategory.ANALYSIS]:
            execution_order.append(groups[ToolCategory.ANALYSIS])

        # Fourth wave: Synthesis and validation
        final_wave = groups[ToolCategory.SYNTHESIS] + groups[ToolCategory.VALIDATION]
        if final_wave:
            execution_order.append(final_wave)

        return execution_order

    def _identify_dependencies(self, tools: List[Tool], task: str) -> Dict[str, List[str]]:
        """Identify tool dependencies"""
        dependencies = {}

        # Simple heuristic: tools in later categories depend on earlier ones
        category_order = [
            ToolCategory.SEARCH,
            ToolCategory.EXTRACTION,
            ToolCategory.ANALYSIS,
            ToolCategory.SYNTHESIS,
            ToolCategory.VALIDATION
        ]

        for tool in tools:
            tool_deps = []
            tool_category_idx = category_order.index(tool.category)

            # Find tools in earlier categories
            for other_tool in tools:
                if other_tool.name != tool.name:
                    other_category_idx = category_order.index(other_tool.category)
                    if other_category_idx < tool_category_idx:
                        tool_deps.append(other_tool.name)

            if tool_deps:
                dependencies[tool.name] = tool_deps

        return dependencies

    def _estimate_execution_time(self,
                                execution_order: List[List[str]],
                                tools: List[Tool]) -> float:
        """Estimate total execution time"""
        tool_map = {tool.name: tool for tool in tools}
        total_time = 0

        for wave in execution_order:
            # Parallel execution - time is max of the wave
            wave_time = 0
            for tool_name in wave:
                if tool_name in tool_map:
                    tool = tool_map[tool_name]
                    # Convert speed to estimated seconds (inverse, scaled)
                    tool_time = (1 - tool.speed) * 10  # 0-10 seconds range
                    wave_time = max(wave_time, tool_time)

            total_time += wave_time

        return total_time

    def _calculate_plan_confidence(self, tools: List[Tool]) -> float:
        """Calculate confidence in execution plan"""
        if not tools:
            return 0.0

        # Factors: tool accuracy, historical performance
        confidence_factors = []

        for tool in tools:
            # Tool accuracy
            confidence_factors.append(tool.accuracy)

            # Historical performance
            perf = self.tool_performance[tool.name]
            if perf["total_executions"] > 0:
                confidence_factors.append(perf["success_rate"])

        return sum(confidence_factors) / len(confidence_factors) if confidence_factors else 0.5

    async def execute_plan(self,
                          plan: ToolExecutionPlan,
                          inputs: Dict[str, Any],
                          tool_functions: Dict[str, Callable]) -> List[ToolResult]:
        """
        Execute a tool execution plan

        Args:
            plan: Execution plan
            inputs: Input data for tools
            tool_functions: Mapping of tool names to actual functions

        Returns:
            List of ToolResults
        """
        results = []
        intermediate_data = {}  # Store outputs for dependent tools

        for wave_idx, wave in enumerate(plan.execution_order):
            logger.info(f"Executing wave {wave_idx + 1}: {wave}")

            # Execute tools in parallel
            wave_tasks = []
            for tool_name in wave:
                if tool_name in plan.tools:
                    tool = next(t for t in plan.tools if t.name == tool_name)

                    # Prepare inputs for tool
                    tool_inputs = self._prepare_tool_inputs(
                        tool,
                        inputs,
                        intermediate_data,
                        plan.dependencies.get(tool_name, [])
                    )

                    # Get tool function
                    if tool_name in tool_functions:
                        func = tool_functions[tool_name]
                        task = self._execute_tool(tool, func, tool_inputs)
                        wave_tasks.append((tool_name, task))

            # Wait for all tools in wave to complete
            if wave_tasks:
                wave_results = await asyncio.gather(
                    *[task for _, task in wave_tasks],
                    return_exceptions=True
                )

                # Process results
                for (tool_name, _), result in zip(wave_tasks, wave_results):
                    if isinstance(result, Exception):
                        tool_result = ToolResult(
                            tool_name=tool_name,
                            success=False,
                            output=None,
                            error=str(result),
                            execution_time=0,
                            cost=0,
                            metadata={"wave": wave_idx}
                        )
                    else:
                        tool_result = result
                        # Store output for dependent tools
                        intermediate_data[tool_name] = tool_result.output

                    results.append(tool_result)

                    # Update performance metrics
                    self._update_tool_performance(tool_name, tool_result)

        return results

    async def _execute_tool(self,
                          tool: Tool,
                          func: Callable,
                          inputs: Dict) -> ToolResult:
        """Execute a single tool"""
        start_time = datetime.now()

        try:
            # Execute tool function
            if asyncio.iscoroutinefunction(func):
                output = await func(**inputs)
            else:
                output = await asyncio.to_thread(func, **inputs)

            execution_time = (datetime.now() - start_time).total_seconds()

            return ToolResult(
                tool_name=tool.name,
                success=True,
                output=output,
                error=None,
                execution_time=execution_time,
                cost=tool.cost,
                metadata={
                    "category": tool.category.value,
                    "accuracy": tool.accuracy
                }
            )

        except Exception as e:
            logger.error(f"Tool {tool.name} execution failed: {e}")

            return ToolResult(
                tool_name=tool.name,
                success=False,
                output=None,
                error=str(e),
                execution_time=(datetime.now() - start_time).total_seconds(),
                cost=tool.cost,
                metadata={"category": tool.category.value}
            )

    def _prepare_tool_inputs(self,
                           tool: Tool,
                           base_inputs: Dict,
                           intermediate_data: Dict,
                           dependencies: List[str]) -> Dict:
        """Prepare inputs for a tool"""
        tool_inputs = {}

        # Add required parameters
        for param in tool.required_params:
            if param in base_inputs:
                tool_inputs[param] = base_inputs[param]
            else:
                # Try to get from dependent tools
                for dep in dependencies:
                    if dep in intermediate_data:
                        dep_output = intermediate_data[dep]
                        if isinstance(dep_output, dict) and param in dep_output:
                            tool_inputs[param] = dep_output[param]
                            break

        # Add optional parameters if available
        for param in tool.optional_params:
            if param in base_inputs:
                tool_inputs[param] = base_inputs[param]

        return tool_inputs

    def _update_tool_performance(self, tool_name: str, result: ToolResult):
        """Update tool performance metrics"""
        if tool_name not in self.tool_performance:
            return

        perf = self.tool_performance[tool_name]

        # Update execution count
        perf["total_executions"] += 1

        # Update success rate
        if result.success:
            current_successes = perf["success_rate"] * (perf["total_executions"] - 1)
            perf["success_rate"] = (current_successes + 1) / perf["total_executions"]
        else:
            current_successes = perf["success_rate"] * (perf["total_executions"] - 1)
            perf["success_rate"] = current_successes / perf["total_executions"]

        # Update average execution time
        current_total_time = perf["avg_execution_time"] * (perf["total_executions"] - 1)
        perf["avg_execution_time"] = (
            (current_total_time + result.execution_time) / perf["total_executions"]
        )

        # Update total cost
        perf["total_cost"] += result.cost

    async def execute_with_fallback(self,
                                   task: str,
                                   inputs: Dict,
                                   tool_functions: Dict,
                                   max_attempts: int = 2) -> List[ToolResult]:
        """
        Execute with fallback strategies

        Args:
            task: Task description
            inputs: Input data
            tool_functions: Tool function mapping
            max_attempts: Maximum execution attempts

        Returns:
            List of ToolResults
        """
        for attempt in range(max_attempts):
            # Create execution plan
            requirements = {
                "max_cost": 1.0 - (attempt * 0.2),  # Reduce cost on retries
                "min_accuracy": 0.7 - (attempt * 0.1)  # Relax accuracy on retries
            }

            plan = await self.create_execution_plan(task, requirements)

            # Execute plan
            results = await self.execute_plan(plan, inputs, tool_functions)

            # Check if execution was successful
            success_rate = sum(1 for r in results if r.success) / len(results) if results else 0

            if success_rate >= 0.7:  # At least 70% success
                return results

            logger.warning(f"Attempt {attempt + 1} failed with {success_rate:.2%} success rate")

            # Wait before retry
            if attempt < max_attempts - 1:
                await asyncio.sleep(2 ** attempt)

        logger.error(f"All {max_attempts} attempts failed for task: {task}")
        return results

    def get_performance_report(self) -> Dict[str, Any]:
        """Get tool performance report"""
        return {
            "tool_performance": self.tool_performance,
            "total_tools": len(self.tools),
            "categories": {
                cat.value: len([t for t in self.tools.values() if t.category == cat])
                for cat in ToolCategory
            },
            "execution_history_size": len(self.execution_history)
        }