"""
Test News-Sentiment Correlation System
Demonstrates the integration and shows example output
"""

import asyncio
import os
from datetime import datetime
import json
import sys

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from dotenv import load_dotenv
from langchain_openai import ChatOpenAI

from agents.tavily_agents.integrated_news_sentiment_agent import IntegratedNewsSentimentAgent
from services.news_sentiment_correlator import NewsSentimentCorrelator

load_dotenv()


async def test_correlator_standalone():
    """Test the correlator with mock news data"""
    print("\n" + "="*80)
    print("TEST 1: News-Sentiment Correlator (Standalone)")
    print("="*80 + "\n")

    # Mock news articles (as they would come from Tavily)
    mock_news = [
        {
            'title': 'AAPL Beats Q4 Earnings Expectations, Stock Surges',
            'summary': 'Apple Inc. reported better-than-expected earnings with strong iPhone sales driving revenue growth. Analysts raise price targets.',
            'url': 'https://example.com/news1',
            'source': 'Bloomberg',
            'published': '2025-10-07T10:00:00Z',
            'relevance_score': 0.95
        },
        {
            'title': 'Apple Faces Regulatory Scrutiny in EU',
            'summary': 'European regulators announced investigation into Apple App Store practices, potential fines could impact margins.',
            'url': 'https://example.com/news2',
            'source': 'Reuters',
            'published': '2025-10-07T14:00:00Z',
            'relevance_score': 0.85
        },
        {
            'title': 'Apple Vision Pro Sales Below Expectations',
            'summary': 'Industry sources report Vision Pro headset sales tracking below initial forecasts, raising questions about mixed reality strategy.',
            'url': 'https://example.com/news3',
            'source': 'CNBC',
            'published': '2025-10-06T16:00:00Z',
            'relevance_score': 0.75
        },
        {
            'title': 'Apple Services Revenue Reaches New High',
            'summary': 'Services division continues strong growth trajectory with App Store and Apple Music subscriptions hitting record levels.',
            'url': 'https://example.com/news4',
            'source': 'MarketWatch',
            'published': '2025-10-06T11:00:00Z',
            'relevance_score': 0.80
        }
    ]

    # Initialize correlator
    llm = ChatOpenAI(model="gpt-3.5-turbo", temperature=0.1, max_tokens=400)
    correlator = NewsSentimentCorrelator(llm=llm)

    # Run correlation
    print("Analyzing sentiment for 4 news articles about AAPL...\n")
    result = await correlator.correlate(
        news_articles=mock_news,
        symbol='AAPL'
    )

    # Display results
    print("CORRELATION RESULTS:")
    print("-" * 80)

    print(f"\nOverall Sentiment: {result['aggregate_sentiment']['label'].upper()}")
    print(f"Sentiment Score: {result['aggregate_sentiment']['score']}")
    print(f"Confidence: {result['aggregate_sentiment']['confidence']}")
    print(f"News Volume: {result['aggregate_sentiment']['news_volume']} articles")

    print("\n\nTOP SENTIMENT DRIVERS:")
    print("-" * 80)
    for i, driver in enumerate(result['sentiment_drivers'][:3], 1):
        print(f"\n{i}. {driver['article']['title']}")
        print(f"   Source: {driver['article']['source']}")
        print(f"   Sentiment: {driver['article']['sentiment']} (score: {driver['article']['sentiment_score']})")
        print(f"   Impact Weight: {driver['impact_weight']}")
        print(f"   Driver Type: {driver['driver_type']}")
        print(f"   Reasoning: {driver['reasoning']}")

    print("\n\nARTICLE-LEVEL SENTIMENTS:")
    print("-" * 80)
    for article in result['article_sentiments']:
        print(f"\n• {article['title'][:60]}...")
        print(f"  Sentiment: {article['sentiment']} (score: {article['sentiment_score']})")
        print(f"  Confidence: {article['sentiment_confidence']}")
        print(f"  Impact Level: {article['impact_level']}")
        if article.get('key_points'):
            print(f"  Key Points: {', '.join(article['key_points'][:2])}")

    print("\n\nSENTIMENT TIMELINE:")
    print("-" * 80)
    for entry in result['sentiment_timeline']:
        print(f"\n{entry['timestamp']}: {entry['sentiment_label'].upper()}")
        print(f"  Score: {entry['sentiment_score']}, Volume: {entry['volume']} articles")

    print("\n\nINSIGHTS:")
    print("-" * 80)
    insights = result['insights']
    print(f"Consensus Level: {insights.get('consensus_level', 'N/A')}")
    print(f"Momentum: {insights.get('momentum', 'N/A')}")
    if insights.get('key_themes'):
        print(f"Key Themes: {', '.join(insights['key_themes'][:3])}")

    print("\n" + "="*80 + "\n")
    return result


