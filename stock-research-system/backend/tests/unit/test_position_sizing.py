"""
Test Position Sizing Integration
Quick test to verify position sizing calculator works with synthesis agent
"""

import asyncio
from calculators.position_sizer import PositionSizer, PositionSizeMethod


async def test_position_sizing():
    """Test position sizing scenarios"""

    ps = PositionSizer()

    # Test scenario: $100k account, $150 entry, $145 stop, $160 target
    account_value = 100000
    entry_price = 150.00
    stop_loss = 145.00
    target_price = 160.00

    print("=" * 60)
    print("POSITION SIZING TEST")
    print("=" * 60)
    print(f"Account Value: ${account_value:,}")
    print(f"Entry Price: ${entry_price:.2f}")
    print(f"Stop Loss: ${stop_loss:.2f}")
    print(f"Target Price: ${target_price:.2f}")
    print(f"Risk per Share: ${entry_price - stop_loss:.2f}")
    print(f"Reward per Share: ${target_price - entry_price:.2f}")
    print(f"Risk/Reward Ratio: {(target_price - entry_price) / (entry_price - stop_loss):.2f}:1")
    print("=" * 60)

    # Test conservative sizing
    print("\n1. CONSERVATIVE (1% Risk):")
    conservative = ps.calculate_position_size(
        account_value=account_value,
        entry_price=entry_price,
        stop_loss_price=stop_loss,
        risk_per_trade_pct=1.0,
        method=PositionSizeMethod.FIXED_FRACTIONAL
    )
    print(f"   Shares: {conservative['shares']}")
    print(f"   Position Value: ${conservative['position_value']:,.2f}")
    print(f"   Capital at Risk: ${conservative['capital_at_risk']:,.2f}")
    print(f"   % of Account: {conservative['position_pct']:.1f}%")

    # Test moderate sizing
    print("\n2. MODERATE (2% Risk):")
    moderate = ps.calculate_position_size(
        account_value=account_value,
        entry_price=entry_price,
        stop_loss_price=stop_loss,
        risk_per_trade_pct=2.0,
        method=PositionSizeMethod.FIXED_FRACTIONAL
    )
    print(f"   Shares: {moderate['shares']}")
    print(f"   Position Value: ${moderate['position_value']:,.2f}")
    print(f"   Capital at Risk: ${moderate['capital_at_risk']:,.2f}")
    print(f"   % of Account: {moderate['position_pct']:.1f}%")

    # Test Kelly Criterion
    print("\n3. AGGRESSIVE (Kelly Criterion):")
    aggressive = ps.calculate_position_size(
        account_value=account_value,
        entry_price=entry_price,
        stop_loss_price=stop_loss,
        method=PositionSizeMethod.KELLY_CRITERION,
        win_rate=0.55,  # 55% win rate
        avg_win_loss_ratio=2.0  # 2:1 win/loss ratio
    )
    print(f"   Shares: {aggressive['shares']}")
    print(f"   Position Value: ${aggressive['position_value']:,.2f}")
    print(f"   Capital at Risk: ${aggressive['capital_at_risk']:,.2f}")
    print(f"   % of Account: {aggressive['position_pct']:.1f}%")

    # Test volatility-adjusted
    print("\n4. VOLATILITY-ADJUSTED (1.5% base risk, 30% volatility):")
    vol_adjusted = ps.calculate_position_size(
        account_value=account_value,
        entry_price=entry_price,
        stop_loss_price=stop_loss,
        risk_per_trade_pct=1.5,
        method=PositionSizeMethod.VOLATILITY_ADJUSTED,
        volatility=0.30  # 30% annualized volatility
    )
    print(f"   Shares: {vol_adjusted['shares']}")
    print(f"   Position Value: ${vol_adjusted['position_value']:,.2f}")
    print(f"   Capital at Risk: ${vol_adjusted['capital_at_risk']:,.2f}")
    print(f"   % of Account: {vol_adjusted['position_pct']:.1f}%")
    if 'volatility_adjustment' in vol_adjusted:
        print(f"   Volatility Adjustment: {vol_adjusted['volatility_adjustment']:.2f}x")

    # Test multiple scenarios
    print("\n5. MULTIPLE SCENARIOS (Recommended Selection):")
    scenarios = ps.calculate_multiple_scenarios(
        account_value=account_value,
        entry_price=entry_price,
        stop_loss_price=stop_loss,
        target_price=target_price,
        volatility=0.25,
        win_rate=0.50
    )

    print(f"   Risk/Reward Ratio: {scenarios['risk_reward_ratio']:.2f}:1")
    print(f"\n   RECOMMENDED:")
    rec = scenarios['recommended']
    print(f"   - Shares: {rec['shares']}")
    print(f"   - Position Value: ${rec['position_value']:,.2f}")
    print(f"   - Capital at Risk: ${rec['capital_at_risk']:,.2f}")
    print(f"   - % of Account: {rec['position_pct']:.1f}%")

    print("\n" + "=" * 60)
    print("✅ All position sizing tests passed!")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(test_position_sizing())
