import React, { useState } from 'react';
import {
  Card,
  Descriptions,
  Tag,
  Space,
  Typography,
  Alert,
  Row,
  Col,
  Statistic,
  List,
  Badge,
  Button,
  message,
  Dropdown,
} from 'antd';
import type { MenuProps } from 'antd';
import {
  ArrowUpOutlined,
  ArrowDownOutlined,
  TrophyOutlined,
  AlertOutlined,
  CheckCircleOutlined,
  DownloadOutlined,
  FilePdfOutlined,
  FileExcelOutlined,
  FileTextOutlined,
} from '@ant-design/icons';
import axios from 'axios';
import { Tooltip, ResponsiveContainer, PieChart, Pie, Cell } from 'recharts';
import AdvancedCharts from './AdvancedCharts';
import ChartAnalyticsPanel from './ChartAnalyticsPanel';
import DCFValuationDisplay from './DCFValuationDisplay';
import MacroEconomicsDisplay from './MacroEconomicsDisplay';
import InsiderActivityDisplay from './InsiderActivityDisplay';
import { AnalystInsightsSection } from './analyst';
import SentimentPanel from './SentimentPanel';
import { CatalystTimeline } from './catalyst';
import {
  ConfidenceMeter,
  AgentConfidenceBreakdown,
  ConfidenceBadge,
  ConfidenceWarning,
} from './confidence';
import {
  formatCurrency,
  formatLargeNumber,
  formatMarketCap,
  formatVolume,
  formatPercentage,
  formatRatio,
  getMarketCapTier,
  getBetaDescription,
} from '../utils/formatters';

const { Title, Text, Paragraph } = Typography;

interface AnalysisResultsProps {
  results: any;
}

