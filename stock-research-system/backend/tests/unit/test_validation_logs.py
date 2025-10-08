"""
Test synthesis validation to ensure it logs warnings/errors correctly
"""

import sys
import logging

# Setup logging to capture validation messages
logging.basicConfig(
    level=logging.INFO,
    format='%(levelname)s:%(name)s:%(message)s'
)

from validators.synthesis_validator import SynthesisValidator

def test_validation():
    """Test synthesis validation with various scenarios"""

    print("\n" + "="*80)
    print("SYNTHESIS VALIDATION TEST")
    print("="*80)

    validator = SynthesisValidator()

    # Test Case 1: Good synthesis (should pass)
    print("\n[TEST 1] Valid synthesis (AAPL, ATR-based stop loss)")
    print("-" * 80)

    good_synthesis = {
        'symbol': 'AAPL',
        'action': 'BUY',
        'confidence': 0.7,
        'target_price': 280.0,
        'stop_loss': 214.0,  # Correct ATR-based stop
        'entry_price': 257.0,
        'risk_reward_ratio': 2.3,
        'pe_ratio': 39.2,
        'roe': 4.3,
        'sharpe_ratio': 1.2,
        'max_drawdown': 15
    }

    result1 = validator.validate(good_synthesis, current_price=257.0)

    print(f"Valid: {result1.is_valid}")
    print(f"Errors: {len(result1.errors)}")
    if result1.errors:
        for err in result1.errors:
            print(f"  - {err}")

    print(f"Warnings: {len(result1.warnings)}")
    if result1.warnings:
        for warn in result1.warnings:
            print(f"  - {warn}")

    if result1.is_valid and len(result1.errors) == 0:
        print("✅ TEST 1 PASSED: Valid synthesis accepted")
        test1_passed = True
    else:
        print("❌ TEST 1 FAILED: Valid synthesis rejected")
        test1_passed = False

    # Test Case 2: Wrong stop loss (should fail/warn)
    print("\n[TEST 2] WRONG stop loss ($2,739 - the old bug)")
    print("-" * 80)

    bad_synthesis = good_synthesis.copy()
    bad_synthesis['stop_loss'] = 2739.0  # Wrong value!

    result2 = validator.validate(bad_synthesis, current_price=257.0)

    print(f"Valid: {result2.is_valid}")
    print(f"Errors: {len(result2.errors)}")
    if result2.errors:
        for err in result2.errors:
            print(f"  - {err}")

    print(f"Warnings: {len(result2.warnings)}")
    if result2.warnings:
        for warn in result2.warnings:
            print(f"  - {warn}")

    if len(result2.errors) > 0 or len(result2.warnings) > 0:
        print("✅ TEST 2 PASSED: Wrong stop loss detected")
        test2_passed = True
    else:
        print("❌ TEST 2 FAILED: Wrong stop loss NOT detected!")
        test2_passed = False

    # Test Case 3: Stop loss as percentage (< 1)
    print("\n[TEST 3] Stop loss as percentage (0.05 instead of price)")
    print("-" * 80)

    pct_synthesis = good_synthesis.copy()
    pct_synthesis['stop_loss'] = 0.05  # Percentage, not price!

    result3 = validator.validate(pct_synthesis, current_price=257.0)

    print(f"Valid: {result3.is_valid}")
    print(f"Errors: {len(result3.errors)}")
    if result3.errors:
        for err in result3.errors:
            print(f"  - {err}")

    print(f"Corrections: {len(result3.corrected_values)}")
    if result3.corrected_values:
        for key, val in result3.corrected_values.items():
            print(f"  - {key}: {val}")

    if len(result3.errors) > 0 and 'stop_loss' in result3.corrected_values:
        print("✅ TEST 3 PASSED: Percentage stop loss detected and corrected")
        test3_passed = True
    else:
        print("❌ TEST 3 FAILED: Percentage stop loss not corrected")
        test3_passed = False

    # Test Case 4: BUY with target below current price (inconsistent)
    print("\n[TEST 4] BUY recommendation but target < current (inconsistent)")
    print("-" * 80)

    inconsistent_synthesis = good_synthesis.copy()
    inconsistent_synthesis['action'] = 'BUY'
    inconsistent_synthesis['target_price'] = 240.0  # Below current!

    result4 = validator.validate(inconsistent_synthesis, current_price=257.0)

    print(f"Valid: {result4.is_valid}")
    print(f"Errors: {len(result4.errors)}")
    if result4.errors:
        for err in result4.errors:
            print(f"  - {err}")

    if len(result4.errors) > 0:
        print("✅ TEST 4 PASSED: Inconsistent BUY/target detected")
        test4_passed = True
    else:
        print("❌ TEST 4 FAILED: Inconsistent BUY/target not detected")
        test4_passed = False

    # Summary
    print("\n" + "="*80)
    print("SUMMARY")
    print("="*80)

    tests_passed = sum([test1_passed, test2_passed, test3_passed, test4_passed])
    tests_total = 4

    if test1_passed:
        print("✅ TEST 1 PASSED: Valid synthesis accepted")
    else:
        print("❌ TEST 1 FAILED: Valid synthesis rejected")

    if test2_passed:
        print("✅ TEST 2 PASSED: Wrong stop loss detected")
    else:
        print("❌ TEST 2 FAILED: Wrong stop loss not detected")

    if test3_passed:
        print("✅ TEST 3 PASSED: Percentage stop loss corrected")
    else:
        print("❌ TEST 3 FAILED: Percentage stop loss not corrected")

    if test4_passed:
        print("✅ TEST 4 PASSED: Inconsistent recommendation detected")
    else:
        print("❌ TEST 4 FAILED: Inconsistent recommendation not detected")

    print(f"\nFINAL RESULT: {tests_passed}/{tests_total} tests passed")

    if tests_passed == tests_total:
        print("\n✅ ALL TESTS PASSED - Validation is WORKING")
        print("="*80 + "\n")
        return True
    else:
        print(f"\n⚠️  {tests_total - tests_passed} TEST(S) FAILED - Validation needs review")
        print("="*80 + "\n")
        return False


if __name__ == "__main__":
    success = test_validation()
    sys.exit(0 if success else 1)
