"""
Real-Time Drift Monitoring Service - Phase 4 Task 2

Monitors market conditions and detects when they change significantly enough
that analysis recommendations may no longer be valid.

Key Features:
- Track price, volume, volatility, and sentiment drift
- Calculate composite drift scores
- Trigger alerts when thresholds are exceeded
- Store drift history in MongoDB
- WebSocket notifications for real-time alerts
"""

import asyncio
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, asdict
import math

from services.yahoo_finance_service import YahooFinanceService
from services.mongodb_connection import mongodb_connection
from services.websocket_manager import websocket_manager
from services.tavily_service import TavilyMarketService

logger = logging.getLogger(__name__)


@dataclass
class DriftMetrics:
    """Container for drift metrics"""
    price_drift: float
    volume_drift: float
    volatility_drift: float
    sentiment_drift: float
    composite_score: float
    timestamp: datetime


@dataclass
class DriftAlert:
    """Drift alert data structure"""
    alert_id: str
    analysis_id: str
    alert_type: str  # PRICE_DRIFT, VOLUME_DRIFT, VOLATILITY_DRIFT, SENTIMENT_DRIFT, COMPOSITE_DRIFT
    severity: str  # LOW, MEDIUM, HIGH, CRITICAL
    message: str
    drift_metrics: Dict[str, float]
    triggered_at: datetime
    recommendation: str


