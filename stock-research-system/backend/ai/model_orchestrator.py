"""
Multi-Model Orchestrator for TavilyAI Pro
Intelligently routes tasks to optimal models (Claude-3, GPT-4, etc.)
"""

import os
import asyncio
import logging
from typing import Dict, Any, Optional, List, Tuple
from enum import Enum
from dataclasses import dataclass
import tiktoken
from langchain_openai import ChatOpenAI
from langchain_anthropic import ChatAnthropic
from langchain_core.messages import HumanMessage, SystemMessage, AIMessage
from langchain.callbacks.streaming_stdout import StreamingStdOutCallbackHandler

logger = logging.getLogger(__name__)


class TaskType(Enum):
    """Task types for model routing"""
    GENERAL = "general"  # Default general purpose task
    STRATEGIC_PLANNING = "strategic_planning"
    FINANCIAL_ANALYSIS = "financial_analysis"
    WEB_SYNTHESIS = "web_synthesis"
    DATA_EXTRACTION = "data_extraction"
    CREATIVE_WRITING = "creative_writing"
    CODE_GENERATION = "code_generation"
    SIMPLE_TASK = "simple_task"
    REASONING = "reasoning"
    SUMMARIZATION = "summarization"


class ModelType(Enum):
    """Available model types"""
    CLAUDE_3_OPUS = "claude-3-opus-20240229"
    CLAUDE_3_SONNET = "claude-3-sonnet-20240229"
    CLAUDE_3_HAIKU = "claude-3-haiku-20240307"
    GPT_4_TURBO = "gpt-4-turbo-preview"
    GPT_4 = "gpt-4"
    GPT_35_TURBO = "gpt-3.5-turbo"


@dataclass
class ModelConfig:
    """Configuration for a specific model"""
    model_type: ModelType
    temperature: float
    max_tokens: int
    top_p: float
    frequency_penalty: float
    presence_penalty: float
    streaming: bool = False


@dataclass
class TaskContext:
    """Context for task execution"""
    task_type: TaskType
    complexity_score: float  # 0.0 to 1.0
    urgency: str  # "low", "medium", "high"
    token_budget: Optional[int] = None
    require_citations: bool = False
    require_confidence: bool = True
    memory_context: Optional[str] = None


@dataclass
class ModelResponse:
    """Response from a model"""
    content: str
    confidence: float
    token_count: int
    model_used: str
    metadata: Dict[str, Any]


