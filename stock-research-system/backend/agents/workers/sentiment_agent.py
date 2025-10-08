"""Sentiment Analysis Agent - Analyzes market sentiment and news using Tavily"""

from typing import Dict, Any, List
import logging
from datetime import datetime, timedelta
from agents.base_agent import BaseFinancialAgent, AgentState
import re

logger = logging.getLogger(__name__)


class SentimentAgent(BaseFinancialAgent):
    """Agent for analyzing market sentiment and news"""

    def __init__(self, agent_id: str, agent_type: str, tavily_client=None):
        super().__init__(agent_id, agent_type, tavily_client)

    async def execute(self, context: Dict[str, Any]) -> AgentState:
        """Analyze market sentiment for specified stocks

        Args:
            context: Contains 'stock_symbols' and 'query' fields

        Returns:
            AgentState with sentiment analysis
        """
        try:
            symbols = context.get('stock_symbols', [])
            original_query = context.get('query', '')

            if not symbols:
                raise ValueError("No stock symbols provided")

            logger.info(f"Analyzing sentiment for {symbols}")

            # Collect sentiment data
            sentiment_data = {}

            for symbol in symbols:
                symbol_sentiment = await self._analyze_stock_sentiment(symbol)
                sentiment_data[symbol] = symbol_sentiment

            # Analyze overall market sentiment
            market_sentiment = await self._analyze_market_sentiment()

            # Prepare output
            output_data = {
                'stocks': sentiment_data,
                'market_sentiment': market_sentiment,
                'overall_sentiment_score': self._calculate_overall_sentiment(sentiment_data),
                'sentiment_summary': self._generate_sentiment_summary(sentiment_data),
                'timestamp': datetime.utcnow().isoformat(),
                'data_points': self._count_data_points(sentiment_data),
                'source_count': len(self.state.citations)
            }

            self.state.output_data = output_data
            self.state.confidence_score = self.calculate_confidence(output_data)

            logger.info(f"Successfully analyzed sentiment for {len(symbols)} symbols")
            return self.state

        except Exception as e:
            logger.error(f"Sentiment analysis failed: {str(e)}")
            self.state.error_message = str(e)
            self.state.status = "FAILED"
            return self.state

    async def _analyze_stock_sentiment(self, symbol: str) -> Dict[str, Any]:
        """Analyze sentiment for a single stock

        Args:
            symbol: Stock symbol

        Returns:
            Sentiment analysis dictionary
        """
        sentiment = {
            'symbol': symbol,
            'news_sentiment': {},
            'analyst_sentiment': {},
            'social_sentiment': {},
            'insider_activity': {},
            'institutional_flow': {},
            'momentum_indicators': {},
            'composite_score': 0
        }

        try:
            # Use QnA for immediate sentiment assessment
            sentiment_qna = f"What is the current market sentiment and analyst outlook for {symbol} stock today?"
            sentiment_answer = await self.qna_search_tavily(sentiment_qna)

            if sentiment_answer:
                sentiment['sentiment_overview'] = sentiment_answer

            # Search for recent news sentiment (focusing on latest)
            news_query = f"{symbol} stock news today latest 2024 2025 bullish bearish outlook"
            news_results = await self.search_tavily(news_query, search_depth="advanced", max_results=5)

            if news_results:
                sentiment['news_sentiment'] = await self._extract_news_sentiment(news_results, symbol)
                self.state.citations.extend(self.extract_citations(news_results))

            # Use QnA for analyst consensus
            analyst_qna = f"What is the current analyst consensus and price target for {symbol} stock?"
            analyst_answer = await self.qna_search_tavily(analyst_qna)

            if analyst_answer:
                sentiment['analyst_consensus'] = analyst_answer

            # Search for recent analyst ratings
            analyst_query = f"{symbol} latest analyst rating upgrade downgrade price target 2024 2025"
            analyst_results = await self.search_tavily(analyst_query, search_depth="basic", max_results=3)

            if analyst_results:
                sentiment['analyst_sentiment'] = await self._extract_analyst_sentiment(analyst_results, symbol)

                # Structure analyst_targets for frontend ExecutiveSummary component
                analyst_data = sentiment['analyst_sentiment']
                if analyst_data.get('average_target') or analyst_data.get('consensus'):
                    total_ratings = analyst_data['buy_ratings'] + analyst_data['hold_ratings'] + analyst_data['sell_ratings']
                    sentiment['analyst_targets'] = {
                        'analyst_consensus': analyst_data.get('consensus', 'Hold'),
                        'target_mean': analyst_data.get('average_target'),
                        'consensus_price_target': analyst_data.get('average_target'),
                        'number_of_analysts': total_ratings if total_ratings > 0 else None,
                        'upside_potential': None  # Will be calculated if we have current price
                    }

            # Search for social media sentiment with date focus
            social_query = f"{symbol} stock social media sentiment Reddit WallStreetBets trending today 2024 2025"
            social_results = await self.search_tavily(social_query, search_depth="basic", max_results=2)

            if social_results:
                sentiment['social_sentiment'] = await self._extract_social_sentiment(social_results, symbol)

            # Use QnA for insider activity summary
            insider_qna = f"What recent insider trading activity has occurred for {symbol} stock in 2024-2025?"
            insider_answer = await self.qna_search_tavily(insider_qna)

            if insider_answer:
                sentiment['insider_summary'] = insider_answer

            # Search for detailed insider trading activity
            insider_query = f"{symbol} insider trading latest 2024 2025 CEO CFO buying selling"
            insider_results = await self.search_tavily(insider_query, search_depth="basic", max_results=2)

            if insider_results:
                sentiment['insider_activity'] = await self._extract_insider_sentiment(insider_results, symbol)

            # Calculate composite sentiment score
            sentiment['composite_score'] = self._calculate_composite_sentiment(sentiment)

        except Exception as e:
            logger.error(f"Failed to analyze sentiment for {symbol}: {str(e)}")
            sentiment['error'] = str(e)

        return sentiment

    async def _analyze_market_sentiment(self) -> Dict[str, Any]:
        """Analyze overall market sentiment

        Args:
            None

        Returns:
            Market sentiment data
        """
        market_sentiment = {
            'overall_trend': None,
            'fear_greed_index': None,
            'market_breadth': {},
            'sector_sentiment': {},
            'economic_sentiment': {},
            'geopolitical_factors': []
        }

        try:
            # Use QnA for current market sentiment
            market_qna = "What is the current stock market sentiment, fear greed index, and VIX level today?"
            market_answer = await self.qna_search_tavily(market_qna)

            if market_answer:
                market_sentiment['market_overview'] = market_answer

            # Search for detailed market sentiment indicators
            market_query = "stock market sentiment today 2024 2025 fear greed index VIX volatility"
            market_results = await self.search_tavily(market_query, search_depth="basic", max_results=3)

            if market_results:
                market_sentiment.update(await self._extract_market_indicators(market_results))

            # Search for economic sentiment
            econ_query = "economic outlook inflation interest rates Fed GDP employment sentiment"
            econ_results = await self.search_tavily(econ_query, search_depth="basic", max_results=2)

            if econ_results:
                market_sentiment['economic_sentiment'] = await self._extract_economic_sentiment(econ_results)

        except Exception as e:
            logger.error(f"Failed to analyze market sentiment: {str(e)}")
            market_sentiment['error'] = str(e)

        return market_sentiment

    async def _extract_news_sentiment(self, results: List[Dict], symbol: str) -> Dict[str, Any]:
        """Extract news sentiment from search results

        Args:
            results: Tavily search results
            symbol: Stock symbol

        Returns:
            News sentiment dictionary
        """
        news_sentiment = {
            'positive_mentions': 0,
            'negative_mentions': 0,
            'neutral_mentions': 0,
            'key_topics': [],
            'recent_headlines': [],
            'sentiment_score': 0
        }

        positive_words = ['bullish', 'upgrade', 'beat', 'surge', 'rally', 'gain', 'rise', 'outperform', 
                         'strong', 'positive', 'growth', 'record', 'high', 'breakthrough', 'success']
        negative_words = ['bearish', 'downgrade', 'miss', 'fall', 'drop', 'decline', 'underperform',
                         'weak', 'negative', 'loss', 'low', 'concern', 'risk', 'warning', 'cut']

        for result in results:
            content = result.get('content', '').lower() + ' ' + result.get('title', '').lower()

            # Store headlines
            if result.get('title'):
                news_sentiment['recent_headlines'].append(result['title'][:100])

            # Count sentiment words
            positive_count = sum(1 for word in positive_words if word in content)
            negative_count = sum(1 for word in negative_words if word in content)

            if positive_count > negative_count:
                news_sentiment['positive_mentions'] += 1
            elif negative_count > positive_count:
                news_sentiment['negative_mentions'] += 1
            else:
                news_sentiment['neutral_mentions'] += 1

            # Extract key topics
            topics = re.findall(r'\b(earnings|revenue|guidance|merger|acquisition|product|launch|partnership|lawsuit|regulation)\b', content)
            news_sentiment['key_topics'].extend(topics[:3])

        # Calculate sentiment score (0-100)
        total = news_sentiment['positive_mentions'] + news_sentiment['negative_mentions'] + news_sentiment['neutral_mentions']
        if total > 0:
            positive_ratio = news_sentiment['positive_mentions'] / total
            negative_ratio = news_sentiment['negative_mentions'] / total
            news_sentiment['sentiment_score'] = int((positive_ratio - negative_ratio + 1) * 50)
        else:
            news_sentiment['sentiment_score'] = 50

        # Keep unique topics
        news_sentiment['key_topics'] = list(set(news_sentiment['key_topics']))[:5]

        return news_sentiment

    async def _extract_analyst_sentiment(self, results: List[Dict], symbol: str) -> Dict[str, Any]:
        """Extract analyst sentiment from search results

        Args:
            results: Tavily search results
            symbol: Stock symbol

        Returns:
            Analyst sentiment dictionary
        """
        analyst_sentiment = {
            'buy_ratings': 0,
            'hold_ratings': 0,
            'sell_ratings': 0,
            'average_target': None,
            'recent_changes': [],
            'consensus': None
        }

        # Collect all target prices found
        target_prices = []
        total_analysts = 0

        for result in results:
            content = result.get('content', '') + ' ' + result.get('title', '')

            # Extract ratings
            buy_match = re.findall(r'(\d+)\s*(?:buy|strong buy|outperform)', content, re.IGNORECASE)
            if buy_match:
                analyst_sentiment['buy_ratings'] = int(buy_match[0])
                total_analysts = max(total_analysts, int(buy_match[0]))

            hold_match = re.findall(r'(\d+)\s*(?:hold|neutral)', content, re.IGNORECASE)
            if hold_match:
                analyst_sentiment['hold_ratings'] = int(hold_match[0])
                total_analysts = max(total_analysts, int(hold_match[0]))

            sell_match = re.findall(r'(\d+)\s*(?:sell|underperform)', content, re.IGNORECASE)
            if sell_match:
                analyst_sentiment['sell_ratings'] = int(sell_match[0])
                total_analysts = max(total_analysts, int(sell_match[0]))

            # Extract target prices - multiple patterns
            # Pattern 1: "price target $XXX" or "target price: $XXX"
            target_match = re.search(r'(?:target|price target)[:\s]+\$?([0-9,]+\.?[0-9]*)', content, re.IGNORECASE)
            if target_match:
                try:
                    price = float(target_match.group(1).replace(',', ''))
                    target_prices.append(price)
                except:
                    pass

            # Pattern 2: "consensus price target" or "average target price"
            consensus_match = re.search(r'(?:consensus|average|mean)\s+(?:price\s+)?target[:\s]+\$?([0-9,]+\.?[0-9]*)', content, re.IGNORECASE)
            if consensus_match:
                try:
                    price = float(consensus_match.group(1).replace(',', ''))
                    target_prices.append(price)
                except:
                    pass

            # Pattern 3: "analyst target of $XXX"
            analyst_target_match = re.search(r'analyst\s+target\s+of\s+\$?([0-9,]+\.?[0-9]*)', content, re.IGNORECASE)
            if analyst_target_match:
                try:
                    price = float(analyst_target_match.group(1).replace(',', ''))
                    target_prices.append(price)
                except:
                    pass

            # Extract number of analysts
            analyst_count_match = re.search(r'(\d+)\s+analysts?', content, re.IGNORECASE)
            if analyst_count_match:
                try:
                    count = int(analyst_count_match.group(1))
                    total_analysts = max(total_analysts, count)
                except:
                    pass

            # Extract recent changes
            if 'upgrade' in content.lower():
                analyst_sentiment['recent_changes'].append('upgrade')
            if 'downgrade' in content.lower():
                analyst_sentiment['recent_changes'].append('downgrade')

        # Calculate average target price
        if target_prices:
            analyst_sentiment['average_target'] = sum(target_prices) / len(target_prices)

        # If no explicit analyst count found, use total ratings
        if total_analysts == 0:
            total_analysts = analyst_sentiment['buy_ratings'] + analyst_sentiment['hold_ratings'] + analyst_sentiment['sell_ratings']

        # Determine consensus
        total_ratings = analyst_sentiment['buy_ratings'] + analyst_sentiment['hold_ratings'] + analyst_sentiment['sell_ratings']
        if total_ratings > 0:
            buy_pct = analyst_sentiment['buy_ratings'] / total_ratings
            if buy_pct > 0.6:
                analyst_sentiment['consensus'] = 'Buy'
            elif buy_pct > 0.4:
                analyst_sentiment['consensus'] = 'Hold'
            else:
                analyst_sentiment['consensus'] = 'Sell'
        else:
            analyst_sentiment['consensus'] = 'Hold'  # Default to Hold if no ratings found

        return analyst_sentiment

    async def _extract_social_sentiment(self, results: List[Dict], symbol: str) -> Dict[str, Any]:
        """Extract social media sentiment from search results

        Args:
            results: Tavily search results
            symbol: Stock symbol

        Returns:
            Social sentiment dictionary
        """
        social_sentiment = {
            'trending': False,
            'mention_volume': 'normal',
            'sentiment_lean': 'neutral',
            'key_discussions': []
        }

        for result in results:
            content = result.get('content', '').lower() + ' ' + result.get('title', '').lower()

            # Check if trending
            if 'trending' in content or 'viral' in content or 'popular' in content:
                social_sentiment['trending'] = True

            # Estimate mention volume
            if 'high volume' in content or 'surge' in content or 'spike' in content:
                social_sentiment['mention_volume'] = 'high'
            elif 'low' in content or 'quiet' in content:
                social_sentiment['mention_volume'] = 'low'

            # Determine sentiment lean
            if 'bullish' in content or 'positive' in content or 'buy' in content:
                social_sentiment['sentiment_lean'] = 'positive'
            elif 'bearish' in content or 'negative' in content or 'sell' in content:
                social_sentiment['sentiment_lean'] = 'negative'

            # Extract key discussion topics
            topics = re.findall(r'discussing\s+(\w+)', content)
            social_sentiment['key_discussions'].extend(topics[:2])

        social_sentiment['key_discussions'] = list(set(social_sentiment['key_discussions']))[:3]

        return social_sentiment

    async def _extract_insider_sentiment(self, results: List[Dict], symbol: str) -> Dict[str, Any]:
        """Extract insider trading sentiment from search results

        Args:
            results: Tavily search results
            symbol: Stock symbol

        Returns:
            Insider sentiment dictionary
        """
        insider_sentiment = {
            'recent_buys': 0,
            'recent_sells': 0,
            'net_activity': 'neutral',
            'key_transactions': []
        }

        for result in results:
            content = result.get('content', '') + ' ' + result.get('title', '')

            # Count buy transactions
            buy_matches = re.findall(r'(?:bought|purchased|acquired)\s+([0-9,]+)\s+shares', content, re.IGNORECASE)
            insider_sentiment['recent_buys'] += len(buy_matches)

            # Count sell transactions
            sell_matches = re.findall(r'(?:sold|disposed)\s+([0-9,]+)\s+shares', content, re.IGNORECASE)
            insider_sentiment['recent_sells'] += len(sell_matches)

            # Extract key transactions
            exec_match = re.search(r'(CEO|CFO|CTO|President|Director)\s+(?:bought|sold)', content, re.IGNORECASE)
            if exec_match:
                insider_sentiment['key_transactions'].append(exec_match.group(0))

        # Determine net activity
        if insider_sentiment['recent_buys'] > insider_sentiment['recent_sells']:
            insider_sentiment['net_activity'] = 'buying'
        elif insider_sentiment['recent_sells'] > insider_sentiment['recent_buys']:
            insider_sentiment['net_activity'] = 'selling'

        return insider_sentiment

    async def _extract_market_indicators(self, results: List[Dict]) -> Dict[str, Any]:
        """Extract market sentiment indicators from search results

        Args:
            results: Tavily search results

        Returns:
            Market indicators dictionary
        """
        indicators = {
            'fear_greed_index': None,
            'vix_level': None,
            'put_call_ratio': None,
            'market_trend': None
        }

        for result in results:
            content = result.get('content', '') + ' ' + result.get('title', '')

            # Extract Fear & Greed Index
            fg_match = re.search(r'fear\s*(?:&|and)?\s*greed\s*(?:index)?[:\s]+(\d+)', content, re.IGNORECASE)
            if fg_match and not indicators['fear_greed_index']:
                try:
                    indicators['fear_greed_index'] = int(fg_match.group(1))
                except:
                    pass

            # Extract VIX
            vix_match = re.search(r'VIX[:\s]+([0-9.]+)', content, re.IGNORECASE)
            if vix_match and not indicators['vix_level']:
                try:
                    indicators['vix_level'] = float(vix_match.group(1))
                except:
                    pass

            # Extract Put/Call Ratio
            pc_match = re.search(r'put[\s/]call\s*ratio[:\s]+([0-9.]+)', content, re.IGNORECASE)
            if pc_match and not indicators['put_call_ratio']:
                try:
                    indicators['put_call_ratio'] = float(pc_match.group(1))
                except:
                    pass

            # Determine market trend
            if 'bull market' in content.lower() or 'uptrend' in content.lower():
                indicators['market_trend'] = 'bullish'
            elif 'bear market' in content.lower() or 'downtrend' in content.lower():
                indicators['market_trend'] = 'bearish'

        return indicators

    async def _extract_economic_sentiment(self, results: List[Dict]) -> Dict[str, Any]:
        """Extract economic sentiment from search results

        Args:
            results: Tavily search results

        Returns:
            Economic sentiment dictionary
        """
        economic = {
            'inflation_outlook': None,
            'interest_rate_outlook': None,
            'gdp_outlook': None,
            'employment_outlook': None,
            'overall_economic_sentiment': 'neutral'
        }

        positive_count = 0
        negative_count = 0

        for result in results:
            content = result.get('content', '').lower()

            # Inflation outlook
            if 'inflation' in content:
                if 'rising' in content or 'high' in content or 'concern' in content:
                    economic['inflation_outlook'] = 'concerning'
                    negative_count += 1
                elif 'cooling' in content or 'easing' in content or 'stable' in content:
                    economic['inflation_outlook'] = 'improving'
                    positive_count += 1

            # Interest rate outlook
            if 'interest rate' in content or 'fed' in content:
                if 'raise' in content or 'hike' in content:
                    economic['interest_rate_outlook'] = 'rising'
                    negative_count += 1
                elif 'cut' in content or 'lower' in content or 'pause' in content:
                    economic['interest_rate_outlook'] = 'easing'
                    positive_count += 1

            # GDP outlook
            if 'gdp' in content or 'growth' in content:
                if 'strong' in content or 'robust' in content or 'accelerat' in content:
                    economic['gdp_outlook'] = 'positive'
                    positive_count += 1
                elif 'slow' in content or 'recession' in content or 'contract' in content:
                    economic['gdp_outlook'] = 'negative'
                    negative_count += 1

            # Employment outlook
            if 'employment' in content or 'jobs' in content or 'unemployment' in content:
                if 'strong' in content or 'low unemployment' in content or 'job gains' in content:
                    economic['employment_outlook'] = 'positive'
                    positive_count += 1
                elif 'layoffs' in content or 'rising unemployment' in content or 'job cuts' in content:
                    economic['employment_outlook'] = 'negative'
                    negative_count += 1

        # Determine overall economic sentiment
        if positive_count > negative_count:
            economic['overall_economic_sentiment'] = 'positive'
        elif negative_count > positive_count:
            economic['overall_economic_sentiment'] = 'negative'

        return economic

    def _calculate_composite_sentiment(self, sentiment_data: Dict[str, Any]) -> float:
        """Calculate composite sentiment score for a stock

        Args:
            sentiment_data: All sentiment data for a stock

        Returns:
            Composite score between 0 and 100
        """
        score = 50  # Neutral baseline

        # Weight different sentiment sources
        weights = {
            'news': 0.3,
            'analyst': 0.3,
            'social': 0.15,
            'insider': 0.25
        }

        # News sentiment contribution
        if 'news_sentiment' in sentiment_data and 'sentiment_score' in sentiment_data['news_sentiment']:
            news_score = sentiment_data['news_sentiment']['sentiment_score']
            score += (news_score - 50) * weights['news']

        # Analyst sentiment contribution
        if 'analyst_sentiment' in sentiment_data and 'consensus' in sentiment_data['analyst_sentiment']:
            consensus = sentiment_data['analyst_sentiment']['consensus']
            if consensus == 'Buy':
                score += 20 * weights['analyst']
            elif consensus == 'Sell':
                score -= 20 * weights['analyst']

        # Social sentiment contribution
        if 'social_sentiment' in sentiment_data and 'sentiment_lean' in sentiment_data['social_sentiment']:
            lean = sentiment_data['social_sentiment']['sentiment_lean']
            if lean == 'positive':
                score += 15 * weights['social']
            elif lean == 'negative':
                score -= 15 * weights['social']

        # Insider sentiment contribution
        if 'insider_activity' in sentiment_data and 'net_activity' in sentiment_data['insider_activity']:
            activity = sentiment_data['insider_activity']['net_activity']
            if activity == 'buying':
                score += 25 * weights['insider']
            elif activity == 'selling':
                score -= 25 * weights['insider']

        return max(0, min(100, score))

    def _calculate_overall_sentiment(self, sentiment_data: Dict[str, Any]) -> float:
        """Calculate overall sentiment across all stocks

        Args:
            sentiment_data: All sentiment data

        Returns:
            Overall sentiment score between 0 and 100
        """
        scores = []
        for symbol, data in sentiment_data.items():
            if isinstance(data, dict) and 'composite_score' in data:
                scores.append(data['composite_score'])

        return sum(scores) / len(scores) if scores else 50

    def _generate_sentiment_summary(self, sentiment_data: Dict[str, Any]) -> str:
        """Generate a summary of sentiment analysis

        Args:
            sentiment_data: All sentiment data

        Returns:
            Summary string
        """
        overall_score = self._calculate_overall_sentiment(sentiment_data)

        if overall_score > 70:
            return "Strong positive sentiment across analyzed stocks"
        elif overall_score > 55:
            return "Moderately positive sentiment with some optimism"
        elif overall_score > 45:
            return "Neutral to mixed sentiment in the market"
        elif overall_score > 30:
            return "Moderately negative sentiment with caution advised"
        else:
            return "Strong negative sentiment suggesting risk-off environment"

    def _count_data_points(self, data: Dict[str, Any]) -> int:
        """Count non-null data points

        Args:
            data: Data dictionary

        Returns:
            Number of non-null data points
        """
        count = 0

        def count_dict(d):
            nonlocal count
            for value in d.values():
                if value is not None:
                    if isinstance(value, dict):
                        count_dict(value)
                    elif isinstance(value, (list, tuple)):
                        count += len(value)
                    else:
                        count += 1

        count_dict(data)
        return count