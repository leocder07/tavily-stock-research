"""
Consensus Engine Demo - Phase 4 Task 1
Demonstrates how the consensus engine resolves conflicting agent recommendations
"""

import asyncio
import logging
from typing import Dict, Any
from services.consensus_engine import ConsensusEngine

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def create_sample_analyses_scenario_1() -> Dict[str, Any]:
    """
    Scenario 1: Strong Agreement (High Confidence)
    All agents agree on BUY recommendation
    """
    return {
        'fundamental': {
            'symbol': 'AAPL',
            'recommendation': 'BUY',
            'confidence': 0.85,
            'summary': 'Strong fundamentals with P/E of 28, ROE 147%',
            'pe_ratio': 28.3,
            'roe': 147.2,
            'analyst_target_price': 250.0
        },
        'technical': {
            'signal': 'BUY',
            'confidence': 0.78,
            'analysis_summary': 'Bullish trend with RSI at 58',
            'trend': 'uptrend',
            'rsi': {'value': 58.2},
            'momentum': 'positive'
        },
        'risk': {
            'risk_level': 'low',
            'confidence': 0.72,
            'sharpe_ratio': 1.8,
            'max_drawdown': 12.5,
            'var_95': 3200
        },
        'sentiment': {
            'overall_sentiment': 'bullish',
            'confidence': 0.65,
            'sentiment_score': 78,
            'total_mentions': 15420
        },
        'news': {
            'sentiment': {
                'score': 0.6,
                'confidence': 0.70,
                'overall': 'positive'
            },
            'articles': ['article1', 'article2', 'article3']
        },
        'market': {
            'price_data': {
                'current_price': 227.50,
                'change_percent': 2.3,
                'volume': 52000000
            }
        }
    }


def create_sample_analyses_scenario_2() -> Dict[str, Any]:
    """
    Scenario 2: Conflicting Signals (Technical BUY vs Risk SELL)
    Technical and Fundamental say BUY, but Risk says SELL
    """
    return {
        'fundamental': {
            'symbol': 'TSLA',
            'recommendation': 'BUY',
            'confidence': 0.70,
            'summary': 'Growth potential high but valuation stretched',
            'pe_ratio': 68.5,
            'roe': 23.4,
            'analyst_target_price': 290.0
        },
        'technical': {
            'signal': 'BUY',
            'confidence': 0.82,
            'analysis_summary': 'Strong uptrend with positive momentum',
            'trend': 'uptrend',
            'rsi': {'value': 72.1},
            'momentum': 'strong_positive'
        },
        'risk': {
            'risk_level': 'high',
            'confidence': 0.85,
            'sharpe_ratio': 0.3,
            'max_drawdown': 45.2,
            'var_95': 12500
        },
        'sentiment': {
            'overall_sentiment': 'positive',
            'confidence': 0.55,
            'sentiment_score': 62,
            'total_mentions': 8920
        },
        'news': {
            'sentiment': {
                'score': 0.2,
                'confidence': 0.60,
                'overall': 'mixed'
            },
            'articles': ['article1', 'article2']
        },
        'market': {
            'price_data': {
                'current_price': 245.00,
                'change_percent': 5.7,
                'volume': 125000000
            }
        }
    }


def create_sample_analyses_scenario_3() -> Dict[str, Any]:
    """
    Scenario 3: Mixed Signals (No Clear Consensus)
    Agents split between BUY, HOLD, and SELL
    """
    return {
        'fundamental': {
            'symbol': 'NVDA',
            'recommendation': 'HOLD',
            'confidence': 0.60,
            'summary': 'Fair valuation with moderate growth prospects',
            'pe_ratio': 42.8,
            'roe': 89.5,
            'analyst_target_price': 485.0
        },
        'technical': {
            'signal': 'SELL',
            'confidence': 0.68,
            'analysis_summary': 'Overbought conditions with bearish divergence',
            'trend': 'downtrend',
            'rsi': {'value': 78.5},
            'momentum': 'negative'
        },
        'risk': {
            'risk_level': 'medium',
            'confidence': 0.65,
            'sharpe_ratio': 1.2,
            'max_drawdown': 22.8,
            'var_95': 8200
        },
        'sentiment': {
            'overall_sentiment': 'bullish',
            'confidence': 0.72,
            'sentiment_score': 81,
            'total_mentions': 22340
        },
        'news': {
            'sentiment': {
                'score': -0.1,
                'confidence': 0.55,
                'overall': 'neutral'
            },
            'articles': ['article1']
        },
        'market': {
            'price_data': {
                'current_price': 475.25,
                'change_percent': -1.2,
                'volume': 48000000
            }
        }
    }


