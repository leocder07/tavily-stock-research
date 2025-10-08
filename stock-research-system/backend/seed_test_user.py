"""
Seed script to add test user (vkpr15@gmail.com) with realistic portfolio and profile data.
Run this script to populate MongoDB with test data for development.

Usage:
    python3 seed_test_user.py
"""

import asyncio
from datetime import datetime, timedelta
from motor.motor_asyncio import AsyncIOMotorClient
import os
from dotenv import load_dotenv
import logging

# Load environment variables
load_dotenv()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Test user details - Using Clerk-compatible ID format
# Clerk user IDs typically look like: user_2abc123def456ghi789
TEST_USER_ID = "user_2test_tavily_vkpr15"
TEST_USER_EMAIL = "vkpr15@gmail.com"
TEST_USER_FIRST_NAME = "Tavily"
TEST_USER_LAST_NAME = "Test User"
TEST_USER_IMAGE_URL = "https://api.dicebear.com/7.x/avataaars/svg?seed=TavilyTest"

# Realistic portfolio holdings
HOLDINGS = [
    {
        "symbol": "AAPL",
        "company_name": "Apple Inc.",
        "shares": 50,
        "purchase_price": 180.50,
        "purchase_date": "2024-01-15",
        "notes": "Tech leader with strong ecosystem"
    },
    {
        "symbol": "MSFT",
        "company_name": "Microsoft Corporation",
        "shares": 30,
        "purchase_price": 370.25,
        "purchase_date": "2024-02-20",
        "notes": "Cloud computing and AI growth"
    },
    {
        "symbol": "GOOGL",
        "company_name": "Alphabet Inc.",
        "shares": 25,
        "purchase_price": 138.75,
        "purchase_date": "2024-03-10",
        "notes": "Search and AI dominance"
    },
    {
        "symbol": "NVDA",
        "company_name": "NVIDIA Corporation",
        "shares": 15,
        "purchase_price": 495.00,
        "purchase_date": "2024-04-05",
        "notes": "AI chip leader"
    },
    {
        "symbol": "TSLA",
        "company_name": "Tesla, Inc.",
        "shares": 20,
        "purchase_price": 245.30,
        "purchase_date": "2024-05-12",
        "notes": "EV and energy storage"
    },
    {
        "symbol": "AMZN",
        "company_name": "Amazon.com Inc.",
        "shares": 35,
        "purchase_price": 175.80,
        "purchase_date": "2024-06-01",
        "notes": "E-commerce and AWS"
    },
]


