import React from 'react';
import { Card, Typography, Space, Tooltip } from 'antd';
import { StarFilled, StarOutlined } from '@ant-design/icons';
import './AnalystRatings.css';

const { Text, Title } = Typography;

interface AnalystRatings {
  strong_buy: number;
  buy: number;
  hold: number;
  sell: number;
  strong_sell: number;
}

interface AnalystRatingsChartProps {
  ratings: AnalystRatings;
  consensus?: string;
  consensusScore?: number;
}

const AnalystRatingsChart: React.FC<AnalystRatingsChartProps> = ({
  ratings,
  consensus = 'No Coverage',
  consensusScore = 0,
}) => {
  const totalAnalysts = Object.values(ratings).reduce((a, b) => a + b, 0);

  if (totalAnalysts === 0) {
    return (
      <Card className="analyst-ratings-card" bordered={false}>
        <Space direction="vertical" size="small" style={{ width: '100%' }}>
          <Text type="secondary">No analyst coverage available</Text>
        </Space>
      </Card>
    );
  }

  // Calculate percentages
  const getPercentage = (value: number) => ((value / totalAnalysts) * 100).toFixed(1);

  // Rating data with colors
  const ratingData = [
    {
      label: 'Strong Buy',
      value: ratings.strong_buy,
      percentage: getPercentage(ratings.strong_buy),
      color: '#10b981', // Emerald green
    },
    {
      label: 'Buy',
      value: ratings.buy,
      percentage: getPercentage(ratings.buy),
      color: '#52c41a', // Success green
    },
    {
      label: 'Hold',
      value: ratings.hold,
      percentage: getPercentage(ratings.hold),
      color: '#faad14', // Warning orange
    },
    {
      label: 'Sell',
      value: ratings.sell,
      percentage: getPercentage(ratings.sell),
      color: '#ff7875', // Light red
    },
    {
      label: 'Strong Sell',
      value: ratings.strong_sell,
      percentage: getPercentage(ratings.strong_sell),
      color: '#f5222d', // Error red
    },
  ];

  // Render star rating based on consensus score
  const renderStars = (score: number) => {
    const fullStars = Math.floor(score);
    const stars = [];

    for (let i = 0; i < 5; i++) {
      if (i < fullStars) {
        stars.push(<StarFilled key={i} style={{ color: '#fadb14', fontSize: '18px' }} />);
      } else {
        stars.push(<StarOutlined key={i} style={{ color: '#d9d9d9', fontSize: '18px' }} />);
      }
    }

    return stars;
  };

  // Get consensus color
  const getConsensusColor = (cons: string) => {
    switch (cons.toLowerCase()) {
      case 'strong buy':
        return '#10b981';
      case 'buy':
        return '#52c41a';
      case 'hold':
        return '#faad14';
      case 'sell':
        return '#ff7875';
      case 'strong sell':
        return '#f5222d';
      default:
        return '#8c8c8c';
    }
  };

  return (
    <Card className="analyst-ratings-card" bordered={false}>
      <Space direction="vertical" size="large" style={{ width: '100%' }}>
        {/* Header with consensus */}
        <div>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 8 }}>
            <Title level={5} style={{ margin: 0 }}>Analyst Ratings</Title>
            <Text type="secondary">{totalAnalysts} Analysts</Text>
          </div>

          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
            <div>
              <Text strong style={{ fontSize: '20px', color: getConsensusColor(consensus) }}>
                {consensus}
              </Text>
              <div style={{ marginTop: 4 }}>
                {renderStars(consensusScore)}
                <Text type="secondary" style={{ marginLeft: 8 }}>
                  {consensusScore.toFixed(1)}/5.0
                </Text>
              </div>
            </div>
          </div>
        </div>

        {/* Rating bars */}
        <div className="ratings-bars">
          {ratingData.map((rating) => (
            <div key={rating.label} className="rating-bar-container">
              <div className="rating-label">
                <Text style={{ fontSize: '13px', width: '90px', display: 'inline-block' }}>
                  {rating.label}
                </Text>
                <Text type="secondary" style={{ fontSize: '13px', width: '35px', textAlign: 'right', display: 'inline-block' }}>
                  {rating.value}
                </Text>
              </div>

              <Tooltip title={`${rating.percentage}% (${rating.value} analysts)`}>
                <div className="rating-bar-track">
                  <div
                    className="rating-bar-fill"
                    style={{
                      width: `${rating.percentage}%`,
                      backgroundColor: rating.color,
                    }}
                  />
                </div>
              </Tooltip>
            </div>
          ))}
        </div>

        {/* Summary stats */}
        <div className="rating-summary">
          <div className="rating-stat">
            <Text type="secondary" style={{ fontSize: '12px' }}>Bullish</Text>
            <Text strong style={{ color: '#52c41a' }}>
              {((ratings.strong_buy + ratings.buy) / totalAnalysts * 100).toFixed(0)}%
            </Text>
          </div>
          <div className="rating-stat">
            <Text type="secondary" style={{ fontSize: '12px' }}>Neutral</Text>
            <Text strong style={{ color: '#faad14' }}>
              {(ratings.hold / totalAnalysts * 100).toFixed(0)}%
            </Text>
          </div>
          <div className="rating-stat">
            <Text type="secondary" style={{ fontSize: '12px' }}>Bearish</Text>
            <Text strong style={{ color: '#f5222d' }}>
              {((ratings.sell + ratings.strong_sell) / totalAnalysts * 100).toFixed(0)}%
            </Text>
          </div>
        </div>
      </Space>
    </Card>
  );
};

export default AnalystRatingsChart;
