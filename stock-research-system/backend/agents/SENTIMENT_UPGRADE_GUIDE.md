# Multi-Source Sentiment Analysis Upgrade Guide

## Overview

The sentiment analysis system has been upgraded from a single-source (Tavily-only) approach to a professional-grade multi-source aggregation system that combines data from:

- **Twitter/X API** (30% weight) - Real-time social sentiment
- **Reddit API** (20% weight) - Retail investor sentiment from r/wallstreetbets, r/stocks, etc.
- **News APIs** (30% weight) - Professional financial news with sentiment scoring
- **Tavily Search** (20% weight) - Fallback/supplementary data

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│           EnhancedSentimentTrackerAgent                     │
│  (Main agent with multi-source + legacy fallback)           │
└──────────────────┬──────────────────────────────────────────┘
                   │
                   ▼
        ┌──────────────────────┐
        │ SentimentAggregator  │
        │ (Weighted combiner)  │
        └──────────┬───────────┘
                   │
        ┌──────────┼───────────────────────┐
        │          │                       │
        ▼          ▼           ▼           ▼
┌─────────┐ ┌──────────┐ ┌────────┐ ┌──────────┐
│ Twitter │ │  Reddit  │ │  News  │ │  Tavily  │
│ Source  │ │  Source  │ │ Source │ │  Source  │
└─────────┘ └──────────┘ └────────┘ └──────────┘
```

## Components

### 1. Base Sentiment Source (`base_source.py`)
- Abstract base class for all sentiment sources
- Defines `SentimentData` model with normalized -1.0 to 1.0 scoring
- Common utilities: score normalization, sentiment classification, confidence calculation

### 2. Twitter Source (`twitter_source.py`)
- Uses Twitter API v2 for recent tweets
- Searches by cashtag ($AAPL) and hashtag
- Analyzes engagement metrics (likes, retweets)
- Keyword-based sentiment classification

### 3. Reddit Source (`reddit_source.py`)
- OAuth2 authentication with Reddit API
- Monitors multiple subreddits: wallstreetbets, stocks, investing, StockMarket
- Weights posts by upvote score (popular posts matter more)
- Extracts bull/bear arguments from post titles

### 4. News API Source (`news_api_source.py`)
- **Primary**: Alpha Vantage News Sentiment API (provides native sentiment scores)
- **Fallback**: NewsAPI.org (keyword-based sentiment analysis)
- Relevance-weighted sentiment aggregation
- Professional financial news focus

### 5. Tavily Source (`tavily_source.py`)
- Backward-compatible with existing Tavily integration
- Advanced search across financial platforms
- Used as supplementary source or fallback

### 6. Sentiment Aggregator (`sentiment_aggregator.py`)
- Combines data from all available sources
- Weighted average calculation (configurable weights)
- Handles source failures gracefully (automatic reweighting)
- Calculates divergence score (measures agreement/disagreement)
- Concurrent data fetching with timeout protection

### 7. Enhanced Sentiment Tracker Agent (`enhanced_sentiment_tracker_agent.py`)
- Drop-in replacement for `TavilySentimentTrackerAgent`
- Same interface: `track()` and `analyze()` methods
- Automatic fallback to legacy mode if all APIs unavailable
- Enhanced result format with source breakdown

## Configuration

### Environment Variables

Add to `.env`:

```bash
# Multi-Source Sentiment API Keys (Optional)
TWITTER_BEARER_TOKEN=your-twitter-bearer-token-here
REDDIT_CLIENT_ID=your-reddit-client-id-here
REDDIT_CLIENT_SECRET=your-reddit-client-secret-here
ALPHA_VANTAGE_API_KEY=your-alpha-vantage-api-key-here
NEWS_API_KEY=your-newsapi-key-here

# Sentiment Configuration
SENTIMENT_USE_MULTI_SOURCE=true
SENTIMENT_USE_LEGACY_FALLBACK=true

