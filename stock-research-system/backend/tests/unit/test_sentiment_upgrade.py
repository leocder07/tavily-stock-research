"""
Test Script for Multi-Source Sentiment Upgrade
Tests all components and validates fallback behavior
"""

import asyncio
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Test imports
try:
    from agents.sentiment_sources import (
        TwitterSentimentSource,
        RedditSentimentSource,
        NewsAPISentimentSource,
        TavilySentimentSource
    )
    from agents.sentiment_aggregator import SentimentAggregator
    from agents.tavily_agents.enhanced_sentiment_tracker_agent import EnhancedSentimentTrackerAgent
    print("✓ All imports successful")
except ImportError as e:
    print(f"✗ Import failed: {e}")
    exit(1)


async def test_individual_sources():
    """Test each sentiment source individually"""
    print("\n" + "="*60)
    print("TESTING INDIVIDUAL SOURCES")
    print("="*60)

    test_symbol = "AAPL"

    # Test Twitter
    print("\n[1/4] Testing Twitter Source...")
    twitter = TwitterSentimentSource(bearer_token=os.getenv('TWITTER_BEARER_TOKEN'))
    if await twitter.is_available():
        result = await twitter.fetch_sentiment(test_symbol)
        if result:
            print(f"  ✓ Twitter: {result.sentiment_label} (score: {result.sentiment_score:.3f}, volume: {result.volume})")
        else:
            print("  ⚠ Twitter returned no data")
    else:
        print("  ⚠ Twitter API not configured")

    # Test Reddit
    print("\n[2/4] Testing Reddit Source...")
    reddit = RedditSentimentSource(
        client_id=os.getenv('REDDIT_CLIENT_ID'),
        client_secret=os.getenv('REDDIT_CLIENT_SECRET')
    )
    if await reddit.is_available():
        result = await reddit.fetch_sentiment(test_symbol)
        if result:
            print(f"  ✓ Reddit: {result.sentiment_label} (score: {result.sentiment_score:.3f}, volume: {result.volume})")
        else:
            print("  ⚠ Reddit returned no data")
    else:
        print("  ⚠ Reddit API not configured")

    # Test News
    print("\n[3/4] Testing News Source...")
    news = NewsAPISentimentSource(
        alpha_vantage_key=os.getenv('ALPHA_VANTAGE_API_KEY'),
        news_api_key=os.getenv('NEWS_API_KEY')
    )
    if await news.is_available():
        result = await news.fetch_sentiment(test_symbol)
        if result:
            print(f"  ✓ News: {result.sentiment_label} (score: {result.sentiment_score:.3f}, volume: {result.volume})")
        else:
            print("  ⚠ News returned no data")
    else:
        print("  ⚠ News API not configured")

    # Test Tavily
    print("\n[4/4] Testing Tavily Source...")
    tavily = TavilySentimentSource(tavily_api_key=os.getenv('TAVILY_API_KEY'))
    if await tavily.is_available():
        result = await tavily.fetch_sentiment(test_symbol)
        if result:
            print(f"  ✓ Tavily: {result.sentiment_label} (score: {result.sentiment_score:.3f}, volume: {result.volume})")
        else:
            print("  ⚠ Tavily returned no data")
    else:
        print("  ⚠ Tavily API not configured")


async def test_aggregator():
    """Test sentiment aggregator"""
    print("\n" + "="*60)
    print("TESTING SENTIMENT AGGREGATOR")
    print("="*60)

    aggregator = SentimentAggregator(
        twitter_api_key=os.getenv('TWITTER_BEARER_TOKEN'),
        reddit_client_id=os.getenv('REDDIT_CLIENT_ID'),
        reddit_client_secret=os.getenv('REDDIT_CLIENT_SECRET'),
        alpha_vantage_key=os.getenv('ALPHA_VANTAGE_API_KEY'),
        news_api_key=os.getenv('NEWS_API_KEY'),
        tavily_api_key=os.getenv('TAVILY_API_KEY')
    )

    test_symbol = "AAPL"
    print(f"\nAggregating sentiment for {test_symbol}...")

    result = await aggregator.aggregate_sentiment(test_symbol)

    print(f"\n  Overall Sentiment: {result['aggregated_sentiment']['sentiment_label']}")
    print(f"  Sentiment Score: {result['aggregated_sentiment']['sentiment_score']:.3f}")
    print(f"  Confidence: {result['aggregated_sentiment']['confidence']:.3f}")
    print(f"  Total Volume: {result['aggregated_sentiment']['total_volume']}")
    print(f"  Sources Used: {result['aggregated_sentiment']['source_count']}")
    print(f"  Divergence: {result['aggregated_sentiment']['divergence']:.3f}")

    if result['source_breakdown']:
        print("\n  Source Breakdown:")
        for source in result['source_breakdown']:
            print(f"    - {source['source']}: {source['sentiment_label']} "
                  f"(score: {source['sentiment_score']:.3f}, weight: {source['weight']:.2f})")

    if result['bull_arguments']:
        print(f"\n  Bull Arguments ({len(result['bull_arguments'])}):")
        for arg in result['bull_arguments'][:3]:
            print(f"    • {arg}")

    if result['bear_arguments']:
        print(f"\n  Bear Arguments ({len(result['bear_arguments'])}):")
        for arg in result['bear_arguments'][:3]:
            print(f"    • {arg}")

    print(f"\n  Quality Tier: {result['metadata'].get('available_sources', [])}")


