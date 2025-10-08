"""Seed portfolio data for user vkpr15@gmail.com"""

import asyncio
import os
from datetime import datetime, timedelta
from motor.motor_asyncio import AsyncIOMotorClient
from dotenv import load_dotenv

load_dotenv()

MONGODB_URL = os.getenv("MONGODB_URL", "mongodb://localhost:27017")
DATABASE_NAME = os.getenv("DATABASE_NAME", "stock_research")

# Portfolio data for vkpr15@gmail.com
PORTFOLIO_DATA = {
    "user_email": "vkpr15@gmail.com",
    "user_id": "user_vkpr15",
    "holdings": [
        {
            "symbol": "AAPL",
            "name": "Apple Inc.",
            "shares": 50,
            "avg_cost": 145.20,
            "current_price": 195.20,
            "sector": "Technology",
            "purchase_date": "2023-01-15"
        },
        {
            "symbol": "MSFT",
            "name": "Microsoft Corporation",
            "shares": 30,
            "avg_cost": 320.50,
            "current_price": 425.30,
            "sector": "Technology",
            "purchase_date": "2023-02-20"
        },
        {
            "symbol": "GOOGL",
            "name": "Alphabet Inc.",
            "shares": 25,
            "avg_cost": 125.40,
            "current_price": 162.80,
            "sector": "Technology",
            "purchase_date": "2023-03-10"
        },
        {
            "symbol": "NVDA",
            "name": "NVIDIA Corporation",
            "shares": 40,
            "avg_cost": 420.00,
            "current_price": 880.50,
            "sector": "Technology",
            "purchase_date": "2023-04-05"
        },
        {
            "symbol": "TSLA",
            "name": "Tesla Inc.",
            "shares": 20,
            "avg_cost": 180.00,
            "current_price": 242.00,
            "sector": "Automotive",
            "purchase_date": "2023-05-12"
        }
    ],
    "total_invested": 0.0,  # Will be calculated
    "current_value": 0.0,  # Will be calculated
    "total_return": 0.0,  # Will be calculated
    "total_return_percent": 0.0,  # Will be calculated
    "created_at": datetime.utcnow(),
    "updated_at": datetime.utcnow()
}

async def seed_portfolio():
    """Seed portfolio data into MongoDB"""
    client = AsyncIOMotorClient(MONGODB_URL)
    db = client[DATABASE_NAME]
    portfolios_collection = db['portfolios']

    # Calculate totals
    total_invested = sum(holding['shares'] * holding['avg_cost'] for holding in PORTFOLIO_DATA['holdings'])
    current_value = sum(holding['shares'] * holding['current_price'] for holding in PORTFOLIO_DATA['holdings'])
    total_return = current_value - total_invested
    total_return_percent = (total_return / total_invested) * 100 if total_invested > 0 else 0

    PORTFOLIO_DATA['total_invested'] = round(total_invested, 2)
    PORTFOLIO_DATA['current_value'] = round(current_value, 2)
    PORTFOLIO_DATA['total_return'] = round(total_return, 2)
    PORTFOLIO_DATA['total_return_percent'] = round(total_return_percent, 2)

    # Calculate per-holding metrics
    for holding in PORTFOLIO_DATA['holdings']:
        holding['value'] = round(holding['shares'] * holding['current_price'], 2)
        holding['cost_basis'] = round(holding['shares'] * holding['avg_cost'], 2)
        holding['total_return'] = round(holding['value'] - holding['cost_basis'], 2)
        holding['total_return_percent'] = round((holding['total_return'] / holding['cost_basis']) * 100, 2)
        holding['allocation'] = round((holding['value'] / current_value) * 100, 2)
        # Simulate day change (random between -3% and +3%)
        import random
        random.seed(42)  # Fixed seed for consistent results
        day_change_percent = random.uniform(-3, 3)
        holding['day_change'] = round((holding['current_price'] * day_change_percent) / 100, 2)
        holding['day_change_percent'] = round(day_change_percent, 2)

    # Delete existing portfolio for this user
    await portfolios_collection.delete_many({"user_email": "vkpr15@gmail.com"})

    # Insert new portfolio
    result = await portfolios_collection.insert_one(PORTFOLIO_DATA)

    print(f"✅ Portfolio seeded successfully!")
    print(f"Portfolio ID: {result.inserted_id}")
    print(f"Total Invested: ${PORTFOLIO_DATA['total_invested']:,.2f}")
    print(f"Current Value: ${PORTFOLIO_DATA['current_value']:,.2f}")
    print(f"Total Return: ${PORTFOLIO_DATA['total_return']:,.2f} ({PORTFOLIO_DATA['total_return_percent']:.2f}%)")
    print(f"\nHoldings:")
    for holding in PORTFOLIO_DATA['holdings']:
        print(f"  {holding['symbol']}: {holding['shares']} shares @ ${holding['current_price']} = ${holding['value']:,.2f}")

    client.close()

if __name__ == "__main__":
    asyncio.run(seed_portfolio())
