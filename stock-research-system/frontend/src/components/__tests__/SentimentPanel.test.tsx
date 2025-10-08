import React from 'react';
import { render, screen } from '@testing-library/react';
import '@testing-library/jest-dom';
import SentimentPanel from '../SentimentPanel';

describe('SentimentPanel', () => {
  const mockSentimentData = {
    composite_score: 75,
    overall_sentiment_score: 75,
    sentiment: 'bullish',
    sentiment_score: 0.5,
    sentiment_summary: 'Strong positive sentiment across analyzed stocks',
    data_points: 247,
    source_count: 8,
    timestamp: new Date().toISOString(),
    stocks: {
      AAPL: {
        composite_score: 75,
        news_sentiment: {
          sentiment_score: 65,
          positive_mentions: 15,
          negative_mentions: 3,
          recent_headlines: ['Q4 earnings beat expectations', 'Product launch announced']
        },
        analyst_sentiment: {
          consensus: 'Buy',
          buy_ratings: 12,
          hold_ratings: 3,
          sell_ratings: 1
        },
        social_sentiment: {
          sentiment_lean: 'positive',
          mention_volume: 'high',
          trending: true
        },
        insider_activity: {
          net_activity: 'buying',
          recent_buys: 5,
          recent_sells: 1
        }
      }
    },
    market_sentiment: {
      fear_greed_index: 72,
      vix_level: 14.5,
      market_trend: 'bullish'
    }
  };

  it('renders without crashing', () => {
    render(<SentimentPanel sentimentData={mockSentimentData} symbol="AAPL" />);
    expect(screen.getByText(/Market Sentiment Analysis/i)).toBeInTheDocument();
  });

  it('displays overall sentiment correctly', () => {
    render(<SentimentPanel sentimentData={mockSentimentData} symbol="AAPL" />);
    expect(screen.getByText(/BULLISH/i)).toBeInTheDocument();
  });

  it('shows sentiment score', () => {
    render(<SentimentPanel sentimentData={mockSentimentData} symbol="AAPL" />);
    expect(screen.getByText(/75.0\/100/i)).toBeInTheDocument();
  });

  it('displays sentiment summary', () => {
    render(<SentimentPanel sentimentData={mockSentimentData} symbol="AAPL" />);
    expect(screen.getByText(/Strong positive sentiment across analyzed stocks/i)).toBeInTheDocument();
  });

  it('shows source breakdown when available', () => {
    render(<SentimentPanel sentimentData={mockSentimentData} symbol="AAPL" />);
    expect(screen.getByText(/News/i)).toBeInTheDocument();
    expect(screen.getByText(/Analyst/i)).toBeInTheDocument();
    expect(screen.getByText(/Social/i)).toBeInTheDocument();
    expect(screen.getByText(/Insider/i)).toBeInTheDocument();
  });

  it('displays market context when available', () => {
    render(<SentimentPanel sentimentData={mockSentimentData} symbol="AAPL" />);
    expect(screen.getByText(/Market Context/i)).toBeInTheDocument();
    expect(screen.getByText(/Fear & Greed/i)).toBeInTheDocument();
    expect(screen.getByText(/72/i)).toBeInTheDocument();
  });

  it('handles bearish sentiment correctly', () => {
    const bearishData = {
      ...mockSentimentData,
      composite_score: 25,
      sentiment: 'bearish'
    };
    render(<SentimentPanel sentimentData={bearishData} symbol="AAPL" />);
    expect(screen.getByText(/BEARISH/i)).toBeInTheDocument();
  });

  it('handles neutral sentiment correctly', () => {
    const neutralData = {
      ...mockSentimentData,
      composite_score: 50,
      sentiment: 'neutral'
    };
    render(<SentimentPanel sentimentData={neutralData} symbol="AAPL" />);
    expect(screen.getByText(/NEUTRAL/i)).toBeInTheDocument();
  });

  it('returns null when no sentiment data provided', () => {
    const { container } = render(<SentimentPanel sentimentData={null} />);
    expect(container.firstChild).toBeNull();
  });

  it('returns null when empty sentiment data provided', () => {
    const { container } = render(<SentimentPanel sentimentData={{}} />);
    expect(container.firstChild).toBeNull();
  });

  it('has data-test attribute for E2E testing', () => {
    render(<SentimentPanel sentimentData={mockSentimentData} symbol="AAPL" />);
    expect(screen.getByTestId('sentiment-panel')).toBeInTheDocument();
  });
});
