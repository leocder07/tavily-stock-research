import React from 'react';
import { Card, Typography, Space, Progress, Statistic } from 'antd';
import { ArrowUpOutlined, ArrowDownOutlined, AimOutlined } from '@ant-design/icons';
import './PriceTarget.css';

const { Text, Title } = Typography;

interface PriceTargetCardProps {
  currentPrice: number;
  targetPrice: number;
  symbol: string;
}

const PriceTargetCard: React.FC<PriceTargetCardProps> = ({
  currentPrice,
  targetPrice,
  symbol,
}) => {
  // Calculate potential gain/loss
  const priceDiff = targetPrice - currentPrice;
  const percentChange = ((priceDiff / currentPrice) * 100);
  const isUpside = priceDiff > 0;

  // Calculate progress (how far current price is toward target)
  const getProgress = () => {
    if (isUpside) {
      // For upside, progress is 0 at current, 100 at target
      return 0;
    } else {
      // For downside, current is above target
      return 100 - Math.min(100, Math.abs(percentChange));
    }
  };

  // Get color based on potential
  const getColor = () => {
    if (Math.abs(percentChange) < 5) return '#8c8c8c'; // Gray for minimal change
    if (isUpside) return '#52c41a'; // Green for upside
    return '#f5222d'; // Red for downside
  };

  // Format currency
  const formatPrice = (price: number) => `$${price.toFixed(2)}`;

  // Get status text
  const getStatusText = () => {
    if (Math.abs(percentChange) < 5) {
      return 'Near Target';
    }
    return isUpside ? 'Upside Potential' : 'Downside Risk';
  };

  return (
    <Card className="price-target-card" bordered={false}>
      <Space direction="vertical" size="middle" style={{ width: '100%' }}>
        {/* Header */}
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
          <Title level={5} style={{ margin: 0 }}>
            <AimOutlined style={{ marginRight: 8, color: getColor() }} />
            Analyst Price Target
          </Title>
        </div>

        {/* Current vs Target Price */}
        <div className="price-comparison">
          <div className="price-item">
            <Text type="secondary" style={{ fontSize: '12px' }}>Current Price</Text>
            <Text strong style={{ fontSize: '24px', display: 'block' }}>
              {formatPrice(currentPrice)}
            </Text>
          </div>

          <div className="price-arrow">
            {isUpside ? (
              <ArrowUpOutlined style={{ fontSize: '32px', color: '#52c41a' }} />
            ) : (
              <ArrowDownOutlined style={{ fontSize: '32px', color: '#f5222d' }} />
            )}
          </div>

          <div className="price-item">
            <Text type="secondary" style={{ fontSize: '12px' }}>Target Price</Text>
            <Text strong style={{ fontSize: '24px', display: 'block', color: getColor() }}>
              {formatPrice(targetPrice)}
            </Text>
          </div>
        </div>

        {/* Potential change */}
        <div className="potential-change" style={{
          background: isUpside ? '#f6ffed' : '#fff2f0',
          borderRadius: '8px',
          padding: '16px',
          border: `1px solid ${isUpside ? '#b7eb8f' : '#ffccc7'}`
        }}>
          <Space direction="vertical" size="small" style={{ width: '100%' }}>
            <Text type="secondary" style={{ fontSize: '12px' }}>{getStatusText()}</Text>
            <div style={{ display: 'flex', alignItems: 'baseline', gap: '8px' }}>
              <Text strong style={{ fontSize: '28px', color: getColor() }}>
                {isUpside ? '+' : ''}{percentChange.toFixed(1)}%
              </Text>
              <Text type="secondary">
                ({isUpside ? '+' : ''}{formatPrice(Math.abs(priceDiff))})
              </Text>
            </div>

            {/* Visual progress bar */}
            <div style={{ marginTop: 8 }}>
              <Progress
                percent={Math.abs(percentChange)}
                strokeColor={getColor()}
                showInfo={false}
                strokeWidth={8}
              />
            </div>

            <Text type="secondary" style={{ fontSize: '12px', marginTop: 4 }}>
              {isUpside
                ? `Analysts expect ${symbol} to reach ${formatPrice(targetPrice)} representing ${percentChange.toFixed(1)}% upside`
                : `Current price is ${Math.abs(percentChange).toFixed(1)}% above analyst target`
              }
            </Text>
          </Space>
        </div>

        {/* Additional context */}
        <div className="target-context">
          <Space size="large" style={{ width: '100%', justifyContent: 'space-around' }}>
            <div style={{ textAlign: 'center' }}>
              <Text type="secondary" style={{ fontSize: '12px' }}>Gain Required</Text>
              <Text strong style={{ display: 'block', fontSize: '16px', color: getColor() }}>
                {isUpside ? '+' : ''}{percentChange.toFixed(1)}%
              </Text>
            </div>
            <div style={{ textAlign: 'center' }}>
              <Text type="secondary" style={{ fontSize: '12px' }}>Price Gap</Text>
              <Text strong style={{ display: 'block', fontSize: '16px' }}>
                {formatPrice(Math.abs(priceDiff))}
              </Text>
            </div>
          </Space>
        </div>
      </Space>
    </Card>
  );
};

export default PriceTargetCard;