async def seed_database():
    """Seed MongoDB with test user data."""

    try:
        # Connect to MongoDB
        mongodb_url = os.getenv("MONGODB_URL")
        if not mongodb_url:
            raise ValueError("MONGODB_URL not found in environment variables")

        client = AsyncIOMotorClient(mongodb_url)
        db = client["stock_research"]  # Database name

        logger.info("Connected to MongoDB")

        # 1. Create User Profile
        logger.info("Creating user profile...")
        profiles_collection = db["user_profiles"]

        user_profile = {
            "user_id": TEST_USER_ID,
            "email": TEST_USER_EMAIL,
            "first_name": "Tavily",
            "last_name": "Test User",

            # Investment Profile
            "investment_goals": [
                "Long-term Wealth Building",
                "Retirement Planning",
                "Portfolio Diversification"
            ],
            "risk_tolerance": "moderate",
            "experience_level": "intermediate",

            # Preferences
            "preferred_sectors": [
                "Technology",
                "Healthcare",
                "Consumer Discretionary",
                "Financial Services"
            ],
            "investment_horizon": "long-term",
            "capital_range": "50k-100k",

            # AI Personality
            "ai_personality": "buffett",  # Conservative Sage
            "trading_style": "Value Investing",

            # Dashboard Preferences
            "dashboard_preferences": {
                "layout": "modern",
                "dataVisualization": "charts",
                "updateFrequency": "5min"
            },
            "notification_settings": {
                "email": True,
                "push": True,
                "priceAlerts": True
            },

            # Metadata
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow(),
            "onboarding_completed": True
        }

        await profiles_collection.replace_one(
            {"user_id": TEST_USER_ID},
            user_profile,
            upsert=True
        )
        logger.info(f"✓ User profile created for {TEST_USER_EMAIL}")

        # 2. Create Portfolio with Holdings
        logger.info("Creating portfolio...")
        portfolios_collection = db["portfolios"]

        # Calculate portfolio metrics
        total_cost_basis = sum(h["shares"] * h["purchase_price"] for h in HOLDINGS)

        # Assume current prices for realistic metrics (you can update these with real data)
        # For demo, assume 12% total return
        current_value = total_cost_basis * 1.12
        total_return = ((current_value - total_cost_basis) / total_cost_basis) * 100

        portfolio = {
            "user_id": TEST_USER_ID,
            "user_email": TEST_USER_EMAIL,
            "current_value": current_value,
            "cost_basis": total_cost_basis,
            "total_return_percent": total_return,
            "day_change": current_value * 0.015,  # 1.5% day change
            "day_change_percent": 1.5,
            "win_rate": 72.5,  # 72.5% win rate
            "sharpe_ratio": 1.8,  # 1.8 Sharpe ratio
            "holdings": HOLDINGS,
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow()
        }

        await portfolios_collection.replace_one(
            {"user_id": TEST_USER_ID},
            portfolio,
            upsert=True
        )
        logger.info(f"✓ Portfolio created with {len(HOLDINGS)} holdings")
        logger.info(f"  Total Value: ${current_value:,.2f}")
        logger.info(f"  Total Return: {total_return:.2f}%")
        logger.info(f"  Win Rate: {portfolio['win_rate']}%")
        logger.info(f"  Sharpe Ratio: {portfolio['sharpe_ratio']}")

        # 3. Create Sample Analysis History
        logger.info("Creating analysis history...")
        analyses_collection = db["analyses"]

        sample_analyses = [
            {
                "_id": f"analysis-{TEST_USER_ID}-1",
                "query": "Analyze AAPL for long-term investment",
                "user_id": TEST_USER_ID,
                "status": "completed",
                "created_at": datetime.utcnow() - timedelta(days=7),
                "completed_at": datetime.utcnow() - timedelta(days=7, seconds=120),
                "execution_time": 120.5
            },
            {
                "_id": f"analysis-{TEST_USER_ID}-2",
                "query": "Compare NVDA vs AMD",
                "user_id": TEST_USER_ID,
                "status": "completed",
                "created_at": datetime.utcnow() - timedelta(days=3),
                "completed_at": datetime.utcnow() - timedelta(days=3, seconds=95),
                "execution_time": 95.2
            },
            {
                "_id": f"analysis-{TEST_USER_ID}-3",
                "query": "Should I buy TSLA?",
                "user_id": TEST_USER_ID,
                "status": "completed",
                "created_at": datetime.utcnow() - timedelta(days=1),
                "completed_at": datetime.utcnow() - timedelta(days=1, seconds=105),
                "execution_time": 105.8
            }
        ]

        for analysis in sample_analyses:
            await analyses_collection.replace_one(
                {"_id": analysis["_id"]},
                analysis,
                upsert=True
            )

        logger.info(f"✓ Created {len(sample_analyses)} sample analyses")

        # 4. Create User Document
        logger.info("Creating user document...")
        users_collection = db["users"]

        user_doc = {
            "_id": TEST_USER_ID,
            "email": TEST_USER_EMAIL,
            "name": "Tavily Test User",
            "subscription_tier": "premium",
            "created_at": datetime.utcnow(),
            "last_login": datetime.utcnow(),
            "preferences": {
                "theme": "dark",
                "language": "en",
                "timezone": "America/New_York"
            },
            "usage_stats": {
                "total_analyses": 3,
                "analyses_this_month": 3,
                "last_analysis_date": datetime.utcnow() - timedelta(days=1)
            }
        }

        await users_collection.replace_one(
            {"_id": TEST_USER_ID},
            user_doc,
            upsert=True
        )
        logger.info(f"✓ User document created")

        logger.info("\n" + "="*60)
        logger.info("✓ Test user seeding completed successfully!")
        logger.info("="*60)
        logger.info(f"\nTest User Credentials:")
        logger.info(f"  Email: {TEST_USER_EMAIL}")
        logger.info(f"  Password: tavilyUser@123")
        logger.info(f"  User ID: {TEST_USER_ID}")
        logger.info(f"\nPortfolio Summary:")
        logger.info(f"  Holdings: {len(HOLDINGS)} stocks")
        logger.info(f"  Total Value: ${current_value:,.2f}")
        logger.info(f"  Total Return: {total_return:.2f}%")
        logger.info(f"  Win Rate: {portfolio['win_rate']}%")
        logger.info(f"  Sharpe Ratio: {portfolio['sharpe_ratio']}")
        logger.info("\n" + "="*60)

        client.close()

    except Exception as e:
        logger.error(f"Error seeding database: {e}")
        raise


if __name__ == "__main__":
    asyncio.run(seed_database())
