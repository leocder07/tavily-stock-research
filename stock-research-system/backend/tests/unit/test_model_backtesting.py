"""
Test Model Backtesting Integration
Tests predictive agent with backtest metrics
"""

import asyncio
from agents.workers.predictive_agent import PredictiveAnalyticsAgent


async def test_backtesting_integration():
    """Test predictive agent with integrated backtesting"""

    print("=" * 70)
    print("MODEL BACKTESTING TEST")
    print("=" * 70)

    # Initialize agent
    agent = PredictiveAnalyticsAgent()

    # Test symbols
    symbols = ['AAPL', 'TSLA']

    for symbol in symbols:
        print(f"\n{'='*70}")
        print(f"Testing {symbol}")
        print(f"{'='*70}")

        # Run prediction with backtesting
        result = await agent.execute(symbol)

        if 'error' in result:
            print(f"❌ Error: {result['error']}")
            continue

        # Display backtest results
        if 'backtest_results' in result:
            bt = result['backtest_results']

            print(f"\n📊 BACKTEST PERFORMANCE METRICS:")
            print(f"{'='*70}")

            # Overall metrics
            print(f"\n🎯 Accuracy: {bt.get('accuracy', 'N/A')}")
            print(f"📈 Win Rate: {bt.get('win_rate', 'N/A')}")
            print(f"💰 Total Return: {bt.get('total_return', 'N/A')}")
            print(f"📉 Max Drawdown: {bt.get('max_drawdown', 'N/A')}")

            # Risk-adjusted returns
            print(f"\n📊 RISK-ADJUSTED METRICS:")
            print(f"   Sharpe Ratio: {bt.get('sharpe_ratio', 'N/A')}")
            print(f"   Sortino Ratio: {bt.get('sortino_ratio', 'N/A')}")

            # Performance grade
            grade = bt.get('performance_grade', 'N/A')
            print(f"\n🏆 Performance Grade: {grade}")

            # Out-of-sample results
            if 'out_of_sample' in bt:
                oos = bt['out_of_sample']
                print(f"\n🔬 OUT-OF-SAMPLE TESTING:")
                print(f"   Train Accuracy: {oos.get('train_accuracy', 'N/A')}")
                print(f"   Test Accuracy: {oos.get('test_accuracy', 'N/A')}")
                print(f"   Overfitting Gap: {oos.get('overfitting_gap', 'N/A')}")

                # Check for overfitting
                gap_str = oos.get('overfitting_gap', '0%')
                gap = float(gap_str.replace('%', ''))
                if gap > 15:
                    print(f"   ⚠️  WARNING: Possible overfitting detected!")
                elif gap > 10:
                    print(f"   ⚡ Moderate overfitting - monitor closely")
                else:
                    print(f"   ✅ Model is well-generalized")

            # Summary
            if 'summary' in bt:
                summary = bt['summary']
                print(f"\n📋 SUMMARY:")
                print(f"   Total Predictions: {summary.get('total_predictions', 'N/A')}")
                print(f"   Accuracy: {summary.get('accuracy', 'N/A')}")
                print(f"   Win Rate: {summary.get('win_rate', 'N/A')}")
                print(f"   Avg Return/Trade: {summary.get('avg_return_per_trade', 'N/A')}")

        # Display price predictions
        predictions = result.get('predictions', {})
        price_forecast = predictions.get('price_forecast', {})

        print(f"\n💲 PRICE PREDICTIONS:")
        print(f"   Current: ${result.get('current_price', 0):.2f}")

        for period in ['1_day', '5_day', '30_day']:
            if period in price_forecast:
                forecast = price_forecast[period]
                if 'ensemble' in forecast:
                    expected_return = forecast.get('expected_return', 0)
                    print(f"   {period.replace('_', ' ').title()}: ${forecast['ensemble']:.2f} ({expected_return:+.2f}%)")

        # Model confidence
        print(f"\n🔍 Model Confidence: {result.get('model_confidence', 0)*100:.1f}%")

    print(f"\n{'='*70}")
    print("TEST COMPLETED")
    print(f"{'='*70}")


