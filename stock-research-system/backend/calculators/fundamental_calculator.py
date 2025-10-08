"""
Fundamental Analysis Calculator
Pure mathematical implementations of valuation models
No external API dependencies - Warren Buffett-style analysis
"""

from typing import Dict, List, Optional
from datetime import datetime
import math


class FundamentalCalculator:
    """Calculate fundamental metrics and valuations"""

    def calculate_dcf(self,
                     free_cash_flows: List[float],
                     growth_rate: float,
                     discount_rate: float,
                     terminal_growth: float = 0.03,
                     years: int = 5) -> Dict:
        """
        Discounted Cash Flow Valuation

        Args:
            free_cash_flows: Historical FCF data
            growth_rate: Expected growth rate (decimal)
            discount_rate: WACC or required return (decimal)
            terminal_growth: Perpetual growth rate (decimal)
            years: Forecast period
        """
        if not free_cash_flows:
            return {'intrinsic_value': None, 'error': 'No cash flow data'}

        # Project future cash flows
        last_fcf = free_cash_flows[-1]
        projected_fcf = []

        for year in range(1, years + 1):
            fcf = last_fcf * ((1 + growth_rate) ** year)
            projected_fcf.append(fcf)

        # Calculate present value of projected cash flows
        pv_fcf = []
        for year, fcf in enumerate(projected_fcf, start=1):
            pv = fcf / ((1 + discount_rate) ** year)
            pv_fcf.append(pv)

        # Calculate terminal value
        terminal_fcf = projected_fcf[-1] * (1 + terminal_growth)
        terminal_value = terminal_fcf / (discount_rate - terminal_growth)
        pv_terminal = terminal_value / ((1 + discount_rate) ** years)

        # Total enterprise value
        enterprise_value = sum(pv_fcf) + pv_terminal

        return {
            'intrinsic_value': round(enterprise_value, 2),
            'pv_cash_flows': round(sum(pv_fcf), 2),
            'pv_terminal_value': round(pv_terminal, 2),
            'terminal_value_percent': round((pv_terminal / enterprise_value) * 100, 2),
            'projected_fcf': [round(f, 2) for f in projected_fcf],
            'assumptions': {
                'growth_rate': growth_rate,
                'discount_rate': discount_rate,
                'terminal_growth': terminal_growth
            }
        }

    def calculate_pe_ratio(self, price: float, earnings_per_share: float) -> Optional[float]:
        """Price-to-Earnings Ratio"""
        if earnings_per_share <= 0:
            return None
        return round(price / earnings_per_share, 2)

    def calculate_peg_ratio(self, pe_ratio: float, growth_rate: float) -> Optional[float]:
        """Price/Earnings-to-Growth Ratio"""
        if growth_rate <= 0 or pe_ratio is None:
            return None
        return round(pe_ratio / (growth_rate * 100), 2)

    def calculate_roe(self, net_income: float, shareholder_equity: float) -> Optional[float]:
        """Return on Equity - Validated to prevent extreme outliers"""
        if shareholder_equity <= 0:
            return None

        roe = round((net_income / shareholder_equity) * 100, 2)

        # Validate ROE bounds - values above 100% or below -100% are extremely rare and likely errors
        if roe > 100:
            print(f"⚠️  Warning: ROE {roe}% exceeds 100% (likely data error). Capping at 100%.")
            return 100.0
        elif roe < -100:
            print(f"⚠️  Warning: ROE {roe}% below -100% (likely data error). Capping at -100%.")
            return -100.0

        return roe

    def calculate_roa(self, net_income: float, total_assets: float) -> Optional[float]:
        """Return on Assets"""
        if total_assets <= 0:
            return None
        return round((net_income / total_assets) * 100, 2)

    def calculate_debt_to_equity(self, total_debt: float, shareholder_equity: float) -> Optional[float]:
        """Debt-to-Equity Ratio"""
        if shareholder_equity <= 0:
            return None
        return round(total_debt / shareholder_equity, 2)

    def calculate_current_ratio(self, current_assets: float, current_liabilities: float) -> Optional[float]:
        """Current Ratio - liquidity metric"""
        if current_liabilities <= 0:
            return None
        return round(current_assets / current_liabilities, 2)

    def calculate_quick_ratio(self, current_assets: float, inventory: float,
                             current_liabilities: float) -> Optional[float]:
        """Quick Ratio (Acid Test)"""
        if current_liabilities <= 0:
            return None
        return round((current_assets - inventory) / current_liabilities, 2)

    def calculate_gross_margin(self, revenue: float, cogs: float) -> Optional[float]:
        """Gross Profit Margin"""
        if revenue <= 0:
            return None
        return round(((revenue - cogs) / revenue) * 100, 2)

    def calculate_operating_margin(self, operating_income: float, revenue: float) -> Optional[float]:
        """Operating Profit Margin"""
        if revenue <= 0:
            return None
        return round((operating_income / revenue) * 100, 2)

    def calculate_net_margin(self, net_income: float, revenue: float) -> Optional[float]:
        """Net Profit Margin"""
        if revenue <= 0:
            return None
        return round((net_income / revenue) * 100, 2)

    def calculate_ev_to_ebitda(self, market_cap: float, total_debt: float,
                               cash: float, ebitda: float) -> Optional[float]:
        """Enterprise Value to EBITDA"""
        if ebitda <= 0:
            return None
        enterprise_value = market_cap + total_debt - cash
        return round(enterprise_value / ebitda, 2)

    def calculate_price_to_book(self, price: float, book_value_per_share: float) -> Optional[float]:
        """Price-to-Book Ratio"""
        if book_value_per_share <= 0:
            return None
        return round(price / book_value_per_share, 2)

    def calculate_dividend_yield(self, annual_dividend: float, price: float) -> Optional[float]:
        """Dividend Yield"""
        if price <= 0:
            return None
        return round((annual_dividend / price) * 100, 2)

    def calculate_payout_ratio(self, dividends: float, net_income: float) -> Optional[float]:
        """Dividend Payout Ratio"""
        if net_income <= 0:
            return None
        return round((dividends / net_income) * 100, 2)

    def assess_financial_health(self, metrics: Dict) -> Dict:
        """
        Comprehensive financial health assessment
        Ray Dalio's principles-based scoring
        """
        score = 0
        max_score = 0
        factors = []

        # Profitability (30 points)
        if metrics.get('roe'):
            max_score += 10
            if metrics['roe'] > 15:
                score += 10
                factors.append({'factor': 'Strong ROE', 'impact': 'positive'})
            elif metrics['roe'] > 10:
                score += 6
                factors.append({'factor': 'Moderate ROE', 'impact': 'neutral'})
            else:
                factors.append({'factor': 'Weak ROE', 'impact': 'negative'})

        if metrics.get('net_margin'):
            max_score += 10
            if metrics['net_margin'] > 15:
                score += 10
                factors.append({'factor': 'High profit margin', 'impact': 'positive'})
            elif metrics['net_margin'] > 8:
                score += 6
            else:
                factors.append({'factor': 'Low profit margin', 'impact': 'negative'})

        if metrics.get('operating_margin'):
            max_score += 10
            if metrics['operating_margin'] > 20:
                score += 10
                factors.append({'factor': 'Excellent operating efficiency', 'impact': 'positive'})
            elif metrics['operating_margin'] > 12:
                score += 6

        # Valuation (25 points)
        if metrics.get('pe_ratio'):
            max_score += 15
            if 10 <= metrics['pe_ratio'] <= 20:
                score += 15
                factors.append({'factor': 'Fair valuation (P/E)', 'impact': 'positive'})
            elif metrics['pe_ratio'] < 10:
                score += 10
                factors.append({'factor': 'Undervalued (P/E)', 'impact': 'positive'})
            elif metrics['pe_ratio'] > 30:
                factors.append({'factor': 'Potentially overvalued', 'impact': 'negative'})

        if metrics.get('peg_ratio'):
            max_score += 10
            if metrics['peg_ratio'] < 1:
                score += 10
                factors.append({'factor': 'Attractive growth valuation', 'impact': 'positive'})
            elif metrics['peg_ratio'] < 1.5:
                score += 6

        # Financial Stability (25 points)
        if metrics.get('debt_to_equity'):
            max_score += 15
            if metrics['debt_to_equity'] < 0.5:
                score += 15
                factors.append({'factor': 'Strong balance sheet', 'impact': 'positive'})
            elif metrics['debt_to_equity'] < 1:
                score += 10
                factors.append({'factor': 'Moderate leverage', 'impact': 'neutral'})
            else:
                factors.append({'factor': 'High debt levels', 'impact': 'negative'})

        if metrics.get('current_ratio'):
            max_score += 10
            if metrics['current_ratio'] > 2:
                score += 10
                factors.append({'factor': 'Strong liquidity', 'impact': 'positive'})
            elif metrics['current_ratio'] > 1:
                score += 6
            else:
                factors.append({'factor': 'Liquidity concerns', 'impact': 'negative'})

        # Moat Indicators (20 points)
        if metrics.get('gross_margin'):
            max_score += 10
            if metrics['gross_margin'] > 50:
                score += 10
                factors.append({'factor': 'Wide economic moat', 'impact': 'positive'})
            elif metrics['gross_margin'] > 35:
                score += 6
                factors.append({'factor': 'Competitive advantage', 'impact': 'positive'})

        if metrics.get('roe') and metrics.get('roe') > 20:
            max_score += 10
            score += 10
            factors.append({'factor': 'Exceptional capital efficiency', 'impact': 'positive'})

        # Calculate final score
        final_score = (score / max_score * 100) if max_score > 0 else 0

        # Determine rating
        if final_score >= 80:
            rating = 'Excellent'
            recommendation = 'STRONG_BUY'
        elif final_score >= 65:
            rating = 'Good'
            recommendation = 'BUY'
        elif final_score >= 50:
            rating = 'Fair'
            recommendation = 'HOLD'
        elif final_score >= 35:
            rating = 'Below Average'
            recommendation = 'SELL'
        else:
            rating = 'Poor'
            recommendation = 'STRONG_SELL'

        return {
            'score': round(final_score, 2),
            'rating': rating,
            'recommendation': recommendation,
            'factors': factors,
            'strengths': [f['factor'] for f in factors if f['impact'] == 'positive'],
            'weaknesses': [f['factor'] for f in factors if f['impact'] == 'negative']
        }

    def calculate_magic_formula_rank(self, earnings_yield: float, roic: float) -> Dict:
        """
        Joel Greenblatt's Magic Formula
        Combines value (earnings yield) and quality (ROIC)
        """
        # Earnings Yield = EBIT / Enterprise Value
        # ROIC = EBIT / (Net Working Capital + Net Fixed Assets)

        ey_rank = earnings_yield * 100  # Higher is better
        roic_rank = roic * 100  # Higher is better

        combined_score = (ey_rank + roic_rank) / 2

        if combined_score > 20:
            signal = 'strong_buy'
            interpretation = 'High quality at reasonable price'
        elif combined_score > 15:
            signal = 'buy'
            interpretation = 'Good value proposition'
        elif combined_score > 10:
            signal = 'hold'
            interpretation = 'Fair value'
        else:
            signal = 'avoid'
            interpretation = 'Poor value or quality'

        return {
            'earnings_yield': round(earnings_yield * 100, 2),
            'roic': round(roic * 100, 2),
            'magic_formula_score': round(combined_score, 2),
            'signal': signal,
            'interpretation': interpretation
        }

    def graham_number(self, eps: float, book_value: float) -> Dict:
        """
        Benjamin Graham's intrinsic value formula
        Fair value = sqrt(22.5 * EPS * Book Value per Share)
        """
        if eps <= 0 or book_value <= 0:
            return {'fair_value': None, 'error': 'Invalid inputs'}

        fair_value = math.sqrt(22.5 * eps * book_value)

        return {
            'fair_value': round(fair_value, 2),
            'formula': 'sqrt(22.5 * EPS * Book Value)',
            'interpretation': 'Conservative value estimate'
        }
