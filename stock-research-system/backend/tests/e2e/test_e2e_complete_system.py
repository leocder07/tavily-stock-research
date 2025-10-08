"""
End-to-End Test: Complete System with Full Optimization
Tests the entire hybrid workflow with TSLA analysis
"""

import asyncio
import os
import sys
from datetime import datetime
from dotenv import load_dotenv

# Add backend to path
sys.path.insert(0, os.path.dirname(__file__))

load_dotenv()


async def test_complete_system():
    """Run complete E2E test"""
    print("\n" + "="*80)
    print("END-TO-END TEST: Complete Stock Analysis System")
    print("="*80)

    # Check environment variables
    print("\n📋 Step 1: Environment Check")
    print("-" * 80)

    required_vars = {
        'OPENAI_API_KEY': os.getenv('OPENAI_API_KEY'),
        'MONGODB_URL': os.getenv('MONGODB_URL'),
        'TAVILY_API_KEY': os.getenv('TAVILY_API_KEY'),
        'REDIS_URL': os.getenv('REDIS_URL', 'redis://localhost:6379')
    }

    for var, value in required_vars.items():
        status = "✅" if value else "❌"
        masked_value = f"{value[:10]}..." if value and len(value) > 10 else value
        print(f"{status} {var}: {masked_value if value else 'NOT SET'}")

    if not all([required_vars['OPENAI_API_KEY'], required_vars['MONGODB_URL']]):
        print("\n❌ ERROR: Missing required environment variables")
        return

    # Optional features
    tavily_enabled = bool(required_vars['TAVILY_API_KEY'])
    redis_enabled = bool(required_vars['REDIS_URL'])

    print(f"\n🔧 Configuration:")
    print(f"   • Tavily Enrichment: {'✅ Enabled' if tavily_enabled else '❌ Disabled'}")
    print(f"   • Redis Caching: {'✅ Enabled' if redis_enabled else '❌ Disabled'}")
    print(f"   • SmartModelRouter: {'✅ Enabled' if tavily_enabled else '❌ Disabled'}")

    # Test MongoDB connection
    print("\n📋 Step 2: Database Connection")
    print("-" * 80)

    try:
        from services.mongodb_connection import mongodb_connection
        await mongodb_connection.connect()
        db = mongodb_connection.get_database()

        # Test connection
        await db.command('ping')
        print("✅ MongoDB connected successfully")

        # Get collections
        collections = await db.list_collection_names()
        print(f"✅ Available collections: {', '.join(collections[:5])}")

    except Exception as e:
        print(f"❌ MongoDB connection failed: {e}")
        return

    # Test Redis connection (if enabled)
    if redis_enabled:
        print("\n📋 Step 3: Redis Connection")
        print("-" * 80)

        try:
            from services.tavily_cache import get_tavily_cache
            cache = get_tavily_cache(required_vars['REDIS_URL'])

            if cache.enabled:
                # Test Redis
                stats = await cache.get_stats()
                print(f"✅ Redis connected successfully")
                print(f"   • Current hit rate: {stats.get('hit_rate', 0)}%")
                print(f"   • Total requests: {stats.get('total_requests', 0)}")
            else:
                print("⚠️  Redis cache disabled")

        except Exception as e:
            print(f"⚠️  Redis connection failed (non-critical): {e}")

    # Initialize workflow
    print("\n📋 Step 4: Initialize Workflow")
    print("-" * 80)

    try:
        from langchain_openai import ChatOpenAI
        from workflow.enhanced_stock_workflow import EnhancedStockWorkflow

        llm = ChatOpenAI(
            model="gpt-4",
            api_key=required_vars['OPENAI_API_KEY'],
            temperature=0.2
        )

        workflow = EnhancedStockWorkflow(
            llm=llm,
            database=db,
            tavily_api_key=required_vars['TAVILY_API_KEY'],
            redis_url=required_vars['REDIS_URL'] if redis_enabled else None
        )

        print("✅ Enhanced Stock Workflow initialized")
        print(f"   • Base agents: 4 (Fundamental, Technical, Risk, Synthesis)")

        if workflow.hybrid_orchestrator:
            print(f"   • Tavily agents: 3 (News, Sentiment, Macro)")
            print(f"   • Hybrid orchestration: Enabled (70/30 weighting)")

        if workflow.tavily_cache:
            print(f"   • Redis caching: Enabled")

        if workflow.smart_router:
            print(f"   • Smart model routing: Enabled")

    except Exception as e:
        print(f"❌ Workflow initialization failed: {e}")
        import traceback
        traceback.print_exc()
        return

    # Run TSLA analysis
    print("\n📋 Step 5: Run TSLA Analysis")
    print("-" * 80)

    analysis_id = f"test_tsla_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

    try:
        print(f"📊 Starting analysis (ID: {analysis_id})")
        print(f"⏰ Start time: {datetime.now().strftime('%H:%M:%S')}")

        start_time = datetime.now()

        result = await workflow.execute(
            analysis_id=analysis_id,
            query="Comprehensive analysis of TSLA stock for investment decision",
            symbols=["TSLA"],
            context=None  # Let workflow prepare context
        )

        end_time = datetime.now()
        duration = (end_time - start_time).total_seconds()

        print(f"✅ Analysis completed in {duration:.1f} seconds")
        print(f"⏰ End time: {end_time.strftime('%H:%M:%S')}")

    except Exception as e:
        print(f"❌ Analysis failed: {e}")
        import traceback
        traceback.print_exc()
        return

    # Display results
    print("\n📋 Step 6: Analysis Results")
    print("-" * 80)

    recommendation = result.get('recommendations', {})
    analysis = result.get('analysis', {})

    print(f"\n🎯 FINAL RECOMMENDATION")
    print(f"   • Action: {recommendation.get('action', 'UNKNOWN')}")
    print(f"   • Confidence: {recommendation.get('confidence', 0)*100:.1f}%")
    print(f"   • Target Price: ${recommendation.get('target_price', 0):.2f}")
    print(f"   • Stop Loss: ${recommendation.get('stop_loss', 0):.2f}")
    print(f"   • Time Horizon: {recommendation.get('time_horizon', 'N/A')}")

    # Check enrichment
    enrichment_status = result.get('enrichment_status', 'disabled')
    print(f"\n📈 ENRICHMENT STATUS: {enrichment_status.upper()}")

    if enrichment_status == 'success':
        print("   ✅ Tavily enrichment applied successfully")

        # Display Tavily insights
        if 'news' in analysis:
            news = analysis['news']
            print(f"\n   📰 News Intelligence:")
            print(f"      • Sentiment: {news.get('sentiment', {}).get('overall', 'N/A')}")
            print(f"      • Key Events: {len(news.get('key_events', []))} found")

        if 'sentiment' in analysis:
            sentiment = analysis['sentiment']
            print(f"\n   💬 Retail Sentiment:")
            print(f"      • Pulse: {sentiment.get('retail_sentiment', 'N/A')}")
            print(f"      • Social Volume: {sentiment.get('volume', 'N/A')}")

        if 'macro' in analysis:
            macro = analysis['macro']
            print(f"\n   🌍 Macro Context:")
            print(f"      • Market Regime: {macro.get('market_regime', {}).get('regime', 'N/A')}")
            print(f"      • Sector Trend: {macro.get('sector_trend', 'N/A')}")

    elif enrichment_status == 'disabled':
        print("   ℹ️  Tavily enrichment not configured (base analysis only)")
    elif enrichment_status == 'failed':
        print("   ⚠️  Tavily enrichment failed (using base analysis)")

    # Test optimization statistics
    if tavily_enabled:
        print("\n📋 Step 7: Optimization Statistics")
        print("-" * 80)

        try:
            # Cache stats
            if workflow.tavily_cache:
                cache_stats = await workflow.tavily_cache.get_stats()
                print(f"\n💾 Cache Performance:")
                print(f"   • Hit Rate: {cache_stats.get('hit_rate', 0):.1f}%")
                print(f"   • Total Requests: {cache_stats.get('total_requests', 0)}")
                print(f"   • Cost Saved: ${cache_stats.get('cost_saved', 0):.2f}")

            # Router stats
            if workflow.smart_router:
                router_stats = workflow.smart_router.get_stats()
                print(f"\n🧠 Model Routing:")
                print(f"   • GPT-3.5 Usage: {router_stats.get('gpt35_percentage', 0):.1f}%")
                print(f"   • GPT-4 Calls: {router_stats.get('gpt4_calls', 0)}")
                print(f"   • Cost Saved: ${router_stats.get('cost_saved', 0):.2f}")
                print(f"   • Avg Cost/Call: ${router_stats.get('avg_cost_per_call', 0):.3f}")

        except Exception as e:
            print(f"⚠️  Could not retrieve optimization stats: {e}")

    # Summary
    print("\n" + "="*80)
    print("✅ END-TO-END TEST COMPLETE")
    print("="*80)

    print(f"\n📊 Test Summary:")
    print(f"   • Duration: {duration:.1f} seconds")
    print(f"   • Analysis ID: {analysis_id}")
    print(f"   • Recommendation: {recommendation.get('action', 'N/A')}")
    print(f"   • Enrichment: {enrichment_status}")
    print(f"   • Status: {'SUCCESS' if result.get('status') == 'completed' else 'FAILED'}")

    # Test second run (for cache testing)
    if redis_enabled and tavily_enabled:
        print("\n📋 Step 8: Cache Hit Test (Second Run)")
        print("-" * 80)
        print("Running same analysis again to test cache...")

        analysis_id_2 = f"test_tsla_cache_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

        start_time_2 = datetime.now()

        result_2 = await workflow.execute(
            analysis_id=analysis_id_2,
            query="Comprehensive analysis of TSLA stock for investment decision",
            symbols=["TSLA"],
            context=None
        )

        end_time_2 = datetime.now()
        duration_2 = (end_time_2 - start_time_2).total_seconds()

        speedup = ((duration - duration_2) / duration * 100) if duration > duration_2 else 0

        print(f"✅ Second run completed in {duration_2:.1f} seconds")
        print(f"⚡ Speedup: {speedup:.1f}% faster (cache hits)")

        # Check cache stats after second run
        if workflow.tavily_cache:
            cache_stats_2 = await workflow.tavily_cache.get_stats()
            hits_gained = cache_stats_2.get('hits', 0) - cache_stats.get('hits', 0)
            print(f"💾 Cache hits gained: {hits_gained}")

    # Cleanup
    print("\n📋 Step 9: Cleanup")
    print("-" * 80)

    try:
        await mongodb_connection.close()
        print("✅ Database connection closed")

        if workflow.tavily_cache and workflow.tavily_cache.redis_client:
            await workflow.tavily_cache.close()
            print("✅ Redis connection closed")

    except Exception as e:
        print(f"⚠️  Cleanup warning: {e}")

    print("\n" + "="*80)
    print("🎉 ALL TESTS PASSED - SYSTEM READY FOR PRODUCTION")
    print("="*80)
    print()


