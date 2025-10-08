/**
 * Insider Activity Analysis Display Component
 * Shows insider trading, institutional ownership, and smart money sentiment
 */

import React from 'react';
import { Card, Row, Col, Statistic, Tag, Progress, Table, Space, Badge, Tooltip } from 'antd';
import {
  TeamOutlined,
  UserOutlined,
  TrophyOutlined,
  RiseOutlined,
  FallOutlined,
  InfoCircleOutlined
} from '@ant-design/icons';
import type { ColumnsType } from 'antd/es/table';

interface InsiderData {
  symbol: string;
  insider_trading: {
    sentiment: 'BULLISH' | 'NEUTRAL' | 'BEARISH';
    net_buys: number;
    buy_transactions: number;
    sell_transactions: number;
    notable_transactions: Array<{
      insider: string;
      position: string;
      transaction_type: 'BUY' | 'SELL';
      shares: number;
      value: number;
    }>;
  };
  institutional_ownership: {
    ownership_percentage: number;
    trend: 'INCREASING' | 'STABLE' | 'DECREASING';
    top_holders: Array<{
      institution: string;
      shares: number;
      change: number;
    }>;
  };
  analyst_ratings: {
    consensus: 'STRONG_BUY' | 'BUY' | 'HOLD' | 'SELL' | 'STRONG_SELL';
    average_target: number;
    recent_changes: Array<{
      firm: string;
      action: 'UPGRADE' | 'DOWNGRADE' | 'INITIATE';
      from_rating: string;
      to_rating: string;
    }>;
  };
  smart_money_score: number; // -10 to +10
  confidence_score: number;
}

interface InsiderActivityDisplayProps {
  data: Record<string, InsiderData>;
}

