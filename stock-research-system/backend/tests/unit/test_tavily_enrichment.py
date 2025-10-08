"""
Test Tavily Enrichment Integration
Quick test to verify Tavily agents work correctly
"""

import asyncio
import os
import sys
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI

# Add backend to path
sys.path.insert(0, os.path.dirname(__file__))

from agents.tavily_agents import (
    TavilyNewsIntelligenceAgent,
    TavilySentimentTrackerAgent,
    MacroContextAgent
)

load_dotenv()

TAVILY_API_KEY = os.getenv("TAVILY_API_KEY")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")


async def test_news_agent():
    """Test News Intelligence Agent"""
    print("\n" + "="*60)
    print("TESTING: Tavily News Intelligence Agent")
    print("="*60)

    llm = ChatOpenAI(model="gpt-3.5-turbo", api_key=OPENAI_API_KEY, temperature=0.1)
    agent = TavilyNewsIntelligenceAgent(TAVILY_API_KEY, llm)

    context = {
        'symbol': 'TSLA',
        'market_data': {'price': 250.00},
        'base_recommendation': 'HOLD'
    }

    result = await agent.analyze(context)

    print(f"\n✓ Agent: {result['agent']}")
    print(f"✓ Symbol: {result['symbol']}")
    print(f"✓ Sentiment: {result['sentiment']['overall']} (score: {result['sentiment']['score']})")
    print(f"✓ Articles Found: {result['news_data']['total_articles']}")
    print(f"✓ Key Events: {result['key_events'][:2] if result['key_events'] else 'None'}")
    print(f"✓ Enrichment Score: {result['enrichment_score']}")

    return result


async def test_sentiment_agent():
    """Test Sentiment Tracker Agent"""
    print("\n" + "="*60)
    print("TESTING: Tavily Sentiment Tracker Agent")
    print("="*60)

    llm = ChatOpenAI(model="gpt-3.5-turbo", api_key=OPENAI_API_KEY, temperature=0.2)
    agent = TavilySentimentTrackerAgent(TAVILY_API_KEY, llm)

    context = {
        'symbol': 'TSLA',
        'market_data': {'price': 250.00},
        'news_sentiment': {'score': 0.3}  # Slightly bullish news
    }

    result = await agent.analyze(context)

    print(f"\n✓ Agent: {result['agent']}")
    print(f"✓ Retail Sentiment: {result['sentiment_pulse']['retail_sentiment']} "
          f"(score: {result['sentiment_pulse']['score']})")
    print(f"✓ Social Volume: {result['sentiment_pulse']['volume']}")
    print(f"✓ Trending: {result['sentiment_pulse']['trending']}")
    print(f"✓ Platforms: {result['social_data']['platforms'][:3] if result['social_data']['platforms'] else 'None'}")
    print(f"✓ Divergence Score: {result['divergence_score']}")

    return result


async def test_macro_agent():
    """Test Macro Context Agent"""
    print("\n" + "="*60)
    print("TESTING: Macro Context Agent")
    print("="*60)

    llm = ChatOpenAI(model="gpt-3.5-turbo", api_key=OPENAI_API_KEY, temperature=0.2)
    agent = MacroContextAgent(TAVILY_API_KEY, llm)

    context = {
        'symbol': 'TSLA',
        'sector': 'Technology',
        'market_data': {'price': 250.00},
        'base_recommendation': 'HOLD'
    }

    result = await agent.analyze(context)

    print(f"\n✓ Agent: {result['agent']}")
    print(f"✓ Market Regime: {result['market_regime']['regime']} "
          f"(score: {result['market_regime']['score']})")
    print(f"✓ Sector Trend: {result['sector_analysis']['trend']}")
    print(f"✓ Fed Policy: {result['market_regime']['fed_policy']}")
    print(f"✓ Economic Indicators: {result['economic_indicators'][:2] if result['economic_indicators'] else 'None'}")
    print(f"✓ Context Score: {result['context_score']}")

    return result


async def test_hybrid_orchestrator():
    """Test Hybrid Orchestrator (weighted consensus)"""
    print("\n" + "="*60)
    print("TESTING: Hybrid Orchestrator (Weighted Consensus)")
    print("="*60)

    from workflow.hybrid_orchestrator import HybridOrchestrator

    llm = ChatOpenAI(model="gpt-4", api_key=OPENAI_API_KEY, temperature=0.2)

    # Mock database
    class MockDB:
        def get_database(self):
            return self

        async def update_one(self, *args, **kwargs):
            pass

    orchestrator = HybridOrchestrator(TAVILY_API_KEY, llm, MockDB())

    # Base analysis result (from expert agents)
    base_result = {
        'recommendation': 'HOLD',
        'confidence': 0.7,
        'sector': 'Technology',
        'market_data': {'price': 250.00},
        'reasoning': 'Fair valuation with moderate growth prospects'
    }

    enriched = await orchestrator.enrich_analysis(
        analysis_id='test-123',
        symbol='TSLA',
        base_result=base_result
    )

    print(f"\n✓ Base Recommendation: {base_result['recommendation']} ({base_result['confidence']:.2f})")
    print(f"✓ Final Recommendation: {enriched['recommendation']} ({enriched['confidence']:.2f})")
    print(f"✓ Enrichment Status: {enriched['enrichment_status']}")
    print(f"✓ Base Weight: {enriched['consensus_breakdown']['base_weight']}")
    print(f"✓ Tavily Weight: {enriched['consensus_breakdown']['tavily_weight']}")
    print(f"✓ Tavily Adjustment: {enriched['consensus_breakdown']['tavily_adjustment']}")

    return enriched


async def main():
    """Run all tests"""
    print("\n" + "="*60)
    print("TAVILY ENRICHMENT INTEGRATION TEST")
    print("="*60)

    if not TAVILY_API_KEY:
        print("\n❌ ERROR: TAVILY_API_KEY not set in .env")
        return

    if not OPENAI_API_KEY:
        print("\n❌ ERROR: OPENAI_API_KEY not set in .env")
        return

    print("\n✓ API Keys loaded successfully")

    try:
        # Test each agent
        await test_news_agent()
        await test_sentiment_agent()
        await test_macro_agent()

        # Test orchestrator
        await test_hybrid_orchestrator()

        print("\n" + "="*60)
        print("✅ ALL TESTS PASSED")
        print("="*60)
        print("\nTavily enrichment is working correctly!")
        print("The system can now:")
        print("  • Fetch real-time breaking news")
        print("  • Track retail sentiment from social media")
        print("  • Analyze macro market conditions")
        print("  • Combine insights with weighted consensus")
        print("\nNext steps:")
        print("  1. Run backend: uvicorn main:app --reload")
        print("  2. Test TSLA analysis with enrichment")
        print("  3. Compare base vs enriched recommendations")

    except Exception as e:
        print(f"\n❌ TEST FAILED: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())
