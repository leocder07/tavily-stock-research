"""
Test Data Quality Validation Framework
Tests timestamp freshness, source reliability, anomaly detection
"""

from datetime import datetime, timedelta
from calculators.data_quality_validator import DataQualityValidator


def test_timestamp_freshness():
    """Test timestamp freshness validation"""

    print("=" * 70)
    print("TIMESTAMP FRESHNESS TEST")
    print("=" * 70)

    validator = DataQualityValidator()

    # Test 1: Fresh data (1 hour old)
    fresh_data = {
        'symbol': 'AAPL',
        'price': 258.02,
        'timestamp': (datetime.utcnow() - timedelta(hours=1)).isoformat(),
        'source': 'yfinance'
    }

    report = validator.validate_data_quality(fresh_data, 'price', 'intraday')
    print(f"\n✅ Fresh Data (1 hour old):")
    print(f"   Overall Score: {report.overall_score:.1f}/100")
    print(f"   Grade: {report.quality_grade}")
    print(f"   Freshness Score: {report.freshness_score:.1f}")
    print(f"   Issues: {report.issues if report.issues else 'None'}")
    print(f"   Warnings: {report.warnings if report.warnings else 'None'}")

    # Test 2: Stale data (2 days old)
    stale_data = {
        'symbol': 'AAPL',
        'price': 250.00,
        'timestamp': (datetime.utcnow() - timedelta(days=2)).isoformat(),
        'source': 'yfinance'
    }

    report = validator.validate_data_quality(stale_data, 'price', 'intraday')
    print(f"\n❌ Stale Data (2 days old):")
    print(f"   Overall Score: {report.overall_score:.1f}/100")
    print(f"   Grade: {report.quality_grade}")
    print(f"   Freshness Score: {report.freshness_score:.1f}")
    print(f"   Issues: {report.issues}")

    # Test 3: Missing timestamp
    no_timestamp = {
        'symbol': 'AAPL',
        'price': 258.02,
        'source': 'yfinance'
    }

    report = validator.validate_data_quality(no_timestamp, 'price', 'intraday')
    print(f"\n⚠️  No Timestamp:")
    print(f"   Overall Score: {report.overall_score:.1f}/100")
    print(f"   Grade: {report.quality_grade}")
    print(f"   Issues: {report.issues}")


def test_source_reliability():
    """Test source reliability scoring"""

    print("\n" + "=" * 70)
    print("SOURCE RELIABILITY TEST")
    print("=" * 70)

    validator = DataQualityValidator()

    sources = [
        ('yfinance', 'High reliability financial data'),
        ('tavily', 'Medium reliability news data'),
        ('user_input', 'Low reliability manual input'),
        ('unknown', 'Unknown source')
    ]

    for source, description in sources:
        data = {
            'symbol': 'AAPL',
            'price': 258.02,
            'timestamp': datetime.utcnow().isoformat(),
            'source': source
        }

        report = validator.validate_data_quality(data)
        reliability_rating = validator.source_reliability.get(source, 0)

        print(f"\n📊 {source.upper()} ({description}):")
        print(f"   Reliability Rating: {reliability_rating}/10")
        print(f"   Reliability Score: {report.reliability_score:.1f}/100")
        print(f"   Overall Grade: {report.quality_grade}")


def test_anomaly_detection():
    """Test anomaly detection"""

    print("\n" + "=" * 70)
    print("ANOMALY DETECTION TEST")
    print("=" * 70)

    validator = DataQualityValidator()

    # Test 1: Normal data
    normal_data = {
        'symbol': 'AAPL',
        'price': 258.02,
        'volume': 50000000,
        'pe_ratio': 35.5,
        'timestamp': datetime.utcnow().isoformat(),
        'source': 'yfinance'
    }

    report = validator.validate_data_quality(normal_data, 'price')
    print(f"\n✅ Normal Data:")
    print(f"   Anomaly Score: {report.anomaly_score:.1f}/100")
    print(f"   Overall Grade: {report.quality_grade}")
    print(f"   Issues: {report.issues if report.issues else 'None'}")

    # Test 2: Negative price (anomaly)
    anomaly_price = {
        'symbol': 'TEST',
        'price': -10.50,
        'timestamp': datetime.utcnow().isoformat(),
        'source': 'yfinance'
    }

    report = validator.validate_data_quality(anomaly_price, 'price')
    print(f"\n❌ Negative Price Anomaly:")
    print(f"   Anomaly Score: {report.anomaly_score:.1f}/100")
    print(f"   Overall Grade: {report.quality_grade}")
    print(f"   Issues: {report.issues}")

    # Test 3: Extreme P/E ratio
    extreme_pe = {
        'symbol': 'TEST',
        'price': 100,
        'pe_ratio': 750,  # Extremely high
        'timestamp': datetime.utcnow().isoformat(),
        'source': 'yfinance'
    }

    report = validator.validate_data_quality(extreme_pe, 'fundamental')
    print(f"\n⚠️  Extreme P/E Ratio:")
    print(f"   Anomaly Score: {report.anomaly_score:.1f}/100")
    print(f"   Overall Grade: {report.quality_grade}")
    print(f"   Warnings: {report.warnings}")

    # Test 4: RSI out of range
    invalid_rsi = {
        'symbol': 'TEST',
        'rsi': 150,  # Should be 0-100
        'timestamp': datetime.utcnow().isoformat(),
        'source': 'internal_calculation'
    }

    report = validator.validate_data_quality(invalid_rsi, 'technical')
    print(f"\n❌ RSI Out of Range:")
    print(f"   Anomaly Score: {report.anomaly_score:.1f}/100")
    print(f"   Overall Grade: {report.quality_grade}")
    print(f"   Issues: {report.issues}")


