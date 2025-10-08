#!/usr/bin/env python3
"""
Test the enhanced stock research system with multiple stocks
"""

import asyncio
import json
from datetime import datetime
from agents.simple_workflow import SimpleStockWorkflow
from agents.workers.enhanced_valuation_agent import EnhancedValuationAgent
from services.data_aggregator import DataAggregatorService
from services.market_mood import MarketMoodCalculator, SectorRotationAnalyzer
import os
from dotenv import load_dotenv
from tabulate import tabulate

# Load environment variables
load_dotenv()


async def test_stock_analysis(symbol: str, workflow: SimpleStockWorkflow):
    """Test analysis for a single stock"""
    print(f"\n{'='*80}")
    print(f"Testing {symbol}")
    print(f"{'='*80}")

    try:
        # Run the analysis
        query = f"Analyze {symbol} stock"
        result = await workflow.run(query, f"test_{symbol}", symbols=[symbol])

        # Extract key metrics
        analysis_data = {
            'Symbol': symbol,
            'Current Price': f"${result.get('analysis', {}).get('market_data', {}).get(symbol, {}).get('price', 0):.2f}",
            'Market Cap': f"${result.get('analysis', {}).get('market_data', {}).get(symbol, {}).get('marketCap', 0)/1e9:.1f}B",
            'P/E Ratio': result.get('analysis', {}).get('market_data', {}).get(symbol, {}).get('pe_ratio', 'N/A'),
        }

        # Valuation data
        if result.get('valuation'):
            val = result['valuation']
            analysis_data['DCF Price'] = f"${val.get('dcf_valuation', {}).get('dcf_price', 0):.2f}"
            analysis_data['WACC'] = f"{val.get('dcf_valuation', {}).get('wacc', 0):.2f}%"
            analysis_data['Analyst Target'] = f"${val.get('analyst_targets', {}).get('target_mean', 0):.2f}"
            analysis_data['Price Target'] = f"${val.get('price_target', {}).get('price_target', 0):.2f}"
            analysis_data['Upside'] = f"{val.get('price_target', {}).get('upside', 0):+.1f}%"
            analysis_data['Recommendation'] = val.get('price_target', {}).get('recommendation', 'N/A')

        # Confidence scores
        if result.get('confidence_scores'):
            conf = result['confidence_scores']
            analysis_data['Overall Confidence'] = f"{conf.get('overall', 0):.0f}%"
            analysis_data['Data Quality'] = f"{conf.get('price_data', 0):.0f}%"

        # Technical indicators
        if result.get('technical_analysis'):
            tech = result['technical_analysis']
            analysis_data['RSI'] = tech.get('indicators', {}).get('rsi', 'N/A')
            analysis_data['Technical Signal'] = tech.get('signals', {}).get('overall', 'N/A')

        # Market mood
        if result.get('market_mood'):
            mood = result['market_mood']
            analysis_data['Market Mood'] = mood.get('mood_level', 'N/A')
            analysis_data['Mood Score'] = mood.get('mood_score', 'N/A')

        return analysis_data

    except Exception as e:
        print(f"Error analyzing {symbol}: {e}")
        return {'Symbol': symbol, 'Error': str(e)}


async def test_multiple_stocks():
    """Test the system with multiple stocks"""

    # Initialize workflow
    workflow = SimpleStockWorkflow(
        tavily_api_key=os.getenv('TAVILY_API_KEY'),
        openai_api_key=os.getenv('OPENAI_API_KEY')
    )

    # Test stocks from different sectors
    test_stocks = [
        'NVDA',  # Technology - AI leader
        'AAPL',  # Technology - Consumer electronics
        'MSFT',  # Technology - Software
        'TSLA',  # Automotive - EV
        'AMD',   # Technology - Semiconductors
    ]

    print("\n" + "="*80)
    print("MULTI-STOCK SYSTEM TEST")
    print("="*80)
    print(f"Testing {len(test_stocks)} stocks: {', '.join(test_stocks)}")
    print(f"Timestamp: {datetime.now().isoformat()}")

    # Run all analyses
    results = []
    for symbol in test_stocks:
        result = await test_stock_analysis(symbol, workflow)
        results.append(result)
        await asyncio.sleep(2)  # Small delay between requests

    # Display summary table
    print("\n" + "="*80)
    print("SUMMARY RESULTS")
    print("="*80)

    # Create comparison table
    headers = list(results[0].keys())
    rows = []
    for result in results:
        rows.append([result.get(h, 'N/A') for h in headers])

    print(tabulate(rows, headers=headers, tablefmt='grid'))

    # Validation checks
    print("\n" + "="*80)
    print("VALIDATION CHECKS")
    print("="*80)

    issues = []
    for result in results:
        symbol = result.get('Symbol', 'Unknown')

        # Check WACC is reasonable (8-15% for tech companies)
        wacc_str = result.get('WACC', '0%')
        if wacc_str != 'N/A':
            try:
                wacc = float(wacc_str.replace('%', ''))
                if wacc > 15 or wacc < 6:
                    issues.append(f"{symbol}: WACC {wacc:.2f}% outside normal range (6-15%)")
            except:
                pass

        # Check if recommendation makes sense with upside
        upside_str = result.get('Upside', '+0%')
        recommendation = result.get('Recommendation', 'N/A')
        try:
            upside = float(upside_str.replace('%', '').replace('+', ''))
            if upside > 20 and recommendation == 'SELL':
                issues.append(f"{symbol}: Inconsistent - {upside:.1f}% upside but SELL recommendation")
            elif upside < -20 and recommendation == 'BUY':
                issues.append(f"{symbol}: Inconsistent - {upside:.1f}% downside but BUY recommendation")
        except:
            pass

        # Check analyst targets exist
        analyst_target = result.get('Analyst Target', '$0.00')
        if analyst_target == '$0.00':
            issues.append(f"{symbol}: Missing analyst target data")

    if issues:
        print("Issues found:")
        for issue in issues:
            print(f"  ❌ {issue}")
    else:
        print("✅ All validation checks passed!")

    # Market overview
    print("\n" + "="*80)
    print("MARKET OVERVIEW")
    print("="*80)

    # Calculate average metrics
    avg_confidence = []
    recommendations = {'BUY': 0, 'HOLD': 0, 'SELL': 0}

    for result in results:
        # Confidence
        conf_str = result.get('Overall Confidence', '0%')
        try:
            avg_confidence.append(float(conf_str.replace('%', '')))
        except:
            pass

        # Recommendations
        rec = result.get('Recommendation', 'N/A')
        if rec in recommendations:
            recommendations[rec] += 1

    if avg_confidence:
        print(f"Average Confidence: {sum(avg_confidence)/len(avg_confidence):.1f}%")

    print(f"Recommendations: BUY={recommendations['BUY']}, HOLD={recommendations['HOLD']}, SELL={recommendations['SELL']}")

    # Market mood
    if results[0].get('Market Mood'):
        print(f"Market Mood: {results[0]['Market Mood']} (Score: {results[0].get('Mood Score', 'N/A')})")

    print("\n" + "="*80)
    print("TEST COMPLETE")
    print("="*80)


if __name__ == "__main__":
    asyncio.run(test_multiple_stocks())