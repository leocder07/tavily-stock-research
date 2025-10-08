import React from 'react';
import {
  Card,
  Row,
  Col,
  Progress,
  Tag,
  Tooltip,
  Space,
  Badge,
  Typography,
  Alert,
  Statistic,
  Timeline,
  Divider
} from 'antd';
import {
  CheckCircleOutlined,
  ClockCircleOutlined,
  ExclamationCircleOutlined,
  SafetyCertificateOutlined,
  ApiOutlined,
  DatabaseOutlined,
  CloudOutlined,
  RobotOutlined,
  LineChartOutlined,
  TeamOutlined,
  FileSearchOutlined,
  GlobalOutlined
} from '@ant-design/icons';

const { Text, Title, Paragraph } = Typography;

interface DataSource {
  name: string;
  reliability: number;
  lastUpdated?: string;
  status: 'live' | 'cached' | 'estimated';
  dataPoints?: string[];
}

interface ConfidenceScore {
  overall: number;
  price_data: number;
  analyst_consensus: number;
  technical_analysis: number;
}

interface DataConfidenceDisplayProps {
  confidenceScores?: ConfidenceScore;
  aggregatedData?: any;
  marketMood?: any;
  sectorRotation?: any;
}

const DataConfidenceDisplay: React.FC<DataConfidenceDisplayProps> = ({
  confidenceScores,
  aggregatedData,
  marketMood,
  sectorRotation
}) => {
  const getSourceIcon = (source: string) => {
    const icons: { [key: string]: React.ReactNode } = {
      'yahoo_finance': <DatabaseOutlined style={{ color: '#722ed1' }} />,
      'marketbeat': <TeamOutlined style={{ color: '#1890ff' }} />,
      'tradingview': <LineChartOutlined style={{ color: '#52c41a' }} />,
      'tavily_search': <GlobalOutlined style={{ color: '#fa8c16' }} />,
      'calculated': <RobotOutlined style={{ color: '#13c2c2' }} />,
      'api': <ApiOutlined style={{ color: '#2f54eb' }} />,
      'cache': <CloudOutlined style={{ color: '#eb2f96' }} />
    };
    return icons[source.toLowerCase()] || <FileSearchOutlined />;
  };

  const getConfidenceColor = (score: number) => {
    if (score >= 80) return '#52c41a';
    if (score >= 60) return '#1890ff';
    if (score >= 40) return '#faad14';
    return '#f5222d';
  };

  const getConfidenceLabel = (score: number) => {
    if (score >= 80) return 'High Confidence';
    if (score >= 60) return 'Moderate Confidence';
    if (score >= 40) return 'Low Confidence';
    return 'Very Low Confidence';
  };

  const getMoodEmoji = (level: string) => {
    const emojis: { [key: string]: string } = {
      'extreme_fear': '😱',
      'fear': '😨',
      'neutral': '😐',
      'greed': '😊',
      'extreme_greed': '🤑'
    };
    return emojis[level] || '😐';
  };

  // Extract data sources from aggregated data
  const dataSources: DataSource[] = aggregatedData?.sources_used?.map((source: string) => {
    const sourceData = aggregatedData?.data?.[source] || {};
    return {
      name: source.replace(/_/g, ' ').replace(/\b\w/g, (l: string) => l.toUpperCase()),
      reliability: source === 'yahoo_finance' ? 90 :
                   source === 'marketbeat' ? 85 :
                   source === 'tradingview' ? 80 :
                   source === 'tavily_search' ? 75 : 70,
      status: sourceData.error ? 'estimated' : 'live',
      lastUpdated: new Date().toISOString(),
      dataPoints: Object.keys(sourceData).filter(key => key !== 'error' && key !== 'source')
    };
  }) || [];

  return (
    <div className="data-confidence-display">
      {/* Overall Confidence Score */}
      {confidenceScores && (
        <Card
          title={
            <Space>
              <SafetyCertificateOutlined />
              <Title level={4} style={{ margin: 0 }}>Data Confidence & Sources</Title>
            </Space>
          }
          style={{ marginBottom: 16 }}
        >
          <Row gutter={[16, 16]}>
            <Col xs={24} md={12}>
              <Card size="small">
                <Statistic
                  title="Overall Confidence"
                  value={confidenceScores.overall || 0}
                  suffix="%"
                  valueStyle={{ color: getConfidenceColor(confidenceScores.overall || 0) }}
                />
                <Progress
                  percent={confidenceScores.overall || 0}
                  strokeColor={getConfidenceColor(confidenceScores.overall || 0)}
                  showInfo={false}
                  style={{ marginTop: 8 }}
                />
                <Tag color={getConfidenceColor(confidenceScores.overall || 0)} style={{ marginTop: 8 }}>
                  {getConfidenceLabel(confidenceScores.overall || 0)}
                </Tag>
              </Card>
            </Col>
            <Col xs={24} md={12}>
              <Space direction="vertical" style={{ width: '100%' }}>
                <Row justify="space-between">
                  <Text>Price Data</Text>
                  <Progress
                    percent={confidenceScores.price_data || 0}
                    size="small"
                    style={{ width: 150 }}
                    strokeColor={getConfidenceColor(confidenceScores.price_data || 0)}
                  />
                </Row>
                <Row justify="space-between">
                  <Text>Analyst Consensus</Text>
                  <Progress
                    percent={confidenceScores.analyst_consensus || 0}
                    size="small"
                    style={{ width: 150 }}
                    strokeColor={getConfidenceColor(confidenceScores.analyst_consensus || 0)}
                  />
                </Row>
                <Row justify="space-between">
                  <Text>Technical Analysis</Text>
                  <Progress
                    percent={confidenceScores.technical_analysis || 0}
                    size="small"
                    style={{ width: 150 }}
                    strokeColor={getConfidenceColor(confidenceScores.technical_analysis || 0)}
                  />
                </Row>
              </Space>
            </Col>
          </Row>
        </Card>
      )}

      {/* Data Sources */}
      {dataSources.length > 0 && (
        <Card
          title="Data Sources"
          size="small"
          style={{ marginBottom: 16 }}
        >
          <Row gutter={[8, 8]}>
            {dataSources.map((source, index) => (
              <Col key={index} xs={12} sm={8} md={6}>
                <Card
                  size="small"
                  style={{ textAlign: 'center' }}
                  hoverable
                >
                  <Space direction="vertical" size="small">
                    {getSourceIcon(source.name)}
                    <Text strong style={{ fontSize: 12 }}>
                      {source.name}
                    </Text>
                    <Badge
                      status={source.status === 'live' ? 'success' : source.status === 'cached' ? 'warning' : 'default'}
                      text={
                        <Text style={{ fontSize: 10 }}>
                          {source.status.toUpperCase()}
                        </Text>
                      }
                    />
                    <Progress
                      percent={source.reliability}
                      size="small"
                      showInfo={false}
                      strokeColor={getConfidenceColor(source.reliability)}
                    />
                  </Space>
                </Card>
              </Col>
            ))}
          </Row>
        </Card>
      )}

      {/* Market Mood Indicator */}
      {marketMood && (
        <Card
          title="Market Mood Index"
          size="small"
          style={{ marginBottom: 16 }}
        >
          <Row gutter={[16, 16]}>
            <Col xs={24} md={8}>
              <Card size="small" style={{ textAlign: 'center', background: '#f0f2f5' }}>
                <Space direction="vertical">
                  <Text style={{ fontSize: 48 }}>
                    {getMoodEmoji(marketMood.mood_level)}
                  </Text>
                  <Title level={4} style={{ margin: 0 }}>
                    {marketMood.mood_score || 50}
                  </Title>
                  <Text strong>{marketMood.mood_level?.replace(/_/g, ' ').toUpperCase()}</Text>
                </Space>
              </Card>
            </Col>
            <Col xs={24} md={16}>
              <Paragraph style={{ marginBottom: 16 }}>
                {marketMood.interpretation}
              </Paragraph>
              <Space direction="vertical" style={{ width: '100%' }}>
                {marketMood.components?.slice(0, 3).map((component: any, index: number) => (
                  <Row key={index} justify="space-between">
                    <Text>{component.name}</Text>
                    <Progress
                      percent={component.value}
                      size="small"
                      style={{ width: 100 }}
                      strokeColor={getConfidenceColor(component.value)}
                    />
                  </Row>
                ))}
              </Space>
            </Col>
          </Row>
        </Card>
      )}

      {/* Sector Rotation Signals */}
      {sectorRotation && (
        <Card
          title="Sector Rotation Analysis"
          size="small"
          style={{ marginBottom: 16 }}
        >
          <Row gutter={[16, 16]}>
            <Col xs={24} md={12}>
              <Card size="small" title="Leading Sectors" style={{ background: '#f6ffed' }}>
                {sectorRotation.leaders?.map((sector: any, index: number) => (
                  <Row key={index} justify="space-between" style={{ marginBottom: 8 }}>
                    <Text>{sector.name}</Text>
                    <Tag color="green">
                      {sector.performance_1w > 0 ? '+' : ''}{sector.performance_1w?.toFixed(1)}%
                    </Tag>
                  </Row>
                ))}
              </Card>
            </Col>
            <Col xs={24} md={12}>
              <Card size="small" title="Lagging Sectors" style={{ background: '#fff1f0' }}>
                {sectorRotation.laggards?.map((sector: any, index: number) => (
                  <Row key={index} justify="space-between" style={{ marginBottom: 8 }}>
                    <Text>{sector.name}</Text>
                    <Tag color="red">
                      {sector.performance_1w > 0 ? '+' : ''}{sector.performance_1w?.toFixed(1)}%
                    </Tag>
                  </Row>
                ))}
              </Card>
            </Col>
          </Row>
          <Alert
            message={sectorRotation.rotation_signal}
            type="info"
            showIcon
            style={{ marginTop: 16 }}
          />
        </Card>
      )}

      {/* Data Update Timeline */}
      <Card
        title="Data Freshness"
        size="small"
      >
        <Timeline mode="left">
          <Timeline.Item
            color="green"
            dot={<CheckCircleOutlined />}
          >
            <Text strong>Real-time Price Data</Text>
            <br />
            <Text type="secondary" style={{ fontSize: 12 }}>Updated every 15 seconds during market hours</Text>
          </Timeline.Item>
          <Timeline.Item
            color="blue"
            dot={<ClockCircleOutlined />}
          >
            <Text strong>Analyst Consensus</Text>
            <br />
            <Text type="secondary" style={{ fontSize: 12 }}>Updated daily from multiple sources</Text>
          </Timeline.Item>
          <Timeline.Item
            color="orange"
            dot={<ExclamationCircleOutlined />}
          >
            <Text strong>Technical Indicators</Text>
            <br />
            <Text type="secondary" style={{ fontSize: 12 }}>Calculated every 5 minutes</Text>
          </Timeline.Item>
        </Timeline>
      </Card>

      {/* Data Quality Alert */}
      {confidenceScores && confidenceScores.overall < 60 && (
        <Alert
          message="Data Quality Notice"
          description="Some data sources may be unavailable or outdated. Results should be verified with additional research."
          type="warning"
          showIcon
          style={{ marginTop: 16 }}
        />
      )}
    </div>
  );
};

export default DataConfidenceDisplay;