def test_data_completeness():
    """Test data completeness validation"""

    print("\n" + "=" * 70)
    print("DATA COMPLETENESS TEST")
    print("=" * 70)

    validator = DataQualityValidator()

    # Test 1: Complete price data
    complete_data = {
        'symbol': 'AAPL',
        'price': 258.02,
        'volume': 50000000,
        'timestamp': datetime.utcnow().isoformat(),
        'source': 'yfinance'
    }

    report = validator.validate_data_quality(complete_data, 'price')
    print(f"\n✅ Complete Price Data:")
    print(f"   Completeness Score: {report.completeness_score:.1f}/100")
    print(f"   Overall Grade: {report.quality_grade}")

    # Test 2: Incomplete price data
    incomplete_data = {
        'symbol': 'AAPL',
        # Missing: price, volume, timestamp
        'source': 'yfinance'
    }

    report = validator.validate_data_quality(incomplete_data, 'price')
    print(f"\n❌ Incomplete Price Data:")
    print(f"   Completeness Score: {report.completeness_score:.1f}/100")
    print(f"   Overall Grade: {report.quality_grade}")
    print(f"   Issues: {report.issues}")

    # Test 3: Fundamental data with None values
    none_values = {
        'symbol': 'AAPL',
        'pe_ratio': None,
        'market_cap': 3000000000000,
        'revenue': None,
        'timestamp': datetime.utcnow().isoformat(),
        'source': 'yfinance'
    }

    report = validator.validate_data_quality(none_values, 'fundamental')
    print(f"\n⚠️  Data with None Values:")
    print(f"   Completeness Score: {report.completeness_score:.1f}/100")
    print(f"   Overall Grade: {report.quality_grade}")


def test_time_series_validation():
    """Test time series gap detection"""

    print("\n" + "=" * 70)
    print("TIME SERIES VALIDATION TEST")
    print("=" * 70)

    validator = DataQualityValidator()

    # Test 1: No gaps
    timestamps = [
        datetime(2025, 10, 1, 9, 0),
        datetime(2025, 10, 2, 9, 0),
        datetime(2025, 10, 3, 9, 0),
        datetime(2025, 10, 4, 9, 0),
        datetime(2025, 10, 5, 9, 0)
    ]
    values = [250, 252, 255, 253, 258]

    result = validator.validate_time_series(timestamps, values, 'daily')
    print(f"\n✅ Continuous Time Series (No Gaps):")
    print(f"   Has Gaps: {result['has_gaps']}")
    print(f"   Gap Count: {result['gap_count']}")
    print(f"   Issues: {result['issues'] if result['issues'] else 'None'}")

    # Test 2: With gaps
    timestamps_with_gaps = [
        datetime(2025, 10, 1, 9, 0),
        datetime(2025, 10, 2, 9, 0),
        datetime(2025, 10, 5, 9, 0),  # Gap: missing Oct 3-4
        datetime(2025, 10, 10, 9, 0),  # Gap: missing Oct 6-9
    ]
    values_with_gaps = [250, 252, 258, 260]

    result = validator.validate_time_series(timestamps_with_gaps, values_with_gaps, 'daily')
    print(f"\n⚠️  Time Series with Gaps:")
    print(f"   Has Gaps: {result['has_gaps']}")
    print(f"   Gap Count: {result['gap_count']}")
    print(f"   Warnings: {result['warnings']}")
    if result['gaps']:
        print(f"\n   Gap Details:")
        for gap in result['gaps']:
            print(f"      {gap['start']} to {gap['end']} ({gap['duration_hours']:.1f} hours)")


