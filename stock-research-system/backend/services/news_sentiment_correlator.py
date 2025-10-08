"""
News-Sentiment Correlation Service
Links sentiment scores with specific news events to identify sentiment drivers
"""

import logging
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime, timedelta
import asyncio
from dataclasses import dataclass, asdict
import json

from langchain_openai import ChatOpenAI
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)


@dataclass
class NewsArticle:
    """Individual news article with metadata"""
    title: str
    summary: str
    url: str
    source: str
    published: str
    relevance_score: float

    # Sentiment-specific fields (populated by analysis)
    sentiment: Optional[str] = None  # bullish/neutral/bearish
    sentiment_score: Optional[float] = None  # -1 to 1
    sentiment_confidence: Optional[float] = None  # 0 to 1
    key_points: Optional[List[str]] = None
    impact_level: Optional[str] = None  # high/medium/low


@dataclass
class SentimentDriver:
    """News article identified as a sentiment driver"""
    article: NewsArticle
    impact_weight: float  # 0-1, contribution to overall sentiment
    driver_type: str  # catalyst/risk/neutral
    reasoning: str  # Why this news impacts sentiment


@dataclass
class SentimentTimeline:
    """Timeline entry mapping news to sentiment"""
    timestamp: datetime
    news_articles: List[NewsArticle]
    aggregate_sentiment_score: float
    sentiment_label: str  # bullish/neutral/bearish
    volume: int  # number of articles


class ArticleSentimentAnalysis(BaseModel):
    """Structured output from LLM sentiment extraction"""
    sentiment: str = Field(description="Article sentiment: bullish/neutral/bearish")
    sentiment_score: float = Field(description="Sentiment score -1 to 1", ge=-1, le=1)
    confidence: float = Field(description="Confidence 0-1", ge=0, le=1)
    key_points: List[str] = Field(description="Key points that drive sentiment")
    impact_level: str = Field(description="Impact level: high/medium/low")
    reasoning: str = Field(description="Brief explanation of sentiment")


