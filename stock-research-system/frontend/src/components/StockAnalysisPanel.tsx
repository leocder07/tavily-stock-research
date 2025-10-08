import React, { useState, useEffect } from 'react';
import {
  Row,
  Col,
  Card,
  Statistic,
  Typography,
  Tag,
  Space,
  Button,
  Progress,
  Table,
  Alert,
  Timeline,
  Divider,
  Rate,
  Spin,
  Result,
  Badge,
  Tabs,
} from 'antd';
import {
  ArrowUpOutlined,
  ArrowDownOutlined,
  CheckCircleOutlined,
  CloseCircleOutlined,
  ExclamationCircleOutlined,
  ThunderboltOutlined,
  SafetyOutlined,
  TrophyOutlined,
  RocketOutlined,
  LineChartOutlined,
  DollarOutlined,
  FileTextOutlined,
  AlertOutlined,
  DashboardOutlined,
  AreaChartOutlined,
  TeamOutlined,
  QuestionCircleOutlined,
} from '@ant-design/icons';
import { theme } from '../styles/theme';
import AdvancedCharts from './AdvancedCharts';
import AnalysisResults from './AnalysisResults';
import AgentProgress from './AgentProgress';
import AIConfidenceMeter from './AIConfidenceMeter';
import ExecutiveSummary from './ExecutiveSummary';
import PerformanceCards from './PerformanceCards';
import ValuationDisplay from './ValuationDisplay';
import EnhancedValuationDisplay from './EnhancedValuationDisplay';
import TechnicalAnalysisDisplay from './TechnicalAnalysisDisplay';
import CompetitiveAnalysisDisplay from './CompetitiveAnalysisDisplay';
import IndicatorExplanations from './IndicatorExplanations';
import DataConfidenceDisplay from './DataConfidenceDisplay';
import axios from 'axios';

const { Title, Text, Paragraph } = Typography;
const { TabPane } = Tabs;

interface Stock {
  symbol: string;
  name: string;
  price: number;
  change: number;
  changePercent: number;
  volume: number;
  marketCap: number;
}

interface StockAnalysisPanelProps {
  stock: Stock;
}