def test_cross_validation():
    """Test cross-source validation"""

    print("\n" + "=" * 70)
    print("CROSS-SOURCE VALIDATION TEST")
    print("=" * 70)

    validator = DataQualityValidator()

    # Test 1: Agreement between sources
    sources = [
        {'price': 258.00, 'source': 'yfinance'},
        {'price': 258.50, 'source': 'alpha_vantage'},
        {'price': 257.80, 'source': 'finnhub'}
    ]

    result = validator.cross_validate_sources(sources, 'price')
    print(f"\n✅ High Agreement Between Sources:")
    print(f"   Consensus Value: ${result['consensus_value']:.2f}")
    print(f"   Variance: ${result['variance']:.2f}")
    print(f"   Agreement: {result['agreement']:.1f}%")
    print(f"   Sources: {result['sources_count']}")
    print(f"   Outliers: {len(result['outliers'])}")

    # Test 2: Outlier detection
    sources_with_outlier = [
        {'price': 258.00, 'source': 'yfinance'},
        {'price': 258.50, 'source': 'alpha_vantage'},
        {'price': 300.00, 'source': 'unknown'}  # Outlier
    ]

    result = validator.cross_validate_sources(sources_with_outlier, 'price')
    print(f"\n⚠️  Sources with Outlier:")
    print(f"   Consensus Value: ${result['consensus_value']:.2f}")
    print(f"   Variance: ${result['variance']:.2f}")
    print(f"   Agreement: {result['agreement']:.1f}%")
    print(f"   Outliers: {len(result['outliers'])}")
    if result['outliers']:
        for outlier in result['outliers']:
            print(f"      {outlier['source']}: ${outlier['value']} ({outlier['deviation']:+.1f}% deviation)")


def test_comprehensive_validation():
    """Test complete data quality validation"""

    print("\n" + "=" * 70)
    print("COMPREHENSIVE DATA QUALITY TEST")
    print("=" * 70)

    validator = DataQualityValidator()

    # High quality data
    high_quality = {
        'symbol': 'AAPL',
        'price': 258.02,
        'volume': 50000000,
        'pe_ratio': 35.5,
        'market_cap': 3000000000000,
        'timestamp': datetime.utcnow().isoformat(),
        'source': 'yfinance'
    }

    report = validator.validate_data_quality(high_quality, 'price', 'intraday')
    print(f"\n🏆 HIGH QUALITY DATA:")
    print(f"   Overall Score: {report.overall_score:.1f}/100")
    print(f"   Grade: {report.quality_grade}")
    print(f"   Freshness: {report.freshness_score:.1f}/100")
    print(f"   Reliability: {report.reliability_score:.1f}/100")
    print(f"   Completeness: {report.completeness_score:.1f}/100")
    print(f"   Anomaly Score: {report.anomaly_score:.1f}/100")

    # Low quality data
    low_quality = {
        'symbol': 'TEST',
        'price': -50,  # Anomaly
        'timestamp': (datetime.utcnow() - timedelta(days=10)).isoformat(),  # Stale
        'source': 'unknown'  # Low reliability
        # Missing volume
    }

    report = validator.validate_data_quality(low_quality, 'price', 'intraday')
    print(f"\n❌ LOW QUALITY DATA:")
    print(f"   Overall Score: {report.overall_score:.1f}/100")
    print(f"   Grade: {report.quality_grade}")
    print(f"   Freshness: {report.freshness_score:.1f}/100")
    print(f"   Reliability: {report.reliability_score:.1f}/100")
    print(f"   Completeness: {report.completeness_score:.1f}/100")
    print(f"   Anomaly Score: {report.anomaly_score:.1f}/100")
    print(f"\n   Issues:")
    for issue in report.issues:
        print(f"      - {issue}")
    if report.warnings:
        print(f"\n   Warnings:")
        for warning in report.warnings:
            print(f"      - {warning}")


if __name__ == "__main__":
    test_timestamp_freshness()
    test_source_reliability()
    test_anomaly_detection()
    test_data_completeness()
    test_time_series_validation()
    test_cross_validation()
    test_comprehensive_validation()

    print("\n" + "=" * 70)
    print("ALL TESTS COMPLETED")
    print("=" * 70)
