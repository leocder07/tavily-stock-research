#!/usr/bin/env python3
"""Demo test showing the analysis system works with mock data"""

import requests
import json
import time

def test_analysis_demo():
    """Test the analysis workflow with demo data"""

    # 1. Start analysis
    print("\n" + "="*60)
    print("STOCK ANALYSIS SYSTEM DEMO")
    print("="*60)
    print("\n📊 Starting NVIDIA (NVDA) comprehensive stock analysis...")

    response = requests.post(
        "http://localhost:8000/api/v1/analyze",
        json={
            "query": "Perform comprehensive analysis of NVIDIA stock",
            "symbols": ["NVDA"],
            "priority": "high"
        }
    )

    if response.status_code != 200:
        print(f"❌ Failed to start analysis: {response.text}")
        return False

    result = response.json()
    analysis_id = result['analysis_id']
    print(f"✅ Analysis initiated with ID: {analysis_id}")

    # 2. Monitor progress
    print("\n⏳ Processing analysis...")
    max_attempts = 20
    for i in range(max_attempts):
        time.sleep(1)

        status_response = requests.get(
            f"http://localhost:8000/api/v1/analyze/{analysis_id}/status"
        )

        if status_response.status_code == 200:
            status = status_response.json()
            current_status = status['status']

            if current_status == 'completed':
                print("✅ Analysis completed!")
                break
            elif current_status == 'failed':
                print("❌ Analysis failed!")
                return False
            else:
                print(f"   Status: {current_status} - Processing divisions...")
    else:
        print("⏱️ Analysis timeout!")
        return False

    # 3. Get results
    print("\n📈 Fetching analysis results...")
    result_response = requests.get(
        f"http://localhost:8000/api/v1/analyze/{analysis_id}/result"
    )

    if result_response.status_code == 200:
        results = result_response.json()

        print("\n" + "="*60)
        print("ANALYSIS RESULTS")
        print("="*60)

        # Display key metrics from mock data
        if results.get('analysis', {}).get('summary'):
            print(f"\n📊 Executive Summary:")
            print(f"   {results['analysis']['summary'][:200]}...")

        # Show division results
        if results.get('analysis', {}).get('technical'):
            print(f"\n📈 Technical Analysis:")
            tech = results['analysis']['technical']
            if isinstance(tech, dict) and 'NVDA' in tech:
                nvda_tech = tech['NVDA']
                print(f"   • Current Price: ${nvda_tech.get('current_price', 0):.2f}")
                print(f"   • Change: {nvda_tech.get('change_percent', 0):.2f}%")
                print(f"   • Trend: {nvda_tech.get('trend', 'N/A')}")
                print(f"   • RSI: {nvda_tech.get('rsi', 0)}")

        if results.get('analysis', {}).get('fundamental'):
            print(f"\n💰 Fundamental Analysis:")
            fund = results['analysis']['fundamental']
            if isinstance(fund, dict) and 'NVDA' in fund:
                nvda_fund = fund['NVDA']
                print(f"   • Market Cap: ${nvda_fund.get('market_cap', 0):,.0f}")
                print(f"   • Recommendation: {nvda_fund.get('recommendation', 'N/A')}")

        if results.get('analysis', {}).get('recommendations'):
            print(f"\n💡 Recommendations:")
            for rec in results['analysis']['recommendations'][:3]:
                print(f"   • {rec}")

        # Show confidence scores
        if results.get('confidence_scores'):
            print(f"\n🎯 Confidence Scores:")
            scores = results['confidence_scores']
            print(f"   • Research: {scores.get('research', 0)*100:.0f}%")
            print(f"   • Analysis: {scores.get('analysis', 0)*100:.0f}%")
            print(f"   • Strategy: {scores.get('strategy', 0)*100:.0f}%")

        print("\n" + "="*60)
        print("✅ DEMO COMPLETED - System is operational!")
        print("="*60)

        # Note about mock data
        print("\n⚠️ Note: Using simulated data due to network limitations")
        print("   In production, this would fetch real-time data from:")
        print("   • Yahoo Finance API")
        print("   • Tavily Search API")
        print("   • OpenAI GPT-4 for analysis")

        return True
    else:
        print(f"❌ Failed to get results: {result_response.text}")
        return False

if __name__ == "__main__":
    success = test_analysis_demo()
    exit(0 if success else 1)