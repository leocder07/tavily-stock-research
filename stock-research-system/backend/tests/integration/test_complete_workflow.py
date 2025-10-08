#!/usr/bin/env python3
"""Test complete orchestration workflow"""

import asyncio
import os
from dotenv import load_dotenv
from agents.workflow_adapter import StockResearchWorkflow

load_dotenv()

async def test_complete_workflow():
    """Test the complete stock research workflow"""
    print("=" * 50)
    print("Testing Complete Orchestration Workflow")
    print("=" * 50)

    # Initialize workflow
    workflow = StockResearchWorkflow(
        tavily_api_key=os.getenv("TAVILY_API_KEY"),
        openai_api_key=os.getenv("OPENAI_API_KEY")
    )

    # Test query
    query = "Analyze NVDA stock - provide comprehensive analysis with price data and recommendations"
    request_id = "test-complete-001"

    print(f"\nQuery: {query}")
    print(f"Request ID: {request_id}")
    print("\nExecuting full orchestration...")
    print("-" * 50)

    try:
        result = await workflow.run(
            query=query,
            request_id=request_id,
            user_id="test_user"
        )

        print("\n✅ WORKFLOW COMPLETED SUCCESSFULLY!")
        print("=" * 50)

        # Display results
        if result.get("status") == "completed":
            analysis = result.get("analysis", {})

            # Show symbols analyzed
            symbols = result.get("symbols", [])
            print(f"\nSymbols Analyzed: {', '.join(symbols)}")

            # Show market data
            market_data = analysis.get("market_data", {})
            if market_data:
                print("\n📊 Market Data:")
                for symbol, data in market_data.items():
                    if isinstance(data, dict):
                        print(f"  {symbol}:")
                        print(f"    Price: ${data.get('price', 0):.2f}")
                        print(f"    Change: {data.get('changePercent', 0):.2f}%")
                        print(f"    Volume: {data.get('volume', 0):,}")

            # Show technical analysis
            technical = analysis.get("technical", {})
            if technical:
                print("\n📈 Technical Analysis:")
                for symbol, data in technical.items():
                    if isinstance(data, dict):
                        print(f"  {symbol}:")
                        print(f"    Trend: {data.get('trend', 'unknown')}")
                        print(f"    RSI: {data.get('rsi', 0)}")

            # Show recommendations
            recommendations = analysis.get("recommendations", [])
            if recommendations:
                print("\n💡 Recommendations:")
                for rec in recommendations[:3]:
                    print(f"  • {rec}")

            # Show key insights
            insights = analysis.get("key_insights", [])
            if insights:
                print("\n🔍 Key Insights:")
                for insight in insights[:3]:
                    print(f"  • {insight}")

            # Show confidence scores
            confidence = result.get("confidence_scores", {})
            print("\n📊 Confidence Scores:")
            print(f"  Research: {confidence.get('research', 0):.2f}")
            print(f"  Analysis: {confidence.get('analysis', 0):.2f}")
            print(f"  Strategy: {confidence.get('strategy', 0):.2f}")

            # Show summary
            summary = analysis.get("summary", "")
            if summary:
                print(f"\n📝 Summary:")
                print(f"  {summary}")

        else:
            print("❌ Workflow did not complete successfully")
            print(f"Status: {result.get('status', 'unknown')}")

    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        import traceback
        traceback.print_exc()

    print("\n" + "=" * 50)
    print("Test Complete")
    print("=" * 50)

if __name__ == "__main__":
    asyncio.run(test_complete_workflow())