"""
Query Intelligence Service - NLP-powered query parsing and enhancement
Uses advanced NLP to understand user intent and extract entities
"""

import re
import json
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass
from enum import Enum
import logging
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)


class QueryIntent(Enum):
    """Types of query intents"""
    ANALYZE = "analyze"  # Single stock analysis
    COMPARE = "compare"  # Compare multiple stocks
    SCREEN = "screen"  # Screen for opportunities
    PORTFOLIO = "portfolio"  # Portfolio analysis
    TREND = "trend"  # Market trend analysis
    NEWS = "news"  # News and sentiment
    TECHNICAL = "technical"  # Technical analysis
    FUNDAMENTAL = "fundamental"  # Fundamental analysis
    RISK = "risk"  # Risk assessment
    SECTOR = "sector"  # Sector analysis


class AnalysisDepth(Enum):
    """Depth of analysis required"""
    QUICK = "quick"  # 1-2 min analysis
    STANDARD = "standard"  # 3-5 min analysis
    DEEP = "deep"  # 5-10 min comprehensive
    RESEARCH = "research"  # 10+ min institutional grade


class TimeFrame(Enum):
    """Analysis timeframes"""
    INTRADAY = "intraday"
    WEEK = "week"
    MONTH = "month"
    QUARTER = "quarter"
    YTD = "ytd"
    YEAR = "1y"
    YEARS_3 = "3y"
    YEARS_5 = "5y"
    ALL = "all"


@dataclass
class QueryEnhancement:
    """Enhanced query with extracted information"""
    original_query: str
    enhanced_query: str
    intent: QueryIntent
    confidence: float
    extracted_entities: Dict[str, Any]
    suggested_params: Dict[str, Any]
    query_templates: List[str]
    follow_up_suggestions: List[str]
    tavily_apis_needed: List[str]


