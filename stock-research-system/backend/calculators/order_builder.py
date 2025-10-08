"""
Order Builder - Conditional Order Logic
Generates executable trading orders with bracket, OCO, and trailing stop logic
CRITICAL for professional traders to execute recommendations
"""

import logging
from typing import Dict, Any, List, Optional
from enum import Enum
from datetime import datetime

logger = logging.getLogger(__name__)


class OrderType(str, Enum):
    """Order types"""
    MARKET = "market"
    LIMIT = "limit"
    STOP = "stop"
    STOP_LIMIT = "stop_limit"
    TRAILING_STOP = "trailing_stop"


class OrderSide(str, Enum):
    """Order side"""
    BUY = "buy"
    SELL = "sell"


class TimeInForce(str, Enum):
    """Time in force"""
    DAY = "day"
    GTC = "gtc"  # Good till canceled
    IOC = "ioc"  # Immediate or cancel
    FOK = "fok"  # Fill or kill


class OrderBuilder:
    """
    Builds conditional orders for trade execution

    Supports:
    - Bracket orders (entry + profit target + stop loss)
    - OCO (One-Cancels-Other) orders
    - Trailing stop orders
    - Scaling in/out strategies
    """

    def __init__(self):
        self.name = "OrderBuilder"

    def build_bracket_order(
        self,
        symbol: str,
        side: OrderSide,
        quantity: int,
        entry_price: float,
        profit_target: float,
        stop_loss: float,
        trailing_stop_pct: Optional[float] = None,
        scale_in_levels: Optional[List[float]] = None
    ) -> Dict[str, Any]:
        """
        Build a bracket order with entry, profit target, and stop loss

        Bracket order automatically creates:
        1. Entry order (buy/sell)
        2. Profit target (limit order to exit)
        3. Stop loss (stop order to cut losses)
        4. The profit and stop orders are OCO (one cancels the other)

        Args:
            symbol: Stock symbol
            side: BUY or SELL
            quantity: Number of shares
            entry_price: Entry price
            profit_target: Take profit price
            stop_loss: Stop loss price
            trailing_stop_pct: Optional trailing stop %
            scale_in_levels: Optional list of prices to scale in

        Returns:
            Complete bracket order structure
        """

        # Validate inputs
        if quantity <= 0:
            raise ValueError("Quantity must be positive")

        if side == OrderSide.BUY:
            if profit_target <= entry_price:
                raise ValueError("Profit target must be above entry for BUY")
            if stop_loss >= entry_price:
                raise ValueError("Stop loss must be below entry for BUY")
        else:  # SELL
            if profit_target >= entry_price:
                raise ValueError("Profit target must be below entry for SELL")
            if stop_loss <= entry_price:
                raise ValueError("Stop loss must be above entry for SELL")

        # Calculate risk/reward
        risk = abs(entry_price - stop_loss)
        reward = abs(profit_target - entry_price)
        risk_reward_ratio = reward / risk if risk > 0 else 0

        # Build entry order
        if scale_in_levels:
            entry_orders = self._build_scale_in_orders(
                symbol, side, quantity, entry_price, scale_in_levels
            )
        else:
            entry_orders = [{
                'order_id': self._generate_order_id('ENTRY'),
                'symbol': symbol,
                'side': side.value,
                'type': OrderType.LIMIT.value,
                'quantity': quantity,
                'limit_price': entry_price,
                'time_in_force': TimeInForce.GTC.value,
                'order_class': 'entry'
            }]

        # Build exit orders (OCO)
        exit_orders = []

        # Profit target order
        profit_order = {
            'order_id': self._generate_order_id('PROFIT'),
            'symbol': symbol,
            'side': 'sell' if side == OrderSide.BUY else 'buy',
            'type': OrderType.LIMIT.value,
            'quantity': quantity,
            'limit_price': profit_target,
            'time_in_force': TimeInForce.GTC.value,
            'order_class': 'profit_target',
            'parent_order_id': entry_orders[0]['order_id'],
            'oco_group': 'exit_1'
        }
        exit_orders.append(profit_order)

        # Stop loss order
        if trailing_stop_pct:
            # Trailing stop
            stop_order = {
                'order_id': self._generate_order_id('TRAIL_STOP'),
                'symbol': symbol,
                'side': 'sell' if side == OrderSide.BUY else 'buy',
                'type': OrderType.TRAILING_STOP.value,
                'quantity': quantity,
                'trail_percent': trailing_stop_pct,
                'time_in_force': TimeInForce.GTC.value,
                'order_class': 'trailing_stop',
                'parent_order_id': entry_orders[0]['order_id'],
                'oco_group': 'exit_1'
            }
        else:
            # Fixed stop loss
            stop_order = {
                'order_id': self._generate_order_id('STOP'),
                'symbol': symbol,
                'side': 'sell' if side == OrderSide.BUY else 'buy',
                'type': OrderType.STOP.value,
                'quantity': quantity,
                'stop_price': stop_loss,
                'time_in_force': TimeInForce.GTC.value,
                'order_class': 'stop_loss',
                'parent_order_id': entry_orders[0]['order_id'],
                'oco_group': 'exit_1'
            }
        exit_orders.append(stop_order)

        return {
            'bracket_order_id': self._generate_order_id('BRACKET'),
            'symbol': symbol,
            'strategy': 'bracket',
            'entry_orders': entry_orders,
            'exit_orders': exit_orders,
            'risk_reward_ratio': round(risk_reward_ratio, 2),
            'total_risk': round(risk * quantity, 2),
            'total_reward': round(reward * quantity, 2),
            'created_at': datetime.utcnow().isoformat(),
            'status': 'pending',
            'instructions': self._generate_order_instructions(
                symbol, side, quantity, entry_price, profit_target, stop_loss
            )
        }

    def build_oco_order(
        self,
        symbol: str,
        side: OrderSide,
        quantity: int,
        order1_type: OrderType,
        order1_price: float,
        order2_type: OrderType,
        order2_price: float
    ) -> Dict[str, Any]:
        """
        Build One-Cancels-Other (OCO) order
        When one order fills, the other is automatically canceled

        Example: Place both buy limit at $150 and buy stop at $155
        If price drops to $150, buy limit fills and buy stop cancels
        If price rises to $155, buy stop fills and buy limit cancels
        """

        oco_group_id = self._generate_order_id('OCO')

        order1 = {
            'order_id': self._generate_order_id('OCO1'),
            'symbol': symbol,
            'side': side.value,
            'type': order1_type.value,
            'quantity': quantity,
            'limit_price' if 'limit' in order1_type.value else 'stop_price': order1_price,
            'time_in_force': TimeInForce.GTC.value,
            'oco_group': oco_group_id
        }

        order2 = {
            'order_id': self._generate_order_id('OCO2'),
            'symbol': symbol,
            'side': side.value,
            'type': order2_type.value,
            'quantity': quantity,
            'limit_price' if 'limit' in order2_type.value else 'stop_price': order2_price,
            'time_in_force': TimeInForce.GTC.value,
            'oco_group': oco_group_id
        }

        return {
            'oco_order_id': oco_group_id,
            'symbol': symbol,
            'strategy': 'oco',
            'orders': [order1, order2],
            'created_at': datetime.utcnow().isoformat(),
            'status': 'pending'
        }

    def build_scaling_strategy(
        self,
        symbol: str,
        side: OrderSide,
        total_quantity: int,
        entry_price: float,
        scale_levels: List[Dict[str, float]],
        profit_target: float,
        stop_loss: float
    ) -> Dict[str, Any]:
        """
        Build scaling in/out strategy

        Example scale-in:
        - Buy 100 shares at $150 (1/3 position)
        - Buy 100 shares at $148 (1/3 position)
        - Buy 100 shares at $146 (1/3 position)

        Args:
            scale_levels: [{'price': 150, 'pct': 0.33}, {'price': 148, 'pct': 0.33}, ...]
        """

        orders = []

        for idx, level in enumerate(scale_levels):
            quantity = int(total_quantity * level['pct'])

            order = {
                'order_id': self._generate_order_id(f'SCALE_{idx}'),
                'symbol': symbol,
                'side': side.value,
                'type': OrderType.LIMIT.value,
                'quantity': quantity,
                'limit_price': level['price'],
                'time_in_force': TimeInForce.GTC.value,
                'order_class': f'scale_in_{idx + 1}'
            }
            orders.append(order)

        return {
            'scaling_order_id': self._generate_order_id('SCALE'),
            'symbol': symbol,
            'strategy': 'scaling',
            'total_quantity': total_quantity,
            'scale_orders': orders,
            'profit_target': profit_target,
            'stop_loss': stop_loss,
            'created_at': datetime.utcnow().isoformat(),
            'instructions': f"Scale into {total_quantity} shares across {len(scale_levels)} levels"
        }

    def build_trailing_stop_order(
        self,
        symbol: str,
        side: OrderSide,
        quantity: int,
        trail_percent: float,
        trail_amount: Optional[float] = None
    ) -> Dict[str, Any]:
        """
        Build trailing stop order
        Stop loss automatically adjusts as price moves in your favor

        Example: Buy at $150, set 5% trailing stop
        - If price rises to $160, stop moves to $152 (5% below)
        - If price rises to $170, stop moves to $161.50 (5% below)
        - If price falls back, stop stays at highest level
        """

        return {
            'order_id': self._generate_order_id('TRAIL'),
            'symbol': symbol,
            'side': side.value,
            'type': OrderType.TRAILING_STOP.value,
            'quantity': quantity,
            'trail_percent': trail_percent if not trail_amount else None,
            'trail_amount': trail_amount if trail_amount else None,
            'time_in_force': TimeInForce.GTC.value,
            'created_at': datetime.utcnow().isoformat(),
            'instructions': f"Trailing stop: locks in profits by trailing {trail_percent}% behind price"
        }

    def _build_scale_in_orders(
        self,
        symbol: str,
        side: OrderSide,
        total_quantity: int,
        entry_price: float,
        scale_levels: List[float]
    ) -> List[Dict]:
        """Build multiple entry orders for scaling in"""

        orders = []
        qty_per_level = int(total_quantity / len(scale_levels))

        for idx, price in enumerate(scale_levels):
            order = {
                'order_id': self._generate_order_id(f'ENTRY_{idx}'),
                'symbol': symbol,
                'side': side.value,
                'type': OrderType.LIMIT.value,
                'quantity': qty_per_level,
                'limit_price': price,
                'time_in_force': TimeInForce.GTC.value,
                'order_class': f'entry_scale_{idx + 1}'
            }
            orders.append(order)

        return orders

    def _generate_order_id(self, prefix: str) -> str:
        """Generate unique order ID"""
        timestamp = datetime.utcnow().strftime('%Y%m%d%H%M%S')
        return f"{prefix}_{timestamp}"

    def _generate_order_instructions(
        self,
        symbol: str,
        side: OrderSide,
        quantity: int,
        entry: float,
        target: float,
        stop: float
    ) -> str:
        """Generate human-readable order instructions"""

        action = "BUY" if side == OrderSide.BUY else "SELL"
        risk = abs(entry - stop)
        reward = abs(target - entry)
        rr_ratio = reward / risk if risk > 0 else 0

        instructions = f"""
BRACKET ORDER INSTRUCTIONS FOR {symbol}:

1. ENTRY: {action} {quantity} shares at ${entry:.2f} (Limit Order)

2. PROFIT TARGET:
   - Sell {quantity} shares at ${target:.2f} (Limit Order)
   - Expected profit: ${reward * quantity:,.2f}

3. STOP LOSS:
   - Sell {quantity} shares at ${stop:.2f} (Stop Order)
   - Maximum loss: ${risk * quantity:,.2f}

4. RISK/REWARD: {rr_ratio:.2f}:1

EXECUTION:
- Orders 2 and 3 are OCO (One-Cancels-Other)
- When profit target hits, stop loss cancels automatically
- When stop loss hits, profit target cancels automatically
- All orders Good-Till-Canceled (GTC)
        """.strip()

        return instructions

    def validate_order(self, order: Dict[str, Any]) -> Dict[str, Any]:
        """Validate order before submission"""

        validations = {
            'is_valid': True,
            'errors': [],
            'warnings': []
        }

        # Check required fields
        required = ['symbol', 'side', 'type', 'quantity']
        for field in required:
            if field not in order:
                validations['is_valid'] = False
                validations['errors'].append(f"Missing required field: {field}")

        # Check quantity
        if order.get('quantity', 0) <= 0:
            validations['is_valid'] = False
            validations['errors'].append("Quantity must be positive")

        # Check prices
        if order.get('type') == OrderType.LIMIT.value:
            if 'limit_price' not in order or order['limit_price'] <= 0:
                validations['is_valid'] = False
                validations['errors'].append("Limit order requires positive limit_price")

        if order.get('type') == OrderType.STOP.value:
            if 'stop_price' not in order or order['stop_price'] <= 0:
                validations['is_valid'] = False
                validations['errors'].append("Stop order requires positive stop_price")

        # Warnings for risk management
        if 'risk_reward_ratio' in order and order['risk_reward_ratio'] < 1.5:
            validations['warnings'].append(f"Poor risk/reward ratio: {order['risk_reward_ratio']:.2f}:1 (prefer >2:1)")

        return validations
