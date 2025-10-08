import React from 'react';
import { Card, Row, Col, Progress, Tag, Space, Typography, Tooltip, Badge, List } from 'antd';
import {
  ArrowUpOutlined,
  ArrowDownOutlined,
  MinusOutlined,
  InfoCircleOutlined,
  ClockCircleOutlined,
  TrophyOutlined,
  TeamOutlined,
  LineChartOutlined,
  BulbOutlined,
} from '@ant-design/icons';
import { theme } from '../styles/theme';

const { Title, Text, Paragraph } = Typography;

interface SentimentPanelProps {
  sentimentData: any;
  symbol?: string;
}

/**
 * SentimentPanel - Comprehensive sentiment visualization component
 *
 * Maps sentiment scores to visual indicators:
 * - Sentiment gauge/meter (bullish/neutral/bearish)
 * - Color coding (green: bullish, yellow: neutral, red: bearish)
 * - Source breakdown (News, Analyst, Social, Insider)
 * - Sentiment drivers (top factors affecting sentiment)
 *
 * Design: Uses CRED design tokens for premium feel
 */
const SentimentPanel: React.FC<SentimentPanelProps> = ({ sentimentData, symbol }) => {
  if (!sentimentData || Object.keys(sentimentData).length === 0) {
    return null;
  }

  // Extract sentiment data - supports both formats
  const compositeScore = sentimentData.composite_score || sentimentData.overall_sentiment_score || 50;
  const sentimentScore = sentimentData.sentiment_score || (compositeScore - 50) / 50; // Map 0-100 to -1 to 1
  const sentiment = sentimentData.sentiment || getSentimentLabel(compositeScore);
  const stocks = sentimentData.stocks || {};
  const newsData = sentimentData.news_sentiment || sentimentData.sentiment || {};
  const socialData = sentimentData.social_sentiment || {};
  const analystData = sentimentData.analyst_sentiment || {};
  const insiderData = sentimentData.insider_activity || {};

  // Get stock-specific sentiment if symbol provided
  const stockSentiment = symbol && stocks[symbol] ? stocks[symbol] : null;

  /**
   * Map sentiment score to label
   * Score range: 0-100
   * - 0-35: Bearish
   * - 35-65: Neutral
   * - 65-100: Bullish
   */
  function getSentimentLabel(score: number): string {
    if (score > 65) return 'bullish';
    if (score < 35) return 'bearish';
    return 'neutral';
  }

  /**
   * Get sentiment color based on score
   * Uses CRED design tokens
   */
  function getSentimentColor(score: number): string {
    if (score > 65) return theme.colors.success;
    if (score < 35) return theme.colors.danger;
    return theme.colors.warning;
  }

  /**
   * Get sentiment icon
   */
  function getSentimentIcon(score: number) {
    if (score > 65) return <ArrowUpOutlined style={{ color: theme.colors.success }} />;
    if (score < 35) return <ArrowDownOutlined style={{ color: theme.colors.danger }} />;
    return <MinusOutlined style={{ color: theme.colors.warning }} />;
  }

  /**
   * Calculate source breakdown percentages
   */
  function calculateSourceBreakdown() {
    const sources = [];

    // News sentiment
    if (stockSentiment?.news_sentiment?.sentiment_score !== undefined) {
      sources.push({
        name: 'News',
        score: stockSentiment.news_sentiment.sentiment_score,
        icon: <LineChartOutlined />,
        details: `${stockSentiment.news_sentiment.positive_mentions || 0} positive, ${stockSentiment.news_sentiment.negative_mentions || 0} negative`
      });
    } else if (newsData.sentiment_score !== undefined) {
      sources.push({
        name: 'News',
        score: typeof newsData.sentiment_score === 'number' ? newsData.sentiment_score :
               (newsData.sentiment_score > 0 ? newsData.sentiment_score * 100 : 50),
        icon: <LineChartOutlined />,
        details: newsData.summary || 'News sentiment analysis'
      });
    }

    // Analyst sentiment
    if (stockSentiment?.analyst_sentiment?.consensus) {
      const consensus = stockSentiment.analyst_sentiment.consensus;
      const score = consensus === 'Buy' ? 75 : consensus === 'Sell' ? 25 : 50;
      sources.push({
        name: 'Analyst',
        score,
        icon: <TrophyOutlined />,
        details: `Consensus: ${consensus}, ${stockSentiment.analyst_sentiment.buy_ratings || 0} buy ratings`
      });
    }

    // Social sentiment
    if (stockSentiment?.social_sentiment?.sentiment_lean) {
      const lean = stockSentiment.social_sentiment.sentiment_lean;
      const score = lean === 'positive' ? 70 : lean === 'negative' ? 30 : 50;
      sources.push({
        name: 'Social',
        score,
        icon: <TeamOutlined />,
        details: `${lean.charAt(0).toUpperCase() + lean.slice(1)} lean, ${stockSentiment.social_sentiment.mention_volume || 'normal'} volume`
      });
    }

    // Insider activity
    if (stockSentiment?.insider_activity?.net_activity) {
      const activity = stockSentiment.insider_activity.net_activity;
      const score = activity === 'buying' ? 75 : activity === 'selling' ? 25 : 50;
      sources.push({
        name: 'Insider',
        score,
        icon: <BulbOutlined />,
        details: `Net ${activity}, ${stockSentiment.insider_activity.recent_buys || 0} buys, ${stockSentiment.insider_activity.recent_sells || 0} sells`
      });
    }

    return sources;
  }

  const sourceBreakdown = calculateSourceBreakdown();

  /**
   * Extract sentiment drivers (top factors)
   */
  function getSentimentDrivers() {
    const drivers = [];

    // Key events
    if (newsData.key_events && Array.isArray(newsData.key_events)) {
      drivers.push(...newsData.key_events.slice(0, 3));
    }

    // Catalysts (positive)
    if (newsData.catalysts && Array.isArray(newsData.catalysts)) {
      drivers.push(...newsData.catalysts.slice(0, 2));
    }

    // Risks (negative)
    if (newsData.risks && Array.isArray(newsData.risks)) {
      drivers.push(...newsData.risks.slice(0, 2));
    }

    // Recent headlines
    if (stockSentiment?.news_sentiment?.recent_headlines) {
      drivers.push(...stockSentiment.news_sentiment.recent_headlines.slice(0, 2));
    }

    return drivers.slice(0, 5);
  }

  const drivers = getSentimentDrivers();

  /**
   * Get data freshness indicator
   */
  function getDataFreshness(): string {
    const timestamp = sentimentData.timestamp;
    if (!timestamp) return 'Unknown';

    const date = new Date(timestamp);
    const now = new Date();
    const diffMinutes = Math.floor((now.getTime() - date.getTime()) / 60000);

    if (diffMinutes < 5) return 'Just now';
    if (diffMinutes < 60) return `${diffMinutes}m ago`;
    const diffHours = Math.floor(diffMinutes / 60);
    if (diffHours < 24) return `${diffHours}h ago`;
    return `${Math.floor(diffHours / 24)}d ago`;
  }

  return (
    <Card
      title={
        <Space>
          <Title level={4} style={{ margin: 0 }}>
            Market Sentiment Analysis
          </Title>
          <Badge
            count={getDataFreshness()}
            style={{
              backgroundColor: theme.colors.background.elevated,
              color: theme.colors.text.secondary,
              border: `1px solid ${theme.colors.border}`
            }}
          />
        </Space>
      }
      style={{
        background: theme.colors.background.secondary,
        border: `1px solid ${theme.colors.border}`,
        borderRadius: theme.borderRadius.lg,
      }}
      data-test="sentiment-panel"
    >
      <Row gutter={[24, 24]}>
        {/* Overall Sentiment Gauge */}
        <Col xs={24} lg={12}>
          <Card
            size="small"
            title={
              <Space>
                <Text strong>Overall Sentiment</Text>
                <Tooltip title="Composite sentiment score aggregated from news, analyst ratings, social media, and insider activity. Weighted by source reliability.">
                  <InfoCircleOutlined style={{ color: theme.colors.text.muted }} />
                </Tooltip>
              </Space>
            }
            style={{
              background: theme.effects.glassMorphism.background,
              backdropFilter: theme.effects.glassMorphism.backdropFilter,
              border: theme.effects.glassMorphism.border,
            }}
          >
            <Space direction="vertical" size="large" style={{ width: '100%' }}>
              {/* Sentiment Meter */}
              <div style={{ textAlign: 'center' }}>
                <div style={{ fontSize: 64, marginBottom: 16 }}>
                  {getSentimentIcon(compositeScore)}
                </div>
                <Title level={2} style={{ margin: 0, color: getSentimentColor(compositeScore) }}>
                  {sentiment.toUpperCase()}
                </Title>
                <Text type="secondary" style={{ fontSize: 14 }}>
                  Score: {compositeScore.toFixed(1)}/100
                </Text>
              </div>

              {/* Progress Bar */}
              <Progress
                percent={compositeScore}
                strokeColor={{
                  '0%': compositeScore < 35 ? theme.colors.danger :
                        compositeScore > 65 ? theme.colors.success : theme.colors.warning,
                  '100%': compositeScore < 35 ? theme.colors.danger :
                          compositeScore > 65 ? theme.colors.success : theme.colors.warning,
                }}
                strokeWidth={12}
                showInfo={false}
                style={{ marginBottom: 8 }}
              />

              {/* Sentiment Range Labels */}
              <Row justify="space-between">
                <Col>
                  <Text style={{ fontSize: 12, color: theme.colors.danger }}>
                    Bearish (0)
                  </Text>
                </Col>
                <Col>
                  <Text style={{ fontSize: 12, color: theme.colors.warning }}>
                    Neutral (50)
                  </Text>
                </Col>
                <Col>
                  <Text style={{ fontSize: 12, color: theme.colors.success }}>
                    Bullish (100)
                  </Text>
                </Col>
              </Row>

              {/* Sentiment Summary */}
              {sentimentData.sentiment_summary && (
                <div
                  style={{
                    padding: 12,
                    background: theme.colors.background.elevated,
                    borderRadius: theme.borderRadius.md,
                    border: `1px solid ${theme.colors.border}`,
                  }}
                >
                  <Text type="secondary">{sentimentData.sentiment_summary}</Text>
                </div>
              )}
            </Space>
          </Card>
        </Col>

        {/* Source Breakdown */}
        <Col xs={24} lg={12}>
          <Card
            size="small"
            title={
              <Space>
                <Text strong>Sentiment by Source</Text>
                <Tooltip title="Breakdown of sentiment across different data sources. Each source is analyzed independently and weighted by reliability.">
                  <InfoCircleOutlined style={{ color: theme.colors.text.muted }} />
                </Tooltip>
              </Space>
            }
            style={{
              background: theme.effects.glassMorphism.background,
              backdropFilter: theme.effects.glassMorphism.backdropFilter,
              border: theme.effects.glassMorphism.border,
            }}
          >
            <Space direction="vertical" size="middle" style={{ width: '100%' }}>
              {sourceBreakdown.length > 0 ? (
                sourceBreakdown.map((source, index) => (
                  <div key={index}>
                    <Row justify="space-between" align="middle" style={{ marginBottom: 8 }}>
                      <Col>
                        <Space>
                          {source.icon}
                          <Text strong>{source.name}</Text>
                        </Space>
                      </Col>
                      <Col>
                        <Tag
                          color={getSentimentColor(source.score)}
                          icon={getSentimentIcon(source.score)}
                          style={{ fontWeight: 600 }}
                        >
                          {source.score.toFixed(0)}%
                        </Tag>
                      </Col>
                    </Row>
                    <Progress
                      percent={source.score}
                      strokeColor={getSentimentColor(source.score)}
                      showInfo={false}
                      style={{ marginBottom: 4 }}
                    />
                    <Text type="secondary" style={{ fontSize: 12 }}>
                      {source.details}
                    </Text>
                  </div>
                ))
              ) : (
                <Text type="secondary">No source breakdown available</Text>
              )}

              {/* Data Points Count */}
              {sentimentData.data_points && (
                <div
                  style={{
                    marginTop: 16,
                    padding: 12,
                    background: theme.colors.background.elevated,
                    borderRadius: theme.borderRadius.md,
                    border: `1px solid ${theme.colors.border}`,
                  }}
                >
                  <Space>
                    <ClockCircleOutlined style={{ color: theme.colors.primary }} />
                    <Text type="secondary" style={{ fontSize: 12 }}>
                      Analyzed {sentimentData.data_points} data points from {sentimentData.source_count || 0} sources
                    </Text>
                  </Space>
                </div>
              )}
            </Space>
          </Card>
        </Col>

        {/* Sentiment Drivers */}
        {drivers.length > 0 && (
          <Col xs={24}>
            <Card
              size="small"
              title={
                <Space>
                  <Text strong>Top Sentiment Drivers</Text>
                  <Tooltip title="Key events, catalysts, and risks identified from recent news and market activity. These are the primary factors influencing current sentiment.">
                    <InfoCircleOutlined style={{ color: theme.colors.text.muted }} />
                  </Tooltip>
                </Space>
              }
              style={{
                background: theme.effects.glassMorphism.background,
                backdropFilter: theme.effects.glassMorphism.backdropFilter,
                border: theme.effects.glassMorphism.border,
              }}
            >
              <List
                dataSource={drivers}
                renderItem={(driver: string, index) => (
                  <List.Item style={{ borderBottom: `1px solid ${theme.colors.border}` }}>
                    <List.Item.Meta
                      avatar={
                        <div
                          style={{
                            width: 32,
                            height: 32,
                            borderRadius: '50%',
                            background: theme.colors.primary,
                            display: 'flex',
                            alignItems: 'center',
                            justifyContent: 'center',
                            color: theme.colors.text.inverse,
                            fontWeight: 700,
                          }}
                        >
                          {index + 1}
                        </div>
                      }
                      title={
                        <Text style={{ color: theme.colors.text.primary }}>
                          {driver}
                        </Text>
                      }
                    />
                  </List.Item>
                )}
                style={{ marginTop: 0 }}
              />
            </Card>
          </Col>
        )}

        {/* Market Sentiment Context (if available) */}
        {sentimentData.market_sentiment && (
          <Col xs={24}>
            <Card
              size="small"
              title={<Text strong>Market Context</Text>}
              style={{
                background: theme.effects.glassMorphism.background,
                backdropFilter: theme.effects.glassMorphism.backdropFilter,
                border: theme.effects.glassMorphism.border,
              }}
            >
              <Row gutter={[16, 16]}>
                {sentimentData.market_sentiment.fear_greed_index && (
                  <Col xs={24} sm={12} md={6}>
                    <div style={{ textAlign: 'center' }}>
                      <Text type="secondary" style={{ fontSize: 12 }}>
                        Fear & Greed
                      </Text>
                      <Title level={3} style={{ margin: '8px 0', color: theme.colors.primary }}>
                        {sentimentData.market_sentiment.fear_greed_index}
                      </Title>
                    </div>
                  </Col>
                )}
                {sentimentData.market_sentiment.vix_level && (
                  <Col xs={24} sm={12} md={6}>
                    <div style={{ textAlign: 'center' }}>
                      <Text type="secondary" style={{ fontSize: 12 }}>
                        VIX Level
                      </Text>
                      <Title level={3} style={{ margin: '8px 0', color: theme.colors.warning }}>
                        {sentimentData.market_sentiment.vix_level.toFixed(2)}
                      </Title>
                    </div>
                  </Col>
                )}
                {sentimentData.market_sentiment.market_trend && (
                  <Col xs={24} sm={12} md={6}>
                    <div style={{ textAlign: 'center' }}>
                      <Text type="secondary" style={{ fontSize: 12 }}>
                        Market Trend
                      </Text>
                      <Title
                        level={3}
                        style={{
                          margin: '8px 0',
                          color: sentimentData.market_sentiment.market_trend === 'bullish' ?
                                theme.colors.success : theme.colors.danger
                        }}
                      >
                        {sentimentData.market_sentiment.market_trend.toUpperCase()}
                      </Title>
                    </div>
                  </Col>
                )}
              </Row>
            </Card>
          </Col>
        )}
      </Row>
    </Card>
  );
};

export default SentimentPanel;