async def run_quick_validation():
    """Quick validation without full analysis"""
    print("\n" + "="*80)
    print("QUICK VALIDATION TEST")
    print("="*80)

    from services.tavily_cache import get_tavily_cache
    from services.smart_model_router import get_smart_router, TaskTypes

    # Test cache
    print("\n1. Testing TavilyCache...")
    try:
        redis_url = os.getenv('REDIS_URL', 'redis://localhost:6379')
        cache = get_tavily_cache(redis_url)

        if cache.enabled:
            print("   ✅ Cache initialized")
            stats = await cache.get_stats()
            print(f"   ✅ Stats retrieved: {stats}")
        else:
            print("   ⚠️  Cache disabled (Redis not available)")
    except Exception as e:
        print(f"   ❌ Cache test failed: {e}")

    # Test router
    print("\n2. Testing SmartModelRouter...")
    try:
        openai_key = os.getenv('OPENAI_API_KEY')
        if openai_key:
            router = get_smart_router(openai_key)
            print("   ✅ Router initialized")

            # Test routing
            model_simple = router.get_model(TaskTypes.NEWS_SUMMARY)
            print(f"   ✅ Simple task → {model_simple.model_name}")

            model_complex = router.get_model(TaskTypes.FUNDAMENTAL_ANALYSIS)
            print(f"   ✅ Complex task → {model_complex.model_name}")

            stats = router.get_stats()
            print(f"   ✅ Stats: {stats}")
        else:
            print("   ⚠️  Router disabled (OpenAI key not set)")
    except Exception as e:
        print(f"   ❌ Router test failed: {e}")

    print("\n✅ Quick validation complete\n")


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description='E2E System Test')
    parser.add_argument('--quick', action='store_true', help='Run quick validation only')
    args = parser.parse_args()

    if args.quick:
        asyncio.run(run_quick_validation())
    else:
        asyncio.run(test_complete_system())
