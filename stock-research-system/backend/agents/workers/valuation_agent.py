"""
Valuation Agent - Advanced price target and valuation analysis
Implements DCF modeling, comparative valuation, and price targets
"""

import asyncio
from typing import Dict, Any, List, Optional
import numpy as np
import logging
import yfinance as yf
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)


class ValuationAgent:
    """Advanced valuation agent for price target calculations"""

    def __init__(self):
        self.name = "ValuationAgent"
        self.risk_free_rate = 0.045  # Current 10-year Treasury yield
        self.market_risk_premium = 0.08  # Historical equity risk premium

    async def execute(self, symbol: str, market_data: Dict[str, Any]) -> Dict[str, Any]:
        """Execute comprehensive valuation analysis"""
        try:
            logger.info(f"Starting valuation analysis for {symbol}")

            # Fetch financial data
            ticker = yf.Ticker(symbol)
            info = ticker.info
            financials = ticker.financials
            balance_sheet = ticker.balance_sheet
            cash_flow = ticker.cashflow

            # Calculate various valuation metrics
            dcf_valuation = await self._calculate_dcf(ticker, info)
            comparative_valuation = await self._calculate_comparative_valuation(symbol, info)
            analyst_targets = await self._get_analyst_targets(ticker, info)
            technical_targets = await self._calculate_technical_targets(market_data)

            # Calculate weighted price target
            price_target = self._calculate_weighted_target(
                dcf_valuation,
                comparative_valuation,
                analyst_targets,
                technical_targets,
                info.get('currentPrice', 0)
            )

            return {
                "symbol": symbol,
                "current_price": info.get('currentPrice', 0),
                "dcf_valuation": dcf_valuation,
                "comparative_valuation": comparative_valuation,
                "analyst_targets": analyst_targets,
                "technical_targets": technical_targets,
                "price_target": price_target,
                "valuation_summary": self._generate_valuation_summary(
                    price_target,
                    info.get('currentPrice', 0)
                )
            }

        except Exception as e:
            logger.error(f"Valuation analysis failed: {e}")
            return {"error": str(e)}

    async def _calculate_dcf(self, ticker, info: Dict) -> Dict[str, Any]:
        """Calculate Discounted Cash Flow valuation"""
        try:
            # Get free cash flow data
            cash_flow = ticker.cashflow
            if cash_flow.empty:
                return {"error": "No cash flow data available"}

            # Get latest free cash flow (in millions)
            if 'Free Cash Flow' in cash_flow.index:
                fcf = cash_flow.loc['Free Cash Flow'].iloc[0]
            else:
                # Calculate FCF = Operating Cash Flow - CapEx
                operating_cf = cash_flow.loc['Total Cash From Operating Activities'].iloc[0]
                capex = abs(cash_flow.loc['Capital Expenditures'].iloc[0])
                fcf = operating_cf - capex

            # Growth assumptions - more realistic for NVDA and tech companies
            # Adjust based on company's historical growth
            revenue_growth = info.get('revenueGrowth', 0.20)
            growth_rate_1_5 = min(0.25, max(0.10, revenue_growth))  # Cap between 10-25%
            growth_rate_6_10 = growth_rate_1_5 * 0.6  # Decay to 60% of initial rate
            terminal_growth = 0.03  # 3% perpetual growth

            # Calculate WACC (Weighted Average Cost of Capital) - More accurate
            beta = info.get('beta', 1.2)  # Default to slight higher for tech
            beta = min(2.0, max(0.5, beta))  # Cap beta between 0.5 and 2.0

            # Cost of equity using CAPM
            cost_of_equity = self.risk_free_rate + beta * self.market_risk_premium

            # Get debt information for proper WACC
            market_cap = info.get('marketCap', 0)
            total_debt = info.get('totalDebt', 0)
            cash = info.get('totalCash', 0)
            net_debt = max(0, total_debt - cash)  # Net debt can't be negative for WACC

            # Calculate weights
            enterprise_value_for_wacc = market_cap + net_debt
            if enterprise_value_for_wacc > 0:
                weight_equity = market_cap / enterprise_value_for_wacc
                weight_debt = net_debt / enterprise_value_for_wacc
            else:
                weight_equity = 1.0
                weight_debt = 0.0

            # Cost of debt (approximate)
            if total_debt > 0:
                # Try to get interest expense for more accurate cost of debt
                try:
                    income = ticker.financials
                    if 'Interest Expense' in income.index:
                        interest_expense = abs(income.loc['Interest Expense'].iloc[0])
                        cost_of_debt = interest_expense / total_debt
                    else:
                        cost_of_debt = 0.03  # Default 3% cost of debt
                except:
                    cost_of_debt = 0.03
            else:
                cost_of_debt = 0.03

            # Tax rate
            tax_rate = info.get('taxRate', 0.21) if info.get('taxRate') else 0.21  # Default 21% US corporate tax

            # Calculate WACC
            wacc = (weight_equity * cost_of_equity) + (weight_debt * cost_of_debt * (1 - tax_rate))
            wacc = min(0.15, max(0.06, wacc))  # Cap WACC between 6% and 15% for reasonableness

            # Project cash flows for 10 years
            projected_fcf = []
            current_fcf = fcf

            # Years 1-5
            for year in range(1, 6):
                current_fcf = current_fcf * (1 + growth_rate_1_5)
                projected_fcf.append(current_fcf)

            # Years 6-10
            for year in range(6, 11):
                current_fcf = current_fcf * (1 + growth_rate_6_10)
                projected_fcf.append(current_fcf)

            # Calculate present value of projected cash flows
            pv_fcf = sum([cf / ((1 + wacc) ** (i + 1))
                         for i, cf in enumerate(projected_fcf)])

            # Calculate terminal value
            terminal_fcf = projected_fcf[-1] * (1 + terminal_growth)
            terminal_value = terminal_fcf / (wacc - terminal_growth)
            pv_terminal = terminal_value / ((1 + wacc) ** 10)

            # Enterprise value
            enterprise_value = pv_fcf + pv_terminal

            # Calculate equity value
            cash = info.get('totalCash', 0)
            debt = info.get('totalDebt', 0)
            equity_value = enterprise_value + cash - debt

            # Calculate price per share
            shares_outstanding = info.get('sharesOutstanding', 1)
            dcf_price = equity_value / shares_outstanding

            return {
                "dcf_price": round(dcf_price, 2),
                "enterprise_value": round(enterprise_value / 1e9, 2),  # In billions
                "wacc": round(wacc * 100, 2),  # As percentage
                "terminal_growth_rate": terminal_growth * 100,
                "confidence": 0.7  # DCF has moderate confidence
            }

        except Exception as e:
            logger.error(f"DCF calculation failed: {e}")
            return {"error": str(e), "dcf_price": 0}

    async def _calculate_comparative_valuation(self, symbol: str, info: Dict) -> Dict[str, Any]:
        """Calculate valuation based on peer multiples"""
        try:
            current_price = info.get('currentPrice', 0)

            # Get key multiples
            pe_ratio = info.get('trailingPE', 0)
            forward_pe = info.get('forwardPE', 0)
            price_to_book = info.get('priceToBook', 0)
            price_to_sales = info.get('priceToSalesTrailing12Months', 0)
            peg_ratio = info.get('pegRatio', 0)

            # Industry averages - these should be dynamic based on sector
            # For semiconductors (NVDA's industry), use more appropriate multiples
            sector = info.get('sector', 'Technology')

            # Set industry averages based on sector
            if 'Semiconductor' in str(info.get('industry', '')) or symbol in ['NVDA', 'AMD', 'INTC']:
                # Semiconductor industry averages (as of 2024)
                industry_pe = 35  # Higher due to growth expectations
                industry_pb = 8   # Higher for asset-light tech companies
                industry_ps = 7   # Higher for high-margin semiconductors
            elif sector == 'Technology':
                # General tech sector averages
                industry_pe = 28
                industry_pb = 5
                industry_ps = 6
            else:
                # Default market averages
                industry_pe = 20
                industry_pb = 3
                industry_ps = 2

            # Calculate implied prices based on industry multiples
            implied_prices = []

            if pe_ratio > 0:
                eps = current_price / pe_ratio
                implied_pe_price = eps * industry_pe
                implied_prices.append(implied_pe_price)

            if price_to_book > 0:
                book_value = current_price / price_to_book
                implied_pb_price = book_value * industry_pb
                implied_prices.append(implied_pb_price)

            if price_to_sales > 0:
                sales_per_share = current_price / price_to_sales
                implied_ps_price = sales_per_share * industry_ps
                implied_prices.append(implied_ps_price)

            # Calculate average implied price
            if implied_prices:
                comparative_price = np.mean(implied_prices)
            else:
                comparative_price = current_price

            return {
                "comparative_price": round(comparative_price, 2),
                "pe_ratio": round(pe_ratio, 2) if pe_ratio else "N/A",
                "forward_pe": round(forward_pe, 2) if forward_pe else "N/A",
                "price_to_book": round(price_to_book, 2) if price_to_book else "N/A",
                "price_to_sales": round(price_to_sales, 2) if price_to_sales else "N/A",
                "peg_ratio": round(peg_ratio, 2) if peg_ratio else "N/A",
                "valuation_rating": self._get_valuation_rating(pe_ratio, peg_ratio)
            }

        except Exception as e:
            logger.error(f"Comparative valuation failed: {e}")
            return {"error": str(e), "comparative_price": 0}

    async def _get_analyst_targets(self, ticker, info: Dict) -> Dict[str, Any]:
        """Get analyst price targets and recommendations"""
        try:
            current_price = info.get('currentPrice', 0)

            # Get analyst recommendations
            recommendations = ticker.recommendations
            rec_counts = {}
            consensus = "Hold"  # Default

            if recommendations is not None and not recommendations.empty:
                try:
                    recent_recs = recommendations.tail(10)

                    # Try different column names that might exist
                    grade_column = None
                    for col in ['To Grade', 'ToGrade', 'Grade', 'Action', 'Recommendation']:
                        if col in recent_recs.columns:
                            grade_column = col
                            break

                    if grade_column:
                        # Count recommendation types
                        rec_counts = recent_recs[grade_column].value_counts().to_dict()

                        # Calculate consensus - be more flexible with grade names
                        buy_terms = ['Buy', 'Strong Buy', 'Overweight', 'Outperform', 'Positive', 'Add', 'Accumulate']
                        hold_terms = ['Hold', 'Equal-Weight', 'Neutral', 'Market Perform', 'Sector Perform']
                        sell_terms = ['Sell', 'Strong Sell', 'Underweight', 'Underperform', 'Negative', 'Reduce']

                        buy_count = sum(rec_counts.get(term, 0) for term in buy_terms)
                        hold_count = sum(rec_counts.get(term, 0) for term in hold_terms)
                        sell_count = sum(rec_counts.get(term, 0) for term in sell_terms)
                except Exception as e:
                    logger.warning(f"Could not parse recommendations: {e}")
                    buy_count = hold_count = sell_count = 0
            else:
                buy_count = hold_count = sell_count = 0

                total = buy_count + hold_count + sell_count
                if total > 0:
                    consensus = "Buy" if buy_count > (hold_count + sell_count) else "Hold" if hold_count > sell_count else "Sell"
                else:
                    consensus = "Hold"
            else:
                consensus = "Hold"
                rec_counts = {}

            # Get price targets from info
            target_high = info.get('targetHighPrice', 0)
            target_low = info.get('targetLowPrice', 0)
            target_mean = info.get('targetMeanPrice', 0)
            target_median = info.get('targetMedianPrice', 0)

            # If no analyst targets available, try to use recommendation trends
            if target_mean == 0 or target_mean is None:
                # Use consensus and current price to estimate
                if consensus == "Buy":
                    target_mean = current_price * 1.15  # 15% upside for buy
                    target_high = current_price * 1.30
                    target_low = current_price * 1.05
                elif consensus == "Sell":
                    target_mean = current_price * 0.85  # 15% downside for sell
                    target_high = current_price * 0.95
                    target_low = current_price * 0.70
                else:  # Hold
                    target_mean = current_price * 1.05  # 5% upside for hold
                    target_high = current_price * 1.15
                    target_low = current_price * 0.95
                target_median = target_mean

            return {
                "analyst_consensus": consensus,
                "target_high": round(target_high, 2),
                "target_low": round(target_low, 2),
                "target_mean": round(target_mean, 2),
                "target_median": round(target_median, 2),
                "number_of_analysts": info.get('numberOfAnalystOpinions', 0),
                "recommendation_breakdown": rec_counts,
                "upside_potential": round((target_mean - current_price) / current_price * 100, 2)
            }

        except Exception as e:
            logger.error(f"Failed to get analyst targets: {e}")
            return {"analyst_consensus": "Hold", "target_mean": 0}

    async def _calculate_technical_targets(self, market_data: Dict) -> Dict[str, Any]:
        """Calculate technical price targets based on chart patterns"""
        try:
            current_price = market_data.get('price', 0)
            high_52week = market_data.get('52WeekHigh', current_price * 1.2)
            low_52week = market_data.get('52WeekLow', current_price * 0.8)

            # Fibonacci retracement levels
            price_range = high_52week - low_52week
            fib_levels = {
                "fib_236": low_52week + price_range * 0.236,
                "fib_382": low_52week + price_range * 0.382,
                "fib_500": low_52week + price_range * 0.500,
                "fib_618": low_52week + price_range * 0.618,
                "fib_786": low_52week + price_range * 0.786
            }

            # Find nearest resistance and support
            resistance = min([level for level in fib_levels.values() if level > current_price],
                           default=high_52week)
            support = max([level for level in fib_levels.values() if level < current_price],
                        default=low_52week)

            # Pivot point calculation
            high = market_data.get('dayHigh', current_price)
            low = market_data.get('dayLow', current_price)
            close = current_price

            pivot = (high + low + close) / 3
            r1 = 2 * pivot - low  # First resistance
            r2 = pivot + (high - low)  # Second resistance
            s1 = 2 * pivot - high  # First support
            s2 = pivot - (high - low)  # Second support

            return {
                "technical_target": round(resistance, 2),
                "resistance_levels": {
                    "R1": round(r1, 2),
                    "R2": round(r2, 2),
                    "52_week_high": round(high_52week, 2)
                },
                "support_levels": {
                    "S1": round(s1, 2),
                    "S2": round(s2, 2),
                    "52_week_low": round(low_52week, 2)
                },
                "fibonacci_levels": {k: round(v, 2) for k, v in fib_levels.items()},
                "pivot_point": round(pivot, 2)
            }

        except Exception as e:
            logger.error(f"Technical targets calculation failed: {e}")
            return {"technical_target": 0}

    def _calculate_weighted_target(self, dcf: Dict, comparative: Dict,
                                  analyst: Dict, technical: Dict,
                                  current_price: float) -> Dict[str, Any]:
        """Calculate weighted average price target"""
        targets = []
        weights = []

        # DCF target (30% weight)
        if dcf.get('dcf_price', 0) > 0:
            targets.append(dcf['dcf_price'])
            weights.append(0.30)

        # Comparative target (25% weight)
        if comparative.get('comparative_price', 0) > 0:
            targets.append(comparative['comparative_price'])
            weights.append(0.25)

        # Analyst target (35% weight - highest as it's consensus)
        if analyst.get('target_mean', 0) > 0:
            targets.append(analyst['target_mean'])
            weights.append(0.35)

        # Technical target (10% weight)
        if technical.get('technical_target', 0) > 0:
            targets.append(technical['technical_target'])
            weights.append(0.10)

        # Calculate weighted average
        if targets and weights:
            # Normalize weights
            total_weight = sum(weights)
            weights = [w / total_weight for w in weights]

            weighted_target = sum(t * w for t, w in zip(targets, weights))

            # Calculate confidence based on spread
            spread = (max(targets) - min(targets)) / current_price
            confidence = max(0.4, min(0.9, 1 - spread))

            return {
                "price_target": round(weighted_target, 2),
                "upside": round((weighted_target - current_price) / current_price * 100, 2),
                "confidence": round(confidence, 2),
                "target_range": {
                    "low": round(min(targets), 2),
                    "high": round(max(targets), 2)
                },
                "methodology_weights": {
                    "DCF": "30%",
                    "Comparative": "25%",
                    "Analyst Consensus": "35%",
                    "Technical": "10%"
                }
            }
        else:
            return {
                "price_target": round(current_price * 1.1, 2),
                "upside": 10.0,
                "confidence": 0.5,
                "note": "Limited data available for accurate targeting"
            }

    def _get_valuation_rating(self, pe_ratio: float, peg_ratio: float) -> str:
        """Determine if stock is undervalued, fairly valued, or overvalued"""
        if pe_ratio <= 0:
            return "Cannot determine"

        if peg_ratio > 0:
            if peg_ratio < 1:
                return "Undervalued"
            elif peg_ratio < 1.5:
                return "Fairly Valued"
            else:
                return "Overvalued"
        else:
            if pe_ratio < 15:
                return "Potentially Undervalued"
            elif pe_ratio < 25:
                return "Fairly Valued"
            else:
                return "Potentially Overvalued"

    def _generate_valuation_summary(self, price_target: Dict, current_price: float) -> str:
        """Generate executive summary of valuation"""
        upside = price_target.get('upside', 0)
        confidence = price_target.get('confidence', 0.5)
        target = price_target.get('price_target', current_price)

        if upside > 20:
            recommendation = "STRONG BUY"
            action = "significant upside potential"
        elif upside > 10:
            recommendation = "BUY"
            action = "moderate upside potential"
        elif upside > -10:
            recommendation = "HOLD"
            action = "limited upside, fairly valued"
        else:
            recommendation = "SELL"
            action = "downside risk"

        summary = f"""
        Valuation Summary:
        Current Price: ${current_price:.2f}
        Price Target: ${target:.2f}
        Upside/Downside: {upside:.1f}%
        Confidence: {confidence*100:.0f}%
        Recommendation: {recommendation}

        The stock shows {action} based on our comprehensive valuation analysis
        combining DCF modeling, peer comparison, analyst consensus, and technical levels.
        """

        return summary.strip()