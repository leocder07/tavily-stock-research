"""
Drift Monitoring API Endpoints - Phase 4 Task 2

Provides REST API for accessing drift monitoring data and triggering manual checks.
"""

from fastapi import APIRouter, HTTPException, status
from typing import Dict, Any, Optional
from datetime import datetime
import logging

from services.drift_monitor import get_drift_monitor
from services.mongodb_connection import mongodb_connection

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/v1", tags=["drift_monitoring"])


@router.get("/analysis/{analysis_id}/drift")
async def get_analysis_drift(analysis_id: str):
    """
    Get drift status and metrics for an analysis.

    Shows when market conditions have changed significantly since the original analysis,
    including recommendations on whether to re-run the analysis.

    Args:
        analysis_id: Unique analysis identifier

    Returns:
        {
            "analysis_id": "uuid",
            "symbols": {
                "AAPL": {
                    "composite_score": 0.12,
                    "price_drift": 0.05,
                    "volume_drift": 0.30,
                    "volatility_drift": 0.15,
                    "sentiment_drift": 0.08,
                    "last_checked": "2025-10-07T12:00:00",
                    "requires_reanalysis": false,
                    "severity": "MEDIUM"
                }
            },
            "overall_drift_score": 0.12,
            "requires_reanalysis": false,
            "recommendation": "Analysis still valid - normal market fluctuation",
            "recent_alerts": [...],
            "last_monitored": "2025-10-07T12:00:00"
        }
    """
    try:
        drift_monitor = get_drift_monitor()
        drift_status = await drift_monitor.get_drift_status(analysis_id)

        return drift_status

    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Error getting drift status for analysis {analysis_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve drift status: {str(e)}"
        )


