"""
Test Chart Pattern Detection Integration
Tests pattern detector with real market data via yfinance
"""

import asyncio
import os
from dotenv import load_dotenv
import yfinance as yf
from datetime import datetime, timedelta
from langchain_openai import ChatOpenAI
from agents.expert_agents.expert_technical_agent import ExpertTechnicalAgent

# Load environment variables
load_dotenv()


async def test_pattern_detection_with_real_data():
    """Test pattern detection with real AAPL data"""

    print("=" * 70)
    print("CHART PATTERN DETECTION TEST - REAL MARKET DATA")
    print("=" * 70)

    # Initialize agent
    llm = ChatOpenAI(model="gpt-4", temperature=0.1)
    agent = ExpertTechnicalAgent(llm)

    # Fetch real data for AAPL
    symbol = "AAPL"
    print(f"\n📊 Fetching data for {symbol}...")

    ticker = yf.Ticker(symbol)

    # Get 6 months of daily data for pattern detection
    end_date = datetime.now()
    start_date = end_date - timedelta(days=180)

    hist = ticker.history(start=start_date, end=end_date)

    if hist.empty:
        print(f"❌ No data available for {symbol}")
        return

    print(f"✅ Retrieved {len(hist)} days of data")

    # Prepare context
    context = {
        'symbol': symbol,
        'price': float(hist['Close'].iloc[-1]),
        'prices': hist['Close'].tolist(),
        'highs': hist['High'].tolist(),
        'lows': hist['Low'].tolist(),
        'volumes': hist['Volume'].tolist()
    }

    print(f"\nCurrent Price: ${context['price']:.2f}")
    print(f"Price Range: ${hist['Close'].min():.2f} - ${hist['Close'].max():.2f}")

    # Run technical analysis with pattern detection
    print(f"\n🔍 Running technical analysis with pattern detection...")
    result = await agent.analyze(context)

    # Display results
    print("\n" + "=" * 70)
    print("ANALYSIS RESULTS")
    print("=" * 70)

    print(f"\n📈 Technical Signal: {result.get('signal', 'N/A')}")
    print(f"📊 Trend: {result.get('trend', 'N/A')}")
    print(f"🎯 Confidence: {result.get('confidence', 0) * 100:.1f}%")

    # Pattern detection results
    patterns = result.get('patterns', {})
    print(f"\n🔍 CHART PATTERNS DETECTED: {patterns.get('patterns_detected', 0)}")

    if patterns.get('patterns'):
        print("\nDetected Patterns:")
        for i, pattern in enumerate(patterns['patterns'][:5], 1):
            print(f"\n{i}. {pattern.get('pattern', 'Unknown')}")
            print(f"   Type: {pattern.get('type', 'N/A')}")
            print(f"   Confidence: {pattern.get('confidence', 0) * 100:.0f}%")
            print(f"   Target: ${pattern.get('target', 'N/A')}")
            print(f"   Description: {pattern.get('description', '')}")

    # Support/Resistance levels
    sr_data = patterns.get('support_resistance', {})
    support_levels = sr_data.get('support', [])
    resistance_levels = sr_data.get('resistance', [])

    print(f"\n💪 Support Levels: {[f'${s:.2f}' for s in support_levels[:3]]}")
    print(f"🚧 Resistance Levels: {[f'${r:.2f}' for r in resistance_levels[:3]]}")

    # Pattern trading signals
    pattern_signals = patterns.get('trading_signals', [])
    if pattern_signals:
        print(f"\n📡 PATTERN TRADING SIGNALS:")
        for signal in pattern_signals[:3]:
            # Handle both dict and string formats
            if isinstance(signal, dict):
                print(f"   {signal.get('signal', 'HOLD')} at ${signal.get('price_target', 'N/A')}")
                print(f"   Reasoning: {signal.get('reasoning', '')}")
            else:
                print(f"   {signal}")

    # Technical indicators
    print(f"\n📊 TECHNICAL INDICATORS:")

    rsi = result.get('rsi', {})
    print(f"   RSI: {rsi.get('value', 'N/A')} ({rsi.get('signal', 'neutral')})")

    macd = result.get('macd', {})
    print(f"   MACD: {macd.get('macd', 'N/A')} (Trend: {macd.get('trend', 'neutral')})")

    bb = result.get('bollinger_bands', {})
    print(f"   Bollinger Bands: {bb.get('position', 'N/A')}")

    gc = result.get('golden_cross', {})
    print(f"   Golden/Death Cross: {gc.get('type', 'none')}")

    # Expert insights
    insights = result.get('insights', {})
    if insights:
        print(f"\n🎓 EXPERT ANALYSIS:")
        print(f"\n📈 Trend Analysis:")
        print(f"   {insights.get('trend_analysis', 'N/A')}")

        print(f"\n🔍 Pattern Recognition:")
        print(f"   {insights.get('pattern_recognition', 'N/A')}")

        print(f"\n🎯 Entry/Exit Strategy:")
        print(f"   {insights.get('entry_exit_strategy', 'N/A')}")

    print("\n" + "=" * 70)
    print("TEST COMPLETED SUCCESSFULLY")
    print("=" * 70)


async def test_multiple_stocks():
    """Test pattern detection on multiple stocks"""

    print("\n" + "=" * 70)
    print("MULTI-STOCK PATTERN DETECTION TEST")
    print("=" * 70)

    symbols = ['AAPL', 'TSLA', 'NVDA']
    llm = ChatOpenAI(model="gpt-4", temperature=0.1)
    agent = ExpertTechnicalAgent(llm)

    for symbol in symbols:
        print(f"\n📊 Analyzing {symbol}...")

        try:
            ticker = yf.Ticker(symbol)
            end_date = datetime.now()
            start_date = end_date - timedelta(days=180)
            hist = ticker.history(start=start_date, end=end_date)

            if hist.empty:
                print(f"   ❌ No data for {symbol}")
                continue

            context = {
                'symbol': symbol,
                'price': float(hist['Close'].iloc[-1]),
                'prices': hist['Close'].tolist(),
                'highs': hist['High'].tolist(),
                'lows': hist['Low'].tolist(),
                'volumes': hist['Volume'].tolist()
            }

            result = await agent.analyze(context)
            patterns = result.get('patterns', {})

            print(f"   Current Price: ${context['price']:.2f}")
            print(f"   Signal: {result.get('signal', 'N/A')}")
            print(f"   Patterns Detected: {patterns.get('patterns_detected', 0)}")

            if patterns.get('patterns'):
                top_pattern = patterns['patterns'][0]
                print(f"   Top Pattern: {top_pattern.get('pattern', 'N/A')} ({top_pattern.get('type', 'N/A')})")
                print(f"   Confidence: {top_pattern.get('confidence', 0) * 100:.0f}%")

        except Exception as e:
            print(f"   ❌ Error analyzing {symbol}: {e}")

    print("\n" + "=" * 70)
    print("MULTI-STOCK TEST COMPLETED")
    print("=" * 70)


if __name__ == "__main__":
    # Run tests
    asyncio.run(test_pattern_detection_with_real_data())
    asyncio.run(test_multiple_stocks())
