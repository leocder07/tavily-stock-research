"""
User Profile API Endpoints
Manages user profiles, preferences, and AI personality settings
"""

from fastapi import APIRouter, HTTPException, Depends, status
from pydantic import BaseModel, Field
from typing import Dict, Any, List, Optional
from datetime import datetime
import logging
from services.mongodb_connection import mongodb_connection

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/user", tags=["User Profile"])


class UserProfile(BaseModel):
    """User profile model."""
    user_id: str = Field(..., description="Clerk user ID")
    email: Optional[str] = None
    first_name: Optional[str] = None
    last_name: Optional[str] = None

    # Investment Profile
    investment_goals: List[str] = Field(default_factory=list)
    risk_tolerance: str = Field("moderate", pattern="^(conservative|moderate|aggressive)$")
    experience_level: str = Field("intermediate", pattern="^(beginner|intermediate|expert)$")

    # Preferences
    preferred_sectors: List[str] = Field(default_factory=list)
    investment_horizon: str = Field("long-term")
    capital_range: Optional[str] = None

    # AI Personality
    ai_personality: str = Field("balanced", description="Selected AI advisor personality")
    trading_style: Optional[str] = None

    # Dashboard Preferences
    dashboard_preferences: Dict[str, Any] = Field(default_factory=dict)
    notification_settings: Dict[str, bool] = Field(default_factory=dict)

    # Metadata
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    onboarding_completed: bool = Field(False)

    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class ProfileUpdate(BaseModel):
    """Profile update model."""
    investment_goals: Optional[List[str]] = None
    risk_tolerance: Optional[str] = None
    experience_level: Optional[str] = None
    preferred_sectors: Optional[List[str]] = None
    investment_horizon: Optional[str] = None
    ai_personality: Optional[str] = None
    dashboard_preferences: Optional[Dict[str, Any]] = None
    notification_settings: Optional[Dict[str, bool]] = None


class PersonalitySettings(BaseModel):
    """AI personality configuration."""
    personality_type: str
    risk_adjustment: float = Field(1.0, ge=0.5, le=2.0)
    analysis_depth: str = Field("comprehensive", pattern="^(basic|moderate|comprehensive)$")
    communication_style: str = Field("professional", pattern="^(casual|professional|technical)$")
    focus_areas: List[str] = Field(default_factory=list)


@router.post("/profile", response_model=Dict[str, Any])
async def create_user_profile(profile: UserProfile):
    """
    Create or update user profile.

    Args:
        profile: User profile data

    Returns:
        Success status and profile ID
    """
    try:
        db = mongodb_connection.get_database(async_mode=True)
        profiles_collection = db["user_profiles"]

        # Check if profile exists
        existing = await profiles_collection.find_one({"user_id": profile.user_id})

        profile_dict = profile.dict()
        profile_dict["updated_at"] = datetime.utcnow()

        if existing:
            # Update existing profile
            result = await profiles_collection.update_one(
                {"user_id": profile.user_id},
                {"$set": profile_dict}
            )
            logger.info(f"Updated profile for user: {profile.user_id}")
            return {
                "status": "updated",
                "profile_id": str(existing["_id"]),
                "user_id": profile.user_id
            }
        else:
            # Create new profile
            profile_dict["created_at"] = datetime.utcnow()
            profile_dict["onboarding_completed"] = True
            result = await profiles_collection.insert_one(profile_dict)
            logger.info(f"Created profile for user: {profile.user_id}")
            return {
                "status": "created",
                "profile_id": str(result.inserted_id),
                "user_id": profile.user_id
            }

    except Exception as e:
        logger.error(f"Error creating/updating profile: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to save profile: {str(e)}"
        )


@router.get("/profile/{user_id}", response_model=Dict[str, Any])
async def get_user_profile(user_id: str):
    """
    Get user profile by ID.

    Args:
        user_id: Clerk user ID

    Returns:
        User profile data
    """
    try:
        db = mongodb_connection.get_database(async_mode=True)
        profiles_collection = db["user_profiles"]

        profile = await profiles_collection.find_one({"user_id": user_id})

        if not profile:
            return {
                "profile": None,
                "exists": False,
                "message": "Profile not found"
            }

        # Convert ObjectId to string
        profile["_id"] = str(profile["_id"])

        return {
            "profile": profile,
            "exists": True,
            "message": "Profile retrieved successfully"
        }

    except Exception as e:
        logger.error(f"Error retrieving profile: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve profile: {str(e)}"
        )


