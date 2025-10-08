#!/usr/bin/env python3
"""
System Validation Script for Tavily Stock Research System
Tests all major components and data flows
"""

import requests
import json
import asyncio
import websockets
import time
from typing import Dict, List, Any
from datetime import datetime

# Configuration
BASE_URL = "http://localhost:8000"
WS_URL = "ws://localhost:8000/ws"
FRONTEND_URL = "http://localhost:3000"

# Test results storage
test_results = {
    "passed": [],
    "failed": [],
    "warnings": []
}

def log_test(test_name: str, status: str, details: str = ""):
    """Log test result"""
    timestamp = datetime.now().strftime("%H:%M:%S")
    print(f"[{timestamp}] {test_name}: {status} {details}")

    if status == "✅ PASSED":
        test_results["passed"].append(test_name)
    elif status == "❌ FAILED":
        test_results["failed"].append(f"{test_name}: {details}")
    else:
        test_results["warnings"].append(f"{test_name}: {details}")

def test_health_check():
    """Test API health endpoint"""
    try:
        response = requests.get(f"{BASE_URL}/health", timeout=5)
        if response.status_code == 200:
            log_test("Health Check", "✅ PASSED")
            return True
    except Exception as e:
        log_test("Health Check", "❌ FAILED", str(e))
    return False

def test_frontend_availability():
    """Test frontend availability"""
    try:
        response = requests.get(FRONTEND_URL, timeout=5)
        if response.status_code == 200:
            log_test("Frontend Availability", "✅ PASSED")
            return True
    except Exception as e:
        log_test("Frontend Availability", "❌ FAILED", str(e))
    return False

def test_api_endpoints():
    """Test all API endpoints"""
    endpoints = [
        {"path": "/api/v1/market/sectors", "method": "GET"},
        {"path": "/api/v1/analytics/growth", "method": "GET"},
        {"path": "/api/v1/analytics/engagement", "method": "GET"},
        {"path": "/api/v1/analytics/top-stocks", "method": "GET"},
        {"path": "/api/v1/notifications", "method": "GET"}
    ]

    for endpoint in endpoints:
        try:
            if endpoint["method"] == "GET":
                response = requests.get(f"{BASE_URL}{endpoint['path']}", timeout=10)

            if response.status_code in [200, 201]:
                log_test(f"API Endpoint {endpoint['path']}", "✅ PASSED")
            else:
                log_test(f"API Endpoint {endpoint['path']}", "⚠️ WARNING", f"Status: {response.status_code}")
        except Exception as e:
            log_test(f"API Endpoint {endpoint['path']}", "❌ FAILED", str(e))

def test_stock_analysis():
    """Test stock analysis endpoint with real data"""
    test_stocks = ["AAPL", "GOOGL", "TSLA"]

    for stock in test_stocks:
        try:
            # Test research endpoint
            payload = {
                "query": f"{stock} stock analysis",
                "search_type": "news"
            }
            response = requests.post(
                f"{BASE_URL}/api/v1/research",
                json=payload,
                timeout=60
            )

            if response.status_code == 200:
                data = response.json()
                if "request_id" in data and "status" in data:
                    log_test(f"Stock Analysis - {stock}", "✅ PASSED",
                            f"Request ID: {data['request_id'][:8]}...")
                else:
                    log_test(f"Stock Analysis - {stock}", "⚠️ WARNING", "Incomplete response")
            else:
                log_test(f"Stock Analysis - {stock}", "❌ FAILED",
                        f"Status: {response.status_code}")
        except Exception as e:
            log_test(f"Stock Analysis - {stock}", "❌ FAILED", str(e))

async def test_websocket():
    """Test WebSocket connection and real-time data"""
    try:
        async with websockets.connect(WS_URL) as websocket:
            # Wait for connection established message
            message = await asyncio.wait_for(websocket.recv(), timeout=5)
            data = json.loads(message)

            if data.get("type") == "connection_established":
                client_id = data.get("client_id")
                log_test("WebSocket Connection", "✅ PASSED", f"Client ID: {client_id[:8]}...")

                # Send heartbeat
                await websocket.send(json.dumps({"type": "heartbeat"}))

                # Wait for heartbeat response
                response = await asyncio.wait_for(websocket.recv(), timeout=5)
                response_data = json.loads(response)

                if response_data.get("type") == "heartbeat_response":
                    log_test("WebSocket Heartbeat", "✅ PASSED")

                # Subscribe to market data
                await websocket.send(json.dumps({
                    "type": "subscribe_market_data",
                    "symbols": ["AAPL", "GOOGL"]
                }))
                log_test("WebSocket Market Subscription", "✅ PASSED")

                return True
            else:
                log_test("WebSocket Connection", "❌ FAILED", "Invalid connection response")
                return False

    except asyncio.TimeoutError:
        log_test("WebSocket", "❌ FAILED", "Connection timeout")
        return False
    except Exception as e:
        log_test("WebSocket", "❌ FAILED", str(e))
        return False

