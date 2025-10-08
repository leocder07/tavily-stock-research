"""Database models and utilities for MongoDB."""

from typing import Dict, Any, List, Optional
from datetime import datetime
from pydantic import BaseModel, Field
from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase
import logging

logger = logging.getLogger(__name__)


class AnalysisDocument(BaseModel):
    """MongoDB document model for analyses collection."""
    id: str = Field(alias="_id")
    query: str
    user_id: Optional[str] = None
    priority: str = "normal"
    status: str = "pending"  # pending, processing, completed, failed
    config: Dict[str, Any] = Field(default_factory=dict)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    failed_at: Optional[datetime] = None
    execution_time: Optional[float] = None
    error: Optional[str] = None
    current_phase: Optional[str] = None
    agent_executions: List[Dict[str, Any]] = Field(default_factory=list)

    class Config:
        populate_by_name = True
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class AgentExecutionDocument(BaseModel):
    """MongoDB document model for agent executions."""
    id: str = Field(alias="_id")
    analysis_id: str
    agent_name: str
    agent_id: str
    status: str  # IDLE, PROCESSING, COMPLETED, FAILED
    started_at: datetime
    completed_at: Optional[datetime] = None
    execution_time: Optional[float] = None
    input_data: Dict[str, Any] = Field(default_factory=dict)
    output_data: Dict[str, Any] = Field(default_factory=dict)
    confidence_score: float = 0.0
    citations: List[Dict[str, str]] = Field(default_factory=list)
    error_message: Optional[str] = None
    retry_count: int = 0

    class Config:
        populate_by_name = True
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class AnalysisResultDocument(BaseModel):
    """MongoDB document model for analysis results."""
    analysis_id: str
    query: str
    symbols: List[str]
    recommendations: Dict[str, Any]
    executive_summary: str
    investment_thesis: str
    confidence_score: float
    market_data: Dict[str, Any] = Field(default_factory=dict)
    fundamental_analysis: Dict[str, Any] = Field(default_factory=dict)
    sentiment_analysis: Dict[str, Any] = Field(default_factory=dict)
    technical_analysis: Dict[str, Any] = Field(default_factory=dict)
    risk_analysis: Dict[str, Any] = Field(default_factory=dict)
    peer_comparison: Dict[str, Any] = Field(default_factory=dict)
    valuation_analysis: Dict[str, Any] = Field(default_factory=dict)  # NEW
    macro_analysis: Dict[str, Any] = Field(default_factory=dict)  # NEW
    insider_analysis: Dict[str, Any] = Field(default_factory=dict)  # NEW
    execution_time: float
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    metadata: Dict[str, Any] = Field(default_factory=dict)

    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class UserDocument(BaseModel):
    """MongoDB document model for users collection."""
    id: str = Field(alias="_id")
    email: str
    name: Optional[str] = None
    subscription_tier: str = "free"  # free, premium, enterprise
    created_at: datetime = Field(default_factory=datetime.utcnow)
    last_login: Optional[datetime] = None
    preferences: Dict[str, Any] = Field(default_factory=dict)
    usage_stats: Dict[str, Any] = Field(default_factory=dict)
    api_keys: List[Dict[str, Any]] = Field(default_factory=list)

    class Config:
        populate_by_name = True
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class DatabaseManager:
    """Manages database operations."""

    def __init__(self, client: AsyncIOMotorClient, database_name: str):
        """Initialize database manager.

        Args:
            client: MongoDB client
            database_name: Name of the database
        """
        self.client = client
        self.db: AsyncIOMotorDatabase = client[database_name]

    async def setup_indexes(self):
        """Create database indexes for optimal performance."""
        try:
            # Analyses collection indexes
            analyses = self.db.analyses
            await analyses.create_index("user_id")
            await analyses.create_index("status")
            await analyses.create_index([("created_at", -1)])
            await analyses.create_index([("user_id", 1), ("created_at", -1)])

            # Agent executions indexes
            executions = self.db.agent_executions
            await executions.create_index("analysis_id")
            await executions.create_index([("analysis_id", 1), ("agent_name", 1)])
            await executions.create_index([("started_at", -1)])

            # Results indexes
            results = self.db.analysis_results
            await results.create_index("analysis_id", unique=True)
            await results.create_index([("symbols", 1)])
            await results.create_index([("timestamp", -1)])

            # Users indexes
            users = self.db.users
            await users.create_index("email", unique=True)
            await users.create_index([("created_at", -1)])

            logger.info("Database indexes created successfully")

        except Exception as e:
            logger.error(f"Error creating indexes: {e}")
            raise

    async def save_analysis(self, analysis: AnalysisDocument) -> bool:
        """Save or update analysis document.

        Args:
            analysis: Analysis document to save

        Returns:
            Success status
        """
        try:
            doc = analysis.dict(by_alias=True, exclude_none=True)
            await self.db.analyses.replace_one(
                {"_id": doc["_id"]},
                doc,
                upsert=True
            )
            return True
        except Exception as e:
            logger.error(f"Error saving analysis: {e}")
            return False

    async def get_analysis(self, analysis_id: str) -> Optional[AnalysisDocument]:
        """Get analysis by ID.

        Args:
            analysis_id: Analysis ID

        Returns:
            Analysis document or None
        """
        try:
            doc = await self.db.analyses.find_one({"_id": analysis_id})
            if doc:
                return AnalysisDocument(**doc)
            return None
        except Exception as e:
            logger.error(f"Error fetching analysis: {e}")
            return None

    async def save_agent_execution(self, execution: AgentExecutionDocument) -> bool:
        """Save agent execution record.

        Args:
            execution: Agent execution document

        Returns:
            Success status
        """
        try:
            doc = execution.dict(by_alias=True, exclude_none=True)
            await self.db.agent_executions.insert_one(doc)

            # Update analysis with execution info
            await self.db.analyses.update_one(
                {"_id": execution.analysis_id},
                {
                    "$push": {
                        "agent_executions": {
                            "agent": execution.agent_name,
                            "status": execution.status,
                            "confidence": execution.confidence_score
                        }
                    }
                }
            )
            return True
        except Exception as e:
            logger.error(f"Error saving agent execution: {e}")
            return False

    async def save_result(self, result: AnalysisResultDocument) -> bool:
        """Save analysis result.

        Args:
            result: Analysis result document

        Returns:
            Success status
        """
        try:
            doc = result.dict(exclude_none=True)
            await self.db.analysis_results.replace_one(
                {"analysis_id": doc["analysis_id"]},
                doc,
                upsert=True
            )
            return True
        except Exception as e:
            logger.error(f"Error saving result: {e}")
            return False

    async def get_result(self, analysis_id: str) -> Optional[AnalysisResultDocument]:
        """Get analysis result.

        Args:
            analysis_id: Analysis ID

        Returns:
            Result document or None
        """
        try:
            doc = await self.db.analysis_results.find_one({"analysis_id": analysis_id})
            if doc:
                return AnalysisResultDocument(**doc)
            return None
        except Exception as e:
            logger.error(f"Error fetching result: {e}")
            return None

    async def get_user_analyses(
        self,
        user_id: str,
        limit: int = 10,
        skip: int = 0
    ) -> List[AnalysisDocument]:
        """Get analyses for a user.

        Args:
            user_id: User ID
            limit: Maximum number of results
            skip: Number of results to skip

        Returns:
            List of analysis documents
        """
        try:
            cursor = self.db.analyses.find(
                {"user_id": user_id}
            ).sort("created_at", -1).skip(skip).limit(limit)

            analyses = []
            async for doc in cursor:
                analyses.append(AnalysisDocument(**doc))
            return analyses
        except Exception as e:
            logger.error(f"Error fetching user analyses: {e}")
            return []

    async def get_analysis_stats(self) -> Dict[str, Any]:
        """Get system-wide analysis statistics.

        Returns:
            Statistics dictionary
        """
        try:
            total = await self.db.analyses.count_documents({})
            completed = await self.db.analyses.count_documents({"status": "completed"})
            failed = await self.db.analyses.count_documents({"status": "failed"})
            processing = await self.db.analyses.count_documents({"status": "processing"})

            # Average execution time
            pipeline = [
                {"$match": {"status": "completed", "execution_time": {"$exists": True}}},
                {"$group": {"_id": None, "avg_time": {"$avg": "$execution_time"}}}
            ]
            cursor = self.db.analyses.aggregate(pipeline)
            avg_time_result = await cursor.to_list(1)
            avg_time = avg_time_result[0]["avg_time"] if avg_time_result else 0

            return {
                "total_analyses": total,
                "completed": completed,
                "failed": failed,
                "processing": processing,
                "success_rate": (completed / total * 100) if total > 0 else 0,
                "average_execution_time": avg_time
            }
        except Exception as e:
            logger.error(f"Error getting stats: {e}")
            return {}