@router.patch("/profile/{user_id}", response_model=Dict[str, Any])
async def update_user_profile(user_id: str, update: ProfileUpdate):
    """
    Update specific fields in user profile.

    Args:
        user_id: Clerk user ID
        update: Fields to update

    Returns:
        Update status
    """
    try:
        db = mongodb_connection.get_database(async_mode=True)
        profiles_collection = db["user_profiles"]

        # Build update dict (exclude None values)
        update_dict = {k: v for k, v in update.dict().items() if v is not None}
        update_dict["updated_at"] = datetime.utcnow()

        result = await profiles_collection.update_one(
            {"user_id": user_id},
            {"$set": update_dict}
        )

        if result.modified_count == 0:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Profile not found or no changes made"
            )

        logger.info(f"Updated profile fields for user: {user_id}")
        return {
            "status": "updated",
            "user_id": user_id,
            "fields_updated": list(update_dict.keys())
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating profile: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update profile: {str(e)}"
        )


@router.post("/profile/{user_id}/personality", response_model=Dict[str, Any])
async def set_ai_personality(user_id: str, settings: PersonalitySettings):
    """
    Set AI personality configuration for user.

    Args:
        user_id: Clerk user ID
        settings: Personality settings

    Returns:
        Configuration status
    """
    try:
        db = mongodb_connection.get_database(async_mode=True)
        profiles_collection = db["user_profiles"]

        # Update personality settings
        result = await profiles_collection.update_one(
            {"user_id": user_id},
            {
                "$set": {
                    "ai_personality": settings.personality_type,
                    "personality_settings": settings.dict(),
                    "updated_at": datetime.utcnow()
                }
            }
        )

        if result.modified_count == 0:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Profile not found"
            )

        logger.info(f"Updated AI personality for user: {user_id}")
        return {
            "status": "configured",
            "user_id": user_id,
            "personality": settings.personality_type,
            "settings": settings.dict()
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error setting personality: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to set personality: {str(e)}"
        )


@router.get("/profile/{user_id}/preferences", response_model=Dict[str, Any])
async def get_user_preferences(user_id: str):
    """
    Get user preferences for analysis customization.

    Args:
        user_id: Clerk user ID

    Returns:
        User preferences and settings
    """
    try:
        db = mongodb_connection.get_database(async_mode=True)
        profiles_collection = db["user_profiles"]

        profile = await profiles_collection.find_one(
            {"user_id": user_id},
            {
                "ai_personality": 1,
                "personality_settings": 1,
                "risk_tolerance": 1,
                "experience_level": 1,
                "investment_goals": 1,
                "preferred_sectors": 1,
                "investment_horizon": 1,
                "dashboard_preferences": 1
            }
        )

        if not profile:
            # Return default preferences
            return {
                "preferences": {
                    "ai_personality": "balanced",
                    "risk_tolerance": "moderate",
                    "experience_level": "intermediate",
                    "investment_goals": [],
                    "preferred_sectors": [],
                    "investment_horizon": "long-term"
                },
                "is_default": True
            }

        # Remove MongoDB _id
        profile.pop("_id", None)

        return {
            "preferences": profile,
            "is_default": False
        }

    except Exception as e:
        logger.error(f"Error getting preferences: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get preferences: {str(e)}"
        )


@router.delete("/profile/{user_id}", response_model=Dict[str, Any])
async def delete_user_profile(user_id: str):
    """
    Delete user profile.

    Args:
        user_id: Clerk user ID

    Returns:
        Deletion status
    """
    try:
        db = mongodb_connection.get_database(async_mode=True)
        profiles_collection = db["user_profiles"]

        result = await profiles_collection.delete_one({"user_id": user_id})

        if result.deleted_count == 0:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Profile not found"
            )

        logger.info(f"Deleted profile for user: {user_id}")
        return {
            "status": "deleted",
            "user_id": user_id
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting profile: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete profile: {str(e)}"
        )


@router.get("/profiles/analytics", response_model=Dict[str, Any])
async def get_user_analytics():
    """
    Get analytics on user profiles (admin endpoint).

    Returns:
        User analytics and statistics
    """
    try:
        db = mongodb_connection.get_database(async_mode=True)
        profiles_collection = db["user_profiles"]

        # Aggregate statistics
        pipeline = [
            {
                "$group": {
                    "_id": None,
                    "total_users": {"$sum": 1},
                    "risk_distribution": {
                        "$push": "$risk_tolerance"
                    },
                    "personality_distribution": {
                        "$push": "$ai_personality"
                    },
                    "experience_distribution": {
                        "$push": "$experience_level"
                    }
                }
            }
        ]

        result = await profiles_collection.aggregate(pipeline).to_list(1)

        if not result:
            return {
                "total_users": 0,
                "risk_distribution": {},
                "personality_distribution": {},
                "experience_distribution": {}
            }

        stats = result[0]

        # Count distributions
        def count_distribution(items):
            counts = {}
            for item in items:
                if item:
                    counts[item] = counts.get(item, 0) + 1
            return counts

        return {
            "total_users": stats["total_users"],
            "risk_distribution": count_distribution(stats["risk_distribution"]),
            "personality_distribution": count_distribution(stats["personality_distribution"]),
            "experience_distribution": count_distribution(stats["experience_distribution"])
        }

    except Exception as e:
        logger.error(f"Error getting analytics: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get analytics: {str(e)}"
        )