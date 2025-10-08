"""
Analysis History API Endpoints
Provides access to completed stock analyses
"""

from fastapi import APIRouter, HTTPException, Query
from typing import List, Optional
from datetime import datetime, timedelta
import logging

from services.mongodb_connection import mongodb_connection

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/v1/analyses", tags=["analyses"])


@router.get("/recent")
async def get_recent_analyses(
    limit: int = Query(default=5, ge=1, le=50),
    user_id: Optional[str] = None,
    status: Optional[str] = None
):
    """
    Get recent completed analyses for displaying AI trading signals.

    Args:
        limit: Maximum number of analyses to return (1-50, default 5)
        user_id: Optional filter by user ID
        status: Optional filter by status (e.g., 'completed')

    Returns:
        List of recent analyses with recommendations
    """
    try:
        db = mongodb_connection.get_database()
        analyses_collection = db['analyses']

        # Build query filter
        query_filter = {}
        if status:
            query_filter['status'] = status
        else:
            # Default to completed analyses only
            query_filter['status'] = 'completed'

        if user_id:
            query_filter['user_id'] = user_id

        # Query recent analyses - include _id as it's the analysis_id
        cursor = analyses_collection.find(
            query_filter
        ).sort('completed_at', -1).limit(limit)

        analyses = await cursor.to_list(length=limit)

        # If no analyses found, return empty list with structure
        if not analyses:
            logger.info(f"No analyses found with filter: {query_filter}")
            return {
                "analyses": [],
                "total": 0,
                "message": "No completed analyses available yet"
            }

        # Enrich analyses with results from analysis_results collection
        analysis_results_collection = db['analysis_results']

        enriched_analyses = []
        seen_symbols = set()  # Track symbols to avoid duplicates

        # Common words to exclude from symbol extraction
        EXCLUDED_WORDS = {'STOCK', 'STOCKS', 'ANALYZE', 'THE', 'AND', 'FOR', 'WITH'}

        for analysis in analyses:
            # Convert ObjectId to string and rename _id to id
            if '_id' in analysis:
                analysis_id = str(analysis['_id'])
                analysis['id'] = analysis_id
                del analysis['_id']
            else:
                analysis_id = analysis.get('id')

            if analysis_id:
                # Fetch the result
                result = await analysis_results_collection.find_one(
                    {"analysis_id": analysis_id},
                    {"_id": 0}
                )

                if result:
                    # Merge result into analysis
                    analysis['analysis'] = result.get('analysis', {})
                    analysis['recommendations'] = result.get('recommendations', {})

                # Extract symbols from query if not present
                if 'symbols' not in analysis and 'query' in analysis:
                    # Simple extraction: look for uppercase words that might be stock symbols
                    import re
                    words = analysis['query'].upper().split()
                    symbols = [
                        w for w in words
                        if w.isalpha() and 2 <= len(w) <= 5 and w not in EXCLUDED_WORDS
                    ]
                    if symbols:
                        analysis['symbols'] = symbols

                # Get primary symbol for deduplication
                primary_symbol = None
                if 'symbols' in analysis and analysis['symbols']:
                    # Filter out excluded words from symbols list
                    valid_symbols = [s for s in analysis['symbols'] if s not in EXCLUDED_WORDS]
                    if valid_symbols:
                        primary_symbol = valid_symbols[0]
                        analysis['symbols'] = valid_symbols  # Update with filtered list

                # Only include if this symbol hasn't been seen (most recent wins)
                if primary_symbol and primary_symbol not in seen_symbols:
                    seen_symbols.add(primary_symbol)
                    enriched_analyses.append(analysis)
                elif not primary_symbol:
                    # Include analyses without symbols
                    enriched_analyses.append(analysis)

        return {
            "analyses": enriched_analyses,
            "total": len(enriched_analyses)
        }

    except Exception as e:
        logger.error(f"Error fetching recent analyses: {e}")
        # Return empty structure on error instead of failing
        return {
            "analyses": [],
            "total": 0,
            "error": str(e)
        }


