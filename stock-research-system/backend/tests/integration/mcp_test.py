#!/usr/bin/env python3
"""MCP-based testing for Stock Research System"""

import json
import time
import requests

def test_health_endpoint():
    """Test the health endpoint"""
    print("🔍 Testing Health Endpoint...")
    try:
        response = requests.get("http://localhost:8000/health")
        data = response.json()

        if response.status_code == 200 and data['status'] == 'healthy':
            print("✅ Health check passed")
            print(f"   Database: {data.get('database', 'unknown')}")
            return True
        else:
            print(f"❌ Health check failed: {data}")
            return False
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

def test_chat_api(query):
    """Test the chat API endpoint"""
    print(f"\n🔍 Testing: {query}")
    try:
        start_time = time.time()
        response = requests.post(
            "http://localhost:8000/api/v1/chat",
            json={"message": query},
            headers={"Content-Type": "application/json"},
            timeout=30
        )
        elapsed_time = time.time() - start_time

        if response.status_code == 200:
            data = response.json()
            print(f"✅ Response received in {elapsed_time:.2f}s")

            # Check response quality
            response_text = data.get('response', '')
            print(f"   Response length: {len(response_text)} chars")

            # Save response for analysis
            filename = f"/tmp/test_response_{query.replace(' ', '_')[:20]}.json"
            with open(filename, 'w') as f:
                json.dump({
                    'query': query,
                    'response': response_text,
                    'request_id': data.get('request_id'),
                    'time': elapsed_time,
                    'timestamp': time.strftime('%Y-%m-%d %H:%M:%S')
                }, f, indent=2)
            print(f"   Saved to: {filename}")

            # Analyze response content
            if '$' in response_text or 'price' in response_text.lower():
                print("   ✅ Contains price data")
            if any(term in response_text.lower() for term in ['revenue', 'earnings', 'profit']):
                print("   ✅ Contains fundamental data")
            if any(term in response_text.lower() for term in ['support', 'resistance', 'trend']):
                print("   ✅ Contains technical analysis")

            return True
        else:
            print(f"❌ API returned status {response.status_code}")
            return False

    except requests.Timeout:
        print("❌ Request timed out (>30s)")
        return False
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

def main():
    """Run all tests"""
    print("🚀 Stock Research System Test Suite")
    print("=" * 50)

    # Test health
    if not test_health_endpoint():
        print("\n⚠️ Backend not healthy, stopping tests")
        return

    # Test queries
    test_queries = [
        "What is the current price of AAPL?",
        "Analyze Tesla stock fundamentals",
        "Technical analysis for NVDA",
        "Compare Microsoft and Google stocks",
        "What are the risks of investing in META?"
    ]

    results = []
    for query in test_queries:
        success = test_chat_api(query)
        results.append({'query': query, 'success': success})
        time.sleep(2)  # Wait between requests

    # Summary
    print("\n" + "=" * 50)
    print("📊 TEST SUMMARY")
    print("=" * 50)

    successful = sum(1 for r in results if r['success'])
    print(f"✅ Passed: {successful}/{len(results)}")
    print(f"❌ Failed: {len(results) - successful}/{len(results)}")

    # Save summary
    with open('/tmp/test_summary.json', 'w') as f:
        json.dump({
            'timestamp': time.strftime('%Y-%m-%d %H:%M:%S'),
            'total_tests': len(results),
            'passed': successful,
            'failed': len(results) - successful,
            'results': results
        }, f, indent=2)

    print(f"\n📄 Full results saved to: /tmp/test_summary.json")
    print("✅ Testing complete!")

if __name__ == "__main__":
    main()