def create_sample_analyses_scenario_4() -> Dict[str, Any]:
    """
    Scenario 4: Risk Override Scenario
    Strong BUY signals but terrible risk metrics should trigger downgrade
    """
    return {
        'fundamental': {
            'symbol': 'MEME',
            'recommendation': 'STRONG_BUY',
            'confidence': 0.90,
            'summary': 'Extremely bullish fundamentals',
            'pe_ratio': 8.2,
            'roe': 245.0,
            'analyst_target_price': 150.0
        },
        'technical': {
            'signal': 'BUY',
            'confidence': 0.88,
            'analysis_summary': 'Explosive uptrend',
            'trend': 'strong_uptrend',
            'rsi': {'value': 65.0},
            'momentum': 'very_positive'
        },
        'risk': {
            'risk_level': 'very_high',
            'confidence': 0.95,
            'sharpe_ratio': 0.15,
            'max_drawdown': 72.3,
            'var_95': 45000
        },
        'sentiment': {
            'overall_sentiment': 'bullish',
            'confidence': 0.80,
            'sentiment_score': 92,
            'total_mentions': 45000
        },
        'news': {
            'sentiment': {
                'score': 0.8,
                'confidence': 0.75,
                'overall': 'very_positive'
            },
            'articles': ['article1', 'article2', 'article3', 'article4']
        },
        'market': {
            'price_data': {
                'current_price': 85.00,
                'change_percent': 15.2,
                'volume': 250000000
            }
        }
    }


