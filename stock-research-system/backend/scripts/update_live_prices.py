"""Update portfolio with live stock prices"""

import asyncio
import os
import sys

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from motor.motor_asyncio import AsyncIOMotorClient
from dotenv import load_dotenv
from services.live_price_service import LivePriceService

load_dotenv()

MONGODB_URL = os.getenv("MONGODB_URL", "mongodb://localhost:27017")
DATABASE_NAME = os.getenv("DATABASE_NAME", "stock_research")


async def update_prices():
    """Update portfolio with live prices"""
    client = AsyncIOMotorClient(MONGODB_URL)
    db = client[DATABASE_NAME]

    print("Fetching live prices and updating portfolio...")

    success = await LivePriceService.update_portfolio_prices(db, "vkpr15@gmail.com")

    if success:
        print("✅ Portfolio updated with live prices!")

        # Show updated data
        portfolios_collection = db['portfolios']
        portfolio = await portfolios_collection.find_one({"user_email": "vkpr15@gmail.com"})

        print(f"\nPortfolio Summary:")
        print(f"Total Value: ${portfolio['current_value']:,.2f}")
        print(f"Total Return: ${portfolio['total_return']:,.2f} ({portfolio['total_return_percent']:.2f}%)")
        print(f"\nUpdated Holdings:")
        for holding in portfolio['holdings']:
            print(f"  {holding['symbol']}: ${holding['current_price']:.2f} "
                  f"({holding['day_change']:+.2f}, {holding['day_change_percent']:+.2f}%) "
                  f"= ${holding['value']:,.2f}")
    else:
        print("❌ Failed to update portfolio")

    client.close()


if __name__ == "__main__":
    asyncio.run(update_prices())
