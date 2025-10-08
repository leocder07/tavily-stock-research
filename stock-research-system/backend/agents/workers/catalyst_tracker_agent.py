"""
Catalyst Tracker Agent
Tracks upcoming catalysts: earnings, product launches, regulatory events, macro events
"""

import asyncio
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
import yfinance as yf
import logging

logger = logging.getLogger(__name__)


class CatalystTrackerAgent:
    """Tracks upcoming catalysts and key events"""

    def __init__(self, tavily_client=None):
        self.name = "CatalystTrackerAgent"
        self.tavily_client = tavily_client

    async def execute(self, symbol: str, context: Optional[Dict] = None) -> Dict[str, Any]:
        """Execute catalyst tracking"""
        try:
            if isinstance(symbol, dict):
                symbol = symbol.get('symbol', symbol.get('ticker', ''))

            symbol = str(symbol).upper() if symbol else ''

            if not symbol:
                return {"error": "No symbol provided"}

            logger.info(f"[{self.name}] Tracking catalysts for {symbol}")

            # Get earnings dates and calendar
            earnings_data = await self._get_earnings_calendar(symbol)

            # Get product launch calendar (from news/Tavily)
            product_launches = await self._get_product_launches(symbol)

            # Get regulatory events
            regulatory_events = await self._get_regulatory_events(symbol)

            # Get macro calendar (Fed meetings, CPI, etc.)
            macro_events = await self._get_macro_events()

            # Historical earnings analysis
            earnings_history = await self._analyze_earnings_history(symbol)

            # Prioritize catalysts by impact
            prioritized_catalysts = self._prioritize_catalysts(
                earnings_data,
                product_launches,
                regulatory_events,
                macro_events
            )

            return {
                "symbol": symbol,
                "earnings": earnings_data,
                "product_launches": product_launches,
                "regulatory_events": regulatory_events,
                "macro_events": macro_events,
                "earnings_history": earnings_history,
                "prioritized_catalysts": prioritized_catalysts,
                "next_catalyst": prioritized_catalysts[0] if prioritized_catalysts else None,
                "catalyst_count": len(prioritized_catalysts)
            }

        except Exception as e:
            logger.error(f"[{self.name}] Catalyst tracking failed: {e}")
            return {"error": str(e)}

    async def _get_earnings_calendar(self, symbol: str) -> Dict[str, Any]:
        """Get earnings calendar from yfinance"""
        try:
            ticker = await asyncio.to_thread(yf.Ticker, symbol)

            # Get earnings dates
            calendar = None
            try:
                calendar = await asyncio.to_thread(lambda: ticker.calendar)
            except:
                pass

            result = {
                "next_earnings_date": None,
                "earnings_confirmed": False,
                "estimated_eps": None,
                "analyst_estimates": []
            }

            # Check if calendar has data (DataFrame or dict)
            has_data = False
            if calendar is not None:
                if isinstance(calendar, dict):
                    has_data = bool(calendar)
                elif hasattr(calendar, 'empty'):
                    has_data = not calendar.empty
                else:
                    has_data = True

            if has_data:
                # Extract earnings date (handle both dict and DataFrame)
                if isinstance(calendar, dict):
                    earnings_date = calendar.get('Earnings Date')
                    # Convert date object to ISO string if needed
                    if earnings_date:
                        # Handle tuple/list of dates (yfinance sometimes returns (date1, date2))
                        if isinstance(earnings_date, (list, tuple)):
                            earnings_date = earnings_date[0] if earnings_date else None
                        # Convert to string
                        if earnings_date:
                            result["next_earnings_date"] = earnings_date.isoformat() if hasattr(earnings_date, 'isoformat') else str(earnings_date)
                    result["estimated_eps"] = calendar.get('EPS Estimate')
                elif hasattr(calendar, 'index'):
                    # DataFrame structure
                    if 'Earnings Date' in calendar.index:
                        earnings_dates = calendar.loc['Earnings Date']
                        if isinstance(earnings_dates, str):
                            result["next_earnings_date"] = earnings_dates
                        elif hasattr(earnings_dates, 'values'):
                            # Get first value and convert datetime.date to string
                            date_val = earnings_dates.values[0]
                            result["next_earnings_date"] = date_val.isoformat() if hasattr(date_val, 'isoformat') else str(date_val)

                    # Extract EPS estimate
                    if 'EPS Estimate' in calendar.index:
                        result["estimated_eps"] = float(calendar.loc['EPS Estimate'])

            # Fallback: check info for earnings date
            if not result["next_earnings_date"]:
                info = await asyncio.to_thread(lambda: ticker.info)
                if 'earningsTimestamp' in info:
                    timestamp = info['earningsTimestamp']
                    result["next_earnings_date"] = datetime.fromtimestamp(timestamp).strftime('%Y-%m-%d')

            # Check if date is confirmed (within 60 days)
            if result["next_earnings_date"]:
                try:
                    earnings_dt = datetime.strptime(result["next_earnings_date"].split()[0], '%Y-%m-%d')
                    days_until = (earnings_dt - datetime.now()).days
                    result["earnings_confirmed"] = 0 < days_until < 60
                    result["days_until_earnings"] = days_until
                except:
                    pass

            return result

        except Exception as e:
            logger.error(f"[{self.name}] Error fetching earnings calendar: {e}")
            return {
                "next_earnings_date": None,
                "earnings_confirmed": False,
                "error": str(e)
            }

    async def _get_product_launches(self, symbol: str) -> List[Dict]:
        """Get product launch calendar from news"""
        launches = []

        if self.tavily_client:
            try:
                # Search for product launch news
                query = f"{symbol} product launch announcement 2024 2025"
                results = await self.tavily_client.search(
                    query=query,
                    max_results=3
                )

                # Handle both dict and coroutine responses
                if hasattr(results, 'get'):
                    items = results.get('results', [])
                else:
                    items = []

                for item in items:
                    # Extract potential launch dates from news
                    launches.append({
                        "type": "product_launch",
                        "title": item.get('title', ''),
                        "date": "TBD",  # Would need NLP to extract dates
                        "source": item.get('url', ''),
                        "impact": "medium"
                    })

            except Exception as e:
                logger.warning(f"[{self.name}] Could not fetch product launches: {e}")

        return launches

    async def _get_regulatory_events(self, symbol: str) -> List[Dict]:
        """Get regulatory events (FDA approvals, antitrust, etc.)"""
        events = []

        if self.tavily_client:
            try:
                # Search for regulatory news
                query = f"{symbol} regulatory approval FDA antitrust lawsuit 2024"
                results = await self.tavily_client.search(
                    query=query,
                    max_results=3
                )

                # Handle both dict and coroutine responses
                if hasattr(results, 'get'):
                    items = results.get('results', [])
                else:
                    items = []

                for item in items:
                    events.append({
                        "type": "regulatory",
                        "title": item.get('title', ''),
                        "date": "TBD",
                        "source": item.get('url', ''),
                        "impact": "high"
                    })

            except Exception as e:
                logger.warning(f"[{self.name}] Could not fetch regulatory events: {e}")

        return events

    async def _get_macro_events(self) -> List[Dict]:
        """Get macro calendar (Fed meetings, CPI, GDP)"""
        # Hardcoded key 2024-2025 events (in production, fetch from economic calendar API)
        macro_events = [
            {
                "type": "fed_meeting",
                "date": "2024-11-07",
                "title": "FOMC Meeting",
                "impact": "high"
            },
            {
                "type": "fed_meeting",
                "date": "2024-12-18",
                "title": "FOMC Meeting",
                "impact": "high"
            },
            {
                "type": "economic_data",
                "date": "2024-11-13",
                "title": "CPI Release",
                "impact": "high"
            }
        ]

        # Filter to upcoming events only
        today = datetime.now()
        upcoming = []
        for event in macro_events:
            try:
                event_date = datetime.strptime(event['date'], '%Y-%m-%d')
                if event_date > today:
                    days_until = (event_date - today).days
                    event['days_until'] = days_until
                    upcoming.append(event)
            except:
                pass

        return sorted(upcoming, key=lambda x: x.get('days_until', 999))

    async def _analyze_earnings_history(self, symbol: str) -> Dict[str, Any]:
        """Analyze historical earnings surprises"""
        try:
            ticker = await asyncio.to_thread(yf.Ticker, symbol)

            # Get quarterly earnings
            earnings_history = await asyncio.to_thread(lambda: ticker.earnings_history)

            if earnings_history is None or earnings_history.empty:
                return {"error": "No earnings history available"}

            # Calculate surprise metrics
            surprises = []
            beat_count = 0
            miss_count = 0

            for _, row in earnings_history.iterrows():
                if 'epsActual' in row and 'epsEstimate' in row:
                    actual = row['epsActual']
                    estimate = row['epsEstimate']
                    surprise = actual - estimate
                    surprise_pct = (surprise / estimate * 100) if estimate != 0 else 0

                    if surprise > 0:
                        beat_count += 1
                    elif surprise < 0:
                        miss_count += 1

                    surprises.append(surprise_pct)

            return {
                "total_reports": len(surprises),
                "beat_count": beat_count,
                "miss_count": miss_count,
                "beat_rate": round(beat_count / len(surprises) * 100, 2) if surprises else 0,
                "avg_surprise_pct": round(sum(surprises) / len(surprises), 2) if surprises else 0,
                "last_surprise_pct": surprises[0] if surprises else None
            }

        except Exception as e:
            logger.error(f"[{self.name}] Error analyzing earnings history: {e}")
            return {"error": str(e)}

    def _prioritize_catalysts(self,
                            earnings: Dict,
                            products: List[Dict],
                            regulatory: List[Dict],
                            macro: List[Dict]) -> List[Dict]:
        """Prioritize catalysts by date and impact"""
        all_catalysts = []

        # Add earnings
        if earnings.get('next_earnings_date'):
            all_catalysts.append({
                "type": "earnings",
                "date": earnings['next_earnings_date'],
                "title": "Earnings Release",
                "impact": "high",
                "confirmed": earnings.get('earnings_confirmed', False),
                "days_until": earnings.get('days_until_earnings')
            })

        # Add product launches
        all_catalysts.extend(products)

        # Add regulatory
        all_catalysts.extend(regulatory)

        # Add macro events (only most impactful)
        all_catalysts.extend([m for m in macro if m.get('impact') == 'high'][:3])

        # Sort by days until (if available) or impact
        def sort_key(catalyst):
            days = catalyst.get('days_until', 999)
            impact_weight = {'high': 1, 'medium': 2, 'low': 3}.get(catalyst.get('impact', 'low'), 3)
            return (days, impact_weight)

        return sorted(all_catalysts, key=sort_key)
