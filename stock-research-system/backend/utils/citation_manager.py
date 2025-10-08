"""Citation management system for tracking and formatting data sources"""

import hashlib
import re
from typing import Dict, List, Any, Optional
from datetime import datetime
from urllib.parse import urlparse
import logging

logger = logging.getLogger(__name__)


class Citation:
    """Represents a single citation/source"""

    def __init__(
        self,
        url: str,
        title: str,
        content: str,
        source_type: str = 'web',
        timestamp: Optional[datetime] = None,
        relevance_score: float = 0.0
    ):
        """Initialize a citation

        Args:
            url: Source URL
            title: Source title
            content: Relevant content excerpt
            source_type: Type of source (web, api, research, news)
            timestamp: When the data was retrieved
            relevance_score: Relevance score (0-1)
        """
        self.url = url
        self.title = title
        self.content = content[:500] if content else ""  # Limit content length
        self.source_type = source_type
        self.timestamp = timestamp or datetime.utcnow()
        self.relevance_score = relevance_score
        self.id = self._generate_id()
        self.domain = self._extract_domain()

    def _generate_id(self) -> str:
        """Generate unique ID for citation"""
        content = f"{self.url}{self.title}{self.timestamp}"
        return hashlib.md5(content.encode()).hexdigest()[:8]

    def _extract_domain(self) -> str:
        """Extract domain from URL"""
        try:
            parsed = urlparse(self.url)
            return parsed.netloc.replace('www.', '')
        except:
            return 'unknown'

    def to_dict(self) -> Dict[str, Any]:
        """Convert citation to dictionary"""
        return {
            'id': self.id,
            'url': self.url,
            'title': self.title,
            'content': self.content,
            'source_type': self.source_type,
            'domain': self.domain,
            'timestamp': self.timestamp.isoformat(),
            'relevance_score': self.relevance_score
        }

    def format_inline(self) -> str:
        """Format as inline citation"""
        return f"[{self.id}]"

    def format_full(self) -> str:
        """Format as full citation"""
        return f"[{self.id}] {self.title}. {self.domain}. Retrieved {self.timestamp.strftime('%Y-%m-%d')}"


