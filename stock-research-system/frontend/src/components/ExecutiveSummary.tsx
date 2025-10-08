import React from 'react';
import {
  Card,
  Row,
  Col,
  Typography,
  Tag,
  Statistic,
  Progress,
  Space,
  Divider,
  Alert,
  Badge,
  Tooltip,
  Button
} from 'antd';
import {
  ArrowUpOutlined,
  ArrowDownOutlined,
  SafetyCertificateOutlined,
  ThunderboltOutlined,
  ExclamationCircleOutlined,
  CheckCircleOutlined,
  WarningOutlined,
  DownloadOutlined,
  PrinterOutlined,
  ShareAltOutlined
} from '@ant-design/icons';
import { motion } from 'framer-motion';

const { Title, Text } = Typography;

interface ValuationData {
  price_target?: {
    price_target: number;
    upside: number;
    confidence: number;
    target_range?: {
      low: number;
      high: number;
    };
  };
  dcf_valuation?: {
    dcf_price: number;
    wacc: number;
  };
  comparative_valuation?: {
    comparative_price: number;
    pe_ratio: number | string;
    valuation_rating: string;
  };
  analyst_targets?: {
    analyst_consensus: string;
    target_mean: number;
    upside_potential: number;
    number_of_analysts: number;
  };
}

interface ExecutiveSummaryProps {
  analysisData: any;
  valuation?: ValuationData;
  onExport?: () => void;
  onPrint?: () => void;
  onShare?: () => void;
}

