"""
Insider Activity Agent - Insider Trading, Institutional Ownership, Analyst Ratings

This agent analyzes insider and institutional activity:
1. Insider trading (Form 4 filings - buys/sells by executives)
2. Institutional ownership changes (13F filings)
3. Analyst ratings and price targets
4. Smart money flow and sentiment
5. Major shareholder activity
"""

import asyncio
from typing import Dict, Any, List, Optional
from datetime import datetime
import logging

from services.progress_tracker import Citation, progress_tracker

logger = logging.getLogger(__name__)


class InsiderActivityAgent:
    """
    Insider Activity Agent for analyzing insider trading and institutional activity.

    Uses Tavily APIs to gather:
    - Recent insider buys/sells (Form 4 filings)
    - Institutional ownership trends (13F filings)
    - Analyst ratings, upgrades/downgrades
    - Consensus price targets
    - Major shareholder activities
    """

    def __init__(self, tavily_client=None, memory=None, **kwargs):
        self.tavily_client = tavily_client
        self.memory = memory
        self.name = "insider_activity"
        self.description = "Analyzes insider trading, institutional ownership, and analyst ratings"
        self.citations = []
        self.request_id = None

    async def execute(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """Execute insider activity analysis."""
        try:
            await self.send_progress("Starting insider activity analysis...", 0.0)

            symbol = state.get('symbol') or state.get('symbols', [''])[0]
            if not symbol:
                raise ValueError("No stock symbol provided for insider analysis")

            # Phase 1: Insider Trading Analysis (30%)
            await self.send_progress(f"Analyzing insider trading for {symbol}...", 0.05)
            insider_trading = await self._analyze_insider_trading(symbol)
            await self.send_progress("Insider trading analysis complete", 0.3)

            # Phase 2: Institutional Ownership (60%)
            await self.send_progress("Analyzing institutional ownership...", 0.35)
            institutional = await self._analyze_institutional_ownership(symbol)
            await self.send_progress("Institutional ownership analysis complete", 0.6)

            # Phase 3: Analyst Ratings (85%)
            await self.send_progress("Gathering analyst ratings and price targets...", 0.65)
            analyst_data = await self._analyze_analyst_ratings(symbol)
            await self.send_progress("Analyst ratings analysis complete", 0.85)

            # Phase 4: Smart Money Sentiment (95%)
            await self.send_progress("Assessing smart money sentiment...", 0.90)
            smart_money = await self._assess_smart_money_sentiment(
                insider_trading, institutional, analyst_data
            )
            await self.send_progress("Smart money sentiment complete", 0.95)

            # Synthesize insider activity outlook
            await self.send_progress("Synthesizing insider activity outlook...", 0.98)
            insider_outlook = await self._synthesize_insider_outlook(
                symbol, insider_trading, institutional, analyst_data, smart_money
            )
            await self.send_progress("Insider activity analysis complete", 1.0)

            return {
                'insider_analysis': insider_outlook,
                'citations': self.citations
            }

        except Exception as e:
            logger.error(f"Error in InsiderActivityAgent: {e}", exc_info=True)
            await self.send_progress(f"Insider analysis failed: {str(e)}", 1.0)
            return {'insider_analysis': None, 'error': str(e)}

    async def _analyze_insider_trading(self, symbol: str) -> Dict[str, Any]:
        """Analyze recent insider trading activity (Form 4 filings)."""
        insider_trading = {
            'recent_insider_buys': [],
            'recent_insider_sells': [],
            'insider_buy_sell_ratio': None,
            'notable_transactions': [],
            'insider_sentiment': 'NEUTRAL',
            'insider_confidence': 'MODERATE'
        }

        try:
            # Query 1: Recent insider transactions
            insider_query = f"{symbol} stock insider trading Form 4 filings recent insider buys sells executives CEO CFO"
            insider_results = await self.search_tavily(insider_query)

            if insider_results:
                for result in insider_results[:4]:
                    self.add_citation(
                        url=result.get('url', ''),
                        title=result.get('title', ''),
                        content=result.get('content', ''),
                        relevance_score=result.get('score', 0.85)
                    )

                # Analyze content for buy/sell signals
                content = ' '.join([r.get('content', '') for r in insider_results[:4]]).lower()

                buy_count = content.count('insider buy') + content.count('purchase')
                sell_count = content.count('insider sell') + content.count('sold')

                if buy_count > 0 or sell_count > 0:
                    insider_trading['insider_buy_sell_ratio'] = (
                        buy_count / (sell_count + 1) if sell_count > 0 else buy_count
                    )

                # Determine sentiment based on activity
                if buy_count > sell_count * 1.5:
                    insider_trading['insider_sentiment'] = 'BULLISH'
                    insider_trading['insider_confidence'] = 'HIGH'
                elif sell_count > buy_count * 1.5:
                    insider_trading['insider_sentiment'] = 'BEARISH'
                    insider_trading['insider_confidence'] = 'MODERATE'
                else:
                    insider_trading['insider_sentiment'] = 'NEUTRAL'
                    insider_trading['insider_confidence'] = 'LOW'

                # Extract notable transactions
                for result in insider_results[:3]:
                    if 'ceo' in result.get('content', '').lower() or 'cfo' in result.get('content', '').lower():
                        insider_trading['notable_transactions'].append({
                            'description': result.get('title', ''),
                            'source': result.get('url', '')
                        })

            # Query 2: Specific insider sentiment analysis
            sentiment_query = f"{symbol} insider trading sentiment analysis executives buying or selling confidence"
            sentiment_results = await self.qna_search_tavily(sentiment_query)

            if sentiment_results:
                # Handle both string and dict responses from Tavily
                if isinstance(sentiment_results, dict):
                    self.add_citation(
                        url=sentiment_results.get('url', ''),
                        title=f"{symbol} Insider Sentiment",
                        content=sentiment_results.get('answer', sentiment_results.get('content', '')),
                        relevance_score=0.8
                    )
                elif isinstance(sentiment_results, str):
                    # QnA search returned a string answer directly
                    self.add_citation(
                        url='',
                        title=f"{symbol} Insider Sentiment",
                        content=sentiment_results,
                        relevance_score=0.8
                    )

        except Exception as e:
            logger.error(f"Error analyzing insider trading: {e}", exc_info=True)

        return insider_trading

    async def _analyze_institutional_ownership(self, symbol: str) -> Dict[str, Any]:
        """Analyze institutional ownership and 13F filings."""
        institutional = {
            'institutional_ownership_pct': None,
            'top_institutional_holders': [],
            'recent_ownership_changes': [],
            'institutional_sentiment': 'NEUTRAL',
            'ownership_trend': 'STABLE',
            'smart_money_activity': []
        }

        try:
            # Query 1: Institutional ownership percentage
            ownership_query = f"{symbol} stock institutional ownership percentage top holders BlackRock Vanguard"
            ownership_results = await self.search_tavily(ownership_query)

            if ownership_results:
                for result in ownership_results[:3]:
                    self.add_citation(
                        url=result.get('url', ''),
                        title=result.get('title', ''),
                        content=result.get('content', ''),
                                    relevance_score=result.get('score', 0.8)
                    )

                content = ' '.join([r.get('content', '') for r in ownership_results[:3]])

                # Extract institutional ownership percentage
                institutional['institutional_ownership_pct'] = self._extract_percentage(content)

                # Extract top holders
                for holder in ['BlackRock', 'Vanguard', 'State Street', 'Fidelity', 'JPMorgan']:
                    if holder.lower() in content.lower():
                        institutional['top_institutional_holders'].append(holder)

            # Query 2: Recent 13F changes
            changes_query = f"{symbol} stock 13F filings institutional investors buying selling Q4 2024 latest quarter"
            changes_results = await self.search_tavily(changes_query)

            if changes_results:
                for result in changes_results[:3]:
                    self.add_citation(
                        url=result.get('url', ''),
                        title=result.get('title', ''),
                        content=result.get('content', ''),
                                    relevance_score=result.get('score', 0.85)
                    )

                content = ' '.join([r.get('content', '') for r in changes_results[:3]]).lower()

                # Analyze ownership changes
                increased = content.count('increased') + content.count('added') + content.count('bought')
                decreased = content.count('decreased') + content.count('reduced') + content.count('sold')

                if increased > decreased * 1.3:
                    institutional['institutional_sentiment'] = 'BULLISH'
                    institutional['ownership_trend'] = 'INCREASING'
                elif decreased > increased * 1.3:
                    institutional['institutional_sentiment'] = 'BEARISH'
                    institutional['ownership_trend'] = 'DECREASING'
                else:
                    institutional['institutional_sentiment'] = 'NEUTRAL'
                    institutional['ownership_trend'] = 'STABLE'

                # Extract notable changes
                for result in changes_results[:2]:
                    institutional['recent_ownership_changes'].append({
                        'description': result.get('title', ''),
                        'details': result.get('content', '')[:200]
                    })

            # Query 3: Hedge fund activity
            hedge_fund_query = f"{symbol} stock hedge fund activity notable investors Buffett Ackman 13F"
            hedge_results = await self.search_tavily(hedge_fund_query)

            if hedge_results:
                self.add_citation(
                    url=hedge_results[0].get('url', ''),
                    title=hedge_results[0].get('title', ''),
                    content=hedge_results[0].get('content', ''),
                            relevance_score=hedge_results[0].get('score', 0.75)
                )

                institutional['smart_money_activity'].append({
                    'description': hedge_results[0].get('title', ''),
                    'source': hedge_results[0].get('url', '')
                })

        except Exception as e:
            logger.error(f"Error analyzing institutional ownership: {e}")

        return institutional

    async def _analyze_analyst_ratings(self, symbol: str) -> Dict[str, Any]:
        """Analyze analyst ratings, price targets, and recommendations."""
        analyst_data = {
            'analyst_rating': 'HOLD',
            'consensus_price_target': None,
            'price_target_high': None,
            'price_target_low': None,
            'current_price': None,
            'upside_to_target': None,
            'num_analysts': None,
            'recent_upgrades': [],
            'recent_downgrades': [],
            'rating_distribution': {},
            'analyst_sentiment': 'NEUTRAL'
        }

        try:
            # Query 1: Analyst ratings and price targets
            analyst_query = f"{symbol} stock analyst ratings price target consensus buy hold sell recommendations"
            analyst_results = await self.search_tavily(analyst_query)

            if analyst_results:
                for result in analyst_results[:4]:
                    self.add_citation(
                        url=result.get('url', ''),
                        title=result.get('title', ''),
                        content=result.get('content', ''),
                                    relevance_score=result.get('score', 0.9)
                    )

                content = ' '.join([r.get('content', '') for r in analyst_results[:4]]).lower()

                # Extract consensus rating
                if 'strong buy' in content:
                    analyst_data['analyst_rating'] = 'STRONG BUY'
                elif 'buy' in content and 'hold' not in content:
                    analyst_data['analyst_rating'] = 'BUY'
                elif 'hold' in content:
                    analyst_data['analyst_rating'] = 'HOLD'
                elif 'sell' in content:
                    analyst_data['analyst_rating'] = 'SELL'

                # Extract price targets
                analyst_data['consensus_price_target'] = self._extract_price_target(content, 'consensus')
                analyst_data['price_target_high'] = self._extract_price_target(content, 'high')
                analyst_data['price_target_low'] = self._extract_price_target(content, 'low')

                # Extract current price
                analyst_data['current_price'] = self._extract_current_price(content)

                # Calculate upside
                if analyst_data['consensus_price_target'] and analyst_data['current_price']:
                    upside = (
                        (analyst_data['consensus_price_target'] - analyst_data['current_price']) /
                        analyst_data['current_price']
                    ) * 100
                    analyst_data['upside_to_target'] = upside

                # Extract number of analysts
                analyst_data['num_analysts'] = self._extract_num_analysts(content)

            # Query 2: Recent analyst upgrades/downgrades
            changes_query = f"{symbol} stock analyst upgrades downgrades recent rating changes 2024"
            changes_results = await self.search_tavily(changes_query)

            if changes_results:
                for result in changes_results[:3]:
                    self.add_citation(
                        url=result.get('url', ''),
                        title=result.get('title', ''),
                        content=result.get('content', ''),
                                    relevance_score=result.get('score', 0.85)
                    )

                content = ' '.join([r.get('content', '') for r in changes_results[:3]]).lower()

                upgrades = content.count('upgrade') + content.count('raised')
                downgrades = content.count('downgrade') + content.count('lowered')

                # Determine analyst sentiment
                if upgrades > downgrades * 1.5:
                    analyst_data['analyst_sentiment'] = 'BULLISH'
                elif downgrades > upgrades * 1.5:
                    analyst_data['analyst_sentiment'] = 'BEARISH'
                else:
                    analyst_data['analyst_sentiment'] = 'NEUTRAL'

                # Extract recent changes
                for result in changes_results[:3]:
                    title_lower = result.get('title', '').lower()
                    if 'upgrade' in title_lower or 'raised' in title_lower:
                        analyst_data['recent_upgrades'].append(result.get('title', ''))
                    elif 'downgrade' in title_lower or 'lowered' in title_lower:
                        analyst_data['recent_downgrades'].append(result.get('title', ''))

            # Query 3: Specific analyst commentary
            commentary_query = f"{symbol} stock analyst commentary outlook forecast what analysts say"
            commentary_results = await self.qna_search_tavily(commentary_query)

            if commentary_results:
                # Handle both string and dict responses from Tavily
                if isinstance(commentary_results, dict):
                    self.add_citation(
                        url=commentary_results.get('url', ''),
                        title=f"{symbol} Analyst Commentary",
                        content=commentary_results.get('answer', commentary_results.get('content', '')),
                        relevance_score=0.8
                    )
                elif isinstance(commentary_results, str):
                    # QnA search returned a string answer directly
                    self.add_citation(
                        url='',
                        title=f"{symbol} Analyst Commentary",
                        content=commentary_results,
                        relevance_score=0.8
                    )

        except Exception as e:
            logger.error(f"Error analyzing analyst ratings: {e}", exc_info=True)

        return analyst_data

    async def _assess_smart_money_sentiment(
        self,
        insider_trading: Dict,
        institutional: Dict,
        analyst_data: Dict
    ) -> Dict[str, Any]:
        """Assess overall smart money sentiment combining all sources."""
        smart_money = {
            'overall_sentiment': 'NEUTRAL',
            'confidence_level': 'MODERATE',
            'bullish_signals': [],
            'bearish_signals': [],
            'smart_money_score': 0  # -10 to +10
        }

        score = 0

        # Insider trading signals
        insider_sentiment = insider_trading.get('insider_sentiment', 'NEUTRAL')
        if insider_sentiment == 'BULLISH':
            score += 3
            smart_money['bullish_signals'].append('Insiders are buying shares')
        elif insider_sentiment == 'BEARISH':
            score -= 2
            smart_money['bearish_signals'].append('Insiders are selling shares')

        # Institutional ownership signals
        inst_sentiment = institutional.get('institutional_sentiment', 'NEUTRAL')
        ownership_trend = institutional.get('ownership_trend', 'STABLE')

        if inst_sentiment == 'BULLISH' or ownership_trend == 'INCREASING':
            score += 2
            smart_money['bullish_signals'].append('Institutions increasing ownership')
        elif inst_sentiment == 'BEARISH' or ownership_trend == 'DECREASING':
            score -= 2
            smart_money['bearish_signals'].append('Institutions reducing positions')

        # Analyst signals
        analyst_sentiment = analyst_data.get('analyst_sentiment', 'NEUTRAL')
        analyst_rating = analyst_data.get('analyst_rating', 'HOLD')

        if analyst_rating in ['STRONG BUY', 'BUY'] or analyst_sentiment == 'BULLISH':
            score += 2
            smart_money['bullish_signals'].append('Analysts recommend buying')
        elif analyst_rating == 'SELL' or analyst_sentiment == 'BEARISH':
            score -= 2
            smart_money['bearish_signals'].append('Analysts recommend selling')

        # Price target upside
        upside = analyst_data.get('upside_to_target')
        if upside and upside > 20:
            score += 1
            smart_money['bullish_signals'].append(f'Price target implies {upside:.0f}% upside')
        elif upside and upside < -10:
            score -= 1
            smart_money['bearish_signals'].append(f'Price target implies {upside:.0f}% downside')

        # Determine overall sentiment
        smart_money['smart_money_score'] = score

        if score >= 5:
            smart_money['overall_sentiment'] = 'VERY BULLISH'
            smart_money['confidence_level'] = 'HIGH'
        elif score >= 2:
            smart_money['overall_sentiment'] = 'BULLISH'
            smart_money['confidence_level'] = 'MODERATE'
        elif score <= -5:
            smart_money['overall_sentiment'] = 'VERY BEARISH'
            smart_money['confidence_level'] = 'HIGH'
        elif score <= -2:
            smart_money['overall_sentiment'] = 'BEARISH'
            smart_money['confidence_level'] = 'MODERATE'
        else:
            smart_money['overall_sentiment'] = 'NEUTRAL'
            smart_money['confidence_level'] = 'LOW'

        return smart_money

    async def _synthesize_insider_outlook(
        self,
        symbol: str,
        insider_trading: Dict,
        institutional: Dict,
        analyst_data: Dict,
        smart_money: Dict
    ) -> Dict[str, Any]:
        """Synthesize all insider activity into actionable outlook."""

        synthesis = {
            'symbol': symbol,
            'smart_money_sentiment': smart_money.get('overall_sentiment', 'NEUTRAL'),
            'confidence_level': smart_money.get('confidence_level', 'MODERATE'),
            'insider_activity': insider_trading,
            'institutional_ownership': institutional,
            'analyst_ratings': analyst_data,
            'smart_money_analysis': smart_money,
            'investment_implications': [],
            'key_insights': []
        }

        # Add investment implications based on sentiment
        sentiment = smart_money.get('overall_sentiment', 'NEUTRAL')

        if sentiment in ['VERY BULLISH', 'BULLISH']:
            synthesis['investment_implications'] = [
                'Smart money is accumulating shares',
                'Consider increasing position size',
                'Strong conviction from insiders and institutions'
            ]
        elif sentiment in ['VERY BEARISH', 'BEARISH']:
            synthesis['investment_implications'] = [
                'Smart money is reducing exposure',
                'Consider defensive positioning',
                'Wait for clearer signals before adding'
            ]
        else:
            synthesis['investment_implications'] = [
                'Mixed signals from smart money',
                'Focus on fundamental analysis',
                'Monitor for changes in sentiment'
            ]

        # Add key insights
        if insider_trading.get('insider_sentiment') != 'NEUTRAL':
            synthesis['key_insights'].append(
                f"Insider sentiment: {insider_trading.get('insider_sentiment', 'NEUTRAL')}"
            )

        if institutional.get('institutional_ownership_pct'):
            synthesis['key_insights'].append(
                f"Institutional ownership: {institutional['institutional_ownership_pct']:.1f}% "
                f"({institutional.get('ownership_trend', 'STABLE')})"
            )

        if analyst_data.get('analyst_rating'):
            synthesis['key_insights'].append(
                f"Analyst consensus: {analyst_data['analyst_rating']}"
            )

        if analyst_data.get('consensus_price_target') and analyst_data.get('current_price'):
            upside = analyst_data.get('upside_to_target', 0)
            synthesis['key_insights'].append(
                f"Price target implies {upside:.1f}% {'upside' if upside > 0 else 'downside'}"
            )

        synthesis['key_insights'].append(
            f"Smart money score: {smart_money.get('smart_money_score', 0)}/10"
        )

        return synthesis

    def _extract_percentage(self, text: str) -> Optional[float]:
        """Extract percentage from text."""
        import re
        match = re.search(r'(\d+\.?\d*)%', text)
        if match:
            return float(match.group(1))
        return None

    def _extract_price_target(self, text: str, target_type: str) -> Optional[float]:
        """Extract price target from text."""
        import re

        if target_type == 'consensus':
            patterns = [
                r'consensus price target[:\s]+\$?(\d+\.?\d*)',
                r'average price target[:\s]+\$?(\d+\.?\d*)',
                r'target price[:\s]+\$?(\d+\.?\d*)'
            ]
        elif target_type == 'high':
            patterns = [r'high price target[:\s]+\$?(\d+\.?\d*)', r'highest target[:\s]+\$?(\d+\.?\d*)']
        else:  # low
            patterns = [r'low price target[:\s]+\$?(\d+\.?\d*)', r'lowest target[:\s]+\$?(\d+\.?\d*)']

        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                return float(match.group(1))

        return None

    def _extract_current_price(self, text: str) -> Optional[float]:
        """Extract current stock price from text."""
        import re
        patterns = [
            r'current price[:\s]+\$?(\d+\.?\d*)',
            r'trading at[:\s]+\$?(\d+\.?\d*)',
            r'stock price[:\s]+\$?(\d+\.?\d*)'
        ]

        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                return float(match.group(1))

        return None

    def _extract_num_analysts(self, text: str) -> Optional[int]:
        """Extract number of analysts covering the stock."""
        import re
        match = re.search(r'(\d+)\s+analyst', text, re.IGNORECASE)
        if match:
            return int(match.group(1))
        return None

    async def send_progress(self, message: str, progress: float):
        """Send progress update."""
        if self.request_id:
            await progress_tracker.send_update(self.request_id, {
                'agent': self.name,
                'message': message,
                'progress': progress
            })

    async def search_tavily(self, query: str) -> List[Dict]:
        """Search using Tavily API."""
        if not self.tavily_client:
            return []
        try:
            results = await self.tavily_client.search(query)
            return results.get('results', [])
        except Exception as e:
            logger.error(f"Tavily search error: {e}")
            return []

    async def qna_search_tavily(self, query: str) -> Dict:
        """QnA search using Tavily API."""
        if not self.tavily_client:
            return {}
        try:
            result = await self.tavily_client.qna_search(query)
            return result
        except Exception as e:
            logger.error(f"Tavily QnA search error: {e}")
            return {}

    def add_citation(self, url: str, title: str, content: str, relevance_score: float = 0.8):
        """Add a citation to the agent's citation list."""
        self.citations.append(Citation(
            url=url,
            title=title,
            content=content,
            relevance_score=relevance_score,
            published_date=datetime.utcnow().isoformat()
        ))