class QueryIntelligenceService:
    """Advanced query parsing and enhancement service"""

    def __init__(self):
        self.stock_patterns = self._compile_patterns()
        self.intent_keywords = self._load_intent_keywords()
        self.common_tickers = self._load_common_tickers()
        self.query_templates = self._load_query_templates()

    def _compile_patterns(self) -> Dict[str, re.Pattern]:
        """Compile regex patterns for entity extraction"""
        return {
            'ticker': re.compile(r'\b[A-Z]{1,5}\b'),
            'comparison': re.compile(r'\b(vs|versus|against|compare|compared to)\b', re.I),
            'timeframe': re.compile(r'\b(today|week|month|quarter|ytd|year|[0-9]+y|all time)\b', re.I),
            'price_target': re.compile(r'\$[0-9]+(\.[0-9]{2})?'),
            'percentage': re.compile(r'[0-9]+(\.[0-9]+)?%'),
            'sector_industry': re.compile(r'\b(tech|healthcare|finance|energy|consumer|industrial|materials|utilities|real estate)\b', re.I),
            'analysis_type': re.compile(r'\b(technical|fundamental|sentiment|risk|growth|value|momentum)\b', re.I),
            'action': re.compile(r'\b(buy|sell|hold|long|short|invest|trade)\b', re.I),
        }

    def _load_intent_keywords(self) -> Dict[QueryIntent, List[str]]:
        """Load keywords for intent detection"""
        return {
            QueryIntent.ANALYZE: ['analyze', 'analysis', 'evaluate', 'assess', 'review', 'outlook'],
            QueryIntent.COMPARE: ['compare', 'vs', 'versus', 'against', 'better', 'difference'],
            QueryIntent.SCREEN: ['find', 'search', 'screen', 'opportunities', 'undervalued', 'best'],
            QueryIntent.PORTFOLIO: ['portfolio', 'holdings', 'allocation', 'rebalance', 'optimize'],
            QueryIntent.TREND: ['trend', 'trending', 'momentum', 'direction', 'pattern'],
            QueryIntent.NEWS: ['news', 'latest', 'recent', 'announcement', 'earnings'],
            QueryIntent.TECHNICAL: ['technical', 'chart', 'rsi', 'macd', 'support', 'resistance'],
            QueryIntent.FUNDAMENTAL: ['fundamental', 'pe', 'earnings', 'revenue', 'valuation'],
            QueryIntent.RISK: ['risk', 'volatility', 'var', 'beta', 'drawdown', 'safe'],
            QueryIntent.SECTOR: ['sector', 'industry', 'peers', 'competitors', 'market'],
        }

    def _load_common_tickers(self) -> Dict[str, str]:
        """Load common stock tickers and their names"""
        return {
            'AAPL': 'Apple Inc.',
            'GOOGL': 'Alphabet Inc.',
            'MSFT': 'Microsoft Corporation',
            'AMZN': 'Amazon.com Inc.',
            'TSLA': 'Tesla Inc.',
            'META': 'Meta Platforms Inc.',
            'NVDA': 'NVIDIA Corporation',
            'JPM': 'JPMorgan Chase',
            'V': 'Visa Inc.',
            'JNJ': 'Johnson & Johnson',
            'WMT': 'Walmart Inc.',
            'PG': 'Procter & Gamble',
            'MA': 'Mastercard Inc.',
            'UNH': 'UnitedHealth Group',
            'DIS': 'Walt Disney Company',
            'NFLX': 'Netflix Inc.',
            'PYPL': 'PayPal Holdings',
            'BAC': 'Bank of America',
            'XOM': 'Exxon Mobil',
            'PFE': 'Pfizer Inc.',
        }

    def _load_query_templates(self) -> List[Dict[str, str]]:
        """Load query templates for quick actions"""
        return [
            {
                'id': 'single_analysis',
                'template': 'Analyze {symbol} for investment potential',
                'description': 'Comprehensive single stock analysis',
                'required': ['symbol'],
            },
            {
                'id': 'comparison',
                'template': 'Compare {symbol1} vs {symbol2}',
                'description': 'Head-to-head stock comparison',
                'required': ['symbol1', 'symbol2'],
            },
            {
                'id': 'sector_screen',
                'template': 'Find undervalued stocks in {sector}',
                'description': 'Screen for opportunities in a sector',
                'required': ['sector'],
            },
            {
                'id': 'growth_screen',
                'template': 'Find high-growth stocks under ${price}',
                'description': 'Screen for growth opportunities',
                'required': ['price'],
            },
            {
                'id': 'dividend',
                'template': 'Best dividend stocks with yield > {yield}%',
                'description': 'Find high-dividend paying stocks',
                'required': ['yield'],
            },
            {
                'id': 'risk_assessment',
                'template': 'Assess risk for {symbol} over {timeframe}',
                'description': 'Risk analysis for specific timeframe',
                'required': ['symbol', 'timeframe'],
            },
        ]

    def parse_query(self, query: str) -> QueryEnhancement:
        """
        Parse and enhance user query with NLP

        Args:
            query: Raw user query

        Returns:
            Enhanced query with extracted entities and suggestions
        """
        # Normalize query
        normalized = query.strip().lower()

        # Detect intent
        intent, intent_confidence = self._detect_intent(normalized)

        # Extract entities
        entities = self._extract_entities(query)

        # Determine analysis depth
        depth = self._determine_depth(normalized, entities)

        # Generate enhanced query
        enhanced = self._enhance_query(query, intent, entities)

        # Suggest parameters
        params = self._suggest_parameters(intent, entities, depth)

        # Determine Tavily APIs needed
        tavily_apis = self._determine_tavily_apis(intent, depth)

        # Generate follow-up suggestions
        follow_ups = self._generate_follow_ups(intent, entities)

        # Find matching templates
        templates = self._find_matching_templates(intent, entities)

        return QueryEnhancement(
            original_query=query,
            enhanced_query=enhanced,
            intent=intent,
            confidence=intent_confidence,
            extracted_entities=entities,
            suggested_params=params,
            query_templates=templates,
            follow_up_suggestions=follow_ups,
            tavily_apis_needed=tavily_apis
        )

    def _detect_intent(self, query: str) -> Tuple[QueryIntent, float]:
        """Detect query intent using keyword matching"""
        scores = {}

        for intent, keywords in self.intent_keywords.items():
            score = sum(1 for kw in keywords if kw in query)
            if score > 0:
                scores[intent] = score

        if not scores:
            # Default to analyze if no clear intent
            return QueryIntent.ANALYZE, 0.5

        # Get highest scoring intent
        best_intent = max(scores, key=scores.get)
        confidence = min(scores[best_intent] / 3.0, 1.0)  # Normalize confidence

        # Special handling for comparison
        if self.patterns['comparison'].search(query):
            return QueryIntent.COMPARE, 0.9

        return best_intent, confidence

    def _extract_entities(self, query: str) -> Dict[str, Any]:
        """Extract entities from query"""
        entities = {
            'symbols': [],
            'timeframe': None,
            'price_targets': [],
            'percentages': [],
            'sectors': [],
            'analysis_types': [],
            'actions': [],
            'comparison_mode': False,
        }

        # Extract stock symbols
        potential_tickers = self.patterns['ticker'].findall(query)
        entities['symbols'] = [t for t in potential_tickers if t in self.common_tickers]

        # Check for comparison
        if self.patterns['comparison'].search(query):
            entities['comparison_mode'] = True

        # Extract timeframe
        timeframe_match = self.patterns['timeframe'].search(query)
        if timeframe_match:
            entities['timeframe'] = self._normalize_timeframe(timeframe_match.group())

        # Extract price targets
        entities['price_targets'] = self.patterns['price_target'].findall(query)

        # Extract percentages
        entities['percentages'] = self.patterns['percentage'].findall(query)

        # Extract sectors
        sector_matches = self.patterns['sector_industry'].findall(query.lower())
        entities['sectors'] = sector_matches

        # Extract analysis types
        analysis_matches = self.patterns['analysis_type'].findall(query.lower())
        entities['analysis_types'] = analysis_matches

        # Extract actions
        action_matches = self.patterns['action'].findall(query.lower())
        entities['actions'] = action_matches

        return entities

    def _normalize_timeframe(self, timeframe_str: str) -> str:
        """Normalize timeframe string to standard format"""
        tf_lower = timeframe_str.lower()

        mapping = {
            'today': TimeFrame.INTRADAY.value,
            'week': TimeFrame.WEEK.value,
            'month': TimeFrame.MONTH.value,
            'quarter': TimeFrame.QUARTER.value,
            'ytd': TimeFrame.YTD.value,
            'year': TimeFrame.YEAR.value,
            '1y': TimeFrame.YEAR.value,
            '3y': TimeFrame.YEARS_3.value,
            '5y': TimeFrame.YEARS_5.value,
            'all time': TimeFrame.ALL.value,
        }

        return mapping.get(tf_lower, TimeFrame.YEAR.value)

    def _determine_depth(self, query: str, entities: Dict) -> AnalysisDepth:
        """Determine required analysis depth"""
        # Keywords indicating depth
        if any(word in query for word in ['quick', 'brief', 'summary']):
            return AnalysisDepth.QUICK
        elif any(word in query for word in ['comprehensive', 'detailed', 'deep', 'thorough']):
            return AnalysisDepth.DEEP
        elif any(word in query for word in ['research', 'institutional', 'professional']):
            return AnalysisDepth.RESEARCH

        # Multiple analysis types = deeper analysis
        if len(entities.get('analysis_types', [])) > 2:
            return AnalysisDepth.DEEP

        # Comparison = standard depth
        if entities.get('comparison_mode'):
            return AnalysisDepth.STANDARD

        return AnalysisDepth.STANDARD

    def _enhance_query(self, query: str, intent: QueryIntent, entities: Dict) -> str:
        """Enhance query with additional context"""
        enhanced_parts = [query]

        # Add intent clarification
        if intent == QueryIntent.ANALYZE and entities.get('symbols'):
            symbols = ', '.join(entities['symbols'])
            enhanced_parts.append(f"Perform comprehensive analysis on {symbols}")

        # Add timeframe if missing
        if not entities.get('timeframe'):
            enhanced_parts.append("Using 1-year timeframe for analysis")

        # Add analysis types if not specified
        if not entities.get('analysis_types'):
            if intent in [QueryIntent.ANALYZE, QueryIntent.COMPARE]:
                enhanced_parts.append("Include technical, fundamental, and sentiment analysis")

        return '. '.join(enhanced_parts)

    def _suggest_parameters(self, intent: QueryIntent, entities: Dict, depth: AnalysisDepth) -> Dict[str, Any]:
        """Suggest analysis parameters based on query"""
        params = {
            'include_technical': True,
            'include_fundamental': True,
            'include_sentiment': True,
            'include_news': True,
            'depth': depth.value,
            'timeframe': entities.get('timeframe', TimeFrame.YEAR.value),
            'risk_assessment': True,
            'peer_comparison': intent == QueryIntent.COMPARE or intent == QueryIntent.SECTOR,
            'max_revisions': 2 if depth == AnalysisDepth.QUICK else 3,
        }

        # Adjust based on intent
        if intent == QueryIntent.TECHNICAL:
            params['include_fundamental'] = False
            params['include_sentiment'] = False
        elif intent == QueryIntent.FUNDAMENTAL:
            params['include_technical'] = False
        elif intent == QueryIntent.NEWS:
            params['include_technical'] = False
            params['include_fundamental'] = False

        # Adjust based on depth
        if depth == AnalysisDepth.QUICK:
            params['include_news'] = False
            params['risk_assessment'] = False
        elif depth == AnalysisDepth.RESEARCH:
            params['max_revisions'] = 5
            params['include_backtesting'] = True
            params['include_monte_carlo'] = True

        return params

    def _determine_tavily_apis(self, intent: QueryIntent, depth: AnalysisDepth) -> List[str]:
        """Determine which Tavily APIs to use"""
        apis = ['search']  # Always use search

        # Intent-based API selection
        if intent in [QueryIntent.ANALYZE, QueryIntent.COMPARE]:
            apis.extend(['extract', 'crawl'])
            if depth in [AnalysisDepth.DEEP, AnalysisDepth.RESEARCH]:
                apis.append('map')
        elif intent == QueryIntent.NEWS:
            apis.append('extract')
        elif intent == QueryIntent.SECTOR:
            apis.extend(['map', 'crawl'])
        elif intent == QueryIntent.SCREEN:
            apis.extend(['search', 'map'])

        # Depth-based additions
        if depth == AnalysisDepth.RESEARCH:
            # Use all APIs for research-grade analysis
            apis = ['search', 'extract', 'crawl', 'map']

        return list(set(apis))  # Remove duplicates

    def _generate_follow_ups(self, intent: QueryIntent, entities: Dict) -> List[str]:
        """Generate follow-up query suggestions"""
        suggestions = []

        if entities.get('symbols'):
            symbol = entities['symbols'][0]

            # Intent-based suggestions
            if intent == QueryIntent.ANALYZE:
                suggestions.extend([
                    f"Compare {symbol} with its main competitors",
                    f"What's the price target for {symbol}?",
                    f"Show me the risk factors for {symbol}",
                    f"Is {symbol} undervalued?",
                ])
            elif intent == QueryIntent.COMPARE:
                suggestions.extend([
                    "Which has better growth prospects?",
                    "Compare their dividend yields",
                    "Which is safer for long-term investment?",
                    "Show valuation multiples comparison",
                ])

            # Add sector analysis
            suggestions.append(f"How does {symbol} compare to its sector?")
        else:
            # No symbols - suggest screening
            suggestions.extend([
                "Find top growth stocks",
                "Show me undervalued dividend stocks",
                "What are the best tech stocks to buy?",
                "Find stocks with low P/E ratios",
            ])

        return suggestions[:4]  # Return top 4 suggestions

    def _find_matching_templates(self, intent: QueryIntent, entities: Dict) -> List[str]:
        """Find matching query templates"""
        matching = []

        for template in self.query_templates:
            # Check if template matches intent
            if intent == QueryIntent.ANALYZE and template['id'] == 'single_analysis':
                if entities.get('symbols'):
                    filled = template['template'].format(symbol=entities['symbols'][0])
                    matching.append(filled)
            elif intent == QueryIntent.COMPARE and template['id'] == 'comparison':
                if len(entities.get('symbols', [])) >= 2:
                    filled = template['template'].format(
                        symbol1=entities['symbols'][0],
                        symbol2=entities['symbols'][1]
                    )
                    matching.append(filled)
            elif intent == QueryIntent.SCREEN:
                if template['id'] in ['sector_screen', 'growth_screen']:
                    matching.append(template['template'])

        return matching

    def get_auto_suggestions(self, partial_query: str) -> List[Dict[str, str]]:
        """Get auto-suggestions for partial queries"""
        suggestions = []
        partial_lower = partial_query.lower()

        # Suggest stock symbols
        for ticker, name in self.common_tickers.items():
            if ticker.lower().startswith(partial_lower) or partial_lower in name.lower():
                suggestions.append({
                    'type': 'stock',
                    'value': ticker,
                    'display': f"{ticker} - {name}",
                    'query': f"Analyze {ticker}",
                })

        # Suggest common queries
        common_queries = [
            "What's the best stock to buy today?",
            "Compare AAPL vs GOOGL",
            "Find undervalued tech stocks",
            "Show me high dividend stocks",
            "Analyze TSLA for growth potential",
            "Is NVDA overvalued?",
            "Best stocks for 2024",
            "Safe stocks for retirement",
        ]

        for query in common_queries:
            if partial_lower in query.lower():
                suggestions.append({
                    'type': 'query',
                    'value': query,
                    'display': query,
                    'query': query,
                })

        return suggestions[:5]  # Return top 5 suggestions