# Custom Weights (Optional)
SENTIMENT_WEIGHT_TWITTER=0.30
SENTIMENT_WEIGHT_REDDIT=0.20
SENTIMENT_WEIGHT_NEWS=0.30
SENTIMENT_WEIGHT_TAVILY=0.20
```

### Obtaining API Keys

#### Twitter/X API (Free Tier Available)
1. Go to https://developer.twitter.com/
2. Create a project and app
3. Enable "Read" permissions
4. Generate Bearer Token
5. Copy to `TWITTER_BEARER_TOKEN`

**Cost**: Free tier includes 500K tweets/month

#### Reddit API (Free)
1. Go to https://www.reddit.com/prefs/apps
2. Click "Create App" or "Create Another App"
3. Choose "script" type
4. Note the Client ID (under app name)
5. Note the Client Secret
6. Copy to `REDDIT_CLIENT_ID` and `REDDIT_CLIENT_SECRET`

**Cost**: Free (rate limited to 60 requests/minute)

#### Alpha Vantage (Recommended for News)
1. Go to https://www.alphavantage.co/support/#api-key
2. Claim free API key
3. Copy to `ALPHA_VANTAGE_API_KEY`

**Cost**: Free tier includes 25 requests/day (sufficient for sentiment analysis)

#### NewsAPI.org (Alternative)
1. Go to https://newsapi.org/register
2. Sign up for free account
3. Copy API key to `NEWS_API_KEY`

**Cost**: Free tier includes 100 requests/day

## Usage

### Basic Usage (Automatic Multi-Source)

```python
from agents.tavily_agents.enhanced_sentiment_tracker_agent import EnhancedSentimentTrackerAgent
from config import settings

# Initialize agent with all available API keys
agent = EnhancedSentimentTrackerAgent(
    tavily_api_key=settings.TAVILY_API_KEY,
    twitter_api_key=settings.TWITTER_BEARER_TOKEN,
    reddit_client_id=settings.REDDIT_CLIENT_ID,
    reddit_client_secret=settings.REDDIT_CLIENT_SECRET,
    alpha_vantage_key=settings.ALPHA_VANTAGE_API_KEY,
    news_api_key=settings.NEWS_API_KEY,
    use_legacy_fallback=True  # Falls back to Tavily-only if needed
)

# Analyze sentiment
result = await agent.analyze({
    'symbol': 'AAPL',
    'timeframe': '24h'
})

# Access results
print(f"Overall Sentiment: {result['aggregated_sentiment']['sentiment_label']}")
print(f"Confidence: {result['aggregated_sentiment']['confidence']}")
print(f"Sources Used: {result['aggregated_sentiment']['source_count']}")
print(f"Bull Arguments: {result['bull_arguments']}")
print(f"Bear Arguments: {result['bear_arguments']}")
```

### Custom Weights

```python
# Emphasize news over social media
custom_weights = {
    "twitter": 0.20,
    "reddit": 0.10,
    "news": 0.50,
    "tavily": 0.20
}

agent = EnhancedSentimentTrackerAgent(
    tavily_api_key=settings.TAVILY_API_KEY,
    twitter_api_key=settings.TWITTER_BEARER_TOKEN,
    custom_weights=custom_weights
)
```

### Legacy Mode (Tavily-Only)

```python
# Use original Tavily-only implementation
from agents.tavily_agents.sentiment_tracker_agent import TavilySentimentTrackerAgent

