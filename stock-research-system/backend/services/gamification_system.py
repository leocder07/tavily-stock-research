"""
Gamification & Achievement System (Phase 4)
Engage users with achievements, leaderboards, and progression tracking
"""

import logging
from typing import Dict, Any, List, Optional
from datetime import datetime
from enum import Enum

logger = logging.getLogger(__name__)


class AchievementType(Enum):
    """Achievement categories"""
    TRADING = "trading"
    ANALYSIS = "analysis"
    ACCURACY = "accuracy"
    PROFIT = "profit"
    STREAK = "streak"
    MILESTONE = "milestone"


class Achievement:
    """Achievement definition"""
    def __init__(
        self,
        id: str,
        name: str,
        description: str,
        category: AchievementType,
        points: int,
        icon: str,
        requirement: Dict[str, Any]
    ):
        self.id = id
        self.name = name
        self.description = description
        self.category = category
        self.points = points
        self.icon = icon
        self.requirement = requirement


# Define all achievements
ACHIEVEMENTS = [
    # Trading Achievements
    Achievement(
        id="first_trade",
        name="First Steps",
        description="Execute your first trade",
        category=AchievementType.TRADING,
        points=10,
        icon="🎯",
        requirement={"trades_count": 1}
    ),
    Achievement(
        id="active_trader",
        name="Active Trader",
        description="Execute 10 trades",
        category=AchievementType.TRADING,
        points=50,
        icon="📈",
        requirement={"trades_count": 10}
    ),
    Achievement(
        id="veteran_trader",
        name="Veteran Trader",
        description="Execute 100 trades",
        category=AchievementType.TRADING,
        points=200,
        icon="🏆",
        requirement={"trades_count": 100}
    ),

    # Analysis Achievements
    Achievement(
        id="curious_mind",
        name="Curious Mind",
        description="Run your first stock analysis",
        category=AchievementType.ANALYSIS,
        points=10,
        icon="🔍",
        requirement={"analyses_count": 1}
    ),
    Achievement(
        id="research_enthusiast",
        name="Research Enthusiast",
        description="Run 50 stock analyses",
        category=AchievementType.ANALYSIS,
        points=100,
        icon="📊",
        requirement={"analyses_count": 50}
    ),

    # Accuracy Achievements
    Achievement(
        id="sharp_eye",
        name="Sharp Eye",
        description="Achieve 70% recommendation accuracy",
        category=AchievementType.ACCURACY,
        points=150,
        icon="🎯",
        requirement={"accuracy": 0.70, "min_trades": 10}
    ),
    Achievement(
        id="master_predictor",
        name="Master Predictor",
        description="Achieve 80% recommendation accuracy",
        category=AchievementType.ACCURACY,
        points=300,
        icon="🔮",
        requirement={"accuracy": 0.80, "min_trades": 20}
    ),

    # Profit Achievements
    Achievement(
        id="profitable_trader",
        name="Profitable Trader",
        description="Achieve 10% total return",
        category=AchievementType.PROFIT,
        points=100,
        icon="💰",
        requirement={"total_return_pct": 10}
    ),
    Achievement(
        id="market_beater",
        name="Market Beater",
        description="Achieve 25% total return",
        category=AchievementType.PROFIT,
        points=250,
        icon="🚀",
        requirement={"total_return_pct": 25}
    ),

    # Streak Achievements
    Achievement(
        id="on_fire",
        name="On Fire!",
        description="5 consecutive profitable trades",
        category=AchievementType.STREAK,
        points=150,
        icon="🔥",
        requirement={"winning_streak": 5}
    ),
    Achievement(
        id="unstoppable",
        name="Unstoppable",
        description="10 consecutive profitable trades",
        category=AchievementType.STREAK,
        points=500,
        icon="⚡",
        requirement={"winning_streak": 10}
    ),

    # Milestone Achievements
    Achievement(
        id="portfolio_builder",
        name="Portfolio Builder",
        description="Build a portfolio worth $150,000",
        category=AchievementType.MILESTONE,
        points=200,
        icon="🏗️",
        requirement={"portfolio_value": 150000}
    ),
    Achievement(
        id="wealth_creator",
        name="Wealth Creator",
        description="Build a portfolio worth $250,000",
        category=AchievementType.MILESTONE,
        points=500,
        icon="💎",
        requirement={"portfolio_value": 250000}
    ),
]


