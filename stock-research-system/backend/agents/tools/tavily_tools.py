"""
Specialized Tavily Tools for Multi-Agent System
Implements search, extract, crawl, and map functionalities
"""

from typing import Dict, List, Any, Optional
from datetime import datetime
import logging
import asyncio
from tavily import TavilyClient
from langchain_core.tools import tool
from pydantic import BaseModel, Field

from services.progress_tracker import Citation

logger = logging.getLogger(__name__)


class TavilySearchTool(BaseModel):
    """Configuration for Tavily Search"""
    query: str
    search_depth: str = "advanced"
    max_results: int = 10
    include_domains: Optional[List[str]] = None
    exclude_domains: Optional[List[str]] = None
    topic: Optional[str] = None


class TavilyExtractTool(BaseModel):
    """Configuration for Tavily Extract"""
    urls: List[str]
    include_raw_content: bool = False


class TavilyCrawlTool(BaseModel):
    """Configuration for Tavily Crawl"""
    url: str
    max_depth: int = 2
    max_pages: int = 10


class TavilyMapTool(BaseModel):
    """Configuration for Tavily Map (competitive landscape)"""
    domain: str
    max_results: int = 50


class SpecializedTavilyTools:
    """Specialized Tavily tools for different agent types"""

    def __init__(self, tavily_client: TavilyClient):
        self.client = tavily_client

    @tool
    async def research_search(
        self,
        query: str,
        focus: str = "general",
        request_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Advanced search tool for research agents
        Focus can be: 'news', 'financial', 'technical', 'sentiment'
        """
        logger.info(f"Research search: {query} (focus: {focus})")

        # Configure search based on focus
        config = self._get_search_config(focus)

        try:
            results = await asyncio.to_thread(
                self.client.search,
                query=query,
                search_depth=config['search_depth'],
                max_results=config['max_results'],
                include_domains=config.get('include_domains'),
                topic=config.get('topic')
            )

            # Process and structure results
            processed = self._process_search_results(results, focus, request_id)

            return processed

        except Exception as e:
            logger.error(f"Search error: {e}")
            return {'error': str(e), 'results': []}

    @tool
    async def financial_extract(
        self,
        symbols: List[str],
        data_types: List[str] = ["price", "fundamentals"],
        request_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Extract financial data from specific pages
        Data types: 'price', 'fundamentals', 'news', 'analysis'
        """
        logger.info(f"Financial extract for {symbols}: {data_types}")

        urls = self._build_financial_urls(symbols, data_types)
        extracted_data = {}
        citations = []

        for url in urls[:5]:  # Limit to 5 URLs
            try:
                result = await asyncio.to_thread(
                    self.client.extract,
                    urls=[url]
                )

                # Parse extracted content
                symbol = self._extract_symbol_from_url(url)
                if symbol not in extracted_data:
                    extracted_data[symbol] = {}

                parsed = self._parse_financial_extract(result, data_types)
                extracted_data[symbol].update(parsed)

                # Create citation
                citations.append(Citation(
                    source=url.split('/')[2],
                    url=url,
                    content=f"Financial data for {symbol}",
                    timestamp=datetime.utcnow(),
                    confidence=0.9
                ))

            except Exception as e:
                logger.error(f"Extract error for {url}: {e}")

        return {
            'data': extracted_data,
            'citations': citations,
            'extraction_time': datetime.utcnow().isoformat()
        }

    @tool
    async def deep_crawl(
        self,
        company: str,
        crawl_type: str = "comprehensive",
        request_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Deep crawl for comprehensive company analysis
        Crawl types: 'comprehensive', 'news_only', 'investor_relations'
        """
        logger.info(f"Deep crawl for {company}: {crawl_type}")

        # Determine starting URL based on crawl type
        start_url = self._get_crawl_start_url(company, crawl_type)

        try:
            results = await asyncio.to_thread(
                self.client.crawl,
                url=start_url,
                max_depth=3 if crawl_type == "comprehensive" else 2,
                max_pages=20 if crawl_type == "comprehensive" else 10
            )

            # Process crawled data
            processed = self._process_crawl_results(results, company, crawl_type)

            return processed

        except Exception as e:
            logger.error(f"Crawl error: {e}")
            return {'error': str(e), 'pages_crawled': 0}

    @tool
    async def competitive_map(
        self,
        company: str,
        industry: Optional[str] = None,
        request_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Map competitive landscape for a company
        """
        logger.info(f"Competitive mapping for {company} in {industry}")

        # Get company domain
        domain = self._get_company_domain(company)

        try:
            # Use map functionality to understand competitive landscape
            results = await asyncio.to_thread(
                self.client.search,  # Map might not be directly available
                query=f"{company} competitors {industry or ''} market share",
                search_depth="advanced",
                max_results=20
            )

            # Analyze competitive landscape
            landscape = self._analyze_competitive_landscape(results, company, industry)

            return landscape

        except Exception as e:
            logger.error(f"Map error: {e}")
            return {'error': str(e), 'competitors': []}

    # Helper methods

    def _get_search_config(self, focus: str) -> Dict[str, Any]:
        """Get search configuration based on focus"""
        configs = {
            'news': {
                'search_depth': 'advanced',
                'max_results': 10,
                'include_domains': ['reuters.com', 'bloomberg.com', 'cnbc.com', 'wsj.com'],
                'topic': 'news'
            },
            'financial': {
                'search_depth': 'advanced',
                'max_results': 10,
                'include_domains': ['finance.yahoo.com', 'marketwatch.com', 'seekingalpha.com'],
                'topic': 'finance'
            },
            'technical': {
                'search_depth': 'advanced',
                'max_results': 8,
                'include_domains': ['tradingview.com', 'stockcharts.com'],
                'topic': 'finance'
            },
            'sentiment': {
                'search_depth': 'basic',
                'max_results': 15,
                'topic': 'general'
            }
        }

        return configs.get(focus, {
            'search_depth': 'advanced',
            'max_results': 10,
            'topic': 'general'
        })

    def _process_search_results(
        self,
        results: Dict,
        focus: str,
        request_id: Optional[str]
    ) -> Dict[str, Any]:
        """Process and structure search results"""
        processed = {
            'focus': focus,
            'results': [],
            'key_findings': [],
            'citations': []
        }

        for result in results.get('results', []):
            # Structure result
            item = {
                'title': result.get('title'),
                'content': result.get('content'),
                'url': result.get('url'),
                'relevance_score': result.get('score', 0)
            }
            processed['results'].append(item)

            # Extract key findings based on focus
            if focus == 'financial' and 'earnings' in item['content'].lower():
                processed['key_findings'].append(f"Earnings mention: {item['title']}")
            elif focus == 'news' and any(word in item['title'].lower()
                                        for word in ['announces', 'breaking', 'alert']):
                processed['key_findings'].append(f"Breaking: {item['title']}")

            # Create citation
            processed['citations'].append({
                'source': result.get('url', '').split('/')[2] if result.get('url') else 'unknown',
                'url': result.get('url'),
                'title': result.get('title'),
                'confidence': result.get('score', 0.5)
            })

        return processed

    def _build_financial_urls(self, symbols: List[str], data_types: List[str]) -> List[str]:
        """Build URLs for financial data extraction"""
        urls = []

        for symbol in symbols:
            if 'price' in data_types:
                urls.append(f"https://finance.yahoo.com/quote/{symbol}")
            if 'fundamentals' in data_types:
                urls.append(f"https://finance.yahoo.com/quote/{symbol}/key-statistics")
            if 'news' in data_types:
                urls.append(f"https://finance.yahoo.com/quote/{symbol}/news")
            if 'analysis' in data_types:
                urls.append(f"https://finance.yahoo.com/quote/{symbol}/analysis")

        return urls

    def _extract_symbol_from_url(self, url: str) -> str:
        """Extract stock symbol from URL"""
        parts = url.split('/')
        for i, part in enumerate(parts):
            if part == 'quote' and i + 1 < len(parts):
                return parts[i + 1].split('?')[0]
        return 'UNKNOWN'

    def _parse_financial_extract(self, result: Dict, data_types: List[str]) -> Dict[str, Any]:
        """Parse extracted financial data"""
        parsed = {}

        # This would need actual parsing logic based on extracted HTML/text
        # For now, return structured placeholder
        content = result.get('raw_content', '') or result.get('content', '')

        if 'price' in data_types:
            # Extract price data from content
            parsed['price_data'] = self._extract_price_from_content(content)

        if 'fundamentals' in data_types:
            # Extract fundamental metrics
            parsed['fundamentals'] = self._extract_fundamentals_from_content(content)

        return parsed

    def _extract_price_from_content(self, content: str) -> Dict:
        """Extract price information from content"""
        # Simplified extraction - in production use proper parsing
        import re

        price_pattern = r'\$?(\d+\.?\d*)'
        matches = re.findall(price_pattern, content[:500])  # Check first 500 chars

        if matches:
            try:
                price = float(matches[0])
                return {'current_price': price, 'extracted': True}
            except:
                pass

        return {'current_price': None, 'extracted': False}

    def _extract_fundamentals_from_content(self, content: str) -> Dict:
        """Extract fundamental metrics from content"""
        # Simplified extraction
        fundamentals = {
            'pe_ratio': None,
            'market_cap': None,
            'eps': None
        }

        # Look for common patterns
        import re

        pe_pattern = r'P/E.*?(\d+\.?\d*)'
        pe_match = re.search(pe_pattern, content, re.IGNORECASE)
        if pe_match:
            try:
                fundamentals['pe_ratio'] = float(pe_match.group(1))
            except:
                pass

        return fundamentals

    def _get_crawl_start_url(self, company: str, crawl_type: str) -> str:
        """Get starting URL for crawl"""
        company_clean = company.lower().replace(' ', '-')

        urls = {
            'comprehensive': f"https://finance.yahoo.com/quote/{company}",
            'news_only': f"https://www.reuters.com/companies/{company}",
            'investor_relations': f"https://investors.{company_clean}.com"
        }

        return urls.get(crawl_type, f"https://finance.yahoo.com/quote/{company}")

    def _process_crawl_results(
        self,
        results: Dict,
        company: str,
        crawl_type: str
    ) -> Dict[str, Any]:
        """Process crawled pages"""
        processed = {
            'company': company,
            'crawl_type': crawl_type,
            'pages_crawled': len(results.get('pages', [])),
            'key_information': [],
            'data_points': {}
        }

        # Extract key information from crawled pages
        for page in results.get('pages', []):
            # Extract based on crawl type
            if crawl_type == 'news_only':
                # Extract news items
                if 'headline' in page.get('content', '').lower():
                    processed['key_information'].append({
                        'type': 'news',
                        'content': page.get('title', '')
                    })

            elif crawl_type == 'investor_relations':
                # Extract IR information
                if any(term in page.get('content', '').lower()
                      for term in ['earnings', 'quarterly', 'annual report']):
                    processed['key_information'].append({
                        'type': 'investor_update',
                        'content': page.get('title', '')
                    })

        return processed

    def _get_company_domain(self, company: str) -> str:
        """Get company domain for mapping"""
        # Simplified - in production, lookup actual domains
        company_domains = {
            'AAPL': 'apple.com',
            'GOOGL': 'google.com',
            'MSFT': 'microsoft.com',
            'AMZN': 'amazon.com'
        }

        return company_domains.get(company, f"{company.lower()}.com")

    def _analyze_competitive_landscape(
        self,
        results: Dict,
        company: str,
        industry: Optional[str]
    ) -> Dict[str, Any]:
        """Analyze competitive landscape from search results"""
        landscape = {
            'company': company,
            'industry': industry,
            'competitors': [],
            'market_position': 'unknown',
            'competitive_advantages': [],
            'threats': []
        }

        # Extract competitor mentions
        competitor_keywords = ['competitor', 'rival', 'versus', 'vs', 'market share']

        for result in results.get('results', []):
            content = result.get('content', '').lower()

            # Look for competitor mentions
            for keyword in competitor_keywords:
                if keyword in content:
                    # Extract competitor names (simplified)
                    landscape['competitors'].append({
                        'source': result.get('url'),
                        'mention': result.get('title')
                    })

            # Look for competitive advantages
            if 'advantage' in content or 'strength' in content:
                landscape['competitive_advantages'].append(result.get('title', ''))

            # Look for threats
            if 'threat' in content or 'challenge' in content:
                landscape['threats'].append(result.get('title', ''))

        # Deduplicate
        landscape['competitors'] = landscape['competitors'][:5]
        landscape['competitive_advantages'] = list(set(landscape['competitive_advantages']))[:3]
        landscape['threats'] = list(set(landscape['threats']))[:3]

        return landscape