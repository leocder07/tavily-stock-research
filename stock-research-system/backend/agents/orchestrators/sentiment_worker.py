"""Sentiment Research Worker for Research Division"""

from typing import Dict, Any, List
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


class SentimentResearchWorker:
    """Specialized worker for sentiment analysis"""

    def __init__(self, tavily_client):
        self.tavily = tavily_client
        self.name = "Sentiment Researcher"

    async def execute(self, state: Dict) -> Dict[str, Any]:
        """Execute sentiment research"""
        task = state.get('task', {})
        if isinstance(task, dict):
            symbols = task.get('symbols', [])
        else:
            symbols = task.symbols if hasattr(task, 'symbols') else []

        logger.info(f"Sentiment Researcher analyzing sentiment for {symbols}")

        results = {
            'worker_type': 'sentiment_researcher',
            'symbols': symbols,
            'sentiment_data': {},
            'sentiment_summary': None,
            'citations': []
        }

        # Search for sentiment using Tavily
        for symbol in symbols[:2]:  # Limit API calls
            try:
                # Search for sentiment and social media buzz
                search_results = await self.tavily.search(
                    query=f"{symbol} stock sentiment analysis social media",
                    search_depth="basic",
                    max_results=3
                )

                sentiment_score = 0
                sentiment_count = 0

                for result in search_results.get('results', []):
                    content = result.get('content', '').lower()

                    # Basic sentiment analysis (in production, use proper NLP)
                    positive_words = ['bullish', 'buy', 'positive', 'growth', 'strong', 'upgrade']
                    negative_words = ['bearish', 'sell', 'negative', 'decline', 'weak', 'downgrade']

                    pos_count = sum(1 for word in positive_words if word in content)
                    neg_count = sum(1 for word in negative_words if word in content)

                    if pos_count > neg_count:
                        sentiment_score += 1
                    elif neg_count > pos_count:
                        sentiment_score -= 1

                    sentiment_count += 1

                # Calculate average sentiment
                avg_sentiment = sentiment_score / sentiment_count if sentiment_count > 0 else 0

                sentiment_label = "Neutral"
                if avg_sentiment > 0.5:
                    sentiment_label = "Bullish"
                elif avg_sentiment < -0.5:
                    sentiment_label = "Bearish"

                results['sentiment_data'][symbol] = {
                    'sentiment': sentiment_label,
                    'score': avg_sentiment,
                    'sources_analyzed': sentiment_count
                }

            except Exception as e:
                logger.error(f"Sentiment analysis error for {symbol}: {e}")
                results['sentiment_data'][symbol] = {
                    'sentiment': 'Unknown',
                    'score': 0,
                    'error': str(e)
                }

        # Generate summary
        if results['sentiment_data']:
            sentiments = [data.get('sentiment', 'Unknown') for data in results['sentiment_data'].values()]
            bullish_count = sentiments.count('Bullish')
            bearish_count = sentiments.count('Bearish')

            if bullish_count > bearish_count:
                results['sentiment_summary'] = "Overall market sentiment is BULLISH"
            elif bearish_count > bullish_count:
                results['sentiment_summary'] = "Overall market sentiment is BEARISH"
            else:
                results['sentiment_summary'] = "Market sentiment is MIXED/NEUTRAL"

        results['data_quality'] = 'recent'
        return results