const InsiderActivityDisplay: React.FC<InsiderActivityDisplayProps> = ({ data }) => {
  if (!data || Object.keys(data).length === 0) {
    return (
      <Card title="Insider Activity Analysis">
        <p>No insider activity data available</p>
      </Card>
    );
  }

  const getSentimentColor = (sentiment: string) => {
    switch (sentiment) {
      case 'BULLISH':
      case 'STRONG_BUY':
      case 'BUY':
        return 'green';
      case 'NEUTRAL':
      case 'HOLD':
        return 'blue';
      case 'BEARISH':
      case 'SELL':
      case 'STRONG_SELL':
        return 'red';
      default:
        return 'default';
    }
  };

  const getSmartMoneyColor = (score: number) => {
    if (score >= 5) return '#3f8600';
    if (score <= -5) return '#cf1322';
    return '#1890ff';
  };

  const getTransactionIcon = (type: string) => {
    return type === 'BUY' ? <RiseOutlined style={{ color: '#3f8600' }} /> : <FallOutlined style={{ color: '#cf1322' }} />;
  };

  const transactionColumns: ColumnsType<any> = [
    {
      title: 'Insider',
      dataIndex: 'insider',
      key: 'insider',
      render: (text: string, record: any) => (
        <div>
          <div style={{ fontWeight: 500 }}>{text}</div>
          <div style={{ fontSize: 12, color: '#666' }}>{record.position}</div>
        </div>
      ),
    },
    {
      title: 'Type',
      dataIndex: 'transaction_type',
      key: 'transaction_type',
      render: (type: string) => (
        <Tag color={type === 'BUY' ? 'green' : 'red'} icon={getTransactionIcon(type)}>
          {type}
        </Tag>
      ),
    },
    {
      title: 'Shares',
      dataIndex: 'shares',
      key: 'shares',
      render: (shares: number) => shares.toLocaleString(),
    },
    {
      title: 'Value',
      dataIndex: 'value',
      key: 'value',
      render: (value: number) => `$${(value / 1e6).toFixed(2)}M`,
    },
  ];

  const holderColumns: ColumnsType<any> = [
    {
      title: 'Institution',
      dataIndex: 'institution',
      key: 'institution',
    },
    {
      title: 'Shares',
      dataIndex: 'shares',
      key: 'shares',
      render: (shares: number) => (shares / 1e6).toFixed(2) + 'M',
    },
    {
      title: 'Change',
      dataIndex: 'change',
      key: 'change',
      render: (change: number) => (
        <Tag color={change >= 0 ? 'green' : 'red'} icon={change >= 0 ? <RiseOutlined /> : <FallOutlined />}>
          {change >= 0 ? '+' : ''}{change.toFixed(1)}%
        </Tag>
      ),
    },
  ];

  return (
    <Space direction="vertical" size="large" style={{ width: '100%' }}>
      {Object.entries(data).map(([symbol, insider]) => (
        <Card
          key={symbol}
          title={
            <Space>
              <TeamOutlined />
              {`${symbol} - Smart Money Analysis`}
            </Space>
          }
          extra={
            <Tooltip title="Overall confidence in analysis">
              <Tag icon={<InfoCircleOutlined />} color="blue">
                Confidence: {(insider.confidence_score * 100).toFixed(0)}%
              </Tag>
            </Tooltip>
          }
        >
          {/* Smart Money Score */}
          <Card type="inner" size="small" style={{ marginBottom: 16, textAlign: 'center', backgroundColor: '#f0f2f5' }}>
            <Row gutter={16} align="middle" justify="center">
              <Col>
                <TrophyOutlined style={{ fontSize: 32, color: getSmartMoneyColor(insider.smart_money_score) }} />
              </Col>
              <Col>
                <Statistic
                  title="Smart Money Score"
                  value={insider.smart_money_score}
                  precision={1}
                  valueStyle={{ color: getSmartMoneyColor(insider.smart_money_score), fontSize: 32 }}
                  suffix={
                    <span style={{ fontSize: 14, color: '#666' }}>/ 10</span>
                  }
                />
              </Col>
              <Col>
                <Progress
                  type="circle"
                  percent={((insider.smart_money_score + 10) / 20) * 100}
                  format={() => insider.smart_money_score >= 0 ? 'Bullish' : 'Bearish'}
                  strokeColor={getSmartMoneyColor(insider.smart_money_score)}
                  width={80}
                />
              </Col>
            </Row>
          </Card>

          {/* Insider Trading */}
          <Card type="inner" title={<Space><UserOutlined />Insider Trading</Space>} size="small" style={{ marginBottom: 16 }}>
            <Row gutter={16} style={{ marginBottom: 16 }}>
              <Col span={6}>
                <div style={{ textAlign: 'center' }}>
                  <div style={{ fontSize: 12, color: '#666', marginBottom: 4 }}>Sentiment</div>
                  <Tag color={getSentimentColor(insider.insider_trading.sentiment)} style={{ fontSize: 14 }}>
                    {insider.insider_trading.sentiment}
                  </Tag>
                </div>
              </Col>
              <Col span={6}>
                <Statistic
                  title="Net Insider Buys"
                  value={insider.insider_trading.net_buys}
                  valueStyle={{ color: insider.insider_trading.net_buys >= 0 ? '#3f8600' : '#cf1322' }}
                  prefix={insider.insider_trading.net_buys >= 0 ? '+' : ''}
                />
              </Col>
              <Col span={6}>
                <Statistic
                  title="Buy Transactions"
                  value={insider.insider_trading.buy_transactions}
                  valueStyle={{ color: '#3f8600' }}
                />
              </Col>
              <Col span={6}>
                <Statistic
                  title="Sell Transactions"
                  value={insider.insider_trading.sell_transactions}
                  valueStyle={{ color: '#cf1322' }}
                />
              </Col>
            </Row>

            {insider.insider_trading.notable_transactions.length > 0 && (
              <>
                <div style={{ marginBottom: 8, fontWeight: 500 }}>Notable Transactions:</div>
                <Table
                  columns={transactionColumns}
                  dataSource={insider.insider_trading.notable_transactions.map((t, i) => ({ ...t, key: i }))}
                  pagination={false}
                  size="small"
                />
              </>
            )}
          </Card>

          {/* Institutional Ownership */}
          <Card type="inner" title={<Space><TeamOutlined />Institutional Ownership</Space>} size="small" style={{ marginBottom: 16 }}>
            <Row gutter={16} style={{ marginBottom: 16 }}>
              <Col span={12}>
                <Statistic
                  title="Institutional Ownership"
                  value={insider.institutional_ownership.ownership_percentage}
                  precision={1}
                  suffix="%"
                  valueStyle={{ color: '#1890ff' }}
                />
                <Progress
                  percent={insider.institutional_ownership.ownership_percentage}
                  status="active"
                  showInfo={false}
                />
              </Col>
              <Col span={12}>
                <div style={{ marginBottom: 8 }}>
                  <div style={{ fontSize: 12, color: '#666', marginBottom: 4 }}>Trend</div>
                  <Tag
                    icon={
                      insider.institutional_ownership.trend === 'INCREASING' ? (
                        <RiseOutlined />
                      ) : insider.institutional_ownership.trend === 'DECREASING' ? (
                        <FallOutlined />
                      ) : undefined
                    }
                    color={
                      insider.institutional_ownership.trend === 'INCREASING'
                        ? 'green'
                        : insider.institutional_ownership.trend === 'DECREASING'
                        ? 'red'
                        : 'blue'
                    }
                    style={{ fontSize: 14 }}
                  >
                    {insider.institutional_ownership.trend}
                  </Tag>
                </div>
              </Col>
            </Row>

            {insider.institutional_ownership.top_holders.length > 0 && (
              <>
                <div style={{ marginBottom: 8, fontWeight: 500 }}>Top Institutional Holders:</div>
                <Table
                  columns={holderColumns}
                  dataSource={insider.institutional_ownership.top_holders.map((h, i) => ({ ...h, key: i }))}
                  pagination={false}
                  size="small"
                />
              </>
            )}
          </Card>

          {/* Analyst Ratings */}
          <Card type="inner" title="Analyst Consensus" size="small">
            <Row gutter={16}>
              <Col span={8}>
                <div style={{ textAlign: 'center' }}>
                  <div style={{ fontSize: 12, color: '#666', marginBottom: 4 }}>Consensus</div>
                  <Tag color={getSentimentColor(insider.analyst_ratings.consensus)} style={{ fontSize: 14, padding: '4px 12px' }}>
                    {insider.analyst_ratings.consensus.replace('_', ' ')}
                  </Tag>
                </div>
              </Col>
              <Col span={8}>
                <Statistic
                  title="Average Price Target"
                  value={insider.analyst_ratings.average_target}
                  precision={2}
                  prefix="$"
                  valueStyle={{ color: '#1890ff' }}
                />
              </Col>
              <Col span={8}>
                <div style={{ fontSize: 12, color: '#666', marginBottom: 8 }}>Recent Changes:</div>
                <Space direction="vertical" size="small">
                  {insider.analyst_ratings.recent_changes.slice(0, 3).map((change, i) => (
                    <Badge
                      key={i}
                      status={change.action === 'UPGRADE' ? 'success' : change.action === 'DOWNGRADE' ? 'error' : 'default'}
                      text={
                        <span style={{ fontSize: 12 }}>
                          {change.firm}: {change.action}
                        </span>
                      }
                    />
                  ))}
                </Space>
              </Col>
            </Row>
          </Card>
        </Card>
      ))}
    </Space>
  );
};

export default InsiderActivityDisplay;
