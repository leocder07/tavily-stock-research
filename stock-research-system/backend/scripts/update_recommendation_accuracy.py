#!/usr/bin/env python3
"""
Scheduled Job: Update Recommendation Accuracy (Phase 4)
This script should be run daily to update actual returns for recommendations

Usage:
  python scripts/update_recommendation_accuracy.py --days 30

Cron example (daily at 9 PM ET):
  0 21 * * * cd /app && python scripts/update_recommendation_accuracy.py --days 1
"""

import asyncio
import argparse
import logging
import os
from datetime import datetime, timedelta
from typing import Dict, List
import yfinance as yf
from dotenv import load_dotenv

from services.bigquery_data_lake import get_bigquery_data_lake
from services.bigquery_integration import get_bigquery_integration

# Load environment
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


async def fetch_price_returns(symbol: str, start_date: datetime, end_date: datetime) -> Dict[str, float]:
    """
    Fetch actual price returns for a symbol over different periods

    Args:
        symbol: Stock symbol
        start_date: Entry date
        end_date: Current date

    Returns:
        Dict with actual_return_1d, actual_return_7d, actual_return_30d
    """
    try:
        ticker = yf.Ticker(symbol)

        # Get historical data
        hist = ticker.history(start=start_date, end=end_date)

        if hist.empty:
            logger.warning(f"No historical data for {symbol}")
            return {}

        # Calculate returns
        entry_price = hist.iloc[0]['Close']
        returns = {}

        # 1-day return
        if len(hist) >= 2:
            price_1d = hist.iloc[1]['Close']
            returns['actual_return_1d'] = ((price_1d - entry_price) / entry_price) * 100

        # 7-day return
        if len(hist) >= 8:
            price_7d = hist.iloc[min(7, len(hist)-1)]['Close']
            returns['actual_return_7d'] = ((price_7d - entry_price) / entry_price) * 100

        # 30-day return
        if len(hist) >= 31:
            price_30d = hist.iloc[min(30, len(hist)-1)]['Close']
            returns['actual_return_30d'] = ((price_30d - entry_price) / entry_price) * 100
        elif len(hist) > 0:
            # Use latest available price
            latest_price = hist.iloc[-1]['Close']
            returns['actual_return_30d'] = ((latest_price - entry_price) / entry_price) * 100

        logger.info(f"[{symbol}] Returns: {returns}")
        return returns

    except Exception as e:
        logger.error(f"Error fetching returns for {symbol}: {e}")
        return {}


async def update_recommendations(days_back: int = 30):
    """
    Update recommendation accuracy for the last N days

    Args:
        days_back: Number of days to look back
    """
    logger.info(f"Starting recommendation accuracy update for last {days_back} days")

    # Initialize BigQuery
    project_id = os.getenv('BIGQUERY_PROJECT_ID')
    credentials_path = os.getenv('BIGQUERY_CREDENTIALS_PATH')

    if not project_id:
        logger.error("BIGQUERY_PROJECT_ID not configured")
        return

    data_lake = get_bigquery_data_lake(project_id, credentials_path)
    integration = get_bigquery_integration(data_lake)

    if not integration or not integration.enabled:
        logger.error("BigQuery integration not available")
        return

    # Query recommendations that need updating
    cutoff_date = datetime.utcnow() - timedelta(days=days_back)

    query = f"""
    SELECT
        recommendation_id,
        symbol,
        timestamp,
        action,
        entry_price,
        actual_return_1d,
        actual_return_7d,
        actual_return_30d
    FROM `{project_id}.stock_research.recommendations`
    WHERE timestamp >= TIMESTAMP('{cutoff_date.isoformat()}')
      AND (
          actual_return_1d IS NULL
          OR actual_return_7d IS NULL
          OR actual_return_30d IS NULL
      )
    ORDER BY timestamp DESC
    LIMIT 100
    """

    try:
        query_job = data_lake.client.query(query)
        recommendations = list(query_job.result())

        logger.info(f"Found {len(recommendations)} recommendations to update")

        # Update each recommendation
        updated_count = 0
        for rec in recommendations:
            try:
                recommendation_id = rec.recommendation_id
                symbol = rec.symbol
                timestamp = rec.timestamp

                # Calculate how many days have passed
                days_elapsed = (datetime.utcnow() - timestamp).days

                # Fetch returns
                returns = await fetch_price_returns(
                    symbol,
                    timestamp,
                    datetime.utcnow()
                )

                if returns:
                    # Update with available returns
                    await integration.update_recommendation_accuracy(
                        recommendation_id=recommendation_id,
                        actual_return_1d=returns.get('actual_return_1d') if days_elapsed >= 1 else None,
                        actual_return_7d=returns.get('actual_return_7d') if days_elapsed >= 7 else None,
                        actual_return_30d=returns.get('actual_return_30d') if days_elapsed >= 30 else None
                    )

                    updated_count += 1
                    logger.info(f"Updated {recommendation_id} ({symbol}): {returns}")

                # Rate limiting - avoid hitting yfinance too hard
                await asyncio.sleep(0.5)

            except Exception as e:
                logger.error(f"Error updating recommendation {rec.recommendation_id}: {e}")
                continue

        logger.info(f"Successfully updated {updated_count}/{len(recommendations)} recommendations")

        # Generate summary report
        accuracy_stats = await data_lake.get_recommendation_accuracy(days=days_back)

        logger.info("=== Accuracy Report ===")
        for action, stats in accuracy_stats.items():
            logger.info(f"{action}: {stats['accuracy']*100:.1f}% accuracy ({stats['count']} recommendations)")

    except Exception as e:
        logger.error(f"Failed to update recommendations: {e}")


async def generate_performance_report(days: int = 30):
    """
    Generate performance report for monitoring

    Args:
        days: Number of days to analyze
    """
    logger.info(f"\n=== Performance Report (Last {days} days) ===")

    project_id = os.getenv('BIGQUERY_PROJECT_ID')
    credentials_path = os.getenv('BIGQUERY_CREDENTIALS_PATH')

    data_lake = get_bigquery_data_lake(project_id, credentials_path)

    if not data_lake or not data_lake.enabled:
        return

    try:
        # Overall accuracy
        accuracy = await data_lake.get_recommendation_accuracy(days)

        print("\nRecommendation Accuracy:")
        for action, stats in accuracy.items():
            print(f"  {action}: {stats['accuracy']*100:.1f}% ({stats['count']} trades)")

        # Agent performance
        agent_stats = await data_lake.get_agent_performance_stats(days)

        print("\nAgent Performance:")
        for agent_key, stats in sorted(agent_stats.items(), key=lambda x: x[1]['avg_cost'], reverse=True)[:5]:
            print(f"  {stats['agent']} ({stats['model']})")
            print(f"    Cost: ${stats['avg_cost']:.4f}")
            print(f"    Time: {stats['avg_time']:.2f}s")
            print(f"    Cache: {stats['cache_hit_rate']*100:.1f}%")
            print(f"    Quality: {stats['avg_quality']*100:.1f}%")

    except Exception as e:
        logger.error(f"Failed to generate report: {e}")


def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(description='Update recommendation accuracy')
    parser.add_argument('--days', type=int, default=30, help='Number of days to look back')
    parser.add_argument('--report-only', action='store_true', help='Only generate report without updates')

    args = parser.parse_args()

    if args.report_only:
        asyncio.run(generate_performance_report(args.days))
    else:
        asyncio.run(update_recommendations(args.days))
        asyncio.run(generate_performance_report(args.days))


if __name__ == "__main__":
    main()