class DriftMonitor:
    """
    Real-time drift monitoring system for stock analyses.

    Monitors key metrics and alerts when market conditions have changed
    significantly since the original analysis.
    """

    # Drift thresholds
    PRICE_DRIFT_THRESHOLD = 0.05  # 5% price change
    VOLUME_DRIFT_THRESHOLD = 0.50  # 50% volume change
    VOLATILITY_DRIFT_THRESHOLD = 0.30  # 30% volatility increase
    SENTIMENT_DRIFT_THRESHOLD = 0.20  # 20% sentiment change
    COMPOSITE_THRESHOLD_MEDIUM = 0.15  # 15% composite drift
    COMPOSITE_THRESHOLD_HIGH = 0.25  # 25% composite drift
    COMPOSITE_THRESHOLD_CRITICAL = 0.35  # 35% composite drift

    # Time window for considering an analysis "active"
    ACTIVE_ANALYSIS_HOURS = 24

    # Monitoring interval (5 minutes)
    MONITOR_INTERVAL_SECONDS = 300

    def __init__(self, database=None, tavily_api_key: Optional[str] = None):
        """
        Initialize drift monitor.

        Args:
            database: MongoDB database instance
            tavily_api_key: Optional Tavily API key for sentiment analysis
        """
        self.db = database or mongodb_connection.get_database()
        self.yahoo_service = YahooFinanceService()
        self.tavily_service = TavilyMarketService(api_key=tavily_api_key) if tavily_api_key else None
        self.monitoring_task: Optional[asyncio.Task] = None
        self.is_running = False

        logger.info("DriftMonitor initialized")

    async def start_monitoring(self):
        """Start the background monitoring task"""
        if self.is_running:
            logger.warning("DriftMonitor already running")
            return

        self.is_running = True
        self.monitoring_task = asyncio.create_task(self._monitoring_loop())
        logger.info("DriftMonitor started - checking every 5 minutes")

    async def stop_monitoring(self):
        """Stop the background monitoring task"""
        self.is_running = False
        if self.monitoring_task:
            self.monitoring_task.cancel()
            try:
                await self.monitoring_task
            except asyncio.CancelledError:
                pass
        logger.info("DriftMonitor stopped")

    async def _monitoring_loop(self):
        """Main monitoring loop - runs every 5 minutes"""
        while self.is_running:
            try:
                logger.info("Running drift monitoring cycle...")

                # Get active analyses (< 24 hours old)
                active_analyses = await self._get_active_analyses()
                logger.info(f"Monitoring {len(active_analyses)} active analyses")

                # Check each analysis for drift
                for analysis in active_analyses:
                    try:
                        await self._check_analysis_drift(analysis)
                    except Exception as e:
                        logger.error(f"Error checking drift for analysis {analysis.get('id')}: {e}")

                # Wait 5 minutes before next check
                await asyncio.sleep(self.MONITOR_INTERVAL_SECONDS)

            except asyncio.CancelledError:
                logger.info("Monitoring loop cancelled")
                break
            except Exception as e:
                logger.error(f"Error in monitoring loop: {e}")
                await asyncio.sleep(60)  # Wait 1 minute on error

    async def _get_active_analyses(self) -> List[Dict]:
        """
        Get all active analyses (completed in last 24 hours).

        Returns:
            List of active analysis documents
        """
        cutoff_time = datetime.utcnow() - timedelta(hours=self.ACTIVE_ANALYSIS_HOURS)

        cursor = self.db.analyses.find({
            'status': 'completed',
            'completed_at': {'$gte': cutoff_time}
        })

        analyses = await cursor.to_list(length=None)
        return analyses

    async def _check_analysis_drift(self, analysis: Dict):
        """
        Check a single analysis for drift.

        Args:
            analysis: Analysis document from MongoDB
        """
        analysis_id = analysis.get('id')
        symbols = analysis.get('symbols', [])

        if not symbols:
            logger.debug(f"No symbols found for analysis {analysis_id}")
            return

        # Get original analysis data
        analysis_result = await self.db.analysis_results.find_one(
            {'analysis_id': analysis_id}
        )

        if not analysis_result:
            logger.debug(f"No results found for analysis {analysis_id}")
            return

        # Check drift for each symbol
        for symbol in symbols:
            try:
                drift_metrics = await self._calculate_drift(
                    symbol=symbol,
                    analysis_result=analysis_result,
                    analysis_created=analysis.get('completed_at', datetime.utcnow())
                )

                if drift_metrics:
                    # Store drift metrics
                    await self._store_drift_metrics(analysis_id, symbol, drift_metrics)

                    # Check if alerts should be triggered
                    await self._check_and_trigger_alerts(
                        analysis_id=analysis_id,
                        symbol=symbol,
                        drift_metrics=drift_metrics
                    )

            except Exception as e:
                logger.error(f"Error calculating drift for {symbol} in analysis {analysis_id}: {e}")

    async def _calculate_drift(
        self,
        symbol: str,
        analysis_result: Dict,
        analysis_created: datetime
    ) -> Optional[DriftMetrics]:
        """
        Calculate drift metrics for a symbol.

        Args:
            symbol: Stock ticker symbol
            analysis_result: Original analysis result document
            analysis_created: When the analysis was completed

        Returns:
            DriftMetrics object or None if calculation fails
        """
        try:
            # Get current market data
            current_data = await self.yahoo_service.get_stock_price(symbol)
            if current_data.get('error'):
                logger.warning(f"Could not fetch current data for {symbol}")
                return None

            current_price = current_data.get('price', 0)
            current_volume = current_data.get('volume', 0)

            # Get historical data for volatility calculation
            hist_data = await self.yahoo_service.get_historical_data(symbol, period='5d')

            # Extract original analysis data
            market_data = analysis_result.get('market_data', {})
            original_price = market_data.get(symbol, {}).get('price', 0)
            original_volume = market_data.get(symbol, {}).get('volume', 0)

            # Calculate price drift
            price_drift = 0.0
            if original_price > 0:
                price_drift = abs(current_price - original_price) / original_price

            # Calculate volume drift
            volume_drift = 0.0
            if original_volume > 0:
                # Calculate average volume from historical data
                avg_volume = current_volume  # Simplified
                if 'history' in hist_data and hist_data['history']:
                    volumes = hist_data['history'].get('Volume', {})
                    if volumes:
                        avg_volume = sum(volumes.values()) / len(volumes)

                volume_drift = abs(current_volume - avg_volume) / avg_volume if avg_volume > 0 else 0

            # Calculate volatility drift (using standard deviation of recent prices)
            volatility_drift = 0.0
            if 'history' in hist_data and hist_data['history']:
                closes = hist_data['history'].get('Close', {})
                if closes and len(closes) > 1:
                    close_values = list(closes.values())
                    mean_price = sum(close_values) / len(close_values)
                    variance = sum((x - mean_price) ** 2 for x in close_values) / len(close_values)
                    std_dev = math.sqrt(variance)
                    current_volatility = std_dev / mean_price if mean_price > 0 else 0

                    # Compare to historical volatility (simplified - use price change as proxy)
                    original_volatility = 0.02  # Assume 2% baseline
                    volatility_drift = abs(current_volatility - original_volatility) / original_volatility if original_volatility > 0 else 0

            # Calculate sentiment drift (if Tavily available)
            sentiment_drift = 0.0
            if self.tavily_service:
                try:
                    current_sentiment = await self.tavily_service.get_market_sentiment(symbol)
                    sentiment_analysis = analysis_result.get('sentiment_analysis', {})
                    original_sentiment = sentiment_analysis.get(symbol, {}).get('score', 0)

                    if original_sentiment != 0:
                        current_score = current_sentiment.get('score', 0)
                        sentiment_drift = abs(current_score - original_sentiment) / abs(original_sentiment)
                except Exception as e:
                    logger.debug(f"Could not calculate sentiment drift: {e}")

            # Calculate composite drift score (weighted average)
            composite_score = (
                price_drift * 0.40 +
                volume_drift * 0.25 +
                volatility_drift * 0.20 +
                sentiment_drift * 0.15
            )

            return DriftMetrics(
                price_drift=price_drift,
                volume_drift=volume_drift,
                volatility_drift=volatility_drift,
                sentiment_drift=sentiment_drift,
                composite_score=composite_score,
                timestamp=datetime.utcnow()
            )

        except Exception as e:
            logger.error(f"Error calculating drift metrics for {symbol}: {e}")
            return None

    async def _store_drift_metrics(
        self,
        analysis_id: str,
        symbol: str,
        drift_metrics: DriftMetrics
    ):
        """
        Store drift metrics in MongoDB.

        Args:
            analysis_id: Analysis identifier
            symbol: Stock symbol
            drift_metrics: Calculated drift metrics
        """
        try:
            drift_doc = {
                'analysis_id': analysis_id,
                'symbol': symbol,
                'metrics': asdict(drift_metrics),
                'timestamp': drift_metrics.timestamp
            }

            # Insert into drift_history collection
            await self.db.drift_history.insert_one(drift_doc)

            # Update analysis document with latest drift status
            await self.db.analyses.update_one(
                {'id': analysis_id},
                {
                    '$set': {
                        f'drift_status.{symbol}': {
                            'composite_score': drift_metrics.composite_score,
                            'last_checked': drift_metrics.timestamp,
                            'requires_reanalysis': drift_metrics.composite_score > self.COMPOSITE_THRESHOLD_HIGH
                        }
                    }
                }
            )

        except Exception as e:
            logger.error(f"Error storing drift metrics: {e}")

    async def _check_and_trigger_alerts(
        self,
        analysis_id: str,
        symbol: str,
        drift_metrics: DriftMetrics
    ):
        """
        Check drift thresholds and trigger alerts if exceeded.

        Args:
            analysis_id: Analysis identifier
            symbol: Stock symbol
            drift_metrics: Calculated drift metrics
        """
        alerts = []

        # Check price drift
        if drift_metrics.price_drift > self.PRICE_DRIFT_THRESHOLD:
            alerts.append(self._create_alert(
                analysis_id=analysis_id,
                symbol=symbol,
                alert_type='PRICE_DRIFT',
                severity='HIGH' if drift_metrics.price_drift > 0.10 else 'MEDIUM',
                message=f"{symbol} price has changed {drift_metrics.price_drift*100:.1f}% since analysis",
                drift_metrics=drift_metrics
            ))

        # Check volume drift
        if drift_metrics.volume_drift > self.VOLUME_DRIFT_THRESHOLD:
            alerts.append(self._create_alert(
                analysis_id=analysis_id,
                symbol=symbol,
                alert_type='VOLUME_DRIFT',
                severity='MEDIUM',
                message=f"{symbol} volume has changed {drift_metrics.volume_drift*100:.1f}% from average",
                drift_metrics=drift_metrics
            ))

        # Check volatility drift
        if drift_metrics.volatility_drift > self.VOLATILITY_DRIFT_THRESHOLD:
            alerts.append(self._create_alert(
                analysis_id=analysis_id,
                symbol=symbol,
                alert_type='VOLATILITY_DRIFT',
                severity='HIGH',
                message=f"{symbol} volatility has increased {drift_metrics.volatility_drift*100:.1f}%",
                drift_metrics=drift_metrics
            ))

        # Check sentiment drift
        if drift_metrics.sentiment_drift > self.SENTIMENT_DRIFT_THRESHOLD:
            alerts.append(self._create_alert(
                analysis_id=analysis_id,
                symbol=symbol,
                alert_type='SENTIMENT_DRIFT',
                severity='MEDIUM',
                message=f"{symbol} sentiment has shifted {drift_metrics.sentiment_drift*100:.1f}%",
                drift_metrics=drift_metrics
            ))

        # Check composite drift
        if drift_metrics.composite_score > self.COMPOSITE_THRESHOLD_CRITICAL:
            alerts.append(self._create_alert(
                analysis_id=analysis_id,
                symbol=symbol,
                alert_type='COMPOSITE_DRIFT',
                severity='CRITICAL',
                message=f"{symbol} market conditions have significantly changed - reanalysis strongly recommended",
                drift_metrics=drift_metrics
            ))
        elif drift_metrics.composite_score > self.COMPOSITE_THRESHOLD_HIGH:
            alerts.append(self._create_alert(
                analysis_id=analysis_id,
                symbol=symbol,
                alert_type='COMPOSITE_DRIFT',
                severity='HIGH',
                message=f"{symbol} market conditions have changed substantially - consider reanalysis",
                drift_metrics=drift_metrics
            ))
        elif drift_metrics.composite_score > self.COMPOSITE_THRESHOLD_MEDIUM:
            alerts.append(self._create_alert(
                analysis_id=analysis_id,
                symbol=symbol,
                alert_type='COMPOSITE_DRIFT',
                severity='MEDIUM',
                message=f"{symbol} market conditions showing moderate drift",
                drift_metrics=drift_metrics
            ))

        # Send alerts
        for alert in alerts:
            await self._send_alert(alert)

    def _create_alert(
        self,
        analysis_id: str,
        symbol: str,
        alert_type: str,
        severity: str,
        message: str,
        drift_metrics: DriftMetrics
    ) -> DriftAlert:
        """Create a drift alert"""
        import uuid

        recommendation = ""
        if severity == 'CRITICAL':
            recommendation = "Immediate reanalysis required. Market conditions have changed dramatically."
        elif severity == 'HIGH':
            recommendation = "Reanalysis strongly recommended. Significant market changes detected."
        elif severity == 'MEDIUM':
            recommendation = "Monitor closely. Consider reanalysis if trend continues."
        else:
            recommendation = "Low priority. Normal market fluctuation."

        return DriftAlert(
            alert_id=str(uuid.uuid4()),
            analysis_id=analysis_id,
            alert_type=alert_type,
            severity=severity,
            message=f"[{symbol}] {message}",
            drift_metrics={
                'price_drift': drift_metrics.price_drift,
                'volume_drift': drift_metrics.volume_drift,
                'volatility_drift': drift_metrics.volatility_drift,
                'sentiment_drift': drift_metrics.sentiment_drift,
                'composite_score': drift_metrics.composite_score
            },
            triggered_at=datetime.utcnow(),
            recommendation=recommendation
        )

    async def _send_alert(self, alert: DriftAlert):
        """
        Send drift alert via WebSocket and store in database.

        Args:
            alert: DriftAlert object to send
        """
        try:
            # Store alert in database
            alert_doc = asdict(alert)
            await self.db.drift_alerts.insert_one(alert_doc)

            # Send WebSocket notification to analysis room
            await websocket_manager.send_to_room(
                message={
                    'type': 'drift_alert',
                    'alert': {
                        'id': alert.alert_id,
                        'analysis_id': alert.analysis_id,
                        'type': alert.alert_type,
                        'severity': alert.severity,
                        'message': alert.message,
                        'recommendation': alert.recommendation,
                        'metrics': alert.drift_metrics,
                        'timestamp': alert.triggered_at.isoformat()
                    }
                },
                room_name=f"analysis_{alert.analysis_id}"
            )

            logger.info(f"Drift alert sent: {alert.alert_type} - {alert.severity} for analysis {alert.analysis_id}")

        except Exception as e:
            logger.error(f"Error sending drift alert: {e}")

    async def get_drift_status(self, analysis_id: str) -> Dict[str, Any]:
        """
        Get current drift status for an analysis.

        Args:
            analysis_id: Analysis identifier

        Returns:
            Drift status information
        """
        try:
            # Get analysis
            analysis = await self.db.analyses.find_one({'id': analysis_id})
            if not analysis:
                raise ValueError(f"Analysis {analysis_id} not found")

            # Get latest drift metrics for each symbol
            symbols = analysis.get('symbols', [])
            drift_status = {}

            for symbol in symbols:
                # Get most recent drift history
                latest_drift = await self.db.drift_history.find_one(
                    {
                        'analysis_id': analysis_id,
                        'symbol': symbol
                    },
                    sort=[('timestamp', -1)]
                )

                if latest_drift:
                    metrics = latest_drift['metrics']
                    drift_status[symbol] = {
                        'composite_score': metrics['composite_score'],
                        'price_drift': metrics['price_drift'],
                        'volume_drift': metrics['volume_drift'],
                        'volatility_drift': metrics['volatility_drift'],
                        'sentiment_drift': metrics['sentiment_drift'],
                        'last_checked': metrics['timestamp'],
                        'requires_reanalysis': metrics['composite_score'] > self.COMPOSITE_THRESHOLD_HIGH,
                        'severity': self._get_severity(metrics['composite_score'])
                    }

            # Get recent alerts
            alerts_cursor = self.db.drift_alerts.find(
                {'analysis_id': analysis_id}
            ).sort('triggered_at', -1).limit(10)

            recent_alerts = []
            async for alert in alerts_cursor:
                alert.pop('_id', None)
                recent_alerts.append(alert)

            # Calculate overall status
            max_drift = max([status['composite_score'] for status in drift_status.values()]) if drift_status else 0

            return {
                'analysis_id': analysis_id,
                'symbols': drift_status,
                'overall_drift_score': max_drift,
                'requires_reanalysis': max_drift > self.COMPOSITE_THRESHOLD_HIGH,
                'recommendation': self._get_reanalysis_recommendation(max_drift),
                'recent_alerts': recent_alerts,
                'last_monitored': datetime.utcnow().isoformat()
            }

        except Exception as e:
            logger.error(f"Error getting drift status: {e}")
            raise

    def _get_severity(self, composite_score: float) -> str:
        """Get severity level from composite score"""
        if composite_score > self.COMPOSITE_THRESHOLD_CRITICAL:
            return 'CRITICAL'
        elif composite_score > self.COMPOSITE_THRESHOLD_HIGH:
            return 'HIGH'
        elif composite_score > self.COMPOSITE_THRESHOLD_MEDIUM:
            return 'MEDIUM'
        else:
            return 'LOW'

    def _get_reanalysis_recommendation(self, composite_score: float) -> str:
        """Get reanalysis recommendation based on drift score"""
        if composite_score > self.COMPOSITE_THRESHOLD_CRITICAL:
            return "Immediate reanalysis required - market conditions have changed dramatically"
        elif composite_score > self.COMPOSITE_THRESHOLD_HIGH:
            return "Reanalysis strongly recommended - significant drift detected"
        elif composite_score > self.COMPOSITE_THRESHOLD_MEDIUM:
            return "Monitor closely - moderate drift detected, consider reanalysis soon"
        else:
            return "Analysis still valid - normal market fluctuation"


# Global drift monitor instance (will be initialized in main.py)
drift_monitor: Optional[DriftMonitor] = None


def get_drift_monitor() -> DriftMonitor:
    """Get the global drift monitor instance"""
    global drift_monitor
    if drift_monitor is None:
        drift_monitor = DriftMonitor()
    return drift_monitor
