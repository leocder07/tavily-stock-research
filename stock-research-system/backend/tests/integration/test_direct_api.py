#!/usr/bin/env python3
"""Direct API test - bypass orchestration and fetch real data"""

import asyncio
import yfinance as yf
from tavily import TavilyClient
from openai import OpenAI
import os
from dotenv import load_dotenv

load_dotenv()

async def test_direct_apis():
    """Test APIs directly without agent orchestration"""
    print("\n" + "="*60)
    print("DIRECT API TEST - Real Data Fetching")
    print("="*60)

    # Test Yahoo Finance
    print("\n📊 Fetching NVIDIA (NVDA) data from Yahoo Finance...")
    ticker = yf.Ticker("NVDA")
    info = ticker.info

    price = info.get('currentPrice') or info.get('regularMarketPrice', 0)
    market_cap = info.get('marketCap', 0)
    pe_ratio = info.get('trailingPE', 0)
    volume = info.get('volume', 0)

    print(f"✅ NVDA Stock Data:")
    print(f"   • Current Price: ${price:.2f}")
    print(f"   • Market Cap: ${market_cap:,.0f}")
    print(f"   • P/E Ratio: {pe_ratio:.2f}")
    print(f"   • Volume: {volume:,}")

    # Test Tavily
    print("\n🔍 Searching for NVIDIA news with Tavily...")
    tavily_client = TavilyClient(api_key=os.getenv("TAVILY_API_KEY"))
    search_results = tavily_client.search(
        "NVIDIA stock AI chip news latest",
        max_results=3
    )

    print(f"✅ Found {len(search_results['results'])} news items:")
    for i, result in enumerate(search_results['results'][:3], 1):
        print(f"   {i}. {result['title'][:80]}...")

    # Test OpenAI
    print("\n🤖 Generating analysis with OpenAI...")
    openai_client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

    prompt = f"""Analyze NVIDIA stock:
    - Price: ${price:.2f}
    - Market Cap: ${market_cap:,.0f}
    - P/E Ratio: {pe_ratio:.2f}

    Provide a 2-sentence investment summary."""

    response = openai_client.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=[
            {"role": "system", "content": "You are a stock analyst."},
            {"role": "user", "content": prompt}
        ],
        max_tokens=100
    )

    analysis = response.choices[0].message.content
    print(f"✅ AI Analysis:")
    print(f"   {analysis}")

    # Summary
    print("\n" + "="*60)
    print("RESULTS SUMMARY")
    print("="*60)
    print(f"✅ Yahoo Finance: NVDA at ${price:.2f}")
    print(f"✅ Tavily: {len(search_results['results'])} news articles found")
    print(f"✅ OpenAI: Analysis generated")
    print("\n🎯 All APIs are working! The issue is in the agent orchestration layer.")
    print("="*60)

    return {
        "price": price,
        "market_cap": market_cap,
        "news_count": len(search_results['results']),
        "analysis": analysis
    }

if __name__ == "__main__":
    result = asyncio.run(test_direct_apis())
    print(f"\n✅ Test completed successfully!")