const ExecutiveSummary: React.FC<ExecutiveSummaryProps> = ({
  analysisData,
  valuation,
  onExport,
  onPrint,
  onShare
}) => {
  if (!analysisData) {
    return (
      <Card>
        <Alert
          message="No Analysis Data"
          description="Please run an analysis to see the executive summary"
          type="info"
          showIcon
        />
      </Card>
    );
  }

  const { symbol, analysis, confidence_scores } = analysisData;
  const marketData = analysis?.market_data?.[symbol] || {};
  const currentPrice = Number(marketData.price) || 0;
  const priceChange = Number(marketData.changePercent) || Number(marketData.change_percent) || 0;

  // Get valuation metrics
  const priceTarget = Number(valuation?.price_target?.price_target) || (currentPrice ? currentPrice * 1.1 : 0);
  const upside = Number(valuation?.price_target?.upside) ||
    (priceTarget && currentPrice ? ((priceTarget - currentPrice) / currentPrice * 100) : 10);
  const confidence = Number(valuation?.price_target?.confidence) || 0.7;
  const dcfPrice = Number(valuation?.dcf_valuation?.dcf_price) || currentPrice || 0;
  const analystConsensus = valuation?.analyst_targets?.analyst_consensus || 'Hold';
  const valuationRating = valuation?.comparative_valuation?.valuation_rating || 'Fairly Valued';

  // Determine recommendation color and icon
  const getRecommendationStyle = (recommendation: string) => {
    switch (recommendation.toUpperCase()) {
      case 'STRONG BUY':
      case 'BUY':
        return { color: '#52c41a', icon: <ArrowUpOutlined /> };
      case 'HOLD':
        return { color: '#faad14', icon: <SafetyCertificateOutlined /> };
      case 'SELL':
      case 'STRONG SELL':
        return { color: '#f5222d', icon: <ArrowDownOutlined /> };
      default:
        return { color: '#1890ff', icon: <ExclamationCircleOutlined /> };
    }
  };

  const recommendationStyle = getRecommendationStyle(analystConsensus);

  // Investment thesis based on data
  const generateInvestmentThesis = () => {
    const thesisPoints = [];

    if (upside > 20) {
      thesisPoints.push({
        type: 'opportunity',
        text: `Strong upside potential of ${upside.toFixed(1)}% to target price`,
        priority: 'high'
      });
    }

    if (valuationRating.includes('Undervalued')) {
      thesisPoints.push({
        type: 'opportunity',
        text: `Stock appears undervalued based on comparative metrics`,
        priority: 'high'
      });
    }

    if (marketData.pe_ratio && marketData.pe_ratio < 20) {
      thesisPoints.push({
        type: 'opportunity',
        text: `Attractive P/E ratio of ${marketData.pe_ratio.toFixed(1)}`,
        priority: 'medium'
      });
    }

    if (priceChange < -10) {
      thesisPoints.push({
        type: 'risk',
        text: `Recent significant decline of ${Math.abs(priceChange).toFixed(1)}%`,
        priority: 'high'
      });
    }

    if (confidence < 0.6) {
      thesisPoints.push({
        type: 'risk',
        text: `Lower confidence in price target due to high volatility`,
        priority: 'medium'
      });
    }

    return thesisPoints;
  };

  const investmentThesis = generateInvestmentThesis();

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.5 }}
    >
      <Card
        className="executive-summary glass-card"
        title={
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
            <Space>
              <Title level={3} style={{ margin: 0 }}>
                Executive Summary: {symbol}
              </Title>
              <Tag color={recommendationStyle.color} icon={recommendationStyle.icon}>
                {analystConsensus.toUpperCase()}
              </Tag>
            </Space>
            <Space>
              <Button icon={<DownloadOutlined />} onClick={onExport}>
                Export
              </Button>
              <Button icon={<PrinterOutlined />} onClick={onPrint}>
                Print
              </Button>
              <Button icon={<ShareAltOutlined />} onClick={onShare}>
                Share
              </Button>
            </Space>
          </div>
        }
      >
        {/* Key Metrics Row */}
        <Row gutter={[16, 16]}>
          <Col xs={24} sm={12} md={6}>
            <Card size="small" className="metric-card">
              <Statistic
                title="Current Price"
                value={currentPrice}
                prefix="$"
                precision={2}
                valueStyle={{ color: priceChange >= 0 ? '#52c41a' : '#f5222d' }}
                suffix={
                  <small style={{ fontSize: '14px', marginLeft: '8px' }}>
                    {priceChange >= 0 ? '+' : ''}{priceChange.toFixed(2)}%
                  </small>
                }
              />
            </Card>
          </Col>
          <Col xs={24} sm={12} md={6}>
            <Card size="small" className="metric-card">
              <Statistic
                title="Price Target"
                value={priceTarget}
                prefix="$"
                precision={2}
                valueStyle={{ color: '#1890ff' }}
                suffix={
                  valuation?.price_target?.target_range ? (
                    <Tooltip title={`Range: $${valuation.price_target.target_range.low.toFixed(2)} - $${valuation.price_target.target_range.high.toFixed(2)}`}>
                      <ExclamationCircleOutlined style={{ marginLeft: 8 }} />
                    </Tooltip>
                  ) : null
                }
              />
            </Card>
          </Col>
          <Col xs={24} sm={12} md={6}>
            <Card size="small" className="metric-card">
              <Statistic
                title="Upside Potential"
                value={upside}
                suffix="%"
                precision={1}
                prefix={upside >= 0 ? <ArrowUpOutlined /> : <ArrowDownOutlined />}
                valueStyle={{ color: upside >= 0 ? '#52c41a' : '#f5222d' }}
              />
            </Card>
          </Col>
          <Col xs={24} sm={12} md={6}>
            <Card size="small" className="metric-card">
              <Statistic
                title="Confidence Score"
                value={confidence * 100}
                suffix="%"
                precision={0}
                valueStyle={{ color: confidence > 0.7 ? '#52c41a' : '#faad14' }}
              />
              <Progress
                percent={confidence * 100}
                strokeColor={confidence > 0.7 ? '#52c41a' : '#faad14'}
                showInfo={false}
                size="small"
              />
            </Card>
          </Col>
        </Row>

        <Divider />

        {/* Investment Thesis */}
        <Row gutter={[16, 16]}>
          <Col span={24}>
            <Card
              title={<Space><ThunderboltOutlined /> Investment Thesis</Space>}
              size="small"
              className="thesis-card"
            >
              <Space direction="vertical" style={{ width: '100%' }}>
                {investmentThesis.map((point, index) => (
                  <Alert
                    key={index}
                    message={point.text}
                    type={point.type === 'opportunity' ? 'success' : 'warning'}
                    showIcon
                    icon={point.type === 'opportunity' ? <CheckCircleOutlined /> : <WarningOutlined />}
                  />
                ))}
              </Space>
            </Card>
          </Col>
        </Row>

        <Divider />

        {/* Valuation Methods Comparison */}
        <Row gutter={[16, 16]}>
          <Col span={24}>
            <Card title="Valuation Analysis" size="small">
              <Row gutter={[16, 16]}>
                <Col xs={24} sm={8}>
                  <div className="valuation-method">
                    <Text type="secondary">DCF Fair Value</Text>
                    <Title level={4}>${dcfPrice.toFixed(2)}</Title>
                    <Progress
                      percent={Math.min((dcfPrice / currentPrice) * 100, 150)}
                      strokeColor="#1890ff"
                      format={() => `${((dcfPrice / currentPrice - 1) * 100).toFixed(1)}%`}
                    />
                  </div>
                </Col>
                <Col xs={24} sm={8}>
                  <div className="valuation-method">
                    <Text type="secondary">Comparative Value</Text>
                    <Title level={4}>
                      {valuation?.comparative_valuation?.comparative_price
                        ? `$${Number(valuation.comparative_valuation.comparative_price).toFixed(2)}`
                        : '$N/A'}
                    </Title>
                    <Badge
                      count={valuationRating}
                      style={{
                        backgroundColor: valuationRating.includes('Under') ? '#52c41a' :
                                       valuationRating.includes('Over') ? '#f5222d' : '#faad14'
                      }}
                    />
                  </div>
                </Col>
                <Col xs={24} sm={8}>
                  <div className="valuation-method">
                    <Text type="secondary">Analyst Target</Text>
                    <Title level={4}>
                      {valuation?.analyst_targets?.target_mean
                        ? `$${Number(valuation.analyst_targets.target_mean).toFixed(2)}`
                        : '$N/A'}
                    </Title>
                    <Text type="secondary">
                      ({valuation?.analyst_targets?.number_of_analysts || 0} analysts)
                    </Text>
                  </div>
                </Col>
              </Row>
            </Card>
          </Col>
        </Row>

        <Divider />

        {/* Key Insights & Risks */}
        <Row gutter={[16, 16]}>
          <Col xs={24} md={12}>
            <Card
              title={<Space><CheckCircleOutlined style={{ color: '#52c41a' }} /> Key Opportunities</Space>}
              size="small"
              className="insight-card"
            >
              {analysis?.key_insights ? (
                <ul style={{ paddingLeft: 20 }}>
                  {analysis.key_insights.slice(0, 3).map((insight: string, index: number) => (
                    <li key={index}>
                      <Text>{insight}</Text>
                    </li>
                  ))}
                </ul>
              ) : (
                <Text type="secondary">No specific opportunities identified</Text>
              )}
            </Card>
          </Col>
          <Col xs={24} md={12}>
            <Card
              title={<Space><WarningOutlined style={{ color: '#f5222d' }} /> Key Risks</Space>}
              size="small"
              className="risk-card"
            >
              {analysis?.risks ? (
                <ul style={{ paddingLeft: 20 }}>
                  {analysis.risks.slice(0, 3).map((risk: string, index: number) => (
                    <li key={index}>
                      <Text>{risk}</Text>
                    </li>
                  ))}
                </ul>
              ) : (
                <Text type="secondary">No specific risks identified</Text>
              )}
            </Card>
          </Col>
        </Row>

        <Divider />

        {/* Action Items */}
        <Card
          title="Recommended Actions"
          size="small"
          className="action-card"
        >
          <Space direction="vertical" style={{ width: '100%' }}>
            {upside > 15 ? (
              <Alert
                message="Consider initiating or increasing position"
                description={`With ${upside.toFixed(1)}% upside potential and ${analystConsensus} consensus, this presents a favorable risk-reward opportunity.`}
                type="success"
                showIcon
                action={
                  <Button size="small" type="primary">
                    View Entry Points
                  </Button>
                }
              />
            ) : upside < -10 ? (
              <Alert
                message="Review position and consider risk management"
                description={`Current valuation suggests limited upside. Consider taking profits or implementing stop-loss orders.`}
                type="warning"
                showIcon
                action={
                  <Button size="small" danger>
                    Risk Analysis
                  </Button>
                }
              />
            ) : (
              <Alert
                message="Monitor for better entry points"
                description={`Current valuation is fair. Watch for price dips or improved fundamentals before taking action.`}
                type="info"
                showIcon
              />
            )}
          </Space>
        </Card>

        {/* Confidence Scores */}
        <Divider />
        <Row>
          <Col span={24}>
            <Text type="secondary">Analysis Confidence Scores:</Text>
            <Space style={{ marginTop: 8, display: 'flex', flexWrap: 'wrap' }}>
              {Object.entries(confidence_scores || {}).map(([key, value]: [string, any]) => (
                <Tag
                  key={key}
                  color={value > 0.8 ? 'green' : value > 0.6 ? 'orange' : 'red'}
                >
                  {key}: {(value * 100).toFixed(0)}%
                </Tag>
              ))}
            </Space>
          </Col>
        </Row>
      </Card>

    </motion.div>
  );
};

export default ExecutiveSummary;