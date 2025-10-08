#!/usr/bin/env python3
"""Test deep analysis functionality with a real stock"""

import asyncio
import json
from datetime import datetime
from agents.workflow_adapter import StockResearchWorkflow
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

async def test_deep_analysis():
    """Test deep analysis with NVDA"""

    # Initialize workflow
    workflow = StockResearchWorkflow(
        tavily_api_key=os.getenv("TAVILY_API_KEY"),
        openai_api_key=os.getenv("OPENAI_API_KEY"),
        mongodb_url=os.getenv("MONGODB_URL")
    )

    # Test query
    query = "Perform deep analysis on NVDA and provide buy/sell recommendation"
    request_id = f"test_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

    print(f"Testing deep analysis for: {query}")
    print(f"Request ID: {request_id}")
    print("-" * 80)

    try:
        # Run the analysis
        result = await workflow.run(query, request_id, user_id="test_user")

        # Display results
        print("\n=== ANALYSIS RESULTS ===\n")
        print(f"Status: {result.get('status')}")
        print(f"Symbol: {result.get('symbol')}")
        print(f"Symbols analyzed: {result.get('symbols')}")

        if result.get('analysis'):
            analysis = result['analysis']

            print("\n--- Summary ---")
            print(analysis.get('summary', 'No summary'))

            print("\n--- Market Data ---")
            market_data = analysis.get('market_data', {})
            if market_data:
                print(json.dumps(market_data, indent=2)[:500])  # First 500 chars

            print("\n--- Technical Analysis ---")
            technical = analysis.get('technical', {})
            if technical:
                for symbol, data in list(technical.items())[:2]:  # First 2 symbols
                    print(f"{symbol}: {json.dumps(data, indent=2)[:300]}")

            print("\n--- Fundamental Analysis ---")
            fundamental = analysis.get('fundamental', {})
            if fundamental:
                for symbol, data in list(fundamental.items())[:2]:
                    print(f"{symbol}: {json.dumps(data, indent=2)[:300]}")

            print("\n--- Recommendations ---")
            recommendations = analysis.get('recommendations', [])
            for rec in recommendations[:5]:  # First 5 recommendations
                print(f"• {rec}")

            print("\n--- Key Insights ---")
            insights = analysis.get('key_insights', [])
            for insight in insights[:5]:  # First 5 insights
                print(f"• {insight}")

        print("\n--- Confidence Scores ---")
        confidence = result.get('confidence_scores', {})
        for key, value in confidence.items():
            print(f"{key}: {value:.2f}" if isinstance(value, (int, float)) else f"{key}: {value}")

        return result

    except Exception as e:
        print(f"Error during analysis: {e}")
        import traceback
        traceback.print_exc()
        return None

if __name__ == "__main__":
    # Run the test
    result = asyncio.run(test_deep_analysis())

    if result:
        print("\n✅ Deep analysis test completed successfully!")

        # Validate data accuracy
        print("\n=== DATA VALIDATION ===")

        # Check if we got real market data
        analysis = result.get('analysis', {})
        market_data = analysis.get('market_data', {})

        if market_data:
            print("✓ Market data retrieved")
        else:
            print("✗ No market data")

        # Check technical analysis
        technical = analysis.get('technical', {})
        if technical and any(technical.values()):
            print("✓ Technical analysis performed")
        else:
            print("✗ No technical analysis")

        # Check fundamental analysis
        fundamental = analysis.get('fundamental', {})
        if fundamental and any(fundamental.values()):
            print("✓ Fundamental analysis performed")
        else:
            print("✗ No fundamental analysis")

        # Check recommendations
        recommendations = analysis.get('recommendations', [])
        if recommendations:
            print(f"✓ {len(recommendations)} recommendations generated")
        else:
            print("✗ No recommendations")

    else:
        print("\n❌ Deep analysis test failed!")