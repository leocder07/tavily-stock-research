#!/usr/bin/env python3
"""Simple test for stock analysis API"""

import requests
import time
import json

def test_analysis():
    """Test the analysis workflow"""

    # 1. Start analysis
    print("Starting NVIDIA stock analysis...")
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
    print(f"✅ Analysis started with ID: {analysis_id}")

    # 2. Check status periodically
    print("\nChecking analysis status...")
    max_attempts = 30
    for i in range(max_attempts):
        time.sleep(2)

        status_response = requests.get(
            f"http://localhost:8000/api/v1/analyze/{analysis_id}/status"
        )

        if status_response.status_code == 200:
            status = status_response.json()
            current_status = status['status']
            progress = status.get('progress', {}).get('percentage', 0)

            print(f"  Status: {current_status} - Progress: {progress}%")

            if current_status == 'completed':
                print("✅ Analysis completed!")
                break
            elif current_status == 'failed':
                print("❌ Analysis failed!")
                return False
    else:
        print("⏱️ Analysis timeout!")
        return False

    # 3. Get results
    print("\nFetching results...")
    result_response = requests.get(
        f"http://localhost:8000/api/v1/analyze/{analysis_id}/result"
    )

    if result_response.status_code == 200:
        results = result_response.json()

        print("\n" + "="*60)
        print("ANALYSIS RESULTS")
        print("="*60)

        # Check if we have actual data
        has_data = False

        if results.get('analysis', {}).get('summary'):
            print(f"\n📊 Summary:\n{results['analysis']['summary'][:500]}...")
            has_data = True

        if results.get('analysis', {}).get('market_data'):
            print(f"\n📈 Market Data: {json.dumps(results['analysis']['market_data'], indent=2)[:500]}")
            has_data = True

        if results.get('analysis', {}).get('recommendations'):
            print(f"\n💡 Recommendations: {results['analysis']['recommendations']}")
            has_data = True

        if not has_data:
            print("⚠️ Analysis completed but no data was generated")
            print(f"Full response: {json.dumps(results, indent=2)[:1000]}")

        return has_data
    else:
        print(f"❌ Failed to get results: {result_response.text}")
        return False

if __name__ == "__main__":
    print("="*60)
    print("Stock Analysis API Test")
    print("="*60)

    success = test_analysis()

    print("\n" + "="*60)
    if success:
        print("✅ TEST PASSED - Analysis workflow is functional")
    else:
        print("❌ TEST FAILED - Analysis workflow needs debugging")
    print("="*60)