async def test_integrated_agent():
    """Test the integrated agent with real Tavily API"""
    print("\n" + "="*80)
    print("TEST 2: Integrated News-Sentiment Agent (Real API)")
    print("="*80 + "\n")

    tavily_api_key = os.getenv('TAVILY_API_KEY')
    openai_api_key = os.getenv('OPENAI_API_KEY')

    if not tavily_api_key or not openai_api_key:
        print("⚠️  Skipping: TAVILY_API_KEY or OPENAI_API_KEY not set")
        return

    # Initialize agent
    llm = ChatOpenAI(model="gpt-4", temperature=0.2, max_tokens=800)
    agent = IntegratedNewsSentimentAgent(
        tavily_api_key=tavily_api_key,
        llm=llm
    )

    # Run analysis
    context = {
        'symbol': 'AAPL',
        'market_data': {'price': 175.50, 'change_percent': 1.2},
        'base_recommendation': 'BUY'
    }

    print("Running integrated analysis for AAPL...\n")
    print("This will:")
    print("1. Fetch real news from Tavily")
    print("2. Track social sentiment from professional sources")
    print("3. Correlate news articles with sentiment")
    print("4. Analyze divergence between news and social sentiment\n")

    result = await agent.analyze(context)

    # Display results
    print("\nINTEGRATED ANALYSIS RESULTS:")
    print("=" * 80)

    print("\n📰 NEWS ANALYSIS:")
    print("-" * 80)
    news = result['news_analysis']
    print(f"Total Articles: {news['total_articles']}")
    print(f"Key Events: {', '.join(news.get('key_events', [])[:2])}")
    print(f"Catalysts: {', '.join(news.get('catalysts', [])[:2])}")
    print(f"Risks: {', '.join(news.get('risks', [])[:2])}")

    print("\n📊 SOCIAL SENTIMENT:")
    print("-" * 80)
    social = result['social_sentiment']
    print(f"Retail Sentiment: {social['retail_sentiment']}")
    print(f"Retail Score: {social['retail_score']}")
    print(f"Social Volume: {social['social_volume']}")
    print(f"Trending: {social['trending']}")
    print(f"Platforms: {', '.join(social.get('platforms', []))}")

    print("\n🔗 NEWS-SENTIMENT CORRELATION:")
    print("-" * 80)
    correlation = result['news_sentiment_correlation']
    print(f"Articles Analyzed: {correlation['correlation_metadata']['articles_analyzed']}")
    print(f"Sentiment Drivers Identified: {correlation['correlation_metadata']['drivers_identified']}")

    if correlation.get('sentiment_drivers'):
        print("\nTop Sentiment Drivers:")
        for i, driver in enumerate(correlation['sentiment_drivers'][:3], 1):
            print(f"  {i}. {driver['article']['title'][:60]}...")
            print(f"     Sentiment: {driver['article']['sentiment']} (impact: {driver['impact_weight']})")

    print("\n🎯 UNIFIED SENTIMENT:")
    print("-" * 80)
    unified = result['unified_sentiment']
    print(f"Overall: {unified['label'].upper()} (score: {unified['score']})")
    print(f"Confidence: {unified['confidence']}")
    print(f"News Sentiment: {unified['news_sentiment']}")
    print(f"Social Sentiment: {unified['social_sentiment']}")
    print(f"Interpretation: {unified['interpretation']}")

    print("\n⚡ DIVERGENCE ANALYSIS:")
    print("-" * 80)
    divergence = result['divergence_analysis']
    print(f"Divergence Level: {divergence['divergence_level']}")
    print(f"Divergence Score: {divergence['divergence_score']}")
    print(f"Sentiment Leader: {divergence['sentiment_leader']}")
    print(f"Interpretation: {divergence['interpretation']}")
    print(f"Trading Signal: {divergence['trading_signal']}")

    print("\n" + "="*80 + "\n")

    # Save to file for reference
    output_file = '/tmp/news_sentiment_correlation_example.json'
    with open(output_file, 'w') as f:
        json.dump(result, f, indent=2, default=str)
    print(f"✅ Full results saved to: {output_file}\n")

    return result


async def main():
    """Run all tests"""
    print("\n" + "="*80)
    print("NEWS-SENTIMENT CORRELATION SYSTEM - TEST SUITE")
    print("="*80)

    # Test 1: Standalone correlator with mock data
    await test_correlator_standalone()

    # Test 2: Integrated agent with real API (if keys available)
    await test_integrated_agent()

    print("\n✅ All tests complete!\n")


if __name__ == "__main__":
    asyncio.run(main())