agent = TavilySentimentTrackerAgent(
    tavily_api_key=settings.TAVILY_API_KEY,
    llm=ChatOpenAI(model="gpt-3.5-turbo")
)
```

## Output Format

### Enhanced Result Structure

```json
{
  "agent": "EnhancedSentimentTrackerAgent",
  "symbol": "AAPL",
  "aggregated_sentiment": {
    "sentiment_score": 0.45,
    "sentiment_label": "bullish",
    "confidence": 0.82,
    "total_volume": 245,
    "source_count": 3,
    "divergence": 0.12
  },
  "source_breakdown": [
    {
      "source": "twitter",
      "weight": 0.30,
      "sentiment_score": 0.52,
      "sentiment_label": "bullish",
      "confidence": 0.85,
      "volume": 100,
      "top_topics": ["$AAPL twitter mentions"]
    },
    {
      "source": "news",
      "weight": 0.30,
      "sentiment_score": 0.38,
      "sentiment_label": "bullish",
      "confidence": 0.90,
      "volume": 75,
      "top_topics": ["Financial News", "Market Analysis"]
    },
    {
      "source": "tavily",
      "weight": 0.40,
      "sentiment_score": 0.42,
      "sentiment_label": "bullish",
      "confidence": 0.70,
      "volume": 70,
      "top_topics": ["Seeking Alpha", "Benzinga"]
    }
  ],
  "bull_arguments": [
    "Strong Q4 earnings beat expectations",
    "iPhone sales surging in China",
    "Services revenue at all-time high"
  ],
  "bear_arguments": [
    "Valuation concerns at 30x P/E",
    "Regulatory pressure in EU"
  ],
  "divergence_score": 0.05,
  "data_lineage": {
    "source_type": "Multi-Source Aggregation",
    "available_sources": ["twitter", "news", "tavily"],
    "unavailable_sources": ["reddit"],
    "aggregation_method": "Weighted Average",
    "weights": {
      "twitter": 0.30,
      "news": 0.30,
      "tavily": 0.40
    },
    "quality_tier": "Professional (3+ Sources)"
  },
  "timestamp": "2025-10-07T12:34:56.789Z",
  "status": "success"
}
```

## Fallback Behavior

The system has multiple fallback layers:

1. **Multi-Source → Available Sources**: If some APIs are unavailable, automatically reweights remaining sources
2. **Available Sources → Tavily Only**: If only Tavily is available, uses full weight
3. **Tavily → Legacy Agent**: If all sources fail, falls back to legacy `TavilySentimentTrackerAgent`
4. **Legacy → Error**: If everything fails, returns error result with neutral sentiment

## Performance Considerations

### Latency
- **Multi-source mode**: ~5-15 seconds (concurrent fetching)
- **Single source**: ~2-5 seconds
- **Legacy fallback**: ~3-8 seconds

### Rate Limits
- **Twitter**: 180 requests/15min (per app)
- **Reddit**: 60 requests/min (per app)
- **Alpha Vantage**: 25 requests/day (free), 75/min (premium)
- **NewsAPI**: 100 requests/day (free), 1000/day (developer)
- **Tavily**: Plan-dependent (no strict limits)

### Cost Optimization
- Enable caching for repeated queries (Redis)
- Use `timeframe` parameter to reduce API calls
- Consider upgrading to paid tiers for high-volume usage
- Monitor `source_count` to ensure multi-source coverage

## Testing

### Unit Tests

```bash
# Run tests for individual sources
pytest tests/test_sentiment_sources.py -v

# Test aggregator
pytest tests/test_sentiment_aggregator.py -v

# Test enhanced agent
pytest tests/test_enhanced_sentiment_agent.py -v
```

### Integration Tests

```python
import asyncio
from agents.tavily_agents.enhanced_sentiment_tracker_agent import EnhancedSentimentTrackerAgent

async def test_sentiment():
    agent = EnhancedSentimentTrackerAgent(
        tavily_api_key="your-key",
        twitter_api_key="your-twitter-key"
    )

    # Test with known stock
    result = await agent.analyze({'symbol': 'AAPL'})

    # Validate structure
    assert 'aggregated_sentiment' in result
    assert result['aggregated_sentiment']['source_count'] > 0
    assert -1.0 <= result['aggregated_sentiment']['sentiment_score'] <= 1.0

    print(f"✓ Sentiment: {result['aggregated_sentiment']['sentiment_label']}")
    print(f"✓ Sources: {result['aggregated_sentiment']['source_count']}")

asyncio.run(test_sentiment())
```

### Manual Testing Checklist

- [ ] Test with all APIs configured (4 sources)
- [ ] Test with only 2-3 APIs (verify reweighting)
- [ ] Test with only Tavily (verify fallback)
- [ ] Test with no APIs (verify legacy fallback)
- [ ] Test divergence calculation (sources disagree)
- [ ] Test with high-volume stock (AAPL, TSLA)
- [ ] Test with low-volume stock (small cap)
- [ ] Verify rate limiting doesn't cause failures
- [ ] Check response times (< 15 seconds target)
- [ ] Validate sentiment scores (-1.0 to 1.0)

## Monitoring

### Key Metrics

```python
# Monitor in production
result = await agent.analyze({'symbol': 'AAPL'})