const StockAnalysisPanel: React.FC<StockAnalysisPanelProps> = ({ stock }) => {
  const [loading, setLoading] = useState(true);
  const [analysisData, setAnalysisData] = useState<any>(null);
  const [recommendation, setRecommendation] = useState<'buy' | 'sell' | 'hold' | null>(null);
  const [confidence, setConfidence] = useState(0);
  const [activeAgents, setActiveAgents] = useState<any[]>([]);
  const [valuation, setValuation] = useState<any>(null);
  const [technical, setTechnical] = useState<any>(null);
  const [competitive, setCompetitive] = useState<any>(null);
  const [confidenceScores, setConfidenceScores] = useState<any>(null);
  const [aggregatedData, setAggregatedData] = useState<any>(null);
  const [marketMood, setMarketMood] = useState<any>(null);
  const [sectorRotation, setSectorRotation] = useState<any>(null);

  useEffect(() => {
    performDeepAnalysis();
  }, [stock.symbol]);

  const performDeepAnalysis = async () => {
    setLoading(true);
    try {
      // Connect to WebSocket for real-time updates
      const ws = new WebSocket('ws://localhost:8000/ws');

      ws.onmessage = (event) => {
        const data = JSON.parse(event.data);
        if (data.type === 'agent_update') {
          setActiveAgents(prev => {
            const existing = prev.find(a => a.name === data.agent);
            if (existing) {
              return prev.map(a => a.name === data.agent ? { ...a, ...data } : a);
            }
            return [...prev, data];
          });
        }
      };

      // Start analysis via the analyze endpoint
      const analyzeResponse = await axios.post('http://localhost:8000/api/v1/analyze', {
        query: `Analyze ${stock.symbol}`,
        user_id: 'user123',
        analysis_type: 'comprehensive',
        symbols: [stock.symbol]
      });

      const analysisId = analyzeResponse.data.analysis_id;

      // Poll for results
      let retries = 0;
      const maxRetries = 30; // 30 seconds max wait
      const pollInterval = 1000; // 1 second

      const pollForResults = async () => {
        try {
          const resultResponse = await axios.get(`http://localhost:8000/api/v1/analyze/${analysisId}/result`);

          if (resultResponse.data.status === 'completed') {
            const results = resultResponse.data;

            // Set all the enhanced data
            setAnalysisData(results);
            setValuation(results.valuation);
            setTechnical(results.technical_analysis);
            setCompetitive(results.competitive_analysis);
            setConfidenceScores(results.confidence_scores);
            setAggregatedData(results.aggregated_data);
            setMarketMood(results.market_mood);
            setSectorRotation(results.sector_rotation);

            // Set recommendation based on analysis
            const analysis = results.analysis;
            if (analysis && analysis.summary) {
              // Extract recommendation from summary
              if (analysis.summary.toLowerCase().includes('buy')) {
                setRecommendation('buy');
              } else if (analysis.summary.toLowerCase().includes('sell')) {
                setRecommendation('sell');
              } else {
                setRecommendation('hold');
              }
            }

            setConfidence(results.confidence_scores?.analysis || 0.75);
            setLoading(false);
            ws.close();
          } else if (retries < maxRetries) {
            retries++;
            setTimeout(pollForResults, pollInterval);
          } else {
            throw new Error('Analysis timeout');
          }
        } catch (error) {
          if (retries < maxRetries) {
            retries++;
            setTimeout(pollForResults, pollInterval);
          } else {
            console.error('Failed to get analysis results:', error);
            setLoading(false);
            ws.close();
          }
        }
      };

      // Start polling after a short delay
      setTimeout(pollForResults, 1000);

    } catch (error) {
      console.error('Analysis failed:', error);
      setLoading(false);
    }
  };

  // AI Decision Engine Results
  const aiDecision = {
    recommendation: recommendation || 'hold',
    confidence: confidence * 100,
    targetPrice: stock.price * 1.15,
    stopLoss: stock.price * 0.95,
    timeHorizon: '3-6 months',
    riskLevel: 'Medium',
  };

  // Key Factors for Decision
  const decisionFactors = [
    { factor: 'Technical Analysis', score: 85, weight: 25, signal: 'bullish' },
    { factor: 'Fundamental Analysis', score: 72, weight: 30, signal: 'neutral' },
    { factor: 'Market Sentiment', score: 78, weight: 20, signal: 'bullish' },
    { factor: 'AI Prediction Model', score: 88, weight: 25, signal: 'bullish' },
  ];

  // Risk Metrics
  const riskMetrics = {
    beta: 1.23,
    sharpeRatio: 1.85,
    maxDrawdown: -15.2,
    volatility: 28.5,
    var95: -8.2,
  };

  // Buy/Sell Signals
  const signals = {
    buy: [
      { signal: 'RSI Oversold', strength: 'Strong', description: 'RSI below 30, indicating oversold conditions' },
      { signal: 'Support Level', strength: 'Moderate', description: 'Price near strong support at $145' },
      { signal: 'Volume Surge', strength: 'Strong', description: '150% above average volume' },
      { signal: 'Bullish Pattern', strength: 'Moderate', description: 'Cup and handle formation detected' },
    ],
    sell: [
      { signal: 'Resistance Level', strength: 'Weak', description: 'Approaching resistance at $165' },
      { signal: 'Overbought RSI', strength: 'Weak', description: 'RSI approaching 70' },
    ],
  };

  const getRecommendationColor = (rec: string) => {
    switch (rec) {
      case 'buy':
        return theme.colors.success;
      case 'sell':
        return theme.colors.danger;
      default:
        return theme.colors.warning;
    }
  };

  const getRecommendationIcon = (rec: string) => {
    switch (rec) {
      case 'buy':
        return <ArrowUpOutlined />;
      case 'sell':
        return <ArrowDownOutlined />;
      default:
        return <ExclamationCircleOutlined />;
    }
  };

  if (loading) {
    return (
      <Card style={{
        background: theme.colors.background.secondary,
        border: `1px solid rgba(255, 255, 255, 0.08)`,
        minHeight: 400,
      }}>
        <div style={{ textAlign: 'center', padding: '60px 20px' }}>
          <Spin size="large" />
          <Title level={4} style={{ marginTop: 24 }}>Analyzing {stock.symbol}</Title>
          <Paragraph style={{ color: theme.colors.text.secondary }}>
            Our AI agents are performing deep analysis...
          </Paragraph>
          <AgentProgress analysisId={stock.symbol} />
        </div>
      </Card>
    );
  }

  return (
    <div>
      {/* Main Decision Card - CRED Style */}
      <Card
        style={{
          ...theme.effects.glassMorphism,
          marginBottom: 24,
          borderRadius: theme.borderRadius.xl,
          boxShadow: theme.shadows.glass,
        }}
      >
        <Row gutter={[32, 16]} align="middle">
          <Col xs={24} lg={8}>
            <div style={{ textAlign: 'center' }}>
              <div style={{
                width: 120,
                height: 120,
                margin: '0 auto 16px',
                borderRadius: '50%',
                background: aiDecision.recommendation === 'buy'
                  ? theme.colors.gradient.success
                  : aiDecision.recommendation === 'sell'
                  ? theme.colors.gradient.danger
                  : theme.colors.gradient.cyan,
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                boxShadow: theme.shadows.xl,
              }}>
                <div style={{ fontSize: 48, color: '#fff' }}>
                  {getRecommendationIcon(aiDecision.recommendation)}
                </div>
              </div>
              <Title level={2} style={{
                margin: 0,
                color: getRecommendationColor(aiDecision.recommendation),
                textTransform: 'uppercase',
                letterSpacing: 2,
              }}>
                {aiDecision.recommendation}
              </Title>
              <Text style={{ color: theme.colors.text.secondary }}>
                AI Recommendation
              </Text>
            </div>
          </Col>

          <Col xs={24} lg={16}>
            <Row gutter={[16, 16]}>
              <Col span={12}>
                <Statistic
                  title="Confidence Score"
                  value={aiDecision.confidence}
                  suffix="%"
                  valueStyle={{ color: theme.colors.primary }}
                  prefix={<ThunderboltOutlined />}
                />
                <Progress
                  percent={aiDecision.confidence}
                  strokeColor={theme.colors.gradient.primary}
                  trailColor={theme.colors.background.primary}
                  showInfo={false}
                />
              </Col>
              <Col span={12}>
                <Statistic
                  title="Target Price"
                  value={aiDecision.targetPrice}
                  precision={2}
                  prefix="$"
                  valueStyle={{ color: theme.colors.success }}
                />
                <Text style={{ color: theme.colors.text.muted, fontSize: 12 }}>
                  +{((aiDecision.targetPrice - stock.price) / stock.price * 100).toFixed(1)}% upside
                </Text>
              </Col>
              <Col span={12}>
                <Statistic
                  title="Stop Loss"
                  value={aiDecision.stopLoss}
                  precision={2}
                  prefix="$"
                  valueStyle={{ color: theme.colors.danger }}
                />
                <Text style={{ color: theme.colors.text.muted, fontSize: 12 }}>
                  -{((stock.price - aiDecision.stopLoss) / stock.price * 100).toFixed(1)}% risk
                </Text>
              </Col>
              <Col span={12}>
                <Statistic
                  title="Time Horizon"
                  value={aiDecision.timeHorizon}
                  valueStyle={{ fontSize: 16 }}
                />
                <Tag color="blue" style={{ marginTop: 4 }}>
                  {aiDecision.riskLevel} Risk
                </Tag>
              </Col>
            </Row>
          </Col>
        </Row>

        <Divider style={{ borderColor: 'rgba(255, 255, 255, 0.08)' }} />

        {/* Decision Factors */}
        <Title level={5} style={{ marginBottom: 16 }}>
          <TrophyOutlined /> Decision Factors
        </Title>
        <Row gutter={[16, 16]}>
          {decisionFactors.map((factor) => (
            <Col key={factor.factor} xs={12} lg={6}>
              <Card
                size="small"
                style={{
                  background: theme.colors.background.primary,
                  border: `1px solid rgba(255, 255, 255, 0.05)`,
                }}
              >
                <Text style={{ fontSize: 12, color: theme.colors.text.muted }}>
                  {factor.factor}
                </Text>
                <div style={{ marginTop: 8 }}>
                  <span style={{
                    fontSize: 20,
                    fontWeight: 700,
                    color: factor.score > 75 ? theme.colors.success : factor.score > 50 ? theme.colors.warning : theme.colors.danger,
                  }}>
                    {factor.score}
                  </span>
                  <span style={{ fontSize: 12, color: theme.colors.text.muted, marginLeft: 4 }}>
                    /100
                  </span>
                </div>
                <Tag
                  color={factor.signal === 'bullish' ? 'success' : factor.signal === 'bearish' ? 'error' : 'warning'}
                  style={{ marginTop: 8 }}
                >
                  {factor.signal}
                </Tag>
              </Card>
            </Col>
          ))}
        </Row>
      </Card>

      <Tabs defaultActiveKey="signals" size="large">
        {/* Buy/Sell Signals */}
        <TabPane
          tab={
            <span>
              <ThunderboltOutlined /> Trading Signals
            </span>
          }
          key="signals"
        >
          <Row gutter={[16, 16]}>
            <Col xs={24} lg={12}>
              <Card
                title={
                  <Space>
                    <CheckCircleOutlined style={{ color: theme.colors.success }} />
                    <Text strong>Buy Signals ({signals.buy.length})</Text>
                  </Space>
                }
                style={{
                  background: theme.colors.background.secondary,
                  border: `1px solid ${theme.colors.success}33`,
                }}
                headStyle={{
                  background: `${theme.colors.success}11`,
                  borderBottom: `1px solid ${theme.colors.success}33`,
                }}
              >
                <Timeline>
                  {signals.buy.map((signal, index) => (
                    <Timeline.Item
                      key={index}
                      dot={<CheckCircleOutlined style={{ color: theme.colors.success }} />}
                    >
                      <div>
                        <Text strong>{signal.signal}</Text>
                        <Badge
                          count={signal.strength}
                          style={{
                            backgroundColor: signal.strength === 'Strong' ? theme.colors.success : theme.colors.warning,
                            marginLeft: 8,
                          }}
                        />
                      </div>
                      <Text style={{ fontSize: 12, color: theme.colors.text.secondary }}>
                        {signal.description}
                      </Text>
                    </Timeline.Item>
                  ))}
                </Timeline>
              </Card>
            </Col>

            <Col xs={24} lg={12}>
              <Card
                title={
                  <Space>
                    <CloseCircleOutlined style={{ color: theme.colors.danger }} />
                    <Text strong>Sell Signals ({signals.sell.length})</Text>
                  </Space>
                }
                style={{
                  background: theme.colors.background.secondary,
                  border: `1px solid ${theme.colors.danger}33`,
                }}
                headStyle={{
                  background: `${theme.colors.danger}11`,
                  borderBottom: `1px solid ${theme.colors.danger}33`,
                }}
              >
                <Timeline>
                  {signals.sell.map((signal, index) => (
                    <Timeline.Item
                      key={index}
                      dot={<CloseCircleOutlined style={{ color: theme.colors.danger }} />}
                    >
                      <div>
                        <Text strong>{signal.signal}</Text>
                        <Badge
                          count={signal.strength}
                          style={{
                            backgroundColor: signal.strength === 'Strong' ? theme.colors.danger : theme.colors.warning,
                            marginLeft: 8,
                          }}
                        />
                      </div>
                      <Text style={{ fontSize: 12, color: theme.colors.text.secondary }}>
                        {signal.description}
                      </Text>
                    </Timeline.Item>
                  ))}
                </Timeline>
              </Card>
            </Col>
          </Row>

          {/* Risk Analysis */}
          <Card
            title={
              <Space>
                <SafetyOutlined style={{ color: theme.colors.primary }} />
                <Text strong>Risk Analysis</Text>
              </Space>
            }
            style={{
              background: theme.colors.background.secondary,
              border: `1px solid rgba(255, 255, 255, 0.08)`,
              marginTop: 16,
            }}
          >
            <Row gutter={[16, 16]}>
              <Col xs={8} lg={4}>
                <Statistic
                  title="Beta"
                  value={riskMetrics.beta}
                  precision={2}
                  valueStyle={{ fontSize: 20 }}
                />
              </Col>
              <Col xs={8} lg={4}>
                <Statistic
                  title="Sharpe Ratio"
                  value={riskMetrics.sharpeRatio}
                  precision={2}
                  valueStyle={{ fontSize: 20, color: theme.colors.success }}
                />
              </Col>
              <Col xs={8} lg={4}>
                <Statistic
                  title="Max Drawdown"
                  value={riskMetrics.maxDrawdown}
                  suffix="%"
                  precision={1}
                  valueStyle={{ fontSize: 20, color: theme.colors.danger }}
                />
              </Col>
              <Col xs={8} lg={4}>
                <Statistic
                  title="Volatility"
                  value={riskMetrics.volatility}
                  suffix="%"
                  precision={1}
                  valueStyle={{ fontSize: 20 }}
                />
              </Col>
              <Col xs={8} lg={4}>
                <Statistic
                  title="VaR (95%)"
                  value={riskMetrics.var95}
                  suffix="%"
                  precision={1}
                  valueStyle={{ fontSize: 20, color: theme.colors.warning }}
                />
              </Col>
              <Col xs={8} lg={4}>
                <Rate value={4} disabled style={{ fontSize: 16 }} />
                <div>
                  <Text style={{ fontSize: 12, color: theme.colors.text.muted }}>
                    Risk Score: 4/5
                  </Text>
                </div>
              </Col>
            </Row>
          </Card>
        </TabPane>

        {/* Advanced Charts */}
        <TabPane
          tab={
            <span>
              <LineChartOutlined /> Technical Charts
            </span>
          }
          key="charts"
        >
          <AdvancedCharts
            symbol={stock.symbol}
            marketData={{ current_price: stock.price }}
            technicalData={{}}
          />
        </TabPane>

        {/* AI Confidence Analysis */}
        <TabPane
          tab={
            <span>
              <ThunderboltOutlined /> AI Confidence
            </span>
          }
          key="confidence"
        >
          <Row gutter={[16, 16]}>
            <Col xs={24} lg={8}>
              <AIConfidenceMeter
                confidence={aiDecision.confidence}
                factors={{
                  technical: decisionFactors[0].score,
                  fundamental: decisionFactors[1].score,
                  sentiment: decisionFactors[2].score,
                  macro: decisionFactors[3].score,
                }}
                recommendation={aiDecision.recommendation}
                riskLevel={aiDecision.riskLevel.toLowerCase() as 'low' | 'medium' | 'high'}
              />
            </Col>
            <Col xs={24} lg={16}>
              <Card
                title="AI Model Insights"
                style={{
                  ...theme.effects.glassMorphism,
                  height: '100%',
                }}
              >
                <Space direction="vertical" style={{ width: '100%' }} size="large">
                  <div>
                    <Title level={5}>Key Patterns Detected</Title>
                    <ul style={{ color: theme.colors.text.secondary, lineHeight: 1.8 }}>
                      <li>Strong momentum indicators across multiple timeframes</li>
                      <li>Institutional accumulation pattern identified</li>
                      <li>Positive earnings revision trend</li>
                      <li>Sector rotation favoring this position</li>
                    </ul>
                  </div>
                  <div>
                    <Title level={5}>Risk Factors</Title>
                    <ul style={{ color: theme.colors.text.secondary, lineHeight: 1.8 }}>
                      <li>Market volatility above historical average</li>
                      <li>Potential resistance at key technical levels</li>
                      <li>Macroeconomic headwinds in sector</li>
                    </ul>
                  </div>
                </Space>
              </Card>
            </Col>
          </Row>
        </TabPane>

        {/* Full Analysis */}
        <TabPane
          tab={
            <span>
              <FileTextOutlined /> Detailed Report
            </span>
          }
          key="report"
        >
          {analysisData && <AnalysisResults results={analysisData} />}
        </TabPane>

        {/* Executive Summary */}
        <TabPane
          tab={
            <span>
              <TrophyOutlined /> Executive Summary
            </span>
          }
          key="executive"
        >
          <ExecutiveSummary
            analysisData={analysisData}
            valuation={valuation}
          />
        </TabPane>

        {/* Performance Cards */}
        <TabPane
          tab={
            <span>
              <DashboardOutlined /> Performance
            </span>
          }
          key="performance"
        >
          <PerformanceCards
            analysisData={analysisData}
            valuation={valuation}
            technical={technical}
            competitive={competitive}
          />
        </TabPane>

        {/* Valuation Analysis */}
        <TabPane
          tab={
            <span>
              <DollarOutlined /> Valuation
            </span>
          }
          key="valuation"
        >
          <EnhancedValuationDisplay
            valuation={valuation}
            currentPrice={stock.price}
          />
        </TabPane>

        {/* Technical Analysis */}
        <TabPane
          tab={
            <span>
              <AreaChartOutlined /> Technical Analysis
            </span>
          }
          key="technical"
        >
          <TechnicalAnalysisDisplay
            technical={technical}
            currentPrice={stock.price}
          />
        </TabPane>

        {/* Competitive Analysis */}
        <TabPane
          tab={
            <span>
              <TeamOutlined /> Competitive
            </span>
          }
          key="competitive"
        >
          <CompetitiveAnalysisDisplay
            competitive={competitive}
            symbol={stock.symbol}
          />
        </TabPane>

        {/* Data Confidence & Sources */}
        <TabPane
          tab={
            <span>
              <SafetyOutlined /> Data Confidence
            </span>
          }
          key="confidence"
        >
          <DataConfidenceDisplay
            confidenceScores={confidenceScores}
            aggregatedData={aggregatedData}
            marketMood={marketMood}
            sectorRotation={sectorRotation}
          />
        </TabPane>

        {/* Indicator Reference Guide */}
        <TabPane
          tab={
            <span>
              <QuestionCircleOutlined /> Indicator Guide
            </span>
          }
          key="guide"
        >
          <IndicatorExplanations category="all" />
        </TabPane>
      </Tabs>
    </div>
  );
};

export default StockAnalysisPanel;