import React from 'react';
import {
  Card,
  Row,
  Col,
  Progress,
  Typography,
  Space,
  Tag,
  Alert,
  Badge,
  Statistic,
  List,
  Divider,
  Tooltip
} from 'antd';
import {
  LineChartOutlined,
  RiseOutlined,
  FallOutlined,
  ThunderboltOutlined,
  AreaChartOutlined,
  StockOutlined,
  FlagOutlined,
  DashboardOutlined
} from '@ant-design/icons';

const { Title, Text } = Typography;

interface TechnicalAnalysisDisplayProps {
  technical: any;
  currentPrice: number;
}

const TechnicalAnalysisDisplay: React.FC<TechnicalAnalysisDisplayProps> = ({ technical, currentPrice }) => {
  if (!technical) {
    return (
      <Card>
        <Alert message="No technical analysis data available" type="info" showIcon />
      </Card>
    );
  }

  const indicators = technical?.indicators || {};
  const patterns = technical?.patterns || {};
  const signals = technical?.signals || {};
  const supportResistance = technical?.support_resistance || {};

  const getRSIColor = (rsi: number) => {
    if (rsi > 70) return '#f5222d'; // Overbought
    if (rsi < 30) return '#52c41a'; // Oversold
    return '#1890ff'; // Neutral
  };

  const getRSILabel = (rsi: number) => {
    if (rsi > 70) return 'Overbought';
    if (rsi < 30) return 'Oversold';
    return 'Neutral';
  };

  const getSignalColor = (signal: string) => {
    if (signal === 'STRONG_BUY' || signal === 'BUY') return '#52c41a';
    if (signal === 'STRONG_SELL' || signal === 'SELL') return '#f5222d';
    return '#faad14';
  };

  const getSignalIcon = (signal: string) => {
    if (signal === 'STRONG_BUY' || signal === 'BUY') return <RiseOutlined />;
    if (signal === 'STRONG_SELL' || signal === 'SELL') return <FallOutlined />;
    return <DashboardOutlined />;
  };

  return (
    <div className="technical-analysis-display">
      {/* Overall Signal */}
      <Card
        style={{ marginBottom: 16 }}
        bodyStyle={{ background: `linear-gradient(135deg, ${getSignalColor(signals?.overall || 'NEUTRAL')}20, transparent)` }}
      >
        <Row align="middle" justify="space-between">
          <Col>
            <Space>
              <ThunderboltOutlined style={{ fontSize: 24, color: getSignalColor(signals?.overall || 'NEUTRAL') }} />
              <div>
                <Text type="secondary">Technical Signal</Text>
                <Title level={3} style={{ margin: 0, color: getSignalColor(signals?.overall || 'NEUTRAL') }}>
                  {signals?.overall || 'NEUTRAL'}
                </Title>
              </div>
            </Space>
          </Col>
          <Col>
            <Space>
              <Badge
                count={`${signals?.buy_signals || 0} Buy`}
                style={{ backgroundColor: '#52c41a' }}
              />
              <Badge
                count={`${signals?.sell_signals || 0} Sell`}
                style={{ backgroundColor: '#f5222d' }}
              />
            </Space>
          </Col>
        </Row>
      </Card>

      {/* Indicators Grid */}
      <Row gutter={[16, 16]}>
        {/* Momentum Indicators */}
        <Col xs={24} md={12}>
          <Card
            title={
              <Space>
                <LineChartOutlined />
                <Text strong>Momentum Indicators</Text>
              </Space>
            }
            size="small"
          >
            <Space direction="vertical" style={{ width: '100%' }}>
              {/* RSI */}
              <div>
                <Row justify="space-between" align="middle">
                  <Text>RSI (14)</Text>
                  <Tag color={getRSIColor(indicators?.momentum?.rsi || 50)}>
                    {getRSILabel(indicators?.momentum?.rsi || 50)}
                  </Tag>
                </Row>
                <Progress
                  percent={indicators?.momentum?.rsi || 50}
                  strokeColor={getRSIColor(indicators?.momentum?.rsi || 50)}
                  showInfo={true}
                  format={percent => `${percent?.toFixed(0)}`}
                />
              </div>

              {/* MACD */}
              {indicators?.trend?.macd && (
                <div>
                  <Row justify="space-between">
                    <Text>MACD</Text>
                    <Space>
                      <Text type={indicators.trend.macd.histogram > 0 ? 'success' : 'danger'}>
                        {indicators.trend.macd.histogram?.toFixed(2) || '0'}
                      </Text>
                      {indicators.trend.macd.crossover && (
                        <Tag color="green">Crossover</Tag>
                      )}
                    </Space>
                  </Row>
                </div>
              )}

              {/* Stochastic */}
              {indicators?.momentum?.stochastic && (
                <div>
                  <Row justify="space-between">
                    <Text>Stochastic</Text>
                    <Space>
                      <Text>K: {indicators.momentum.stochastic.k?.toFixed(0)}</Text>
                      <Text>D: {indicators.momentum.stochastic.d?.toFixed(0)}</Text>
                    </Space>
                  </Row>
                </div>
              )}
            </Space>
          </Card>
        </Col>

        {/* Volatility Indicators */}
        <Col xs={24} md={12}>
          <Card
            title={
              <Space>
                <AreaChartOutlined />
                <Text strong>Volatility Analysis</Text>
              </Space>
            }
            size="small"
          >
            <Space direction="vertical" style={{ width: '100%' }}>
              {/* Bollinger Bands */}
              {indicators?.volatility?.bollinger && (
                <div>
                  <Text strong>Bollinger Bands</Text>
                  <Row justify="space-between" style={{ marginTop: 8 }}>
                    <Text type="secondary">Upper:</Text>
                    <Text>${indicators.volatility.bollinger.upper?.toFixed(2)}</Text>
                  </Row>
                  <Row justify="space-between">
                    <Text type="secondary">Middle:</Text>
                    <Text>${indicators.volatility.bollinger.middle?.toFixed(2)}</Text>
                  </Row>
                  <Row justify="space-between">
                    <Text type="secondary">Lower:</Text>
                    <Text>${indicators.volatility.bollinger.lower?.toFixed(2)}</Text>
                  </Row>
                  <Tag color={
                    indicators.volatility.bollinger.position === 'ABOVE_UPPER' ? 'red' :
                    indicators.volatility.bollinger.position === 'BELOW_LOWER' ? 'green' : 'blue'
                  } style={{ marginTop: 8 }}>
                    {indicators.volatility.bollinger.position || 'MIDDLE'}
                  </Tag>
                </div>
              )}

              {/* ATR */}
              {indicators?.volatility?.atr && (
                <div style={{ marginTop: 16 }}>
                  <Row justify="space-between">
                    <Text>ATR (14)</Text>
                    <Text strong>${indicators.volatility.atr?.toFixed(2)}</Text>
                  </Row>
                  <Progress
                    percent={(indicators.volatility.atr / currentPrice) * 100}
                    size="small"
                    showInfo={false}
                  />
                </div>
              )}
            </Space>
          </Card>
        </Col>

        {/* Volume Indicators */}
        <Col xs={24} md={12}>
          <Card
            title={
              <Space>
                <StockOutlined />
                <Text strong>Volume Analysis</Text>
              </Space>
            }
            size="small"
          >
            <Space direction="vertical" style={{ width: '100%' }}>
              {/* VWAP */}
              {indicators?.volume?.vwap && (
                <div>
                  <Row justify="space-between">
                    <Text>VWAP</Text>
                    <Text strong>${indicators.volume.vwap?.toFixed(2)}</Text>
                  </Row>
                  <Text type={currentPrice > indicators.volume.vwap ? 'success' : 'danger'}>
                    Price {currentPrice > indicators.volume.vwap ? 'above' : 'below'} VWAP
                  </Text>
                </div>
              )}

              {/* OBV Trend */}
              {indicators?.volume?.obv_trend && (
                <div style={{ marginTop: 16 }}>
                  <Row justify="space-between">
                    <Text>OBV Trend</Text>
                    <Tag color={indicators.volume.obv_trend === 'BULLISH' ? 'green' : 'red'}>
                      {indicators.volume.obv_trend}
                    </Tag>
                  </Row>
                </div>
              )}
            </Space>
          </Card>
        </Col>

        {/* Support & Resistance */}
        <Col xs={24} md={12}>
          <Card
            title={
              <Space>
                <FlagOutlined />
                <Text strong>Key Levels</Text>
              </Space>
            }
            size="small"
          >
            <Space direction="vertical" style={{ width: '100%' }}>
              {/* Resistance Levels */}
              <div>
                <Text type="secondary">Resistance</Text>
                <List
                  size="small"
                  dataSource={supportResistance?.resistance || []}
                  renderItem={(level: number, index: number) => (
                    <List.Item>
                      <Space>
                        <Badge
                          count={`R${index + 1}`}
                          style={{ backgroundColor: '#f5222d' }}
                        />
                        <Text>${level.toFixed(2)}</Text>
                        <Text type="secondary">
                          ({((level - currentPrice) / currentPrice * 100).toFixed(1)}%)
                        </Text>
                      </Space>
                    </List.Item>
                  )}
                />
              </div>

              <Divider style={{ margin: '8px 0' }} />

              {/* Support Levels */}
              <div>
                <Text type="secondary">Support</Text>
                <List
                  size="small"
                  dataSource={supportResistance?.support || []}
                  renderItem={(level: number, index: number) => (
                    <List.Item>
                      <Space>
                        <Badge
                          count={`S${index + 1}`}
                          style={{ backgroundColor: '#52c41a' }}
                        />
                        <Text>${level.toFixed(2)}</Text>
                        <Text type="secondary">
                          ({((currentPrice - level) / currentPrice * 100).toFixed(1)}%)
                        </Text>
                      </Space>
                    </List.Item>
                  )}
                />
              </div>
            </Space>
          </Card>
        </Col>
      </Row>

      {/* Pattern Detection */}
      {patterns?.detected && patterns.detected.length > 0 && (
        <Card
          title={
            <Space>
              <AreaChartOutlined />
              <Text strong>Chart Patterns Detected</Text>
            </Space>
          }
          style={{ marginTop: 16 }}
        >
          <List
            grid={{ gutter: 16, xs: 1, sm: 2, md: 3, lg: 3 }}
            dataSource={patterns.detected}
            renderItem={(pattern: any) => (
              <List.Item>
                <Card size="small">
                  <Space direction="vertical">
                    <Text strong>{pattern.name}</Text>
                    <Text type="secondary">{pattern.type}</Text>
                    {pattern.confidence && (
                      <Progress
                        percent={pattern.confidence * 100}
                        size="small"
                        strokeColor="#1890ff"
                      />
                    )}
                  </Space>
                </Card>
              </List.Item>
            )}
          />
        </Card>
      )}

      {/* Trading Recommendation */}
      <Alert
        message="Technical Trading Recommendation"
        description={
          <Space direction="vertical">
            <Row align="middle" gutter={16}>
              <Col>
                <Space>
                  {getSignalIcon(signals?.overall || 'NEUTRAL')}
                  <Text strong style={{ fontSize: 16 }}>
                    {signals?.overall || 'NEUTRAL'}
                  </Text>
                </Space>
              </Col>
              <Col>
                <Text>Signal Strength: {signals?.strength || 0}%</Text>
              </Col>
            </Row>
            {signals?.trend && (
              <Text>Primary Trend: {signals.trend}</Text>
            )}
            {supportResistance?.resistance?.[0] && (
              <Text>Next Resistance: ${supportResistance.resistance[0].toFixed(2)}</Text>
            )}
            {supportResistance?.support?.[0] && (
              <Text>Next Support: ${supportResistance.support[0].toFixed(2)}</Text>
            )}
          </Space>
        }
        type={signals?.overall?.includes('BUY') ? 'success' : signals?.overall?.includes('SELL') ? 'error' : 'warning'}
        showIcon
        style={{ marginTop: 16 }}
      />
    </div>
  );
};

export default TechnicalAnalysisDisplay;