@router.post("/analysis/{analysis_id}/drift/check")
async def trigger_drift_check(analysis_id: str):
    """
    Manually trigger a drift check for an analysis.

    Useful for getting immediate drift status without waiting for the
    scheduled 5-minute monitoring cycle.

    Args:
        analysis_id: Unique analysis identifier

    Returns:
        Immediate drift status after check
    """
    try:
        drift_monitor = get_drift_monitor()

        # Get analysis
        db = mongodb_connection.get_database()
        analysis = await db.analyses.find_one({'id': analysis_id})

        if not analysis:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Analysis {analysis_id} not found"
            )

        # Trigger drift check
        await drift_monitor._check_analysis_drift(analysis)

        # Get updated status
        drift_status = await drift_monitor.get_drift_status(analysis_id)

        return {
            "message": "Drift check completed",
            "analysis_id": analysis_id,
            "drift_status": drift_status,
            "checked_at": datetime.utcnow().isoformat()
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error triggering drift check for analysis {analysis_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to trigger drift check: {str(e)}"
        )


@router.get("/analysis/{analysis_id}/drift/history")
async def get_drift_history(
    analysis_id: str,
    symbol: Optional[str] = None,
    limit: int = 50
):
    """
    Get historical drift measurements for an analysis.

    Args:
        analysis_id: Unique analysis identifier
        symbol: Optional filter by specific symbol
        limit: Maximum number of history records to return (default: 50)

    Returns:
        List of historical drift measurements with timestamps
    """
    try:
        db = mongodb_connection.get_database()

        # Build query
        query = {'analysis_id': analysis_id}
        if symbol:
            query['symbol'] = symbol.upper()

        # Get drift history
        cursor = db.drift_history.find(query).sort('timestamp', -1).limit(limit)
        history = []

        async for record in cursor:
            record.pop('_id', None)
            history.append(record)

        if not history:
            return {
                "analysis_id": analysis_id,
                "symbol": symbol,
                "history": [],
                "message": "No drift history found"
            }

        return {
            "analysis_id": analysis_id,
            "symbol": symbol,
            "history": history,
            "count": len(history)
        }

    except Exception as e:
        logger.error(f"Error getting drift history: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve drift history: {str(e)}"
        )


@router.get("/analysis/{analysis_id}/drift/alerts")
async def get_drift_alerts(
    analysis_id: str,
    severity: Optional[str] = None,
    limit: int = 20
):
    """
    Get drift alerts for an analysis.

    Args:
        analysis_id: Unique analysis identifier
        severity: Optional filter by severity (LOW, MEDIUM, HIGH, CRITICAL)
        limit: Maximum number of alerts to return (default: 20)

    Returns:
        List of drift alerts with details
    """
    try:
        db = mongodb_connection.get_database()

        # Build query
        query = {'analysis_id': analysis_id}
        if severity:
            query['severity'] = severity.upper()

        # Get alerts
        cursor = db.drift_alerts.find(query).sort('triggered_at', -1).limit(limit)
        alerts = []

        async for alert in cursor:
            alert.pop('_id', None)
            alerts.append(alert)

        return {
            "analysis_id": analysis_id,
            "alerts": alerts,
            "count": len(alerts),
            "severity_filter": severity
        }

    except Exception as e:
        logger.error(f"Error getting drift alerts: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve drift alerts: {str(e)}"
        )


@router.get("/drift/monitoring/status")
async def get_monitoring_status():
    """
    Get the status of the drift monitoring system.

    Returns:
        System status including whether monitoring is active,
        number of analyses being tracked, and recent activity
    """
    try:
        drift_monitor = get_drift_monitor()
        db = mongodb_connection.get_database()

        # Count active analyses
        from datetime import timedelta
        cutoff_time = datetime.utcnow() - timedelta(hours=24)
        active_count = await db.analyses.count_documents({
            'status': 'completed',
            'completed_at': {'$gte': cutoff_time}
        })

        # Count recent alerts (last hour)
        recent_cutoff = datetime.utcnow() - timedelta(hours=1)
        recent_alerts = await db.drift_alerts.count_documents({
            'triggered_at': {'$gte': recent_cutoff}
        })

        # Get alert severity breakdown
        severity_pipeline = [
            {'$match': {'triggered_at': {'$gte': recent_cutoff}}},
            {'$group': {'_id': '$severity', 'count': {'$sum': 1}}}
        ]
        severity_breakdown = {}
        async for result in db.drift_alerts.aggregate(severity_pipeline):
            severity_breakdown[result['_id']] = result['count']

        return {
            "monitoring_active": drift_monitor.is_running,
            "check_interval_seconds": drift_monitor.MONITOR_INTERVAL_SECONDS,
            "active_analyses_count": active_count,
            "recent_alerts_count": recent_alerts,
            "alert_severity_breakdown": severity_breakdown,
            "thresholds": {
                "price_drift": drift_monitor.PRICE_DRIFT_THRESHOLD,
                "volume_drift": drift_monitor.VOLUME_DRIFT_THRESHOLD,
                "volatility_drift": drift_monitor.VOLATILITY_DRIFT_THRESHOLD,
                "sentiment_drift": drift_monitor.SENTIMENT_DRIFT_THRESHOLD,
                "composite_medium": drift_monitor.COMPOSITE_THRESHOLD_MEDIUM,
                "composite_high": drift_monitor.COMPOSITE_THRESHOLD_HIGH,
                "composite_critical": drift_monitor.COMPOSITE_THRESHOLD_CRITICAL
            },
            "timestamp": datetime.utcnow().isoformat()
        }

    except Exception as e:
        logger.error(f"Error getting monitoring status: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve monitoring status: {str(e)}"
        )


@router.get("/drift/summary")
async def get_drift_summary():
    """
    Get summary of drift across all active analyses.

    Useful for dashboard overview of market drift conditions.

    Returns:
        Summary statistics of drift across all monitored analyses
    """
    try:
        db = mongodb_connection.get_database()

        # Get analyses requiring reanalysis
        analyses_cursor = db.analyses.find({
            'status': 'completed',
            'drift_status': {'$exists': True}
        })

        total_analyses = 0
        requires_reanalysis = 0
        high_drift_symbols = []

        async for analysis in analyses_cursor:
            total_analyses += 1
            drift_status = analysis.get('drift_status', {})

            for symbol, status in drift_status.items():
                if status.get('requires_reanalysis'):
                    requires_reanalysis += 1
                    high_drift_symbols.append({
                        'symbol': symbol,
                        'analysis_id': analysis.get('id'),
                        'composite_score': status.get('composite_score'),
                        'last_checked': status.get('last_checked')
                    })

        # Sort by composite score
        high_drift_symbols.sort(key=lambda x: x['composite_score'], reverse=True)

        # Get recent critical alerts
        cutoff = datetime.utcnow() - timedelta(hours=1)
        critical_alerts = await db.drift_alerts.count_documents({
            'severity': 'CRITICAL',
            'triggered_at': {'$gte': cutoff}
        })

        return {
            "summary": {
                "total_monitored_analyses": total_analyses,
                "analyses_requiring_reanalysis": requires_reanalysis,
                "critical_alerts_last_hour": critical_alerts
            },
            "high_drift_symbols": high_drift_symbols[:10],  # Top 10
            "timestamp": datetime.utcnow().isoformat()
        }

    except Exception as e:
        logger.error(f"Error getting drift summary: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve drift summary: {str(e)}"
        )
