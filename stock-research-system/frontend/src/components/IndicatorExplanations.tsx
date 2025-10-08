import React, { useState } from 'react';
import {
  Card,
  Collapse,
  Typography,
  Space,
  Tag,
  Tooltip,
  Divider,
  Row,
  Col,
  Alert,
  Badge,
  Button,
  Modal,
  List
} from 'antd';
import {
  QuestionCircleOutlined,
  InfoCircleOutlined,
  BookOutlined,
  CalculatorOutlined,
  ExperimentOutlined,
  LineChartOutlined,
  FundOutlined
} from '@ant-design/icons';

const { Panel } = Collapse;
const { Title, Text, Paragraph } = Typography;

interface IndicatorExplanationsProps {
  category?: 'valuation' | 'technical' | 'competitive' | 'all';
}

const IndicatorExplanations: React.FC<IndicatorExplanationsProps> = ({ category = 'all' }) => {
  const [modalVisible, setModalVisible] = useState(false);
  const [selectedIndicator, setSelectedIndicator] = useState<any>(null);

  const valuationIndicators = {
    dcf: {
      name: 'DCF (Discounted Cash Flow)',
      formula: 'DCF = Σ(CFt / (1 + r)^t) + TV / (1 + r)^n',
      explanation: 'DCF calculates the present value of expected future cash flows using a discount rate (WACC).',
      interpretation: {
        positive: 'DCF > Current Price = Potentially Undervalued',
        negative: 'DCF < Current Price = Potentially Overvalued',
        neutral: 'DCF ≈ Current Price = Fairly Valued'
      },
      factors: [
        'Free Cash Flow projections',
        'WACC (Weighted Average Cost of Capital)',
        'Terminal Growth Rate',
        'Company Beta'
      ],
      citation: 'Damodaran, A. (2012). Investment Valuation. John Wiley & Sons.'
    },
    wacc: {
      name: 'WACC (Weighted Average Cost of Capital)',
      formula: 'WACC = (E/V × Re) + (D/V × Rd × (1 - Tc))',
      explanation: 'WACC represents the average rate a company expects to pay to finance its assets.',
      interpretation: {
        low: 'WACC < 10% = Lower risk, stable company',
        medium: 'WACC 10-15% = Average risk',
        high: 'WACC > 15% = Higher risk, growth company'
      },
      factors: [
        'Cost of Equity (Re)',
        'Cost of Debt (Rd)',
        'Tax Rate (Tc)',
        'Capital Structure (E/V, D/V)'
      ],
      citation: 'Ross, S., Westerfield, R., & Jaffe, J. (2019). Corporate Finance. McGraw-Hill.'
    },
    peRatio: {
      name: 'P/E Ratio (Price-to-Earnings)',
      formula: 'P/E = Stock Price / Earnings Per Share',
      explanation: 'P/E ratio shows how much investors are willing to pay per dollar of earnings.',
      interpretation: {
        low: 'P/E < 15 = Potentially undervalued or low growth',
        medium: 'P/E 15-25 = Fair value for stable companies',
        high: 'P/E > 25 = High growth expectations or overvalued'
      },
      factors: [
        'Industry average P/E',
        'Historical P/E range',
        'Growth rate',
        'Market sentiment'
      ],
      citation: 'Graham, B., & Dodd, D. (2008). Security Analysis. McGraw-Hill.'
    },
    peg: {
      name: 'PEG Ratio (Price/Earnings to Growth)',
      formula: 'PEG = P/E Ratio / Annual EPS Growth Rate',
      explanation: 'PEG ratio adjusts P/E for growth, providing a more complete valuation picture.',
      interpretation: {
        undervalued: 'PEG < 1 = Potentially undervalued',
        fair: 'PEG ≈ 1 = Fairly valued',
        overvalued: 'PEG > 1 = Potentially overvalued'
      },
      factors: [
        'Earnings growth rate',
        'P/E ratio',
        'Industry comparison',
        'Growth sustainability'
      ],
      citation: 'Lynch, P. (1989). One Up On Wall Street. Simon & Schuster.'
    }
  };

  const technicalIndicators = {
    rsi: {
      name: 'RSI (Relative Strength Index)',
      formula: 'RSI = 100 - (100 / (1 + RS)), where RS = Avg Gain / Avg Loss',
      explanation: 'RSI measures momentum by comparing magnitude of recent gains to losses.',
      interpretation: {
        oversold: 'RSI < 30 = Oversold (potential buy signal)',
        neutral: 'RSI 30-70 = Neutral zone',
        overbought: 'RSI > 70 = Overbought (potential sell signal)'
      },
      factors: [
        '14-period average gains',
        '14-period average losses',
        'Price momentum',
        'Divergence patterns'
      ],
      citation: 'Wilder, J.W. (1978). New Concepts in Technical Trading Systems.'
    },
    macd: {
      name: 'MACD (Moving Average Convergence Divergence)',
      formula: 'MACD = 12-day EMA - 26-day EMA; Signal = 9-day EMA of MACD',
      explanation: 'MACD identifies trend changes through the relationship between moving averages.',
      interpretation: {
        bullish: 'MACD crosses above Signal = Buy signal',
        bearish: 'MACD crosses below Signal = Sell signal',
        divergence: 'Price/MACD divergence = Potential reversal'
      },
      factors: [
        '12-day EMA',
        '26-day EMA',
        'Signal line (9-day EMA)',
        'Histogram strength'
      ],
      citation: 'Appel, G. (2005). Technical Analysis: Power Tools for Active Investors.'
    },
    bollingerBands: {
      name: 'Bollinger Bands',
      formula: 'Upper = SMA + (2 × σ); Lower = SMA - (2 × σ)',
      explanation: 'Bollinger Bands use standard deviation to create a volatility-based trading range.',
      interpretation: {
        squeeze: 'Narrow bands = Low volatility, potential breakout',
        expansion: 'Wide bands = High volatility',
        reversal: 'Price at bands = Potential reversal points'
      },
      factors: [
        '20-day Simple Moving Average',
        'Standard deviation (volatility)',
        'Band width',
        'Price position relative to bands'
      ],
      citation: 'Bollinger, J. (2001). Bollinger on Bollinger Bands. McGraw-Hill.'
    },
    vwap: {
      name: 'VWAP (Volume Weighted Average Price)',
      formula: 'VWAP = Σ(Price × Volume) / Σ(Volume)',
      explanation: 'VWAP gives the average price weighted by volume, showing true average cost.',
      interpretation: {
        above: 'Price > VWAP = Bullish intraday trend',
        below: 'Price < VWAP = Bearish intraday trend',
        support: 'VWAP often acts as support/resistance'
      },
      factors: [
        'Cumulative volume',
        'Typical price (H+L+C)/3',
        'Time period',
        'Volume distribution'
      ],
      citation: 'Konishi, A. (2002). VWAP Strategies. Institutional Investor.'
    },
    atr: {
      name: 'ATR (Average True Range)',
      formula: 'ATR = MA of True Range over n periods',
      explanation: 'ATR measures volatility by calculating the average range of price movement.',
      interpretation: {
        high: 'High ATR = High volatility, wider stops needed',
        low: 'Low ATR = Low volatility, tighter stops possible',
        trend: 'Rising ATR = Increasing volatility'
      },
      factors: [
        'True Range calculation',
        'Period length (typically 14)',
        'Historical volatility',
        'Market conditions'
      ],
      citation: 'Wilder, J.W. (1978). New Concepts in Technical Trading Systems.'
    }
  };

  const competitiveIndicators = {
    marketShare: {
      name: 'Market Share',
      formula: 'Market Share = (Company Revenue / Total Market Revenue) × 100%',
      explanation: 'Market share represents the percentage of total market sales captured by a company.',
      interpretation: {
        leader: 'Market Share > 30% = Market leader',
        challenger: 'Market Share 10-30% = Market challenger',
        follower: 'Market Share < 10% = Market follower'
      },
      factors: [
        'Total addressable market (TAM)',
        'Company revenue',
        'Geographic coverage',
        'Product portfolio'
      ],
      citation: 'Porter, M.E. (1980). Competitive Strategy. Free Press.'
    },
    moat: {
      name: 'Economic Moat',
      formula: 'Qualitative assessment based on competitive advantages',
      explanation: 'Economic moat represents sustainable competitive advantages protecting market position.',
      interpretation: {
        wide: 'Wide Moat = Strong, lasting competitive advantages',
        narrow: 'Narrow Moat = Some competitive advantages',
        none: 'No Moat = No sustainable advantages'
      },
      factors: [
        'Brand strength',
        'Network effects',
        'Switching costs',
        'Cost advantages',
        'Intangible assets'
      ],
      citation: 'Buffett, W. & Cunningham, L.A. (2013). The Essays of Warren Buffett.'
    },
    grossMargin: {
      name: 'Gross Margin',
      formula: 'Gross Margin = (Revenue - COGS) / Revenue × 100%',
      explanation: 'Gross margin shows profitability after direct costs, indicating pricing power.',
      interpretation: {
        excellent: 'Gross Margin > 50% = Excellent pricing power',
        good: 'Gross Margin 30-50% = Good profitability',
        poor: 'Gross Margin < 30% = Low pricing power'
      },
      factors: [
        'Pricing strategy',
        'Cost structure',
        'Product differentiation',
        'Supply chain efficiency'
      ],
      citation: 'Brealey, R., Myers, S., & Allen, F. (2020). Principles of Corporate Finance.'
    }
  };

  const allIndicators = {
    valuation: valuationIndicators,
    technical: technicalIndicators,
    competitive: competitiveIndicators
  };

  const showIndicatorDetail = (indicator: any) => {
    setSelectedIndicator(indicator);
    setModalVisible(true);
  };

  const renderIndicatorCard = (indicator: any, key: string) => (
    <Card
      key={key}
      size="small"
      hoverable
      onClick={() => showIndicatorDetail(indicator)}
      style={{ marginBottom: 12, cursor: 'pointer' }}
    >
      <Space direction="vertical" style={{ width: '100%' }}>
        <Space>
          <CalculatorOutlined style={{ fontSize: 18, color: '#1890ff' }} />
          <Text strong>{indicator.name}</Text>
          <Tooltip title="Click for detailed explanation">
            <InfoCircleOutlined style={{ color: '#8c8c8c' }} />
          </Tooltip>
        </Space>
        <Text type="secondary" style={{ fontSize: 12 }}>
          {indicator.explanation.substring(0, 100)}...
        </Text>
        <Space wrap>
          {Object.keys(indicator.interpretation).map(key => (
            <Tag key={key} color="blue" style={{ fontSize: 10 }}>
              {key.toUpperCase()}
            </Tag>
          ))}
        </Space>
      </Space>
    </Card>
  );

  const renderDetailModal = () => (
    <Modal
      title={
        <Space>
          <ExperimentOutlined />
          <Text strong>{selectedIndicator?.name}</Text>
        </Space>
      }
      visible={modalVisible}
      onCancel={() => setModalVisible(false)}
      width={800}
      footer={[
        <Button key="close" onClick={() => setModalVisible(false)}>
          Close
        </Button>
      ]}
    >
      {selectedIndicator && (
        <Space direction="vertical" style={{ width: '100%' }} size="large">
          {/* Formula */}
          <Card size="small" title="Formula">
            <Alert
              message={
                <Text code style={{ fontSize: 14 }}>
                  {selectedIndicator.formula}
                </Text>
              }
              type="info"
            />
          </Card>

          {/* Explanation */}
          <Card size="small" title="Detailed Explanation">
            <Paragraph>{selectedIndicator.explanation}</Paragraph>
          </Card>

          {/* Interpretation Guide */}
          <Card size="small" title="How to Interpret">
            <List
              dataSource={Object.entries(selectedIndicator.interpretation)}
              renderItem={([key, value]) => (
                <List.Item>
                  <Space>
                    <Badge color={
                      key.includes('buy') || key.includes('under') || key.includes('low') ? 'green' :
                      key.includes('sell') || key.includes('over') || key.includes('high') ? 'red' :
                      'blue'
                    } />
                    <Text strong>{key.charAt(0).toUpperCase() + key.slice(1)}:</Text>
                    <Text>{value as string}</Text>
                  </Space>
                </List.Item>
              )}
            />
          </Card>

          {/* Key Factors */}
          <Card size="small" title="Key Factors">
            <List
              dataSource={selectedIndicator.factors}
              renderItem={(factor: string) => (
                <List.Item>
                  <Space>
                    <LineChartOutlined style={{ color: '#1890ff' }} />
                    <Text>{factor}</Text>
                  </Space>
                </List.Item>
              )}
            />
          </Card>

          {/* Citation */}
          <Alert
            message="Academic Reference"
            description={
              <Space>
                <BookOutlined />
                <Text type="secondary" italic>
                  {selectedIndicator.citation}
                </Text>
              </Space>
            }
            type="info"
            showIcon={false}
          />
        </Space>
      )}
    </Modal>
  );

  const renderCategorySection = (categoryKey: string, indicators: any) => (
    <Collapse defaultActiveKey={['1']} style={{ marginBottom: 24 }}>
      <Panel
        header={
          <Space>
            <FundOutlined />
            <Text strong>
              {categoryKey.charAt(0).toUpperCase() + categoryKey.slice(1)} Indicators
            </Text>
            <Badge count={Object.keys(indicators).length} style={{ backgroundColor: '#52c41a' }} />
          </Space>
        }
        key="1"
      >
        <Row gutter={[16, 16]}>
          {Object.entries(indicators).map(([key, indicator]) => (
            <Col xs={24} sm={12} md={8} key={key}>
              {renderIndicatorCard(indicator, key)}
            </Col>
          ))}
        </Row>
      </Panel>
    </Collapse>
  );

  return (
    <div className="indicator-explanations">
      <Card
        title={
          <Space>
            <BookOutlined style={{ fontSize: 24 }} />
            <Title level={3} style={{ margin: 0 }}>
              Indicator Reference Guide
            </Title>
          </Space>
        }
      >
        <Alert
          message="Understanding Your Analysis"
          description="Click on any indicator card below for detailed explanations, formulas, and interpretation guidelines. Each indicator includes academic citations and key factors that influence its calculation."
          type="info"
          showIcon
          style={{ marginBottom: 24 }}
        />

        {(category === 'all' || category === 'valuation') &&
          renderCategorySection('valuation', valuationIndicators)}

        {(category === 'all' || category === 'technical') &&
          renderCategorySection('technical', technicalIndicators)}

        {(category === 'all' || category === 'competitive') &&
          renderCategorySection('competitive', competitiveIndicators)}

        {renderDetailModal()}
      </Card>
    </div>
  );
};

export default IndicatorExplanations;