# Track these metrics
metrics = {
    'source_count': result['aggregated_sentiment']['source_count'],
    'confidence': result['aggregated_sentiment']['confidence'],
    'divergence': result['aggregated_sentiment']['divergence'],
    'quality_tier': result['data_lineage']['quality_tier'],
    'response_time': result['timestamp']
}

# Alert if:
# - source_count < 2 (degraded coverage)
# - confidence < 0.5 (low quality data)
# - divergence > 0.5 (sources strongly disagree)
```

## Migration Guide

### Step 1: Update Environment Variables

Add new API keys to `.env` (see Configuration section)

### Step 2: Update Requirements

```bash
# Already included in requirements.txt
# - aiohttp (for async HTTP requests)
# - pydantic (for data models)
```

### Step 3: Update Agent Initialization

**Before**:
```python
from agents.tavily_agents.sentiment_tracker_agent import TavilySentimentTrackerAgent

agent = TavilySentimentTrackerAgent(
    tavily_api_key=settings.TAVILY_API_KEY,
    llm=llm
)
```

**After**:
```python
from agents.tavily_agents.enhanced_sentiment_tracker_agent import EnhancedSentimentTrackerAgent

agent = EnhancedSentimentTrackerAgent(
    tavily_api_key=settings.TAVILY_API_KEY,
    twitter_api_key=settings.TWITTER_BEARER_TOKEN,
    reddit_client_id=settings.REDDIT_CLIENT_ID,
    reddit_client_secret=settings.REDDIT_CLIENT_SECRET,
    alpha_vantage_key=settings.ALPHA_VANTAGE_API_KEY,
    news_api_key=settings.NEWS_API_KEY,
    use_legacy_fallback=True  # Ensures backward compatibility
)
```

### Step 4: Update Result Handling (Optional)

The enhanced agent returns additional fields. Update your code to use them:

```python
# New fields available
result['aggregated_sentiment']['source_count']  # Number of sources used
result['source_breakdown']  # Individual source results
result['data_lineage']['quality_tier']  # Data quality indicator
```

### Step 5: Test Thoroughly

Run integration tests to ensure backward compatibility:

```bash
python test_sentiment_upgrade.py
```

## Troubleshooting

### "No sentiment sources available"
- Check API keys in `.env`
- Verify API keys are valid (test manually)
- Check network connectivity
- Review rate limits (may be temporarily exceeded)

### Low Source Count (< 2)
- Some API keys may be invalid
- Rate limits may be hit
- Check logs for specific API errors

### High Divergence (> 0.5)
- Normal for controversial stocks
- May indicate recent news event
- Consider weighting professional news higher

### Slow Response Times (> 20s)
- Enable Redis caching
- Reduce `max_results` in source configs
- Check network latency to APIs
- Consider async optimization

## Trade-offs and Limitations

### Advantages
✅ More comprehensive sentiment coverage
✅ Source diversity reduces bias
✅ Professional news sentiment (Alpha Vantage)
✅ Real-time social media sentiment
✅ Automatic fallback ensures reliability

### Limitations
❌ More API dependencies (more points of failure)
❌ Increased latency (5-15s vs 3-8s)
❌ Rate limit complexity (multiple APIs to manage)
❌ Free tier limits may be restrictive
❌ Requires multiple API key setups

### When to Use Legacy Mode
- High-frequency queries (> 100/hour)
- Cost-sensitive applications
- Simpler deployment requirements
- Don't need source attribution
- Tavily-only data is sufficient

## Support

For issues or questions:
1. Check logs for specific API errors
2. Review API documentation (links in Configuration section)
3. Test individual sources in isolation
4. Enable debug logging: `LOG_LEVEL=DEBUG`
5. File issue with error logs and configuration

## Future Enhancements

Potential improvements:
- [ ] Machine learning sentiment model (trained on historical data)
- [ ] StockTwits API integration (dedicated stock social network)
- [ ] Bloomberg Terminal integration (institutional sentiment)
- [ ] Options flow sentiment (puts/calls ratio)
- [ ] Insider trading sentiment (Form 4 filings)
- [ ] Google Trends integration (retail interest)
- [ ] Historical sentiment tracking (time series)
- [ ] Sentiment change alerts (sudden shifts)
