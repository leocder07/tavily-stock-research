/**
 * Macro Economics Analysis Display Component
 * Shows Fed policy, GDP trends, inflation, and economic cycle assessment
 */

import React from 'react';
import { Card, Row, Col, Statistic, Tag, Timeline, Badge, Space, Progress, Alert } from 'antd';
import {
  BankOutlined,
  LineChartOutlined,
  DollarCircleOutlined,
  RiseOutlined,
  FallOutlined,
  WarningOutlined
} from '@ant-design/icons';

interface MacroData {
  symbols: string[];
  fed_policy: {
    current_rate: number;
    stance: 'DOVISH' | 'NEUTRAL' | 'HAWKISH';
    direction: 'EASING' | 'NEUTRAL' | 'TIGHTENING';
    next_move_probability: { hike: number; hold: number; cut: number };
  };
  gdp_trends: {
    current_growth: number;
    unemployment_rate: number;
    consumer_spending_trend: 'STRONG' | 'MODERATE' | 'WEAK';
  };
  inflation: {
    cpi: number;
    core_cpi: number;
    trend: 'RISING' | 'STABLE' | 'FALLING';
  };
  economic_cycle: {
    phase: 'EARLY_CYCLE' | 'MID_CYCLE' | 'LATE_CYCLE' | 'RECESSION';
    indicators: Array<{
      name: string;
      status: 'POSITIVE' | 'NEUTRAL' | 'NEGATIVE';
      signal: string;
    }>;
  };
  market_impact: {
    overall_rating: 'BULLISH' | 'NEUTRAL' | 'BEARISH';
    sector_preferences: Array<{ sector: string; rating: string }>;
  };
  confidence_score: number;
}

interface MacroEconomicsDisplayProps {
  data: MacroData;
}