async def run_consensus_demo():
    """Run comprehensive consensus engine demonstration"""

    print("\n" + "=" * 100)
    print("CONSENSUS RECOMMENDATION ENGINE - DEMONSTRATION")
    print("=" * 100)

    # Initialize consensus engine
    engine = ConsensusEngine()

    # Update historical accuracy for some agents (simulate learning)
    engine.update_historical_accuracy('fundamental', 0.82)
    engine.update_historical_accuracy('technical', 0.68)
    engine.update_historical_accuracy('risk', 0.91)
    engine.update_historical_accuracy('sentiment', 0.55)
    engine.update_historical_accuracy('news', 0.73)

    # Scenario 1: Strong Agreement
    print("\n" + "=" * 100)
    print("SCENARIO 1: STRONG AGREEMENT - All agents bullish")
    print("=" * 100)

    analyses_1 = create_sample_analyses_scenario_1()
    result_1 = engine.calculate_consensus(analyses_1, risk_adjusted=True)

    print("\nCONSENSUS RESULT:")
    print(f"  Recommendation: {result_1.recommendation}")
    print(f"  Confidence: {result_1.confidence:.1%}")
    print(f"  Agreement Level: {result_1.agreement_level:.1%}")
    print(f"  Consensus Score: {result_1.consensus_score:.3f}")
    print(f"\nWeighted Votes:")
    for rec, votes in sorted(result_1.weighted_votes.items(), key=lambda x: x[1], reverse=True):
        print(f"    {rec:15s}: {votes:.3f}")
    print(f"\nReasoning: {result_1.reasoning}")
    print(f"\nDissenting Opinions: {len(result_1.dissenting_opinions)}")
    print(f"Conflicts Resolved: {len(result_1.conflicts_resolved)}")

    # Print full report
    report_1 = engine.get_consensus_report(result_1)
    print("\n" + report_1)

    # Scenario 2: Conflicting Signals
    print("\n" + "=" * 100)
    print("SCENARIO 2: CONFLICTING SIGNALS - Technical BUY vs Risk SELL")
    print("=" * 100)

    analyses_2 = create_sample_analyses_scenario_2()
    result_2 = engine.calculate_consensus(analyses_2, risk_adjusted=True)

    print("\nCONSENSUS RESULT:")
    print(f"  Recommendation: {result_2.recommendation}")
    print(f"  Confidence: {result_2.confidence:.1%}")
    print(f"  Agreement Level: {result_2.agreement_level:.1%}")
    print(f"  Consensus Score: {result_2.consensus_score:.3f}")
    print(f"\nWeighted Votes:")
    for rec, votes in sorted(result_2.weighted_votes.items(), key=lambda x: x[1], reverse=True):
        print(f"    {rec:15s}: {votes:.3f}")
    print(f"\nReasoning: {result_2.reasoning}")
    print(f"\nDissenting Opinions: {len(result_2.dissenting_opinions)}")
    if result_2.dissenting_opinions:
        print("  Dissenters:")
        for d in result_2.dissenting_opinions:
            print(f"    - {d['agent']}: {d['recommendation']} (weight: {d['weight']:.3f}, divergence: {d['divergence']:.3f})")
    print(f"\nConflicts Resolved: {len(result_2.conflicts_resolved)}")
    if result_2.conflicts_resolved:
        for conflict in result_2.conflicts_resolved:
            print(f"  - {conflict}")

    # Print full report
    report_2 = engine.get_consensus_report(result_2)
    print("\n" + report_2)

    # Scenario 3: Mixed Signals
    print("\n" + "=" * 100)
    print("SCENARIO 3: MIXED SIGNALS - No clear consensus")
    print("=" * 100)

    analyses_3 = create_sample_analyses_scenario_3()
    result_3 = engine.calculate_consensus(analyses_3, risk_adjusted=True)

    print("\nCONSENSUS RESULT:")
    print(f"  Recommendation: {result_3.recommendation}")
    print(f"  Confidence: {result_3.confidence:.1%}")
    print(f"  Agreement Level: {result_3.agreement_level:.1%}")
    print(f"  Consensus Score: {result_3.consensus_score:.3f}")
    print(f"\nWeighted Votes:")
    for rec, votes in sorted(result_3.weighted_votes.items(), key=lambda x: x[1], reverse=True):
        print(f"    {rec:15s}: {votes:.3f}")
    print(f"\nReasoning: {result_3.reasoning}")
    print(f"\nDissenting Opinions: {len(result_3.dissenting_opinions)}")
    if result_3.dissenting_opinions:
        print("  Dissenters:")
        for d in result_3.dissenting_opinions:
            print(f"    - {d['agent']}: {d['recommendation']} (weight: {d['weight']:.3f})")
    print(f"\nConflicts Resolved: {len(result_3.conflicts_resolved)}")

    # Print full report
    report_3 = engine.get_consensus_report(result_3)
    print("\n" + report_3)

    # Scenario 4: Risk Override
    print("\n" + "=" * 100)
    print("SCENARIO 4: RISK OVERRIDE - Strong BUY signals but terrible risk metrics")
    print("=" * 100)

    analyses_4 = create_sample_analyses_scenario_4()

    # First without risk adjustment
    result_4_no_risk = engine.calculate_consensus(analyses_4, risk_adjusted=False)
    print("\nWITHOUT RISK ADJUSTMENT:")
    print(f"  Recommendation: {result_4_no_risk.recommendation}")
    print(f"  Confidence: {result_4_no_risk.confidence:.1%}")
    print(f"  Agreement Level: {result_4_no_risk.agreement_level:.1%}")

    # Then with risk adjustment
    result_4_with_risk = engine.calculate_consensus(analyses_4, risk_adjusted=True)
    print("\nWITH RISK ADJUSTMENT:")
    print(f"  Recommendation: {result_4_with_risk.recommendation}")
    print(f"  Confidence: {result_4_with_risk.confidence:.1%}")
    print(f"  Agreement Level: {result_4_with_risk.agreement_level:.1%}")

    print(f"\nRISK OVERRIDE APPLIED: {result_4_no_risk.recommendation} -> {result_4_with_risk.recommendation}")
    print(f"Reason: Sharpe ratio 0.15 and VERY_HIGH risk level triggered downgrade")

    # Print full report
    report_4 = engine.get_consensus_report(result_4_with_risk)
    print("\n" + report_4)

    # Summary comparison
    print("\n" + "=" * 100)
    print("SUMMARY COMPARISON")
    print("=" * 100)

    scenarios = [
        ("Strong Agreement", result_1),
        ("Conflicting Signals", result_2),
        ("Mixed Signals", result_3),
        ("Risk Override", result_4_with_risk)
    ]

    print(f"\n{'Scenario':<25} {'Recommendation':<15} {'Confidence':<12} {'Agreement':<12} {'Conflicts'}")
    print("-" * 100)

    for name, result in scenarios:
        print(
            f"{name:<25} {result.recommendation:<15} {result.confidence:>10.1%} "
            f"{result.agreement_level:>11.1%} {len(result.conflicts_resolved):>10}"
        )

    print("\n" + "=" * 100)
    print("DEMO COMPLETE")
    print("=" * 100)


if __name__ == "__main__":
    asyncio.run(run_consensus_demo())