async def test_backtest_framework_directly():
    """Test backtesting framework directly with sample data"""

    from calculators.model_backtester import ModelBacktester
    from datetime import datetime, timedelta
    import numpy as np

    print("\n" + "=" * 70)
    print("DIRECT BACKTESTING FRAMEWORK TEST")
    print("=" * 70)

    backtester = ModelBacktester()

    # Generate sample predictions (simulated)
    np.random.seed(42)
    n_predictions = 100

    predictions = []
    actual_prices = [100]  # Start at $100
    timestamps = []

    for i in range(n_predictions):
        # Simulate actual price movement
        actual_return = np.random.normal(0.001, 0.02)  # Mean 0.1% daily return, 2% volatility
        actual_price = actual_prices[-1] * (1 + actual_return)
        actual_prices.append(actual_price)

        # Simulate prediction (with some accuracy)
        prediction_accuracy = 0.6  # 60% correlation
        predicted_return = actual_return * prediction_accuracy + np.random.normal(0, 0.01)

        direction = 'up' if predicted_return > 0.005 else ('down' if predicted_return < -0.005 else 'neutral')
        confidence = min(abs(predicted_return) * 50 + 0.4, 0.9)

        predictions.append({
            'direction': direction,
            'predicted_return': predicted_return,
            'confidence': confidence
        })

        timestamps.append(datetime.now() - timedelta(days=n_predictions - i))

    # Remove last actual price (we need n_predictions, not n_predictions+1)
    actual_prices = actual_prices[:-1]

    # Run backtest
    print("\n🔬 Running comprehensive backtest...")
    result = backtester.backtest_predictions(
        predictions=predictions,
        actual_prices=actual_prices,
        timestamps=timestamps,
        initial_capital=100000
    )

    print(f"\n📊 RESULTS:")
    print(f"   Total Predictions: {result.total_predictions}")
    print(f"   Correct Predictions: {result.correct_predictions}")
    print(f"   Accuracy: {result.accuracy * 100:.1f}%")
    print(f"   Win Rate: {result.win_rate * 100:.1f}%")
    print(f"   Sharpe Ratio: {result.sharpe_ratio:.2f}")
    print(f"   Sortino Ratio: {result.sortino_ratio:.2f}")
    print(f"   Max Drawdown: {result.max_drawdown * 100:.1f}%")
    print(f"   Total Return: {result.total_return * 100:.1f}%")
    print(f"   Avg Return/Trade: {result.avg_return * 100:.2f}%")

    # Out-of-sample test
    print(f"\n🔬 Running out-of-sample test...")
    oos_results = backtester.out_of_sample_test(
        predictions=predictions,
        actual_prices=actual_prices,
        timestamps=timestamps,
        train_ratio=0.7
    )

    print(f"\n📊 OUT-OF-SAMPLE RESULTS:")
    print(f"   Train Accuracy: {oos_results['train'].accuracy * 100:.1f}%")
    print(f"   Test Accuracy: {oos_results['test'].accuracy * 100:.1f}%")
    print(f"   Overfitting Gap: {oos_results['overfitting_gap'] * 100:.1f}%")

    if oos_results['overfitting_gap'] > 0.15:
        print(f"   ⚠️  Overfitting detected!")
    else:
        print(f"   ✅ Model generalizes well")

    # Generate report
    print(f"\n📋 Generating comprehensive report...")
    report = backtester.generate_backtest_report(result)

    print(f"\n🏆 Performance Grade: {report['performance_grade']}")
    print(f"\n📊 Summary:")
    for key, value in report['summary'].items():
        print(f"   {key}: {value}")

    print("\n" + "=" * 70)
    print("FRAMEWORK TEST COMPLETED")
    print("=" * 70)


if __name__ == "__main__":
    # Run both tests
    asyncio.run(test_backtesting_integration())
    asyncio.run(test_backtest_framework_directly())
