"""
Background Task Setup for Drift Monitoring - Phase 4 Task 2

Initializes and manages the drift monitoring background task.
Integrates with FastAPI lifespan to ensure proper startup/shutdown.
"""

import asyncio
import logging
from typing import Optional

from services.drift_monitor import DriftMonitor, get_drift_monitor
from services.mongodb_connection import mongodb_connection

logger = logging.getLogger(__name__)


class DriftMonitoringService:
    """
    Service to manage drift monitoring background tasks.

    Handles initialization, startup, and graceful shutdown of the
    drift monitoring system.
    """

    def __init__(self):
        self.drift_monitor: Optional[DriftMonitor] = None
        self.is_initialized = False

    async def initialize(self, tavily_api_key: Optional[str] = None):
        """
        Initialize the drift monitoring system.

        Args:
            tavily_api_key: Optional Tavily API key for sentiment analysis
        """
        try:
            logger.info("Initializing Drift Monitoring System...")

            # Get database instance
            database = mongodb_connection.get_database()

            # Create drift monitor instance
            self.drift_monitor = DriftMonitor(
                database=database,
                tavily_api_key=tavily_api_key
            )

            # Ensure MongoDB collections and indexes exist
            await self._setup_database_collections(database)

            self.is_initialized = True
            logger.info("Drift Monitoring System initialized successfully")

        except Exception as e:
            logger.error(f"Failed to initialize Drift Monitoring System: {e}")
            raise

    async def _setup_database_collections(self, database):
        """
        Ensure required MongoDB collections and indexes exist.

        Args:
            database: MongoDB database instance
        """
        try:
            # Create indexes for drift_history collection
            await database.drift_history.create_index([
                ('analysis_id', 1),
                ('timestamp', -1)
            ])
            await database.drift_history.create_index([
                ('analysis_id', 1),
                ('symbol', 1),
                ('timestamp', -1)
            ])

            # Create indexes for drift_alerts collection
            await database.drift_alerts.create_index([
                ('analysis_id', 1),
                ('triggered_at', -1)
            ])
            await database.drift_alerts.create_index([
                ('severity', 1),
                ('triggered_at', -1)
            ])

            # Create index on analyses for drift monitoring queries
            await database.analyses.create_index([
                ('status', 1),
                ('completed_at', -1)
            ])

            logger.info("Database collections and indexes created for drift monitoring")

        except Exception as e:
            # Log but don't fail - indexes might already exist
            logger.warning(f"Could not create all indexes (may already exist): {e}")

    async def start(self):
        """
        Start the drift monitoring background task.

        This begins the 5-minute monitoring cycle that checks all active
        analyses for drift.
        """
        if not self.is_initialized:
            raise RuntimeError("DriftMonitoringService not initialized. Call initialize() first.")

        try:
            logger.info("Starting Drift Monitoring background task...")
            await self.drift_monitor.start_monitoring()
            logger.info("Drift Monitoring is now active (5-minute check cycle)")

        except Exception as e:
            logger.error(f"Failed to start Drift Monitoring: {e}")
            raise

    async def stop(self):
        """
        Stop the drift monitoring background task gracefully.
        """
        if self.drift_monitor and self.drift_monitor.is_running:
            logger.info("Stopping Drift Monitoring background task...")
            await self.drift_monitor.stop_monitoring()
            logger.info("Drift Monitoring stopped")

    def get_monitor(self) -> DriftMonitor:
        """
        Get the drift monitor instance.

        Returns:
            DriftMonitor instance

        Raises:
            RuntimeError if not initialized
        """
        if not self.is_initialized or not self.drift_monitor:
            raise RuntimeError("DriftMonitoringService not initialized")

        return self.drift_monitor


# Global service instance
drift_monitoring_service = DriftMonitoringService()


async def initialize_drift_monitoring(tavily_api_key: Optional[str] = None):
    """
    Initialize drift monitoring system.

    Args:
        tavily_api_key: Optional Tavily API key for sentiment analysis
    """
    await drift_monitoring_service.initialize(tavily_api_key)


async def start_drift_monitoring():
    """Start the drift monitoring background task."""
    await drift_monitoring_service.start()


async def stop_drift_monitoring():
    """Stop the drift monitoring background task."""
    await drift_monitoring_service.stop()


def get_drift_monitoring_service() -> DriftMonitoringService:
    """Get the global drift monitoring service instance."""
    return drift_monitoring_service