class NewsSentimentCorrelator:
    """
    Correlates news articles with sentiment scores to identify drivers

    Architecture:
    1. Extract sentiment from each news article (title + content)
    2. Calculate article-level sentiment scores
    3. Aggregate to overall sentiment with source attribution
    4. Identify top sentiment drivers (most impactful articles)
    5. Build timeline of sentiment aligned with news events

    LLM Usage:
    - Uses GPT-3.5 for cost-efficient article-level sentiment extraction
    - Batch processing where possible to minimize API calls
    - Structured output with Pydantic for reliable parsing
    """

    def __init__(self, llm: ChatOpenAI = None):
        """
        Initialize correlator

        Args:
            llm: LangChain LLM for sentiment analysis (defaults to GPT-3.5)
        """
        self.llm = llm or ChatOpenAI(
            model="gpt-3.5-turbo",
            temperature=0.1,  # Low temperature for consistent sentiment analysis
            max_tokens=400
        )

    async def correlate(
        self,
        news_articles: List[Dict[str, Any]],
        symbol: str,
        aggregate_sentiment: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Main correlation method - links news to sentiment

        Args:
            news_articles: List of news articles from Tavily API
            symbol: Stock symbol being analyzed
            aggregate_sentiment: Optional pre-calculated aggregate sentiment

        Returns:
            Dict with:
                - article_sentiments: List of NewsArticle with sentiment scores
                - sentiment_drivers: Top 3-5 articles driving sentiment
                - sentiment_timeline: Chronological view of sentiment evolution
                - aggregate_sentiment: Overall sentiment with attribution
                - correlation_metadata: Stats about the correlation
        """
        if not news_articles:
            logger.warning(f"[NewsSentimentCorrelator] No news articles for {symbol}")
            return self._empty_result(symbol)

        logger.info(f"[NewsSentimentCorrelator] Correlating {len(news_articles)} articles for {symbol}")

        try:
            # Step 1: Extract sentiment from each article
            article_sentiments = await self._analyze_article_sentiments(news_articles, symbol)

            # Step 2: Identify sentiment drivers (most impactful articles)
            sentiment_drivers = self._identify_sentiment_drivers(article_sentiments)

            # Step 3: Build sentiment timeline
            sentiment_timeline = self._build_sentiment_timeline(article_sentiments)

            # Step 4: Calculate aggregate sentiment with attribution
            attributed_sentiment = self._calculate_attributed_sentiment(
                article_sentiments,
                sentiment_drivers,
                aggregate_sentiment
            )

            # Step 5: Generate correlation insights
            insights = self._generate_insights(
                article_sentiments,
                sentiment_drivers,
                sentiment_timeline
            )

            result = {
                'symbol': symbol,
                'article_sentiments': [asdict(a) for a in article_sentiments],
                'sentiment_drivers': [asdict(d) for d in sentiment_drivers],
                'sentiment_timeline': [self._serialize_timeline_entry(e) for e in sentiment_timeline],
                'aggregate_sentiment': attributed_sentiment,
                'insights': insights,
                'correlation_metadata': {
                    'total_articles': len(news_articles),
                    'articles_analyzed': len(article_sentiments),
                    'drivers_identified': len(sentiment_drivers),
                    'timeline_points': len(sentiment_timeline),
                    'timestamp': datetime.utcnow().isoformat()
                }
            }

            logger.info(
                f"[NewsSentimentCorrelator] Correlation complete: "
                f"{len(sentiment_drivers)} drivers identified, "
                f"overall sentiment: {attributed_sentiment['label']}"
            )

            return result

        except Exception as e:
            logger.error(f"[NewsSentimentCorrelator] Correlation failed: {e}", exc_info=True)
            return self._error_result(symbol, str(e))

    async def _analyze_article_sentiments(
        self,
        news_articles: List[Dict[str, Any]],
        symbol: str
    ) -> List[NewsArticle]:
        """
        Extract sentiment from each article using LLM

        Uses batch processing to minimize API calls
        """
        article_objects = []

        # Convert raw articles to NewsArticle objects
        for article in news_articles:
            article_objects.append(NewsArticle(
                title=article.get('title', ''),
                summary=article.get('summary', article.get('content', ''))[:300],
                url=article.get('url', ''),
                source=article.get('source', 'Unknown'),
                published=article.get('published', datetime.utcnow().isoformat()),
                relevance_score=article.get('relevance_score', 0.5)
            ))

        # Analyze sentiment for each article (in parallel)
        tasks = [
            self._analyze_single_article(article, symbol)
            for article in article_objects
        ]

        analyzed_articles = await asyncio.gather(*tasks, return_exceptions=True)

        # Filter out failures
        valid_articles = [
            art for art in analyzed_articles
            if isinstance(art, NewsArticle) and art.sentiment is not None
        ]

        logger.info(f"[NewsSentimentCorrelator] Analyzed {len(valid_articles)}/{len(article_objects)} articles")
        return valid_articles

    async def _analyze_single_article(self, article: NewsArticle, symbol: str) -> NewsArticle:
        """
        Analyze sentiment for a single article using LLM
        """
        try:
            prompt = f"""Analyze the sentiment of this news article about ${symbol}:

TITLE: {article.title}

SUMMARY: {article.summary}

SOURCE: {article.source}

Provide a structured sentiment analysis:
1. Overall sentiment (bullish/neutral/bearish)
2. Sentiment score (-1=very bearish, 0=neutral, 1=very bullish)
3. Confidence in your analysis (0-1)
4. Key points that drive the sentiment (2-3 points)
5. Impact level (high/medium/low) - how much this news matters
6. Brief reasoning for the sentiment

Return as JSON:
{{
    "sentiment": "bullish|neutral|bearish",
    "sentiment_score": -1 to 1,
    "confidence": 0 to 1,
    "key_points": ["point1", "point2"],
    "impact_level": "high|medium|low",
    "reasoning": "brief explanation"
}}"""

            response = await self.llm.ainvoke(prompt)

            # Parse JSON response
            try:
                data = json.loads(response.content)
                analysis = ArticleSentimentAnalysis(**data)

                # Populate article with sentiment data
                article.sentiment = analysis.sentiment
                article.sentiment_score = analysis.sentiment_score
                article.sentiment_confidence = analysis.confidence
                article.key_points = analysis.key_points
                article.impact_level = analysis.impact_level

                return article

            except json.JSONDecodeError:
                logger.warning(f"[NewsSentimentCorrelator] Failed to parse LLM response for article: {article.title[:50]}")
                # Use fallback sentiment analysis
                return self._fallback_article_sentiment(article)

        except Exception as e:
            logger.error(f"[NewsSentimentCorrelator] Failed to analyze article: {e}")
            return self._fallback_article_sentiment(article)

    def _fallback_article_sentiment(self, article: NewsArticle) -> NewsArticle:
        """
        Rule-based fallback when LLM analysis fails
        """
        text = f"{article.title} {article.summary}".lower()

        # Keyword-based sentiment
        bullish_keywords = ['beat', 'exceed', 'upgrade', 'surge', 'rally', 'growth',
                           'positive', 'strong', 'buy', 'acquisition', 'innovation']
        bearish_keywords = ['miss', 'decline', 'downgrade', 'plunge', 'warning',
                           'negative', 'weak', 'sell', 'lawsuit', 'investigation']

        bull_count = sum(1 for kw in bullish_keywords if kw in text)
        bear_count = sum(1 for kw in bearish_keywords if kw in text)

        if bull_count > bear_count + 1:
            sentiment = "bullish"
            score = 0.6
        elif bear_count > bull_count + 1:
            sentiment = "bearish"
            score = -0.6
        else:
            sentiment = "neutral"
            score = 0.0

        article.sentiment = sentiment
        article.sentiment_score = score
        article.sentiment_confidence = 0.4  # Lower confidence for fallback
        article.key_points = ["Automated analysis"]
        article.impact_level = "medium"

        return article

    def _identify_sentiment_drivers(self, articles: List[NewsArticle]) -> List[SentimentDriver]:
        """
        Identify top articles that drive overall sentiment

        Criteria:
        - High impact level
        - Strong sentiment (positive or negative)
        - High confidence
        - Recent publication
        """
        drivers = []

        # Calculate impact weight for each article
        for article in articles:
            if article.sentiment_score is None:
                continue

            # Weight factors
            impact_weight = 0.0

            # 1. Sentiment strength (absolute value)
            sentiment_strength = abs(article.sentiment_score)
            impact_weight += sentiment_strength * 0.4

            # 2. Confidence
            impact_weight += (article.sentiment_confidence or 0.5) * 0.3

            # 3. Impact level
            impact_level_weights = {'high': 1.0, 'medium': 0.6, 'low': 0.3}
            impact_weight += impact_level_weights.get(article.impact_level, 0.5) * 0.2

            # 4. Relevance score
            impact_weight += (article.relevance_score or 0.5) * 0.1

            # Determine driver type
            if article.sentiment_score > 0.3:
                driver_type = "catalyst"
            elif article.sentiment_score < -0.3:
                driver_type = "risk"
            else:
                driver_type = "neutral"

            # Generate reasoning
            reasoning = self._generate_driver_reasoning(article)

            drivers.append(SentimentDriver(
                article=article,
                impact_weight=round(impact_weight, 3),
                driver_type=driver_type,
                reasoning=reasoning
            ))

        # Sort by impact weight and return top 5
        drivers.sort(key=lambda d: d.impact_weight, reverse=True)

        return drivers[:5]

    def _generate_driver_reasoning(self, article: NewsArticle) -> str:
        """Generate human-readable reasoning for why article is a driver"""
        impact = article.impact_level or "medium"
        sentiment = article.sentiment or "neutral"

        if sentiment == "bullish":
            return f"Strong positive catalyst with {impact} impact - drives bullish sentiment"
        elif sentiment == "bearish":
            return f"Significant risk factor with {impact} impact - drives bearish sentiment"
        else:
            return f"Neutral news with {impact} impact - balanced perspective"

    def _build_sentiment_timeline(self, articles: List[NewsArticle]) -> List[SentimentTimeline]:
        """
        Build chronological timeline of sentiment aligned with news

        Groups articles by time period (e.g., daily) and calculates aggregate sentiment
        """
        # Sort articles by published date
        sorted_articles = sorted(
            articles,
            key=lambda a: a.published if a.published else datetime.min.isoformat()
        )

        # Group by day
        timeline: Dict[str, List[NewsArticle]] = {}
        for article in sorted_articles:
            try:
                pub_date = datetime.fromisoformat(article.published.replace('Z', '+00:00'))
                day_key = pub_date.date().isoformat()
            except:
                day_key = datetime.utcnow().date().isoformat()

            if day_key not in timeline:
                timeline[day_key] = []
            timeline[day_key].append(article)

        # Create timeline entries
        timeline_entries = []
        for day_key, day_articles in sorted(timeline.items()):
            # Calculate aggregate sentiment for the day
            scores = [a.sentiment_score for a in day_articles if a.sentiment_score is not None]
            avg_score = sum(scores) / len(scores) if scores else 0

            if avg_score > 0.2:
                sentiment_label = "bullish"
            elif avg_score < -0.2:
                sentiment_label = "bearish"
            else:
                sentiment_label = "neutral"

            timeline_entries.append(SentimentTimeline(
                timestamp=datetime.fromisoformat(day_key),
                news_articles=day_articles,
                aggregate_sentiment_score=round(avg_score, 3),
                sentiment_label=sentiment_label,
                volume=len(day_articles)
            ))

        return timeline_entries

    def _calculate_attributed_sentiment(
        self,
        articles: List[NewsArticle],
        drivers: List[SentimentDriver],
        aggregate_sentiment: Optional[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Calculate overall sentiment with attribution to specific news
        """
        # Calculate weighted average sentiment
        total_weight = 0
        weighted_sum = 0

        for article in articles:
            if article.sentiment_score is not None and article.sentiment_confidence is not None:
                weight = article.sentiment_confidence * (article.relevance_score or 0.5)
                weighted_sum += article.sentiment_score * weight
                total_weight += weight

        avg_sentiment_score = weighted_sum / total_weight if total_weight > 0 else 0

        # Determine label
        if avg_sentiment_score > 0.2:
            sentiment_label = "bullish"
        elif avg_sentiment_score < -0.2:
            sentiment_label = "bearish"
        else:
            sentiment_label = "neutral"

        # Calculate confidence based on article agreement
        scores = [a.sentiment_score for a in articles if a.sentiment_score is not None]
        if len(scores) > 1:
            variance = sum((s - avg_sentiment_score) ** 2 for s in scores) / len(scores)
            confidence = max(0.3, 1.0 - variance)  # Lower variance = higher confidence
        else:
            confidence = 0.5

        # Source attribution
        source_breakdown = {}
        for article in articles:
            source = article.source
            if source not in source_breakdown:
                source_breakdown[source] = {
                    'count': 0,
                    'avg_sentiment': 0,
                    'articles': []
                }
            source_breakdown[source]['count'] += 1
            source_breakdown[source]['articles'].append(article.title)

        # Calculate avg sentiment per source
        for source in source_breakdown:
            source_articles = [a for a in articles if a.source == source and a.sentiment_score is not None]
            if source_articles:
                source_breakdown[source]['avg_sentiment'] = round(
                    sum(a.sentiment_score for a in source_articles) / len(source_articles),
                    3
                )

        return {
            'label': sentiment_label,
            'score': round(avg_sentiment_score, 3),
            'confidence': round(confidence, 3),
            'source_attribution': source_breakdown,
            'primary_drivers': [
                {
                    'title': d.article.title,
                    'source': d.article.source,
                    'sentiment': d.article.sentiment,
                    'impact_weight': d.impact_weight,
                    'reasoning': d.reasoning
                }
                for d in drivers[:3]  # Top 3 drivers
            ],
            'news_volume': len(articles),
            'analysis_method': 'LLM-powered article-level sentiment with weighted aggregation'
        }

    def _generate_insights(
        self,
        articles: List[NewsArticle],
        drivers: List[SentimentDriver],
        timeline: List[SentimentTimeline]
    ) -> Dict[str, Any]:
        """
        Generate insights about sentiment-news correlation
        """
        insights = {
            'sentiment_shifts': [],
            'consensus_level': None,
            'key_themes': [],
            'momentum': None
        }

        # 1. Detect sentiment shifts in timeline
        if len(timeline) > 1:
            for i in range(1, len(timeline)):
                prev_sentiment = timeline[i-1].aggregate_sentiment_score
                curr_sentiment = timeline[i].aggregate_sentiment_score

                if abs(curr_sentiment - prev_sentiment) > 0.4:
                    insights['sentiment_shifts'].append({
                        'date': timeline[i].timestamp.isoformat(),
                        'shift': 'positive' if curr_sentiment > prev_sentiment else 'negative',
                        'magnitude': round(abs(curr_sentiment - prev_sentiment), 2),
                        'trigger_news': [a.title for a in timeline[i].news_articles[:2]]
                    })

        # 2. Calculate consensus level
        scores = [a.sentiment_score for a in articles if a.sentiment_score is not None]
        if scores:
            avg = sum(scores) / len(scores)
            variance = sum((s - avg) ** 2 for s in scores) / len(scores)

            if variance < 0.1:
                insights['consensus_level'] = 'high'
            elif variance < 0.3:
                insights['consensus_level'] = 'moderate'
            else:
                insights['consensus_level'] = 'low'

        # 3. Extract key themes from drivers
        all_key_points = []
        for driver in drivers:
            if driver.article.key_points:
                all_key_points.extend(driver.article.key_points)

        insights['key_themes'] = list(set(all_key_points))[:5]

        # 4. Calculate momentum (recent vs older sentiment)
        if len(timeline) >= 2:
            recent_sentiment = sum(t.aggregate_sentiment_score for t in timeline[-2:]) / 2
            if recent_sentiment > 0.3:
                insights['momentum'] = 'bullish'
            elif recent_sentiment < -0.3:
                insights['momentum'] = 'bearish'
            else:
                insights['momentum'] = 'neutral'

        return insights

    def _serialize_timeline_entry(self, entry: SentimentTimeline) -> Dict[str, Any]:
        """Serialize timeline entry for JSON"""
        return {
            'timestamp': entry.timestamp.isoformat(),
            'sentiment_score': entry.aggregate_sentiment_score,
            'sentiment_label': entry.sentiment_label,
            'volume': entry.volume,
            'articles': [
                {
                    'title': a.title,
                    'source': a.source,
                    'sentiment': a.sentiment,
                    'sentiment_score': a.sentiment_score
                }
                for a in entry.news_articles
            ]
        }

    def _empty_result(self, symbol: str) -> Dict[str, Any]:
        """Return empty result when no articles"""
        return {
            'symbol': symbol,
            'article_sentiments': [],
            'sentiment_drivers': [],
            'sentiment_timeline': [],
            'aggregate_sentiment': {
                'label': 'neutral',
                'score': 0,
                'confidence': 0,
                'source_attribution': {},
                'primary_drivers': [],
                'news_volume': 0
            },
            'insights': {},
            'correlation_metadata': {
                'total_articles': 0,
                'articles_analyzed': 0,
                'drivers_identified': 0,
                'timeline_points': 0,
                'timestamp': datetime.utcnow().isoformat()
            }
        }

    def _error_result(self, symbol: str, error: str) -> Dict[str, Any]:
        """Return error result"""
        result = self._empty_result(symbol)
        result['error'] = error
        result['status'] = 'failed'
        return result