class CitationManager:
    """Manages citations across the analysis workflow"""

    def __init__(self):
        """Initialize citation manager"""
        self.citations: Dict[str, Citation] = {}
        self.agent_citations: Dict[str, List[str]] = {}

    def add_citation(
        self,
        url: str,
        title: str,
        content: str,
        agent_id: str,
        source_type: str = 'web',
        relevance_score: float = 0.0
    ) -> Citation:
        """Add a new citation

        Args:
            url: Source URL
            title: Source title
            content: Relevant content
            agent_id: ID of agent adding the citation
            source_type: Type of source
            relevance_score: Relevance score

        Returns:
            Citation object
        """
        citation = Citation(
            url=url,
            title=title,
            content=content,
            source_type=source_type,
            relevance_score=relevance_score
        )

        # Store citation
        self.citations[citation.id] = citation

        # Track which agent added it
        if agent_id not in self.agent_citations:
            self.agent_citations[agent_id] = []
        self.agent_citations[agent_id].append(citation.id)

        logger.debug(f"Added citation {citation.id} from {agent_id}")
        return citation

    def add_from_tavily_results(
        self,
        results: List[Dict],
        agent_id: str,
        source_type: str = 'web'
    ) -> List[Citation]:
        """Add citations from Tavily search results

        Args:
            results: Tavily search results
            agent_id: ID of agent
            source_type: Type of source

        Returns:
            List of Citation objects
        """
        citations = []

        for result in results:
            if isinstance(result, dict):
                citation = self.add_citation(
                    url=result.get('url', ''),
                    title=result.get('title', ''),
                    content=result.get('content', ''),
                    agent_id=agent_id,
                    source_type=source_type,
                    relevance_score=result.get('score', 0.0)
                )
                citations.append(citation)

        return citations

    def get_citation(self, citation_id: str) -> Optional[Citation]:
        """Get citation by ID

        Args:
            citation_id: Citation ID

        Returns:
            Citation object or None
        """
        return self.citations.get(citation_id)

    def get_agent_citations(self, agent_id: str) -> List[Citation]:
        """Get all citations from a specific agent

        Args:
            agent_id: Agent ID

        Returns:
            List of Citation objects
        """
        citation_ids = self.agent_citations.get(agent_id, [])
        return [self.citations[cid] for cid in citation_ids if cid in self.citations]

    def get_top_citations(self, n: int = 10) -> List[Citation]:
        """Get top N most relevant citations

        Args:
            n: Number of citations to return

        Returns:
            List of top Citation objects
        """
        sorted_citations = sorted(
            self.citations.values(),
            key=lambda c: c.relevance_score,
            reverse=True
        )
        return sorted_citations[:n]

    def format_inline_citations(self, text: str) -> str:
        """Add inline citations to text

        Args:
            text: Text to add citations to

        Returns:
            Text with inline citations
        """
        # Find statements that need citations (containing facts/numbers)
        fact_patterns = [
            r'\$[\d,]+\.?\d*[BM]?',  # Dollar amounts
            r'\d+\.?\d*%',  # Percentages
            r'Q[1-4]\s+20\d{2}',  # Quarters
            r'20\d{2}',  # Years
            r'\d+\.?\d*[BM]?\s+(?:revenue|earnings|profit|loss)',  # Financial metrics
        ]

        for pattern in fact_patterns:
            matches = re.finditer(pattern, text, re.IGNORECASE)
            for match in matches:
                # Find relevant citation
                fact = match.group()
                relevant_citation = self._find_relevant_citation(fact)
                if relevant_citation:
                    # Add citation after the fact
                    citation_text = relevant_citation.format_inline()
                    text = text[:match.end()] + citation_text + text[match.end():]

        return text

    def _find_relevant_citation(self, fact: str) -> Optional[Citation]:
        """Find citation relevant to a fact

        Args:
            fact: Fact to find citation for

        Returns:
            Most relevant Citation or None
        """
        best_citation = None
        best_score = 0

        for citation in self.citations.values():
            # Check if fact appears in citation content
            if fact.lower() in citation.content.lower():
                if citation.relevance_score > best_score:
                    best_citation = citation
                    best_score = citation.relevance_score

        return best_citation

    def format_bibliography(self) -> str:
        """Format all citations as bibliography

        Returns:
            Formatted bibliography string
        """
        if not self.citations:
            return "No sources cited."

        bibliography = "## Sources\n\n"

        # Group by source type
        grouped = {}
        for citation in self.citations.values():
            if citation.source_type not in grouped:
                grouped[citation.source_type] = []
            grouped[citation.source_type].append(citation)

        # Format each group
        for source_type, citations in grouped.items():
            bibliography += f"### {source_type.title()} Sources\n\n"
            for citation in sorted(citations, key=lambda c: c.timestamp):
                bibliography += f"- {citation.format_full()}\n"
            bibliography += "\n"

        return bibliography

    def to_dict(self) -> Dict[str, Any]:
        """Convert manager state to dictionary

        Returns:
            Dictionary representation
        """
        return {
            'total_citations': len(self.citations),
            'citations': [c.to_dict() for c in self.citations.values()],
            'agent_citations': self.agent_citations,
            'top_sources': [c.domain for c in self.get_top_citations(5)]
        }

    def merge(self, other: 'CitationManager'):
        """Merge citations from another manager

        Args:
            other: Another CitationManager
        """
        for citation_id, citation in other.citations.items():
            if citation_id not in self.citations:
                self.citations[citation_id] = citation

        for agent_id, citation_ids in other.agent_citations.items():
            if agent_id not in self.agent_citations:
                self.agent_citations[agent_id] = []
            self.agent_citations[agent_id].extend(citation_ids)


# Global citation manager instance
_citation_manager = None

def get_citation_manager() -> CitationManager:
    """Get or create citation manager instance

    Returns:
        CitationManager instance
    """
    global _citation_manager
    if _citation_manager is None:
        _citation_manager = CitationManager()
    return _citation_manager

def reset_citation_manager():
    """Reset the global citation manager"""
    global _citation_manager
    _citation_manager = CitationManager()