@router.get("/{analysis_id}")
async def get_analysis_by_id(analysis_id: str):
    """
    Get a specific analysis by ID.

    Args:
        analysis_id: The analysis ID

    Returns:
        Analysis details
    """
    try:
        db = mongodb_connection.get_database()
        analyses_collection = db['analyses']

        analysis = await analyses_collection.find_one(
            {"id": analysis_id},
            {"_id": 0}
        )

        if not analysis:
            raise HTTPException(status_code=404, detail=f"Analysis {analysis_id} not found")

        return analysis

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching analysis {analysis_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/user/{user_id}")
async def get_user_analyses(
    user_id: str,
    limit: int = Query(default=20, ge=1, le=100),
    skip: int = Query(default=0, ge=0)
):
    """
    Get all analyses for a specific user with pagination.

    Args:
        user_id: User ID
        limit: Number of results to return
        skip: Number of results to skip (for pagination)

    Returns:
        List of user's analyses
    """
    try:
        db = mongodb_connection.get_database()
        analyses_collection = db['analyses']

        # Count total for pagination
        total = await analyses_collection.count_documents({"user_id": user_id})

        # Get paginated results
        cursor = analyses_collection.find(
            {"user_id": user_id},
            {"_id": 0}
        ).sort('created_at', -1).skip(skip).limit(limit)

        analyses = await cursor.to_list(length=limit)

        return {
            "analyses": analyses,
            "total": total,
            "limit": limit,
            "skip": skip,
            "has_more": (skip + limit) < total
        }

    except Exception as e:
        logger.error(f"Error fetching user analyses: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{analysis_id}/lineage")
async def get_analysis_lineage(analysis_id: str):
    """
    Get complete data lineage tracking for a specific analysis.

    This endpoint returns comprehensive source attribution, data quality metrics,
    and transformation history for all data points used in the analysis.

    Args:
        analysis_id: The analysis ID

    Returns:
        Complete lineage report including:
        - Source attribution for each data point
        - Data quality scores
        - Freshness metrics
        - Transformation history
        - Upstream dependencies
        - Citations and references
    """
    try:
        db = mongodb_connection.get_database()
        analysis_results_collection = db['analysis_results']

        # Fetch the analysis result with lineage data
        result = await analysis_results_collection.find_one(
            {"analysis_id": analysis_id},
            {"_id": 0}
        )

        if not result:
            raise HTTPException(status_code=404, detail=f"Analysis {analysis_id} not found")

        # Extract lineage data from all agents
        analysis_data = result.get('analysis', {})

        lineage_report = {
            'analysis_id': analysis_id,
            'timestamp': result.get('timestamp', datetime.utcnow().isoformat()),
            'agents': {}
        }

        # Collect lineage from each agent
        agent_names = ['fundamental', 'technical', 'risk', 'synthesis']
        for agent_name in agent_names:
            agent_data = analysis_data.get(agent_name, {})
            lineage = agent_data.get('lineage', {})

            if lineage:
                # Extract key lineage metrics
                data_quality = lineage.get('data_quality', {})
                source_breakdown = lineage.get('source_breakdown', {})
                citations = agent_data.get('citations', [])

                lineage_report['agents'][agent_name] = {
                    'data_quality': {
                        'overall_score': data_quality.get('overall_score', 0),
                        'total_fields': data_quality.get('total_fields', 0),
                        'high_confidence_fields': data_quality.get('high_confidence_fields', 0),
                        'average_confidence': data_quality.get('average_confidence', 0)
                    },
                    'source_breakdown': source_breakdown,
                    'citations': citations[:10],  # Top 10 citations
                    'freshness': lineage.get('freshness', {}),
                    'reliability': lineage.get('reliability', {})
                }

        # Calculate aggregate lineage metrics
        total_fields = sum(
            agent.get('data_quality', {}).get('total_fields', 0)
            for agent in lineage_report['agents'].values()
        )

        avg_quality_score = (
            sum(
                agent.get('data_quality', {}).get('overall_score', 0)
                for agent in lineage_report['agents'].values()
            ) / len(lineage_report['agents'])
            if lineage_report['agents'] else 0
        )

        lineage_report['summary'] = {
            'total_tracked_fields': total_fields,
            'agents_with_lineage': len(lineage_report['agents']),
            'average_quality_score': round(avg_quality_score, 2),
            'quality_grade': _calculate_grade(avg_quality_score)
        }

        return lineage_report

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching analysis lineage {analysis_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


def _calculate_grade(score: float) -> str:
    """Convert quality score to letter grade"""
    if score >= 90:
        return 'A'
    elif score >= 80:
        return 'B'
    elif score >= 70:
        return 'C'
    elif score >= 60:
        return 'D'
    else:
        return 'F'