const MacroEconomicsDisplay: React.FC<MacroEconomicsDisplayProps> = ({ data }) => {
  if (!data) {
    return (
      <Card title="Macro Economics Analysis">
        <p>No macro economics data available</p>
      </Card>
    );
  }

  const getStanceColor = (stance: string) => {
    switch (stance) {
      case 'DOVISH':
        return 'green';
      case 'NEUTRAL':
        return 'blue';
      case 'HAWKISH':
        return 'red';
      default:
        return 'default';
    }
  };

  const getCycleColor = (phase: string) => {
    switch (phase) {
      case 'EARLY_CYCLE':
        return 'green';
      case 'MID_CYCLE':
        return 'blue';
      case 'LATE_CYCLE':
        return 'orange';
      case 'RECESSION':
        return 'red';
      default:
        return 'default';
    }
  };

  const getRatingIcon = (rating: string) => {
    switch (rating) {
      case 'BULLISH':
      case 'POSITIVE':
        return <RiseOutlined style={{ color: '#3f8600' }} />;
      case 'BEARISH':
      case 'NEGATIVE':
        return <FallOutlined style={{ color: '#cf1322' }} />;
      default:
        return <LineChartOutlined />;
    }
  };

  const getStatusBadge = (status: string) => {
    switch (status) {
      case 'POSITIVE':
        return <Badge status="success" text="Positive" />;
      case 'NEUTRAL':
        return <Badge status="default" text="Neutral" />;
      case 'NEGATIVE':
        return <Badge status="error" text="Negative" />;
      default:
        return <Badge status="default" text={status} />;
    }
  };

  return (
    <Card
      title={
        <Space>
          <BankOutlined />
          Macro Economics Analysis
        </Space>
      }
      extra={
        <Tag color="blue">
          Confidence: {(data.confidence_score * 100).toFixed(0)}%
        </Tag>
      }
    >
      {/* Overall Market Impact */}
      <Alert
        message={
          <Space>
            {getRatingIcon(data.market_impact.overall_rating)}
            <strong>Overall Market Assessment: {data.market_impact.overall_rating}</strong>
          </Space>
        }
        type={data.market_impact.overall_rating === 'BULLISH' ? 'success' : data.market_impact.overall_rating === 'BEARISH' ? 'error' : 'info'}
        style={{ marginBottom: 24 }}
      />

      {/* Economic Cycle */}
      <Card type="inner" title="Economic Cycle" size="small" style={{ marginBottom: 16 }}>
        <Row gutter={16} align="middle">
          <Col span={8}>
            <div style={{ textAlign: 'center' }}>
              <Tag color={getCycleColor(data.economic_cycle.phase)} style={{ fontSize: 16, padding: '8px 16px' }}>
                {data.economic_cycle.phase.replace('_', ' ')}
              </Tag>
            </div>
          </Col>
          <Col span={16}>
            <Timeline
              items={data.economic_cycle.indicators.map((indicator) => ({
                color: indicator.status === 'POSITIVE' ? 'green' : indicator.status === 'NEGATIVE' ? 'red' : 'blue',
                children: (
                  <div>
                    <Space>
                      {getStatusBadge(indicator.status)}
                      <strong>{indicator.name}:</strong>
                      {indicator.signal}
                    </Space>
                  </div>
                ),
              }))}
            />
          </Col>
        </Row>
      </Card>

      {/* Fed Policy */}
      <Card type="inner" title={<Space><BankOutlined />Federal Reserve Policy</Space>} size="small" style={{ marginBottom: 16 }}>
        <Row gutter={16}>
          <Col span={8}>
            <Statistic
              title="Fed Funds Rate"
              value={data.fed_policy.current_rate}
              precision={2}
              suffix="%"
              prefix={<BankOutlined />}
            />
          </Col>
          <Col span={8}>
            <div style={{ marginBottom: 8 }}>
              <div style={{ fontSize: 12, color: '#666', marginBottom: 4 }}>Policy Stance</div>
              <Tag color={getStanceColor(data.fed_policy.stance)} style={{ fontSize: 14 }}>
                {data.fed_policy.stance}
              </Tag>
            </div>
            <div>
              <div style={{ fontSize: 12, color: '#666', marginBottom: 4 }}>Direction</div>
              <Tag color={data.fed_policy.direction === 'TIGHTENING' ? 'red' : data.fed_policy.direction === 'EASING' ? 'green' : 'blue'}>
                {data.fed_policy.direction}
              </Tag>
            </div>
          </Col>
          <Col span={8}>
            <div style={{ fontSize: 12, color: '#666', marginBottom: 8 }}>Next Move Probability</div>
            <Space direction="vertical" style={{ width: '100%' }}>
              <div>
                <span style={{ fontSize: 12 }}>Hike:</span>
                <Progress
                  percent={data.fed_policy.next_move_probability.hike * 100}
                  size="small"
                  strokeColor="#cf1322"
                  showInfo={true}
                  format={(percent) => `${percent?.toFixed(0)}%`}
                />
              </div>
              <div>
                <span style={{ fontSize: 12 }}>Hold:</span>
                <Progress
                  percent={data.fed_policy.next_move_probability.hold * 100}
                  size="small"
                  strokeColor="#1890ff"
                  showInfo={true}
                  format={(percent) => `${percent?.toFixed(0)}%`}
                />
              </div>
              <div>
                <span style={{ fontSize: 12 }}>Cut:</span>
                <Progress
                  percent={data.fed_policy.next_move_probability.cut * 100}
                  size="small"
                  strokeColor="#3f8600"
                  showInfo={true}
                  format={(percent) => `${percent?.toFixed(0)}%`}
                />
              </div>
            </Space>
          </Col>
        </Row>
      </Card>

      {/* GDP & Employment */}
      <Card type="inner" title={<Space><LineChartOutlined />GDP & Employment</Space>} size="small" style={{ marginBottom: 16 }}>
        <Row gutter={16}>
          <Col span={8}>
            <Statistic
              title="GDP Growth"
              value={data.gdp_trends.current_growth}
              precision={1}
              suffix="%"
              valueStyle={{ color: data.gdp_trends.current_growth >= 2 ? '#3f8600' : '#cf1322' }}
            />
          </Col>
          <Col span={8}>
            <Statistic
              title="Unemployment Rate"
              value={data.gdp_trends.unemployment_rate}
              precision={1}
              suffix="%"
              valueStyle={{ color: data.gdp_trends.unemployment_rate <= 4.5 ? '#3f8600' : '#cf1322' }}
            />
          </Col>
          <Col span={8}>
            <div style={{ marginBottom: 8 }}>
              <div style={{ fontSize: 12, color: '#666', marginBottom: 4 }}>Consumer Spending</div>
              <Tag
                color={
                  data.gdp_trends.consumer_spending_trend === 'STRONG'
                    ? 'green'
                    : data.gdp_trends.consumer_spending_trend === 'WEAK'
                    ? 'red'
                    : 'blue'
                }
                style={{ fontSize: 14 }}
              >
                {data.gdp_trends.consumer_spending_trend}
              </Tag>
            </div>
          </Col>
        </Row>
      </Card>

      {/* Inflation */}
      <Card type="inner" title={<Space><DollarCircleOutlined />Inflation</Space>} size="small" style={{ marginBottom: 16 }}>
        <Row gutter={16}>
          <Col span={8}>
            <Statistic
              title="CPI (Headline)"
              value={data.inflation.cpi}
              precision={1}
              suffix="%"
              valueStyle={{ color: data.inflation.cpi <= 2.5 ? '#3f8600' : '#cf1322' }}
            />
          </Col>
          <Col span={8}>
            <Statistic
              title="Core CPI"
              value={data.inflation.core_cpi}
              precision={1}
              suffix="%"
              valueStyle={{ color: data.inflation.core_cpi <= 2.5 ? '#3f8600' : '#cf1322' }}
            />
          </Col>
          <Col span={8}>
            <div style={{ marginBottom: 8 }}>
              <div style={{ fontSize: 12, color: '#666', marginBottom: 4 }}>Trend</div>
              <Tag
                icon={data.inflation.trend === 'RISING' ? <RiseOutlined /> : data.inflation.trend === 'FALLING' ? <FallOutlined /> : undefined}
                color={
                  data.inflation.trend === 'FALLING' ? 'green' : data.inflation.trend === 'RISING' ? 'red' : 'blue'
                }
                style={{ fontSize: 14 }}
              >
                {data.inflation.trend}
              </Tag>
            </div>
          </Col>
        </Row>
      </Card>

      {/* Sector Preferences */}
      {data.market_impact.sector_preferences.length > 0 && (
        <Card type="inner" title="Recommended Sector Allocation" size="small">
          <Space wrap>
            {data.market_impact.sector_preferences.map((sector) => (
              <Tag
                key={sector.sector}
                color={sector.rating === 'OVERWEIGHT' ? 'green' : sector.rating === 'UNDERWEIGHT' ? 'red' : 'blue'}
                style={{ fontSize: 12, padding: '4px 8px' }}
              >
                {sector.sector}: {sector.rating}
              </Tag>
            ))}
          </Space>
        </Card>
      )}
    </Card>
  );
};

export default MacroEconomicsDisplay;