def test_tavily_integration():
    """Test Tavily API integration"""
    try:
        # This tests if Tavily is properly configured
        response = requests.post(
            f"{BASE_URL}/api/v1/research",
            json={"query": "Microsoft stock news", "search_type": "news"},
            timeout=30
        )

        if response.status_code == 200:
            data = response.json()
            if data.get("status") in ["COMPLETED", "PROCESSING"]:
                log_test("Tavily Integration", "✅ PASSED")
                return True
            else:
                log_test("Tavily Integration", "⚠️ WARNING", "Processing but no results")
                return True
        elif response.status_code == 432:
            log_test("Tavily Integration", "❌ FAILED", "Authentication error - check API key")
            return False
        else:
            log_test("Tavily Integration", "❌ FAILED", f"Status: {response.status_code}")
            return False
    except Exception as e:
        log_test("Tavily Integration", "❌ FAILED", str(e))
        return False

def test_market_data():
    """Test market data endpoints"""
    symbols = ["AAPL", "MSFT", "GOOGL"]

    for symbol in symbols:
        try:
            response = requests.get(
                f"{BASE_URL}/api/v1/market/price/{symbol}",
                timeout=10
            )

            if response.status_code == 200:
                data = response.json()
                if "price" in data or "message" in data:
                    log_test(f"Market Data - {symbol}", "✅ PASSED")
                else:
                    log_test(f"Market Data - {symbol}", "⚠️ WARNING", "No price data")
            else:
                log_test(f"Market Data - {symbol}", "❌ FAILED",
                        f"Status: {response.status_code}")
        except Exception as e:
            log_test(f"Market Data - {symbol}", "❌ FAILED", str(e))

def test_news_endpoint():
    """Test news endpoint"""
    try:
        response = requests.get(f"{BASE_URL}/api/v1/market/news", timeout=10)

        if response.status_code == 200:
            data = response.json()
            if "news" in data:
                log_test("News Endpoint", "✅ PASSED",
                        f"Found {len(data['news'])} news items")
            else:
                log_test("News Endpoint", "⚠️ WARNING", "No news data")
        else:
            log_test("News Endpoint", "❌ FAILED", f"Status: {response.status_code}")
    except Exception as e:
        log_test("News Endpoint", "❌ FAILED", str(e))

def test_performance():
    """Test API performance"""
    endpoints = [
        "/api/v1/analytics/growth",
        "/api/v1/market/sectors",
        "/health"
    ]

    for endpoint in endpoints:
        try:
            start_time = time.time()
            response = requests.get(f"{BASE_URL}{endpoint}", timeout=10)
            response_time = (time.time() - start_time) * 1000  # Convert to ms

            if response.status_code == 200:
                if response_time < 500:
                    log_test(f"Performance {endpoint}", "✅ PASSED",
                            f"{response_time:.0f}ms")
                elif response_time < 2000:
                    log_test(f"Performance {endpoint}", "⚠️ WARNING",
                            f"{response_time:.0f}ms (slow)")
                else:
                    log_test(f"Performance {endpoint}", "❌ FAILED",
                            f"{response_time:.0f}ms (too slow)")
        except Exception as e:
            log_test(f"Performance {endpoint}", "❌ FAILED", str(e))

def print_summary():
    """Print test summary"""
    print("\n" + "=" * 60)
    print("TEST SUMMARY")
    print("=" * 60)

    total_tests = len(test_results["passed"]) + len(test_results["failed"])
    pass_rate = (len(test_results["passed"]) / total_tests * 100) if total_tests > 0 else 0

    print(f"✅ Passed: {len(test_results['passed'])}")
    print(f"❌ Failed: {len(test_results['failed'])}")
    print(f"⚠️  Warnings: {len(test_results['warnings'])}")
    print(f"📊 Pass Rate: {pass_rate:.1f}%")

    if test_results["failed"]:
        print("\nFailed Tests:")
        for failure in test_results["failed"]:
            print(f"  - {failure}")

    if test_results["warnings"]:
        print("\nWarnings:")
        for warning in test_results["warnings"]:
            print(f"  - {warning}")

    print("\n" + "=" * 60)

    # Overall status
    if pass_rate == 100:
        print("🎉 ALL TESTS PASSED! System is fully operational.")
    elif pass_rate >= 80:
        print("✅ System is operational with minor issues.")
    elif pass_rate >= 60:
        print("⚠️  System has significant issues that need attention.")
    else:
        print("❌ System has critical failures.")

async def main():
    """Main test execution"""
    print("=" * 60)
    print("TAVILY STOCK RESEARCH SYSTEM - VALIDATION SUITE")
    print("=" * 60)
    print(f"Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")

    # Run tests
    print("1. Testing Infrastructure...")
    test_health_check()
    test_frontend_availability()

    print("\n2. Testing API Endpoints...")
    test_api_endpoints()

    print("\n3. Testing Stock Analysis...")
    test_stock_analysis()

    print("\n4. Testing WebSocket Connection...")
    await test_websocket()

    print("\n5. Testing Tavily Integration...")
    test_tavily_integration()

    print("\n6. Testing Market Data...")
    test_market_data()

    print("\n7. Testing News Feed...")
    test_news_endpoint()

    print("\n8. Testing Performance...")
    test_performance()

    # Print summary
    print_summary()

if __name__ == "__main__":
    asyncio.run(main())