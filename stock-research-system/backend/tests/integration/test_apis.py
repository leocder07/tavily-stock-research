#!/usr/bin/env python3
"""Test external APIs connectivity"""

import os
import sys
import yfinance as yf
import requests
from dotenv import load_dotenv
from tavily import TavilyClient

# Load environment variables
load_dotenv()

def test_yahoo_finance():
    """Test Yahoo Finance API"""
    print("\n📊 Testing Yahoo Finance API...")
    try:
        ticker = yf.Ticker("NVDA")
        info = ticker.info

        price = info.get('currentPrice') or info.get('regularMarketPrice', 0)
        print(f"✅ Yahoo Finance API working!")
        print(f"   NVDA current price: ${price:.2f}")
        print(f"   Market Cap: ${info.get('marketCap', 0):,.0f}")
        print(f"   P/E Ratio: {info.get('trailingPE', 'N/A')}")
        return True
    except Exception as e:
        print(f"❌ Yahoo Finance API failed: {e}")
        return False

def test_tavily_api():
    """Test Tavily API"""
    print("\n🔍 Testing Tavily API...")
    try:
        api_key = os.getenv("TAVILY_API_KEY")
        if not api_key:
            print("❌ TAVILY_API_KEY not found in environment")
            return False

        client = TavilyClient(api_key=api_key)
        response = client.search("NVDA stock price", max_results=1)

        if response and 'results' in response:
            print(f"✅ Tavily API working!")
            print(f"   Found {len(response['results'])} results")
            if response['results']:
                print(f"   First result: {response['results'][0].get('title', 'N/A')[:60]}...")
            return True
        else:
            print(f"❌ Tavily API returned no results")
            return False
    except Exception as e:
        print(f"❌ Tavily API failed: {e}")
        return False

def test_openai_api():
    """Test OpenAI API"""
    print("\n🤖 Testing OpenAI API...")
    try:
        from openai import OpenAI

        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            print("❌ OPENAI_API_KEY not found in environment")
            return False

        client = OpenAI(api_key=api_key)
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[{"role": "user", "content": "Say 'API test successful' in 3 words"}],
            max_tokens=10
        )

        print(f"✅ OpenAI API working!")
        print(f"   Response: {response.choices[0].message.content}")
        return True
    except Exception as e:
        print(f"❌ OpenAI API failed: {e}")
        return False

def test_direct_http():
    """Test direct HTTP requests"""
    print("\n🌐 Testing direct HTTP requests...")

    urls = [
        "https://query2.finance.yahoo.com/v8/finance/chart/NVDA",
        "https://api.tavily.com/",
        "https://www.google.com"
    ]

    for url in urls:
        try:
            response = requests.get(url, timeout=5)
            print(f"✅ {url[:50]}... - Status: {response.status_code}")
        except Exception as e:
            print(f"❌ {url[:50]}... - Error: {str(e)[:50]}")

    return True

if __name__ == "__main__":
    print("=" * 60)
    print("External API Connectivity Test")
    print("=" * 60)

    results = []
    results.append(("Yahoo Finance", test_yahoo_finance()))
    results.append(("Tavily", test_tavily_api()))
    results.append(("OpenAI", test_openai_api()))
    results.append(("HTTP", test_direct_http()))

    print("\n" + "=" * 60)
    print("Summary:")
    print("=" * 60)
    for name, success in results:
        status = "✅" if success else "❌"
        print(f"{status} {name}")

    all_passed = all(r[1] for r in results[:3])  # First 3 are critical
    sys.exit(0 if all_passed else 1)