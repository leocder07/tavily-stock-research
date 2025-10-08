import React from 'react';
import {
  Card,
  Row,
  Col,
  Statistic,
  Progress,
  Typography,
  Space,
  Tag,
  Divider,
  Alert,
  Badge,
  Tooltip
} from 'antd';
import {
  DollarOutlined,
  ArrowUpOutlined,
  ArrowDownOutlined,
  CalculatorOutlined,
  LineChartOutlined,
  TeamOutlined,
  SafetyCertificateOutlined
} from '@ant-design/icons';

const { Title, Text, Paragraph } = Typography;

interface ValuationDisplayProps {
  valuation: any;
  currentPrice: number;
}

const ValuationDisplay: React.FC<ValuationDisplayProps> = ({ valuation, currentPrice }) => {
  if (!valuation) {
    return (
      <Card>
        <Alert message="No valuation data available" type="info" showIcon />
      </Card>
    );
  }

  const priceTarget = valuation?.price_target?.price_target || currentPrice;
  const upside = valuation?.price_target?.upside || 0;
  const confidence = valuation?.price_target?.confidence || 0.5;
  const dcfPrice = valuation?.dcf_valuation?.dcf_price || currentPrice;
  const wacc = valuation?.dcf_valuation?.wacc || 0;
  const analystConsensus = valuation?.analyst_targets?.analyst_consensus || 'Hold';
  const analystTarget = valuation?.analyst_targets?.target_mean || currentPrice;
  const comparativePrice = valuation?.comparative_valuation?.comparative_price || currentPrice;
  const valuationRating = valuation?.comparative_valuation?.valuation_rating || 'Fair Value';

  const getUpsideColor = (upside: number) => {
    if (upside > 20) return '#52c41a';
    if (upside > 0) return '#1890ff';
    if (upside > -10) return '#faad14';
    return '#f5222d';
  };

  const getValuationIcon = (rating: string) => {
    if (rating.includes('Under')) return <ArrowUpOutlined style={{ color: '#52c41a' }} />;
    if (rating.includes('Over')) return <ArrowDownOutlined style={{ color: '#f5222d' }} />;
    return <SafetyCertificateOutlined style={{ color: '#faad14' }} />;
  };

  return (
    <div className="valuation-display">
      {/* Price Target Summary */}
      <Card
        title={
          <Space>
            <DollarOutlined />
            <Title level={4} style={{ margin: 0 }}>Valuation Analysis</Title>
          </Space>
        }
        style={{ marginBottom: 16 }}
      >
        <Row gutter={[16, 16]}>
          <Col xs={24} sm={12} md={6}>
            <Card size="small" style={{ textAlign: 'center', background: '#f0f2f5' }}>
              <Statistic
                title="Current Price"
                value={currentPrice}
                prefix="$"
                precision={2}
              />
            </Card>
          </Col>
          <Col xs={24} sm={12} md={6}>
            <Card size="small" style={{ textAlign: 'center', background: '#e6f7ff' }}>
              <Statistic
                title="Price Target"
                value={priceTarget}
                prefix="$"
                precision={2}
                valueStyle={{ color: getUpsideColor(upside) }}
              />
              <Text type="secondary" style={{ fontSize: 12 }}>
                {upside >= 0 ? '+' : ''}{upside.toFixed(1)}% upside
              </Text>
            </Card>
          </Col>
          <Col xs={24} sm={12} md={6}>
            <Card size="small" style={{ textAlign: 'center', background: '#f6ffed' }}>
              <Statistic
                title="DCF Fair Value"
                value={dcfPrice}
                prefix="$"
                precision={2}
                valueStyle={{ color: '#52c41a' }}
              />
              <Text type="secondary" style={{ fontSize: 12 }}>
                WACC: {(wacc * 100).toFixed(2)}%
              </Text>
            </Card>
          </Col>
          <Col xs={24} sm={12} md={6}>
            <Card size="small" style={{ textAlign: 'center', background: '#fff7e6' }}>
              <Statistic
                title="Analyst Target"
                value={analystTarget}
                prefix="$"
                precision={2}
              />
              <Tag color={analystConsensus === 'Buy' ? 'green' : analystConsensus === 'Sell' ? 'red' : 'orange'}>
                {analystConsensus}
              </Tag>
            </Card>
          </Col>
        </Row>

        <Divider />

        {/* Confidence Score */}
        <Row gutter={[16, 16]}>
          <Col span={24}>
            <Space direction="vertical" style={{ width: '100%' }}>
              <Space>
                <Text strong>Confidence in Price Target:</Text>
                <Text>{(confidence * 100).toFixed(0)}%</Text>
              </Space>
              <Progress
                percent={confidence * 100}
                strokeColor={{
                  '0%': '#108ee9',
                  '100%': '#87d068',
                }}
                showInfo={false}
              />
            </Space>
          </Col>
        </Row>
      </Card>

      {/* Valuation Methods Breakdown */}
      <Row gutter={[16, 16]}>
        <Col xs={24} md={12}>
          <Card
            title={
              <Space>
                <CalculatorOutlined />
                <Text strong>DCF Analysis</Text>
              </Space>
            }
            size="small"
          >
            <Space direction="vertical" style={{ width: '100%' }}>
              <Row justify="space-between">
                <Text>Fair Value:</Text>
                <Text strong>${dcfPrice?.toFixed(2) || 'N/A'}</Text>
              </Row>
              <Row justify="space-between">
                <Text>vs Current Price:</Text>
                <Text strong style={{ color: getUpsideColor(((dcfPrice - currentPrice) / currentPrice) * 100) }}>
                  {dcfPrice ? `${(((dcfPrice - currentPrice) / currentPrice) * 100).toFixed(1)}%` : 'N/A'}
                </Text>
              </Row>
              <Row justify="space-between">
                <Text>WACC:</Text>
                <Text>{wacc ? `${(wacc * 100).toFixed(2)}%` : 'N/A'}</Text>
              </Row>
              <Row justify="space-between">
                <Text>Terminal Growth:</Text>
                <Text>{valuation?.dcf_valuation?.terminal_growth_rate ?
                  `${valuation.dcf_valuation.terminal_growth_rate.toFixed(1)}%` : '3.0%'}</Text>
              </Row>
            </Space>
          </Card>
        </Col>

        <Col xs={24} md={12}>
          <Card
            title={
              <Space>
                <LineChartOutlined />
                <Text strong>Comparative Valuation</Text>
              </Space>
            }
            size="small"
          >
            <Space direction="vertical" style={{ width: '100%' }}>
              <Row justify="space-between">
                <Text>Peer-Based Price:</Text>
                <Text strong>${comparativePrice?.toFixed(2) || 'N/A'}</Text>
              </Row>
              <Row justify="space-between">
                <Text>P/E Ratio:</Text>
                <Text>{valuation?.comparative_valuation?.pe_ratio || 'N/A'}</Text>
              </Row>
              <Row justify="space-between">
                <Text>PEG Ratio:</Text>
                <Text>{valuation?.comparative_valuation?.peg_ratio || 'N/A'}</Text>
              </Row>
              <Row justify="space-between">
                <Text>Rating:</Text>
                <Badge
                  count={
                    <Space>
                      {getValuationIcon(valuationRating)}
                      <Text style={{ fontSize: 12 }}>{valuationRating}</Text>
                    </Space>
                  }
                  style={{
                    backgroundColor: valuationRating.includes('Under') ? '#52c41a' :
                                   valuationRating.includes('Over') ? '#f5222d' : '#faad14'
                  }}
                />
              </Row>
            </Space>
          </Card>
        </Col>
      </Row>

      {/* Target Range */}
      {valuation?.price_target?.target_range && (
        <Card style={{ marginTop: 16 }} size="small">
          <Row align="middle">
            <Col span={4}>
              <Text>Target Range:</Text>
            </Col>
            <Col span={20}>
              <div style={{ position: 'relative', height: 40, display: 'flex', alignItems: 'center' }}>
                <div
                  style={{
                    position: 'absolute',
                    left: 0,
                    right: 0,
                    height: 4,
                    background: 'linear-gradient(to right, #f5222d, #faad14, #52c41a)',
                    borderRadius: 2
                  }}
                />
                <Tooltip title={`Low: $${valuation.price_target.target_range.low.toFixed(2)}`}>
                  <div
                    style={{
                      position: 'absolute',
                      left: '0%',
                      width: 8,
                      height: 8,
                      background: '#f5222d',
                      borderRadius: '50%'
                    }}
                  />
                </Tooltip>
                <Tooltip title={`Current: $${currentPrice.toFixed(2)}`}>
                  <div
                    style={{
                      position: 'absolute',
                      left: `${((currentPrice - valuation.price_target.target_range.low) /
                        (valuation.price_target.target_range.high - valuation.price_target.target_range.low)) * 100}%`,
                      width: 12,
                      height: 12,
                      background: '#1890ff',
                      borderRadius: '50%',
                      border: '2px solid white',
                      boxShadow: '0 2px 4px rgba(0,0,0,0.2)'
                    }}
                  />
                </Tooltip>
                <Tooltip title={`Target: $${priceTarget.toFixed(2)}`}>
                  <div
                    style={{
                      position: 'absolute',
                      left: `${((priceTarget - valuation.price_target.target_range.low) /
                        (valuation.price_target.target_range.high - valuation.price_target.target_range.low)) * 100}%`,
                      width: 16,
                      height: 16,
                      background: '#52c41a',
                      borderRadius: '50%',
                      border: '2px solid white',
                      boxShadow: '0 2px 4px rgba(0,0,0,0.2)'
                    }}
                  />
                </Tooltip>
                <Tooltip title={`High: $${valuation.price_target.target_range.high.toFixed(2)}`}>
                  <div
                    style={{
                      position: 'absolute',
                      right: '0%',
                      width: 8,
                      height: 8,
                      background: '#52c41a',
                      borderRadius: '50%'
                    }}
                  />
                </Tooltip>
              </div>
              <Row justify="space-between" style={{ marginTop: 8, width: '100%' }}>
                <Text type="secondary">${valuation.price_target.target_range.low.toFixed(2)}</Text>
                <Text type="secondary">${valuation.price_target.target_range.high.toFixed(2)}</Text>
              </Row>
            </Col>
          </Row>
        </Card>
      )}

      {/* Methodology Weights */}
      {valuation?.price_target?.methodology_weights && (
        <Alert
          message="Valuation Methodology"
          description={
            <Space direction="vertical">
              <Text>Price target calculated using weighted average of:</Text>
              <ul style={{ margin: '8px 0' }}>
                {Object.entries(valuation.price_target.methodology_weights).map(([method, weight]) => (
                  <li key={method}>
                    <Text>{`${method}: ${weight}`}</Text>
                  </li>
                ))}
              </ul>
            </Space>
          }
          type="info"
          showIcon
          icon={<CalculatorOutlined />}
          style={{ marginTop: 16 }}
        />
      )}
    </div>
  );
};

export default ValuationDisplay;