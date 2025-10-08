# Multi-Source Sentiment Analysis Architecture

## System Architecture

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                        STOCK RESEARCH SYSTEM                                │
│                                                                             │
│  ┌───────────────────────────────────────────────────────────────────────┐ │
│  │                    LangGraph Workflow Orchestrator                    │ │
│  └─────────────────────────────────┬─────────────────────────────────────┘ │
│                                    │                                        │
│                                    ▼                                        │
│  ┌───────────────────────────────────────────────────────────────────────┐ │
│  │              EnhancedSentimentTrackerAgent                            │ │
│  │  • track(context) / analyze(context)                                  │ │
│  │  • Backward compatible with TavilySentimentTrackerAgent               │ │
│  │  • Automatic multi-source aggregation                                 │ │
│  │  • Legacy fallback if APIs unavailable                                │ │
│  └─────────────────────────────────┬─────────────────────────────────────┘ │
│                                    │                                        │
│                                    ▼                                        │
│  ┌───────────────────────────────────────────────────────────────────────┐ │
│  │                    SentimentAggregator                                │ │
│  │  • aggregate_sentiment(symbol, timeframe)                             │ │
│  │  • Weighted combination: Twitter(30%) + Reddit(20%) +                 │ │
│  │    News(30%) + Tavily(20%)                                            │ │
│  │  • Concurrent fetching with timeout (30s)                             │ │
│  │  • Automatic reweighting on source failures                           │ │
│  │  • Divergence calculation (measures agreement)                        │ │
│  └─────────────┬──────────────┬──────────────┬──────────────┬────────────┘ │
│                │              │              │              │              │
│                ▼              ▼              ▼              ▼              │
│  ┌──────────────────┐ ┌─────────────┐ ┌────────────┐ ┌─────────────┐    │
│  │ TwitterSentiment │ │   Reddit    │ │   News     │ │   Tavily    │    │
│  │     Source       │ │   Sentiment │ │  Sentiment │ │  Sentiment  │    │
│  │                  │ │   Source    │ │   Source   │ │   Source    │    │
│  │ • fetch_sentiment│ │ • OAuth2    │ │ • Alpha    │ │ • Advanced  │    │
│  │ • is_available() │ │ • Multi-sub │ │   Vantage  │ │   Search    │    │
│  │ • Twitter API v2 │ │ • Upvote    │ │ • NewsAPI  │ │ • Multi-    │    │
│  │ • Cashtags       │ │   weighted  │ │ • Native   │ │   platform  │    │
│  │ • Engagement     │ │ • WSB, etc. │ │   scores   │ │ • Fallback  │    │
│  └────────┬─────────┘ └──────┬──────┘ └─────┬──────┘ └──────┬──────┘    │
│           │                  │              │              │              │
│           └──────────────────┴──────────────┴──────────────┘              │
│                                    │                                        │
│                                    ▼                                        │
│  ┌───────────────────────────────────────────────────────────────────────┐ │
│  │                     BaseSentimentSource                               │ │
│  │  • Abstract base class                                                │ │
│  │  • SentimentData model (normalized -1.0 to 1.0)                       │ │
│  │  • Common utilities: normalize_score(), classify_sentiment()          │ │
│  └───────────────────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────────────────────┘

                                    │
                                    ▼
                        ┌───────────────────────┐
                        │   External APIs       │
                        ├───────────────────────┤
                        │ • Twitter API v2      │
                        │ • Reddit OAuth2       │
                        │ • Alpha Vantage       │
                        │ • NewsAPI.org         │
                        │ • Tavily Search       │
                        └───────────────────────┘
```

## Data Flow

```
┌────────────┐
│   Query    │
│ {symbol:   │
│  "AAPL"}   │
└─────┬──────┘
      │
      ▼
┌────────────────────────────────────────────────────────┐
│ Step 1: Check Available Sources                       │
│ - Test API connectivity (parallel)                    │
│ - Timeout: 10 seconds                                 │
│ Result: [twitter, news, tavily] (reddit unavailable)  │
└─────┬──────────────────────────────────────────────────┘
      │
      ▼
┌────────────────────────────────────────────────────────┐
│ Step 2: Fetch Sentiment from Available Sources        │
│ - Concurrent requests (asyncio.gather)                │
│ - Timeout: 30 seconds                                 │
│                                                        │
│   Twitter API ────────────┐                           │
│   News API (Alpha V.) ────┼─→ Parallel Fetch         │
│   Tavily Search ──────────┘                           │
│                                                        │
│ Results:                                              │
│ - Twitter: score=0.52, volume=100, confidence=0.85   │
│ - News: score=0.38, volume=75, confidence=0.90       │
│ - Tavily: score=0.42, volume=70, confidence=0.70     │
└─────┬──────────────────────────────────────────────────┘
      │
      ▼
