"""
Query Intelligence API Endpoints
Provides endpoints for query parsing, enhancement, and suggestions
"""

from typing import List, Dict, Any, Optional
from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field
import logging

from services.query_intelligence import (
    QueryIntelligenceService,
    QueryIntent,
    AnalysisDepth,
    QueryEnhancement
)

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/query", tags=["Query Intelligence"])

# Initialize service
query_service = QueryIntelligenceService()


class QueryParseRequest(BaseModel):
    """Request model for query parsing"""
    query: str = Field(..., min_length=1, max_length=500)
    user_context: Optional[Dict[str, Any]] = None


class QueryParseResponse(BaseModel):
    """Response model for parsed query"""
    original_query: str
    enhanced_query: str
    intent: str
    confidence: float
    extracted_entities: Dict[str, Any]
    suggested_params: Dict[str, Any]
    query_templates: List[str]
    follow_up_suggestions: List[str]
    tavily_apis_needed: List[str]


class AutoSuggestionResponse(BaseModel):
    """Response model for auto-suggestions"""
    suggestions: List[Dict[str, str]]


class QueryTemplate(BaseModel):
    """Query template model"""
    id: str
    name: str
    template: str
    description: str
    category: str
    required_params: List[str]
    example: str


class QueryExample(BaseModel):
    """Query example model"""
    query: str
    description: str
    category: str
    complexity: str


@router.post("/parse", response_model=QueryParseResponse)
async def parse_query(request: QueryParseRequest):
    """
    Parse and enhance user query with NLP

    Extracts entities, detects intent, and provides suggestions
    """
    try:
        # Parse query
        enhancement = query_service.parse_query(request.query)

        # Log for monitoring
        logger.info(f"Parsed query: {request.query[:50]}... Intent: {enhancement.intent.value}")

        return QueryParseResponse(
            original_query=enhancement.original_query,
            enhanced_query=enhancement.enhanced_query,
            intent=enhancement.intent.value,
            confidence=enhancement.confidence,
            extracted_entities=enhancement.extracted_entities,
            suggested_params=enhancement.suggested_params,
            query_templates=enhancement.query_templates,
            follow_up_suggestions=enhancement.follow_up_suggestions,
            tavily_apis_needed=enhancement.tavily_apis_needed
        )
    except Exception as e:
        logger.error(f"Query parsing error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Query parsing failed: {str(e)}")


@router.get("/suggest", response_model=AutoSuggestionResponse)
async def get_suggestions(q: str = Query(..., min_length=1, max_length=100)):
    """
    Get auto-suggestions for partial queries

    Returns stock symbols, common queries, and templates
    """
    try:
        suggestions = query_service.get_auto_suggestions(q)
        return AutoSuggestionResponse(suggestions=suggestions)
    except Exception as e:
        logger.error(f"Suggestion error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to get suggestions: {str(e)}")


@router.get("/templates", response_model=List[QueryTemplate])
async def get_query_templates(category: Optional[str] = None):
    """
    Get available query templates

    Templates help users quickly create complex queries
    """
    templates = [
        QueryTemplate(
            id="analyze_single",
            name="Single Stock Analysis",
            template="Analyze {symbol} for investment potential",
            description="Comprehensive analysis of a single stock",
            category="analysis",
            required_params=["symbol"],
            example="Analyze AAPL for investment potential"
        ),
        QueryTemplate(
            id="compare_stocks",
            name="Stock Comparison",
            template="Compare {symbol1} vs {symbol2}",
            description="Head-to-head comparison of two stocks",
            category="comparison",
            required_params=["symbol1", "symbol2"],
            example="Compare AAPL vs GOOGL"
        ),
        QueryTemplate(
            id="sector_screen",
            name="Sector Screening",
            template="Find undervalued stocks in {sector}",
            description="Screen for opportunities in a specific sector",
            category="screening",
            required_params=["sector"],
            example="Find undervalued stocks in technology"
        ),
        QueryTemplate(
            id="growth_screen",
            name="Growth Screening",
            template="Find high-growth stocks under ${price}",
            description="Screen for growth opportunities within price range",
            category="screening",
            required_params=["price"],
            example="Find high-growth stocks under $100"
        ),
        QueryTemplate(
            id="dividend_screen",
            name="Dividend Screening",
            template="Best dividend stocks with yield > {yield}%",
            description="Find high-dividend paying stocks",
            category="income",
            required_params=["yield"],
            example="Best dividend stocks with yield > 3%"
        ),
        QueryTemplate(
            id="risk_assessment",
            name="Risk Analysis",
            template="Assess risk for {symbol} over {timeframe}",
            description="Evaluate risk for specific timeframe",
            category="risk",
            required_params=["symbol", "timeframe"],
            example="Assess risk for TSLA over 1 year"
        ),
        QueryTemplate(
            id="technical_analysis",
            name="Technical Analysis",
            template="Technical analysis of {symbol} with {indicators}",
            description="Technical indicators and chart patterns",
            category="technical",
            required_params=["symbol", "indicators"],
            example="Technical analysis of NVDA with RSI and MACD"
        ),
        QueryTemplate(
            id="earnings_play",
            name="Earnings Analysis",
            template="Analyze {symbol} before earnings on {date}",
            description="Pre-earnings analysis and prediction",
            category="events",
            required_params=["symbol", "date"],
            example="Analyze AMZN before earnings on Feb 1"
        ),
    ]

    if category:
        templates = [t for t in templates if t.category == category]

    return templates