async def test_enhanced_agent():
    """Test enhanced sentiment tracker agent"""
    print("\n" + "="*60)
    print("TESTING ENHANCED SENTIMENT AGENT")
    print("="*60)

    agent = EnhancedSentimentTrackerAgent(
        tavily_api_key=os.getenv('TAVILY_API_KEY'),
        twitter_api_key=os.getenv('TWITTER_BEARER_TOKEN'),
        reddit_client_id=os.getenv('REDDIT_CLIENT_ID'),
        reddit_client_secret=os.getenv('REDDIT_CLIENT_SECRET'),
        alpha_vantage_key=os.getenv('ALPHA_VANTAGE_API_KEY'),
        news_api_key=os.getenv('NEWS_API_KEY'),
        use_legacy_fallback=True
    )

    test_symbols = ["AAPL", "TSLA", "NVDA"]

    for symbol in test_symbols:
        print(f"\n[{symbol}] Analyzing sentiment...")

        result = await agent.analyze({'symbol': symbol, 'timeframe': '24h'})

        print(f"  Status: {result.get('status', 'unknown')}")
        print(f"  Sentiment: {result['aggregated_sentiment']['sentiment_label']}")
        print(f"  Score: {result['aggregated_sentiment']['sentiment_score']:.3f}")
        print(f"  Confidence: {result['aggregated_sentiment']['confidence']:.3f}")
        print(f"  Sources: {result['aggregated_sentiment']['source_count']}")
        print(f"  Quality: {result['data_lineage'].get('quality_tier', 'unknown')}")

        if result.get('error'):
            print(f"  ⚠ Error: {result['error']}")


async def test_fallback_behavior():
    """Test fallback behavior with limited APIs"""
    print("\n" + "="*60)
    print("TESTING FALLBACK BEHAVIOR")
    print("="*60)

    # Test with only Tavily (simulating other APIs unavailable)
    print("\n[Test 1] Only Tavily configured...")
    agent = EnhancedSentimentTrackerAgent(
        tavily_api_key=os.getenv('TAVILY_API_KEY'),
        twitter_api_key=None,
        reddit_client_id=None,
        reddit_client_secret=None,
        alpha_vantage_key=None,
        news_api_key=None,
        use_legacy_fallback=True
    )

    result = await agent.analyze({'symbol': 'AAPL'})
    print(f"  Sources Used: {result['aggregated_sentiment']['source_count']}")
    print(f"  Status: {result.get('status', 'unknown')}")

    # Test with no APIs (should use legacy fallback)
    print("\n[Test 2] No APIs configured (testing legacy fallback)...")
    agent_no_apis = EnhancedSentimentTrackerAgent(
        tavily_api_key=os.getenv('TAVILY_API_KEY'),
        twitter_api_key=None,
        reddit_client_id=None,
        reddit_client_secret=None,
        alpha_vantage_key=None,
        news_api_key=None,
        use_legacy_fallback=True
    )

    result = await agent_no_apis.analyze({'symbol': 'AAPL'})
    print(f"  Status: {result.get('status', 'unknown')}")
    print(f"  Agent Used: {result.get('agent', 'unknown')}")


async def main():
    """Run all tests"""
    print("\n" + "="*60)
    print("MULTI-SOURCE SENTIMENT UPGRADE TEST SUITE")
    print("="*60)

    # Check environment
    print("\nEnvironment Check:")
    print(f"  TAVILY_API_KEY: {'✓' if os.getenv('TAVILY_API_KEY') else '✗'}")
    print(f"  TWITTER_BEARER_TOKEN: {'✓' if os.getenv('TWITTER_BEARER_TOKEN') else '✗'}")
    print(f"  REDDIT_CLIENT_ID: {'✓' if os.getenv('REDDIT_CLIENT_ID') else '✗'}")
    print(f"  ALPHA_VANTAGE_API_KEY: {'✓' if os.getenv('ALPHA_VANTAGE_API_KEY') else '✗'}")
    print(f"  NEWS_API_KEY: {'✓' if os.getenv('NEWS_API_KEY') else '✗'}")

    try:
        # Run tests
        await test_individual_sources()
        await test_aggregator()
        await test_enhanced_agent()
        await test_fallback_behavior()

        print("\n" + "="*60)
        print("ALL TESTS COMPLETED")
        print("="*60)

    except Exception as e:
        print(f"\n✗ Test failed with error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())
