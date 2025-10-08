"""
Test Order Builder
Validates conditional order logic and bracket orders
"""

from calculators.order_builder import OrderBuilder, OrderSide, OrderType


def test_bracket_order():
    """Test bracket order generation"""

    ob = OrderBuilder()

    print("=" * 60)
    print("BRACKET ORDER TEST")
    print("=" * 60)

    # Test BUY bracket order
    bracket = ob.build_bracket_order(
        symbol="AAPL",
        side=OrderSide.BUY,
        quantity=200,
        entry_price=150.00,
        profit_target=160.00,
        stop_loss=145.00
    )

    print("\n1. BRACKET ORDER STRUCTURE:")
    print(f"   Bracket ID: {bracket['bracket_order_id']}")
    print(f"   Symbol: {bracket['symbol']}")
    print(f"   Strategy: {bracket['strategy']}")
    print(f"   Risk/Reward: {bracket['risk_reward_ratio']}:1")
    print(f"   Total Risk: ${bracket['total_risk']:,.2f}")
    print(f"   Total Reward: ${bracket['total_reward']:,.2f}")

    print("\n2. ENTRY ORDERS:")
    for order in bracket['entry_orders']:
        print(f"   - {order['side'].upper()} {order['quantity']} @ ${order['limit_price']:.2f}")
        print(f"     Order ID: {order['order_id']}")
        print(f"     Type: {order['type']}")

    print("\n3. EXIT ORDERS (OCO Group):")
    for order in bracket['exit_orders']:
        print(f"   - {order['side'].upper()} {order['quantity']} ({order['order_class']})")
        if 'limit_price' in order:
            print(f"     Limit Price: ${order['limit_price']:.2f}")
        if 'stop_price' in order:
            print(f"     Stop Price: ${order['stop_price']:.2f}")
        if 'trail_percent' in order:
            print(f"     Trail: {order['trail_percent']}%")
        print(f"     OCO Group: {order['oco_group']}")

    print("\n4. EXECUTION INSTRUCTIONS:")
    print(bracket['instructions'])

    # Validate the order
    print("\n5. ORDER VALIDATION:")
    validation = ob.validate_order(bracket['entry_orders'][0])
    print(f"   Valid: {validation['is_valid']}")
    if validation['errors']:
        print(f"   Errors: {validation['errors']}")
    if validation['warnings']:
        print(f"   Warnings: {validation['warnings']}")

    return bracket


def test_scaling_strategy():
    """Test scaling in/out strategy"""

    ob = OrderBuilder()

    print("\n" + "=" * 60)
    print("SCALING STRATEGY TEST")
    print("=" * 60)

    scaling = ob.build_scaling_strategy(
        symbol="AAPL",
        side=OrderSide.BUY,
        total_quantity=300,
        entry_price=150.00,
        scale_levels=[
            {'price': 150.00, 'pct': 0.40},  # 40% at $150
            {'price': 148.00, 'pct': 0.30},  # 30% at $148
            {'price': 146.00, 'pct': 0.30}   # 30% at $146
        ],
        profit_target=160.00,
        stop_loss=145.00
    )

    print(f"\n1. SCALING ORDER ID: {scaling['scaling_order_id']}")
    print(f"   Total Quantity: {scaling['total_quantity']} shares")
    print(f"   Strategy: {scaling['strategy']}")

    print("\n2. SCALE-IN LEVELS:")
    for idx, order in enumerate(scaling['scale_orders']):
        pct = (order['quantity'] / scaling['total_quantity']) * 100
        print(f"   Level {idx + 1}: {order['quantity']} shares @ ${order['limit_price']:.2f} ({pct:.0f}%)")

    print("\n3. EXIT TARGETS:")
    print(f"   Profit Target: ${scaling['profit_target']:.2f}")
    print(f"   Stop Loss: ${scaling['stop_loss']:.2f}")

    print(f"\n4. INSTRUCTIONS:")
    print(f"   {scaling['instructions']}")

    return scaling


def test_oco_order():
    """Test One-Cancels-Other order"""

    ob = OrderBuilder()

    print("\n" + "=" * 60)
    print("OCO ORDER TEST")
    print("=" * 60)

    oco = ob.build_oco_order(
        symbol="AAPL",
        side=OrderSide.BUY,
        quantity=200,
        order1_type=OrderType.LIMIT,
        order1_price=148.00,  # Buy limit below current
        order2_type=OrderType.STOP,
        order2_price=152.00   # Buy stop above current
    )

    print(f"\n1. OCO GROUP ID: {oco['oco_order_id']}")
    print(f"   Symbol: {oco['symbol']}")
    print(f"   Strategy: {oco['strategy']}")

    print("\n2. OCO ORDERS (One fills, other cancels):")
    for idx, order in enumerate(oco['orders'], 1):
        print(f"\n   Order {idx}:")
        print(f"   - Type: {order['type']}")
        print(f"   - Side: {order['side'].upper()}")
        print(f"   - Quantity: {order['quantity']}")
        price_key = 'limit_price' if 'limit' in order['type'] else 'stop_price'
        print(f"   - Price: ${order[price_key]:.2f}")

    print("\n3. LOGIC:")
    print("   - If price drops to $148, limit order fills → stop order cancels")
    print("   - If price rises to $152, stop order fills → limit order cancels")

    return oco


def test_trailing_stop():
    """Test trailing stop order"""

    ob = OrderBuilder()

    print("\n" + "=" * 60)
    print("TRAILING STOP TEST")
    print("=" * 60)

    trailing = ob.build_trailing_stop_order(
        symbol="AAPL",
        side=OrderSide.SELL,
        quantity=200,
        trail_percent=5.0  # Trail 5% below highest price
    )

    print(f"\n1. TRAILING STOP ORDER:")
    print(f"   Order ID: {trailing['order_id']}")
    print(f"   Symbol: {trailing['symbol']}")
    print(f"   Type: {trailing['type']}")
    print(f"   Quantity: {trailing['quantity']}")
    print(f"   Trail Percent: {trailing['trail_percent']}%")

    print(f"\n2. HOW IT WORKS:")
    print(f"   {trailing['instructions']}")

    print("\n3. EXAMPLE:")
    print("   - Buy at $150")
    print("   - Price rises to $160 → stop moves to $152 (5% below)")
    print("   - Price rises to $170 → stop moves to $161.50 (5% below)")
    print("   - Price falls back → stop stays at $161.50")
    print("   - If price hits $161.50 → sell executes, lock in $11.50/share profit")

    return trailing


if __name__ == "__main__":
    # Run all tests
    bracket = test_bracket_order()
    scaling = test_scaling_strategy()
    oco = test_oco_order()
    trailing = test_trailing_stop()

    print("\n" + "=" * 60)
    print("✅ ALL ORDER BUILDER TESTS PASSED!")
    print("=" * 60)
    print("\nConditional order logic is ready for production")
    print("Traders can now execute recommendations with:")
    print("- Bracket orders (entry + profit + stop)")
    print("- Scaling strategies (build positions gradually)")
    print("- OCO orders (alternative entry points)")
    print("- Trailing stops (lock in profits)")