@router.get("/examples", response_model=List[QueryExample])
async def get_query_examples(complexity: Optional[str] = None):
    """
    Get example queries to help users

    Provides examples of different query types and complexities
    """
    examples = [
        # Simple queries
        QueryExample(
            query="AAPL",
            description="Quick analysis of Apple stock",
            category="simple",
            complexity="beginner"
        ),
        QueryExample(
            query="Is Tesla overvalued?",
            description="Valuation analysis of Tesla",
            category="valuation",
            complexity="beginner"
        ),

        # Intermediate queries
        QueryExample(
            query="Compare Microsoft and Google for long-term investment",
            description="Detailed comparison for investment decision",
            category="comparison",
            complexity="intermediate"
        ),
        QueryExample(
            query="Find undervalued tech stocks with P/E < 20",
            description="Screen for value opportunities in tech",
            category="screening",
            complexity="intermediate"
        ),

        # Advanced queries
        QueryExample(
            query="Comprehensive analysis of NVDA including technical indicators, fundamental metrics, and competitive positioning",
            description="Deep dive analysis with multiple dimensions",
            category="comprehensive",
            complexity="advanced"
        ),
        QueryExample(
            query="Build a diversified portfolio with $100k focusing on growth and dividend stocks",
            description="Portfolio construction with specific criteria",
            category="portfolio",
            complexity="advanced"
        ),
        QueryExample(
            query="Analyze semiconductor sector rotation opportunities with focus on AI chip manufacturers",
            description="Sector analysis with thematic investing",
            category="sector",
            complexity="advanced"
        ),

        # Expert queries
        QueryExample(
            query="Perform Monte Carlo simulation for AAPL options strategy with 30-day expiry",
            description="Advanced options analysis with risk modeling",
            category="derivatives",
            complexity="expert"
        ),
        QueryExample(
            query="Pairs trading opportunity between XOM and CVX with statistical arbitrage analysis",
            description="Quantitative trading strategy analysis",
            category="quantitative",
            complexity="expert"
        ),
    ]

    if complexity:
        examples = [e for e in examples if e.complexity == complexity]

    return examples


@router.get("/intents")
async def get_supported_intents():
    """
    Get list of supported query intents

    Helps frontend understand what types of queries are supported
    """
    return {
        "intents": [
            {
                "value": intent.value,
                "name": intent.name,
                "description": f"{intent.value.capitalize()} queries",
                "examples": query_service.intent_keywords.get(intent, [])
            }
            for intent in QueryIntent
        ]
    }


@router.get("/validate")
async def validate_query(q: str = Query(..., min_length=1, max_length=500)):
    """
    Validate if a query can be processed

    Checks for required entities and returns validation result
    """
    try:
        enhancement = query_service.parse_query(q)

        # Validation rules
        is_valid = True
        issues = []
        warnings = []

        # Check for symbols if needed
        if enhancement.intent in [QueryIntent.ANALYZE, QueryIntent.COMPARE]:
            if not enhancement.extracted_entities.get('symbols'):
                is_valid = False
                issues.append("No stock symbols detected. Please include ticker symbols (e.g., AAPL, GOOGL)")

        # Check for comparison requirements
        if enhancement.intent == QueryIntent.COMPARE:
            if len(enhancement.extracted_entities.get('symbols', [])) < 2:
                is_valid = False
                issues.append("Comparison requires at least 2 stock symbols")

        # Warnings for better results
        if not enhancement.extracted_entities.get('timeframe'):
            warnings.append("No timeframe specified. Will use 1-year default")

        if enhancement.confidence < 0.5:
            warnings.append("Query intent unclear. Results may not match expectations")

        return {
            "is_valid": is_valid,
            "confidence": enhancement.confidence,
            "issues": issues,
            "warnings": warnings,
            "suggestions": enhancement.follow_up_suggestions[:2] if not is_valid else []
        }

    except Exception as e:
        return {
            "is_valid": False,
            "confidence": 0,
            "issues": [str(e)],
            "warnings": [],
            "suggestions": []
        }


@router.post("/enhance")
async def enhance_query(request: QueryParseRequest):
    """
    Enhance a query with additional context and parameters

    Used when user accepts AI suggestions to improve their query
    """
    try:
        enhancement = query_service.parse_query(request.query)

        # Apply user context if provided
        if request.user_context:
            # Add user preferences to enhancement
            if request.user_context.get('preferred_timeframe'):
                enhancement.suggested_params['timeframe'] = request.user_context['preferred_timeframe']

            if request.user_context.get('risk_tolerance'):
                enhancement.suggested_params['risk_tolerance'] = request.user_context['risk_tolerance']

            if request.user_context.get('investment_style'):
                style = request.user_context['investment_style']
                if style == 'value':
                    enhancement.suggested_params['focus_on_value_metrics'] = True
                elif style == 'growth':
                    enhancement.suggested_params['focus_on_growth_metrics'] = True

        # Build fully enhanced query
        enhanced_query_parts = [enhancement.enhanced_query]

        # Add user context to query
        if request.user_context:
            if request.user_context.get('investment_goal'):
                enhanced_query_parts.append(f"Investment goal: {request.user_context['investment_goal']}")

            if request.user_context.get('holding_period'):
                enhanced_query_parts.append(f"Holding period: {request.user_context['holding_period']}")

        final_enhanced_query = '. '.join(enhanced_query_parts)

        return {
            "original_query": request.query,
            "enhanced_query": final_enhanced_query,
            "applied_context": request.user_context,
            "recommended_params": enhancement.suggested_params,
            "confidence": enhancement.confidence
        }

    except Exception as e:
        logger.error(f"Query enhancement error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to enhance query: {str(e)}")