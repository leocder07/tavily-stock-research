"""
Value Extractors
Utility functions to safely extract numeric values from various formats
"""

import logging
from typing import Any, Optional, Union

logger = logging.getLogger(__name__)


def extract_numeric_value(
    data: Any,
    field_name: str = "value",
    default: float = 0.0
) -> float:
    """
    Extract numeric value from metadata dict or direct number

    Handles formats:
    - Direct number: 150.0
    - Metadata dict: {"value": 150.0, "unit": "USD", "formatted": "$150"}
    - String number: "150.0"
    - None/invalid: returns default

    Args:
        data: Input data to extract from
        field_name: Name of field for logging
        default: Default value if extraction fails

    Returns:
        Extracted float value or default
    """
    if data is None:
        return default

    # Already a number
    if isinstance(data, (int, float)):
        return float(data)

    # Metadata dict format
    if isinstance(data, dict):
        if 'value' in data:
            value = data['value']
            if isinstance(value, (int, float)):
                return float(value)
            elif isinstance(value, str):
                try:
                    return float(value.replace(',', '').replace('$', '').replace('%', ''))
                except ValueError:
                    logger.warning(f"Could not parse {field_name} value from dict: {value}")
                    return default

        # Try other common keys
        for key in ['price', 'amount', 'total', 'number', 'val']:
            if key in data and isinstance(data[key], (int, float)):
                return float(data[key])

    # String number
    if isinstance(data, str):
        try:
            # Remove common formatting characters
            cleaned = data.replace(',', '').replace('$', '').replace('%', '').strip()
            return float(cleaned)
        except ValueError:
            logger.warning(f"Could not parse {field_name} string: {data}")
            return default

    logger.warning(f"Unexpected type for {field_name}: {type(data)}")
    return default


def extract_price_value(
    price_data: Any,
    field_name: str = "price",
    default: Optional[float] = None
) -> Optional[float]:
    """
    Extract price value, returning None if invalid (for required prices)

    Args:
        price_data: Input price data
        field_name: Name of field for logging
        default: Default value (None means required)

    Returns:
        Extracted price or default/None
    """
    value = extract_numeric_value(price_data, field_name, default=0.0 if default is None else default)

    # Validate price is positive
    if value <= 0:
        if default is None:
            logger.error(f"Invalid {field_name}: {value} (must be positive)")
            return None
        return default

    return value


def safe_divide(
    numerator: Union[float, Any],
    denominator: Union[float, Any],
    field_name: str = "ratio",
    default: Optional[float] = None
) -> Optional[float]:
    """
    Safely divide two values that might be dicts or numbers

    Args:
        numerator: Top value (may be dict or number)
        denominator: Bottom value (may be dict or number)
        field_name: Name of calculation for logging
        default: Default value if division fails

    Returns:
        Division result or default/None
    """
    num_val = extract_numeric_value(numerator, f"{field_name}_numerator", 0.0)
    denom_val = extract_numeric_value(denominator, f"{field_name}_denominator", 0.0)

    if denom_val == 0:
        logger.warning(f"Division by zero in {field_name} calculation")
        return default

    return num_val / denom_val


def safe_subtract(
    value1: Union[float, Any],
    value2: Union[float, Any],
    field_name: str = "difference",
    default: float = 0.0
) -> float:
    """
    Safely subtract two values that might be dicts or numbers

    Args:
        value1: First value (may be dict or number)
        value2: Second value (may be dict or number)
        field_name: Name of calculation for logging
        default: Default value if subtraction fails

    Returns:
        Subtraction result or default
    """
    val1 = extract_numeric_value(value1, f"{field_name}_value1", 0.0)
    val2 = extract_numeric_value(value2, f"{field_name}_value2", 0.0)

    return val1 - val2


def calculate_risk_reward_ratio(
    entry_price: Union[float, Any],
    target_price: Union[float, Any],
    stop_loss: Union[float, Any],
    field_prefix: str = "position"
) -> Optional[float]:
    """
    Calculate risk/reward ratio with comprehensive validation

    Formula: (Target - Entry) / (Entry - Stop Loss)

    Args:
        entry_price: Entry price (may be dict or number)
        target_price: Target price (may be dict or number)
        stop_loss: Stop loss price (may be dict or number)
        field_prefix: Prefix for logging

    Returns:
        Risk/reward ratio or None if invalid
    """
    # Extract values
    entry = extract_price_value(entry_price, f"{field_prefix}_entry_price")
    target = extract_price_value(target_price, f"{field_prefix}_target_price")
    stop = extract_price_value(stop_loss, f"{field_prefix}_stop_loss")

    # Validate all prices exist and are valid
    if entry is None or target is None or stop is None:
        logger.error(
            f"Invalid prices for R/R calculation: "
            f"entry={entry}, target={target}, stop={stop}"
        )
        return None

    # Validate price logic
    if stop >= entry:
        logger.error(
            f"Invalid R/R setup: stop loss ({stop}) must be below entry ({entry})"
        )
        return None

    if target <= entry:
        logger.error(
            f"Invalid R/R setup: target ({target}) must be above entry ({entry})"
        )
        return None

    # Calculate R/R
    potential_gain = target - entry
    potential_loss = entry - stop

    if potential_loss <= 0:
        logger.error(f"Invalid risk calculation: potential_loss={potential_loss}")
        return None

    risk_reward_ratio = potential_gain / potential_loss

    logger.info(
        f"R/R calculated: {risk_reward_ratio:.2f}:1 "
        f"(gain: ${potential_gain:.2f}, loss: ${potential_loss:.2f})"
    )

    return round(risk_reward_ratio, 2)