class GamificationSystem:
    """
    Gamification engine for user engagement
    Tracks achievements, levels, and leaderboards
    """

    def __init__(self, database):
        self.database = database
        self.achievements_collection = database['user_achievements']
        self.leaderboard_collection = database['leaderboard']
        self.user_stats_collection = database['user_stats']

    async def check_and_award_achievements(self, user_id: str, user_stats: Dict[str, Any]) -> List[Achievement]:
        """Check if user earned any new achievements"""
        new_achievements = []

        # Get already earned achievements
        earned = await self.achievements_collection.find({"user_id": user_id}).to_list(None)
        earned_ids = {a['achievement_id'] for a in earned}

        # Check each achievement
        for achievement in ACHIEVEMENTS:
            if achievement.id in earned_ids:
                continue  # Already earned

            if self._check_requirement(achievement.requirement, user_stats):
                # Award achievement
                await self.achievements_collection.insert_one({
                    "user_id": user_id,
                    "achievement_id": achievement.id,
                    "earned_at": datetime.utcnow(),
                    "points": achievement.points
                })

                new_achievements.append(achievement)

                logger.info(f"[Gamification] User {user_id} earned achievement: {achievement.name}")

        # Update user total points
        if new_achievements:
            total_points = sum(a.points for a in new_achievements)
            await self._update_user_points(user_id, total_points)

        return new_achievements

    def _check_requirement(self, requirement: Dict[str, Any], user_stats: Dict[str, Any]) -> bool:
        """Check if user meets achievement requirement"""
        for key, value in requirement.items():
            user_value = user_stats.get(key, 0)

            if isinstance(value, (int, float)):
                if user_value < value:
                    return False
            elif isinstance(value, bool):
                if user_value != value:
                    return False

        return True

    async def _update_user_points(self, user_id: str, points: int):
        """Update user's total points and level"""
        await self.user_stats_collection.update_one(
            {"user_id": user_id},
            {
                "$inc": {"total_points": points},
                "$set": {"updated_at": datetime.utcnow()}
            },
            upsert=True
        )

        # Calculate level (100 points per level)
        user_stats = await self.user_stats_collection.find_one({"user_id": user_id})
        level = user_stats['total_points'] // 100

        await self.user_stats_collection.update_one(
            {"user_id": user_id},
            {"$set": {"level": level}}
        )

    async def get_user_progress(self, user_id: str) -> Dict[str, Any]:
        """Get user's gamification progress"""
        # Get stats
        stats = await self.user_stats_collection.find_one({"user_id": user_id})
        if not stats:
            stats = {
                "total_points": 0,
                "level": 0,
                "achievements_count": 0
            }

        # Get earned achievements
        earned = await self.achievements_collection.find({"user_id": user_id}).to_list(None)

        # Get next achievements
        earned_ids = {a['achievement_id'] for a in earned}
        next_achievements = [a for a in ACHIEVEMENTS if a.id not in earned_ids][:3]

        return {
            "level": stats.get('level', 0),
            "total_points": stats.get('total_points', 0),
            "points_to_next_level": (stats.get('level', 0) + 1) * 100 - stats.get('total_points', 0),
            "achievements_earned": len(earned),
            "achievements_total": len(ACHIEVEMENTS),
            "recent_achievements": [
                {
                    "id": a['achievement_id'],
                    "name": next((ach.name for ach in ACHIEVEMENTS if ach.id == a['achievement_id']), "Unknown"),
                    "earned_at": a['earned_at'].isoformat()
                }
                for a in sorted(earned, key=lambda x: x['earned_at'], reverse=True)[:5]
            ],
            "next_achievements": [
                {
                    "id": a.id,
                    "name": a.name,
                    "description": a.description,
                    "points": a.points,
                    "icon": a.icon
                }
                for a in next_achievements
            ]
        }

    async def get_leaderboard(self, period: str = "all_time", limit: int = 100) -> List[Dict]:
        """Get leaderboard rankings"""
        # Aggregate user stats
        pipeline = [
            {
                "$lookup": {
                    "from": "users",
                    "localField": "user_id",
                    "foreignField": "_id",
                    "as": "user"
                }
            },
            {
                "$unwind": "$user"
            },
            {
                "$project": {
                    "user_id": 1,
                    "username": "$user.username",
                    "total_points": 1,
                    "level": 1,
                    "portfolio_value": "$user.portfolio_value",
                    "total_return": "$user.total_return"
                }
            },
            {
                "$sort": {"total_points": -1}
            },
            {
                "$limit": limit
            }
        ]

        results = await self.user_stats_collection.aggregate(pipeline).to_list(None)

        leaderboard = []
        for rank, user in enumerate(results, 1):
            leaderboard.append({
                "rank": rank,
                "user_id": user['user_id'],
                "username": user.get('username', 'Anonymous'),
                "level": user.get('level', 0),
                "total_points": user.get('total_points', 0),
                "portfolio_value": user.get('portfolio_value', 0),
                "total_return": user.get('total_return', 0)
            })

        return leaderboard

    async def get_user_rank(self, user_id: str) -> Dict[str, Any]:
        """Get user's global rank"""
        user_stats = await self.user_stats_collection.find_one({"user_id": user_id})
        if not user_stats:
            return {"rank": None, "total_users": 0}

        # Count users with more points
        higher_ranked = await self.user_stats_collection.count_documents({
            "total_points": {"$gt": user_stats.get('total_points', 0)}
        })

        total_users = await self.user_stats_collection.count_documents({})

        return {
            "rank": higher_ranked + 1,
            "total_users": total_users,
            "percentile": round((1 - (higher_ranked / max(total_users, 1))) * 100, 1)
        }


# Global gamification system
gamification_system = None


def get_gamification_system(database):
    """Get or create gamification system instance"""
    global gamification_system
    if gamification_system is None:
        gamification_system = GamificationSystem(database)
    return gamification_system
