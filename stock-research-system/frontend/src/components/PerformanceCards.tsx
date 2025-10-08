import React from 'react';
import { Card, Row, Col, Typography, Progress, Space, Tag, Divider, Avatar } from 'antd';
import {
  LineChartOutlined,
  RiseOutlined,
  HeartOutlined,
  TeamOutlined,
  TrophyOutlined,
  ThunderboltOutlined,
  BarChartOutlined,
  ArrowRightOutlined
} from '@ant-design/icons';
import { motion } from 'framer-motion';

const { Title, Text, Paragraph } = Typography;

interface PerformanceCardsProps {
  analysisData: any;
  valuation?: any;
  technical?: any;
  competitive?: any;
}

const PerformanceCards: React.FC<PerformanceCardsProps> = ({
  analysisData,
  valuation,
  technical,
  competitive
}) => {
  // Calculate performance scores
  const calculateFundamentalsScore = () => {
    if (!valuation) return { score: 'N/A', rating: 'Moderate', color: '#faad14' };

    const upside = valuation?.price_target?.upside || 0;
    const peRatio = analysisData?.analysis?.market_data?.[analysisData.symbol]?.pe_ratio || 0;
    const valuationRating = valuation?.comparative_valuation?.valuation_rating || '';

    let score = 50;
    let rating = 'Moderate';
    let color = '#faad14';

    if (upside > 20) {
      score = 85;
      rating = 'Strong (A)';
      color = '#52c41a';
    } else if (upside > 10) {
      score = 70;
      rating = 'Moderate (B)';
      color = '#1890ff';
    } else if (upside > 0) {
      score = 60;
      rating = 'Neutral (C)';
      color = '#faad14';
    } else {
      score = 40;
      rating = 'Weak (D)';
      color = '#f5222d';
    }

    return { score, rating, color };
  };

  const calculateTechnicalScore = () => {
    if (!technical) return { score: 'N/A', rating: 'Hold', color: '#faad14' };

    const signals = technical?.signals?.overall || 'NEUTRAL';
    const momentum = technical?.indicators?.momentum?.rsi || 50;

    let rating = 'Hold';
    let color = '#faad14';
    let score = 50;

    if (signals === 'STRONG_BUY' || (momentum > 30 && momentum < 70)) {
      rating = 'Buy';
      color = '#52c41a';
      score = 75;
    } else if (signals === 'BUY') {
      rating = 'Buy';
      color = '#52c41a';
      score = 65;
    } else if (signals === 'SELL' || signals === 'STRONG_SELL') {
      rating = 'Sell';
      color = '#f5222d';
      score = 25;
    }

    return { score, rating, color };
  };

  const calculateSentimentScore = () => {
    const news = analysisData?.analysis?.news || [];
    const recommendation = analysisData?.analysis?.recommendations?.[0] || '';

    let rating = 'Neutral';
    let color = '#faad14';
    let score = 50;

    if (recommendation.includes('BUY') || news.length > 3) {
      rating = 'Bullish';
      color = '#52c41a';
      score = 70;
    } else if (recommendation.includes('SELL')) {
      rating = 'Bearish';
      color = '#f5222d';
      score = 30;
    }

    return { score, rating, color };
  };

  const fundamentals = calculateFundamentalsScore();
  const technicals = calculateTechnicalScore();
  const sentiment = calculateSentimentScore();

  // Calculate investor trend (mock data - in production this would come from real user data)
  const investorTrend = {
    buy: 15,
    hold: 70,
    sell: 15
  };

  const getMaxTrend = () => {
    const max = Math.max(investorTrend.buy, investorTrend.hold, investorTrend.sell);
    if (max === investorTrend.buy) return { label: 'Buy', color: '#52c41a' };
    if (max === investorTrend.sell) return { label: 'Sell', color: '#f5222d' };
    return { label: 'Hold', color: '#faad14' };
  };

  const maxTrend = getMaxTrend();

  return (
    <div className="performance-cards">
      <Title level={3} style={{ marginBottom: 24 }}>Performance Analysis</Title>

      <Row gutter={[16, 16]}>
        {/* Fundamentals Card */}
        <Col xs={24} md={8}>
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.3 }}
          >
            <Card
              hoverable
              className="performance-card"
              onClick={() => {}}
            >
              <Space direction="vertical" style={{ width: '100%' }} size="middle">
                <Space align="center">
                  <Avatar
                    size={48}
                    style={{ backgroundColor: fundamentals.color + '20' }}
                    icon={<BarChartOutlined style={{ color: fundamentals.color }} />}
                  />
                  <div style={{ flex: 1 }}>
                    <Title level={4} style={{ margin: 0 }}>Fundamentals</Title>
                    <Text type="secondary">Intrinsic value & financials</Text>
                  </div>
                  <Tag color={fundamentals.color} style={{ fontSize: 16, padding: '4px 12px' }}>
                    {fundamentals.rating}
                  </Tag>
                  <ArrowRightOutlined style={{ color: '#999' }} />
                </Space>

                <Paragraph style={{ margin: 0, color: '#666' }}>
                  Examining company's intrinsic value, financial health, and growth potential based on DCF and peer comparison.
                </Paragraph>

                {typeof fundamentals.score === 'number' && (
                  <Progress
                    percent={fundamentals.score}
                    strokeColor={fundamentals.color}
                    showInfo={false}
                    size="small"
                  />
                )}
              </Space>
            </Card>
          </motion.div>
        </Col>

        {/* Technicals Card */}
        <Col xs={24} md={8}>
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.3, delay: 0.1 }}
          >
            <Card
              hoverable
              className="performance-card"
              onClick={() => {}}
            >
              <Space direction="vertical" style={{ width: '100%' }} size="middle">
                <Space align="center">
                  <Avatar
                    size={48}
                    style={{ backgroundColor: technicals.color + '20' }}
                    icon={<LineChartOutlined style={{ color: technicals.color }} />}
                  />
                  <div style={{ flex: 1 }}>
                    <Title level={4} style={{ margin: 0 }}>Technicals</Title>
                    <Text type="secondary">Charts & indicators</Text>
                  </div>
                  <Tag color={technicals.color} style={{ fontSize: 16, padding: '4px 12px' }}>
                    {technicals.rating}
                  </Tag>
                  <ArrowRightOutlined style={{ color: '#999' }} />
                </Space>

                <Paragraph style={{ margin: 0, color: '#666' }}>
                  Analyzing price charts, trading volumes, and technical indicators to predict future price movements.
                </Paragraph>

                {typeof technicals.score === 'number' && (
                  <Progress
                    percent={technicals.score}
                    strokeColor={technicals.color}
                    showInfo={false}
                    size="small"
                  />
                )}
              </Space>
            </Card>
          </motion.div>
        </Col>

        {/* Sentiment Card */}
        <Col xs={24} md={8}>
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.3, delay: 0.2 }}
          >
            <Card
              hoverable
              className="performance-card"
              onClick={() => {}}
            >
              <Space direction="vertical" style={{ width: '100%' }} size="middle">
                <Space align="center">
                  <Avatar
                    size={48}
                    style={{ backgroundColor: sentiment.color + '20' }}
                    icon={<HeartOutlined style={{ color: sentiment.color }} />}
                  />
                  <div style={{ flex: 1 }}>
                    <Title level={4} style={{ margin: 0 }}>Sentiment</Title>
                    <Text type="secondary">Market mood</Text>
                  </div>
                  <Tag color={sentiment.color} style={{ fontSize: 16, padding: '4px 12px' }}>
                    {sentiment.rating}
                  </Tag>
                  <ArrowRightOutlined style={{ color: '#999' }} />
                </Space>

                <Paragraph style={{ margin: 0, color: '#666' }}>
                  Assessing market mood and opinions from news, analyst ratings, and social signals to gauge overall sentiment.
                </Paragraph>

                {typeof sentiment.score === 'number' && (
                  <Progress
                    percent={sentiment.score}
                    strokeColor={sentiment.color}
                    showInfo={false}
                    size="small"
                  />
                )}
              </Space>
            </Card>
          </motion.div>
        </Col>
      </Row>

      {/* Investor Trend Card */}
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.3, delay: 0.3 }}
      >
        <Card style={{ marginTop: 24 }} className="investor-trend-card">
          <Title level={4}>
            <TeamOutlined style={{ marginRight: 8 }} />
            Investor Sentiment Trend
          </Title>

          <Row gutter={[16, 16]} style={{ marginTop: 24 }}>
            <Col xs={24} md={12}>
              <div className="trend-visual">
                <Space direction="vertical" style={{ width: '100%' }} size="small">
                  <Space style={{ width: '100%', justifyContent: 'space-between' }}>
                    <Text>Buy ({investorTrend.buy}%)</Text>
                    <Progress
                      percent={investorTrend.buy}
                      strokeColor="#52c41a"
                      showInfo={false}
                      style={{ width: 200 }}
                    />
                  </Space>

                  <Space style={{ width: '100%', justifyContent: 'space-between' }}>
                    <Text>Hold ({investorTrend.hold}%)</Text>
                    <Progress
                      percent={investorTrend.hold}
                      strokeColor="#faad14"
                      showInfo={false}
                      style={{ width: 200 }}
                    />
                  </Space>

                  <Space style={{ width: '100%', justifyContent: 'space-between' }}>
                    <Text>Sell ({investorTrend.sell}%)</Text>
                    <Progress
                      percent={investorTrend.sell}
                      strokeColor="#f5222d"
                      showInfo={false}
                      style={{ width: 200 }}
                    />
                  </Space>
                </Space>
              </div>
            </Col>

            <Col xs={24} md={12}>
              <div style={{ textAlign: 'center', padding: '20px' }}>
                <Avatar
                  size={80}
                  style={{ backgroundColor: maxTrend.color + '20', marginBottom: 16 }}
                >
                  <Title level={2} style={{ margin: 0, color: maxTrend.color }}>
                    {maxTrend.label}
                  </Title>
                </Avatar>
                <Paragraph style={{ color: '#666' }}>
                  Majority of investors are choosing to <strong>{maxTrend.label.toLowerCase()}</strong> based on current market conditions and analysis.
                  This represents the community's collective assessment of the stock's near-term prospects.
                </Paragraph>
              </div>
            </Col>
          </Row>
        </Card>
      </motion.div>

      {/* Competitive Position Card */}
      {competitive && (
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.3, delay: 0.4 }}
        >
          <Card style={{ marginTop: 24 }} className="competitive-position-card">
            <Title level={4}>
              <TrophyOutlined style={{ marginRight: 8 }} />
              Competitive Position
            </Title>

            <Row gutter={[16, 16]} style={{ marginTop: 24 }}>
              <Col xs={12} md={6}>
                <div style={{ textAlign: 'center' }}>
                  <Text type="secondary">Market Share</Text>
                  <Title level={3} style={{ margin: '8px 0' }}>
                    {competitive?.market_analysis?.market_share?.revenue_share?.toFixed(1) || '0'}%
                  </Title>
                </div>
              </Col>

              <Col xs={12} md={6}>
                <div style={{ textAlign: 'center' }}>
                  <Text type="secondary">Revenue Rank</Text>
                  <Title level={3} style={{ margin: '8px 0' }}>
                    {competitive?.market_analysis?.market_position?.revenue_rank || 'N/A'}
                  </Title>
                </div>
              </Col>

              <Col xs={12} md={6}>
                <div style={{ textAlign: 'center' }}>
                  <Text type="secondary">Moat Rating</Text>
                  <Title level={3} style={{ margin: '8px 0', fontSize: 18 }}>
                    {competitive?.competitive_assessment?.moat_analysis?.moat_rating || 'N/A'}
                  </Title>
                </div>
              </Col>

              <Col xs={12} md={6}>
                <div style={{ textAlign: 'center' }}>
                  <Text type="secondary">Competitive Score</Text>
                  <Title level={3} style={{ margin: '8px 0' }}>
                    {competitive?.comparative_metrics?.composite_score?.overall_score?.toFixed(0) || '0'}%
                  </Title>
                </div>
              </Col>
            </Row>

            {competitive?.competitive_assessment?.strategic_position && (
              <div style={{ marginTop: 24, padding: 16, backgroundColor: '#f0f2f5', borderRadius: 8 }}>
                <Text strong>Strategic Position: </Text>
                <Text>{competitive.competitive_assessment.strategic_position}</Text>
              </div>
            )}
          </Card>
        </motion.div>
      )}

    </div>
  );
};

export default PerformanceCards;