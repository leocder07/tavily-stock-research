import React from 'react';
import { Row, Col, Card, Typography, Space, Divider } from 'antd';
import { TrophyOutlined, DollarOutlined } from '@ant-design/icons';
import AnalystRatingsChart from './AnalystRatingsChart';
import PriceTargetCard from './PriceTargetCard';

const { Title, Text, Paragraph } = Typography;

interface AnalystInsightsSectionProps {
  fundamentalData?: {
    symbol?: string;
    name?: string;
    peg_ratio?: number;
    analyst_ratings?: {
      strong_buy: number;
      buy: number;
      hold: number;
      sell: number;
      strong_sell: number;
    };
    analyst_consensus?: string;
    analyst_consensus_score?: number;
    analyst_target_price?: number;
    price?: number;
  };
  marketData?: {
    price?: number;
  };
}

const AnalystInsightsSection: React.FC<AnalystInsightsSectionProps> = ({
  fundamentalData = {},
  marketData = {},
}) => {
  const {
    symbol = '',
    name = '',
    peg_ratio,
    analyst_ratings,
    analyst_consensus,
    analyst_consensus_score = 0,
    analyst_target_price,
  } = fundamentalData;

  // Get current price from market data or fundamental data
  const currentPrice = marketData.price || fundamentalData.price || 0;

  // If no analyst data, don't render
  if (!analyst_ratings || !analyst_target_price) {
    return null;
  }

  const totalAnalysts = Object.values(analyst_ratings).reduce((a, b) => a + b, 0);

  if (totalAnalysts === 0) {
    return null;
  }

  return (
    <Card
      title={
        <Space>
          <TrophyOutlined style={{ color: '#1890ff' }} />
          <span>Analyst Insights</span>
        </Space>
      }
      style={{ marginTop: 24 }}
      bordered={false}
    >
      <Space direction="vertical" size="large" style={{ width: '100%' }}>
        {/* Header with stock info */}
        <div>
          <Title level={4} style={{ margin: 0 }}>
            {name} ({symbol})
          </Title>
          <Text type="secondary">Professional analyst coverage and price targets</Text>
        </div>

        <Divider style={{ margin: '12px 0' }} />

        {/* Main content - Ratings and Price Target */}
        <Row gutter={[24, 24]}>
          <Col xs={24} lg={12}>
            <AnalystRatingsChart
              ratings={analyst_ratings}
              consensus={analyst_consensus}
              consensusScore={analyst_consensus_score}
            />
          </Col>

          <Col xs={24} lg={12}>
            <PriceTargetCard
              currentPrice={currentPrice}
              targetPrice={analyst_target_price}
              symbol={symbol}
            />
          </Col>
        </Row>

        {/* Additional metrics */}
        {peg_ratio && (
          <Card size="small" style={{ background: '#f0f5ff', border: 'none' }}>
            <Space direction="vertical" size="small">
              <Text strong>
                <DollarOutlined style={{ marginRight: 8, color: '#1890ff' }} />
                PEG Ratio (Price/Earnings to Growth)
              </Text>
              <div>
                <Text style={{ fontSize: '24px', fontWeight: 600, color: '#1890ff' }}>
                  {peg_ratio.toFixed(2)}
                </Text>
                <Text type="secondary" style={{ marginLeft: 12 }}>
                  {peg_ratio < 1
                    ? 'Potentially undervalued relative to growth'
                    : peg_ratio < 2
                    ? 'Fairly valued considering growth prospects'
                    : 'Expensive relative to growth rate'}
                </Text>
              </div>
            </Space>
          </Card>
        )}

        {/* Interpretation guide */}
        <Card size="small" style={{ background: '#fafafa', border: 'none' }}>
          <Title level={5}>How to Interpret</Title>
          <Space direction="vertical" size="small">
            <Text>
              • <strong>Analyst Ratings:</strong> Based on {totalAnalysts} professional analysts' recommendations
            </Text>
            <Text>
              • <strong>Price Target:</strong> Average 12-month price target from analyst estimates
            </Text>
            {peg_ratio && (
              <Text>
                • <strong>PEG Ratio:</strong> Values below 1.0 may indicate undervaluation, above 2.0 suggest premium pricing
              </Text>
            )}
          </Space>
        </Card>
      </Space>
    </Card>
  );
};

export default AnalystInsightsSection;