┌────────────────────────────────────────────────────────┐
│ Step 3: Reweight Based on Available Sources           │
│ Original weights: Twitter(30%), Reddit(20%),          │
│                   News(30%), Tavily(20%)              │
│                                                        │
│ Reddit unavailable → Reweight remaining:              │
│ - Twitter: 30% / 80% = 0.375 (37.5%)                 │
│ - News: 30% / 80% = 0.375 (37.5%)                    │
│ - Tavily: 20% / 80% = 0.25 (25%)                     │
└─────┬──────────────────────────────────────────────────┘
      │
      ▼
┌────────────────────────────────────────────────────────┐
│ Step 4: Compute Weighted Average                      │
│ weighted_score = (0.52 × 0.375) + (0.38 × 0.375) +   │
│                  (0.42 × 0.25)                        │
│                = 0.195 + 0.1425 + 0.105               │
│                = 0.4425 ≈ 0.44                        │
│                                                        │
│ weighted_confidence = (0.85 × 0.375) + (0.90 × 0.375)│
│                       + (0.70 × 0.25)                 │
│                     = 0.831 ≈ 0.83                    │
└─────┬──────────────────────────────────────────────────┘
      │
      ▼
┌────────────────────────────────────────────────────────┐
│ Step 5: Calculate Divergence                          │
│ scores = [0.52, 0.38, 0.42]                          │
│ mean = 0.44                                           │
│ variance = [(0.52-0.44)², (0.38-0.44)², (0.42-0.44)²]│
│          = [0.0064, 0.0036, 0.0004] = 0.00347        │
│ std_dev = √0.00347 = 0.059                           │
│ divergence = min(0.059 / 2.0, 1.0) = 0.029 (low)    │
│                                                        │
│ Low divergence → sources agree (high confidence)      │
└─────┬──────────────────────────────────────────────────┘
      │
      ▼
┌────────────────────────────────────────────────────────┐
│ Step 6: Classify & Format Result                      │
│ sentiment_score = 0.44 → "bullish" (> 0.15)          │
│                                                        │
│ Return:                                               │
│ {                                                     │
│   "aggregated_sentiment": {                          │
│     "sentiment_score": 0.44,                         │
│     "sentiment_label": "bullish",                    │
│     "confidence": 0.83,                              │
│     "total_volume": 245,                             │
│     "source_count": 3,                               │
│     "divergence": 0.029                              │
│   },                                                  │
│   "source_breakdown": [...],                         │
│   "bull_arguments": [...],                           │
│   "bear_arguments": [...]                            │
│ }                                                     │
└────────────────────────────────────────────────────────┘
```

## Fallback Hierarchy

```
┌─────────────────────────────────────────┐
│ Attempt 1: Multi-Source Aggregation    │
│ (Twitter + Reddit + News + Tavily)      │
└────────────┬────────────────────────────┘
             │
        [All APIs fail?]
             │
             ▼ NO (at least 1 works)
┌─────────────────────────────────────────┐
│ Attempt 2: Available Sources Only       │
│ (Reweight remaining sources)             │
└────────────┬────────────────────────────┘
             │
        [Only Tavily available?]
             │
             ▼ YES
┌─────────────────────────────────────────┐
│ Attempt 3: Tavily-Only Mode             │
│ (100% weight to Tavily)                  │
└────────────┬────────────────────────────┘
             │
   [Legacy fallback enabled?]
             │
             ▼ YES
┌─────────────────────────────────────────┐
│ Attempt 4: Legacy Agent Fallback        │
│ (TavilySentimentTrackerAgent with GPT)   │
└────────────┬────────────────────────────┘
             │
        [Still fails?]
             │
             ▼ YES
┌─────────────────────────────────────────┐
│ Final: Error Result                     │
│ (Neutral sentiment, confidence=0)        │
└─────────────────────────────────────────┘
```

## Scoring & Classification

```
Sentiment Score Range: -1.0 to 1.0
─────────────────────────────────────────────────────
-1.0                    0.0                    1.0
 │                       │                       │
 │◄──────Bearish────────►│◄──────Bullish───────►│
 │                       │                       │
 │    Very    │    Some- │  Neutral │  Some-    │    Very
 │  Bearish   │  what    │          │  what     │  Bullish
 │            │  Bearish │          │  Bullish  │
 │            │          │          │           │
-1.0       -0.5       -0.15       0.15        0.5      1.0

Classification Rules:
• score > 0.15  → "bullish"
• score < -0.15 → "bearish"
• else          → "neutral"

