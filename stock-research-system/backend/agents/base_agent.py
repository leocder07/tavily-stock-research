"""Base Agent Class for Financial Analysis System"""

from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional
from datetime import datetime
from pydantic import BaseModel, Field
import logging
from tavily import TavilyClient
import asyncio
import json

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class AgentState(BaseModel):
    """State model for tracking agent execution"""
    agent_id: str
    agent_type: str
    status: str = "IDLE"  # IDLE, PROCESSING, COMPLETED, COMPLETED_WITH_ERRORS, FAILED
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    input_data: Dict[str, Any] = Field(default_factory=dict)
    output_data: Dict[str, Any] = Field(default_factory=dict)
    error_message: Optional[str] = None
    confidence_score: float = 0.0
    citations: List[Dict[str, str]] = Field(default_factory=list)
    metadata: Dict[str, Any] = Field(default_factory=dict)


class BaseFinancialAgent(ABC):
    """Base class for all financial analysis agents"""

    def __init__(self, agent_id: str, agent_type: str, tavily_client: Optional[TavilyClient] = None):
        """Initialize base agent

        Args:
            agent_id: Unique identifier for the agent
            agent_type: Type of agent (e.g., 'market_data', 'fundamental', etc.)
            tavily_client: Tavily API client for web data
        """
        self.agent_id = agent_id
        self.agent_type = agent_type
        self.tavily = tavily_client
        self.state = AgentState(
            agent_id=agent_id,
            agent_type=agent_type,
            status="IDLE"
        )
        self.max_retries = 3
        self.retry_delay = 1  # seconds

    @abstractmethod
    async def execute(self, context: Dict[str, Any]) -> AgentState:
        """Execute agent-specific analysis logic

        Args:
            context: Input context containing analysis parameters

        Returns:
            AgentState with execution results
        """
        pass

    async def run(self, context: Dict[str, Any]) -> AgentState:
        """Run agent with error handling and retries

        Args:
            context: Input context for analysis

        Returns:
            Final agent state after execution (with partial results if available)
        """
        self.state.status = "PROCESSING"
        self.state.start_time = datetime.utcnow()
        self.state.input_data = context

        for attempt in range(self.max_retries):
            try:
                logger.info(f"Agent {self.agent_id} starting execution (attempt {attempt + 1})")
                self.state = await self.execute(context)
                self.state.status = "COMPLETED"
                break
            except Exception as e:
                logger.error(f"Agent {self.agent_id} failed on attempt {attempt + 1}: {str(e)}")

                # Check if partial results are available
                has_partial_results = (
                    self.state.output_data and
                    len(self.state.output_data) > 0 and
                    any(v for v in self.state.output_data.values() if v)
                )

                if attempt == self.max_retries - 1:
                    # Last attempt failed - use partial results if available
                    if has_partial_results:
                        self.state.status = "COMPLETED_WITH_ERRORS"
                        self.state.error_message = f"Partial results only: {str(e)}"
                        self.state.metadata['partial_results'] = True
                        self.state.metadata['error_details'] = str(e)
                        logger.warning(f"Agent {self.agent_id} completed with partial results after {self.max_retries} attempts")
                    else:
                        self.state.status = "FAILED"
                        self.state.error_message = str(e)
                        logger.error(f"Agent {self.agent_id} failed with no partial results")
                else:
                    await asyncio.sleep(self.retry_delay * (2 ** attempt))  # Exponential backoff

        self.state.end_time = datetime.utcnow()
        return self.state

    async def search_tavily(self, query: str, search_depth: str = "advanced", max_results: int = 5) -> List[Dict]:
        """Search using Tavily API

        Args:
            query: Search query
            search_depth: Search depth ('basic' or 'advanced')
            max_results: Maximum number of results

        Returns:
            List of search results
        """
        if not self.tavily:
            raise ValueError("Tavily client not initialized")

        try:
            response = await self.tavily.search(
                query=query,
                search_depth=search_depth,
                max_results=max_results,
                include_domains=[],
                exclude_domains=[]
            )
            # Handle both dict and coroutine responses
            if hasattr(response, 'get'):
                return response.get('results', [])
            else:
                logger.warning(f"Unexpected Tavily response type: {type(response)}")
                return []
        except Exception as e:
            logger.error(f"Tavily search failed: {str(e)}")
            return []

    async def extract_tavily(self, urls: List[str]) -> List[Dict]:
        """Extract content from URLs using Tavily

        Args:
            urls: List of URLs to extract content from

        Returns:
            List of extracted content
        """
        if not self.tavily:
            raise ValueError("Tavily client not initialized")

        try:
            response = await self.tavily.extract(urls=urls)
            # Handle both dict and coroutine responses
            if hasattr(response, 'get'):
                return response.get('results', [])
            else:
                logger.warning(f"Unexpected Tavily extract response type: {type(response)}")
                return []
        except Exception as e:
            logger.error(f"Tavily extract failed: {str(e)}")
            return []

    async def qna_search_tavily(self, query: str) -> str:
        """QnA search using Tavily for direct answers

        Args:
            query: Question to answer

        Returns:
            Direct answer string
        """
        if not self.tavily:
            raise ValueError("Tavily client not initialized")

        try:
            response = await self.tavily.qna_search(query=query)
            return response
        except Exception as e:
            logger.error(f"Tavily QnA search failed: {str(e)}")
            return ""

    async def get_search_context_tavily(self, query: str, max_tokens: int = 4000) -> str:
        """Get search context using Tavily for RAG applications

        Args:
            query: Search query
            max_tokens: Maximum tokens in response (NOTE: This parameter is kept for API compatibility but not used by Tavily)

        Returns:
            Search context string
        """
        if not self.tavily:
            raise ValueError("Tavily client not initialized")

        try:
            # Note: Tavily's get_search_context doesn't accept max_tokens parameter
            # It returns context based on max_results instead
            response = await self.tavily.get_search_context(
                query=query,
                max_results=5  # Use max_results instead of max_tokens
            )
            # Extract context string from response
            if isinstance(response, dict):
                return response.get('context', '')
            return str(response)
        except Exception as e:
            logger.error(f"Tavily get search context failed: {str(e)}")
            return ""

    def calculate_confidence(self, data: Dict[str, Any]) -> float:
        """Calculate confidence score based on data quality

        Args:
            data: Analysis data

        Returns:
            Confidence score between 0 and 1
        """
        # Base implementation - can be overridden by specific agents
        factors = []

        # Check data completeness
        if data.get('data_points', 0) > 0:
            factors.append(min(data['data_points'] / 100, 1.0))

        # Check source diversity
        if data.get('source_count', 0) > 0:
            factors.append(min(data['source_count'] / 5, 1.0))

        # Check data freshness
        if data.get('is_real_time', False):
            factors.append(1.0)
        elif data.get('data_age_hours', 24) < 24:
            factors.append(0.8)
        else:
            factors.append(0.5)

        return sum(factors) / len(factors) if factors else 0.5

    def extract_citations(self, results: List[Dict]) -> List[Dict[str, str]]:
        """Extract citations from search results

        Args:
            results: Search results from Tavily or other sources

        Returns:
            List of citations with source and URL
        """
        citations = []
        for result in results:
            if isinstance(result, dict):
                citation = {
                    'source': result.get('title', 'Unknown Source'),
                    'url': result.get('url', ''),
                    'relevance_score': result.get('score', 0.0)
                }
                if result.get('published_date'):
                    citation['published_date'] = result['published_date']
                citations.append(citation)
        return citations

    def format_output(self, data: Any) -> Dict[str, Any]:
        """Format agent output for consistency

        Args:
            data: Raw output data

        Returns:
            Formatted output dictionary
        """
        if isinstance(data, dict):
            return data
        elif isinstance(data, list):
            return {'results': data}
        elif isinstance(data, str):
            return {'text': data}
        else:
            return {'data': str(data)}

    async def validate_input(self, context: Dict[str, Any]) -> bool:
        """Validate input context

        Args:
            context: Input context to validate

        Returns:
            True if valid, False otherwise
        """
        # Override in specific agents for custom validation
        required_fields = ['query', 'stock_symbols']
        for field in required_fields:
            if field not in context:
                logger.warning(f"Missing required field: {field}")
                return False
        return True