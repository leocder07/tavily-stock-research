"""
Test Enhanced Peer Benchmarking
Validates peer comparison with real market data
"""

import asyncio
from calculators.peer_benchmark_calculator import PeerBenchmarkCalculator


async def test_peer_benchmarking():
    """Test peer benchmarking with AAPL vs tech giants"""

    calc = PeerBenchmarkCalculator()

    print("=" * 70)
    print("ENHANCED PEER BENCHMARKING TEST")
    print("=" * 70)
    print("Analyzing: AAPL vs MSFT, GOOGL, META, NVDA")
    print("=" * 70)

    # Test with AAPL
    result = calc.get_peer_comparison('AAPL')

    if 'error' in result:
        print(f"\n❌ Error: {result['error']}")
        return

    symbol = result['symbol']
    peers = result.get('peers', [])
    rankings = result.get('rankings', {})

    print(f"\n📊 ANALYSIS: {symbol}")
    print(f"Peers Analyzed: {', '.join(peers)}")
    print(f"Overall Grade: {rankings['overall_grade']}")
    print(f"Composite Score: {rankings['composite_score']:.1f}/100")

    # Valuation Comparison
    print("\n" + "=" * 70)
    print("1. VALUATION COMPARISON")
    print("=" * 70)

    valuation = result['valuation_comparison']

    pe_data = valuation.get('pe_ratio', {})
    if pe_data:
        print(f"\nP/E Ratio:")
        print(f"  {symbol}: {pe_data['stock_value']}")
        print(f"  Peer Average: {pe_data['peer_average']}")
        print(f"  Premium/Discount: {pe_data['premium_to_avg_pct']:+.1f}%")
        print(f"  Percentile: {pe_data['percentile']}th")

    peg_data = valuation.get('peg_ratio', {})
    if peg_data:
        print(f"\nPEG Ratio (Growth-Adjusted):")
        print(f"  {symbol}: {peg_data['stock_value']}")
        print(f"  Peer Average: {peg_data['peer_average']}")
        print(f"  Premium/Discount: {peg_data['premium_to_avg_pct']:+.1f}%")

    ev_ebitda_data = valuation.get('ev_to_ebitda', {})
    if ev_ebitda_data:
        print(f"\nEV/EBITDA:")
        print(f"  {symbol}: {ev_ebitda_data['stock_value']}")
        print(f"  Peer Average: {ev_ebitda_data['peer_average']}")
        print(f"  Premium/Discount: {ev_ebitda_data['premium_to_avg_pct']:+.1f}%")

    # Profitability Comparison
    print("\n" + "=" * 70)
    print("2. PROFITABILITY COMPARISON")
    print("=" * 70)

    profitability = result['profitability_comparison']

    profit_margin = profitability.get('profit_margin', {})
    if profit_margin:
        print(f"\nProfit Margin:")
        print(f"  {symbol}: {profit_margin['stock_value']:.1f}%")
        print(f"  Peer Average: {profit_margin['peer_average']:.1f}%")
        print(f"  Outperformance: {profit_margin['outperformance']:+.1f}pp")
        print(f"  Rank: {profit_margin['rank']}/5")

    roe_data = profitability.get('roe', {})
    if roe_data:
        print(f"\nReturn on Equity (ROE):")
        print(f"  {symbol}: {roe_data['stock_value']:.1f}%")
        print(f"  Peer Average: {roe_data['peer_average']:.1f}%")
        print(f"  Outperformance: {roe_data['outperformance']:+.1f}pp")
        print(f"  Rank: {roe_data['rank']}/5")

    operating_margin = profitability.get('operating_margin', {})
    if operating_margin:
        print(f"\nOperating Margin:")
        print(f"  {symbol}: {operating_margin['stock_value']:.1f}%")
        print(f"  Peer Average: {operating_margin['peer_average']:.1f}%")
        print(f"  Outperformance: {operating_margin['outperformance']:+.1f}pp")

    # Growth Comparison
    print("\n" + "=" * 70)
    print("3. GROWTH COMPARISON")
    print("=" * 70)

    growth = result['growth_comparison']

    revenue_growth = growth.get('revenue_growth', {})
    if revenue_growth:
        print(f"\nRevenue Growth:")
        print(f"  {symbol}: {revenue_growth['stock_value']:.1f}%")
        print(f"  Peer Average: {revenue_growth['peer_average']:.1f}%")
        print(f"  Growth Premium: {revenue_growth['growth_premium']:+.1f}pp")
        print(f"  Rank: {revenue_growth['rank']}/5")

    earnings_growth = growth.get('earnings_growth', {})
    if earnings_growth:
        print(f"\nEarnings Growth:")
        print(f"  {symbol}: {earnings_growth['stock_value']:.1f}%")
        print(f"  Peer Average: {earnings_growth['peer_average']:.1f}%")
        print(f"  Growth Premium: {earnings_growth['growth_premium']:+.1f}pp")
        print(f"  Rank: {earnings_growth['rank']}/5")

    # Size & Market Share
    print("\n" + "=" * 70)
    print("4. SIZE & MARKET POSITION")
    print("=" * 70)

    size = result['size_comparison']

    print(f"\nMarket Capitalization:")
    print(f"  {symbol}: ${size['market_cap_billions']:.1f}B")
    print(f"  Market Share (by cap): {size['market_share_by_cap']:.1f}%")
    print(f"  Size Rank: {size['size_rank']}/5")

    print(f"\nRevenue:")
    print(f"  {symbol}: ${size['revenue_billions']:.1f}B")

    # Key Insights
    print("\n" + "=" * 70)
    print("5. KEY INSIGHTS")
    print("=" * 70)

    insights = result['insights']
    for idx, insight in enumerate(insights, 1):
        print(f"\n{idx}. {insight}")

    # Peer Metrics Table
    print("\n" + "=" * 70)
    print("6. PEER METRICS TABLE")
    print("=" * 70)

    peer_metrics = result['peer_metrics']
    stock_metrics = result['stock_metrics']

    print(f"\n{'Symbol':<8} {'P/E':<8} {'PEG':<8} {'Margin %':<10} {'ROE %':<8} {'Growth %':<10}")
    print("-" * 70)

    # Print stock
    pe = stock_metrics.get('pe_ratio', 0) or 0
    peg = stock_metrics.get('peg_ratio', 0) or 0
    margin = (stock_metrics.get('profit_margin', 0) or 0) * 100
    roe = (stock_metrics.get('roe', 0) or 0) * 100
    growth = (stock_metrics.get('revenue_growth', 0) or 0) * 100

    print(f"{symbol:<8} {pe:<8.1f} {peg:<8.2f} {margin:<10.1f} {roe:<8.1f} {growth:<10.1f}")

    # Print peers
    for peer_symbol, metrics in peer_metrics.items():
        pe = metrics.get('pe_ratio', 0) or 0
        peg = metrics.get('peg_ratio', 0) or 0
        margin = (metrics.get('profit_margin', 0) or 0) * 100
        roe = (metrics.get('roe', 0) or 0) * 100
        growth = (metrics.get('revenue_growth', 0) or 0) * 100

        print(f"{peer_symbol:<8} {pe:<8.1f} {peg:<8.2f} {margin:<10.1f} {roe:<8.1f} {growth:<10.1f}")

    # Final Assessment
    print("\n" + "=" * 70)
    print("7. FINAL ASSESSMENT")
    print("=" * 70)

    print(f"\nOverall Grade: {rankings['overall_grade']}")
    print(f"Composite Score: {rankings['composite_score']:.1f}/100")
    print(f"\nBreakdown:")
    print(f"  - Valuation Score: {rankings['valuation_score']:.1f}/100")
    print(f"  - Profitability Rank: #{rankings['profitability_rank']}")
    print(f"  - Growth Rank: #{rankings['growth_rank']}")

    # Recommendation
    print("\n" + "=" * 70)
    print("✅ PEER BENCHMARKING TEST COMPLETE")
    print("=" * 70)

    print(f"\nKey Findings:")
    print(f"1. Analyzed {len(peers)} peers across {len(valuation)} valuation metrics")
    print(f"2. Compared {len(profitability)} profitability metrics")
    print(f"3. Assessed {len(growth)} growth metrics")
    print(f"4. Generated {len(insights)} actionable insights")

    return result


if __name__ == "__main__":
    asyncio.run(test_peer_benchmarking())