Confidence Calculation:
• Based on data volume (number of mentions/posts/articles)
• volume ≥ 100  → confidence = 1.0
• volume ≥ 50   → confidence = 0.9
• volume ≥ 10   → confidence = 0.7
• volume ≥ 5    → confidence = 0.5
• volume < 5    → confidence = 0.3
```

## Component Interaction Matrix

```
┌─────────────────┬──────────┬─────────┬────────┬─────────┬────────────┐
│   Component     │ Twitter  │ Reddit  │ News   │ Tavily  │ Aggregator │
├─────────────────┼──────────┼─────────┼────────┼─────────┼────────────┤
│ Twitter Source  │    -     │    ✗    │   ✗    │    ✗    │     ✓      │
├─────────────────┼──────────┼─────────┼────────┼─────────┼────────────┤
│ Reddit Source   │    ✗     │    -    │   ✗    │    ✗    │     ✓      │
├─────────────────┼──────────┼─────────┼────────┼─────────┼────────────┤
│ News Source     │    ✗     │    ✗    │   -    │    ✗    │     ✓      │
├─────────────────┼──────────┼─────────┼────────┼─────────┼────────────┤
│ Tavily Source   │    ✗     │    ✗    │   ✗    │    -    │     ✓      │
├─────────────────┼──────────┼─────────┼────────┼─────────┼────────────┤
│ Aggregator      │    ✓     │    ✓    │   ✓    │    ✓    │     -      │
├─────────────────┼──────────┼─────────┼────────┼─────────┼────────────┤
│ Enhanced Agent  │    ✗     │    ✗    │   ✗    │    ✗    │     ✓      │
└─────────────────┴──────────┴─────────┴────────┴─────────┴────────────┘

Legend:
✓ = Direct interaction
✗ = No direct interaction
- = Self
```

## State Transitions

```
┌──────────────────────────────────────────────────────────────┐
│                    Agent State Machine                       │
└──────────────────────────────────────────────────────────────┘

       ┌─────────┐
       │  IDLE   │
       └────┬────┘
            │ analyze() called
            ▼
    ┌──────────────┐
    │ INITIALIZING │ ← Check API availability
    └──────┬───────┘
           │
           ▼
    ┌──────────────┐
    │  FETCHING    │ ← Concurrent API calls
    └──────┬───────┘
           │
     ┌─────┴─────┐
     │           │
     ▼           ▼
┌─────────┐  ┌──────────┐
│ SUCCESS │  │  ERROR   │
└────┬────┘  └─────┬────┘
     │             │
     │     ┌───────┘
     │     │ [Legacy fallback?]
     │     │
     │     ▼
     │  ┌──────────────┐
     │  │   FALLBACK   │ ← Try legacy agent
     │  └──────┬───────┘
     │         │
     │    ┌────┴────┐
     │    │         │
     │    ▼         ▼
     │ ┌────┐  ┌───────┐
     │ │ OK │  │ FAILED│
     │ └──┬─┘  └───┬───┘
     │    │        │
     └────┴────────┴──────┐
                          │
                          ▼
                    ┌──────────┐
                    │ COMPLETE │ ← Return result
                    └──────────┘
```

## Performance Characteristics

```
┌───────────────────────────────────────────────────────────────┐
│                      Response Time (ms)                       │
├───────────────────────────────────────────────────────────────┤
│                                                               │
│  Legacy (Tavily-only):                                        │
│  ██████████████████████ 3-8 seconds                          │
│                                                               │
│  Single Source:                                               │
│  ██████████████████████████ 3-5 seconds                      │
│                                                               │
│  2 Sources (parallel):                                        │
│  ████████████████████████████████ 5-10 seconds               │
│                                                               │
│  3 Sources (parallel):                                        │
│  ████████████████████████████████████████ 8-12 seconds       │
│                                                               │
│  4 Sources (parallel):                                        │
│  ██████████████████████████████████████████████ 8-15 seconds │
│                                                               │
└───────────────────────────────────────────────────────────────┘

┌───────────────────────────────────────────────────────────────┐
│                    Accuracy vs Coverage                       │
├───────────────────────────────────────────────────────────────┤
│  Accuracy (%)                                                 │
│  100 │                                         ●              │
│   90 │                               ●                        │
│   80 │                     ●                                  │
│   70 │           ●                                            │
│   60 │    ●                                                   │
│   50 │                                                        │
│      └────┴─────┴─────┴─────┴─────┴─────                     │
│         Tavily  +News  +Reddit +Twitter +All                 │
│         Only    (2src) (3src)  (4src)  +Weights              │
└───────────────────────────────────────────────────────────────┘
```

## Integration Points

```
┌─────────────────────────────────────────────────────────────┐
│               External System Integration                    │
└─────────────────────────────────────────────────────────────┘

   LangGraph Workflow
         │
         ▼
   ┌──────────────────┐
   │ Sentiment Agent  │ ◄─── config.py (settings)
   └────────┬─────────┘
            │
            ├─────────────► MongoDB (store results)
            │
            ├─────────────► Redis (cache responses)
            │
            ├─────────────► WebSocket (progress updates)
            │
            └─────────────► Logging (Langfuse, Sentry)


   External APIs
         │
   ┌─────┴──────┐
   │            │
   ▼            ▼
Twitter API   Reddit API   Alpha Vantage   NewsAPI   Tavily
   (v2)         (OAuth2)     (REST)         (REST)   (REST)
   │            │             │              │         │
   └────────────┴─────────────┴──────────────┴─────────┘
                     │
                     ▼
              Rate Limiters
              (per-API tracking)
```

This architecture provides a robust, scalable, and maintainable multi-source sentiment analysis system with graceful degradation and backward compatibility.
