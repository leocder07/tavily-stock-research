"""
Test Backtest Fixes - Validate Realistic Results
Tests that the fixed backtest no longer shows unrealistic 96.9% accuracy
"""

import asyncio
import numpy as np
from datetime import datetime, timedelta
from calculators.model_backtester import ModelBacktester
from agents.workers.predictive_agent import PredictiveAnalyticsAgent


async def test_fixed_backtest():
    """Test that backtest now produces realistic results"""

    print("=" * 80)
    print("TESTING BACKTEST FIXES")
    print("=" * 80)

    backtester = ModelBacktester()

    # Generate realistic sample data (random walk with drift)
    print("\n1️⃣  Generating sample data...")
    np.random.seed(42)
    n_predictions = 100

    predictions = []
    actual_prices = [100]  # Start at $100
    timestamps = []

    for i in range(n_predictions):
        # Simulate actual price movement (random walk)
        actual_return = np.random.normal(0.0005, 0.02)  # 0.05% drift, 2% volatility
        actual_price = actual_prices[-1] * (1 + actual_return)
        actual_prices.append(actual_price)

        # Simulate prediction with realistic 55% accuracy
        # Use momentum signal with noise
        if i >= 5:
            momentum = (actual_prices[-1] - actual_prices[-5]) / actual_prices[-5]
            predicted_return = momentum * 0.3 + np.random.normal(0, 0.015)
        else:
            predicted_return = np.random.normal(0, 0.01)

        # Determine direction
        if predicted_return > 0.015:
            direction = 'up'
        elif predicted_return < -0.015:
            direction = 'down'
        else:
            direction = 'neutral'

        confidence = min(abs(predicted_return) * 30 + 0.4, 0.75)

        predictions.append({
            'direction': direction,
            'predicted_return': predicted_return,
            'confidence': confidence
        })

        timestamps.append(datetime.now() - timedelta(days=n_predictions - i))

    # Remove last actual price
    actual_prices = actual_prices[:-1]

    print(f"✅ Generated {len(predictions)} predictions")

    # Run backtest
    print("\n2️⃣  Running backtest with transaction costs and slippage...")
    result = backtester.backtest_predictions(
        predictions=predictions,
        actual_prices=actual_prices,
        timestamps=timestamps,
        initial_capital=100000
    )

    print("\n" + "=" * 80)
    print("BACKTEST RESULTS")
    print("=" * 80)

    print(f"\n📊 Performance Metrics:")
    print(f"   Total Predictions: {result.total_predictions}")
    print(f"   Correct Predictions: {result.correct_predictions}")
    print(f"   Accuracy: {result.accuracy * 100:.1f}%")
    print(f"   Win Rate: {result.win_rate * 100:.1f}%")
    print(f"   Total Return: {result.total_return * 100:.1f}%")
    print(f"   Avg Return/Trade: {result.avg_return * 100:.2f}%")

    print(f"\n📈 Risk-Adjusted Metrics:")
    print(f"   Sharpe Ratio: {result.sharpe_ratio:.2f}")
    print(f"   Sortino Ratio: {result.sortino_ratio:.2f}")
    print(f"   Max Drawdown: {result.max_drawdown * 100:.1f}%")

    print(f"\n✅ Validation Status:")
    print(f"   Passed: {result.validation_passed}")
    if not result.validation_passed:
        print(f"   ⚠️  Validation Errors:")
        for error in result.validation_errors:
            print(f"      - {error}")

    # Check if results are realistic
    print("\n" + "=" * 80)
    print("VALIDATION CHECKS")
    print("=" * 80)

    checks = []

    # Check 1: Accuracy should be realistic
    if result.accuracy <= 0.70:
        checks.append(("✅", f"Accuracy {result.accuracy*100:.1f}% is realistic (≤70%)"))
    else:
        checks.append(("❌", f"Accuracy {result.accuracy*100:.1f}% is too high (>70%)"))

    # Check 2: Sharpe should be realistic
    if result.sharpe_ratio <= 4.0:
        checks.append(("✅", f"Sharpe {result.sharpe_ratio:.2f} is realistic (≤4.0)"))
    else:
        checks.append(("❌", f"Sharpe {result.sharpe_ratio:.2f} is too high (>4.0)"))

    # Check 3: Win rate should be realistic
    if result.win_rate <= 0.65:
        checks.append(("✅", f"Win rate {result.win_rate*100:.1f}% is realistic (≤65%)"))
    else:
        checks.append(("❌", f"Win rate {result.win_rate*100:.1f}% is too high (>65%)"))

    # Check 4: Transaction costs should have impact
    # With 0.25% total costs per round trip, we should see impact on returns
    avg_return_pct = result.avg_return * 100
    if avg_return_pct < 0.5:  # Should be small due to costs
        checks.append(("✅", f"Avg return {avg_return_pct:.2f}% shows transaction cost impact"))
    else:
        checks.append(("❌", f"Avg return {avg_return_pct:.2f}% seems high (costs may not be applied)"))

    # Check 5: Max drawdown should exist
    if result.max_drawdown < 0:
        checks.append(("✅", f"Max drawdown {result.max_drawdown*100:.1f}% exists (not zero)"))
    else:
        checks.append(("❌", f"Max drawdown is zero (unrealistic)"))

    print()
    for status, message in checks:
        print(f"{status} {message}")

    # Summary
    passed = sum(1 for status, _ in checks if status == "✅")
    total = len(checks)

    print("\n" + "=" * 80)
    print(f"SUMMARY: {passed}/{total} checks passed")
    print("=" * 80)

    return result