class ModelOrchestrator:
    """
    Orchestrates multiple AI models for optimal task completion
    Routes tasks to the best model based on requirements
    """

    def __init__(self, openai_api_key: str = None, anthropic_api_key: str = None):
        self.openai_api_key = openai_api_key or os.getenv("OPENAI_API_KEY")
        self.anthropic_api_key = anthropic_api_key or os.getenv("ANTHROPIC_API_KEY")

        # Model routing strategy
        self.model_routing = {
            TaskType.STRATEGIC_PLANNING: ModelType.CLAUDE_3_OPUS,
            TaskType.FINANCIAL_ANALYSIS: ModelType.GPT_4_TURBO,
            TaskType.WEB_SYNTHESIS: ModelType.CLAUDE_3_SONNET,
            TaskType.DATA_EXTRACTION: ModelType.CLAUDE_3_HAIKU,
            TaskType.CREATIVE_WRITING: ModelType.GPT_4,
            TaskType.CODE_GENERATION: ModelType.CLAUDE_3_OPUS,
            TaskType.SIMPLE_TASK: ModelType.GPT_35_TURBO,
            TaskType.REASONING: ModelType.CLAUDE_3_OPUS,
            TaskType.SUMMARIZATION: ModelType.CLAUDE_3_SONNET,
        }

        # Model capabilities and costs (per 1K tokens)
        self.model_capabilities = {
            ModelType.CLAUDE_3_OPUS: {
                "reasoning": 0.95,
                "speed": 0.7,
                "cost_input": 0.015,
                "cost_output": 0.075,
                "context_window": 200000,
                "strengths": ["deep reasoning", "code", "analysis"]
            },
            ModelType.CLAUDE_3_SONNET: {
                "reasoning": 0.85,
                "speed": 0.85,
                "cost_input": 0.003,
                "cost_output": 0.015,
                "context_window": 200000,
                "strengths": ["balance", "synthesis", "general tasks"]
            },
            ModelType.CLAUDE_3_HAIKU: {
                "reasoning": 0.75,
                "speed": 0.95,
                "cost_input": 0.00025,
                "cost_output": 0.00125,
                "context_window": 200000,
                "strengths": ["speed", "simple tasks", "extraction"]
            },
            ModelType.GPT_4_TURBO: {
                "reasoning": 0.9,
                "speed": 0.8,
                "cost_input": 0.01,
                "cost_output": 0.03,
                "context_window": 128000,
                "strengths": ["financial", "math", "structured data"]
            },
            ModelType.GPT_4: {
                "reasoning": 0.88,
                "speed": 0.6,
                "cost_input": 0.03,
                "cost_output": 0.06,
                "context_window": 8192,
                "strengths": ["creativity", "general intelligence"]
            },
            ModelType.GPT_35_TURBO: {
                "reasoning": 0.7,
                "speed": 0.95,
                "cost_input": 0.0005,
                "cost_output": 0.0015,
                "context_window": 16385,
                "strengths": ["speed", "simple tasks", "cost"]
            }
        }

        # Initialize model instances (lazy loading)
        self._models = {}
        self._token_encoders = {}

        # Tracking
        self.model_usage_stats = {model: {"calls": 0, "tokens": 0, "cost": 0}
                                  for model in ModelType}
        self.total_cost = 0.0

    def _get_model(self, model_type: ModelType, config: ModelConfig):
        """Get or create a model instance"""
        key = f"{model_type.value}_{config.temperature}"

        if key not in self._models:
            if "claude" in model_type.value:
                if not self.anthropic_api_key:
                    logger.warning(f"No Anthropic API key, falling back to OpenAI")
                    return self._get_fallback_model(config)

                self._models[key] = ChatAnthropic(
                    model=model_type.value,
                    anthropic_api_key=self.anthropic_api_key,
                    temperature=config.temperature,
                    max_tokens=config.max_tokens,
                    top_p=config.top_p,
                    streaming=config.streaming,
                    callbacks=[StreamingStdOutCallbackHandler()] if config.streaming else []
                )
            else:  # OpenAI models
                self._models[key] = ChatOpenAI(
                    model=model_type.value,
                    openai_api_key=self.openai_api_key,
                    temperature=config.temperature,
                    max_tokens=config.max_tokens,
                    top_p=config.top_p,
                    frequency_penalty=config.frequency_penalty,
                    presence_penalty=config.presence_penalty,
                    streaming=config.streaming,
                    callbacks=[StreamingStdOutCallbackHandler()] if config.streaming else []
                )

        return self._models[key]

    def _get_fallback_model(self, config: ModelConfig):
        """Get fallback model when primary is unavailable"""
        return ChatOpenAI(
            model=ModelType.GPT_4_TURBO.value,
            openai_api_key=self.openai_api_key,
            temperature=config.temperature,
            max_tokens=config.max_tokens,
            streaming=config.streaming
        )

    async def route_task(self,
                         prompt: str,
                         context: TaskContext,
                         system_prompt: Optional[str] = None) -> Tuple[str, Dict[str, Any]]:
        """
        Route a task to the optimal model based on context
        Returns: (response, metadata)
        """
        # Select optimal model
        model_type = self._select_optimal_model(context)

        # Configure model based on task
        config = self._get_model_config(model_type, context)

        # Get model instance
        model = self._get_model(model_type, config)

        # Prepare messages
        messages = []
        if system_prompt:
            messages.append(SystemMessage(content=system_prompt))
        messages.append(HumanMessage(content=prompt))

        # Track token usage
        input_tokens = self._estimate_tokens(prompt, model_type)

        try:
            # Execute with retry logic
            response = await self._execute_with_retry(model, messages, retries=3)

            # Extract response text
            response_text = response.content if hasattr(response, 'content') else str(response)

            # Calculate costs
            output_tokens = self._estimate_tokens(response_text, model_type)
            cost = self._calculate_cost(model_type, input_tokens, output_tokens)

            # Update statistics
            self._update_stats(model_type, input_tokens + output_tokens, cost)

            # Prepare metadata
            metadata = {
                "model": model_type.value,
                "temperature": config.temperature,
                "input_tokens": input_tokens,
                "output_tokens": output_tokens,
                "total_tokens": input_tokens + output_tokens,
                "cost": cost,
                "complexity_score": context.complexity_score,
                "task_type": context.task_type.value
            }

            # Add confidence score if requested
            if context.require_confidence:
                metadata["confidence"] = self._extract_confidence(response_text)

            logger.info(f"Task routed to {model_type.value}: {input_tokens + output_tokens} tokens, ${cost:.4f}")

            return response_text, metadata

        except Exception as e:
            logger.error(f"Model execution failed: {e}")
            # Try fallback model
            return await self._execute_fallback(prompt, context, system_prompt)

    def _select_optimal_model(self, context: TaskContext) -> ModelType:
        """Select the optimal model based on task context"""
        # Primary routing based on task type
        primary_choice = self.model_routing.get(context.task_type, ModelType.GPT_4_TURBO)

        # Adjust based on complexity
        if context.complexity_score > 0.8:
            # High complexity - use most capable model
            if context.task_type in [TaskType.REASONING, TaskType.STRATEGIC_PLANNING]:
                return ModelType.CLAUDE_3_OPUS
            elif context.task_type == TaskType.FINANCIAL_ANALYSIS:
                return ModelType.GPT_4_TURBO
        elif context.complexity_score < 0.3:
            # Low complexity - use faster/cheaper model
            if context.urgency == "high":
                return ModelType.CLAUDE_3_HAIKU
            else:
                return ModelType.GPT_35_TURBO

        # Check token budget constraints
        if context.token_budget:
            # Select model that fits budget
            for model in [ModelType.CLAUDE_3_HAIKU, ModelType.GPT_35_TURBO,
                         ModelType.CLAUDE_3_SONNET, primary_choice]:
                if self._fits_budget(model, context.token_budget):
                    return model

        return primary_choice

    def _get_model_config(self, model_type: ModelType, context: TaskContext) -> ModelConfig:
        """Get optimal configuration for model based on task"""
        # Temperature based on task type
        temperature_map = {
            TaskType.FINANCIAL_ANALYSIS: 0.1,  # Precise
            TaskType.DATA_EXTRACTION: 0.0,     # Deterministic
            TaskType.REASONING: 0.2,           # Focused
            TaskType.STRATEGIC_PLANNING: 0.3,  # Balanced
            TaskType.WEB_SYNTHESIS: 0.4,       # Flexible
            TaskType.CREATIVE_WRITING: 0.7,    # Creative
            TaskType.SIMPLE_TASK: 0.3,         # Standard
        }

        temperature = temperature_map.get(context.task_type, 0.3)

        # Adjust temperature based on complexity
        if context.complexity_score > 0.7:
            temperature = max(0.0, temperature - 0.1)  # More focused for complex tasks

        # Max tokens based on task
        max_tokens = 4000 if context.task_type in [
            TaskType.STRATEGIC_PLANNING,
            TaskType.FINANCIAL_ANALYSIS
        ] else 2000

        return ModelConfig(
            model_type=model_type,
            temperature=temperature,
            max_tokens=max_tokens,
            top_p=0.95,
            frequency_penalty=0.0,
            presence_penalty=0.0,
            streaming=context.urgency != "high"  # Stream unless urgent
        )

    async def _execute_with_retry(self, model, messages, retries=3):
        """Execute model with retry logic"""
        for attempt in range(retries):
            try:
                if asyncio.iscoroutinefunction(model.ainvoke):
                    return await model.ainvoke(messages)
                else:
                    return await asyncio.to_thread(model.invoke, messages)
            except Exception as e:
                logger.warning(f"Attempt {attempt + 1} failed: {e}")
                if attempt == retries - 1:
                    raise
                await asyncio.sleep(2 ** attempt)  # Exponential backoff

    async def _execute_fallback(self, prompt: str, context: TaskContext,
                                system_prompt: Optional[str]) -> Tuple[str, Dict]:
        """Execute with fallback model"""
        logger.info("Using fallback model")

        config = ModelConfig(
            model_type=ModelType.GPT_4_TURBO,
            temperature=0.3,
            max_tokens=2000,
            top_p=0.95,
            frequency_penalty=0.0,
            presence_penalty=0.0
        )

        model = self._get_fallback_model(config)
        messages = []
        if system_prompt:
            messages.append(SystemMessage(content=system_prompt))
        messages.append(HumanMessage(content=prompt))

        response = await self._execute_with_retry(model, messages, retries=2)
        response_text = response.content if hasattr(response, 'content') else str(response)

        metadata = {
            "model": "gpt-4-turbo-preview (fallback)",
            "temperature": 0.3,
            "fallback": True,
            "task_type": context.task_type.value
        }

        return response_text, metadata

    def _estimate_tokens(self, text: str, model_type: ModelType) -> int:
        """Estimate token count for text"""
        # Use tiktoken for OpenAI models
        if "gpt" in model_type.value:
            if model_type.value not in self._token_encoders:
                self._token_encoders[model_type.value] = tiktoken.encoding_for_model(
                    model_type.value.replace("-preview", "")
                )
            encoder = self._token_encoders[model_type.value]
            return len(encoder.encode(text))
        else:
            # Approximate for Claude models (1 token ≈ 4 characters)
            return len(text) // 4

    def _calculate_cost(self, model_type: ModelType, input_tokens: int, output_tokens: int) -> float:
        """Calculate cost for model usage"""
        caps = self.model_capabilities[model_type]
        input_cost = (input_tokens / 1000) * caps["cost_input"]
        output_cost = (output_tokens / 1000) * caps["cost_output"]
        return input_cost + output_cost

    def _fits_budget(self, model_type: ModelType, token_budget: int) -> bool:
        """Check if model fits within token budget"""
        # Conservative estimate: assume 50/50 input/output split
        caps = self.model_capabilities[model_type]
        estimated_cost = (token_budget / 2000) * (caps["cost_input"] + caps["cost_output"])
        return estimated_cost < 0.50  # Max $0.50 per query

    def _extract_confidence(self, response: str) -> float:
        """Extract confidence score from response"""
        # Look for confidence indicators in response
        import re

        # Try to find explicit confidence statement
        confidence_pattern = r'confidence[:\s]+(\d+(?:\.\d+)?%?)'
        match = re.search(confidence_pattern, response.lower())

        if match:
            conf_str = match.group(1).replace('%', '')
            return float(conf_str) / 100 if float(conf_str) > 1 else float(conf_str)

        # Heuristic based on hedging words
        hedging_words = ['might', 'perhaps', 'possibly', 'could', 'may', 'uncertain']
        confident_words = ['definitely', 'certainly', 'clearly', 'obviously', 'undoubtedly']

        response_lower = response.lower()
        hedge_count = sum(1 for word in hedging_words if word in response_lower)
        confident_count = sum(1 for word in confident_words if word in response_lower)

        if confident_count > hedge_count:
            return 0.85
        elif hedge_count > confident_count:
            return 0.65
        else:
            return 0.75

    def _update_stats(self, model_type: ModelType, tokens: int, cost: float):
        """Update usage statistics"""
        self.model_usage_stats[model_type]["calls"] += 1
        self.model_usage_stats[model_type]["tokens"] += tokens
        self.model_usage_stats[model_type]["cost"] += cost
        self.total_cost += cost

    def get_usage_report(self) -> Dict[str, Any]:
        """Get comprehensive usage report"""
        return {
            "total_cost": self.total_cost,
            "model_usage": {
                model.value: stats
                for model, stats in self.model_usage_stats.items()
                if stats["calls"] > 0
            },
            "cost_breakdown": {
                "by_model": {
                    model.value: stats["cost"]
                    for model, stats in self.model_usage_stats.items()
                    if stats["cost"] > 0
                }
            }
        }

    async def parallel_execute(self, tasks: List[Tuple[str, TaskContext, Optional[str]]]) -> List[Tuple[str, Dict]]:
        """Execute multiple tasks in parallel"""
        async def execute_task(task):
            prompt, context, system_prompt = task
            return await self.route_task(prompt, context, system_prompt)

        results = await asyncio.gather(*[execute_task(task) for task in tasks])
        return results