"""MongoDB connection manager with singleton pattern."""

import os
from typing import Optional
from pymongo import MongoClient
from pymongo.server_api import ServerApi
from motor.motor_asyncio import AsyncIOMotorClient
import certifi
import logging

logger = logging.getLogger(__name__)


class MongoDBConnection:
    """Singleton MongoDB connection manager."""

    _sync_client: Optional[MongoClient] = None
    _async_client: Optional[AsyncIOMotorClient] = None
    _database_name: str = None

    @classmethod
    def get_sync_client(cls) -> MongoClient:
        """Get or create synchronous MongoDB client."""
        if cls._sync_client is None:
            mongodb_url = os.getenv("MONGODB_URL")
            cls._database_name = os.getenv("DATABASE_NAME", "stock_research")

            # Create client with proper SSL configuration
            cls._sync_client = MongoClient(
                mongodb_url,
                server_api=ServerApi('1'),
                tlsCAFile=certifi.where(),
                tls=True,
                tlsAllowInvalidCertificates=False,
                maxPoolSize=50,
                minPoolSize=10,
                maxIdleTimeMS=45000,
                waitQueueTimeoutMS=5000,
                serverSelectionTimeoutMS=30000,
                retryWrites=True,
                w='majority'
            )

            # Test connection
            try:
                cls._sync_client.admin.command('ping')
                logger.info("MongoDB sync connection established successfully")
            except Exception as e:
                logger.error(f"Failed to connect to MongoDB: {e}")
                raise

        return cls._sync_client

    @classmethod
    def get_async_client(cls) -> AsyncIOMotorClient:
        """Get or create asynchronous MongoDB client."""
        if cls._async_client is None:
            mongodb_url = os.getenv("MONGODB_URL")
            cls._database_name = os.getenv("DATABASE_NAME", "stock_research")

            # Create async client with proper configuration
            cls._async_client = AsyncIOMotorClient(
                mongodb_url,
                server_api=ServerApi('1'),
                tlsCAFile=certifi.where(),
                tls=True,
                tlsAllowInvalidCertificates=False,
                maxPoolSize=50,
                minPoolSize=10,
                maxIdleTimeMS=45000,
                waitQueueTimeoutMS=5000,
                serverSelectionTimeoutMS=30000,
                retryWrites=True,
                w='majority'
            )

            logger.info("MongoDB async client created")

        return cls._async_client

    @classmethod
    def get_database(cls, async_mode=True):
        """Get database instance."""
        if async_mode:
            client = cls.get_async_client()
        else:
            client = cls.get_sync_client()

        return client[cls._database_name]

    @classmethod
    async def health_check(cls):
        """Check MongoDB connection health."""
        try:
            client = cls.get_async_client()
            # Ping the database to check connection
            result = await client.admin.command('ping')
            return {'status': 'healthy', 'ping': result}
        except Exception as e:
            logger.error(f"MongoDB health check failed: {e}")
            return {'status': 'unhealthy', 'error': str(e)}

    @classmethod
    def close_connections(cls):
        """Close all MongoDB connections."""
        if cls._sync_client:
            cls._sync_client.close()
            cls._sync_client = None
            logger.info("Closed sync MongoDB connection")

        if cls._async_client:
            cls._async_client.close()
            cls._async_client = None
            logger.info("Closed async MongoDB connection")


# Global instance
mongodb_connection = MongoDBConnection()