const AnalysisResults: React.FC<AnalysisResultsProps> = ({ results }) => {
  const [exporting, setExporting] = useState(false);

  if (!results) {
    return <Alert message="No results available" type="warning" />;
  }

  const {
    analysis_id,
    symbols = [],
    recommendations = {},
    executive_summary = '',
    investment_thesis = '',
    confidence_score = 0,
    market_data = {},
    fundamental_analysis = {},
    technical_analysis = {},
    risk_analysis = {},
    valuation_analysis = {},
    macro_analysis = {},
    insider_analysis = {},
    catalyst_analysis = {},
    catalyst_calendar = {},
    analysis = {},
  } = results;

  // Extract additional data from nested analysis object
  const sentiment = analysis?.sentiment || {};
  const news = analysis?.news || {};
  const predictive = analysis?.predictive || {};
  const peer_comparison = analysis?.peer_comparison || {};

  // Extract confidence data from synthesis results
  const synthesis_result = results.synthesis_result || {};
  const consensus_breakdown = synthesis_result.consensus_breakdown || {};
  const agent_agreement = synthesis_result.agent_agreement || '';
  const overall_confidence = synthesis_result.confidence || confidence_score || 0;

  const API_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000';

  // Export handlers
  const handleExport = async (format: 'json' | 'csv' | 'pdf') => {
    if (!analysis_id) {
      message.error('Analysis ID not found');
      return;
    }

    try {
      setExporting(true);
      message.loading({ content: `Exporting as ${format.toUpperCase()}...`, key: 'export' });

      const response = await axios.get(
        `${API_URL}/api/v1/analyze/${analysis_id}/export/${format}`,
        {
          responseType: 'blob'
        }
      );

      // Create download link
      const url = window.URL.createObjectURL(new Blob([response.data]));
      const link = document.createElement('a');
      link.href = url;
      link.setAttribute('download', `analysis_${analysis_id}.${format}`);
      document.body.appendChild(link);
      link.click();
      link.remove();

      message.success({ content: `Exported successfully as ${format.toUpperCase()}!`, key: 'export', duration: 2 });
    } catch (error: any) {
      console.error('Export error:', error);
      message.error({
        content: `Export failed: ${error.response?.data?.detail || error.message}`,
        key: 'export',
        duration: 3
      });
    } finally {
      setExporting(false);
    }
  };

  // Export menu items
  const exportMenuItems: MenuProps['items'] = [
    {
      key: 'pdf',
      label: 'Export as PDF',
      icon: <FilePdfOutlined />,
      onClick: () => handleExport('pdf'),
    },
    {
      key: 'csv',
      label: 'Export as CSV',
      icon: <FileExcelOutlined />,
      onClick: () => handleExport('csv'),
    },
    {
      key: 'json',
      label: 'Export as JSON',
      icon: <FileTextOutlined />,
      onClick: () => handleExport('json'),
    },
  ];

  // Prepare chart data
  const confidenceData = [
    { name: 'Confidence', value: confidence_score * 100 },
    { name: 'Uncertainty', value: (1 - confidence_score) * 100 },
  ];

  const COLORS = ['#52c41a', '#d9d9d9'];

  const getRecommendationColor = (action: string) => {
    switch (action?.toUpperCase()) {
      case 'BUY':
        return 'success';
      case 'SELL':
        return 'error';
      case 'HOLD':
        return 'warning';
      default:
        return 'default';
    }
  };

  const getRecommendationIcon = (action: string) => {
    switch (action?.toUpperCase()) {
      case 'BUY':
        return <ArrowUpOutlined />;
      case 'SELL':
        return <ArrowDownOutlined />;
      default:
        return <CheckCircleOutlined />;
    }
  };

  return (
    <Space direction="vertical" style={{ width: '100%' }} size="large">
      {/* Export Button */}
      <div style={{ display: 'flex', justifyContent: 'flex-end', marginBottom: 16 }}>
        <Dropdown menu={{ items: exportMenuItems }} placement="bottomRight">
          <Button
            type="primary"
            icon={<DownloadOutlined />}
            loading={exporting}
            disabled={!analysis_id}
          >
            Export Report
          </Button>
        </Dropdown>
      </div>

      {/* Executive Summary */}
      <Card>
        <Space direction="vertical" style={{ width: '100%' }} size="large">
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
            <Title level={4} style={{ margin: 0 }}>Executive Summary</Title>
            {overall_confidence > 0 && (
              <ConfidenceBadge
                confidence={overall_confidence}
                size="default"
                showIcon={true}
                showLabel={true}
              />
            )}
          </div>
          <Alert
            message={executive_summary || 'Analysis complete'}
            type="info"
            showIcon
          />
          {investment_thesis && (
            <Paragraph>
              <Text strong>Investment Thesis:</Text> {investment_thesis}
            </Paragraph>
          )}
        </Space>
      </Card>

      {/* Expert Trading Charts - Chart Analytics Panel */}
      {symbols && symbols.length > 0 && (
        <Card title="📊 Expert Trading Charts" style={{ marginTop: 16 }}>
          <ChartAnalyticsPanel symbol={symbols[0]} />
        </Card>
      )}

      {/* Advanced Charts - Show for first symbol */}
      {symbols && symbols.length > 0 && (
        <AdvancedCharts
          symbol={symbols[0]}
          marketData={market_data?.market_data?.[symbols[0]] || {}}
          technicalData={{}}
        />
      )}

      {/* Confidence Score Section - Enhanced */}
      <Row gutter={[16, 16]}>
        <Col xs={24} md={12}>
          <Card
            title="Overall Confidence Score"
            style={{
              background: 'linear-gradient(135deg, rgba(212, 175, 55, 0.05) 0%, rgba(0, 0, 0, 0.1) 100%)',
              border: '1px solid rgba(212, 175, 55, 0.2)',
            }}
          >
            <ConfidenceMeter
              confidence={overall_confidence}
              label="AI Confidence"
              size="large"
              showIcon={true}
              showPercentage={true}
              animated={true}
            />
            <ConfidenceWarning
              confidence={overall_confidence}
              showAlways={true}
            />
          </Card>
        </Col>
        <Col xs={24} md={12}>
          <AgentConfidenceBreakdown
            consensusBreakdown={consensus_breakdown}
            agentAgreement={agent_agreement}
          />
        </Col>
      </Row>

      {/* Stock Recommendations */}
      <Card title="Stock Recommendations">
        <Row gutter={[16, 16]}>
          {Object.entries(recommendations).map(([symbol, rec]: [string, any]) => (
            <Col key={symbol} xs={24} sm={12} lg={8}>
              <Card
                hoverable
                style={{
                  height: '100%',
                  opacity: rec.confidence && rec.confidence < 0.4 ? 0.7 : 1,
                  border: rec.confidence && rec.confidence >= 0.7 ? '2px solid rgba(0, 212, 170, 0.3)' : undefined,
                  boxShadow: rec.confidence && rec.confidence >= 0.7 ? '0 0 20px rgba(0, 212, 170, 0.1)' : undefined,
                }}
                title={
                  <Space direction="vertical" style={{ width: '100%' }}>
                    <Space style={{ width: '100%', justifyContent: 'space-between' }}>
                      <Space>
                        <Text strong style={{ fontSize: 18 }}>{symbol}</Text>
                        <Tag color={getRecommendationColor(rec.action)} icon={getRecommendationIcon(rec.action)}>
                          {rec.action}
                        </Tag>
                      </Space>
                      {rec.confidence && (
                        <ConfidenceBadge
                          confidence={rec.confidence}
                          size="small"
                          showIcon={true}
                          showLabel={false}
                          pulse={rec.confidence >= 0.7}
                        />
                      )}
                    </Space>
                  </Space>
                }
              >
                <Space direction="vertical" style={{ width: '100%' }}>
                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                    <div>
                      <Text type="secondary">Conviction:</Text>
                      <Badge
                        status={rec.conviction === 'high' ? 'success' : rec.conviction === 'medium' ? 'warning' : 'default'}
                        text={rec.conviction?.toUpperCase()}
                        style={{ marginLeft: 8 }}
                      />
                    </div>
                  </div>

                  {rec.price_target && (
                    <Statistic
                      title="Price Target"
                      value={rec.price_target}
                      precision={2}
                      prefix="$"
                      valueStyle={{ fontSize: 20 }}
                    />
                  )}

                  {rec.rationale && rec.rationale.length > 0 && (
                    <div>
                      <Text strong>Key Points:</Text>
                      <List
                        size="small"
                        dataSource={rec.rationale.slice(0, 3)}
                        renderItem={(item: string) => (
                          <List.Item>
                            <Text style={{ fontSize: 12 }}>• {item}</Text>
                          </List.Item>
                        )}
                      />
                    </div>
                  )}

                  {rec.risks && rec.risks.length > 0 && (
                    <div>
                      <Text strong type="danger">
                        <AlertOutlined /> Risks:
                      </Text>
                      <List
                        size="small"
                        dataSource={rec.risks.slice(0, 2)}
                        renderItem={(item: string) => (
                          <List.Item>
                            <Text type="danger" style={{ fontSize: 12 }}>
                              • {item}
                            </Text>
                          </List.Item>
                        )}
                      />
                    </div>
                  )}
                </Space>
              </Card>
            </Col>
          ))}
        </Row>
      </Card>

      {/* Market Data */}
      {market_data.market_data && (
        <Card title="Market Data Analysis">
          <Row gutter={[16, 16]}>
            {Object.entries(market_data.market_data).map(([symbol, data]: [string, any]) => (
              <Col key={symbol} span={12}>
                <Card title={symbol} size="small">
                  <Descriptions column={2} size="small">
                    <Descriptions.Item label="Current Price">
                      ${data.current_price?.toFixed(2) || 'N/A'}
                    </Descriptions.Item>
                    <Descriptions.Item label="P/E Ratio">
                      {data.pe_ratio?.toFixed(2) || 'N/A'}
                    </Descriptions.Item>
                    <Descriptions.Item label="Market Cap">
                      ${((data.market_cap || 0) / 1e9).toFixed(2)}B
                    </Descriptions.Item>
                    <Descriptions.Item label="Volume">
                      {((data.volume || 0) / 1e6).toFixed(2)}M
                    </Descriptions.Item>
                    <Descriptions.Item label="52W High">
                      ${data['52_week_high']?.toFixed(2) || 'N/A'}
                    </Descriptions.Item>
                    <Descriptions.Item label="52W Low">
                      ${data['52_week_low']?.toFixed(2) || 'N/A'}
                    </Descriptions.Item>
                  </Descriptions>
                </Card>
              </Col>
            ))}
          </Row>
        </Card>
      )}

      {/* Fundamental Analysis */}
      {fundamental_analysis.fundamental_data && (
        <Card title="Fundamental Analysis">
          <Row gutter={[16, 16]}>
            {Object.entries(fundamental_analysis.fundamental_data).map(([symbol, data]: [string, any]) => (
              <Col key={symbol} span={12}>
                <Card
                  title={
                    <Space>
                      <Text>{symbol}</Text>
                      <Tag color={data.financial_strength === 'strong' ? 'success' : data.financial_strength === 'moderate' ? 'warning' : 'default'}>
                        {data.financial_strength?.toUpperCase()}
                      </Tag>
                    </Space>
                  }
                  size="small"
                >
                  <Space direction="vertical" style={{ width: '100%' }}>
                    <div>
                      <Text strong>Investment Grade:</Text>
                      <Badge
                        count={data.investment_grade || 'NR'}
                        style={{
                          backgroundColor: data.investment_grade === 'A' ? '#52c41a' : data.investment_grade === 'B' ? '#faad14' : '#d9d9d9',
                          marginLeft: 8,
                        }}
                      />
                    </div>

                    {data.profitability && (
                      <div>
                        <Text type="secondary">Key Metrics:</Text>
                        <ul style={{ marginTop: 8, paddingLeft: 20 }}>
                          {data.profitability.roe && <li>ROE: {data.profitability.roe.toFixed(1)}%</li>}
                          {data.profitability.net_margin && <li>Net Margin: {data.profitability.net_margin.toFixed(1)}%</li>}
                        </ul>
                      </div>
                    )}
                  </Space>
                </Card>
              </Col>
            ))}
          </Row>

          {fundamental_analysis.key_insights && fundamental_analysis.key_insights.length > 0 && (
            <div style={{ marginTop: 16 }}>
              <Title level={5}>
                <TrophyOutlined /> Key Insights
              </Title>
              <List
                dataSource={fundamental_analysis.key_insights}
                renderItem={(insight: string) => (
                  <List.Item>
                    <Text>• {insight}</Text>
                  </List.Item>
                )}
              />
            </div>
          )}
        </Card>
      )}

      {/* Analyst Insights Section - NEW! */}
      {fundamental_analysis.fundamental_data && symbols && symbols.length > 0 && (
        <AnalystInsightsSection
          fundamentalData={fundamental_analysis.fundamental_data[symbols[0]]}
          marketData={market_data?.market_data?.[symbols[0]]}
        />
      )}

      {/* Technical Analysis with Charts */}
      {technical_analysis && technical_analysis.technical_data && symbols && symbols.length > 0 && (
        <>
          <AdvancedCharts
            symbol={symbols[0]}
            marketData={market_data?.market_data?.[symbols[0]]}
            technicalData={technical_analysis.technical_data[symbols[0]]}
          />
          <Card title="Technical Analysis Summary">
            <Space direction="vertical" style={{ width: '100%' }}>
              {technical_analysis.trend_analysis && (
                <Alert
                  message="Trend Analysis"
                  description={technical_analysis.trend_analysis}
                  type="info"
                  showIcon
                />
              )}
              {technical_analysis.signals && (
                <Row gutter={[16, 16]}>
                  {technical_analysis.signals.rsi && (
                    <Col span={12}>
                      <Card size="small" title="RSI">
                        <Statistic
                          title="Value"
                          value={technical_analysis.signals.rsi.value}
                          suffix={`/ 100`}
                          valueStyle={{ color: technical_analysis.signals.rsi.value > 70 ? '#cf1322' : technical_analysis.signals.rsi.value < 30 ? '#3f8600' : '#000' }}
                        />
                        <Text type="secondary">{technical_analysis.signals.rsi.signal}</Text>
                      </Card>
                    </Col>
                  )}
                  {technical_analysis.signals.macd && (
                    <Col span={12}>
                      <Card size="small" title="MACD">
                        <Space direction="vertical">
                          <Text>Signal: {technical_analysis.signals.macd.signal}</Text>
                          <Text type="secondary">Histogram: {technical_analysis.signals.macd.histogram?.toFixed(2)}</Text>
                        </Space>
                      </Card>
                    </Col>
                  )}
                </Row>
              )}
            </Space>
          </Card>
        </>
      )}

      {/* Risk Analysis */}
      {risk_analysis && Object.keys(risk_analysis).length > 0 && (
        <Card title="Risk Analysis">
          <Row gutter={[16, 16]}>
            <Col span={8}>
              <Card size="small">
                <Statistic
                  title="Risk Level"
                  value={risk_analysis.risk_level}
                  valueStyle={{
                    color: risk_analysis.risk_level === 'HIGH' ? '#cf1322' :
                           risk_analysis.risk_level === 'MEDIUM' ? '#faad14' : '#3f8600'
                  }}
                  prefix={risk_analysis.risk_level === 'HIGH' ? <AlertOutlined /> : <CheckCircleOutlined />}
                />
              </Card>
            </Col>
            <Col span={8}>
              <Card size="small">
                <Statistic
                  title="Risk Score"
                  value={risk_analysis.risk_score}
                  suffix="/ 100"
                  valueStyle={{ color: risk_analysis.risk_score > 70 ? '#cf1322' : risk_analysis.risk_score > 50 ? '#faad14' : '#3f8600' }}
                />
              </Card>
            </Col>
            {risk_analysis.risk_data && symbols && symbols.length > 0 && risk_analysis.risk_data[symbols[0]] && (
              <Col span={8}>
                <Card size="small">
                  <Statistic
                    title="Sharpe Ratio"
                    value={risk_analysis.risk_data[symbols[0]].sharpe_ratio?.toFixed(2) || 'N/A'}
                    valueStyle={{ color: (risk_analysis.risk_data[symbols[0]].sharpe_ratio || 0) > 1 ? '#3f8600' : '#cf1322' }}
                  />
                </Card>
              </Col>
            )}
          </Row>
          {risk_analysis.mitigation_strategies && (
            <div style={{ marginTop: 16 }}>
              <Alert
                message="Risk Mitigation Strategies"
                description={risk_analysis.mitigation_strategies}
                type="warning"
                showIcon
              />
            </div>
          )}
        </Card>
      )}

      {/* Enhanced Sentiment Panel - NEW! */}
      {sentiment && Object.keys(sentiment).length > 0 && (
        <SentimentPanel
          sentimentData={sentiment}
          symbol={symbols && symbols.length > 0 ? symbols[0] : undefined}
        />
      )}

      {/* Recent News */}
      {news && news.articles && news.articles.length > 0 && (
        <Card title={`Recent News (${news.articles.length})`}>
          <List
            dataSource={news.articles.slice(0, 5)}
            renderItem={(article: any) => (
              <List.Item>
                <List.Item.Meta
                  title={<a href={article.url} target="_blank" rel="noopener noreferrer">{article.title}</a>}
                  description={article.source}
                />
              </List.Item>
            )}
          />
        </Card>
      )}

      {/* Predictive Analytics */}
      {predictive && Object.keys(predictive).length > 0 && (
        <Card title="Predictive Analytics">
          <Row gutter={[16, 16]}>
            {predictive.price_forecast && (
              <Col span={12}>
                <Card size="small" title="Price Forecast">
                  <Space direction="vertical" style={{ width: '100%' }}>
                    {predictive.price_forecast.short_term && (
                      <div>
                        <Text strong>Short Term (30 days): </Text>
                        <Tag color={predictive.price_forecast.short_term > 0 ? 'green' : 'red'}>
                          {predictive.price_forecast.short_term > 0 ? '+' : ''}{predictive.price_forecast.short_term.toFixed(2)}%
                        </Tag>
                      </div>
                    )}
                    {predictive.price_forecast.long_term && (
                      <div>
                        <Text strong>Long Term (1 year): </Text>
                        <Tag color={predictive.price_forecast.long_term > 0 ? 'green' : 'red'}>
                          {predictive.price_forecast.long_term > 0 ? '+' : ''}{predictive.price_forecast.long_term.toFixed(2)}%
                        </Tag>
                      </div>
                    )}
                  </Space>
                </Card>
              </Col>
            )}
            {predictive.confidence && (
              <Col span={12}>
                <Card size="small">
                  <Statistic
                    title="Forecast Confidence"
                    value={predictive.confidence * 100}
                    suffix="%"
                    precision={1}
                  />
                </Card>
              </Col>
            )}
          </Row>
          {predictive.summary && (
            <div style={{ marginTop: 16 }}>
              <Alert
                message="Predictive Analysis Summary"
                description={predictive.summary}
                type="info"
                showIcon
              />
            </div>
          )}
        </Card>
      )}

      {/* Peer Comparison */}
      {peer_comparison && Object.keys(peer_comparison).length > 0 && (
        <Card title="Peer Comparison">
          {peer_comparison.peers && peer_comparison.peers.length > 0 && (
            <List
              dataSource={peer_comparison.peers}
              renderItem={(peer: any) => (
                <List.Item>
                  <List.Item.Meta
                    title={peer.symbol}
                    description={
                      <Space>
                        <Text>P/E: {peer.pe_ratio?.toFixed(2) || 'N/A'}</Text>
                        <Text>Market Cap: ${((peer.market_cap || 0) / 1e9).toFixed(2)}B</Text>
                      </Space>
                    }
                  />
                  {peer.relative_performance && (
                    <Tag color={peer.relative_performance > 0 ? 'green' : 'red'}>
                      {peer.relative_performance > 0 ? '+' : ''}{peer.relative_performance.toFixed(2)}%
                    </Tag>
                  )}
                </List.Item>
              )}
            />
          )}
          {peer_comparison.summary && (
            <div style={{ marginTop: 16 }}>
              <Alert
                message="Peer Analysis Summary"
                description={peer_comparison.summary}
                type="info"
                showIcon
              />
            </div>
          )}
        </Card>
      )}

      {/* DCF Valuation Analysis */}
      {valuation_analysis && Object.keys(valuation_analysis).length > 0 && (
        <DCFValuationDisplay data={valuation_analysis} />
      )}

      {/* Macro Economics Analysis */}
      {macro_analysis && Object.keys(macro_analysis).length > 0 && (
        <MacroEconomicsDisplay data={macro_analysis} />
      )}

      {/* Catalyst Calendar - Upcoming Events */}
      {((catalyst_analysis && Object.keys(catalyst_analysis).length > 0) || (catalyst_calendar && Object.keys(catalyst_calendar).length > 0)) && (
        <CatalystTimeline
          data={catalyst_analysis || catalyst_calendar}
          symbol={symbols && symbols.length > 0 ? symbols[0] : undefined}
        />
      )}

      {/* Insider Activity Analysis */}
      {insider_analysis && Object.keys(insider_analysis).length > 0 && (
        <InsiderActivityDisplay data={insider_analysis} />
      )}

      {/* Metadata */}
      <Card title="Analysis Metadata" size="small">
        <Descriptions column={3} size="small">
          <Descriptions.Item label="Analysis ID">{results.request_id}</Descriptions.Item>
          <Descriptions.Item label="Execution Time">
            {results.execution_time?.toFixed(2)}s
          </Descriptions.Item>
          <Descriptions.Item label="Timestamp">{results.timestamp}</Descriptions.Item>
        </Descriptions>
      </Card>
    </Space>
  );
};

export default AnalysisResults;