async def test_predictive_agent_integration():
    """Test the full predictive agent with fixed backtest"""

    print("\n\n" + "=" * 80)
    print("TESTING PREDICTIVE AGENT INTEGRATION")
    print("=" * 80)

    agent = PredictiveAnalyticsAgent()

    # Test with real stock data
    print("\n📊 Running predictive analysis with backtest for AAPL...")
    result = await agent.execute('AAPL')

    if 'error' in result:
        print(f"❌ Error: {result['error']}")
        return

    # Extract backtest results
    if 'backtest_results' in result:
        bt = result['backtest_results']

        print(f"\n📊 BACKTEST RESULTS:")
        print(f"   Accuracy: {bt.get('accuracy', 'N/A')}")
        print(f"   Win Rate: {bt.get('win_rate', 'N/A')}")
        print(f"   Sharpe Ratio: {bt.get('sharpe_ratio', 'N/A')}")
        print(f"   Total Return: {bt.get('total_return', 'N/A')}")
        print(f"   Max Drawdown: {bt.get('max_drawdown', 'N/A')}")
        print(f"   Performance Grade: {bt.get('performance_grade', 'N/A')}")

        print(f"\n✅ Validation:")
        print(f"   Passed: {bt.get('validation_passed', False)}")

        if not bt.get('validation_passed', True):
            print(f"   ⚠️  Errors:")
            for error in bt.get('validation_errors', []):
                print(f"      - {error}")

        if 'out_of_sample' in bt:
            oos = bt['out_of_sample']
            print(f"\n🔬 Out-of-Sample:")
            print(f"   Train Accuracy: {oos.get('train_accuracy', 'N/A')}")
            print(f"   Test Accuracy: {oos.get('test_accuracy', 'N/A')}")
            print(f"   Overfitting Gap: {oos.get('overfitting_gap', 'N/A')}")

        print(f"\n📋 {bt.get('disclaimer', '')}")

    print("\n" + "=" * 80)
    print("INTEGRATION TEST COMPLETE")
    print("=" * 80)


async def main():
    """Run all tests"""

    print("\n" + "=" * 80)
    print("BACKTEST FIX VALIDATION SUITE")
    print("Testing fixes for unrealistic 96.9% accuracy and 9.88 Sharpe ratio")
    print("=" * 80)

    # Test 1: Direct backtest framework
    await test_fixed_backtest()

    # Test 2: Full integration with predictive agent
    await test_predictive_agent_integration()

    print("\n\n" + "=" * 80)
    print("ALL TESTS COMPLETED")
    print("=" * 80)
    print("\n📝 Expected Results:")
    print("   - Accuracy: 50-65% (previously 96.9%)")
    print("   - Sharpe Ratio: 0.5-2.5 (previously 9.88)")
    print("   - Win Rate: 45-60% (previously ~97%)")
    print("   - Transaction costs visible in returns")
    print("   - Max drawdown exists (not zero)")
    print("\n✅ If validation checks pass, the look-ahead bias has been fixed!")


if __name__ == "__main__":
    asyncio.run(main())
