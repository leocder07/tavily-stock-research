"""
Test ATR-based stop loss calculation in ExpertSynthesisAgent
Verifies that stop loss is calculated correctly as: price - (ATR * 2)
"""

import sys
import asyncio
import logging
from typing import Dict, Any

# Setup logging to see validation messages
logging.basicConfig(
    level=logging.INFO,
    format='%(levelname)s:%(name)s:%(message)s'
)

# Import the synthesis agent
from agents.expert_agents.expert_synthesis_agent import ExpertSynthesisAgent
from langchain_openai import ChatOpenAI


async def test_atr_stop_loss():
    """Test ATR-based stop loss calculation"""

    print("\n" + "="*80)
    print("ATR STOP LOSS CALCULATION TEST")
    print("="*80)

    # Initialize agent
    llm = ChatOpenAI(model="gpt-4", temperature=0)
    agent = ExpertSynthesisAgent(llm)

    # Test Case 1: AAPL with ATR = $21.50
    print("\n[TEST 1] AAPL at $257 with ATR = $21.50")
    print("-" * 80)

    analyses_aapl = {
        'fundamental': {
            'symbol': 'AAPL',
            'recommendation': 'BUY',
            'confidence': 0.7,
            'pe_ratio': 39.2,
            'roe': 4.3,
            'analyst_target_price': 280
        },
        'technical': {
            'signal': 'BUY',
            'confidence': 0.65,
            'trend': 'uptrend',
            'rsi': {'value': 71.05},
            'indicators': {
                'atr': {'value': 21.5}  # CRITICAL: ATR value
            },
            'volatility': 0.25
        },
        'risk': {
            'risk_level': 'medium',
            'sharpe_ratio': 1.2,
            'max_drawdown': 15,
            'var_95': 2500
        },
        'sentiment': {
            'overall_sentiment': 'neutral',
            'sentiment_score': 55,
            'confidence': 0.5
        },
        'market': {
            'symbol': 'AAPL',
            'price': 257.0
        },
        'news': {
            'sentiment': {
                'overall': 'neutral',
                'score': 0.1,
                'confidence': 0.6
            },
            'key_events': ['Q4 earnings ahead'],
            'analyst_actions': []
        },
        'macro': {
            'market_regime': {
                'regime': 'neutral',
                'fed_policy': 'neutral'
            },
            'sector_analysis': {
                'trend': 'neutral'
            }
        }
    }

    # Run synthesis
    result = await agent.synthesize(analyses_aapl)

    # Verify results
    stop_loss = result.get('stop_loss')
    entry_price = result.get('entry_price')

    expected_stop = 257.0 - (21.5 * 2)  # = $214.00

    print(f"\nRESULTS:")
    print(f"  Entry Price: ${entry_price:.2f}")
    print(f"  Stop Loss:   ${stop_loss:.2f}")
    print(f"  ATR:         $21.50")
    print(f"  Expected:    ${expected_stop:.2f}")
    print(f"  Formula:     ${entry_price:.2f} - ($21.50 * 2) = ${stop_loss:.2f}")

    # Check if correct
    if abs(stop_loss - expected_stop) < 1:
        print(f"  ✅ STATUS:    CORRECT (stop loss uses ATR formula)")
    else:
        print(f"  ❌ STATUS:    WRONG (expected ~${expected_stop:.2f}, got ${stop_loss:.2f})")

    # Check validation
    validation_errors = result.get('validation_errors', [])
    validation_warnings = result.get('validation_warnings', [])

    print(f"\nVALIDATION:")
    if validation_errors:
        print(f"  ❌ Errors ({len(validation_errors)}):")
        for err in validation_errors:
            print(f"     - {err}")
    else:
        print(f"  ✅ No validation errors")

    if validation_warnings:
        print(f"  ⚠️  Warnings ({len(validation_warnings)}):")
        for warn in validation_warnings:
            print(f"     - {warn}")
    else:
        print(f"  ✅ No validation warnings")

    # Test Case 2: No ATR available (fallback)
    print("\n" + "="*80)
    print("[TEST 2] Stock with NO ATR (fallback to 2%)")
    print("-" * 80)

    analyses_no_atr = analyses_aapl.copy()
    analyses_no_atr['technical'] = {
        'signal': 'BUY',
        'confidence': 0.65,
        'trend': 'uptrend',
        'rsi': {'value': 60},
        'indicators': {},  # No ATR
        'volatility': 0.20
    }

    result_no_atr = await agent.synthesize(analyses_no_atr)
    stop_no_atr = result_no_atr.get('stop_loss')
    expected_fallback = 257.0 * 0.98  # 2% below

    print(f"\nRESULTS:")
    print(f"  Entry Price: ${entry_price:.2f}")
    print(f"  Stop Loss:   ${stop_no_atr:.2f}")
    print(f"  Expected:    ${expected_fallback:.2f} (2% fallback)")

    if abs(stop_no_atr - expected_fallback) < 1:
        print(f"  ✅ STATUS:    CORRECT (fallback to 2% when no ATR)")
    else:
        print(f"  ⚠️  STATUS:    Different than expected (got ${stop_no_atr:.2f})")

    # Summary
    print("\n" + "="*80)
    print("SUMMARY")
    print("="*80)

    tests_passed = 0
    tests_total = 2

    if abs(stop_loss - expected_stop) < 1:
        print("✅ TEST 1 PASSED: ATR-based stop loss calculation correct")
        tests_passed += 1
    else:
        print("❌ TEST 1 FAILED: ATR-based stop loss calculation incorrect")

    if abs(stop_no_atr - expected_fallback) < 2:  # Allow more variance for fallback
        print("✅ TEST 2 PASSED: Fallback stop loss when no ATR")
        tests_passed += 1
    else:
        print("⚠️  TEST 2 PARTIAL: Fallback differs from 2% (may use rule-based)")

    print(f"\nFINAL RESULT: {tests_passed}/{tests_total} tests passed")

    if stop_loss != 2739.0:  # Check it's NOT the old wrong value
        print("✅ CONFIRMED: Stop loss is NOT the old wrong value ($2,739)")
    else:
        print("❌ CRITICAL: Stop loss is still the old wrong value ($2,739)!")

    print("="*80 + "\n")

    return tests_passed == tests_total


if __name__ == "__main__":
    success = asyncio.run(test_atr_stop_loss())
    sys.exit(0 if success else 1)
