#!/usr/bin/env python3
"""Test script for enhanced valuation agent"""

import asyncio
import os
import sys
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from agents.workers.enhanced_valuation_agent import EnhancedValuationAgent


async def test_nvda_valuation():
    """Test NVDA valuation with enhanced agent"""
    agent = EnhancedValuationAgent()

    print("\n" + "="*60)
    print("Testing Enhanced Valuation Agent with NVDA")
    print("="*60)

    # Run valuation for NVDA
    result = await agent.execute("NVDA", None)

    if "error" in result:
        print(f"Error: {result['error']}")
        return

    # Display results
    print(f"\nSymbol: {result['symbol']}")
    print(f"Current Price: ${result['current_price']:.2f}")

    print("\n--- Analyst Targets ---")
    analyst = result.get('analyst_targets', {})
    print(f"Consensus: {analyst.get('analyst_consensus', 'N/A')}")
    print(f"Mean Target: ${analyst.get('target_mean', 0):.2f}")
    print(f"High Target: ${analyst.get('target_high', 0):.2f}")
    print(f"Low Target: ${analyst.get('target_low', 0):.2f}")
    print(f"Upside Potential: {analyst.get('upside_potential', 0):.1f}%")
    print(f"Data Source: {analyst.get('data_source', 'unknown')}")

    print("\n--- DCF Valuation ---")
    dcf = result.get('dcf_valuation', {})
    print(f"DCF Price: ${dcf.get('dcf_price', 0):.2f}")
    print(f"WACC: {dcf.get('wacc', 0):.2f}%")
    print(f"Growth Assumptions: {dcf.get('growth_assumptions', {})}")

    print("\n--- Comparative Valuation ---")
    comp = result.get('comparative_valuation', {})
    print(f"Comparative Price: ${comp.get('comparative_price', 0):.2f}")
    print(f"P/E Ratio: {comp.get('pe_ratio', 'N/A')}")
    print(f"Forward P/E: {comp.get('forward_pe', 'N/A')}")
    print(f"Valuation Rating: {comp.get('valuation_rating', 'N/A')}")

    print("\n--- Final Price Target ---")
    target = result.get('price_target', {})
    print(f"Price Target: ${target.get('price_target', 0):.2f}")
    print(f"Upside/Downside: {target.get('upside', 0):+.1f}%")
    print(f"Confidence: {target.get('confidence', 0)*100:.0f}%")
    print(f"Recommendation: {target.get('recommendation', 'N/A')}")

    print("\n--- Summary ---")
    print(result.get('valuation_summary', 'No summary available'))

    # Validation checks
    print("\n" + "="*60)
    print("VALIDATION CHECKS")
    print("="*60)

    issues = []

    # Check analyst targets
    if analyst.get('target_mean', 0) < 100:
        issues.append(f"❌ Analyst target too low: ${analyst.get('target_mean', 0):.2f} (should be ~$212)")
    else:
        print(f"✅ Analyst target reasonable: ${analyst.get('target_mean', 0):.2f}")

    # Check WACC
    wacc = dcf.get('wacc', 0)
    if wacc > 15:
        issues.append(f"❌ WACC too high: {wacc:.2f}% (should be 8-12%)")
    else:
        print(f"✅ WACC reasonable: {wacc:.2f}%")

    # Check final target
    final_target = target.get('price_target', 0)
    if final_target < 150:
        issues.append(f"❌ Final target too low: ${final_target:.2f} (should be ~$200+)")
    else:
        print(f"✅ Final target reasonable: ${final_target:.2f}")

    # Check recommendation
    rec = target.get('recommendation', '')
    if rec in ['SELL', 'STRONG SELL']:
        issues.append(f"❌ Wrong recommendation: {rec} (should be BUY/HOLD)")
    else:
        print(f"✅ Recommendation appropriate: {rec}")

    if issues:
        print("\n⚠️  Issues found:")
        for issue in issues:
            print(f"  {issue}")
    else:
        print("\n✅ All validation checks passed!")

    print("\n" + "="*60)


if __name__ == "__main__":
    asyncio.run(test_nvda_valuation())